"""Editable Vivid vector recipes. Geometry is retained, never rasterized.

The default is a reusable design example, not new scientific evidence.
Labels, element attributes, component visibility/translation and custom Python edits
are supported. Structural redesign remains an explicit code/layout task.
"""
from pathlib import Path
from copy import deepcopy
from collections.abc import Mapping
import argparse, base64, json, math, re
import xml.etree.ElementTree as ET

NS='http://www.w3.org/2000/svg'
ET.register_namespace('',NS)
ET.register_namespace('xlink','http://www.w3.org/1999/xlink')
def tag(s): return '{'+NS+'}'+s
def local(e): return e.tag.split('}')[-1]
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,obj): Path(p).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')


def asset_identity(asset):
    """Native IDs first; support older already-prepared working copies."""
    ident=asset.get('id') or asset.get('asset_id') or asset.get('reference_id')
    if not ident:raise ValueError('asset.json must declare id')
    return ident


def asset_guide(recipe_dir,asset):
    path=Path(recipe_dir)/'guide.json'
    if path.exists():return read(path)
    return {k:asset[k] for k in ['name','when_to_use','avoid','preserve','adapt','visual_note'] if k in asset}

def normalize_font_families(root):
    """Quote PDF subset family names; an unquoted '+' invalidates CSS values."""
    repairs=[]
    def fixed(value):
        return ', '.join(('"'+p.strip()+'"') if '+' in p and not p.strip().startswith(('"',"'")) else p.strip() for p in value.split(','))
    for i,e in enumerate(root.iter()):
        if 'font-family' in e.attrib:
            old=e.get('font-family');new=fixed(old)
            if new!=old:e.set('font-family',new);repairs.append({'node':i,'old':old,'new':new})
        if 'font-family:' in e.get('style',''):
            e.set('style',re.sub(r'font-family\s*:\s*([^;]+)',lambda m:'font-family:'+fixed(m.group(1)),e.get('style')))
    return repairs


def source_tree(path):
    root=ET.parse(path).getroot();counter=0
    normalize_font_families(root)
    def walk(e,definitions=False):
        nonlocal counter
        definitions=definitions or local(e) in {'defs','clipPath','marker','pattern','symbol','mask'}
        if not definitions and local(e) in {'path','rect','circle','ellipse','line','polyline','polygon','text','image','use'}:
            counter+=1;e.set('data-asset-key',f'e{counter:04d}')
            if local(e)=='text':return
        for child in e:walk(child,definitions)
    walk(root)
    return root

def element_map(root):
    """Index keyed elements without silently discarding duplicate objects."""
    elements={}
    for e in root.iter():
        key=e.get('data-asset-key')
        if not key:continue
        if key in elements:
            def describe(node):return f'<{local(node)}'+(f' id={node.get("id")!r}' if node.get('id') else '')+'>'
            raise ValueError(f'Duplicate data-asset-key {key!r}: {describe(elements[key])} and {describe(e)}. Assign a unique key to each keyed element.')
        elements[key]=e
    return elements

def viewbox_size(root):
    """Read the final canvas, which customize may change independently of geometry."""
    value=root.get('viewBox','')
    try:
        values=[float(n) for n in re.split(r'[\s,]+',value.strip())]
    except ValueError:
        values=[]
    if len(values)!=4 or not all(math.isfinite(n) for n in values) or values[2]<=0 or values[3]<=0:
        raise ValueError(f'Invalid final SVG viewBox {value!r}: expected four finite numbers with positive width and height.')
    return values[2],values[3]

def translate(e,dx,dy,meta):
    # Source coords can be transformed/scaled/rotated: translate in parent coords.
    a,b,c,d,_,_=meta.get('parent_matrix',[1,0,0,1,0,0]);det=a*d-b*c
    if abs(det)<1e-12:raise ValueError('Cannot move element under singular source transform')
    tx=(d*dx-c*dy)/det;ty=(-b*dx+a*dy)/det
    e.set('transform',f'translate({tx:.8g},{ty:.8g}) '+e.get('transform',''))

