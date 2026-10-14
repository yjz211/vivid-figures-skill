from pathlib import Path
import json,urllib.request,zipfile,subprocess,sys,hashlib
from playwright.sync_api import sync_playwright
WEB=Path(__file__).resolve().parent.parent;OUT=WEB/'verification/editor-multitable';OUT.mkdir(exist_ok=True)
checks=[];errors=[]
def check(name,ok):checks.append(dict(name=name,ok=bool(ok)));assert ok,name
def ready(page):
    page.wait_for_function('!document.getElementById("export-toggle").disabled || !document.getElementById("data-error").hidden',timeout=180000)
    assert page.locator('#data-error').is_hidden(),page.locator('#data-error').inner_text()
def data(page):return json.load(urllib.request.urlopen('http://127.0.0.1:8766'+page.evaluate('lastRender.base')+'data_used.json'))
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
    page=browser.new_page(viewport={'width':1536,'height':1000},accept_downloads=True);page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8766/editor.html?template=advanced.fan');ready(page)
    check('Single-column history table supported',page.locator('#data-table th').count()==2)
    page.locator('#dataset-select').select_option('forecast')
    original=page.locator('[data-row="0"][data-col="0"]').inner_text();new=float(original)+.1
    page.locator('[data-row="0"][data-col="0"]').fill(str(new));page.locator('#dataset-select').select_option('history')
    page.locator('#dataset-select').select_option('forecast');check('Edits survive sheet switching',float(page.locator('[data-row="0"][data-col="0"]').inner_text())==new)
    check('Multisheet edit disables old exports',page.locator('#export-toggle').is_disabled())
    page.locator('#render').click();ready(page);check('Forecast edit reached renderer',data(page)['inputs']['pred_mean'][0]==new)
    with page.expect_download() as dl:page.locator('#save-project').click()
    project=OUT/'多表项目.vivid.json';dl.value.save_as(str(project));saved=json.loads(project.read_text(encoding='utf8'))
    check('Project contains all sheets',set(saved['tables'])=={'history','forecast'})
    page.locator('#export-toggle').click()
    with page.expect_download() as dl:page.locator('#export-links a').filter(has_text='完整复现包').click()
    package=OUT/'多表复现包.zip';dl.value.save_as(str(package));page.locator('#export-close').click()
    with zipfile.ZipFile(package) as z:check('ZIP exports all CSV sheets',{'tables/history.csv','tables/forecast.csv'}<=set(z.namelist()))
    page.locator('#load-example').click();page.locator('#project-file').set_input_files(str(project));page.wait_for_function('Number(project.tables.forecast.rows[0][0])==='+str(new));check('Multisheet project restores',True)
    page.goto('http://127.0.0.1:8766/editor.html?template=screenshot.cone_vortex');ready(page)
    page.locator('[data-setting="elev"]').fill('55');page.locator('[data-setting="azim"]').fill('-45')
    check('Editing camera selects custom view',not page.locator('[data-setting="view_template"]').is_checked())
    page.locator('#render').click();ready(page);check('3D custom camera settings rendered',data(page)['inputs']['settings']['elev']==55)
    page.goto('http://127.0.0.1:8766/editor.html?template=advanced.dumbbell');ready(page)
    # Same required columns, reordered through the actual UI field bindings.
    headers=page.evaluate('project.table.headers');rows=page.evaluate('project.table.rows');width=len(headers)
    reordered=[headers[::-1]]+[r[::-1] for r in rows]
    import csv
    csvpath=OUT/'反序字段.csv'
    with csvpath.open('w',encoding='utf-8-sig',newline='') as f:csv.writer(f).writerows(reordered)
    page.locator('#import-file').set_input_files(str(csvpath));page.wait_for_function('project.table.headers[0]==='+json.dumps(headers[-1]))
    for i in range(width):page.locator('[data-column-role="'+str(i)+'"]').select_option(str(width-1-i))
    page.locator('#render').click();ready(page);check('Reordered field mapping renders',True)
    page.locator('#output-image').evaluate('(el)=>el.decode()');page.screenshot(path=str(OUT/'editor-multitable.png'))
    check('No browser JavaScript errors',not errors);browser.close()
# Rerun exported multi-table package from a different directory and compare actual data & PNG.
repro=OUT/'reproduced';repro.mkdir(exist_ok=True)
with zipfile.ZipFile(package) as z:z.extractall(repro)
expected=json.loads((repro/'data_used.json').read_text(encoding='utf8'))['inputs']
r=subprocess.run([sys.executable,'-X','utf8','run.py'],cwd=repro,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf8',timeout=180)
(OUT/'reproduce.log').write_text(r.stdout,encoding='utf8');check('Downloaded ZIP runs independently',r.returncode==0)
actual=json.loads((repro/'data_used.json').read_text(encoding='utf8'))['inputs'];check('Reproduced inputs equal exported inputs',actual==expected)
for ext in ['png','svg','pdf']:check('Reproduced '+ext,(repro/('figure.'+ext)).stat().st_size>1000)
(OUT/'results.json').write_text(json.dumps(dict(checks=checks,errors=errors),ensure_ascii=False,indent=2),encoding='utf8')
print('PASS',len(checks),flush=True)
