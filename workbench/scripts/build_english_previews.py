"""Build Chinese or English gallery previews from unchanged downloadable template demos.

Run with workbench/.venv Python. The renderer branches in each run_demo.py are
retained. Intermediate bundles, logs and cache records stay in verification.
"""
from pathlib import Path
import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile

from PIL import Image, ImageOps

WEB=Path(__file__).resolve().parents[1]
OUT=WEB/'verification/gallery-english'
CJK=re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]')

# This observer wraps actual saves before the existing runner captures them.
# It neither changes source data nor redraws the chart using another renderer.
OBSERVER=r'''from pathlib import Path
import json,runpy,sys
import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
from matplotlib.text import Text
import plotly.graph_objects as go
root=Path(__file__).resolve().parent
captures=[]
def save_record(kind,path,texts,originals,fonts=()):
    captures.append({'kind':kind,'path':str(path),'texts':list(dict.fromkeys(t for t in texts if t)),
                     'originals':list(dict.fromkeys(t for t in originals if t)), 'fonts':list(fonts)})
    (root/'captured-display.json').write_text(json.dumps(captures,ensure_ascii=False),encoding='utf8')
real_save=Figure.savefig
def mpl_save(fig,*args,**kwargs):
    result=real_save(fig,*args,**kwargs)
    artists=[t for t in fig.findobj(match=Text) if t.get_visible()]
    save_record('matplotlib',args[0] if args else kwargs.get('fname'),
                [t.get_text() for t in artists],[getattr(t,'_vivid_source_text',t.get_text()) for t in artists],
                [{'text':t.get_text(),'families':t.get_fontfamily(),'size_pt':t.get_fontsize(),
                  'weight':t.get_fontweight(),'style':t.get_fontstyle()} for t in artists if t.get_text()])
    return result
Figure.savefig=mpl_save
real_write=go.Figure.write_image
def strings(value):
    if isinstance(value,str):return [value]
    if hasattr(value,'tolist'):value=value.tolist()
    if isinstance(value,(list,tuple)):return [t for v in value for t in strings(v)]
    return []
def plotly_display_texts(fig):
    texts=[]
    def walk(node):
        if isinstance(node,dict):
            for key,value in node.items():
                if key in ('text','name','ticktext','hovertext','label'):texts.extend(strings(value))
                elif key=='title' and isinstance(value,str):texts.append(value)
                elif key not in ('x','y','z','values','customdata','ids','source','target','labels','parents'):walk(value)
        elif isinstance(node,list):
            for value in node:walk(value)
    payload=fig.to_plotly_json();walk(payload)
    for trace in fig.data:
        raw=getattr(trace,'labels',None)
        if raw is not None:
            template=getattr(trace,'texttemplate',None) or ''
            info=getattr(trace,'textinfo',None)
            if '%{label}' in template or (not template and (info is None or 'label' in info)):
                texts.extend(strings(raw))
    return texts

plotly_originals={}
sys.path[:0]=[str(root),str(root/'_utils')]
from _utils import figure_language as language_helper
real_localize_plotly=language_helper.localize_plotly
def observe_localize_plotly(fig,*args,**kwargs):
    originals=plotly_originals.setdefault(id(fig),plotly_display_texts(fig))
    for trace in fig.data:
        for field in ('labels','x','y','z'):
            originals.extend(strings(getattr(trace,field,None)))
    return real_localize_plotly(fig,*args,**kwargs)
language_helper.localize_plotly=observe_localize_plotly

def plotly_save(fig,*args,**kwargs):
    texts=plotly_display_texts(fig)
    originals=plotly_originals.get(id(fig),list(texts))
    originals.extend(str(n) for n in getattr(fig,'_vivid_source_names',{}).values() if n)
    fonts=[]
    def font_walk(node,path='figure'):
        if isinstance(node,dict):
            for key,value in node.items():
                if key.endswith('font') and isinstance(value,dict):
                    fonts.append({'scope':path+'.'+key,'families':[part.strip() for part in (value.get('family') or '').split(',') if part.strip()], 'size_pt':value.get('size')})
                font_walk(value,path+'.'+key)
        elif isinstance(node,list):
            for index,value in enumerate(node):font_walk(value,path+'.'+str(index))
    font_walk(fig.to_plotly_json())
    save_record('plotly',args[0] if args else kwargs.get('file'),texts,originals,fonts)
    return real_write(fig,*args,**kwargs)
go.Figure.write_image=plotly_save
sys.argv=[str(root/'run_demo.py'),'--language','__VIVID_LANGUAGE__','--labels',str(root/'english-labels.input.json')]
runpy.run_path(str(root/'run_demo.py'),run_name='__main__')
'''