def set_attr(e,key,value):
    if value is None:e.attrib.pop(key,None)
    else:e.set(key,str(value))
    # Presentation attributes must not be overridden by the source inline style.
    styles=[x for x in e.get('style','').split(';') if x.strip() and x.split(':',1)[0].strip()!=key]
    if value is not None and key in {'fill','stroke','font-family','font-size','font-weight','font-style','opacity','display'}:
        styles.append(f'{key}:{value}')
    if styles:e.set('style',';'.join(styles))
    elif 'style' in e.attrib:del e.attrib['style']

def substitute_label(e,value,meta,options):
    """Collapse per-glyph source coordinates only for the explicitly changed label."""
    first=next((x for x in e.iter() if x is not e and local(x)=='tspan'),None)
    if first is not None:
        attrs=dict(first.attrib)
        for key in ['x','y','dx','dy']:
            if key in attrs:attrs[key]=re.split(r'[\s,]+',attrs[key].strip())[0]
        for child in list(e):e.remove(child)
        e.text=None;node=ET.SubElement(e,tag('tspan'),attrs);node.text=str(value)
    else:e.text=str(value)
    # PDF-extracted fonts can be subsets. Use full supplied replacement families.
    old=meta.get('font_family','').lower()
    family=options.get('font_family') or ('Tinos' if any(x in old for x in ['times','termes','roman','cmr','serif']) and 'sans' not in old else 'Arimo')
    weight=options.get('font_weight') or ('700' if 'bold' in old or str(meta.get('font_weight')) in {'700','800','900'} else '400')
    style=options.get('font_style') or ('italic' if any(x in old for x in ['italic','oblique']) or meta.get('font_style')=='italic' else 'normal')
    if 'vividsource-' in old and not options.get('font_family') and not any(k in options for k in ['font_weight','font_style']):
        family=meta['font_family'];weight='400';style='normal'
    elif 'vividsource-carlito' in old and not options.get('font_family'):
        family='Carlito'
    for node in e.iter():
        if local(node) in {'text','tspan'}:
            set_attr(node,'font-family',family);set_attr(node,'font-weight',weight);set_attr(node,'font-style',style)
            if 'font_size' in options:set_attr(node,'font-size',options['font_size'])
    return family

def embed_full_fonts(root,font_dir,families):
    rules=[]
    for family in sorted(families):
        if family not in {'Arimo','Tinos','Carlito'}:continue
        for face,weight,style in [('Regular','400','normal'),('Bold','700','normal'),('Italic','400','italic'),('BoldItalic','700','italic')]:
            path=font_dir/f'{family}-{face}.ttf'
            if not path.exists():raise FileNotFoundError(f'Replacement font missing: {path}')
            uri=base64.b64encode(path.read_bytes()).decode()
            rules.append(f'@font-face{{font-family:"{family}";font-weight:{weight};font-style:{style};src:url(data:font/ttf;base64,{uri}) format("truetype");}}')
    if rules:ET.SubElement(root,tag('style'),{'id':'vivid-replacement-fonts'}).text='\n'.join(rules)

def component_members(asset,geometry):
    """Contained source objects form selectable vector parts; no raster crop."""
    x0,y0,w,h=geometry['viewBox'];out=[]
    known_keys={e['key'] for e in geometry['elements']}
    for part in asset['parts']:
        x,y,pw,ph=part['box'];box=[x0+x*w,y0+y*h,pw*w,ph*h];tol=max(w,h)*.004
        excluded=set(part.get('exclude_keys',[]))
        if excluded-known_keys:raise ValueError(f"Unknown excluded elements in part {part['id']}: {sorted(excluded-known_keys)}")
        keys=[]
        for e in geometry['elements']:
            if not e.get('visible') or e['key'] in excluded:continue
            bx,by,bw,bh=e['bounds']
            if bx>=box[0]-tol and by>=box[1]-tol and bx+bw<=box[0]+box[2]+tol and by+bh<=box[1]+box[3]+tol:keys.append(e['key'])
        out.append(dict(part,bounds=box,element_keys=keys,text_keys=[k for k in keys if next(e for e in geometry['elements'] if e['key']==k)['tag']=='text']))
    return out

