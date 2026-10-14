from pathlib import Path
import json
from playwright.sync_api import sync_playwright
WEB=Path(__file__).resolve().parents[1];OUT=WEB/'verification/interactions';checks=[];errors=[]
def check(name,value):checks.append(dict(name=name,ok=bool(value)));print(name,bool(value),flush=True);assert value,name
def ready(p):
 p.wait_for_function('!document.getElementById("export-toggle").disabled || !document.getElementById("data-error").hidden',timeout=180000)
 assert p.locator('#data-error').is_hidden(),p.locator('#data-error').inner_text()
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
  p=b.new_page(viewport={'width':1600,'height':1000});p.on('pageerror',lambda e:errors.append(str(e)))
  p.goto('http://127.0.0.1:8766/editor.html?template=advanced.dumbbell');ready(p)
  p.locator('.tabulator-row').first.locator('[tabulator-field="c0"]').click();p.keyboard.press('ArrowRight');p.keyboard.press('Shift+ArrowDown')
  check('Keyboard navigation and Shift region',p.evaluate('gridSelection().rows.length===2&&gridSelection().cols[0]===1'))
  p.locator('.tabulator-col[tabulator-field="c1"]').click();check('Whole column selection',p.evaluate('gridSelection().rows.length===project.table.rows.length'))
  p.locator('.tabulator-col[tabulator-field="c1"]').dblclick();p.locator('.vivid-header-editor').fill('数值 <A> & 测试');p.locator('.vivid-header-editor').press('Enter')
  check('Rename literal Chinese header',p.evaluate("project.table.headers[1]==='数值 <A> & 测试'"));p.locator('#undo').click()
  p.wait_for_timeout(100);p.evaluate("dataGrid.addRange(dataGrid.getRow(0).getCell('c0'))")
  p.locator('#paste-headers').check();p.evaluate("gridPaste('项目\\t前值\\t后值\\n测试甲\\t1\\t3\\n测试乙\\t2\\t4')")
  check('Paste headers and values',p.evaluate("project.table.headers[0]==='项目' && project.table.rows[1][2]==='4'"));p.locator('#undo').click()
  csv=OUT/'字段对应.csv';csv.write_text('之后,指标,之前\n14,准确率,10\n18,精度,20\n33,效率,30\n',encoding='utf-8-sig')
  p.locator('#import-file').set_input_files(str(csv));p.wait_for_function("project.table.headers[0]==='之后'")
  p.locator('#match-fields').click();check('Name match reorders bindings',p.evaluate('JSON.stringify(project.column_mappings.data)==="[1,2,0]"'))
  p.locator('[data-field="2"]').drag_to(p.locator('[data-column-role="2"]'));check('Drag field binding',p.locator('[data-column-role="2"]').input_value()=='2');p.locator('#undo').click()
  p.evaluate('deleteDataColumn(0)');check('Deleting bound column becomes unassigned',p.locator('[data-column-role="2"]').input_value()=='-1');p.locator('#undo').click()
  p.locator('#render').click();ready(p)
  p.locator('#style-name').fill('数据不变外观');p.locator('#save-style').click();p.wait_for_function("document.getElementById('style-select').value!==''")
  before=p.evaluate('JSON.stringify(project.table)');p.locator('[data-setting="font_size"]').fill('15');p.locator('[data-setting="font_size"]').press('Tab');p.locator('#apply-style').click();p.wait_for_function('project.settings.font_size===10')
  check('Style preserves data',p.evaluate('JSON.stringify(project.table)')==before);p.locator('#undo').click();check('Style undo',p.evaluate('project.settings.font_size')==15)
  p.locator('#recent-projects').click();p.locator('#library-dialog').wait_for(state='visible');old=p.evaluate('projectId');p.get_by_text('将当前项目存为副本',exact=True).click();p.wait_for_function('document.getElementById("library-dialog").open===false')
  check('Independent project copy',p.evaluate('projectId')!=old)
  p.locator('#render').click();ready(p);p.screenshot(path=str(OUT/'final-editor.png'),full_page=True)
  check('Workflow no JavaScript errors',not errors);b.close()
finally:(OUT/'grid-results.json').write_text(json.dumps(dict(checks=checks,errors=errors),ensure_ascii=False,indent=2),encoding='utf8')