def digest(data):return hashlib.sha256(data).hexdigest()
def read_json(path):return json.loads(path.read_text(encoding='utf8'))
def write_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    temporary.replace(path)
def map_hash(labels):return digest(json.dumps(labels,ensure_ascii=False,sort_keys=True).encode())
def catalog_cards():
    text=(WEB/'assets/catalog.js').read_text(encoding='utf8')
    return json.loads(text[text.index('=')+1:].strip().rstrip(';'))['cards']
def effective_labels(labels,originals):
    # A bounded label/value annotation can use a mapped label as its prefix.
    observed=set(originals)
    return {key:labels[key] for key in sorted(labels) if any(key in text for text in observed)}
def valid_outputs(record):
    return bool(record.get('images')) and all((WEB/image['preview']).is_file() and
        digest((WEB/image['preview']).read_bytes())==image['preview_sha256'] and
        (WEB/image['thumbnail']).is_file() and
        digest((WEB/image['thumbnail']).read_bytes())==image['thumbnail_sha256'] for image in record['images'])


def font_environment(language,records):
    """Fingerprint the selected font files, including every installed weight.

    Paths plus content hashes detect replacement in place (for example adding
    a real MiSans Bold TTF) even when source and family names do not change.
    """
    from matplotlib import font_manager
    helper_path=WEB/'editor_backend/_utils'
    sys.path.insert(0,str(helper_path))
    try:
        from figure_language import font_candidates
        families={name for generic in ('sans-serif','serif','monospace')
                  for name in font_candidates(language,generic)}
    finally:
        sys.path.remove(str(helper_path))
    for record in records:
        for stack in record.get('font_family_counts',{}):
            families.update(name.strip() for name in stack.split(',')
                            if name.strip() and name!='(renderer default)')
    wanted={family.casefold() for family in families}
    file_hashes={};entries={}
    for font in font_manager.fontManager.ttflist:
        if font.name.casefold() not in wanted:continue
        path=Path(font.fname).resolve()
        if not path.is_file():continue
        key=path.as_posix()
        if key not in file_hashes:file_hashes[key]=digest(path.read_bytes())
        identity=(key,font.name,str(font.weight),font.style)
        entries[identity]={'family':font.name,'weight':font.weight,'style':font.style,
                           'path':key,'sha256':file_hashes[key]}
    return {'families':sorted(families),'files':[entries[key] for key in sorted(entries)]}


