"""Local model proposals, explicit visual review, and resumable CVAT export."""
import argparse
from collections import Counter
from datetime import datetime, timezone, timedelta
import fcntl
import importlib.metadata
import json
import math
from pathlib import Path
import subprocess
import sys
import time
from urllib.parse import urlencode
import numpy as np
from PIL import Image, ImageDraw
import requests
from client import CVAT, ROOT, WORK, fingerprint, sha, write_json, log

CONFIG = {'version': 'lab4-v3', 'pose': 'yolo11m-pose.pt', 'imgsz': 1280, 'full_imgsz':640,
          'conf': .20, 'nms': .5, 'threads': 4, 'face': 'mediapipe-face-landmarker-float16-v1'}
FACE_INDICES = [263, 362, 386, 374, 33, 133, 159, 145, 1, 291, 61, 0, 17]
MODEL_URL = 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task'
SCHEMA = json.loads((ROOT / 'src/keypoint_schema.json').read_text())
LABELS = json.loads((ROOT / 'src/lab/labels_d04_keypoint.json').read_text())

def download(url, path):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(url, timeout=180)
        response.raise_for_status()
        tmp = path.with_suffix('.tmp')
        tmp.write_bytes(response.content)
        tmp.replace(path)

def overlap(a, b):
    intersection = max(0, min(a[2], b[2])-max(a[0], b[0])) * max(0, min(a[3], b[3])-max(a[1], b[1]))
    area = lambda x: max(0, x[2]-x[0])*max(0, x[3]-x[1])
    return intersection / max(1, area(a)+area(b)-intersection)

def deduplicate(items):
    kept = []
    for item in sorted(items, key=lambda x: -x['score']):
        a=item['bbox']
        def contained(b):
            area=lambda p:max(0,p[2]-p[0])*max(0,p[3]-p[1])
            intersection=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
            return intersection/max(1,min(area(a),area(b)))>.85 and max(area(a),area(b))/max(1,min(area(a),area(b)))>1.6
        if not any(overlap(a, x['bbox']) > .5 or contained(x['bbox']) for x in kept):
            kept.append(item)
    return sorted(kept, key=lambda x: (x['bbox'][0], x['bbox'][1]))

class Models:
    def __init__(self):
        import torch
        torch.set_num_threads(4)
        self.pose = None
        self.face = None

    def persons(self, image):
        if self.pose is None:
            from ultralytics import YOLO
            path = Path('/cache/models') / CONFIG['pose']
            path.parent.mkdir(parents=True, exist_ok=True)
            self.pose = YOLO(str(path))
        w, h = image.size
        crops = [(0, 0, w, h), (0, 0, w, h)]
        # Overlapping crops increase effective resolution for smaller people.
        if max(w, h) >= 400:
            cw, ch = int(w*.7), int(h*.7)
            crops += [(x, y, x+cw, y+ch) for x in (0, w-cw) for y in (0, h-ch)]
        found = []
        for crop_index, (x0, y0, x1, y1) in enumerate(crops):
            result = self.pose.predict(image.crop((x0,y0,x1,y1)), imgsz=CONFIG['full_imgsz'] if crop_index==0 else CONFIG['imgsz'],
                conf=CONFIG['conf'], iou=.5, device='cpu', verbose=False)[0]
            for box, points in zip(result.boxes, result.keypoints.data.cpu().numpy()):
                bbox = box.xyxy[0].tolist()
                bbox = [bbox[0]+x0,bbox[1]+y0,bbox[2]+x0,bbox[3]+y0]
                if bbox[3]-bbox[1] < 60:
                    continue
                # Preserve complete full-frame people. Crops only add spatially
                # distinct proposals, never replace a full-body prediction with
                # a high-confidence torso/leg fragment.
                if crop_index and any(overlap(bbox, p['bbox']) > .25 for p in found):
                    continue
                # Crop-edge fragments are not independent detections.
                if len(crops)>1 and (x0,y0,x1,y1)!=(0,0,w,h):
                    if ((x0>0 and bbox[0]<x0+4) or (y0>0 and bbox[1]<y0+4)
                        or (x1<w and bbox[2]>x1-4) or (y1<h and bbox[3]>y1-4)):
                        continue
                found.append({'bbox': bbox, 'score': float(box.conf.item()), 'crop_index':crop_index,
                    'points': [[float(p[0]+x0),float(p[1]+y0),float(p[2])] for p in points]})
        return deduplicate(found)

    def faces(self, image):
        import mediapipe as mp
        if self.face is None:
            path = Path('/cache/models/face_landmarker.task')
            download(MODEL_URL, path)
            options = mp.tasks.vision.FaceLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(model_asset_path=str(path)),
                num_faces=1, min_face_detection_confidence=.3,
                min_face_presence_confidence=.3, min_tracking_confidence=.3)
            self.face = mp.tasks.vision.FaceLandmarker.create_from_options(options)
        # Padded retry handles tight face crops; never invent landmarks on failure.
        for pad_fraction in (0, .3, .6):
            w,h = image.size
            px,py = int(w*pad_fraction),int(h*pad_fraction)
            padded = Image.new('RGB',(w+2*px,h+2*py),(127,127,127))
            padded.paste(image,(px,py))
            result = self.face.detect(mp.Image(image_format=mp.ImageFormat.SRGB,
                data=np.asarray(padded)))
            if result.face_landmarks:
                landmarks = result.face_landmarks[0]
                pts = [[float(landmarks[i].x*padded.width-px),
                        float(landmarks[i].y*padded.height-py), None] for i in FACE_INDICES]
                return [{'bbox':[min(p[0] for p in pts),min(p[1] for p in pts),
                                  max(p[0] for p in pts),max(p[1] for p in pts)],
                         'score': None, 'points':pts, 'padding':pad_fraction}]
        return []

