from pathlib import Path
import json,uuid,urllib.request
from playwright.sync_api import sync_playwright
WEB=Path(__file__).resolve().parents[1];OUT=WEB/'verification/direct-edit';checks=[];errors=[];pids=[]
def check(name,ok):checks.append(dict(name=name,ok=bool(ok)));print(name,bool(ok),flush=True);assert ok,name
def ready(p):
 p.wait_for_function('!rendering && !liveRenderPending && (!document.getElementById("export-toggle").disabled || !document.getElementById("data-error").hidden)',timeout=180000)
 assert p.locator('#data-error').is_hidden(),p.locator('#data-error').inner_text()
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
  p=b.new_page(viewport={'width':1500,'height':1000});p.on('pageerror',lambda e:errors.append(str(e)))
  for tid in ['basic.line','screenshot.mesh_surface_3d']:
   pid='palette-test-'+uuid.uuid4().hex;pids.append(pid)
   p.goto('http://127.0.0.1:8766/editor.html?template='+tid+'&project='+pid);ready(p)
   palettes=p.evaluate("Object.keys(palettes).filter(id=>id!==project.settings.palette)")
   p.locator('#palette-select').select_option(palettes[0]);p.wait_for_function('rendering')
   p.locator('#palette-select').select_option(palettes[1]);p.locator('#palette-select').select_option(palettes[2]);ready(p)
   evidence=json.load(urllib.request.urlopen('http://127.0.0.1:8766'+p.evaluate('lastRender.base')+'data_used.json'))
   check(tid+' newest palette wins while render in flight',evidence['inputs']['settings']['palette']==palettes[2])
   check(tid+' export matches current state',p.evaluate('lastRender.signature===signature()'))
  check('No browser errors',not errors);b.close()
finally:(OUT/'palette-results.json').write_text(json.dumps(dict(checks=checks,errors=errors,project_ids=pids),ensure_ascii=False,indent=2),encoding='utf8')