def build_case(card,labels,label_hash,timeout,force,language,font_environment_hash):
    tid=card['id'];folder=OUT/tid;folder.mkdir(parents=True,exist_ok=True)
    cache_path=folder/'build-result.json';start=time.monotonic()
    record={'id':tid,'name':card['display_name'],'expected_images':len(card['previews']),
            'language':language,'map_sha256':label_hash,'cached':False}
    observer=OBSERVER.replace('__VIVID_LANGUAGE__',language)
    try:
        bundle=WEB/card['bundle'];bundle_hash=digest(bundle.read_bytes())
        with zipfile.ZipFile(bundle) as archive:
            source=archive.read('preview.py')
            assert source==(WEB/card['source_path']).read_bytes(),'Bundle preview differs from gallery source'
            source_hash=digest(source)
            helper_hash=digest(b''.join(name.encode()+archive.read(name) for name in sorted(archive.namelist())
                                        if name.startswith('_utils/') or name in ('gallery_theme.py','run_demo.py')))
            # Config label metadata may change independently of a rendered template.
            # Include data/resource payloads, but compare labels by their observed usage.
            resources_hash=digest(b''.join(name.encode()+archive.read(name) for name in sorted(archive.namelist())
                if not name.startswith('_utils/') and not name.endswith(('.md','.diff'))
                and name not in ('preview.py','original.py','run_demo.py','gallery_theme.py',
                                 'metadata.json','.vivid/config.json','LICENSE','requirements.txt')))
            config=json.loads(archive.read('.vivid/config.json'))
            config.pop('english_labels',None)
            record['bundle_sha256']=bundle_hash
            basis={'source_sha256':source_hash,'helper_sha256':helper_hash,
                   'resources_sha256':resources_hash,'config_sha256':map_hash(config),
                   'observer_sha256':digest(observer.encode()),'preview_paths':card['previews'],
                   'font_environment_sha256':font_environment_hash}
            record.update(basis)
            if not force and cache_path.is_file():
                previous=read_json(cache_path)
                same_basis=all(previous.get(key)==value for key,value in basis.items())
                observed=previous.get('observed_originals',[])
                unchanged_map=(language=='zh' or previous.get('map_sha256')==label_hash or
                    (previous.get('status') in ('ready','needs_translation') and
                     previous.get('effective_map_sha256')==map_hash(effective_labels(labels,observed))))
                if same_basis and unchanged_map and valid_outputs(previous):
                    previous.update(cached=True,map_sha256=label_hash,bundle_sha256=bundle_hash)
                    write_json(cache_path,previous)
                    return previous
            for name in archive.namelist():
                if not (folder/name).resolve().is_relative_to(folder.resolve()):raise ValueError('Unsafe bundle path: '+name)
            archive.extractall(folder)
        write_json(folder/'english-labels.input.json',labels)
        (folder/'_observe_render.py').write_text(observer,encoding='utf8',newline='\n')
        # Old capture logs are replaced so failed reruns cannot look successful.
        write_json(folder/'captured-display.json',[])
        with (folder/'render.log').open('w',encoding='utf8') as log:
            process=subprocess.Popen([sys.executable,'-B','-X','utf8',str(folder/'_observe_render.py')],cwd=folder,
                stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            try:code=process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                if os.name=='nt':subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True,
                    creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                else:process.kill()
                process.wait();raise TimeoutError(f'Render exceeded {timeout} seconds')
        record['exit_code']=code
        render_log=(folder/'render.log').read_text(encoding='utf8')
        record['missing_glyph_warnings']=list(dict.fromkeys(line.strip() for line in render_log.splitlines()
            if re.search(r'Glyph \d+.*missing from font',line)))
        record['font_warnings']=list(dict.fromkeys(line.strip() for line in render_log.splitlines()
            if re.search(r'findfont:|Font family .*not found|Glyph \d+.*missing from font',line)))
        if code:
            raise RuntimeError(render_log[-2600:])
        captures=read_json(folder/'captured-display.json')
        texts=list(dict.fromkeys(t for capture in captures for t in capture['texts']))
        originals=list(dict.fromkeys(t for capture in captures for t in capture['originals']))
        record['display_texts']=texts
        record['observed_originals']=originals
        record['effective_map_sha256']=map_hash(effective_labels(labels,originals))
        family_counts={}
        for capture in captures:
            for font in capture.get('fonts',[]):
                family=', '.join(font.get('families',[])) or '(renderer default)'
                family_counts[family]=family_counts.get(family,0)+1
        record['font_family_counts']=dict(sorted(family_counts.items()))
        record['untranslated']=sorted(set(t for t in texts if CJK.search(t))) if language=='en' else []
        output=folder/'output';result_path=output/'result.json'
        if tid=='advanced.grouped_radial_bar':
            produced=[output/'fig_grouped_radial_bar.png']
        else:
            result=read_json(result_path)
            if result.get('status')!='ok':raise RuntimeError('Runner reported '+str(result))
            produced=[output/name for name in result.get('exports',[])]
        record['rendered_images']=len(produced)
        if len(produced)!=len(card['previews']):
            record.update(status='image_count_mismatch',error=f'Catalog expects {len(card["previews"])} images; runner produced {len(produced)}',exports=[str(p) for p in produced])
        else:
            images=[]
            for image,expected in zip(produced,card['previews']):
                if not image.is_file():raise FileNotFoundError(str(image))
                preview=WEB/('assets/previews-en' if language=='en' else 'assets/previews')/Path(expected['full']).name
                thumbnail=WEB/('assets/thumbs-en' if language=='en' else 'assets/thumbs')/Path(expected['thumb']).name
                preview.parent.mkdir(parents=True,exist_ok=True);thumbnail.parent.mkdir(parents=True,exist_ok=True)
                # Full previews are the native runner output, copied without resampling.
                preview_temporary=preview.with_suffix(preview.suffix+'.tmp')
                shutil.copyfile(image,preview_temporary)
                preview_temporary.replace(preview)
                with Image.open(WEB/expected['thumb']) as old_thumb:thumb_size=old_thumb.size
                with Image.open(image) as original:
                    original.load();pixels=original.size
                    if min(pixels)<100:raise ValueError('Unexpectedly small output '+str(pixels))
                    converted=original.convert('RGBA');background=Image.new('RGBA',converted.size,'white');background.alpha_composite(converted)
                    small=ImageOps.contain(background.convert('RGB'),thumb_size,Image.Resampling.LANCZOS)
                    canvas=Image.new('RGB',thumb_size,'white');canvas.paste(small,((thumb_size[0]-small.width)//2,(thumb_size[1]-small.height)//2))
                    thumbnail_temporary=thumbnail.with_suffix(thumbnail.suffix+'.tmp')
                    canvas.save(thumbnail_temporary,format='WEBP',quality=88)
                    thumbnail_temporary.replace(thumbnail)
                images.append({'preview':preview.relative_to(WEB).as_posix(),'thumbnail':thumbnail.relative_to(WEB).as_posix(),
                    'pixels':list(pixels),'thumbnail_pixels':list(thumb_size),'preview_sha256':digest(preview.read_bytes()),'thumbnail_sha256':digest(thumbnail.read_bytes())})
            record.update(status='needs_translation' if record['untranslated'] else 'ready',images=images)
    except Exception as error:
        record.update(status='failed',error=str(error))
    record['seconds']=round(time.monotonic()-start,2)
    write_json(cache_path,record)
    return record


def summarize(records,label_hash,language):
    counts={key:sum(r.get('status')==key for r in records.values()) for key in ('ready','needs_translation','failed','image_count_mismatch')}
    unknown={}
    for record in records.values():
        for text in record.get('untranslated',[]):unknown.setdefault(text,[]).append(record['id'])
    family_counts={}
    for record in records.values():
        for family,count in record.get('font_family_counts',{}).items():family_counts[family]=family_counts.get(family,0)+count
    return {'language':language,'palette':'pastel-girl','templates':len(records),'map_sha256':label_hash,
            'font_family_counts':dict(sorted(family_counts.items())),
            'templates_with_missing_glyph_warnings':sum(bool(r.get('missing_glyph_warnings')) for r in records.values()),
            'templates_with_font_warnings':sum(bool(r.get('font_warnings')) for r in records.values()),
            'counts':counts,'images':sum(len(r.get('images',[])) for r in records.values()),
            'untranslated':dict(sorted(unknown.items())),
            'cases':sorted(records.values(),key=lambda r:r['id'])}


def main():
    global OUT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--language',choices=('zh','en'),default='en',help='Preview language; default en preserves previous invocation behavior')
    parser.add_argument('--only',nargs='+',help='Render or retry selected template IDs only')
    parser.add_argument('--labels',type=Path,default=WEB/'assets/english-labels.json')
    parser.add_argument('--workers',type=int,default=2,choices=(1,2,3))
    parser.add_argument('--timeout',type=int,default=240)
    parser.add_argument('--force',action='store_true')
    args=parser.parse_args()
    OUT=WEB/('verification/gallery-english' if args.language=='en' else 'verification/gallery-chinese')
    cards=catalog_cards();ids={c['id'] for c in cards}
    if args.only and set(args.only)-ids:parser.error('Unknown template IDs: '+', '.join(set(args.only)-ids))
    labels=read_json(args.labels) if args.labels.is_file() else {}
    if not isinstance(labels,dict) or any(not isinstance(k,str) or not isinstance(v,str) for k,v in labels.items()):parser.error('English labels must be a JSON string-to-string map')
    label_hash=map_hash(labels);OUT.mkdir(parents=True,exist_ok=True)
    write_json(OUT/'labels-snapshot.json',labels)
    records={}
    for card in cards:
        cache=OUT/card['id']/'build-result.json'
        if cache.is_file():records[card['id']]=read_json(cache)
    fonts=font_environment(args.language,records.values())
    font_environment_hash=map_hash(fonts)
    write_json(OUT/'font-environment.json',dict(fonts,sha256=font_environment_hash))
    selected=[c for c in cards if not args.only or c['id'] in args.only]
    print(json.dumps({'language':args.language,'selected':len(selected),'workers':args.workers,'map_sha256':label_hash,'mapped_labels':len(labels),'font_environment_sha256':font_environment_hash},ensure_ascii=False),flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures={pool.submit(build_case,card,labels,label_hash,args.timeout,args.force,args.language,font_environment_hash):card['id'] for card in selected}
        for index,future in enumerate(concurrent.futures.as_completed(futures),1):
            result=future.result();records[result['id']]=result
            write_json(OUT/'report.json',summarize(records,label_hash,args.language))
            print(json.dumps({'done':index,'total':len(selected),'id':result['id'],'status':result['status'],'cached':result.get('cached',False),'untranslated':len(result.get('untranslated',[])),'seconds':result.get('seconds',0)},ensure_ascii=False),flush=True)
    summary=summarize(records,label_hash,args.language);write_json(OUT/'report.json',summary)
    print(json.dumps({'counts':summary['counts'],'images':summary['images'],'unknown_strings':len(summary['untranslated']),'report':str(OUT/'report.json')},ensure_ascii=False),flush=True)
    selected_ready=all(records[card['id']]['status']=='ready' for card in selected)
    raise SystemExit(0 if selected_ready and (args.only or len(records)==len(cards)) else 1)

if __name__=='__main__':main()
