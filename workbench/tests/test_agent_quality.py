"""Representative complex data renders through the Agent's manual binding API."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json, os, time, math
import httpx, numpy as np
WEB=Path(__file__).resolve().parents[1];OUT=WEB/'verification/polish';OUT.mkdir(parents=True,exist_ok=True)
URL=os.environ.get('VIVID_TEST_URL','http://127.0.0.1:8766')
client=httpx.Client(base_url=URL,trust_env=False,timeout=30)
client.headers['X-Vivid-Token']=client.get('/api/bootstrap').json()['token']
def post(path,data):
    r=client.post(path,json=data);assert r.is_success,(path,r.text);return r.json()
sid=post('/api/agent/sessions',{'name':'作品自测 · 六类复杂数据（模拟）'})['id']
rng=np.random.default_rng(20261015)
table=lambda h,r:{'headers':h,'rows':r}
regions=['滨海产业园','北部制造区','西部物流港','南部科研城','中央商务区','东部加工园','机场经济区','生态示范城']
series=['常规调度','峰谷调度','协同储能','预测优化']
bar=table(['地区']+series,[[v,*np.round(rng.uniform(65,180,4),2).tolist()] for v in regions])
groups=['常规调度','峰谷调度','协同储能','预测优化','滚动控制','联合优化']
ridges=table(['策略','日均能耗'],[[g,round(float(x),2)] for i,g in enumerate(groups) for x in np.r_[rng.normal(140-i*10,9+i,70),rng.normal(165-i*12,5,20)]])
heat=table(['园区']+[f'{i+1}月' for i in range(8)],[[f'园区{i+1}',*np.round(rng.normal(0,.7,8)+np.sin(np.arange(8)+i/2),3).tolist()] for i in range(12)])
bar3d=table(['区域']+series,[[v,*np.round(rng.uniform(8,48,4),2).tolist()] for v in regions[:6]])
x=rng.uniform(5,50,180);y=8+1.6*x+rng.normal(0,6,180)
scatter=table(['设备负荷','日均能耗'],np.round(np.c_[x,y],3).tolist())
multi={
 'line':table(['月份']+series[:3],[[f'{i+1}月',*np.round(100+np.array([20,5,-5])+20*np.sin(i*.5)+rng.normal(0,4,3),2).tolist()] for i in range(18)]),
 'bar':table(['园区']+series[:2],[[g,*np.round(rng.uniform(60,130,2),2).tolist()] for g in regions]),
 'scatter':table(['分组','X','Y'],[[groups[i%3],float(round(a,3)),float(round(b,3))] for i,(a,b) in enumerate(zip(x,y))]),
 'hist':table(['分组','数值'],[[groups[i],round(float(v),3)] for i in range(3) for v in rng.normal(90-i*8,8,100)])}
cases=[('basic.grouped_bar',{'data':bar},{'title':'各园区调度方案比较（模拟数据）','ylabel':'能耗（MWh）'}),
 ('advanced.ridgeline',{'data':ridges},{'title':'六种策略的能耗分布（模拟数据）','xlabel':'日均能耗（MWh）'}),
 ('advanced.cluster_heatmap',{'data':heat},{'title':'园区月度标准化偏差（模拟数据）'}),
 ('advanced.grouped_bar_3d',{'data':bar3d},{'title':'各区域与策略的节能率（模拟数据）','zlabel':'节能率（%）'}),
 ('basic.scatter_regression',{'data':scatter},{'title':'负荷与能耗的关系（模拟数据）','xlabel':'设备负荷（MW）','ylabel':'日均能耗（MWh）'}),
 ('basic.multipanel',multi,{'title':'园区运行综合观察（模拟数据）'})]
def draw(case):
    tid,tables,settings=case;bindings=[]
    for key,t in tables.items():
        d=post('/api/agent/sessions/'+sid+'/datasets',{'name':tid+' / '+key+' · 模拟','table':t})
        bindings.append({'table_key':key,'dataset_id':d['id'],'columns':list(range(len(t['headers'])))})
    mapping={'group':0,'value':1} if tid=='advanced.ridgeline' else {'x':0,'y':1} if tid=='basic.scatter_regression' else None
    c=post('/api/agent/sessions/'+sid+'/bind',{'template_id':tid,'name':settings['title'],'bindings':bindings,'mapping':mapping,'settings':{'palette':'pastel-girl',**settings}})
    # Ensure every injected table is exactly the supplied simulation, with no demo fallback.
    actual=c['project'].get('tables',{'data':c['project']['table']});assert actual==tables
    j=post('/api/render',c['project']);start=time.monotonic()
    while time.monotonic()-start<210:
        r=client.get('/api/jobs/'+j['job']).json()
        if r['state']=='done':break
        if r['state']=='error':raise AssertionError((tid,r))
        time.sleep(.4)
    assert r['state']=='done',(tid,r)
    c=post('/api/agent/charts/'+c['id']+'/save',{'project':c['project'],'base_revision':c['revision'],'job':j['job']})
    png=OUT/(tid+'.png');png.write_bytes(client.get(r['base']+'preview.png').content)
    objects=client.get(r['base']+'objects.json').json()
    report={'template':tid,'chart':c['id'],'job':j['job'],'rows':{k:len(t['rows']) for k,t in tables.items()},'objects':len(objects.get('objects',[])),'notes':r.get('notes',[]),'png':str(png)}
    print(json.dumps(report,ensure_ascii=False),flush=True);return report
with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(draw,cases))
(OUT/'quality-results.json').write_text(json.dumps({'session':sid,'results':results},ensure_ascii=False,indent=2),encoding='utf8')
print('QUALITY RENDERS COMPLETE',sid,flush=True)
