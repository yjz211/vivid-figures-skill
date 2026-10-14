from pathlib import Path
import sys,json,shutil,subprocess,concurrent.futures
WEB=Path(__file__).resolve().parents[1];sys.path.insert(0,str(WEB/'editor_backend'))
from schema import SPECS,sample
OUT=WEB/'verification/interaction-all';OUT.mkdir(exist_ok=True)
def run(tid):
    folder=OUT/tid;folder.mkdir(exist_ok=True)
    if '--retry' in sys.argv and (folder/'objects.json').exists() and json.loads((folder/'status.json').read_text(encoding='utf8')).get('state')=='done':return dict(id=tid,**json.loads((folder/'status.json').read_text(encoding='utf8')),objects=len(json.loads((folder/'objects.json').read_text(encoding='utf8'))['objects']),cached=True)
    try:
        project=sample(tid);(folder/'project.json').write_text(json.dumps(project,ensure_ascii=False),encoding='utf8')
        for src,dst in [('preview.py','source.py'),('original.py','original.py')]:shutil.copy2(WEB/'assets/sources'/tid/src,folder/dst)
        with (folder/'render.log').open('w',encoding='utf8') as log:r=subprocess.run([sys.executable,'-X','utf8',str(WEB/'editor_backend/worker.py'),str(folder)],stdout=log,stderr=log,timeout=210)
        status=json.loads((folder/'status.json').read_text(encoding='utf8'))
        if status['state']=='done':status['objects']=len(json.loads((folder/'objects.json').read_text(encoding='utf8'))['objects'])
        print(tid,status['state'],flush=True);return dict(id=tid,**status)
    except Exception as e:return dict(id=tid,state='error',message=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(run,SPECS))
(OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
print('TOTAL',len(results),'ERROR',sum(r['state']!='done' for r in results),flush=True)
