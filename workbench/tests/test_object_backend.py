from pathlib import Path
import sys,json,subprocess,shutil,zipfile,concurrent.futures
WEB=Path(__file__).resolve().parents[1];sys.path.insert(0,str(WEB/'editor_backend'))
from schema import sample
from object_editor import structure_guard,validate
from PIL import Image,ImageChops
OUT=WEB/'verification/object-backend';OUT.mkdir(exist_ok=True)
def run(tid):
 folder=OUT/tid;folder.mkdir(exist_ok=True);project=sample(tid)
 for src,dst in [('preview.py','source.py'),('original.py','original.py')]:shutil.copy2(WEB/'assets/sources'/tid/src,folder/dst)
 guard=structure_guard(project,folder);prefix='part0-' if tid=='template.sem_violin_pearson' else ''
 axis_id=f'vivid-{prefix}ax1-x' if tid=='advanced.cluster_heatmap' else f'vivid-{prefix}ax0-x'
 edits={axis_id:{'guard':guard,'props':{'label':'对象编辑验证','rotation':20,'fontsize':11}}}
 if tid=='basic.line':edits['vivid-ax0-legend']={'guard':guard,'props':{'ncols':2,'loc':'lower right','fontsize':11,'frame':False}}
 project['object_edits']=edits;(folder/'project.json').write_text(json.dumps(project,ensure_ascii=False),encoding='utf8')
 with (folder/'run.log').open('w',encoding='utf8') as log:r=subprocess.run([sys.executable,'-X','utf8',str(WEB/'editor_backend/worker.py'),str(folder)],stdout=log,stderr=log,timeout=240)
 assert r.returncode==0,(folder/'run.log').read_text(encoding='utf8')
 manifest=json.loads((folder/'objects.json').read_text(encoding='utf8'))
 axis=next(o for o in manifest['objects'] if o['id']==axis_id);assert axis['props']['label']=='对象编辑验证'
 svg=(folder/'figure.svg').read_text(encoding='utf8');assert axis['dom_id'] in svg
 target=folder/'standalone';target.mkdir(exist_ok=True)
 with zipfile.ZipFile(folder/'reproduce.zip') as z:
  assert all((target/n).resolve().is_relative_to(target.resolve()) for n in z.namelist());z.extractall(target)
 with (target/'run.log').open('w',encoding='utf8') as log:r=subprocess.run([sys.executable,'-X','utf8','run.py'],cwd=target,stdout=log,stderr=log,timeout=240)
 assert r.returncode==0,(target/'run.log').read_text(encoding='utf8')
 assert json.loads((target/'objects.json').read_text(encoding='utf8'))==manifest
 a=Image.open(folder/'figure.png').convert('RGB');b=Image.open(target/'figure.png').convert('RGB')
 assert a.size==b.size and ImageChops.difference(a,b).getbbox() is None
 print(tid,'native edit + standalone exact pixels passed',flush=True)
 return dict(template=tid,passed=True,checks=['对象属性生效','SVG可选对象ID正确','独立复现元数据一致','独立复现PNG逐像素一致'])
ids=['basic.line','advanced.grouped_bar_3d','advanced.cluster_heatmap','template.sem_violin_pearson']
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,ids))
for project in [dict(object_edits={'a':{'guard':'test','props':{'min':3,'max':3}}}),dict(plotly_view={'scene.camera':{'eye':{'x':float('nan')}}}),dict(object_edits={'a':{'guard':'test','props':{'exec':'bad'}}})]:
 try:validate(project);raise AssertionError('invalid input accepted')
 except ValueError:pass
(OUT/'results.json').write_text(json.dumps(dict(results=results,invalid_cases_rejected=3),ensure_ascii=False,indent=2),encoding='utf8')
