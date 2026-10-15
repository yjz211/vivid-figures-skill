"""Rendered regression for empty annotation boxes and data labels in four panels."""
from pathlib import Path
import json, os, time, hashlib, zipfile, subprocess, sys
import httpx
WEB=Path(__file__).resolve().parents[1];OUT=WEB/'verification/polish'
URL=os.environ.get('VIVID_TEST_URL','http://127.0.0.1:8766')
c=httpx.Client(base_url=URL,trust_env=False,timeout=30);c.headers['X-Vivid-Token']=c.get('/api/bootstrap').json()['token']
info=json.loads((OUT/'quality-results.json').read_text(encoding='utf8'));results=[]
for case in info['results']:
    if case['template'] not in ['basic.grouped_bar','basic.multipanel']:continue
    chart=c.get('/api/agent/charts/'+case['chart']).json();p=chart['project']
    response=c.post('/api/render',json=p);response.raise_for_status();job=response.json()['job']
    for _ in range(420):
        status=c.get('/api/jobs/'+job).json()
        if status['state'] in ['done','error']:break
        time.sleep(.5)
    assert status['state']=='done',status
    folder=WEB/'workspace/jobs'/job;code=(folder/'plot.py').read_text(encoding='utf8')
    if case['template']=='basic.grouped_bar':
        assert 'if is_best else None)' in code
        assert 'if is_best else {})' not in code
    else:
        manifest=json.loads((folder/'objects.json').read_text(encoding='utf8'))
        labels=[o['props']['text'] for o in manifest['objects'] if 'text' in o['props']]
        svg=(folder/'figure.svg').read_text(encoding='utf8')
        assert all(label in svg for label in ['常规调度','峰谷调度','协同储能','滨海产业园','东部加工园','1月','18月'])
        assert not any(label in labels for label in ['系列1','方法A','类1','分布1']),labels
        assert p['tables']['line']['headers'][1:] == ['常规调度','峰谷调度','协同储能']
    r=c.post('/api/agent/charts/'+chart['id']+'/save',json={'project':p,'base_revision':chart['revision'],'job':job});r.raise_for_status()
    (OUT/(case['template']+'-fixed.png')).write_bytes((folder/'preview.png').read_bytes())
    result={'template':case['template'],'job':job,'labels_from_data':True,'original_data_unchanged':True}
    if case['template']=='basic.multipanel':
        reproduction=OUT/'reproduction'/job
        with zipfile.ZipFile(folder/'reproduce.zip') as z:
            assert all((reproduction/name).resolve().is_relative_to(reproduction.resolve()) for name in z.namelist())
            z.extractall(reproduction)
        run=subprocess.run([sys.executable,'-X','utf8','run.py'],cwd=reproduction,capture_output=True,text=True,encoding='utf8',timeout=180)
        (OUT/'reproduction.log').write_text(run.stdout+run.stderr,encoding='utf8');assert run.returncode==0,run.stderr
        digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest(folder/'figure.png')==digest(reproduction/'figure.png')
        result['export_reproduces_exactly']=True
    results.append(result);print(json.dumps(result,ensure_ascii=False),flush=True)
(OUT/'quality-repair-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
