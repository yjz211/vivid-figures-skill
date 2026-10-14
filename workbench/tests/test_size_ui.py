from pathlib import Path
import json,urllib.request
from playwright.sync_api import sync_playwright
WEB=Path(__file__).resolve().parent.parent;OUT=WEB/'verification/size-ui';OUT.mkdir(exist_ok=True)
checks=[];errors=[]
def check(name,ok):checks.append({'name':name,'ok':bool(ok)});assert ok,name
def ready(p):
    p.wait_for_function('!document.getElementById("export-toggle").disabled || !document.getElementById("data-error").hidden',timeout=180000)
    assert p.locator('#data-error').is_hidden(),p.locator('#data-error').inner_text()
def inputs(p):return json.load(urllib.request.urlopen('http://127.0.0.1:8766'+p.evaluate('lastRender.base')+'data_used.json'))['inputs']
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
    page=browser.new_page(viewport={'width':1536,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8766/editor.html?template=advanced.dumbbell');ready(page)
    f=OUT/'列对应测试.csv';f.write_text('备注,指标,前值,后值\n甲,准确率,10,14\n乙,精度,20,18\n丙,效率,30,33\n',encoding='utf-8-sig')
    page.locator('#import-file').set_input_files(str(f));page.wait_for_function('project.table.headers.length===4')
    for i in range(3):page.locator(f'[data-column-role="{i}"]').select_option(str(i+1))
    page.locator('[data-delete-column="0"]').click()
    check('Deleting unused column preserves all field bindings',page.evaluate('JSON.stringify(project.column_mappings.data)==="[0,1,2]"'))
    page.locator('#render').click();ready(page)
    check('Values remain correct after column deletion',inputs(page)['before']==[10,20,30] and inputs(page)['after']==[14,18,33])
    page.locator('[data-delete-column="1"]').click()
    check('Deleted required field is visibly unassigned',page.locator('[data-column-role="1"]').input_value()=='-1')
    page.locator('#render').click();page.wait_for_selector('#data-error:not([hidden])')
    check('Required missing field is rejected before plotting','数据列对应' in page.locator('#data-error').inner_text())
    page.locator('#undo').click();check('Undo restores deleted field and binding',page.evaluate('project.table.headers.length===3 && project.column_mappings.data[1]===1'))
    page.goto('http://127.0.0.1:8766/editor.html?template=advanced.grouped_bar_3d');ready(page)
    page.locator('#data-requirements summary').click()
    check('3D size range shown next to data','1–10行' in page.locator('#requirements-content').inner_text())
    check('Auto layout and label avoidance default on',page.locator('[data-setting="auto_layout"]').is_checked() and page.locator('[data-setting="avoid_label_overlap"]').is_checked())
    f=OUT/'三维3乘4.csv';f.write_text('分类,方案A,方案B,方案C,方案D\n甲,3,5,7,8\n乙,4,6,8,9\n丙,5,7,9,10\n',encoding='utf-8-sig')
    page.locator('#import-file').set_input_files(str(f));page.wait_for_function('project.table.rows.length===3 && project.table.headers.length===5')
    page.locator('#render').click();ready(page);v=inputs(page)
    check('Imported 3x4 matrix reaches native 3D renderer',len(v['data'])==3 and all(len(r)==4 for r in v['data']))
    page.locator('[data-delete-row="2"]').click();page.locator('#add-column').click()
    for i in range(2):page.locator(f'[data-row="{i}"][data-col="5"]').fill(str(11+i))
    page.locator('#render').click();ready(page);v=inputs(page)
    check('Row removal and series addition reach renderer',len(v['data'])==2 and all(len(r)==5 for r in v['data']))
    page.locator('[data-setting="auto_layout"]').uncheck();check('Explicit canvas choice stored',page.evaluate('project.settings.auto_layout===false'))
    page.screenshot(path=str(OUT/'editor.png'),full_page=True)
    check('No JavaScript errors',not errors);browser.close()
(OUT/'results.json').write_text(json.dumps({'checks':checks,'errors':errors},ensure_ascii=False,indent=2),encoding='utf8')
print('UI checks passed:',len(checks))
