"""Opt-in: start the configured model, cancel it, verify the run ends promptly."""
from pathlib import Path
import json,time
import httpx
WEB=Path(__file__).resolve().parents[1];OUT=WEB/'verification/agent'
c=httpx.Client(base_url='http://127.0.0.1:8766',trust_env=False,timeout=10)
c.headers['x-vivid-token']=c.get('/api/bootstrap').json()['token']
s=c.post('/api/agent/sessions',json={'name':'Agent 停止功能验证'}).json()
r=c.post('/api/agent/sessions/'+s['id']+'/runs',json={'prompt':'请检查当前项目是否有可用的数据，再说明适合哪些模板。'}).json()
for _ in range(100):
    if (WEB/'workspace/agent/runs'/r['id']/'plan-1/model-events.jsonl').exists():break
    time.sleep(.05)
else:raise AssertionError('model process did not start')
time.sleep(.25);started=time.monotonic()
c.post('/api/agent/runs/'+r['id']+'/stop',json={}).raise_for_status()
for _ in range(100):
    final=c.get('/api/agent/runs/'+r['id']).json()
    if final['status']=='cancelled':break
    time.sleep(.1)
assert final['status']=='cancelled',final
report={'passed':True,'session':s['id'],'run':r['id'],'cancellation_seconds':round(time.monotonic()-started,2)}
(OUT/'cancel-live-results.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(report,flush=True)
