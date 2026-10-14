from pathlib import Path
import json,uuid
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'verification/studio';OUT.mkdir(exist_ok=True)
checks=[];errors=[];ids=[]
def check(name,ok):
 checks.append(dict(name=name,ok=bool(ok)));print(name,bool(ok),flush=True);assert ok,name
def ready(p):
 p.wait_for_function('typeof rendering!=="undefined"&&!rendering&&!liveRenderPending&&lastRender!==null&&!document.getElementById("export-toggle").disabled',timeout=120000)
def load(p,tid):
 pid='studio-test-'+uuid.uuid4().hex;ids.append(pid)
 p.goto('http://127.0.0.1:8766/editor.html?template='+tid+'&project='+pid);ready(p)
 return pid
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
  p=b.new_page(viewport={'width':1440,'height':1000});p.on('pageerror',lambda e:errors.append(str(e)))
  pid=load(p,'basic.grouped_bar')
  chart=p.locator('.canvas-panel').bounding_box();table=p.locator('.data-panel').bounding_box()
  check('Canvas above data, inspector on right',chart['y']<table['y'] and chart['width']>900 and p.locator('.settings-panel').bounding_box()['x']>chart['x'])
  check('Chart settings by default, object controls hidden',p.locator('#palette-select').is_visible() and not p.locator('#object-fields').is_visible())
  initial=p.evaluate('JSON.stringify(project.table)')
  p.locator('#organize-data').click();p.locator('#transform-kind').select_option('sort');p.locator('#transform-fields [name=column]').select_option('1');p.locator('#transform-fields [name=direction]').select_option('desc');p.locator('#transform-preview').click()
  check('Transform preview does not modify source table',p.evaluate('JSON.stringify(project.table)')==initial)
  check('Transform preview presents complete result dimensions', '4 行 × 4 列' in p.locator('#transform-result').inner_text())
  p.locator('#transform-apply').click()
  check('Sort is committed and stale exports disabled',p.evaluate('project.table.rows[0][1]')==92.1 and p.locator('#export-toggle').is_disabled())
  check('Data inspector opens after transform',p.locator('#mapping-fields').is_visible() and not p.locator('#palette-select').is_visible())
  p.locator('#undo').click();ready(p);check('Undo restores data exactly',p.evaluate('JSON.stringify(project.table)')==initial)
  p.locator('#redo').click();ready(p);check('Redo replays sort',p.evaluate('project.table.rows[0][1]')==92.1)
  p.locator('#open-mapping').click()
  content='方法C,指标,方法B,本文方法\n6,新的甲,4,8\n7,新的乙,5,9\n'
  p.locator('#import-file').set_input_files(dict(name='reordered.csv',mimeType='text/csv',buffer=content.encode('utf-8-sig')))
  p.wait_for_function('project.table.headers[0]==="方法C"')
  check('Import maps reordered columns by identity',p.evaluate('project.mapping.category===1&&JSON.stringify(project.mapping.values)==="[3,2,0]"'))
  p.locator('#render').click();ready(p)
  check('Imported data renders with original template',p.locator('#data-error').is_hidden())
  content='组别,实验量,对照量,标准差\n甲,8,4,1\n乙,9,5,2\n'
  p.locator('#import-file').set_input_files(dict(name='new-columns.csv',mimeType='text/csv',buffer=content.encode('utf-8-sig')))
  p.wait_for_function('project.table.headers[0]==="组别"')
  check('Unknown imported columns are left unbound',p.evaluate('project.mapping.category===-1&&project.mapping.values.length===0'))
  p.locator('#match-fields').click()
  check('Suggestion picks numeric series and excludes error column',p.evaluate('project.mapping.category===0&&JSON.stringify(project.mapping.values)==="[1,2]"'))
  p.locator('#render').click();ready(p)
  p.locator('#organize-data').click();p.locator('#transform-kind').select_option('filter');p.locator('#transform-fields [name=column]').select_option('1');p.locator('#transform-fields [name=operator]').select_option('gte');p.locator('#transform-fields [name=value]').fill('9');p.locator('#transform-preview').click()
  check('Filter preview shows retained row', '1 行 × 4 列' in p.locator('#transform-result').inner_text())
  p.locator('#transform-fields [name=value]').fill('8');check('Changed transform options invalidate preview',p.locator('#transform-apply').is_disabled());p.locator('#transform-close').click()
  check('Closing transform leaves source intact',p.evaluate('project.table.rows.length')==2)
  f=p.locator('#object-preview').element_handle().content_frame();f.wait_for_selector('[data-vivid-drag]')
  q=f.evaluate('''()=>{const el=document.querySelector('[data-vivid-drag]');const r=el.getBoundingClientRect();return {id:el.id,x:r.left+r.width/2,y:r.top+r.height/2}}''')
  origin=p.locator('#object-preview').bounding_box();p.mouse.click(origin['x']+q['x'],origin['y']+q['y'])
  check('Clicking actual SVG text opens object inspector',p.locator('#object-fields').is_visible() and not p.locator('#mapping-fields').is_visible())
  p.mouse.move(origin['x']+q['x'],origin['y']+q['y']);p.mouse.down();p.mouse.move(origin['x']+q['x']+20,origin['y']+q['y']+10,steps=4);p.mouse.up();ready(p)
  check('Dragging still saves physical offsets',p.evaluate('Object.values(project.object_edits||{}).some(e=>Math.abs(e.props.offset_x||0)>0)'))
  f=p.locator('#object-preview').element_handle().content_frame();f.locator('svg').press('Escape');check('Escape returns to chart settings',p.locator('#palette-select').is_visible())
  p.locator('#palette-select').select_option(index=0);ready(p);check('Palette still automatically rerenders',p.locator('#export-toggle').is_enabled())
  p.evaluate('flushAutosave()');saved=p.evaluate('JSON.stringify([project.table,project.mapping,project.object_edits])')
  p.reload();ready(p);check('Table mapping and edits survive project reload',p.evaluate('JSON.stringify([project.table,project.mapping,project.object_edits])')==saved)
  original=p.locator('.data-panel').bounding_box()['height'];p.locator('.data-resizer').focus();p.keyboard.press('ArrowUp');check('Data panel height adjustable by keyboard',p.locator('.data-panel').bounding_box()['height']>original)
  p.locator('#fold-data').click();check('Folding data expands canvas',p.locator('.canvas-panel').bounding_box()['height']>chart['height']);p.locator('#show-data').click()
  p.locator('#fold-project').click();p.locator('#fold-settings').click();check('Folding side panels widens canvas',p.locator('.canvas-panel').bounding_box()['width']>1300);p.locator('#show-project').click();p.locator('#show-settings').click()
  p.screenshot(path=str(OUT/'editor-wide.png'),full_page=True)
  p.set_viewport_size({'width':1100,'height':800});check('Laptop viewport has no horizontal overflow',p.evaluate('document.documentElement.scrollWidth<=innerWidth'));p.screenshot(path=str(OUT/'editor-laptop.png'),full_page=True)
  p.set_viewport_size({'width':390,'height':844});check('Phone viewport has no horizontal overflow',p.evaluate('document.documentElement.scrollWidth<=innerWidth'));p.screenshot(path=str(OUT/'editor-phone.png'),full_page=True)
  p.set_viewport_size({'width':1440,'height':1000});load(p,'advanced.grouped_bar_3d');check('3D template renders in new workspace',p.locator('#data-error').is_hidden())
  load(p,'template.sem_violin_pearson')
  check('Multi-table navigator exposes every contract table',p.locator('[data-open-table]').count()==p.evaluate('spec.tables.length'))
  if p.locator('[data-open-table]').count()>1:
   keys=p.evaluate('spec.tables.map(t=>t.key)');p.locator('[data-open-table]').nth(1).click();check('Navigator switches active table and mapping together',p.evaluate('project.active_table')==keys[1] and p.locator('#mapping-fields').is_visible())
  check('No browser JavaScript errors',not errors);b.close()
finally:
 (OUT/'results.json').write_text(json.dumps(dict(checks=checks,errors=errors,project_ids=ids),ensure_ascii=False,indent=2),encoding='utf8')
