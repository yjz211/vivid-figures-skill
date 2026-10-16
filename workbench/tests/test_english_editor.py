"""Real browser language switch, dragging, palette and reload on an isolated API."""
from pathlib import Path
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request
import uuid

from playwright.sync_api import sync_playwright

WEB=Path(__file__).resolve().parents[1]
OUT=WEB/'verification/english/browser'
BASE='http://127.0.0.1:8767'
HTTP=urllib.request.build_opener(urllib.request.ProxyHandler({}))
checks=[]
errors=[]


def request(path):
    with HTTP.open(BASE+path,timeout=15) as response:
        return json.load(response)


def check(name,okay):
    checks.append({'name':name,'passed':bool(okay)})
    print(name,bool(okay),flush=True)
    assert okay,name


def ready(page):
    page.wait_for_function('!rendering && !liveRenderPending && (!document.getElementById("export-toggle").disabled || !document.getElementById("data-error").hidden)',timeout=180000)
    assert page.locator('#data-error').is_hidden(),page.locator('#data-error').inner_text()


def evidence(page):
    return request(page.evaluate('lastRender.base')+'data_used.json')


def metadata(page):
    return request(page.evaluate('lastRender.base')+'objects.json')


def launch_service():
    # Never replace a service already owned by the user or another test.
    with socket.socket() as test_socket:
        test_socket.bind(('127.0.0.1',8767))
    script=OUT/'qa_server.py'
    script.write_text('''from pathlib import Path
import os,sys
root=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve()
sys.path.insert(0,str(root/'editor_backend'))
os.environ['VIVID_AGENT_HOME']=str(out/'workspace')
import server,library
from agent import jobs
server.JOBS=out/'jobs';jobs.JOBS=out/'jobs';library.ROOT=out/'library'
from agent_server import app
import uvicorn
uvicorn.run(app,host='127.0.0.1',port=8767,log_level='warning')
''',encoding='utf8')
    log=(OUT/'server.log').open('w',encoding='utf8')
    process=subprocess.Popen([sys.executable,'-B','-X','utf8',str(script),str(WEB),str(OUT)],
        cwd=WEB,stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    (OUT/'service.json').write_text(json.dumps({'pid':process.pid,'url':BASE}),encoding='utf8')
    for _ in range(80):
        if process.poll() is not None:raise RuntimeError('QA service exited; see server.log')
        try:
            request('/api/templates')
            return process,log
        except Exception:time.sleep(.25)
    raise RuntimeError('QA service did not become ready')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    service=None
    service_log=None
    completed=False
    project_id='english-ui-'+uuid.uuid4().hex
    try:
        service,service_log=launch_service()
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
            try:
                page=browser.new_page(viewport={'width':1600,'height':1050})
                page.on('pageerror',lambda error:errors.append(str(error)))
                page.goto(BASE+'/editor.html?template=basic.grouped_bar&project='+project_id)
                ready(page)
                check('Default chart language is Chinese',page.locator('#language-select').input_value()=='zh')
                initial=page.evaluate('JSON.parse(JSON.stringify(project.table))')
                job=page.evaluate('lastRender.job')
                page.locator('#language-select').select_option('en')
                ready(page)
                check('English switch automatically rerenders',page.evaluate('lastRender.job')!=job and evidence(page)['inputs']['settings']['language']=='en')
                check('Switch preserves uploaded source table',page.evaluate('project.table')==initial)
                # Select an actual translated category label and drag it with the pointer.
                oid=page.evaluate("objectManifest.objects.find(o=>o.kind==='text'&&o.id.includes('-x-tick-')&&o.props.visible!==false).id")
                label=page.frame_locator('#object-preview').locator('[id="'+oid+'"]')
                label.wait_for()
                box=label.bounding_box();cx=box['x']+box['width']/2;cy=box['y']+box['height']/2
                page.mouse.move(cx,cy)
                page.mouse.down();page.mouse.move(cx+25,cy+15,steps=7);page.mouse.up()
                page.wait_for_function('Object.keys(project.object_edits||{}).length>0')
                ready(page)
                props=page.evaluate('project.object_edits['+json.dumps(oid)+'].props')
                check('English label drag commits offsets',props['offset_x']>0 and props['offset_y']>0)
                moved=next(o for o in metadata(page)['objects'] if o['id']==oid)
                check('Native rendering replays English drag',moved['props']['offset_x']==props['offset_x'])
                page.locator('[data-inspector-tab="chart"]').click()
                page.locator('#palette-select').select_option('blue-sky')
                ready(page)
                check('Palette switch preserves English language and position',evidence(page)['inputs']['settings']['language']=='en' and evidence(page)['object_edits'][oid]['props']==props)
                page.locator('#language-select').select_option('zh')
                ready(page)
                objects=metadata(page)
                check('Chinese switch keeps stable text identity and offset',any(o['id']==oid and o['props'].get('offset_x')==props['offset_x'] for o in objects['objects']) and oid not in objects.get('skipped',[]))
                page.locator('#language-select').select_option('en')
                ready(page)
                page.evaluate('flushAutosave()')
                page.reload();ready(page)
                check('Saved language survives reload',page.locator('#language-select').input_value()=='en' and evidence(page)['inputs']['settings']['language']=='en')
                check('Saved palette and drag survive reload',page.locator('#palette-select').input_value()=='blue-sky' and evidence(page)['object_edits'][oid]['props']==props)
                check('Repeated language switches leave source data unchanged',page.evaluate('project.table')==initial)
                texts=[o['props'].get('text',o['props'].get('label','')) for o in metadata(page)['objects']]
                check('Final editable labels are English',not any(re.search('[\u3400-\u9fff]',t) for t in texts))
                check('No browser script errors',not errors)
                page.screenshot(path=str(OUT/'editor-english.png'),full_page=True)
                (OUT/'final-project.json').write_text(json.dumps(page.evaluate('project'),ensure_ascii=False,indent=2),encoding='utf8')
                completed=True
            finally:browser.close()
    finally:
        if service and service.poll() is None:
            if os.name=='nt':subprocess.run(['taskkill','/PID',str(service.pid),'/T','/F'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
            else:service.terminate();service.wait(timeout=15)
        if service_log:service_log.close()
        (OUT/'browser-results.json').write_text(json.dumps({'passed':completed and all(c['passed'] for c in checks) and not errors,'checks':checks,'errors':errors,'project_id':project_id},ensure_ascii=False,indent=2),encoding='utf8')


if __name__=='__main__':main()
