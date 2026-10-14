"""Real API render and standalone reproduction using the shipped runtime tools."""
from pathlib import Path
import hashlib, json, subprocess, sys, time, urllib.request, zipfile

WEB=Path(__file__).resolve().parents[1]
OUT=WEB/'verification/render-export'
OUT.mkdir(parents=True,exist_ok=True)
HTTP=urllib.request.build_opener(urllib.request.ProxyHandler({}))
BASE='http://127.0.0.1:8766'
def request(path,data=None):
    body=json.dumps(data,ensure_ascii=False).encode('utf8') if data is not None else None
    with HTTP.open(urllib.request.Request(BASE+path,data=body,headers={'Content-Type':'application/json'}),timeout=10) as response:
        return json.load(response)

project=request('/api/sample?id=basic.grouped_bar')
project['table']['rows'][0][1]=91.7
job=request('/api/render',project)['job']
for _ in range(180):
    status=request('/api/jobs/'+job)
    if status['state'] in ['done','error']:break
    time.sleep(.5)
assert status['state']=='done',status
base=status['base']
for name in ['figure.png','figure.pdf','figure.svg','plot.py','data.csv','reproduce.zip']:
    with HTTP.open(BASE+base+name,timeout=10) as response:
        payload=response.read()
    assert payload,name
    (OUT/name).write_bytes(payload)
original=WEB/'workspace/jobs'/job
repro=OUT/job
with zipfile.ZipFile(OUT/'reproduce.zip') as bundle:
    assert all(name in bundle.namelist() for name in ['source.py','original.py','project.json','engine.py','_utils/plot_utils.py','_utils/palettes.json'])
    for name in bundle.namelist():
        target=(repro/name).resolve()
        assert target.is_relative_to(repro.resolve()),name
    bundle.extractall(repro)
process=subprocess.run([sys.executable,'-X','utf8','run.py'],cwd=repro,capture_output=True,text=True,encoding='utf8',timeout=180)
(OUT/'reproduction.log').write_text(process.stdout+process.stderr,encoding='utf8')
assert process.returncode==0,process.stderr[-2000:]
digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert digest(repro/'figure.png')==digest(original/'figure.png'),'Standalone PNG differs'
assert json.loads((repro/'project.json').read_text(encoding='utf8'))['table']['rows'][0][1]==91.7
report={'passed':True,'job':job,'template':project['template'],'standalone_png_matches':True,'exports':['PNG','PDF','SVG','CSV','plot.py','reproduce.zip']}
(OUT/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False),flush=True)
