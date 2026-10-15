from pathlib import Path
import json,urllib.request,sys
from playwright.sync_api import sync_playwright
WEB=Path(__file__).resolve().parent.parent;OUT=WEB/'verification/editor';OUT.mkdir(parents=True,exist_ok=True)
EXPECTED_IDS={card['id'] for card in json.loads((WEB.parent/'catalog/cards.json').read_text(encoding='utf8'))['cards']}
assert 'advanced.grouped_radial_bar' in EXPECTED_IDS
errors=[];checks=[]
def check(name,ok):
    checks.append({'name':name,'ok':bool(ok)});assert ok,name
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
    context=browser.new_context(viewport={'width':1536,'height':1000},accept_downloads=True)
    page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8766/index.html');page.locator('#editable-filter').check()
    check('All catalog templates editable',set(page.evaluate('window.VIVID_EDITABLE_IDS'))==EXPECTED_IDS and page.locator('.card-edit-link').count()==page.locator('.chart-card').count())
    page.locator('.card-edit-link').filter(has_text='修改数据').first.click()
    page.wait_for_function('!document.getElementById("export-toggle").disabled',timeout=90000)
    check('Editor renders on opening',page.locator('#output-image').is_visible())
    page.goto('http://127.0.0.1:8766/editor.html?template=basic.grouped_bar')
    page.wait_for_function('!document.getElementById("export-toggle").disabled',timeout=90000)
    page.locator('#output-image').evaluate('(i)=>i.decode()')
    page.screenshot(path=str(OUT/'editor-desktop.png'))
    check('Desktop fits viewport',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
    cell=page.locator('[data-row="0"][data-col="1"]');cell.fill('120')
    check('Editing disables stale exports',page.locator('#export-toggle').is_disabled())
    page.locator('#undo').click();check('Undo restores original value',page.locator('[data-row="0"][data-col="1"]').inner_text()=='85.2')
    page.locator('#redo').click();check('Redo restores edit',page.locator('[data-row="0"][data-col="1"]').inner_text()=='120')
    page.locator('[data-setting="title"]').fill('修改数据后的模型比较')
    page.locator('[data-setting="palette"]').select_option('blue-sky')
    page.locator('#render').click();page.wait_for_function('!document.getElementById("export-toggle").disabled',timeout=90000)
    check('Changed data is reflected in actual render inputs',page.evaluate('lastRender!==null'))
    base=page.evaluate('lastRender.base');data=json.load(urllib.request.urlopen('http://127.0.0.1:8766'+base+'data_used.json'))
    check('Actual numeric input is 120',data['inputs']['data'][0][0]==120)
    page.locator('[data-row="1"][data-col="2"]').fill('不是数字');page.locator('#render').click()
    page.wait_for_selector('#data-error:not([hidden])')
    check('Invalid cell localized',page.locator('.invalid-cell').count()==1 and '第 2 行' in page.locator('#data-error').inner_text())
    page.locator('[data-row="1"][data-col="2"]').fill('80.5')
    page.locator('#add-row').click();check('Add row',page.locator('#table-count').inner_text().startswith('5 行'))
    page.locator('[data-delete-row="4"]').click()
    # Multi-cell paste expands and changes numeric cells.
    page.locator('[data-row="0"][data-col="1"]').evaluate(r'''el=>{const d=new DataTransfer();d.setData('text/plain','121\t82\n79\t81');el.dispatchEvent(new ClipboardEvent('paste',{clipboardData:d,bubbles:true,cancelable:true}));}''')
    check('Spreadsheet paste',page.locator('[data-row="1"][data-col="2"]').inner_text()=='81')
    with page.expect_download() as dl:page.locator('#save-project').click()
    project_file=OUT/'saved-project.vivid.json';dl.value.save_as(str(project_file))
    saved=json.loads(project_file.read_text(encoding='utf8'));check('Saved project includes edited values',saved['table']['rows'][0][1]=='121')
    csvpath=OUT/'导入测试.csv';csvpath.write_text('区域,销量,利润\n甲,10,3\n乙,15,6\n丙,20,8\n',encoding='utf-8-sig')
    page.locator('#import-file').set_input_files(str(csvpath));page.wait_for_function('document.getElementById("table-count").textContent==="3 行 × 3 列"')
    check('CSV imported with header',page.locator('[data-header="1"]').inner_text()=='销量')
    # Restore the saved project and rerender.
    page.locator('#project-file').set_input_files(str(project_file));page.wait_for_function(r'''document.querySelector('[data-row="0"][data-col="1"]').textContent==='121' ''')
    page.locator('#render').click();page.wait_for_function('!document.getElementById("export-toggle").disabled',timeout=90000)
    page.locator('#export-toggle').click()
    with page.expect_download() as dl:page.locator('#export-links a').filter(has_text='完整复现包').click()
    dl.value.save_as(str(OUT/'reproduce.zip'))
    check('Reproduction package downloaded',(OUT/'reproduce.zip').stat().st_size>100000)
    page.locator('#export-close').click()
    # Excel sheet selection uses the actual uploaded workbook.
    from openpyxl import Workbook
    w=Workbook();a=w.active;a.title='第一表';a.append(['区域','值']);a.append(['甲',5]);a.append(['乙',8]);b=w.create_sheet('第二表');b.append(['区域','值']);b.append(['丙',30]);b.append(['丁',40]);w.save(OUT/'两张表.xlsx')
    page.locator('#import-file').set_input_files(str(OUT/'两张表.xlsx'));page.wait_for_selector('#sheet-row:not([hidden])')
    page.locator('#sheet-select').select_option(label='第二表');page.wait_for_function(r'''document.querySelector('[data-row="0"][data-col="1"]').textContent==='30' ''')
    check('Excel sheet selection',page.locator('[data-row="0"][data-col="0"]').inner_text()=='丙')
    page.locator('#load-example').click();page.locator('#render').click();page.wait_for_function('!document.getElementById("export-toggle").disabled',timeout=90000)
    page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(OUT/'editor-mobile.png'),full_page=True)
    check('Mobile no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
    check('No JS errors',not errors)
    browser.close()
(OUT/'ui-results.json').write_text(json.dumps({'checks':checks,'errors':errors},ensure_ascii=False,indent=2),encoding='utf8');print('UI checks passed:',len(checks))
