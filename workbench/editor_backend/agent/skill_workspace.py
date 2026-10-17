"""Full Vivid sources and references, with task-local code execution and SVG handoff."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,sys,time,uuid,zipfile
import xml.etree.ElementTree as ET
from . import store,jobs
import architecture_editor as editor

ROOT=editor.ROOT
ARCHITECTURE_SKILL='channels/vivid-architecture-diagram-skill/SKILL.md'
ARCHITECTURE_CONTEXT=(ARCHITECTURE_SKILL,'architecture/COMMON.md','architecture/PALETTE.md')
TEXT={'.md','.py','.json','.txt','.svg','.csv','.tex','.toml','.yaml','.yml','.css','.js'}
BLOCKED={'workbench','workspace','.git','.venv','node_modules','__pycache__'}

def under(root,path):
    if not isinstance(path,str) or not path or Path(path).is_absolute():raise ValueError('使用根目录下的相对路径。')
    p=(root/path).resolve()
    if not p.is_relative_to(root.resolve()):raise ValueError('路径超出当前资源目录。')
    # Do not follow junctions or symlinks authored by a script.
    for parent in [p,*p.parents]:
        if parent==root.resolve():break
        if parent.is_symlink() or getattr(parent,'is_junction',lambda:False)():raise ValueError('不支持链接路径。')
    return p

def workspace(s):
    p=store.ROOT/'runs'/s['run_id']/'skill-workspace';p.mkdir(parents=True,exist_ok=True);return p.resolve()

def skill_file(path):
    p=under(ROOT,path)
    if any(part in BLOCKED for part in p.relative_to(ROOT).parts):raise ValueError('只读 Skill 内容，工作台代码、设置与其他会话不可读取。')
    return p

def read_text(p,start=1,lines=160):
    if not p.is_file() or p.suffix.lower() not in TEXT:raise ValueError('请选择文本或源码文件。')
    if p.stat().st_size>25_000_000:raise ValueError('文件过大，请读取相关源码/图元索引。')
    all_lines=p.read_text(encoding='utf8').splitlines();start=max(1,int(start));lines=max(1,min(300,int(lines)))
    text='\n'.join(f'{i+start}: {line}' for i,line in enumerate(all_lines[start-1:start-1+lines]))
    return {'path':p.name,'start':start,'total_lines':len(all_lines),'text':text[:32000],'truncated':len(text)>32000,'next_line':start+lines if start+lines<=len(all_lines) else None}

def listing(p):
    if not p.is_dir():raise ValueError('目录不存在。')
    return [{'name':f.name,'directory':f.is_dir(),'bytes':f.stat().st_size if f.is_file() else None} for f in sorted(p.iterdir()) if f.name not in BLOCKED and not f.is_symlink()][:300]

def prepare(s,a):
    from . import architecture as arch
    item=arch.card(a['asset_id']);aid=item['display_code'];role=a.get('role','primary')
    if role not in ['primary','supplement']:raise ValueError('role 使用 primary 或 supplement。')
    if aid not in s.get('seen_assets',[]):raise ValueError('先 inspect_asset 并在下一轮查看实图，再准备源码。')
    p=workspace(s);name='primary' if role=='primary' else 'references/'+aid
    previous=s.get('source_work',{})
    if role=='primary' and s.get('target')=='current':raise ValueError('续改以当前保存版本为底稿；只可准备补充资产，不可更换主体覆盖人工修改。')
    if role=='primary' and previous.get('primary'):
        name=previous.get('primary_directory','primary') if previous['primary']==aid else 'alternatives/'+aid
    dest=p/name
    if not dest.exists():editor.run([ROOT/'scripts/prepare_architecture.py','--id',aid,'--out',dest],ROOT)
    s['source_work']={**previous,**({'primary':aid,'primary_directory':name} if role=='primary' else {}),'references':list(dict.fromkeys(previous.get('references',[])+([aid] if role=='supplement' else [])))}
    return {'directory':name,'asset':arch.summary(item),'files':listing(dest),'hint':'读取 TEMPLATE.md、guide.json、example.json 和 make_figure.py。196套资产统一从 SVG 底稿出发，在 customize(root,context) 内修改已有对象，不得清空/整体隐藏后重画。新图可重新准备更合适主体，旧工作副本保留在原目录；后续使用此次返回的 directory。补充部件统一 id、defs 与模块归属。'}

def seed_current(s):
    """Preserve the exact current SVG and provenance, never regenerate manual edits."""
    if not s.get('project'):return
    from . import architecture as arch
    p=workspace(s);source=arch.candidate(s)
    for original,dest in [('base.svg','current.svg'),('structure.json','current.structure.json'),('objects.json','current.objects.json'),('motion.json','current.motion.json')]:
        if not (p/dest).exists():shutil.copy2(source/original,p/dest)
    if (source/'source.zip').exists() and not (p/'previous-source').exists():
        dest=p/'previous-source';dest.mkdir()
        with zipfile.ZipFile(source/'source.zip') as z:
            for info in z.infolist():
                if info.is_dir():continue
                target=under(dest,info.filename);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(info))
    s['source_work']={**s.get('source_work',{}),'primary':s['project']['asset'],'current':'current.svg'}

def python_paths(s,a):
    root=workspace(s);cwd=under(root,a.get('cwd','.'));path=under(root,a['path'])
    if not cwd.is_dir():raise ValueError('Python cwd 目录不存在：'+a.get('cwd','.'))
    # Keep existing task-relative calls; also accept the usual cwd/script form.
    if not path.is_file():
        local=under(cwd,a['path'])
        if local.is_file():path=local
    if path.suffix!='.py' or not path.is_file():
        examples=[p.relative_to(root).as_posix() for p in root.glob('*/*.py')][:12]
        raise ValueError('Python 脚本不存在：path='+a['path']+'，cwd='+a.get('cwd','.')+'。path 使用任务根目录相对路径，或 cwd 内相对脚本名；现有脚本示例：'+', '.join(examples))
    return root,path,cwd


def run_python(s,a):
    from . import runtime as rt
    root,path,cwd=python_paths(s,a)
    args=a.get('args',[])
    if not isinstance(args,list) or len(args)>40 or any(not isinstance(x,str) or len(x)>2000 for x in args):raise ValueError('args 应为短字符串数组。')
    exe=shutil.which('codex')
    if not exe or os.name!='nt':raise ValueError('源码运行需要本机 Windows Codex sandbox；当前环境不可用，不会退回无隔离执行。')
    sandbox={'permissionProfile':{'file_system':{'entries':[{'path':{'type':'path','path':str(root)},'access':'write'}]}},'sandboxCwd':cwd.as_uri()}
    command=[exe,'sandbox','--sandbox-state-json',json.dumps(sandbox),'--sandbox-state-disable-network','--',sys.executable,'-X','utf8',str(path),*args]
    # Only runtime variables; never pass model credentials or cloud keys to generated code.
    env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','COMSPEC','PATH','PATHEXT','LOCALAPPDATA','APPDATA','USERPROFILE','PROGRAMFILES','PROGRAMFILES(X86)','PROGRAMDATA'}}
    temp=root/'.tmp';temp.mkdir(exist_ok=True)
    env.update(PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',TEMP=str(temp),TMP=str(temp),MPLCONFIGDIR=str(temp/'matplotlib'),VIVID_WORKSPACE=str(root))
    logs=root/'execution';logs.mkdir(exist_ok=True);log=logs/(uuid.uuid4().hex+'.log');timeout=min(240,max(10,int(a.get('timeout',180))))
    with log.open('w',encoding='utf8') as out:
        p=subprocess.Popen(command,cwd=cwd,env=env,stdout=out,stderr=out,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));rt.process(s['run_id'],p);start=time.monotonic()
        try:
            while p.poll() is None:
                rt.check(s['run_id'])
                if time.monotonic()-start>timeout:raise TimeoutError('源码执行超时；工作副本与日志已保留。')
                time.sleep(.15)
            rt.check(s['run_id'])
        finally:
            if p.poll() is None:jobs.kill(p)
            rt.process(s['run_id'],None)
    text=log.read_text(encoding='utf8',errors='replace')
    if p.returncode:raise ValueError('Python 执行失败（'+str(log.relative_to(root))+'）：\n'+text[-12000:])
    return {'exit_code':p.returncode,'log':str(log.relative_to(root)).replace('\\','/'),'output':text[-18000:],'seconds':round(time.monotonic()-start,2)}

def validate_svg(svg):
    if len(svg.encode())>25_000_000 or '<!DOCTYPE' in svg.upper() or '<!ENTITY' in svg.upper():raise ValueError('SVG 超大或包含外部实体。')
    root=ET.fromstring(svg)
    if root.tag.split('}')[-1]!='svg':raise ValueError('结果根元素必须为 SVG。')
    allowed={'svg','g','defs','style','metadata','title','desc','clipPath','mask','linearGradient','radialGradient','stop','pattern','marker','use','symbol','text','tspan','path','rect','line','circle','ellipse','polygon','polyline'}
    for e in root.iter():
        tag=e.tag.split('}')[-1]
        if tag not in allowed:raise ValueError('可编辑 SVG 不支持图元：'+tag+'；不可使用脚本、外链或位图替代结构。')
        for k,v in e.attrib.items():
            key=k.split('}')[-1].lower()
            if key.startswith('on'):raise ValueError('SVG 不得包含事件脚本。')
            if key=='href' and not v.startswith('#'):raise ValueError('SVG 引用必须为内部 id。')
        css=e.get('style','')+(e.text or '' if tag=='style' else '')
        if re.search(r'@import|expression\s*\(',css,re.I):raise ValueError('SVG 不得载入外部样式。')
        for url in re.findall(r'url\(\s*[\"\']?([^\)\"\']+)',css+' '+str(e.attrib),re.I):
            if not url.startswith(('#','data:font/','data:application/font','data:application/x-font','data:application/octet-stream')):raise ValueError('SVG 仅允许内部资源与内嵌字体。')
    box=root.get('viewBox','').replace(',',' ').split()
    if len(box)!=4:raise ValueError('SVG 必须提供有效 viewBox。')
    values=list(map(float,box))
    from .architecture import finite
    for v in values:finite(v)
    if min(values[2:])<=0:raise ValueError('SVG 画布宽高必须为正。')
    return root

def bundle(s,dest):
    root=workspace(s);manifest=[];total=0
    with zipfile.ZipFile(dest/'source.zip','w',zipfile.ZIP_DEFLATED) as z:
        for f in root.rglob('*'):
            rel=f.relative_to(root)
            if not f.is_file() or any(k in {'.tmp','execution','__pycache__'} for k in rel.parts):continue
            under(root,str(rel))
            if f.suffix.lower() not in TEXT|{'.ttf','.otf','.woff','.woff2'}:continue
            size=f.stat().st_size;total+=size
            if total>160_000_000:raise ValueError('源码包过大，请移除无关临时文件。')
            z.write(f,rel.as_posix());manifest.append({'path':rel.as_posix(),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
    (dest/'source-manifest.json').write_text(store.encode({'files':manifest,'selection':s.get('source_work',{}),'bytes':total}),encoding='utf8')

def source_review(s):
    root=workspace(s);reports=[]
    for manifest in root.glob('**/.vivid/template-sources/manifest.json'):
        if 'previous-source' in manifest.relative_to(root).parts:continue
        data=json.loads(manifest.read_text(encoding='utf8'));recipe=manifest.parents[2];changed=[];missing=[]
        for name,entry in data.get('files',{}).items():
            p=under(recipe,name)
            if not p.exists():missing.append(name)
            elif hashlib.sha256(p.read_bytes()).hexdigest()!=entry['sha256']:changed.append(name)
        reports.append({'asset':data.get('display_code'),'directory':str(recipe.relative_to(root)).replace('\\','/'),'changed_files':changed,'missing_files':missing})
    result={'assets':reports,'note':'底稿差异是来源证据；不自动证明保真、实际复用或结构正确。新脚本也可能读取未修改的底稿，应结合代码与实图判断。'}
    (root/'source-review.json').write_text(store.encode(result),encoding='utf8');return result

def view(s,a):
    source=skill_file(a['path']) if a.get('scope')=='skill' else under(workspace(s),a['path'])
    dest=workspace(s)/'views'/(uuid.uuid4().hex+'.png');dest.parent.mkdir(exist_ok=True)
    if source.suffix.lower()=='.png':shutil.copy2(source,dest)
    elif source.suffix.lower()=='.svg':
        svg=source.read_text(encoding='utf8');root=validate_svg(svg);v=list(map(float,root.get('viewBox').replace(',',' ').split()));height=max(1,min(3000,round(1100*v[3]/v[2])))
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            b=pw.chromium.launch();page=b.new_page(viewport={'width':1100,'height':height})
            page.set_content('<meta http-equiv="Content-Security-Policy" content="default-src \'none\';style-src \'unsafe-inline\';font-src data:;img-src data:"><style>body{margin:0}svg{width:100vw;height:100vh}</style>'+svg);page.evaluate('document.fonts.ready');page.screenshot(path=str(dest));b.close()
    else:raise ValueError('预览支持 PNG 或 SVG；PDF可先由工作副本脚本渲染。')
    relative=str(dest.relative_to(workspace(s))).replace('\\','/');s['source_images']=s.get('source_images',[])+[relative]
    return {'viewed':a['path'],'image':relative,'hint':'下一轮模型将看到此实图，位于资产预览之后、当前候选整图之前。'}

def adopt(s,a):
    from . import architecture as arch
    root=workspace(s);svg=under(root,a['svg']).read_text(encoding='utf8');tree=validate_svg(svg)
    structure=json.loads(under(root,a['structure']).read_text(encoding='utf8'))
    if not isinstance(structure,dict) or not isinstance(structure.get('components'),list):raise ValueError('structure.json 需含 components 数组及具名部件。')
    if not structure['components']:raise ValueError('请给结构中的可移动模块命名和登记对象。')
    ids=set()
    for part in structure['components']:
        if not isinstance(part,dict) or not isinstance(part.get('id'),str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,120}',part['id']) or part['id'] in ids:raise ValueError('组件 id 须唯一，使用英文、数字、点、冒号、下划线或连字符。')
        ids.add(part['id'])
        if not isinstance(part.get('name'),str) or not part['name'].strip():raise ValueError('每个组件需要语义名称 name。')
    dest=editor.write_snapshot(svg,structure,arch.next_path(s));modules=json.loads((dest/'modules.json').read_text(encoding='utf8'))
    if not modules or len(json.loads((dest/'objects.json').read_text(encoding='utf8')))>4000:raise ValueError('结果需包含可编辑图元，最多4000个。')
    provenance=source_review(s)
    asset=s.get('source_work',{}).get('primary') or (s.get('project') or {}).get('asset')
    if not asset:raise ValueError('先选主体并 prepare_asset，再导入成图。')
    project={'path':str(dest),'asset':asset,'name':str(a.get('name') or (s.get('project') or {}).get('name') or 'Vivid 架构图')[:180],'kind':'architecture'}
    work={**s,'project':project,'dirty':True,'source_work':{**s.get('source_work',{}),'output_svg':a['svg'],'output_structure':a['structure']}}
    result=arch.render(work)
    blocked=result.get('fidelity',{}).get('blocking',[])
    if blocked:raise ValueError('底稿沿用检查未通过：'+'；'.join(blocked))
    (root/'fidelity-review.json').write_text(store.encode(result.get('fidelity',{})),encoding='utf8')
    bundle(work,dest)
    s.update(project=project,dirty=True,source_work=work['source_work'])
    return {**result,'modules':len(modules),'source_bundle':True,'source_review':provenance,'hint':'下一轮对照主体与成图，核对实际沿用对象、字号字重、区域比例、线宽、色彩对比和留白。检查结果不是保真通过；仅保留编号、空壳、从头绘图后声明来源均不符合资产改造要求。'}

DESCRIPTIONS=[
 {'name':'read_skill','description':'读取 Vivid 架构通道及按需引用资料。参数 path(相对整个Skill包根目录，如architecture/COMMON.md、architecture/PALETTE.md), start?:行号, lines?:最多300。默认channels/vivid-architecture-diagram-skill/SKILL.md；<SKILL>始终指整个包根目录，不是channels/vivid-architecture-diagram-skill。不允许读取工作台会话/设置。'},
 {'name':'list_skill','description':'列出Skill资源目录。path相对Skill根目录，默认architecture。可查全部指南、原生脚本、字体、数据图与技术图专题。'},
 {'name':'prepare_asset','description':'将已查看资产的完整源码、字体、配置、部件资料与来源底稿准备到任务工作副本。参数 asset_id,role:primary或supplement。沿用返回的directory，不硬编码外部路径。主体不适合时可重新选主体，旧副本保留；续改当前图只能补充资产。矢量资产修改已有对象，按需融合局部，禁止清空或隐藏底稿另画整图。'},
 {'name':'list_source','description':'列出本任务工作副本目录。path默认.。当前图修改使用current.svg/current.structure.json；旧源码如存在位于previous-source，不能覆盖当前手动修改。'},
 {'name':'read_source','description':'读取当前工作副本文件。path,start?,lines?；SVG可能含很长的内嵌字体，优先读取geometry/labels/源码，或用脚本提取局部。'},
 {'name':'view_source','description':'查看完整参考/部件/生成图的真实PNG或SVG。参数path,scope?:workspace（默认）或skill。下一轮提供实图，可核对补充部件与代码输出。'},
 {'name':'write_source','description':'写入工作副本的文本文件（Python、JSON、SVG、Markdown）。参数 path,content。已有底稿优先patch_source；新脚本应解析实际底稿并局部修改，不能重置SVG根节点、清空或整体隐藏原对象后另画整图。'},
 {'name':'patch_source','description':'精确修改源码。参数path,old,new；old必须唯一匹配。可读完整原函数后局部替换。修改make_figure.py/customize或实际SVG，不限于标签和位置。'},
 {'name':'run_python','description':'在本机隔离环境实际执行工作副本Python。参数path（任务相对路径；也接受cwd内脚本名），cwd?(相对任务根，默认.),args?:字符串数组,timeout?:秒<=240。例：path=primary/make_figure.py,cwd=primary,args=[--config,example.json,--out,output,--parts]。完整支持已安装Python绘图/布局/SVG库，不调用模型生成shell。修复非零退出码后重跑。输出fig.svg及structure.json。'},
 {'name':'adopt_source','description':'将生成SVG与具名部件结构导入候选、渲染真实图、归档源码。参数svg,structure（任务相对路径）,name?。支持复杂路径、渐变、字体与任意模块结构；禁止脚本、外链、整图位图。导入后须查看实际图，仍可通过源码反复改造和再次导入；已有项目从当前SVG续改。'},
]

def execute(s,name,a):
    if name=='read_skill':return read_text(skill_file(a.get('path',ARCHITECTURE_SKILL)),a.get('start',1),a.get('lines',160))
    if name=='list_skill':return listing(skill_file(a.get('path','architecture')))
    if name=='prepare_asset':return prepare(s,a)
    if name=='view_source':return view(s,a)
    root=workspace(s)
    if name=='list_source':return listing(under(root,a.get('path','.')))
    if name=='read_source':return read_text(under(root,a['path']),a.get('start',1),a.get('lines',160))
    if name in ['write_source','patch_source']:
        p=under(root,a['path'])
        if p.suffix.lower() not in TEXT:raise ValueError('仅支持源码/配置/文档文本文件。')
        if name=='write_source':content=a['content']
        else:
            content=p.read_text(encoding='utf8');old=a['old']
            if not old or content.count(old)!=1:raise ValueError('old 需在文件中唯一匹配；请先读取当前源码。')
            content=content.replace(old,a['new'],1)
        if not isinstance(content,str) or len(content.encode())>25_000_000:raise ValueError('文件内容无效或过大。')
        p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content,encoding='utf8');return {'path':a['path'],'bytes':p.stat().st_size}
    if name=='run_python':return run_python(s,a)
    if name=='adopt_source':return adopt(s,a)
    raise ValueError('未知源码工具：'+name)

def skill_context():
    """Load the architecture channel, not the router or file-host A/B workflow."""
    return '\n\n'.join('--- '+name+' ---\n'+skill_file(name).read_text(encoding='utf8') for name in ARCHITECTURE_CONTEXT)
