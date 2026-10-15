"""Click successive actual glyphs with the selection toolbar left open."""
from pathlib import Path
import json,uuid,os
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'verification/hit-coordinate';OUT.mkdir(exist_ok=True)
results=[];errors=[];ids=[]
def ready(p):p.wait_for_function('typeof rendering!=="undefined"&&!rendering&&!liveRenderPending&&lastRender!==null&&!document.getElementById("export-toggle").disabled',timeout=120000)
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
  p=b.new_page(viewport={'width':1400,'height':950},device_scale_factor=1.5);p.on('pageerror',lambda e:errors.append(str(e)))
  for tid in ['advanced.radar_ridgeline','basic.grouped_bar','advanced.grouped_bar_3d']:
   pid='coords-test-'+uuid.uuid4().hex;ids.append(pid)
   p.goto(os.environ.get('VIVID_TEST_URL','http://127.0.0.1:8766')+'/editor.html?template='+tid+'&project='+pid);ready(p)
   f=p.locator('#object-preview').element_handle().content_frame();f.wait_for_selector('[data-vivid-drag]')
   for scale in [1,.8,1.25]:
    p.evaluate('(v)=>document.body.style.zoom=v',scale);p.wait_for_timeout(80)
    points=f.evaluate('''()=>Array.from(document.querySelectorAll('[data-vivid-drag]')).flatMap(el=>Array.from(el.querySelectorAll('use')).filter(n=>n.getBoundingClientRect().width).slice(0,1).map(n=>{const r=n.getBoundingClientRect();return {id:el.id,x:r.left+r.width/2,y:r.top+r.height/2};}))''')
    origin=p.locator('#object-preview').bounding_box();miss=[];occluded=[];count=0
    for q in points:
     x=origin['x']+q['x']*scale;y=origin['y']+q['y']*scale
     if not(0<x<1400 and 0<y<950):continue
     owner=p.evaluate('([x,y])=>document.elementFromPoint(x,y)?.id',[x,y])
     if owner!='object-preview':occluded.append(dict(id=q['id'],owner=owner))
     p.mouse.click(x,y);count+=1
     if p.evaluate('selectedObject')!=q['id']:miss.append(q['id'])
    after=p.locator('#object-preview').bounding_box()
    outline=p.locator('.chart-selection').bounding_box()
    target=f.evaluate('(id)=>document.getElementById(id).getBoundingClientRect().toJSON()',p.evaluate('selectedObject'))
    aligned=abs(outline['x']-(origin['x']+target['x']*scale-4))<2 and abs(outline['y']-(origin['y']+target['y']*scale-4))<2
    row=dict(template=tid,scale=scale,clicks=count,misses=miss,occluded=occluded,aligned_outline=aligned,stable_frame=all(abs(origin[k]-after[k])<.1 for k in origin))
    results.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
    assert not miss and not occluded and row['stable_frame'] and aligned
   p.evaluate('document.body.style.zoom=1');p.wait_for_timeout(80)
   framebox=p.locator('#object-preview').bounding_box();toolbar=p.locator('#chart-mini-tools').bounding_box()
   assert toolbar['y']+toolbar['height']<=framebox['y']
   if tid=='advanced.radar_ridgeline':
    p.screenshot(path=str(OUT/'fixed-selected.png'))
    # Drag selected glyph and then select a different label with toolbar present.
    q=f.evaluate('''()=>{const el=document.querySelector('[data-vivid-drag] use');const r=el.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2,id:el.closest('[data-vivid-drag]').id}}''')
    x=framebox['x']+q['x'];y=framebox['y']+q['y'];p.mouse.move(x,y);p.mouse.down();p.mouse.move(x+14,y+8,steps=5);p.mouse.up();ready(p)
    assert p.evaluate('(id)=>Math.abs(project.object_edits[id].props.offset_x)>0',q['id'])
    p.locator('#mini-close').click();assert p.locator('#chart-mini-tools').is_hidden()
    f=p.locator('#object-preview').element_handle().content_frame()
    assert p.locator('#palette-select').is_visible()
  assert not errors;print('PASS: successive glyph clicks, no overlay occlusion, stable frame, drag and close',flush=True);b.close()
finally:(OUT/'fixed-results.json').write_text(json.dumps(dict(results=results,errors=errors,project_ids=ids),ensure_ascii=False,indent=2),encoding='utf8')
