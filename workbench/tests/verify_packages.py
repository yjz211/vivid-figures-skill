from pathlib import Path
import json,zipfile,hashlib,subprocess,sys,concurrent.futures
WEB=Path(__file__).resolve().parent.parent
OUT=WEB/'verification'; OUT.mkdir(exist_ok=True)
checks=[]
for path in sorted((WEB/'assets/downloads').glob('*.zip')):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None,path.name
        meta=json.loads(z.read('metadata.json'))
        assert hashlib.sha256(z.read('original.py')).hexdigest()==meta['original_sha256']
        assert hashlib.sha256(z.read('preview.py')).hexdigest()==meta['preview_source_sha256']
        assert all(name in z.namelist() for name in ['run_demo.py','README.md','card.md','gallery_theme.py','_utils/palettes.json','_utils/plot_utils.py'])
    checks.append(path.stem)
sample=['basic.grouped_bar','advanced.radar_ridgeline','screenshot.isosurface','template.shap_dependence','template.sem_violin_pearson','competition.china_choropleth']
def run(tid):
    target=OUT/'package-smoke'/tid;target.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(WEB/'assets/downloads'/f'{tid}.zip') as z:z.extractall(target)
    with (target/'test.log').open('w',encoding='utf8') as log:
        p=subprocess.run([sys.executable,'-X','utf8','run_demo.py'],cwd=target,stdout=log,stderr=log,timeout=240)
    result=target/'output/result.json'
    payload=json.loads(result.read_text(encoding='utf8')) if result.exists() else {}
    return dict(id=tid,returncode=p.returncode,status=payload.get('status'),images=len(payload.get('exports',[])))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(run,sample))
report=dict(validated_packages=len(checks),original_hashes_verified=True,smoke_tests=results)
(OUT/'package-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
assert all(r['returncode']==0 and r['status']=='ok' and r['images']>0 for r in results)
