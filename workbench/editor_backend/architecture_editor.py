"""Revisioned architecture working copies; mutations are bounded object edits."""
from pathlib import Path
from contextlib import contextmanager
import copy, json, math, os, re, sqlite3, subprocess, sys, time, uuid, zipfile, shutil
import xml.etree.ElementTree as ET
from fastapi import APIRouter
from fastapi.responses import FileResponse
from architecture_assets import architecture_root
from agent import store

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/pptx_runtime'))
from pptx_groups import resolve_ownership
router = APIRouter(prefix='/api/architecture')
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)
ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
TAGS = {'path','rect','circle','ellipse','line','polyline','polygon','text'}

def home():
    p=store.ROOT/'architecture';p.mkdir(parents=True,exist_ok=True);return p

@contextmanager
def connection():
    c=sqlite3.connect(home()/'projects.sqlite3',timeout=30)
    c.row_factory=sqlite3.Row
    c.execute('CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY,name TEXT,asset TEXT,revision INTEGER,created REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS revisions(project TEXT,revision INTEGER,edits TEXT,created REAL,PRIMARY KEY(project,revision))')
    if 'base' not in {r[1] for r in c.execute('PRAGMA table_info(revisions)')}:c.execute("ALTER TABLE revisions ADD COLUMN base TEXT NOT NULL DEFAULT ''")
    c.execute('CREATE TABLE IF NOT EXISTS links(session TEXT,project TEXT,PRIMARY KEY(session,project))')
    c.execute('CREATE TABLE IF NOT EXISTS effects(id TEXT PRIMARY KEY,result TEXT)')
    c.commit()
    try:
        with c:yield c
    finally:c.close()

def folder(pid):
    if not re.fullmatch('[a-f0-9]{32}',pid):raise ValueError('无效项目编号。')
    p=home()/pid
    if not (p/'base.svg').is_file():raise FileNotFoundError(pid)
    return p

def run(args,cwd):
    result=subprocess.run([sys.executable,*map(str,args)],cwd=cwd,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=180,env={**os.environ,'PYTHONUTF8':'1'})
    if result.returncode:
        error=result.stderr or result.stdout
        clipped=re.findall(r'ValueError: Partially clipped text ([^;]+)',error)
        if clipped:raise ValueError(f'文字 {clipped[-1]} 被裁剪边界截断，无法完整导出可编辑 PPT。请在单个图元模式搜索该编号，将文字或所在模块移回原区域，或缩短标签后重试。')
        raise ValueError('生成失败：'+error[-1800:])

def normalize(svg,structure):
    root=ET.fromstring(svg);items=[];used=set()
    def walk(node,groups):
        tag=node.tag.split('}')[-1]
        if tag in {'defs','style','metadata','title','desc','clipPath','mask'}:return
        if tag in TAGS:
            key=node.get('data-asset-key') or node.get('id') or 'edit-'+str(len(items)+1)
            if key in used:raise ValueError('重复对象编号：'+key)
            used.add(key);node.set('data-asset-key',key)
            items.append({'key':key,'tag':tag,'group_ids':groups})
            return
        for ch in node:walk(ch,groups+([node.get('id')] if tag=='g' and node.get('id') else []))
    walk(root,[])
    components,ownership,shared=resolve_ownership(items,structure)
    modules=[{'id':c['id'],'name':c['name'],'keys':[i['key'] for i in items if ownership.get(i['key'])==c['id']]} for c in components]
    modules=[m for m in modules if m['keys']]
    for i in items:
        if i['key'] not in ownership:
            modules.append({'id':'object:'+i['key'],'name':('独立文字' if i['tag']=='text' else '独立图元')+' · '+i['key'],'keys':[i['key']]})
    return ET.tostring(root,encoding='unicode'),modules,items