def predict(models, kind, path):
    dest = WORK / 'predictions' / kind / (path.stem+'.json')
    key = fingerprint({'config':CONFIG,'image':sha(path),'kind':kind,'face_indices':FACE_INDICES})
    if dest.exists():
        old = json.loads(dest.read_text())
        if old['key'] != key:
            raise RuntimeError('Prediction inputs changed; inspect cache before replacement')
        return old
    started = time.monotonic()
    image = Image.open(path).convert('RGB')
    objects = getattr(models, kind)(image)
    value = {'key':key,'image':path.name,'width':image.width,'height':image.height,
             'objects':objects,'seconds':round(time.monotonic()-started,2)}
    write_json(dest,value)
    return value

def reviewed(prediction, kind, reviews):
    """Only image-based review sets v=1/2; unresolved proposals remain v=0."""
    label = 'person' if kind=='persons' else 'face'
    names = SCHEMA[label]['keypoints']
    entry = reviews.get(prediction['image'], {})
    if entry and entry.get('prediction_key') != prediction['key']:
        raise ValueError('Review belongs to different predictions: '+prediction['image'])
    result=[]
    for index,obj in enumerate(prediction['objects']):
        review = entry.get('objects',{}).get(str(index),{})
        if review.get('exclude'):
            continue
        pts=[]
        for name,point in zip(names,obj['points']):
            x,y,confidence=point
            adjustment=review.get('points',{}).get(name,{})
            x,y=adjustment.get('xy',[x,y])
            if not all(math.isfinite(float(v)) for v in (x,y)):
                raise ValueError('Non-finite coordinate')
            inside=0<=x<prediction['width'] and 0<=y<prediction['height']
            v=adjustment.get('v',review.get('default_v',0)) if inside else 0
            if v not in (0,1,2):
                raise ValueError('Invalid visibility')
            pts.append({'name':name,'x':x,'y':y,'v':v,'confidence':confidence})
        result.append({'index':index,'points':pts,'review':review})
    return result

def overlay(prediction, kind, path, reviews):
    label='person' if kind=='persons' else 'face'
    image=Image.open(path).convert('RGB')
    scale=min(3,max(1,1000/max(image.size)))
    image=image.resize((int(image.width*scale),int(image.height*scale)))
    draw=ImageDraw.Draw(image)
    is_reviewed=prediction['image'] in reviews
    draw.text((5,5),'MODEL + ASSISTANT | red=left blue=right | hollow=occluded' if is_reviewed else 'MODEL PROPOSALS (visibility not reviewed)',fill='yellow',stroke_width=1,stroke_fill='black')
    objects=reviewed(prediction,kind,reviews)
    for obj in objects:
        pts=obj['points']
        for a,b in SCHEMA[label]['skeleton']:
            p,q=pts[a-1],pts[b-1]
            if is_reviewed and (p['v']==0 or q['v']==0): continue
            draw.line((p['x']*scale,p['y']*scale,q['x']*scale,q['y']*scale),fill=(80,220,90),width=2)
        for i,p in enumerate(pts):
            if is_reviewed and p['v']==0: continue
            x,y=p['x']*scale,p['y']*scale
            color=(255,70,70) if p['name'].startswith('left') or p['name']=='mouth_left' else (70,140,255)
            draw.ellipse((x-3,y-3,x+3,y+3),outline=color,fill=color if p['v']==2 else None,width=2)
            draw.text((x+4,y-7),str(i+1),fill=color,stroke_width=1,stroke_fill='black')
        p=pts[0]
        draw.text((p['x']*scale,p['y']*scale-23),f"ID {obj['index']}",fill='yellow',stroke_width=1,stroke_fill='black')
    out=ROOT/'automation_previews'/kind/(path.stem+'.png')
    out.parent.mkdir(parents=True,exist_ok=True)
    image.save(out)

