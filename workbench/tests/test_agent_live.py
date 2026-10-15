"""Opt-in real model integration test. Requires the running Agent server and model login."""
from pathlib import Path
import base64, json, math, os, time
import httpx
BASE=os.environ.get('VIVID_TEST_URL','http://127.0.0.1:8766')
OUT=Path(__file__).resolve().parents[1]/'verification/agent';OUT.mkdir(parents=True,exist_ok=True)
client=httpx.Client(base_url=BASE,timeout=30,trust_env=False)
client.headers['x-vivid-token']=client.get('/api/bootstrap').json()['token']
def api(path,data=None):
    r=client.get(path) if data is None else client.post(path,json=data)
    r.raise_for_status();return r.json()
def wait(run):
    seen=None
    for _ in range(650):
        r=api('/api/agent/runs/'+run['id'])
        ev=api('/api/agent/sessions/'+run['session'])['runs'][0]
        stage=r['status']+' '+r['body'].get('message','')
        if stage!=seen:print(stage,flush=True);seen=stage
        if r['status'] in ['done','waiting','error','cancelled']:return r
        time.sleep(1)
    raise TimeoutError('Real model test timed out')

s=api('/api/agent/sessions',{'name':'Agent 实测 · 园区调度对比'})
table={'headers':['月份','常规调度 (MWh)','分时调度 (MWh)','协同优化 (MWh)'],
       'rows':[[f'{i+1}月',round(145+26*math.sin(i*.61)+i*1.5,1),round(128+21*math.sin(i*.61+.3)+i,1),round(104+15*math.sin(i*.61+.5)+i*.8,1)] for i in range(12)]}
content='\ufeff'+','.join(table['headers'])+'\n'+'\n'.join(','.join(map(str,r)) for r in table['rows'])
(OUT/'园区调度_模拟数据.csv').write_text(content,encoding='utf8')
imported=api('/api/import',{'name':'园区调度_模拟数据.csv','content':base64.b64encode(content.encode()).decode()})
d=api('/api/agent/sessions/'+s['id']+'/datasets',{'name':'园区调度 · 模拟数据','table':imported['table']})
run=api('/api/agent/sessions/'+s['id']+'/runs',{'prompt':'比较这组模拟数据中三种方案一整年的能耗趋势。请选择适合的现有模板，使用粉彩少女配色，标题和轴文字用中文，能耗单位是 MWh。不做统计汇总，没有误差数据。保留模板原效果。'})
(OUT/'live-run.json').write_text(json.dumps({'session':s['id'],'run':run['id']},indent=2),encoding='utf8')
print('Started',run['id'],flush=True)
r=wait(run)
(OUT/'first-run-result.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
assert r['status']=='done',r
result=r['body']['result'];assert result.get('chart_id'),r
c=api('/api/agent/charts/'+result['chart_id']);assert c['job'];assert c['project']['table']['rows']==imported['table']['rows']
print('REAL DRAW OK',c['id'],c['job'],flush=True)
(OUT/'current-chart.json').write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'session':s['id'],'chart':c['id'],'job':c['job'],'template':c['project']['template'],'review':r['body'].get('review'),'usage':r['body'].get('usage')},ensure_ascii=False),flush=True)
