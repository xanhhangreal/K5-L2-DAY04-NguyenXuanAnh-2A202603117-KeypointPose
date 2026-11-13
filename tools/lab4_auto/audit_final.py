"""Read-only audit of final exports against live CVAT and assigned images."""
from collections import Counter
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import zipfile
from client import CVAT, ROOT, WORK, sha, write_json

c = CVAT()
assignment = json.loads((ROOT/'src/exports/assignment.json').read_text())
schema = json.loads((ROOT/'src/keypoint_schema.json').read_text())
result = {'checked_at': datetime.now(timezone(timedelta(hours=7))).isoformat(),
          'server': c.call('/api/server/about'), 'datasets': {}}
for kind, task in assignment['tasks'].items():
    base = kind.split('-')[0]
    label = 'person' if base == 'persons' else 'face'
    extra = '-extra' in kind
    path = ROOT/'src/exports'/('NguyenXuanAnh_'+('bonus_' if extra else '')+base+'.zip')
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert not any(n.lower().endswith(('.jpg','.jpeg','.png','.webp')) for n in z.namelist())
        data = json.loads(z.read('annotations/person_keypoints_default.json'))
    cat = next(x for x in data['categories'] if x['name'] == label)
    assert cat['keypoints'] == schema[label]['keypoints']
    assert sorted(map(sorted, cat['skeleton'])) == sorted(map(sorted, schema[label]['skeleton']))
    expected = assignment[base+('_extra' if extra else '')]
    assert sorted(Path(i['file_name']).name for i in data['images']) == sorted(expected)
    tid = task['task_id']
    meta = c.call(f'/api/tasks/{tid}/data/meta')
    live = c.call(f'/api/tasks/{tid}/annotations')
    labels = c.call(f'/api/labels?task_id={tid}&page_size=100')['results']
    parent = next(x for x in labels if x['name'] == label)
    ids = {x['name']: x['id'] for x in parent['sublabels']}
    job = c.call(f"/api/jobs/{task['job_id']}")
    assert job['state'] == 'completed'
    assert not live['tracks'] and not live['tags']
    assert len(live['shapes']) == len(data['annotations'])
    counts = {}
    for im in data['images']:
        name = Path(im['file_name']).name
        frame = next(i for i,f in enumerate(meta['frames']) if Path(f['name']).name == name)
        candidates = [s for s in live['shapes'] if s['frame'] == frame]
        anns = [a for a in data['annotations'] if a['image_id'] == im['id']]
        counts[name] = len(anns)
        for a in anns:
            pts = list(zip(a['keypoints'][::3],a['keypoints'][1::3],a['keypoints'][2::3]))
            assert len(pts) == len(cat['keypoints'])
            assert a['num_keypoints'] == sum(v>0 for x,y,v in pts)
            def matches(s):
                el = {e['label_id']: e for e in s['elements']}
                for n,(x,y,v) in zip(cat['keypoints'],pts):
                    e=el[ids[n]]
                    flag=0 if e['outside'] else 1 if e['occluded'] else 2
                    if flag != v or abs(x-e['points'][0]) > .011 or abs(y-e['points'][1]) > .011:
                        return False
                return True
            candidate=next((s for s in candidates if matches(s)),None)
            assert candidate is not None,(kind,name,a['id'])
            candidates.remove(candidate)
        assert not candidates
    flags=Counter(v for a in data['annotations'] for v in a['keypoints'][2::3])
    seconds=sum(json.loads((WORK/'predictions'/base/(Path(n).stem+'.json')).read_text())['seconds'] for n in expected)
    result['datasets'][kind]={'task_id':tid,'job_id':job['id'],'state':job['state'],
        'file':str(path.relative_to(ROOT)),'sha256':sha(path),'images':len(data['images']),
        'skeletons':len(data['annotations']),'per_image':counts,'visibility':dict(flags),
        'prediction_seconds_cached':round(seconds,2),'live_roundtrip_verified':True,
        'coordinate_tolerance_px':.011,'no_images_in_zip':True}
write_json(ROOT/'report/individual/final_validation.json',result)
print(json.dumps(result,ensure_ascii=False,indent=2))