def signature(shape):
    return fingerprint({'frame':shape['frame'],'label_id':shape['label_id'],'type':shape['type'],
        'elements':sorted([{'label_id':e['label_id'],'points':[round(float(x),3) for x in e['points']],
            'outside':e['outside'],'occluded':e['occluded']} for e in shape['elements']],key=lambda e:e['label_id'])})

def protect_annotations(existing, row, wanted):
    current=Counter(map(signature,existing['shapes']))
    pending_matches=row.get('pending_signature')==dict(current)==dict(wanted)
    if existing.get('tags') or existing.get('tracks'):
        raise RuntimeError('Unexpected tags/tracks; preserving external edits')
    if row.get('annotations_hash') and fingerprint(existing)!=row['annotations_hash'] and not pending_matches:
        raise RuntimeError('CVAT annotations changed externally; preserving manual edits')
    if current!=wanted and existing['shapes'] and not row.get('annotations_hash'):
        raise RuntimeError('Unrecognized existing annotations; refusing overwrite')
    return current

def process(kind, images, predictions, reviews, cvat, state, save, task_name=None, output_path=None):
    row=state['tasks'].setdefault(kind,{})
    input_hash=fingerprint({p.name:sha(p) for p in images})
    if row.get('input_hash',input_hash)!=input_hash:
        raise RuntimeError('Input images changed')
    row['input_hash']=input_hash
    label='person' if kind=='persons' else 'face'
    project=state.get('project_id')
    if not project:
        name='d04-keypoint-auto-2A202603117'
        found=[p for p in cvat.call('/api/projects?'+urlencode({'search':name,'page_size':100}))['results'] if p['name']==name]
        if len(found)>1: raise RuntimeError('Duplicate managed projects')
        marker='https://localhost/lab4-auto/2A202603117'
        if found and found[0].get('bug_tracker') != marker:
            raise RuntimeError('Same-name project is not managed by this tool')
        obj=found[0] if found else cvat.call('/api/projects','POST',{'name':name,'labels':LABELS,'bug_tracker':marker})
        project=state['project_id']=obj['id']; save()
    if not row.get('task_id'):
        name=task_name or kind+'-auto-NguyenXuanAnh'
        found=[t for t in cvat.call('/api/tasks?'+urlencode({'project_id':project,'page_size':100}))['results'] if t['name']==name]
        if len(found)>1: raise RuntimeError('Duplicate managed tasks')
        marker='https://localhost/lab4-auto/'+kind
        if found and found[0].get('bug_tracker') != marker:
            raise RuntimeError('Same-name task is not managed by this tool')
        task=found[0] if found else cvat.call('/api/tasks','POST',{'name':name,'project_id':project,'segment_size':1000,'overlap':0,'bug_tracker':marker})
        row['task_id']=task['id']; save()
    tid=row['task_id']
    task=cvat.call(f'/api/tasks/{tid}')
    if not task.get('size'):
        if not row.get('upload_rq_id'):
            r=cvat.call(f'/api/tasks/{tid}/data','POST',{'image_quality':100,'sorting_method':'lexicographical','use_cache':True},files=images)
            row['upload_rq_id']=r['rq_id']; save()
        cvat.wait(row['upload_rq_id'])
    meta=cvat.call(f'/api/tasks/{tid}/data/meta')
    filenames=[Path(f['name']).name for f in meta['frames']]
    if sorted(filenames)!=sorted(p.name for p in images): raise RuntimeError('Frame mismatch')
    jobs=cvat.call('/api/jobs?'+urlencode({'task_id':tid,'page_size':100}))['results']
    if len(jobs)!=1: raise RuntimeError('Expected one job')
    row['job_id']=jobs[0]['id']
    labels=cvat.call('/api/labels?'+urlencode({'task_id':tid,'page_size':100}))['results']
    parent=next(x for x in labels if x['name']==label)
    sub={x['name']:x['id'] for x in parent['sublabels']}
    if list(sub)!=SCHEMA[label]['keypoints']: raise RuntimeError('Sublabel schema/order mismatch')
    shapes=[]
    for frame,filename in enumerate(filenames):
        prediction=predictions[filename]
        if filename not in reviews: raise RuntimeError('Visual review missing: '+filename)
        for obj in reviewed(prediction,kind,reviews):
            elements=[{'type':'points','frame':frame,'label_id':sub[p['name']],
                'points':[p['x'],p['y']],'outside':p['v']==0,'occluded':p['v']==1,
                'rotation':0,'z_order':0,'attributes':[]} for p in obj['points']]
            shapes.append({'type':'skeleton','frame':frame,'label_id':parent['id'],'points':[],
                'outside':False,'occluded':False,'rotation':0,'z_order':0,'attributes':[],
                'source':'auto','elements':elements})
    if not shapes: raise RuntimeError('No skeletons generated')
    wanted=Counter(map(signature,shapes))
    existing=cvat.call(f'/api/tasks/{tid}/annotations')
    current=protect_annotations(existing,row,wanted)
    if current!=wanted:
        write_json(WORK/'backups'/f'{tid}-{time.time_ns()}.json',existing)
        row['pending_signature']=dict(wanted); save()
        cvat.call(f'/api/tasks/{tid}/annotations','PUT',{'version':existing.get('version',0),'shapes':shapes,'tracks':[],'tags':[]})
        existing=cvat.call(f'/api/tasks/{tid}/annotations')
    if Counter(map(signature,existing['shapes']))!=wanted: raise RuntimeError('CVAT round-trip mismatch')
    row.update(annotations_hash=fingerprint(existing),annotation_count=len(shapes),status='annotated')
    row.pop('pending_signature',None)
    save()
    output=output_path or ROOT/'automation_exports'/('NguyenXuanAnh_'+kind+'.zip')
    if not (output.exists() and sha(output)==row.get('zip_sha256') and row.get('export_signature')==dict(wanted)):
        request=cvat.call(f'/api/tasks/{tid}/dataset/export?'+urlencode({'format':'COCO Keypoints 1.0','save_images':'false','location':'local'}),'POST')
        row['export_rq_id']=request['rq_id']; save()
        result=cvat.wait(request['rq_id'])
        exported=cvat.call(result['result_url'],download=True)
        data=cvat.get_file(exported['file'])
        output.parent.mkdir(parents=True,exist_ok=True)
        if output.exists(): (WORK/'backups'/f'{kind}-{time.time_ns()}.zip').write_bytes(output.read_bytes())
        output.write_bytes(data)
        row.update(zip_sha256=sha(output),export_signature=dict(wanted))
    row.update(status='exported',zip=str(output.relative_to(ROOT)))
    save()

