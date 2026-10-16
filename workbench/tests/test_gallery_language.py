"""Real browser gallery language, project handoff and draft-preservation checks."""
from pathlib import Path
import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
import uuid

from playwright.sync_api import sync_playwright

WEB=Path(__file__).resolve().parents[1]
OUT=WEB/'verification/english/gallery'
BASE='http://127.0.0.1:8768'
HTTP=urllib.request.build_opener(urllib.request.ProxyHandler({}))
checks=[]
errors=[]

def request(path,data=None):
    req=urllib.request.Request(BASE+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
    with HTTP.open(req,timeout=20) as response:return json.load(response)

def check(name,condition):
    checks.append({'name':name,'passed':bool(condition)})
    print(name,bool(condition),flush=True)
    assert condition,name

def ready(page):
    page.wait_for_function('!rendering && !liveRenderPending && (!document.getElementById("export-toggle").disabled || !document.getElementById("data-error").hidden)',timeout=180000)
    assert page.locator('#data-error').is_hidden(),page.locator('#data-error').inner_text()

def wait_preview(page,selector):
    page.wait_for_function('selector=>{const image=document.querySelector(selector);return image&&!image.hidden&&image.complete&&image.naturalWidth>0}',arg=selector,timeout=15000)

def launch():
    with socket.socket() as test_socket:test_socket.bind(('127.0.0.1',8768))
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
uvicorn.run(app,host='127.0.0.1',port=8768,log_level='warning')
''',encoding='utf8')
    log=(OUT/'server.log').open('w',encoding='utf8')
    process=subprocess.Popen([sys.executable,'-B','-X','utf8',str(script),str(WEB),str(OUT)],cwd=WEB,stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    for _ in range(80):
        if process.poll() is not None:raise RuntimeError('QA service exited; see server.log')
        try:request('/api/templates');return process,log
        except Exception:time.sleep(.25)
    raise RuntimeError('QA service did not become ready')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--ui-only',action='store_true',help='Check interaction while English assets are still being built.')
    args=parser.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    service=None;log=None;completed=False
    try:
        service,log=launch()
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
            try:
                page=browser.new_page(viewport={'width':1600,'height':1050})
                page.on('pageerror',lambda error:errors.append(str(error)))
                page.goto(BASE+'/index.html')
                check('Gallery opens before editor',page.locator('#gallery').is_visible() and page.locator('#gallery-language').input_value()=='zh')
                wait_preview(page,'.card-preview img')
                original_ids=page.locator('[data-open]').evaluate_all('(els)=>els.map(el=>el.dataset.open)')
                original_swatches=page.locator('#swatches').inner_html()
                page.locator('#gallery-language').select_option('en')
                check('Gallery switches English paths and editor links',page.locator('.card-preview img').first.get_attribute('src').startswith('assets/thumbs-en/') and 'language=en' in page.locator('.card-edit-link').first.get_attribute('href'))
                check('Language preserves template order and palette',original_ids==page.locator('[data-open]').evaluate_all('(els)=>els.map(el=>el.dataset.open)') and original_swatches==page.locator('#swatches').inner_html())
                if not args.ui_only:
                    loaded=page.locator('.card-preview img').evaluate_all('async images=>{for(const image of images)image.loading="eager";return await Promise.all(images.map(image=>image.decode().then(()=>image.naturalWidth>0).catch(()=>false)))}')
                    check('English gallery images really load',all(loaded))
                page.locator('[data-open]').first.click()
                check('Detail inherits English preview and original-image URL',page.locator('#detail-language').input_value()=='en' and page.locator('#detail-image').get_attribute('src').startswith('assets/previews-en/') and 'assets/previews-en/' in page.locator('#full-image').get_attribute('href'))
                if not args.ui_only:wait_preview(page,'#detail-image')
                page.locator('#code-tab').click()
                check('Shared source explains English demo invocation','python run_demo.py --language en' in page.locator('#code-note').inner_text())
                page.locator('#detail-language').select_option('zh');wait_preview(page,'#detail-image')
                check('Detail switch also updates gallery and editor link',page.locator('#gallery-language').input_value()=='zh' and 'language=zh' in page.locator('#use-template').get_attribute('href') and not 'previews-en/' in page.locator('#detail-image').get_attribute('src'))
                page.locator('#detail-language').select_option('en')
                page.locator('#close-detail').click()
                page.goto(BASE+'/index.html')
                check('Language choice survives a fresh gallery URL',page.locator('#gallery-language').input_value()=='en')
                page.locator('#search').fill('heatmap')
                page.wait_for_function('state.query==="heatmap"')
                filtered_ids=page.locator('[data-open]').evaluate_all('(els)=>els.map(el=>el.dataset.open)')
                page.locator('#gallery-language').select_option('zh')
                check('Language preserves keyword search and result set',page.locator('#search').input_value()=='heatmap' and filtered_ids==page.locator('[data-open]').evaluate_all('(els)=>els.map(el=>el.dataset.open)'))
                page.locator('#gallery-language').select_option('en')
                page.locator('#reset').click()
                if not args.ui_only:
                    page.screenshot(path=str(OUT/'gallery-english.png'),full_page=True)
                    # Verify every full-size and thumbnail URL, including secondary variants.
                    statuses=page.evaluate('''async()=>{const paths=VIVID_CATALOG.cards.flatMap(c=>c.previews.flatMap(p=>[p.full,p.thumb])).map(p=>p.replace("assets/previews/","assets/previews-en/").replace("assets/thumbs/","assets/thumbs-en/"));const failed=[];for(let i=0;i<paths.length;i+=12){await Promise.all(paths.slice(i,i+12).map(async p=>{const response=await fetch(p);if(!response.ok||!(response.headers.get("content-type")||"").startsWith("image/"))failed.push(p);await response.arrayBuffer()}))}return {count:paths.length,failed}}''')
                    check('All English full previews and thumbnails are served',statuses['count']>=296 and not statuses['failed'])
                # A broken English resource must not silently display the Chinese preview.
                page.route('**/assets/thumbs-en/**',lambda route:route.abort())
                page.route('**/assets/previews-en/**',lambda route:route.abort())
                page.reload()
                page.locator('.card-preview .preview-unavailable').first.wait_for(state='visible')
                check('Missing English thumbnail shows a truthful placeholder',page.locator('.card-preview img').first.is_hidden() and '英文预览暂不可用' in page.locator('.card-preview .preview-unavailable').first.inner_text())
                page.locator('[data-open]').first.click()
                page.wait_for_function('document.getElementById("detail-preview-status").textContent.includes("暂不可用")')
                check('Missing English detail is not replaced with Chinese',page.locator('#detail-image').is_hidden() and page.locator('#full-image').is_hidden())
                page.locator('#detail-language').select_option('zh');wait_preview(page,'#detail-image')
                check('Switching back to Chinese recovers failed preview',page.locator('#detail-preview-status').is_hidden() and page.locator('#full-image').is_visible())
                page.unroute('**/assets/thumbs-en/**');page.unroute('**/assets/previews-en/**')
                page.locator('#close-detail').click()
                page.set_viewport_size({'width':390,'height':844})
                page.locator('#gallery-language').select_option('en')
                control=page.locator('#gallery-language').bounding_box()
                check('Gallery language control remains visible on mobile',control['x']>=0 and control['x']+control['width']<=390)
                if not args.ui_only:
                    wait_preview(page,'.card-preview img')
                    page.screenshot(path=str(OUT/'gallery-english-mobile.png'))
                page.set_viewport_size({'width':1600,'height':1050})
                project_id='gallery-new-'+uuid.uuid4().hex
                page.goto(BASE+'/editor.html?template=basic.grouped_bar&language=en&project='+project_id);ready(page)
                original=request('/api/sample?id=basic.grouped_bar')
                check('New editor project inherits selected English',page.locator('#language-select').input_value()=='en' and page.evaluate('project.settings.language')=='en')
                check('Language handoff preserves sample data and palette',page.evaluate('project.table')==original['table'] and page.evaluate('project.settings.palette')==original['settings']['palette'])
                page.evaluate('flushAutosave()')
                page.goto(BASE+'/editor.html?template=basic.grouped_bar&language=zh&project='+project_id);ready(page)
                check('Saved project language takes priority over URL',page.evaluate('project.settings.language')=='en' and page.locator('#language-select').input_value()=='en')
                old_id='gallery-legacy-'+uuid.uuid4().hex
                old=request('/api/sample?id=basic.grouped_bar');old['settings'].pop('language',None)
                request('/api/library',{'kind':'projects','id':old_id,'value':old})
                page.goto(BASE+'/editor.html?template=basic.grouped_bar&language=en&project='+old_id);ready(page)
                check('Old project without a language retains Chinese default',page.locator('#language-select').input_value()=='zh' and page.evaluate('project.settings.language||"zh"')=='zh')
                page.goto(BASE+'/editor.html?language=en')
                page.wait_for_url('**/index.html?language=en')
                check('Bare editor returns to template selection',page.locator('#gallery').is_visible() and page.locator('#gallery-language').input_value()=='en')
                check('Browser has no script errors',not errors)
                completed=True
            finally:browser.close()
    finally:
        if service:
            subprocess.run(['taskkill','/PID',str(service.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            try:service.wait(timeout=10)
            except subprocess.TimeoutExpired:service.kill()
        if log:log.close()
        (OUT/('ui-results.json' if args.ui_only else 'browser-results.json')).write_text(json.dumps({'passed':completed,'ui_only':args.ui_only,'checks':checks,'errors':errors},ensure_ascii=False,indent=2),encoding='utf8')

if __name__=='__main__':main()
