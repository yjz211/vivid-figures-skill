"""Explicit reference-system / bundled-OFL font profiles for this asset."""
from pathlib import Path
import base64,hashlib,json
import xml.etree.ElementTree as ET
from fontTools.ttLib import TTFont

ROOT=Path(__file__).resolve().parent
NS='http://www.w3.org/2000/svg'


def apply_font_profile(d,mode='reference-system'):
    profile=json.loads((ROOT/'font_profile.json').read_text(encoding='utf-8'))
    if mode not in {'reference-system','portable'}:raise ValueError('Unknown font profile: '+mode)
    pack=ROOT/'fonts'
    if not pack.exists():pack=ROOT.parents[1]/'fonts'
    manifest=json.loads((pack/'manifest.json').read_text(encoding='utf-8')) if mode=='portable' else None
    files={e['file']:e for e in manifest['files']} if manifest else {}
    root_family=d.root.get('font-family','')
    found={};css=[];used={}
    for e in d.root.iter(f'{{{NS}}}text'):
        family=e.get('font-family',root_family).split(',')[0].strip(' "\'')
        role=next((key for key,value in profile['roles'].items() if family in value['source_aliases']),None)
        if role is None:raise ValueError(f'Unmapped font {family!r}; describe its role in font_profile.json')
        style=e.get('font-style','normal');weight=e.get('font-weight','normal')
        bold=weight=='bold' or (weight.isdigit() and int(weight)>=600)
        key=(role,style,bold)
        if key not in found:
            spec=profile['roles'][role]
            if mode=='reference-system':
                from matplotlib import font_manager
                family=spec['reference_family']
                prop=font_manager.FontProperties(family=[family],style=style,weight='bold' if bold else 'normal')
                path=Path(font_manager.findfont(prop,fallback_to_default=False))
                selected=family
            else:
                face=('bold-' if bold else '')+('italic' if style=='italic' else 'regular')
                relative=spec['portable_faces'].get(face)
                if not relative:raise ValueError(f'No portable {role} font face for {face}')
                path=pack/relative
                digest=hashlib.sha256(path.read_bytes()).hexdigest()
                if digest!=files[relative]['sha256']:raise ValueError('Font resource hash mismatch: '+relative)
                selected='VividPortable'+role.title()
                payload=base64.b64encode(path.read_bytes()).decode('ascii')
                css.append(f'@font-face{{font-family:"{selected}";font-style:{style};font-weight:{700 if bold else 400};src:url(data:font/ttf;base64,{payload}) format("truetype");}}')
            with TTFont(path) as f:
                name=f['name'].getDebugName(6);cmap=set(f.getBestCmap())
                found[key]={'role':role,'family':selected,'postscript_name':name,'style':style,
                  'weight':700 if bold else 400,'source_file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                  'embedding_rights_fsType':f['OS/2'].fsType,'cmap':cmap}
            used[key]=set()
        data=found[key];text=''.join(e.itertext())
        chars={ord(ch) for ch in text if not ch.isspace()}
        missing=chars-data['cmap']
        if missing:raise ValueError(f"{data['family']} lacks glyphs: "+''.join(chr(n) for n in sorted(missing)))
        used[key]|=chars
        for node in e.iter():
            if node.tag not in {f'{{{NS}}}text',f'{{{NS}}}tspan'}:continue
            node.set('font-family',data['family'])
            styles=[item for item in node.get('style','').split(';') if item.strip() and item.split(':',1)[0].strip()!='font-family']
            if styles:node.set('style',';'.join(styles))
            else:node.attrib.pop('style',None)
    if css:ET.SubElement(d.defs,f'{{{NS}}}style').text='\n'.join(css)
    records=[{k:v for k,v in data.items() if k!='cmap'}|{'checked_codepoints':sorted(used[key])} for key,data in found.items()]
    report={'profile':mode,'silent_fallback_allowed':False,'svg_embeds_font_files':mode=='portable',
            'roles':records,'note':'Reference-system SVG needs the named local fonts; portable SVG embeds unmodified OFL fonts. Portable fonts are an explicit alternative, not identical to the reference typography.'}
    ET.SubElement(d.root,f'{{{NS}}}metadata',{'id':'vivid-font-profile'}).text=json.dumps(report,ensure_ascii=False)
    return report
