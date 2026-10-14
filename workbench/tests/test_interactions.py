from pathlib import Path
import json,urllib.request,sys
from playwright.sync_api import sync_playwright
WEB=Path(__file__).resolve().parents[1];OUT=WEB/'verification/interactions';OUT.mkdir(exist_ok=True)
checks=[];errors=[]
def check(name,ok):
    checks.append(dict(name=name,ok=bool(ok)));print(name,bool(ok),flush=True);assert ok,name
def ready(p):
    p.wait_for_function('!document.getElementById("export-toggle").disabled || !document.getElementById("data-error").hidden',timeout=180000)
    assert p.locator('#data-error').is_hidden(),p.locator('#data-error').inner_text()
def objects(p):return json.load(urllib.request.urlopen('http://127.0.0.1:8766'+p.evaluate('lastRender.base')+'objects.json'))
try:
 with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
    p=browser.new_page(viewport={'width':1600,'height':1000});p.on('pageerror',lambda e:errors.append(str(e)))
    p.goto('http://127.0.0.1:8766/editor.html?template=basic.line');ready(p)
    check('Native object manifest',len(objects(p)['objects'])>3)
    cell=p.locator('.tabulator-row').first.locator('[tabulator-field="c1"]');original=p.evaluate('project.table.rows[0][1]')
    cell.dblclick();cell.locator('input').fill('72.5');cell.locator('input').press('Enter')
    check('Double click edit',p.evaluate('project.table.rows[0][1]')=='72.5')
    p.locator('#undo').click();check('Undo grid edit',p.evaluate('project.table.rows[0][1]')==original)
    p.locator('#redo').click();check('Redo grid edit',p.evaluate('project.table.rows[0][1]')=='72.5')
    p.evaluate("dataGrid.addRange(dataGrid.getRow(0).getCell('c1'),dataGrid.getRow(1).getCell('c2'))")
    p.locator('#paste-mode').select_option('selection');p.evaluate("gridPaste('1\\t2\\n3\\t4')")
    check('Paste exact region',p.evaluate('project.table.rows[1][2]')=='4')
    p.locator('#undo').click();p.wait_for_timeout(100)
    p.evaluate("dataGrid.addRange(dataGrid.getRow(0).getCell('c1'),dataGrid.getRow(1).getCell('c2'))")
    before=p.evaluate('JSON.stringify(project.table)');p.evaluate("gridPaste('1\\t2\\t3')")
    check('Mismatched paste is not truncated',p.evaluate('JSON.stringify(project.table)')==before)
    p.locator('#clear-cells').click();check('Range clear',p.evaluate("project.table.rows[1][2]===''"));p.locator('#undo').click()
    p.locator('#render').click();ready(p)
    p.locator('#pick-objects').click();p.frame_locator('#object-preview').locator('#vivid-ax0-x-line').wait_for(state='attached')
    p.frame_locator('#object-preview').locator('#vivid-ax0-x-line').dispatch_event('click')
    check('Pick original SVG axis',p.locator('#object-select').input_value()=='vivid-ax0-x')
    p.locator('[data-object-prop="label"]').fill('测试横坐标');p.locator('[data-object-prop="label"]').press('Tab')
    check('Object edit invalidates exports',p.locator('#export-toggle').is_disabled())
    p.locator('#render').click();ready(p)
    check('Object edit reaches rendered axis',next(o for o in objects(p)['objects'] if o['id']=='vivid-ax0-x')['props']['label']=='测试横坐标')
    p.locator('#style-name').fill('交互测试外观');p.locator('#save-style').click();p.wait_for_function("document.getElementById('style-select').value!==''")
    check('Style stored locally',bool(p.locator('#style-select').input_value()))
    p.evaluate('flushAutosave()');pid=p.evaluate('projectId');p.reload();ready(p)
    check('Reload restores project',p.evaluate('projectId')==pid and p.evaluate("project.object_edits['vivid-ax0-x'].props.label")=='测试横坐标')
    p.locator('#recent-projects').click();p.locator('#library-dialog').wait_for(state='visible');check('Recent projects',p.locator('#library-list button').count()>0);p.locator('#library-close').click()
    p.screenshot(path=str(OUT/'editor.png'),full_page=True)
    # Change structure without manually clearing old edits: stale edits must be skipped.
    p.evaluate('remember();project.table.rows.pop();tableRender();changed()');p.locator('#render').click();ready(p)
    check('Changed structure skips prior edits',bool(objects(p)['skipped']))
    check('No JavaScript errors',not errors)
    browser.close()
finally:
 (OUT/'ui-results.json').write_text(json.dumps(dict(checks=checks,errors=errors),ensure_ascii=False,indent=2),encoding='utf8')
