"""Apply one documented visual-QC correction to current user-edited annotations."""
import copy
import json
import zipfile
from pathlib import Path
from client import CVAT,ROOT,WORK,write_json,fingerprint

c=CVAT();tid=20
with zipfile.ZipFile(ROOT/'src/exports/NguyenXuanAnh_persons.zip') as z:
    coco=json.loads(z.read('annotations/person_keypoints_default.json'))
image=next(i for i in coco['images'] if i['file_name']=='000000332273.jpg')
target=next(a for a in coco['annotations'] if a['image_id']==image['id'] and a['id']==14)
labels=c.call('/api/labels?task_id=20&page_size=100')['results']
label=next(l for l in labels if l['name']=='person');ids={l['name']:l['id'] for l in label['sublabels']}
meta=c.call('/api/tasks/20/data/meta');frame=next(i for i,f in enumerate(meta['frames']) if Path(f['name']).name==image['file_name'])
stored=c.call('/api/tasks/20/annotations')
names=next(x for x in coco['categories'] if x['name']=='person')['keypoints']
def matches(s):
    elements={e['label_id']:e for e in s['elements']}
    return s['frame']==frame and all(abs(elements[ids[n]]['points'][0]-target['keypoints'][3*j])<.02 and abs(elements[ids[n]]['points'][1]-target['keypoints'][3*j+1])<.02 for j,n in enumerate(names))
found=[s for s in stored['shapes'] if matches(s)]
assert len(found)==1,'Current CVAT shapes do not match reviewed ZIP; stop before editing'
shape=copy.deepcopy(found[0]);point=next(e for e in shape['elements'] if e['label_id']==ids['right_ankle'])
before=copy.deepcopy(point)
backup=WORK/'before-finalization/20-before-ankle-correction.json'
if not backup.exists():write_json(backup,stored)
point['outside']=True;point['occluded']=False
if point!=before:
    c.call('/api/tasks/20/annotations?action=update','PATCH',{'version':stored['version'],'shapes':[shape],'tracks':[],'tags':[]})
after=c.call('/api/tasks/20/annotations')
updated=next(s for s in after['shapes'] if s['id']==shape['id'])
assert next(e for e in updated['elements'] if e['label_id']==ids['right_ankle'])['outside']
others_before=[s for s in stored['shapes'] if s['id']!=shape['id']]
others_after=[s for s in after['shapes'] if s['id']!=shape['id']]
def canonical(value):
    if isinstance(value,dict):return {k:canonical(v) for k,v in value.items()}
    if isinstance(value,list):
        items=[canonical(v) for v in value]
        return sorted(items,key=lambda v:v['id']) if items and all(isinstance(v,dict) and 'id' in v for v in items) else items
    return value
original=json.loads(backup.read_text())
others_before=[s for s in original['shapes'] if s['id']!=shape['id']]
assert canonical(others_before)==canonical(others_after),'Unexpected changes outside target skeleton'
before=next(e for s in original['shapes'] if s['id']==shape['id'] for e in s['elements'] if e['label_id']==ids['right_ankle'])
write_json(WORK/'main-review-change.json',{'image':image['file_name'],'shape_id':shape['id'],'point':'right_ankle','code':'vis_flag',
    'reason':'Sliding player: predicted ankle is on ground without visible ankle/boot; hidden folded leg cannot be located confidently.',
    'before':before,'after':point,'other_shapes_unchanged':True})
print('Verified right_ankle outside; all other skeletons unchanged.')
