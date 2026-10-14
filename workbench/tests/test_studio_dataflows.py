from pathlib import Path
import json,uuid
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'verification/studio';checks=[];errors=[];ids=[]
def check(name,ok):
 checks.append(dict(name=name,ok=bool(ok)));print(name,bool(ok),flush=True);assert ok,name
def ready(p):p.wait_for_function('typeof rendering!=="undefined"&&!rendering&&!liveRenderPending&&lastRender!==null&&!document.getElementById("export-toggle").disabled',timeout=120000)
def load(p,tid):
 pid='studio-test-'+uuid.uuid4().hex;ids.append(pid);p.goto('http://127.0.0.1:8766/editor.html?template='+tid+'&project='+pid);ready(p)
def transform(p,kind):p.locator('#organize-data').click();p.locator('#transform-kind').select_option(kind)
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
  p=b.new_page(viewport={'width':1440,'height':1000});p.on('pageerror',lambda e:errors.append(str(e)))
  load(p,'basic.grouped_bar');original=p.evaluate('JSON.stringify(project.table)')
  transform(p,'melt');p.locator('#transform-preview').click();p.locator('#transform-apply').click()
  check('Wide-to-long UI preserves all observations',p.evaluate('project.table.rows.length===12&&project.table.headers.length===3'))
  check('Template settings stay hidden in data inspector after remapping',p.locator('#specific-settings').is_hidden())
  transform(p,'pivot');p.locator('#transform-preview').click();p.locator('#transform-apply').click()
  check('Long-to-wide UI restores original data',p.evaluate('JSON.stringify(project.table)')==original)
  p.locator('#match-fields').click();p.locator('#render').click();ready(p)
  check('Reshaped data renders through original template',p.locator('#data-error').is_hidden())
  p.locator('.data-more>summary').click();check('Example download and reset remain accessible',p.locator('#example-file').is_visible() and p.locator('#load-example').is_visible());p.locator('.data-more>summary').click()
  load(p,'advanced.fan');keys=p.evaluate('spec.tables.map(t=>t.key)');check('Real multi-table project has separate navigation entries',len(keys)>1 and p.locator('[data-open-table]').count()==len(keys))
  p.locator('[data-open-table]').nth(1).click();check('Clicking table switches dataset and inspector',p.evaluate('project.active_table')==keys[1] and p.locator('#mapping-fields').is_visible())
  original_tables=p.evaluate('JSON.parse(JSON.stringify(project.tables))');original_table=p.evaluate('JSON.parse(JSON.stringify(project.table))')
  reordered=dict(headers=list(reversed(original_table['headers'])),rows=[list(reversed(r)) for r in original_table['rows']])
  import csv,io
  buf=io.StringIO();w=csv.writer(buf);w.writerow(reordered['headers']);w.writerows(reordered['rows'])
  p.locator('#import-file').set_input_files(dict(name='reordered.csv',mimeType='text/csv',buffer=buf.getvalue().encode('utf-8-sig')))
  p.wait_for_function('project.table.headers[0]==='+json.dumps(reordered['headers'][0]))
  check('Catalog fixed fields follow reordered headers',p.evaluate('project.column_mappings[project.active_table]')==list(reversed(range(len(original_table['headers'])))))
  check('Import replaces only active table',p.evaluate('JSON.stringify(project.tables['+json.dumps(keys[0])+'])')==json.dumps(original_tables[keys[0]],ensure_ascii=False,separators=(',',':')))
  p.locator('#render').click();ready(p);check('Multi-table render accepts matched import',p.locator('#data-error').is_hidden())
  p.locator('[data-open-table]').nth(0).click();transform(p,'sort');p.locator('#transform-fields [name=direction]').select_option('desc');p.locator('#transform-preview').click();p.locator('#transform-apply').click()
  check('Preparing one table preserves companion table',p.evaluate('project.tables['+json.dumps(keys[1])+'].headers')==reordered['headers'])
  p.locator('#undo').click();ready(p)
  p.locator('[data-open-table]').nth(1).click();p.evaluate('flushAutosave()');p.reload();ready(p)
  check('Active table selection survives reload',p.evaluate('project.active_table')==keys[1])
  # Ambiguous duplicate names must not guess a fixed field binding.
  p.evaluate('''()=>{project.table.headers[1]=project.table.headers[0];mappingRender();}''');p.locator('#open-mapping').click();p.locator('#match-fields').click()
  check('Duplicate column names leave ambiguous roles unbound',p.evaluate('project.column_mappings[project.active_table].filter(c=>c===-1).length>=2'))
  check('No browser JavaScript errors',not errors);b.close()
finally:(OUT/'dataflow-results.json').write_text(json.dumps(dict(checks=checks,errors=errors,project_ids=ids),ensure_ascii=False,indent=2),encoding='utf8')
