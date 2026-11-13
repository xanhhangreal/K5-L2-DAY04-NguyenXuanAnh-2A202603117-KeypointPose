"""Final submission workflow through the lab's own setup/export with local REST auth."""
import argparse
from datetime import datetime,timezone,timedelta
import json
from pathlib import Path
import shutil
import sys
from urllib.parse import urlencode
from client import CVAT,ROOT,WORK,write_json,fingerprint,sha
from run import Models,predict,overlay,process
sys.path.insert(0,str(ROOT))
import lab

class LocalLabClient:
    def __init__(self,url): self.c=CVAT()
    def login(self,user=None): return self.c.call('/api/users/self')
    def all(self,path):
        items=[]
        while path:
            result=self.c.call(path);items+=result['results'];path=result.get('next')
        return items
    def project(self,name):return next((p for p in self.all('/api/projects?page_size=100') if p['name']==name),None)
    def task(self,pid,name):
        task=next((p for p in self.all('/api/tasks?'+urlencode({'project_id':pid,'page_size':100})) if p['name']==name),None)
        if task and not task.get('size'):
            folder=ROOT/'data'/name.removesuffix('-NguyenXuanAnh')
            self.upload(task['id'],sorted(folder.glob('*.jpg')),100)
            task=self.c.call(f"/api/tasks/{task['id']}")
        return task
    def post(self,path,data):return self.c.call(path,'POST',data)
    def patch(self,path,data):return self.c.call(path,'PATCH',data)
    def upload(self,tid,files,quality):
        request=self.c.call(f'/api/tasks/{tid}/data','POST',{'image_quality':quality,'sorting_method':'lexicographical','use_cache':True},files=files)
        self.c.wait(request['rq_id'])
    def export(self,tid):
        req=self.c.call(f'/api/tasks/{tid}/dataset/export?'+urlencode({'format':'COCO Keypoints 1.0','save_images':'false','location':'local'}),'POST')
        ready=self.c.wait(req['rq_id']);file=self.c.call(ready['result_url'],download=True)
        return self.c.get_file(file['file'])

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['setup','predict-bonus','import-bonus','export','complete']);args=p.parse_args()
    c=CVAT();WORK.mkdir(exist_ok=True)
    lab.Cvat=LocalLabClient
    if args.action=='setup':
        snapshot=WORK/'before-finalization';snapshot.mkdir(exist_ok=True)
        for tid in (20,21):
            for part in ('annotations','data/meta'):
                dest=snapshot/f"{tid}-{part.replace('/','-')}.json"
                if not dest.exists():write_json(dest,c.call(f'/api/tasks/{tid}/{part}'))
        for path in (ROOT/'src/exports').glob('*'):
            if path.is_file() and not (snapshot/path.name).exists():shutil.copy2(path,snapshot/path.name)
        task=c.call('/api/tasks/20');proj=c.call(f"/api/projects/{task['project_id']}")
        assert c.call('/api/tasks/21')['project_id']==proj['id']
        options=argparse.Namespace(mssv='2A202603117',ten='NguyenXuanAnh',force=False,skip_check=True,
            bonus=True,images_dir=None,url='http://localhost:8080',user='anhnguyenkaz',project=proj['name'],quality=100)
        lab.cmd_setup(options)
        write_json(WORK/'finalization-start.json',{'started':datetime.now(timezone(timedelta(hours=7))).isoformat(),
            'project':proj['name'],'project_id':proj['id'],'main_hashes':{str(t):fingerprint(c.call(f'/api/tasks/{t}/annotations')) for t in (20,21)}})
    elif args.action in ('predict-bonus','import-bonus'):
        a=json.loads(lab.ASSIGN_FILE.read_text());models=Models()
        reviewpath=ROOT/'tools/lab4_auto/bonus_review.json';reviews=json.loads(reviewpath.read_text()) if reviewpath.exists() else {}
        statepath=WORK/'bonus-state.json';state=json.loads(statepath.read_text()) if statepath.exists() else {'tasks':{},'project_id':c.call('/api/tasks/20')['project_id']}
        def save():write_json(statepath,state)
        for kind in ('persons','faces'):
            paths=[ROOT/'data'/(kind+'-extra')/name for name in a[kind+'_extra']]
            predictions={}
            for path in paths:
                result=predict(models,kind,path);predictions[path.name]=result
                overlay(result,kind,path,reviews);print(path.name,len(result['objects']),flush=True)
                if not result['objects']:raise RuntimeError('No model proposals: '+path.name)
            if args.action=='import-bonus':
                task=a['tasks'][kind+'-extra'];row=state['tasks'].setdefault(kind,{})
                row['task_id']=task['task_id'];save()
                process(kind,paths,predictions,reviews,c,state,save,task_name=task['task_name'],
                        output_path=ROOT/'src/exports'/f'NguyenXuanAnh_bonus_{kind}.zip')
    elif args.action=='complete':
        a=json.loads(lab.ASSIGN_FILE.read_text())
        for item in a['tasks'].values():
            job=c.call(f"/api/jobs/{item['job_id']}")
            if job['state']!='completed':c.call(f"/api/jobs/{item['job_id']}",'PATCH',{'state':'completed'})
            assert c.call(f"/api/jobs/{item['job_id']}")['state']=='completed'
    else:
        lab.http_ok=lambda url:True
        lab.cmd_export(argparse.Namespace(url='http://localhost:8080',user='anhnguyenkaz'))
    a=json.loads(lab.ASSIGN_FILE.read_text())
    write_json(WORK/'live-jobs.json',{kind:c.call(f"/api/jobs/{item['job_id']}") for kind,item in a['tasks'].items()})

if __name__=='__main__':main()