def report(state):
    lines=['# Day04 — Kết quả tự động hóa','',
        'Nhãn sinh từ model, được trợ lý xem overlay; không phải bài gán tay hoặc tự review của học viên.',
        'Kết quả kiểm cấu trúc không chứng minh tọa độ và visibility chính xác. Không push/nộp LMS.','',
        'Cập nhật UTC+7: '+datetime.now(timezone(timedelta(hours=7))).isoformat(),'',
        '```json',json.dumps(CONFIG,indent=2),'```','',
        '| Bộ ảnh | Task / Job | Skeleton | Trạng thái |','|---|---|---:|---|']
    for kind,r in state['tasks'].items():
        lines.append(f"| {kind} | {r.get('task_id','')} / {r.get('job_id','')} | {r.get('annotation_count','')} | {r.get('status','pending')} |")
    for kind,r in state['tasks'].items():
        if r.get('task_id'): lines.append(f"\n[Job {kind}](http://localhost:8080/tasks/{r['task_id']}/jobs/{r.get('job_id','')})\n")
        if r.get('zip'): lines.append('ZIP: `'+r['zip']+'`\n')
    lines+=['','Hai task gốc 18/19 giữ nguyên: '+str(state.get('originals_unchanged','chưa kiểm cuối lượt'))]
    lines+=['','Thời gian suy luận thực tế theo cache (giây): '+str(state.get('prediction_seconds',{})),
        'Không bao gồm thời gian tải/cài model và review của trợ lý.']
    if state.get('error'): lines+=['','Lỗi: '+state['error']]
    review_path=ROOT/'tools/lab4_auto/visual_review.json'
    if review_path.exists():
        lines+=['','## Quan sát của trợ lý theo ảnh','']
        for name,entry in json.loads(review_path.read_text()).items():
            lines.append('- `'+name+'`: '+entry.get('note',''))
    if state.get('validation'): lines+=['','## Kiểm file xuất','','```text',state['validation'],'```']
    lines+=['','## Phiên bản runtime','','```json',json.dumps(state.get('runtime',{}),indent=2),'```']
    lines+=['','## SHA-256 model','','```json',json.dumps(state.get('model_weights',{}),indent=2),'```']
    verification=WORK/'verification.json'
    if verification.exists(): lines+=['','## Kiểm chứng runner','','```json',verification.read_text(),'```']
    (ROOT/'AUTOMATION_RUN_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

def main():
    parser=argparse.ArgumentParser()
    for option in ('check-only','pilot','predict-only'): parser.add_argument('--'+option,action='store_true')
    args=parser.parse_args()
    WORK.mkdir(exist_ok=True)
    lock=(WORK/'run.lock').open('w'); fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    state_path=WORK/'state.json'
    state=json.loads(state_path.read_text()) if state_path.exists() else {'tasks':{},'config':CONFIG}
    if state['config']!=CONFIG: raise RuntimeError('Configuration changed')
    state['runtime']={p:importlib.metadata.version(p) for p in ('ultralytics','mediapipe','torch','numpy','docker','opencv-python','opencv-contrib-python','onnx')}
    schema_hash=fingerprint({'labels':LABELS,'schema':SCHEMA})
    if state.get('schema_hash',schema_hash)!=schema_hash: raise RuntimeError('Schema changed')
    state['schema_hash']=schema_hash
    for name,expected in state.get('model_weights',{}).items():
        if sha(Path('/cache/models')/name)!=expected: raise RuntimeError('Cached model changed: '+name)
    def save(): write_json(state_path,state); report(state)
    cvat=CVAT()
    baseline={str(t):fingerprint(cvat.call(f'/api/tasks/{t}/annotations')) for t in (18,19)}
    if state.get('originals',baseline)!=baseline: raise RuntimeError('Original tasks changed since baseline')
    state['originals']=baseline
    assignment=json.loads((ROOT/'src/exports/assignment.json').read_text())
    if assignment['mssv']!='2A202603117': raise RuntimeError('Wrong assignment')
    for kind in ('persons','faces'):
        for name in assignment[kind]:
            if not (ROOT/'data'/kind/name).is_file(): raise FileNotFoundError(name)
    save()
    if args.check_only:
        log('Preflight OK; CVAT '+str(cvat.call('/api/server/about'))); return
    models=Models()
    reviews_path=ROOT/'tools/lab4_auto/visual_review.json'
    reviews=json.loads(reviews_path.read_text()) if reviews_path.exists() else {}
    try:
        for kind in ('persons','faces'):
            names=assignment[kind][:1] if args.pilot else assignment[kind]
            images=[ROOT/'data'/kind/n for n in names]
            predictions={}
            for path in images:
                log('Predict '+path.name)
                p=predict(models,kind,path); predictions[path.name]=p
                overlay(p,kind,path,reviews)
                log(f"{path.name}: {len(p['objects'])} skeleton proposals")
                if not p['objects']: raise RuntimeError('Model returned no skeleton: '+path.name)
            if not (args.predict_only or args.pilot): process(kind,images,predictions,reviews,cvat,state,save)
        if not (args.predict_only or args.pilot):
            check=subprocess.run([sys.executable,'src/check_submission.py','--persons',
                'automation_exports/NguyenXuanAnh_persons.zip','--faces','automation_exports/NguyenXuanAnh_faces.zip'],cwd=ROOT,capture_output=True,text=True)
            state['validation']=check.stdout+check.stderr
            if check.returncode: raise RuntimeError('Export structural validation failed')
        state.pop('error',None)
    except Exception as exc:
        state['error']=str(exc); raise
    finally:
        state['model_weights']={p.name:sha(p) for p in (Path('/cache/models')/CONFIG['pose'],Path('/cache/models/face_landmarker.task')) if p.exists()}
        state['prediction_seconds']={kind:round(sum(json.loads(p.read_text())['seconds'] for p in (WORK/'predictions'/kind).glob('*.json')),2) for kind in ('persons','faces')}
        after={str(t):fingerprint(cvat.call(f'/api/tasks/{t}/annotations')) for t in (18,19)}
        state['originals_unchanged']=after==baseline; save()
        if after!=baseline: raise RuntimeError('Original annotations changed')

if __name__=='__main__': main()
