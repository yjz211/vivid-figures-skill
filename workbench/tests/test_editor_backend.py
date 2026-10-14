from pathlib import Path
import urllib.request,json,time,sys
WEB=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(WEB/'editor_backend'))
from schema import SPECS,sample
BASE='http://127.0.0.1:8766'
def request(path,data=None):
    req=urllib.request.Request(BASE+path,data=json.dumps(data,ensure_ascii=False).encode('utf8') if data is not None else None,headers={'Content-Type':'application/json'})
    return json.load(urllib.request.urlopen(req,timeout=20))
jobs=[]
for tid in SPECS:
    project=sample(tid);job=request('/api/render',project)['job'];jobs.append((tid,job))
report=[]
for tid,job in jobs:
    for i in range(180):
        status=request('/api/jobs/'+job)
        if status['state'] in ['done','error']:break
        time.sleep(1)
    print(tid,status,flush=True);report.append(dict(id=tid,job=job,**status))
(WEB/'verification/editor-backend.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
assert all(x['state']=='done' for x in report)