def current_parts(mapping):
    """Use the customized registry, including explicit additions and removals."""
    if not isinstance(mapping,Mapping):raise ValueError('Customized parts must be a mapping of part names to part records.')
    parts=[]
    for key,part in mapping.items():
        if not isinstance(part,dict):raise ValueError(f'Invalid customized part {key!r}: expected a part record.')
        ident=part.get('id');keys=part.get('element_keys')
        if not isinstance(ident,str) or not ident:
            raise ValueError(f'Invalid customized part {key!r}: id must be a nonempty string.')
        if not isinstance(keys,(list,tuple)) or not all(isinstance(k,str) for k in keys):
            raise ValueError(f'Invalid customized part {key!r}: element_keys must be a list of strings.')
        parts.append(part)
    return parts

def export_parts(root,parts,geometry,out):
    folder=out/'parts';folder.mkdir(exist_ok=True);index=[]
    for p in parts:
        clone=deepcopy(root)
        elems=[e for e in geometry['elements'] if e['key'] in p['element_keys'] and e.get('visible') and (e['bounds'][2]>1e-8 or e['bounds'][3]>1e-8)]
        keep={e['key'] for e in elems}
        # Remove unselected visible source objects, retaining ancestors and definitions.
        def prune(e,definitions=False):
            definitions=definitions or local(e) in {'defs','clipPath','marker','pattern','symbol','mask'}
            for child in list(e):
                k=child.get('data-asset-key')
                primitive=local(child) in {'path','rect','circle','ellipse','line','polyline','polygon','text','image','use'}
                if not definitions and primitive and (not k or k not in keep):e.remove(child)
                else:prune(child,definitions)
        prune(clone)
        if elems:
            left=min(e['bounds'][0] for e in elems);top=min(e['bounds'][1] for e in elems)
            right=max(e['bounds'][0]+e['bounds'][2] for e in elems);bottom=max(e['bounds'][1]+e['bounds'][3] for e in elems)
            pad=3;box=[left-pad,top-pad,right-left+pad*2,bottom-top+pad*2]
        else:box=p['bounds']
        clone.set('viewBox',' '.join(map(str,box)));clone.set('width',f'{max(1,box[2])}pt');clone.set('height',f'{max(1,box[3])}pt')
        clone.set('data-component-id',p['id'])
        ET.ElementTree(clone).write(folder/f'{p["id"]}.svg',encoding='utf-8',xml_declaration=True)
        index.append(dict(p,file=f'{p["id"]}.svg',export_bounds=box,visible_element_keys=sorted(keep),empty=not bool(elems)))
    write(folder/'index.json',index)
    return index

