from client import CVAT,WORK,write_json
import json
c=CVAT();a=c.call('/api/tasks/20/annotations');write_json(WORK/'after-ankle-check.json',a)
b=json.loads((WORK/'before-finalization/20-before-ankle-correction.json').read_text())
x={s['id']:s for s in b['shapes']};y={s['id']:s for s in a['shapes']}
for i in x:
 if x[i]!=y.get(i):
  print('shape',i)
  for k in x[i]:
   if x[i][k]!=y[i].get(k): print(k, 'before=',x[i][k], 'after=',y[i].get(k))
print('IDs before',[s['id'] for s in b['shapes']]);print('IDs after',[s['id'] for s in a['shapes']])
