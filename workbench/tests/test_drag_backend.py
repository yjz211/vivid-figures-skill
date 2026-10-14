from pathlib import Path
import sys,json,subprocess,shutil,zipfile
WEB=Path(__file__).resolve().parents[1];sys.path.insert(0,str(WEB/'editor_backend'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from object_editor import offset_text,start,mpl_edit,structure_guard,validate
from schema import sample
from PIL import Image,ImageChops
OUT=WEB/'verification/direct-edit/backend';OUT.mkdir(parents=True,exist_ok=True)
checks=[]
def check(name,ok):checks.append(dict(name=name,ok=bool(ok)));print(name,bool(ok),flush=True);assert ok,name
for dpi in [72,144,300]:
 for kind in ['text','3d','xlabel','title','suptitle','annotation']:
  fig=plt.figure(figsize=(6,5),dpi=dpi);ax=fig.add_subplot(projection='3d' if kind=='3d' else None)
  if kind=='text':t=ax.text(.3,.5,'offset test')
  elif kind=='3d':t=ax.text(.3,.4,.5,'offset test')
  elif kind=='xlabel':t=ax.set_xlabel('offset test')
  elif kind=='title':t=ax.set_title('offset test')
  elif kind=='suptitle':t=fig.suptitle('offset test')
  else:t=ax.annotate('offset test',xy=(.15,.2),xytext=(.3,.5),arrowprops={'arrowstyle':'->'})
  fig.canvas.draw();renderer=fig.canvas.get_renderer()
  # Register a zero offset for 3D to measure its projected extent consistently.
  offset_text(t,fig,0,0);before=t.get_window_extent(renderer).frozen()
  offset_text(t,fig,12,9);fig.canvas.draw();after=t.get_window_extent(renderer).frozen()
  if kind!='annotation':check(f'{kind} physical offset at {dpi} DPI',abs((after.x0-before.x0)-12*dpi/72)<.15 and abs((after.y0-before.y0)+9*dpi/72)<.15)
  else:check(f'Annotation data anchor remains fixed at {dpi} DPI',t.xy==(.15,.2))
  for ext in ['png','svg','pdf']:fig.savefig(OUT/f'{kind}-{dpi}.{ext}',bbox_inches='tight')
  plt.close(fig)
# A native composite figure and 3D figure must replay the edits from their packages.
for tid in ['basic.line','advanced.grouped_bar_3d','template.sem_violin_pearson']:
 folder=OUT/tid;folder.mkdir(exist_ok=True)
 for src,dst in [('preview.py','source.py'),('original.py','original.py')]:shutil.copy2(WEB/'assets/sources'/tid/src,folder/dst)
 p=sample(tid);axis='vivid-part0-ax0-x-label' if tid.startswith('template.') else 'vivid-ax0-x-label'
 # SEM's first native subplot might have no x label; choose an existing annotation from prior metadata.
 if tid.startswith('template.'):
  prior=json.loads((WEB/'verification/object-backend'/tid/'objects.json').read_text(encoding='utf8'))
  axis=next(o['id'] for o in prior['objects'] if o['kind']=='text' and 'text-' in o['id'])
 p['object_edits']={axis:{'guard':structure_guard(p,folder),'props':{'offset_x':18,'offset_y':12}}}
 (folder/'project.json').write_text(json.dumps(p,ensure_ascii=False),encoding='utf8')
 with (folder/'render.log').open('w',encoding='utf8') as log:r=subprocess.run([sys.executable,'-X','utf8',str(WEB/'editor_backend/worker.py'),str(folder)],stdout=log,stderr=log,timeout=180)
 assert r.returncode==0,(folder/'render.log').read_text(encoding='utf8')
 m=json.loads((folder/'objects.json').read_text(encoding='utf8'));check(tid+' applies offset',next(o for o in m['objects'] if o['id']==axis)['props']['offset_x']==18)
 target=folder/'standalone';target.mkdir(exist_ok=True)
 with zipfile.ZipFile(folder/'reproduce.zip') as z:
  assert all((target/n).resolve().is_relative_to(target.resolve()) for n in z.namelist());z.extractall(target)
 with (target/'run.log').open('w',encoding='utf8') as log:r=subprocess.run([sys.executable,'-X','utf8','run.py'],cwd=target,stdout=log,stderr=log,timeout=180)
 assert r.returncode==0,(target/'run.log').read_text(encoding='utf8')
 a=Image.open(folder/'figure.png').convert('RGB');b=Image.open(target/'figure.png').convert('RGB')
 check(tid+' package pixel equality',a.size==b.size and ImageChops.difference(a,b).getbbox() is None)
(OUT/'results.json').write_text(json.dumps(dict(checks=checks),ensure_ascii=False,indent=2),encoding='utf8')
