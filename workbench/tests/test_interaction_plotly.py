from pathlib import Path
import json,urllib.request
from playwright.sync_api import sync_playwright
WEB=Path(__file__).resolve().parents[1];OUT=WEB/'verification/interactions';checks=[];errors=[]
def check(name,value):checks.append(dict(name=name,ok=bool(value)));print(name,bool(value),flush=True);assert value,name
def ready(p):
 p.wait_for_function('!document.getElementById("export-toggle").disabled || !document.getElementById("data-error").hidden',timeout=180000)
 assert p.locator('#data-error').is_hidden(),p.locator('#data-error').inner_text()
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True,args=['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  p=b.new_page(viewport={'width':1500,'height':1000});p.on('pageerror',lambda e:errors.append(str(e)))
  p.goto('http://127.0.0.1:8766/editor.html?template=screenshot.mesh_surface_3d');ready(p)
  p.locator('#native-preview').click();frame=p.frame_locator('#plotly-preview');frame.locator('.plotly-graph-div').wait_for()
  f=p.locator('#plotly-preview').element_handle().content_frame();f.wait_for_function("document.querySelector('.plotly-graph-div')._fullLayout!==undefined")
  f.evaluate("Plotly.relayout(document.querySelector('.plotly-graph-div'),{'scene.camera':{eye:{x:2.3,y:0.5,z:1.2},up:{x:0,y:0,z:1},center:{x:0,y:0,z:0}}})")
  p.wait_for_function("project.plotly_view?.['scene.camera']?.eye?.x===2.3")
  check('Interactive camera enters project',p.evaluate("project.plotly_view['scene.camera'].eye.x===2.3"))
  check('Camera makes export stale',p.locator('#export-toggle').is_disabled())
  p.locator('#undo').click();check('Camera undo',p.evaluate("!project.plotly_view?.['scene.camera']"));p.locator('#redo').click()
  p.locator('#render').click();ready(p)
  manifest=json.load(urllib.request.urlopen('http://127.0.0.1:8766'+p.evaluate('lastRender.base')+'objects.json'))
  check('Camera reaches export renderer',manifest['view']['scene.camera']['eye']['x']==2.3)
  p.evaluate('flushAutosave()');p.reload();ready(p)
  check('Camera survives reload',p.evaluate("project.plotly_view['scene.camera'].eye.x===2.3"))
  p.locator('#object-select').select_option('vivid-title');p.locator('[data-object-prop="text"]').fill('交互曲面测试');p.locator('[data-object-prop="text"]').press('Tab');p.locator('#render').click();ready(p)
  check('Title edits saved',p.evaluate("project.object_edits['vivid-title'].props.text==='交互曲面测试'"))
  (OUT/'plotly-job.json').write_text(json.dumps(dict(job=p.evaluate('lastRender.job'))),encoding='utf8')
  p.screenshot(path=str(OUT/'plotly-editor.png'),full_page=True)
  check('Plotly UI no JavaScript errors',not errors);b.close()
finally:(OUT/'plotly-results.json').write_text(json.dumps(dict(checks=checks,errors=errors),ensure_ascii=False,indent=2),encoding='utf8')
