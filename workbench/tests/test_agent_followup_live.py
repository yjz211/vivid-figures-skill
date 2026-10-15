"""Opt-in real model through browser: physical drag -> Agent style edit -> preserve data/offset."""
from pathlib import Path
import json, time
from playwright.sync_api import sync_playwright
import httpx
WEB=Path(__file__).resolve().parents[1];OUT=WEB/'verification/agent'
info=json.loads((OUT/'live-run.json').read_text());errors=[]
for attempt in range(30):
    try:
        if httpx.get('http://127.0.0.1:8766/api/health',trust_env=False,timeout=1).is_success:break
    except httpx.HTTPError:pass
    time.sleep(.3)
with sync_playwright() as w:
    b=w.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
    p=b.new_page(viewport={'width':1600,'height':1000});p.on('pageerror',lambda e:errors.append(str(e)))
    p.goto('http://127.0.0.1:8766/agent.html?session='+info['session'])
    p.wait_for_function('state.ready&&state.frame?.contentWindow.VividBridge?.snapshot().job!=null',timeout=60000)
    f=p.locator('#editor-host iframe').element_handle().content_frame()
    svg=f.locator('#object-preview').element_handle().content_frame();glyph=svg.locator('#vivid-ax0-x-label use').first;glyph.wait_for()
    box=glyph.bounding_box();assert box
    p.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2);p.mouse.down();p.mouse.move(box['x']+box['width']/2+18,box['y']+box['height']/2+3,steps=10);p.mouse.up()
    p.wait_for_timeout(800);f.wait_for_function('!rendering&&!liveRenderPending',timeout=120000);p.evaluate('VividAgent.flush()')
    before=p.evaluate('state.chart');manual=before['project']['object_edits']['vivid-ax0-x-label']
    assert abs(manual['props']['offset_x'])>1
    p.locator('#prompt').fill('把当前图的配色换成蓝天绿地，并把图例放到右上角。数据、标题、其他设置，以及我刚手动拖动的横轴名称位置全部保留。只修改这两项并出图。')
    p.locator('#send').click();p.wait_for_function('state.run&&["queued","running"].includes(state.run.status)',timeout=10000)
    rid=p.evaluate('state.run.id');print('FOLLOWUP STARTED',rid,flush=True)
    p.wait_for_timeout(600);p.screenshot(path=str(OUT/'agent-running.png'))
    p.wait_for_function('state.run&&["done","error","waiting","cancelled"].includes(state.run.status)',timeout=600000)
    run=p.evaluate('state.run');assert run['status']=='done',run
    p.wait_for_function('state.ready&&state.chart?.job===state.run.body.result.job',timeout=120000)
    after=p.evaluate('state.chart')
    assert after['project']['settings']['palette']=='blue-sky',after['project']['settings']
    assert after['project']['table']==before['project']['table']
    assert after['project']['object_edits']['vivid-ax0-x-label']==manual
    assert after['revision']>=before['revision']
    if before['project']['settings']['palette']!='blue-sky':assert after['revision']>before['revision']
    p.wait_for_timeout(800);p.screenshot(path=str(OUT/'agent-result.png'))
    assert not errors,errors
    report={'passed':True,'session':info['session'],'chart':after['id'],'run':rid,'job':after['job'],'palette':'blue-sky','manual_offset_preserved':True,'data_unchanged':True,'review':run['body'].get('review'),'usage':run['body'].get('usage'),'errors':errors}
    (OUT/'followup-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False),flush=True)
    b.close()
