"""Browser usability regression. Uses an explicit test workspace, no model calls."""
from pathlib import Path
import json, os
from playwright.sync_api import sync_playwright
WEB=Path(__file__).resolve().parents[1];OUT=WEB/'verification/polish';OUT.mkdir(parents=True,exist_ok=True)
URL=os.environ.get('VIVID_TEST_URL','http://127.0.0.1:8766')
errors=[]
with sync_playwright() as w:
    b=w.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
    p=b.new_page(viewport={'width':1366,'height':768})
    p.on('pageerror',lambda e:errors.append(str(e)))
    p.goto(URL+'/agent.html');p.wait_for_function('state.session!==null')
    sid=p.evaluate("async()=>{const s=await api('/api/agent/sessions',{name:'自测 · 导入选图与画布操作'});await sessionList();await openSession(s.id);return s.id;}")
    # Import two files together. Both remain accessible, only the final preview opens.
    csv1='地区,常规方案,优化方案,储能协同\n滨海高新技术产业园,132,112,98\n北部智能制造示范区,158,130,113\n西部综合物流枢纽,108,92,85\n南部大学科研城,124,105,91\n中央商务办公集群,146,121,102\n东部食品加工园区,119,97,88\n'
    csv2='组别,数值\n甲,1\n甲,3\n乙,2\n乙,4\n'
    p.locator('#file-input').set_input_files([{'name':'园区能耗.csv','mimeType':'text/csv','buffer':csv1.encode()},{'name':'另一份数据.csv','mimeType':'text/csv','buffer':csv2.encode()}])
    p.wait_for_function('state.session.datasets.length===2');p.locator('[data-close="dataset-dialog"]').click()
    d=p.evaluate('state.session.datasets.find(d=>d.name==="园区能耗.csv").id')
    p.locator(f'[data-dataset="{d}"]').click();p.locator('#data-template').click()
    p.locator('#gallery-search').fill('分组柱状对比');p.locator('[data-choose="basic.grouped_bar"]').click()
    p.wait_for_selector('#binding-dialog[open]');assert p.locator('[data-source]').input_value()==d
    p.locator('#binding-name').fill('园区能耗 · 自有数据')
    p.locator('#binding-create').click()
    p.wait_for_function('state.ready&&state.chart?.job',timeout=120000)
    p.evaluate('VividAgent.flush()');before=p.evaluate('state.chart')
    assert before['project']['table']['rows'][0][0]=='滨海高新技术产业园'
    f=p.locator('#editor-host iframe').element_handle().content_frame()
    f.wait_for_function('!rendering&&!liveRenderPending&&lastRender')
    assert f.locator('#editor-shell').evaluate('(e)=>e.classList.contains("settings-folded")&&e.classList.contains("data-folded")')
    canvas=f.locator('#canvas').bounding_box();assert canvas['width']>750 and canvas['height']>350,canvas
    assert f.locator('#project-name').bounding_box()['width']>80
    p.screenshot(path=str(OUT/'after-1366.png'))
    # Select and drag letters; the plot must not resize on pointerdown.
    svg=f.locator('#object-preview').element_handle().content_frame();svg.wait_for_selector('[data-vivid-drag] use')
    glyph=svg.locator('#vivid-ax0-x-tick-0 use').first
    if not glyph.count():glyph=svg.locator('[data-vivid-drag] use').first
    box=glyph.bounding_box();old_width=f.locator('#canvas').bounding_box()['width']
    p.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2);p.mouse.down()
    assert f.locator('#canvas').bounding_box()['width']==old_width
    p.mouse.move(box['x']+box['width']/2+16,box['y']+box['height']/2+8,steps=8);p.mouse.up()
    p.wait_for_timeout(100);assert f.evaluate('DirectEdit.compatible()')
    p.wait_for_function('state.selected!==""');p.locator('#clear-selection').click()
    assert not f.evaluate('selectedObject');assert not p.evaluate('state.selected')
    f.wait_for_function('!rendering&&!liveRenderPending',timeout=120000);p.evaluate('VividAgent.flush()')
    manual=p.evaluate('state.chart.project.object_edits');assert manual
    f.locator('#quick-palette').select_option('blue-sky')
    f.wait_for_function('!rendering&&!liveRenderPending&&lastRender?.signature===signature()',timeout=120000)
    p.evaluate('VividAgent.flush()');assert p.evaluate('state.chart.project.settings.palette')=='blue-sky'
    assert p.evaluate('state.chart.project.object_edits')==manual
    # Data and detailed properties remain one click away.
    f.locator('#show-data').click();assert f.locator('.data-panel').bounding_box()['height']>150
    f.locator('#fold-data').click();f.locator('#show-settings').click();assert f.locator('#palette-select').is_visible()
    f.locator('#fold-settings').click()
    p.locator('#version-open').click();p.locator('[data-preview-job]').first.click();p.locator('.revision-preview:not([hidden]) img').wait_for()
    p.wait_for_function('document.querySelector(".revision-preview:not([hidden]) img").naturalWidth>0')
    p.locator('[data-close="versions-dialog"]').click()
    # Reload preserves data/chart and the wider canvas; narrow laptop can hide the assistant.
    p.reload();p.wait_for_function('state.ready&&state.chart?.job',timeout=120000)
    assert p.evaluate('state.session.id')==sid
    p.set_viewport_size({'width':1024,'height':768});p.locator('#toggle-agent').click();p.wait_for_timeout(250)
    assert p.evaluate('document.body.scrollWidth')==1024
    p.screenshot(path=str(OUT/'after-1024.png'))
    p.set_viewport_size({'width':1600,'height':1000});p.locator('#toggle-agent').click();p.wait_for_timeout(250)
    p.screenshot(path=str(OUT/'after-1600.png'))
    assert not errors,errors
    result={'passed':True,'session':sid,'chart':before['id'],'multi_file_import':True,'direct_binding':True,'large_canvas':canvas,'no_resize_on_drag':True,'selection_clear':True,'palette_preserves_offsets':True,'historical_preview':True,'errors':errors}
    (OUT/'browser-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False),flush=True)
    b.close()
