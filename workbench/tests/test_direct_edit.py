from pathlib import Path
import json,uuid,urllib.request
from playwright.sync_api import sync_playwright
WEB=Path(__file__).resolve().parents[1];OUT=WEB/'verification/direct-edit';OUT.mkdir(exist_ok=True)
checks=[];errors=[];pid='drag-test-'+uuid.uuid4().hex
def check(name,ok):checks.append(dict(name=name,ok=bool(ok)));print(name,bool(ok),flush=True);assert ok,name
def ready(p):
 p.wait_for_function('!rendering && !liveRenderPending && (!document.getElementById("export-toggle").disabled || !document.getElementById("data-error").hidden)',timeout=180000)
 assert p.locator('#data-error').is_hidden(),p.locator('#data-error').inner_text()
def metadata(p):return json.load(urllib.request.urlopen('http://127.0.0.1:8766'+p.evaluate('lastRender.base')+'objects.json'))
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
  p=browser.new_page(viewport={'width':1600,'height':1050});p.on('pageerror',lambda e:errors.append(str(e)))
  p.goto('http://127.0.0.1:8766/editor.html?template=advanced.grouped_bar_3d&project='+pid);ready(p)
  p.frame_locator('#object-preview').locator('[data-vivid-drag]').first.wait_for()
  oid=p.evaluate("objectManifest.objects.find(o=>o.id.includes('ax0-text-')).id")
  def label():return p.frame_locator('#object-preview').locator('[id="'+oid+'"]')
  r=label().bounding_box();cx=r['x']+r['width']/2;cy=r['y']+r['height']/2
  p.mouse.move(cx,cy);check('Hover feedback',p.locator('.chart-hover').is_visible())
  p.mouse.down();p.mouse.move(cx+46,cy+25,steps=8)
  moved=label().bounding_box();check('Pointer move previews displacement',abs((moved['x']-r['x'])-46)<2)
  check('Clear selection and local toolbar',p.locator('.chart-selection').is_visible() and p.locator('#chart-mini-tools').is_visible())
  p.mouse.up();p.wait_for_function('Object.keys(project.object_edits||{}).length>0');pos=p.evaluate('project.object_edits['+json.dumps(oid)+'].props')
  check('Drag commits physical offsets',pos['offset_x']>0 and pos['offset_y']>0)
  ready(p);m=metadata(p);entry=next(o for o in m['objects'] if o['id']==oid);check('Automatic native redraw retains offsets',entry['props']['offset_x']==pos['offset_x'])
  p.locator('#undo').click();check('Undo restores position state',p.evaluate('!(project.object_edits||{})['+json.dumps(oid)+']'))
  p.locator('#redo').click();check('Redo restores drag',p.evaluate('project.object_edits['+json.dumps(oid)+'].props.offset_x')==pos['offset_x'])
  p.frame_locator('#object-preview').locator('[id="'+oid+'"]').wait_for();r=label().bounding_box();cx=r['x']+r['width']/2;cy=r['y']+r['height']/2
  p.mouse.move(cx,cy);p.mouse.down();p.mouse.move(cx+25,cy+35,steps=5);p.keyboard.press('Escape');p.mouse.up()
  check('Escape cancels drag',p.evaluate('project.object_edits['+json.dumps(oid)+'].props.offset_x')==pos['offset_x'])
  # Native palette change must dispatch render without clicking the render button.
  previous=p.evaluate('lastRender.job');palette_ids=p.evaluate('Object.keys(palettes)');chosen=[x for x in palette_ids if x!='pastel-girl']
  p.locator('#palette-select').select_option(chosen[0]);p.locator('#palette-select').select_option(chosen[-1]);ready(p)
  check('Palette redraw automatically runs',p.evaluate('lastRender.job')!=previous)
  used=json.load(urllib.request.urlopen('http://127.0.0.1:8766'+p.evaluate('lastRender.base')+'data_used.json'))
  check('Last palette wins and preserves drag',used['inputs']['settings']['palette']==chosen[-1] and used['object_edits'][oid]['props']['offset_x']==pos['offset_x'])
  p.evaluate('selectObject('+json.dumps(oid)+')');p.locator('#mini-size').fill('16');p.locator('#mini-size').press('Tab');ready(p)
  check('Local toolbar changes native font',next(o for o in metadata(p)['objects'] if o['id']==oid)['props']['fontsize']==16)
  p.evaluate('flushAutosave()');p.reload();ready(p)
  check('Reload retains drag',p.evaluate('project.object_edits['+json.dumps(oid)+'].props.offset_x')==pos['offset_x'])
  p.evaluate('selectObject('+json.dumps(oid)+')');p.wait_for_timeout(500);p.screenshot(path=str(OUT/'editor.png'),full_page=True)
  (OUT/'job.json').write_text(json.dumps(dict(job=p.evaluate('lastRender.job'),oid=oid)),encoding='utf8')
  check('No browser runtime errors',not errors);browser.close()
finally:(OUT/'ui-results.json').write_text(json.dumps(dict(checks=checks,errors=errors,project_id=pid),ensure_ascii=False,indent=2),encoding='utf8')
