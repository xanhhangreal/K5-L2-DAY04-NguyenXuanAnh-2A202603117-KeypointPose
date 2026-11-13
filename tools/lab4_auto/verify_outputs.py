"""Check exported coordinates/flags against reviewed input and rerun invariants."""
import json
import subprocess
import sys
import zipfile
from pathlib import Path
from run import ROOT,WORK,SCHEMA,reviewed,write_json,report,overlay

state=json.loads((WORK/'state.json').read_text())
before=json.loads((WORK/'before-rerun.json').read_text())
reviews=json.loads((ROOT/'tools/lab4_auto/visual_review.json').read_text())
result={}
for kind in ('persons','faces'):
    for field in ('task_id','job_id','annotations_hash','zip_sha256'):
        assert state['tasks'][kind][field]==before['tasks'][kind][field],(kind,field)
    with zipfile.ZipFile(ROOT/state['tasks'][kind]['zip']) as z:
        assert all(not n.lower().endswith(('.jpg','.png','.jpeg','.webp')) for n in z.namelist())
        coco=json.loads(z.read('annotations/person_keypoints_default.json'))
    category=next(c for c in coco['categories'] if c['name']==('person' if kind=='persons' else 'face'))
    assert category['keypoints']==SCHEMA[category['name']]['keypoints']
    matched=0
    for image in coco['images']:
        name=Path(image['file_name']).name
        prediction=json.loads((WORK/'predictions'/kind/(Path(name).stem+'.json')).read_text())
        expected=reviewed(prediction,kind,reviews)
        annotations=[a for a in coco['annotations'] if a['image_id']==image['id']]
        assert len(annotations)==len(expected)
        for obj in expected:
            def matches(a):
                triples=list(zip(a['keypoints'][::3],a['keypoints'][1::3],a['keypoints'][2::3]))
                return len(triples)==len(obj['points']) and all(v==p['v'] and abs(x-p['x'])<=.011 and abs(y-p['y'])<=.011 for (x,y,v),p in zip(triples,obj['points']))
            candidate=next((a for a in annotations if matches(a)),None)
            assert candidate is not None,(kind,name,obj['index'])
            assert candidate['num_keypoints']==sum(p['v']>0 for p in obj['points'])
            annotations.remove(candidate);matched+=1
        overlay(prediction,kind,ROOT/'data'/kind/name,reviews)
    result[kind]={'images':len(coco['images']),'skeletons_verified':matched,'max_coordinate_rounding_px':.011}
tests=subprocess.run([sys.executable,'tools/lab4_auto/test_core.py'],cwd=ROOT,capture_output=True,text=True)
assert tests.returncode==0,tests.stderr
deps=subprocess.run([sys.executable,'-m','pip','check'],capture_output=True,text=True)
assert deps.returncode==0,deps.stdout
result.update(core_tests=tests.stderr.strip(),dependencies=deps.stdout.strip(),
              rerun_same_tasks_annotations_zip=True,originals_unchanged=state['originals_unchanged'])
write_json(WORK/'verification.json',result)
report(state)
print(json.dumps(result,ensure_ascii=False,indent=2))
