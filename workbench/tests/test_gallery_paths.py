"""Check live gallery images and compatibility with pre-migration HTML paths."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

WEB=Path(__file__).resolve().parents[1]
OUT=WEB/'verification/gallery-missing'
OUT.mkdir(parents=True,exist_ok=True)
BASE='http://127.0.0.1:8766'
report={'pages':[], 'legacy':{}, 'errors':[], 'failed_requests':[]}

with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
    page=browser.new_page(viewport={'width':1400,'height':950})
    page.on('pageerror',lambda error:report['errors'].append(str(error)))
    page.on('response',lambda response:report['failed_requests'].append([response.status,response.url]) if response.status>=400 else None)
    try:
        response=page.goto(BASE+'/index.html')
        assert response.headers.get('cache-control')=='no-cache'
        page.wait_for_selector('.chart-card')
        assert page.locator('#result-count').inner_text()=='147 张'
        images=page.evaluate('''async()=>{
            const paths=window.VIVID_CATALOG.cards.flatMap(c=>c.previews.flatMap(p=>[p.full,p.thumb]));
            const loaded=await Promise.all(paths.map(src=>new Promise(resolve=>{const i=new Image();i.onload=()=>resolve(i.naturalWidth>0);i.onerror=()=>resolve(false);i.src=src;})));
            return {total:paths.length,failed:paths.filter((_,i)=>!loaded[i])};
        }''')
        report['images']=images
        assert images['total']==298 and not images['failed'],images
        for number in range(1,8):
            page.locator(f'[data-page="{number}"]').first.click()
            page.evaluate('Promise.all(Array.from(document.querySelectorAll(".chart-card img")).map(i=>{i.loading="eager";return i.decode()}))')
            row=page.evaluate('''()=>({cards:document.querySelectorAll('.chart-card').length,loaded:Array.from(document.querySelectorAll('.chart-card img')).every(i=>i.complete&&i.naturalWidth>0)})''')
            row['page']=number;report['pages'].append(row)
            assert row['cards']==(3 if number==7 else 24) and row['loaded'],row
        # Simulate a browser retaining old HTML without depending on archive files.
        legacy=(WEB/'index.html').read_text(encoding='utf8').replace('frontend/','')
        page.route('**/index.html?legacy-path-test',lambda route:route.fulfill(status=200,content_type='text/html; charset=utf-8',body=legacy))
        page.goto(BASE+'/index.html?legacy-path-test');page.wait_for_selector('.chart-card')
        page.evaluate('Promise.all(Array.from(document.querySelectorAll(".chart-card img")).map(i=>{i.loading="eager";return i.decode()}))')
        assert page.locator('.chart-card').count()==24
        assert page.locator('#result-count').inner_text()=='147 张'
        assert page.locator('#gallery').evaluate('(el)=>getComputedStyle(el).display')=='grid'
        report['legacy']={'cards':24,'total':147,'styles_loaded':True}
        for path in (WEB/'frontend').iterdir():
            if path.suffix not in ['.js','.css']:continue
            response=page.request.get(BASE+'/'+path.name)
            assert response.status==200 and response.body()==path.read_bytes(),path.name
        page.locator('[data-open="advanced.radar_ridgeline"]').click()
        page.locator('#detail-image').evaluate('(i)=>i.decode()')
        assert page.locator('#detail-image').evaluate('(i)=>i.naturalWidth>0')
        assert not report['errors'] and not report['failed_requests'],report
        report['passed']=True
        print(json.dumps({'passed':True,'templates':147,'images':images['total'],'pages':len(report['pages']),'legacy_paths':'OK'},ensure_ascii=False),flush=True)
    finally:
        (OUT/'regression-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
        browser.close()
