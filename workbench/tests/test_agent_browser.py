"""Actual embedded editor regression: gallery, render, drag, revisions, restore, export."""
from pathlib import Path
import json, uuid, os
from playwright.sync_api import sync_playwright
WEB=Path(__file__).resolve().parents[1];OUT=WEB/'verification/agent';OUT.mkdir(parents=True,exist_ok=True)
EXPECTED_IDS={card['id'] for card in json.loads((WEB.parent/'catalog/cards.json').read_text(encoding='utf8'))['cards']}
assert 'advanced.grouped_radial_bar' in EXPECTED_IDS
errors=[]
with sync_playwright() as w:
    b=w.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
    p=b.new_page(viewport={'width':1600,'height':1000},device_scale_factor=1)
    p.on('pageerror',lambda e:errors.append(str(e)))
    p.goto(os.environ.get('VIVID_TEST_URL','http://127.0.0.1:8766')+'/agent.html')
    p.wait_for_function('state.session!==null')
    prior=p.evaluate('state.session.id');p.locator('#new-session').click();p.wait_for_function('(id)=>state.session.id!==id',arg=prior)
    sid=p.evaluate('state.session.id')
    p.locator('#empty-gallery').click();assert p.locator('.template-card').count()==len(EXPECTED_IDS)
    assert p.locator('[data-example="advanced.grouped_radial_bar"]').count()==1
    p.locator('#gallery-search').fill('分组柱状对比');p.locator('[data-example="basic.grouped_bar"]').click()
    p.wait_for_function('state.ready&&state.frame?.contentWindow.VividBridge?.snapshot().job!=null',timeout=120000)
    p.evaluate('VividAgent.flush()')
    chart=p.evaluate('state.chart');assert chart['job']
    f=p.locator('#editor-host iframe').element_handle().content_frame()
    f.wait_for_function('!rendering&&!liveRenderPending&&lastRender!==null')
    f.locator('#project-name').fill('浏览器测试图表');f.locator('#project-name').press('Tab')
    p.evaluate('VividAgent.flush()');assert p.evaluate('state.chart.name')=='浏览器测试图表'
    before=p.evaluate('state.chart.revision')
    if f.locator('#show-settings').is_visible():f.locator('#show-settings').click()
    f.locator('[data-setting="title"]').fill('手动调整后的方案对比')
    f.locator('[data-setting="title"]').press('Tab')
    p.evaluate('VividAgent.flush()');assert p.evaluate('state.chart.revision')>before
    f.locator('#render').click();f.wait_for_function('!rendering&&!liveRenderPending&&lastRender?.signature===signature()',timeout=120000)
    p.evaluate('VividAgent.flush()')
    # Click a glyph and physically drag it through both nested iframes.
    svg=f.locator('#object-preview').element_handle().content_frame();svg.wait_for_selector('[data-vivid-drag] use')
    glyph=svg.locator('[data-vivid-drag] use').first;box=glyph.bounding_box();assert box
    p.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2);p.mouse.down();p.mouse.move(box['x']+box['width']/2+22,box['y']+box['height']/2+12,steps=10);p.mouse.up()
    p.wait_for_timeout(250)
    assert f.evaluate('Object.values(project.object_edits||{}).some(e=>Math.abs(e.props.offset_x||0)>1)')
    p.evaluate('VividAgent.flush()');moved=p.evaluate('state.chart');assert moved['project']['object_edits']
    p.screenshot(path=str(OUT/'editor-drag.png'))
    f.wait_for_function('!rendering&&!liveRenderPending',timeout=120000);p.evaluate('VividAgent.flush()')
    # Revision restoration is a new revision and old edits stay available.
    p.locator('#version-open').click();p.locator('[data-restore="1"]').click()
    p.wait_for_function('state.ready&&state.chart.project.settings.title!=="手动调整后的方案对比"',timeout=60000)
    restored=p.evaluate('state.chart');assert restored['revision']>moved['revision']
    f=p.locator('#editor-host iframe').element_handle().content_frame()
    f.wait_for_function('!rendering&&lastRender!==null',timeout=120000);p.evaluate('VividAgent.flush()')
    f.locator('#export-toggle').click();assert f.locator('#export-links a').count()==6
    with p.expect_download() as event:f.locator('#export-links a[download]').first.click()
    downloaded=event.value;downloaded.save_as(str(OUT/'browser-export.png'));assert (OUT/'browser-export.png').stat().st_size>10000
    f.locator('#export-close').click()
    p.screenshot(path=str(OUT/'editor.png'))
    p.reload();p.wait_for_function('state.ready&&state.chart!==null',timeout=60000);assert p.evaluate('state.session.id')==sid
    assert not errors,errors
    report={'passed':True,'session':sid,'chart':chart['id'],'glyph_drag':True,'revision_restore':True,'png_download':True,'reload':True,'errors':errors}
    (OUT/'browser-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False),flush=True)
    b.close()
