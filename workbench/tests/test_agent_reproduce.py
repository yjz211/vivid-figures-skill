"""Reproduce the actual Agent result, including saved manual text offsets."""
from pathlib import Path
import hashlib,json,subprocess,sys,zipfile
import httpx
WEB=Path(__file__).resolve().parents[1];OUT=WEB/'verification/agent'
info=json.loads((OUT/'review-recheck.json').read_text(encoding='utf8'))
c=httpx.Client(base_url='http://127.0.0.1:8766',trust_env=False,timeout=30)
chart=c.get('/api/agent/charts/'+info['chart']).json();job=chart['job']
bundle=OUT/'agent-result.zip';r=c.get('/workspace/jobs/'+job+'/reproduce.zip');r.raise_for_status();bundle.write_bytes(r.content)
dest=(OUT/'reproduction'/job).resolve();dest.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(bundle) as z:
    for name in z.namelist():assert (dest/name).resolve().is_relative_to(dest),name
    z.extractall(dest)
run=subprocess.run([sys.executable,'-X','utf8','run.py'],cwd=dest,capture_output=True,text=True,encoding='utf8',timeout=180)
(OUT/'reproduction.log').write_text(run.stdout+run.stderr,encoding='utf8');assert run.returncode==0,run.stderr[-2000:]
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(dest/'figure.png')==digest(WEB/'workspace/jobs'/job/'figure.png')
assert json.loads((dest/'project.json').read_text(encoding='utf8'))['object_edits']==chart['project']['object_edits']
report={'passed':True,'job':job,'standalone_png_matches':True,'manual_edits_in_bundle':True}
(OUT/'agent-reproduction-results.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(report,flush=True)
