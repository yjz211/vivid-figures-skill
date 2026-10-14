from pathlib import Path
import json,uuid
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'verification/hit-testing';results=[];errors=[];pids=[]
ids=['basic.line','basic.scatter_regression','advanced.cluster_heatmap','competition.radar','advanced.multi_y_gradient_hist','template.sem_violin_pearson']
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
 p=b.new_page(viewport={'width':1600,'height':1050});p.on('pageerror',lambda e:errors.append(str(e)))
 for tid in ids:
  entry={'template':tid};results.append(entry)
  try:
   pid='hit-test-sample-'+uuid.uuid4().hex;pids.append(pid)
   p.goto('http://127.0.0.1:8766/editor.html?template='+tid+'&project='+pid)
   p.wait_for_function('typeof rendering!=="undefined"&&!rendering&&lastRender!==null',timeout=120000)
   f=p.locator('#object-preview').element_handle().content_frame();f.wait_for_selector('[data-vivid-drag]')
   origin=p.locator('#object-preview').bounding_box()
   # Choose spatially distinct text: rotated ticks, axis labels, plot annotations.
   items=f.evaluate('''()=>Array.from(document.querySelectorAll('[data-vivid-drag]')).filter(el=>el.getBoundingClientRect().width>2).flatMap(el=>{let gs=Array.from(el.children).filter(n=>n.tagName==='g'&&n.hasAttribute('transform')&&n.querySelector('use,text'));if(!gs.length)gs=[el];return gs.map(g=>{const n=Array.from(g.querySelectorAll('use')).find(n=>n.getBoundingClientRect().width)||g,r=n.getBoundingClientRect();return {id:el.dataset.vividObject,x:r.left+r.width*.5,y:r.top+r.height*.5};});})''')
   sampled=[]
   for key in ['-label','-tick-','-text-','-title']:
    candidates=[i for i in items if key in i['id']]
    chosen=list(dict.fromkeys(i['id'] for i in candidates))[:2]
    sampled.extend(i for i in candidates if i['id'] in chosen)
   if not sampled:sampled=items[:4]
   matched=[]
   for point in sampled:
    p.mouse.move(origin['x']+point['x'],origin['y']+point['y']);p.wait_for_timeout(20)
    name=p.evaluate('objectManifest.objects.find(o=>o.id==='+json.dumps(point['id'])+').name')
    matched.append(p.locator('.chart-tip').is_visible() and p.locator('.chart-tip').text_content().startswith(name))
   entry['labels_checked']=len(sampled);entry['labels_matched']=sum(matched)
   assert matched and all(matched),(tid,'label hit mismatch',list(zip(sampled,matched)))
   # Check both horizontal and vertical native axis strokes where present.
   strokes=f.evaluate('''()=>Array.from(document.querySelectorAll('[data-vivid-axis-hit]')).slice(0,2).map(n=>{const q=n.getPointAtLength(n.getTotalLength()*.57),p=new DOMPoint(q.x,q.y).matrixTransform(n.getScreenCTM());return {id:n.dataset.vividObject,x:p.x,y:p.y};})''')
   for point in strokes:
    p.mouse.move(origin['x']+point['x'],origin['y']+point['y']);p.wait_for_timeout(20)
    name=p.evaluate('objectManifest.objects.find(o=>o.id==='+json.dumps(point['id'])+').name')
    assert p.locator('.chart-tip').is_visible() and p.locator('.chart-tip').inner_text().startswith(name),(tid,'axis stroke not selectable',point)
   entry['axis_strokes_checked']=len(strokes)
   # Exercise one real drag through each native SVG layout, including nested SVG.
   point=sampled[-1];p.mouse.move(origin['x']+point['x'],origin['y']+point['y']);p.mouse.down();p.mouse.move(origin['x']+point['x']+16,origin['y']+point['y']+8,steps=5);p.mouse.up()
   assert p.evaluate('!!project.object_edits?.['+json.dumps(point['id'])+']?.props.offset_x'),(tid,'drag did not commit')
   p.wait_for_function('!rendering&&!liveRenderPending&&!document.getElementById("export-toggle").disabled',timeout=120000)
   entry['drag_and_redraw']=True;entry['passed']=True
  except Exception as e:entry['passed']=False;entry['error']=str(e)
  print(tid,json.dumps(entry,ensure_ascii=False),flush=True)
 b.close()
(OUT/'sample-results.json').write_text(json.dumps(dict(results=results,errors=errors,project_ids=pids),ensure_ascii=False,indent=2),encoding='utf8')
assert all(r['passed'] for r in results) and not errors
