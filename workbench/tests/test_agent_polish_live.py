"""Opt-in real model: selected dataset, independent chart, review, browser delivery."""
from pathlib import Path
import json, os
from playwright.sync_api import sync_playwright
WEB=Path(__file__).resolve().parents[1];OUT=WEB/'verification/polish'
URL=os.environ.get('VIVID_TEST_URL','http://127.0.0.1:8766')
info=json.loads((OUT/'quality-results.json').read_text(encoding='utf8'))
errors=[]
with sync_playwright() as w:
    b=w.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
    p=b.new_page(viewport={'width':1600,'height':1000});p.on('pageerror',lambda e:errors.append(str(e)))
    p.goto(URL+'/agent.html?session='+info['session']);p.wait_for_function('state.ready',timeout=90000)
    original=p.evaluate('state.chart');old_count=p.evaluate('state.session.charts.length')
    did=p.evaluate('state.session.datasets.find(d=>d.name.startsWith("advanced.ridgeline")).id')
    p.locator('#task-target').select_option('new');p.locator('#task-dataset').select_option(did)
    p.locator('#prompt').fill('使用选中的模拟数据，新建一张比较六种策略日均能耗分布的山脊图。保留全部540个样本，不进行汇总或生成新数据；配色用粉彩少女，横轴为日均能耗（MWh），标题明确写模拟数据。保留模板透明层叠的效果，检查出图；当前已有的组合图保持不变。')
    if p.evaluate('state.run?.status==="interrupted"'):
        p.locator('#run-notice button').click()
    else:p.locator('#send').click()
    p.wait_for_function('state.run&&["queued","running"].includes(state.run.status)',timeout=15000)
    rid=p.evaluate('state.run.id');print('REAL RUN',rid,flush=True)
    p.wait_for_timeout(800);p.screenshot(path=str(OUT/'real-agent-running.png'))
    p.wait_for_function('state.run&&["done","error","waiting","cancelled"].includes(state.run.status)',timeout=600000)
    run=p.evaluate('state.run');assert run['status']=='done',run
    p.wait_for_function('state.ready&&state.chart?.id===state.run.body.result.chart_id',timeout=90000)
    chart=p.evaluate('state.chart');assert chart['id']!=original['id'];assert chart['project']['template']=='advanced.ridgeline'
    assert chart['project']['settings']['palette']=='pastel-girl';assert len(chart['project']['table']['rows'])==540
    assert p.evaluate('state.session.charts.length')==old_count+1
    old=p.evaluate('(cid)=>api("/api/agent/charts/"+cid)',original['id']);assert old['revision']==original['revision'];assert old['project']==original['project']
    data=p.evaluate('(id)=>state.session.datasets.find(d=>d.id===id).table',did);assert chart['project']['table']==data
    assert run['body']['review']['visual'],run['body']['review']
    p.wait_for_timeout(1000);p.screenshot(path=str(OUT/'real-agent-result.png'))
    assert not errors,errors
    report={'passed':True,'session':info['session'],'run':rid,'chart':chart['id'],'original_unchanged':True,'all_rows_preserved':True,'new_chart_auto_opened':True,'review':run['body']['review'],'usage':run['body'].get('usage'),'errors':errors}
    (OUT/'real-agent-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False),flush=True)
    b.close()
