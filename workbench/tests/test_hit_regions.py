from pathlib import Path
import json,uuid
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'verification/hit-testing';OUT.mkdir(exist_ok=True)
checks=[];errors=[];pid='hit-test-'+uuid.uuid4().hex
def check(name,ok):checks.append(dict(name=name,ok=bool(ok)));print(name,bool(ok),flush=True);assert ok,name
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
  p=b.new_page(viewport={'width':1600,'height':1050});p.on('pageerror',lambda e:errors.append(str(e)))
  p.goto('http://127.0.0.1:8766/editor.html?template=advanced.grouped_bar_3d&project='+pid)
  p.wait_for_function('typeof rendering!=="undefined"&&!rendering&&lastRender!==null',timeout=120000)
  f=p.locator('#object-preview').element_handle().content_frame();f.wait_for_selector('[data-vivid-drag]')
  # Avoid selection tools obscuring the test surface; the tests exercise hover first.
  check('Floating tools do not obscure labels on initial load',p.locator('#chart-mini-tools').is_hidden())
  points=f.evaluate('''()=>Array.from(document.querySelectorAll('[data-vivid-drag]')).filter(el=>el.id.includes('ax0-text-')).slice(0,10).flatMap(el=>Array.from(el.querySelectorAll('use')).filter(n=>n.getBoundingClientRect().width).slice(0,4).map(n=>{const r=n.getBoundingClientRect();return {id:el.id,x:r.left+r.width*.5,y:r.top+r.height*.5};}))''')
  origin=p.locator('#object-preview').bounding_box();passed=[]
  for point in points:
   p.mouse.move(origin['x']+point['x'],origin['y']+point['y']);p.wait_for_timeout(15)
   name=p.evaluate('objectManifest.objects.find(o=>o.id==='+json.dumps(point['id'])+').name')
   passed.append(p.locator('.chart-tip').is_visible() and p.locator('.chart-tip').inner_text().startswith(name))
  check('Glyph centers hit correct labels including small decimal text',len(passed)>=30 and all(passed))
  # Check a real axis pane interior: it must no longer have an interactive owner.
  panes=f.evaluate('''()=>Array.from(document.querySelectorAll('g[id^="pane3d_"] > g[id^="patch_"] > path')).map(n=>{const b=n.getBBox(),m=n.getScreenCTM(),pt=new DOMPoint(b.x+b.width*.4,b.y+b.height*.3).matrixTransform(m);return {x:pt.x,y:pt.y,tag:n.closest('[data-vivid-object]')?.dataset.vividObject};})''')
  check('Native SVG axis groups have unique identities',f.evaluate('''()=>{const ids=Array.from(document.querySelectorAll('[id]')).map(e=>e.id);return new Set(ids).size===ids.length;}'''))
  check('3D panes do not carry axis hit identity',bool(panes) and all(not q.get('tag') for q in panes))
  q=panes[0];p.mouse.move(origin['x']+q['x'],origin['y']+q['y']);p.wait_for_timeout(30)
  check('Pane interior does not select an axis',p.locator('.chart-tip').is_hidden())
  # Native axis stroke remains selectable, and the giant rectangular hover is gone.
  q=f.evaluate('''()=>{const n=document.querySelector('#vivid-ax0-x-line path');const q=n.getPointAtLength(n.getTotalLength()*.53),p=new DOMPoint(q.x,q.y).matrixTransform(n.getScreenCTM());return {x:p.x,y:p.y};}''')
  p.mouse.move(origin['x']+q['x'],origin['y']+q['y']);p.wait_for_timeout(30)
  check('Only the actual axis line responds',p.locator('.chart-tip').inner_text().startswith('子图 1 X 轴') and p.locator('.chart-tip').is_visible())
  check('Axis hover does not draw a chart-sized rectangle',p.locator('.chart-hover').is_hidden())
  # Click the center of a glyph, then drag it using the same hit logic.
  point=points[0];p.mouse.move(origin['x']+point['x'],origin['y']+point['y']);p.mouse.down();p.mouse.move(origin['x']+point['x']+20,origin['y']+point['y']+12,steps=5);p.mouse.up()
  check('Dragging can start on the glyph itself',p.evaluate('!!project.object_edits?.['+json.dumps(point['id'])+']?.props.offset_x'))
  p.wait_for_function('!rendering&&!liveRenderPending&&!document.getElementById("export-toggle").disabled',timeout=120000)
  p.screenshot(path=str(OUT/'after.png'),full_page=True)
  p.goto('http://127.0.0.1:8766/editor.html?template=basic.line&project='+pid+'-line')
  p.wait_for_function('typeof rendering!=="undefined"&&!rendering&&lastRender!==null',timeout=120000)
  f=p.locator('#object-preview').element_handle().content_frame();f.wait_for_selector('[data-vivid-axis-hit]',state='attached')
  origin=p.locator('#object-preview').bounding_box()
  q=f.evaluate('''()=>{const n=document.querySelector('#vivid-ax0-x-line path');const q=n.getPointAtLength(n.getTotalLength()*.51),p=new DOMPoint(q.x,q.y).matrixTransform(n.getScreenCTM());return {x:p.x,y:p.y};}''')
  p.mouse.move(origin['x']+q['x'],origin['y']+q['y']);p.wait_for_timeout(30)
  check('2D axis spine remains selectable',p.locator('.chart-tip').is_visible() and p.locator('.chart-tip').inner_text().startswith('子图 1 X 轴'))
  p.mouse.move(origin['x']+q['x'],origin['y']+q['y']-10);p.wait_for_timeout(30)
  check('2D axis does not capture nearby plot area',p.locator('.chart-tip').is_hidden())
  check('No JavaScript errors',not errors);b.close()
finally:(OUT/'results.json').write_text(json.dumps(dict(checks=checks,errors=errors,project_ids=[pid,pid+'-line']),ensure_ascii=False,indent=2),encoding='utf8')