def movement_metadata(svg):
    """Measure baseline parents once; movable clipped subtrees retain their clip."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser=pw.chromium.launch();page=browser.new_page()
        page.set_content('<meta http-equiv="Content-Security-Policy" content="default-src \'none\';style-src \'unsafe-inline\';font-src data:;img-src data:">'+svg)
        result=page.evaluate('''() => {
          const svg=document.querySelector('svg'),inv=svg.getScreenCTM().inverse();
          const matrix=e=>{const m=inv.multiply(e.parentElement.getScreenCTM());return [m.a,m.b,m.c,m.d]};
          const groups=[...svg.querySelectorAll('g')].filter(e=>getComputedStyle(e).clipPath!=='none'&&e.querySelector('[data-asset-key]'));
          groups.forEach((e,i)=>e.setAttribute('data-editor-clip-key','clip-'+i));
          const parent=e=>e.parentElement.closest('[data-editor-clip-key]')?.getAttribute('data-editor-clip-key')||null;
          return {svg:svg.outerHTML,motion:{objects:Object.fromEntries([...svg.querySelectorAll('[data-asset-key]')].map(e=>[e.getAttribute('data-asset-key'),{matrix:matrix(e),clip:parent(e)}])),clips:groups.map(e=>({id:e.getAttribute('data-editor-clip-key'),parent:parent(e),keys:[...e.querySelectorAll('[data-asset-key]')].map(e=>e.getAttribute('data-asset-key')),matrix:matrix(e),transform:e.getAttribute('transform')||''}))}};
        }''')
        browser.close()
    return result['svg'],result['motion']

def motion_offsets(edits,motion):
    def world(e,m):
        x,y=e.get('x',0),e.get('y',0);a,b,c,d=m
        return [a*x+c*y,b*x+d*y]
    def local(v,m):
        a,b,c,d=m;det=a*d-b*c
        if abs(det)<1e-12:raise ValueError('不可逆对象变换。')
        return [(d*v[0]-c*v[1])/det,(-b*v[0]+a*v[1])/det]
    def minus(a,b):return [a[0]-b[0],a[1]-b[1]]
    vectors={k:world(edits.get(k,{}),v['matrix']) for k,v in motion['objects'].items()}
    targets={None:[0,0]};clips={}
    for g in motion['clips']:
        vs=[vectors[k] for k in g['keys']];v=vs[0]
        target=v if all(abs(w[0]-v[0])+abs(w[1]-v[1])<1e-7 for w in vs) else [0,0]
        targets[g['id']]=target;clips[g['id']]=local(minus(target,targets[g['parent']]),g['matrix'])
    leaves={k:local(minus(vectors[k],targets[v['clip']]),v['matrix']) for k,v in motion['objects'].items()}
    return clips,leaves

def replace_text(node,text):
    # Keep the first run's style and origin; only a changed label is flattened.
    first=next((e for e in node.iter() if e is not node and e.tag.split('}')[-1]=='tspan'),None)
    target=copy.deepcopy(first) if first is not None else node
    for child in list(node):node.remove(child)
    if target is not node:
        for child in list(target):target.remove(child)
        node.text=None;target.tail=None;node.append(target)
    for e in [node,target]:
        for a in ['x','y','dx','dy','rotate']:
            if e.get(a):e.set(a,re.split(r'[\s,]+',e.get(a).strip())[0])
        e.attrib.pop('textLength',None);e.attrib.pop('lengthAdjust',None)
    target.text=text

def validate(edits,p):
    if not isinstance(edits,dict):raise ValueError('编辑记录必须为对象。')
    items={i['key']:i for i in json.loads((p/'objects.json').read_text(encoding='utf8'))}
    out={}
    for key,e in edits.items():
        if key not in items or not isinstance(e,dict) or set(e)-{'x','y','text'}:raise ValueError('无效对象编辑。')
        d={}
        for a in ['x','y']:
            v=e.get(a,0)
            if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or abs(v)>100000:raise ValueError('无效位移。')
            d[a]=v
        if 'text' in e:
            t=e['text']
            if items[key]['tag']!='text' or not isinstance(t,str) or len(t)>2000 or any(ord(c)<32 for c in t):raise ValueError('文字最多 2000 字，暂支持单行。')
            d['text']=t
        out[key]=d
    return out

def svg_for(p,edits):
    root=ET.fromstring((p/'base.svg').read_text(encoding='utf8'))
    motion=json.loads((p/'motion.json').read_text(encoding='utf8'));clips,leaves=motion_offsets(edits,motion)
    for node in root.iter():
        gid=node.get('data-editor-clip-key')
        if gid:
            x,y=clips[gid]
            if abs(x)+abs(y)>1e-9:node.set('transform',f'translate({x:.12g},{y:.12g}) '+node.get('transform',''))
        key=node.get('data-asset-key')
        if key in leaves:
            x,y=leaves[key]
            if abs(x)+abs(y)>1e-9:node.set('transform',f'translate({x:.12g},{y:.12g}) '+node.get('transform',''))
        e=edits.get(node.get('data-asset-key'))
        if e is None:continue
        if 'text' in e:replace_text(node,e['text'])
    return ET.tostring(root,encoding='unicode')

@router.get('/projects')
def listing():
    with connection() as c:rows=c.execute('SELECT * FROM projects ORDER BY created DESC').fetchall()
    return {'items':[dict(r) for r in rows]}

@router.post('/projects')
def create(data:dict):
    return create_asset(data)

def create_asset(data,draft=None):
    catalog=json.loads((architecture_root()/'catalog.json').read_text(encoding='utf8'))
    card=next((a for a in catalog if data.get('asset') in [a['id'],a.get('display_code')]),None)
    if not card:raise ValueError('请选择有效架构资源。')
    pid=uuid.uuid4().hex;p=Path(draft) if draft else home()/pid;p.mkdir(parents=True)
    source=architecture_root().parent/card['directory']
    if card.get('runtime')=='vector':
        svg=(source/'diagram.svg').read_text(encoding='utf8')
        structure=json.loads((source/'structure.json').read_text(encoding='utf8'))
    else:
        run([ROOT/'scripts/prepare_architecture.py','--id',card['id'],'--out',p/'recipe'],ROOT)
        run([p/'recipe/make_figure.py','--config','example.json','--out','.','--parts'],p/'recipe')
        svg=(p/'recipe/fig.svg').read_text(encoding='utf8')
        structure=json.loads((p/'recipe/structure.json').read_text(encoding='utf8'))
    svg,modules,items=normalize(svg,structure)
    svg,motion=movement_metadata(svg)
    (p/'base.svg').write_text(svg,encoding='utf8')
    for name,obj in [('structure',structure),('modules',modules),('objects',items),('motion',motion)]:
        (p/(name+'.json')).write_text(json.dumps(obj,ensure_ascii=False),encoding='utf8')
    name=str(data.get('name') or card['display_code']+' · '+card['name'])[:180]
    if draft:return {'path':str(p),'asset':card['display_code'],'name':name,'kind':'architecture'}
    with connection() as c:
        c.execute('INSERT INTO projects VALUES(?,?,?,?,?)',(pid,name,card['display_code'],1,time.time()))
        c.execute('INSERT INTO revisions(project,revision,edits,created) VALUES(?,?,?,?)',(pid,1,'{}',time.time()))
    return load(pid)

@router.get('/projects/{pid}')
def load(pid:str,revision:int|None=None):
    p=folder(pid)
    with connection() as c:
        row=c.execute('SELECT * FROM projects WHERE id=?',(pid,)).fetchone()
        if row is None:raise FileNotFoundError(pid)
        rev=revision or row['revision']
        r=c.execute('SELECT edits,base FROM revisions WHERE project=? AND revision=?',(pid,rev)).fetchone()
        if r is None:raise FileNotFoundError('版本不存在')
    p=p/r['base'] if r['base'] else p
    if not (p/'motion.json').exists():
        svg,motion=movement_metadata((p/'base.svg').read_text(encoding='utf8'))
        (p/'base.svg').write_text(svg,encoding='utf8');(p/'motion.json').write_text(json.dumps(motion),encoding='utf8')
    return {**dict(row),'revision':rev,'edits':json.loads(r['edits']),'svg':(p/'base.svg').read_text(encoding='utf8'),'modules':json.loads((p/'modules.json').read_text(encoding='utf8')),'motion':json.loads((p/'motion.json').read_text(encoding='utf8'))}

@router.post('/projects/{pid}/save')
def save(pid:str,data:dict):
    p=folder(pid)
    with connection() as c:
        c.execute('BEGIN IMMEDIATE')
        row=c.execute('SELECT revision FROM projects WHERE id=?',(pid,)).fetchone()
        if not row:raise FileNotFoundError(pid)
        if data.get('base_revision')!=row['revision']:raise store.Conflict('另一个页面已保存新版本。本页修改仍保留，请下载本地备份，再重开项目比较；不会覆盖新版本。')
        base=c.execute('SELECT base FROM revisions WHERE project=? AND revision=?',(pid,row['revision'])).fetchone()['base']
        edits=validate(data.get('edits'),p/base if base else p)
        rev=row['revision']+1
        c.execute('INSERT INTO revisions(project,revision,edits,created,base) VALUES(?,?,?,?,?)',(pid,rev,json.dumps(edits,ensure_ascii=False),time.time(),base))
        c.execute('UPDATE projects SET revision=? WHERE id=?',(rev,pid))
    return {'id':pid,'revision':rev}

@router.post('/projects/{pid}/export')
def export(pid:str,data:dict):
    p=folder(pid);kind=data.get('format')
    if kind not in ['svg','png','pdf','pptx','zip']:raise ValueError('不支持的格式。')
    rev=data.get('revision')
    if not isinstance(rev,int):raise ValueError('导出需要明确版本。')
    with connection() as c:r=c.execute('SELECT edits,base FROM revisions WHERE project=? AND revision=?',(pid,rev)).fetchone()
    if r is None:raise FileNotFoundError('版本不存在')
    eid=uuid.uuid4().hex;dest=p/'exports'/eid;dest.mkdir(parents=True)
    base=p/r['base'] if r['base'] else p
    svg=dest/'figure.svg';svg.write_text(svg_for(base,json.loads(r['edits'])),encoding='utf8')
    (dest/'structure.json').write_bytes((base/'structure.json').read_bytes())
    for filename in ['source.zip','source-manifest.json','fidelity-review.json']:
        if (base/filename).exists():shutil.copy2(base/filename,dest/filename)
    if kind in ['png','pdf']:
        from playwright.sync_api import sync_playwright
        root=ET.fromstring(svg.read_text(encoding='utf8'));v=list(map(float,root.get('viewBox').replace(',',' ').split()))
        w=1200;h=max(1,round(w*v[3]/v[2]))
        with sync_playwright() as pw:
            browser=pw.chromium.launch();page=browser.new_page(viewport={'width':w,'height':h},device_scale_factor=2)
            page.set_content('<meta http-equiv="Content-Security-Policy" content="default-src \'none\';style-src \'unsafe-inline\';font-src data:;img-src data:"><style>html,body{margin:0}svg{display:block;width:100vw;height:100vh}</style>'+svg.read_text(encoding='utf8'))
            page.evaluate('document.fonts.ready')
            if kind=='png':page.screenshot(path=str(dest/'figure.png'))
            else:page.pdf(path=str(dest/'figure.pdf'),width=f'{w}px',height=f'{h}px',print_background=True,margin={s:'0' for s in ['top','right','bottom','left']})
            browser.close()
    if kind in ['pptx','zip']:
        run([ROOT/'scripts/export_architecture_pptx.py',svg,'--out',dest/'figure.pptx','--structure',dest/'structure.json'],ROOT)
    if kind=='zip':
        (dest/'project.json').write_text(json.dumps({'schema':'vivid-architecture-edits-v1','project':pid,'asset':load(pid)['asset'],'base_revision':rev,'edits':json.loads(r['edits'])},ensure_ascii=False),encoding='utf8')
        with zipfile.ZipFile(dest/'figure.zip','w',zipfile.ZIP_DEFLATED) as z:
            for f in dest.rglob('*'):
                if f.is_file() and f.name!='figure.zip':z.write(f,f.relative_to(dest))
    return {'revision':rev,'url':f'/api/architecture/projects/{pid}/files/{eid}/figure.{kind}'}

@router.get('/projects/{pid}/files/{eid}/{name}')
def download(pid:str,eid:str,name:str):
    if not re.fullmatch('[a-f0-9]{32}',eid) or name not in ['figure.svg','figure.png','figure.pdf','figure.pptx','figure.zip']:raise FileNotFoundError(name)
    p=folder(pid)/'exports'/eid/name
    if not p.is_file():raise FileNotFoundError(name)
    return FileResponse(p,filename=name)


def snapshot_source(pid,revision=None):
    p=folder(pid)
    with connection() as c:
        if revision is None:revision=c.execute('SELECT revision FROM projects WHERE id=?',(pid,)).fetchone()['revision']
        r=c.execute('SELECT edits,base FROM revisions WHERE project=? AND revision=?',(pid,revision)).fetchone()
    if not r:raise FileNotFoundError('版本不存在')
    return (p/r['base'] if r['base'] else p),json.loads(r['edits'])


def write_snapshot(svg,structure,dest):
    dest=Path(dest);dest.mkdir(parents=True,exist_ok=False)
    svg,modules,items=normalize(svg,structure);svg,motion=movement_metadata(svg)
    (dest/'base.svg').write_text(svg,encoding='utf8')
    for name,obj in [('structure',structure),('modules',modules),('objects',items),('motion',motion)]:
        (dest/(name+'.json')).write_text(json.dumps(obj,ensure_ascii=False),encoding='utf8')
    return dest


def commit_snapshot(source,asset,name,session,operation,pid=None,base_revision=None):
    source=Path(source)
    with connection() as c:
        c.execute('BEGIN IMMEDIATE')
        prior=c.execute('SELECT result FROM effects WHERE id=?',(operation,)).fetchone()
        if prior:return json.loads(prior['result'])
        if pid:
            p=folder(pid);head=c.execute('SELECT revision FROM projects WHERE id=?',(pid,)).fetchone()
            if not head or head['revision']!=base_revision:raise store.Conflict('绘图期间当前图已有新版本，保留候选图。')
            rev=base_revision+1;relative='bases/'+uuid.uuid4().hex;dest=p/relative
        else:
            pid=uuid.uuid4().hex;p=home()/pid;dest=p;relative='';rev=1
        dest.mkdir(parents=True)
        for f in ['base.svg','structure.json','modules.json','objects.json','motion.json']:shutil.copy2(source/f,dest/f)
        for f in ['source.zip','source-manifest.json','fidelity-review.json']:
            if (source/f).exists():shutil.copy2(source/f,dest/f)
        if rev==1:c.execute('INSERT INTO projects VALUES(?,?,?,?,?)',(pid,name,asset,rev,time.time()))
        else:c.execute('UPDATE projects SET revision=?,name=? WHERE id=?',(rev,name,pid))
        c.execute('INSERT INTO revisions(project,revision,edits,created,base) VALUES(?,?,?,?,?)',(pid,rev,'{}',time.time(),relative))
        c.execute('INSERT OR IGNORE INTO links VALUES(?,?)',(session,pid))
        result={'architecture_id':pid,'revision':rev,'name':name,'asset':asset}
        c.execute('INSERT INTO effects VALUES(?,?)',(operation,json.dumps(result,ensure_ascii=False)))
    return result


@router.get('/sessions/{sid}/projects')
def linked_projects(sid:str):
    store.session(sid)
    with connection() as c:rows=c.execute('SELECT p.* FROM projects p JOIN links l ON l.project=p.id WHERE l.session=? ORDER BY p.created',(sid,)).fetchall()
    return {'items':[dict(r) for r in rows]}


@router.post('/sessions/{sid}/projects')
def link_project(sid:str,data:dict):
    if store.session(sid).get('domain')!='architecture':raise ValueError('请选择架构图工作区。')
    pid=data['project'];load(pid)
    with connection() as c:c.execute('INSERT OR IGNORE INTO links VALUES(?,?)',(sid,pid))
    return {'id':pid}
