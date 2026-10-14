from pathlib import Path
import sys,json,shutil,subprocess,concurrent.futures
WEB=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(WEB/'editor_backend'))
from schema import SPECS,sample,CONTRACTS
OUT=WEB/'verification/catalog-editor';OUT.mkdir(exist_ok=True)
ids=sys.argv[1:] or list(CONTRACTS)
def run(tid):
    folder=OUT/tid;folder.mkdir(exist_ok=True)
    try:
        p=sample(tid);(folder/'project.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf8')
        shutil.copy2(WEB/'assets/sources'/tid/'preview.py',folder/'source.py');shutil.copy2(WEB/'assets/sources'/tid/'original.py',folder/'original.py')
        with (folder/'render.log').open('w',encoding='utf8') as log:
            r=subprocess.run([sys.executable,'-X','utf8',str(WEB/'editor_backend/worker.py'),str(folder)],stdout=log,stderr=log,timeout=180)
        status=json.loads((folder/'status.json').read_text(encoding='utf8'));return {'id':tid,**status}
    except Exception as e:return {'id':tid,'state':'error','message':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    results=list(pool.map(run,ids))
for r in results:print(r['id'],r['state'],r.get('message'),flush=True)
(OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