def build(recipe_dir,config,customize=None):
    recipe_dir=Path(recipe_dir);asset=read(recipe_dir/'asset.json');geom=read(recipe_dir/'geometry.json')
    source=recipe_dir/'diagram.svg'
    # Compatibility only: newly packaged assets use diagram.svg exclusively.
    if not source.exists():source=recipe_dir/'reference/normalized-source.svg'
    if not source.exists():source=recipe_dir/'reference/source.svg'
    if not source.exists():raise FileNotFoundError(f'Asset vector diagram missing: {recipe_dir}/diagram.svg')
    root=source_tree(source);emap=element_map(root);metas={e['key']:e for e in geom['elements']}
    parts=component_members(asset,geom);by_part={p['id']:p for p in parts}
    families=set();changes=[]
    for key,value in config.get('labels',{}).items():
        if key not in emap or local(emap[key])!='text':raise ValueError(f'Unknown text element: {key}')
        options=value if isinstance(value,dict) else {'text':value}
        families.add(substitute_label(emap[key],options['text'],metas[key],options));changes.append({'type':'label','key':key,'old':metas[key].get('text'),'new':options['text']})
    for ident,patch in config.get('components',{}).items():
        if ident not in by_part:raise ValueError(f'Unknown component: {ident}')
        for key in by_part[ident]['element_keys']:
            e=emap[key]
            if patch.get('visible') is False:set_attr(e,'display','none')
            if patch.get('dx') or patch.get('dy'):translate(e,patch.get('dx',0),patch.get('dy',0),metas[key])
            for attr,value in patch.get('attributes',{}).items():set_attr(e,attr,value)
        changes.append({'type':'component','id':ident,'patch':patch})
    for key,patch in config.get('elements',{}).items():
        if key not in emap:raise ValueError(f'Unknown element: {key}')
        for attr,value in patch.items():set_attr(emap[key],attr,value)
        changes.append({'type':'element','key':key,'patch':patch})
    font_dir=recipe_dir/'fonts'
    if not font_dir.exists():font_dir=recipe_dir.parents[1]/'fonts'/'source-assets'
    if families:embed_full_fonts(root,font_dir,families)
    context={'asset':asset,'geometry':geom,'elements':emap,'parts':by_part,'config':config,'tag':tag}
    if customize:customize(root,context)
    parts=current_parts(context['parts'])
    # New or cloned objects must not overwrite each other in downstream indexes.
    element_map(root)
    from semantic_palette import apply_palette
    changes.extend(apply_palette(root,config,recipe_dir))
    w,h=viewbox_size(root);width=float(config.get('print_width',468))
    root.set('width',f'{width:g}pt');root.set('height',f'{width*h/w:g}pt')
    root.attrib.pop('data-vivid-source-asset',None)
    root.set('data-vivid-asset',asset_identity(asset))
    for node in list(root):
        if local(node)=='metadata' and node.get('id') in {'vivid-source-record','vivid-asset-record'}:root.remove(node)
    meta=ET.SubElement(root,tag('metadata'),{'id':'vivid-asset-record'})
    meta.text=json.dumps({'asset_id':asset_identity(asset),'name':asset.get('name'),'content_status':config.get('content_status','design-example'),'changes':changes,'notice':'Design example labels and values require adaptation to the current task. See ATTRIBUTION.md for derivation and rights.'},ensure_ascii=False)
    return root,asset,geom,parts,changes

def run(recipe_file,customize=None):
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--config',type=Path);ap.add_argument('--out',type=Path,default=Path('.'));ap.add_argument('--parts',action='store_true');ap.add_argument('--print-width',type=float);args=ap.parse_args()
    base=Path(recipe_file).resolve().parent;config=read(args.config or base/'example.json')
    if args.print_width:config['print_width']=args.print_width
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    root,asset,geom,parts,changes=build(base,config,customize)
    ET.ElementTree(root).write(out/'fig.svg',encoding='utf-8',xml_declaration=True)
    write(out/'config.used.json',config);write(out/'structure.json',{'asset_id':asset_identity(asset),'components':parts,'guide':asset_guide(base,asset),'changes':changes})
    if args.parts:
        if changes or customize is not None:
            # Re-measure adapted SVG before exporting moved/changed text bounds.
            from source_measure import measure_file
            updated=measure_file(out/'fig.svg');export_parts(root,parts,updated,out)
        else:export_parts(root,parts,geom,out)
    (out/'caption.txt').write_text(config.get('caption','Reusable architecture design example; adapt labels and values to the current task.'),encoding='utf-8')
    print(json.dumps({'svg':str(out/'fig.svg'),'components':len(parts),'changed_objects':len(changes)},ensure_ascii=False))
