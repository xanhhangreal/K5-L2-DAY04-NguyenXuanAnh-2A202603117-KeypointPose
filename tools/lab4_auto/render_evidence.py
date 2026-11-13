"""Render explicitly labeled evidence from exports; these are NOT UI screenshots."""
import json
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET
from PIL import Image,ImageDraw,ImageFont
from client import ROOT,WORK

FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def font(size):
    try:return ImageFont.truetype(FONT,size)
    except OSError:return ImageFont.load_default()
def load(kind):
    with zipfile.ZipFile(ROOT/'src/exports'/f'NguyenXuanAnh_{kind}.zip') as z:
        return json.loads(z.read('annotations/person_keypoints_default.json'))

def render(kind,filename):
    d=load(kind);im=next(i for i in d['images'] if Path(i['file_name']).name==filename)
    category=next(c for c in d['categories'] if c['name']==('person' if kind=='persons' else 'face'))
    original=Image.open(ROOT/'data'/kind/filename).convert('RGB')
    scale=min(3,1000/max(original.size));size=(int(original.width*scale),int(original.height*scale))
    canvas=Image.new('RGB',(max(size[0],800),size[1]+100),'#172333')
    canvas.paste(original.resize(size),(0,100));draw=ImageDraw.Draw(canvas)
    draw.text((10,8),'RENDERED FROM EXPORTED COCO JSON - NOT A UI SCREENSHOT',font=font(16),fill='white')
    draw.text((10,33),filename+' | red=left, blue=right; hollow=v1; v0 hidden',font=font(15),fill='white')
    annotations=[a for a in d['annotations'] if a['image_id']==im['id']]
    for a in annotations:
        pts=list(zip(a['keypoints'][::3],a['keypoints'][1::3],a['keypoints'][2::3]))
        for u,v in category['skeleton']:
            x,y=pts[u-1],pts[v-1]
            if x[2] and y[2]:draw.line((x[0]*scale,100+x[1]*scale,y[0]*scale,100+y[1]*scale),fill='#5df590',width=2)
        for j,(x,y,v) in enumerate(pts):
            if not v:continue
            name=category['keypoints'][j];color='#ff5050' if name.startswith('left') or name=='mouth_left' else '#5aaaff'
            x*=scale;y=100+y*scale
            draw.ellipse((x-4,y-4,x+4,y+4),outline=color,fill=color if v==2 else None,width=2)
            draw.text((x+5,y-8),str(j+1),font=font(12),fill=color,stroke_width=1,stroke_fill='black')
        visible=[p for p in pts if p[2]]
        if visible:
            x,y,_=min(visible,key=lambda p:p[1]);draw.text((x*scale,75+y*scale),f"ann {a['id']}",font=font(16),fill='yellow',stroke_width=1,stroke_fill='black')
    return canvas

def main():
    out=WORK/'final-review';out.mkdir(exist_ok=True)
    for kind in ('persons','faces'):
        for image in load(kind)['images']:
            name=Path(image['file_name']).name
            render(kind,name).save(out/(Path(name).stem+'.png'))
    evidence=ROOT/'report/individual/images';evidence.mkdir(exist_ok=True)
    render('persons','000000023424.jpg').save(evidence/'2_nguoi_quay_lung.png')
    render('faces','face_324513.jpg').save(evidence/'3_mat_phong_to.png')
    labels=json.loads((ROOT/'src/lab/labels_d04_keypoint.json').read_text())
    p=next(l for l in labels if l['name']=='person');tree=ET.fromstring('<svg>'+p['svg']+'</svg>')
    canvas=Image.new('RGB',(1200,900),'#172333');draw=ImageDraw.Draw(canvas)
    draw.text((24,20),'PERSON LABEL: 17 POINTS / 19 EDGES',font=font(26),fill='white')
    draw.text((24,58),'Rendered from lab label schema; not a CVAT constructor screenshot.',font=font(18),fill='#adc6de')
    for line in tree.findall('line'):
        draw.line((40+float(line.attrib['x1'])*4,110+float(line.attrib['y1'])*6,
                   40+float(line.attrib['x2'])*4,110+float(line.attrib['y2'])*6),fill='#5df590',width=3)
    for circle in tree.findall('circle'):
        a=circle.attrib;x=40+float(a['cx'])*4;y=110+float(a['cy'])*6
        color='#ff5050' if a['data-label-name'].startswith('left') else '#5aaaff'
        draw.ellipse((x-6,y-6,x+6,y+6),fill=color)
        draw.text((x+9,y-8),a['data-node-id'],font=font(18),fill='white')
    for j,label in enumerate(p['sublabels']):
        draw.text((540,115+j*38),f"{j+1:02d}  {label['name']}",font=font(23),fill='white')
    draw.text((24,830),'Left/right follows subject anatomy. Source: src/lab/labels_d04_keypoint.json',font=font(17),fill='#adc6de')
    canvas.save(evidence/'1_label_person.png')
    d=load('persons');img=next(i for i in d['images'] if i['file_name']=='000000023424.jpg')
    a=next(a for a in d['annotations'] if a['image_id']==img['id'])
    lines=['COCO JSON EXPORT EVIDENCE (rendered, not editor screenshot)',
           'File: NguyenXuanAnh_persons.zip / annotations/person_keypoints_default.json',
           f"Image: {img['file_name']} | annotation id={a['id']} | num_keypoints={a['num_keypoints']}",
           'keypoints: 17 triples (x, y, v), 51 numbers','']
    names=next(c for c in d['categories'] if c['name']=='person')['keypoints']
    for j,name in enumerate(names):lines.append(f"{j+1:02d} {name:16s}: {a['keypoints'][3*j:3*j+3]}")
    lines+=['','v=0 ignored; v=1 occluded; v=2 visible.', 'Values copied from ZIP; no exported JSON was edited.']
    canvas=Image.new('RGB',(1250,100+len(lines)*29),'#172333');draw=ImageDraw.Draw(canvas)
    for j,line in enumerate(lines):draw.text((24,24+j*29),line,font=font(19),fill='white')
    canvas.save(evidence/'4_json_export.png')

if __name__=='__main__':main()
