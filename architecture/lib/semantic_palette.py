"""Explicit semantic recoloring of SVG; no automatic role or color inference.

The palette registry and project configuration are shared with Vivid data figures.
Prepared recipes carry exact copies of vivid_config.py and palettes.json.
"""
from pathlib import Path
import importlib.util
import os
import re

PAINTS = {'fill', 'stroke', 'stop-color'}


def _config_module():
    here = Path(__file__).resolve().parent
    path = here / 'vivid_config.py'
    if not path.exists():
        path = here.parents[1] / 'original/resources/assets/shared-scripts/vivid_config.py'
    spec = importlib.util.spec_from_file_location('_vivid_architecture_config', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _paint(value):
    """RGB plus alpha; paint servers and unsupported CSS colors stay untouched."""
    value = value.strip().lower().replace('!important', '').strip()
    value = {'black':'#000000', 'white':'#ffffff', 'red':'#ff0000',
             'blue':'#0000ff', 'green':'#008000', 'gray':'#808080',
             'grey':'#808080', 'transparent':'#00000000'}.get(value, value)
    if re.fullmatch(r'#[0-9a-f]{3,4}', value):
        value = '#' + ''.join(c*2 for c in value[1:])
    if re.fullmatch(r'#[0-9a-f]{6}([0-9a-f]{2})?', value):
        return tuple(int(value[i:i+2], 16) for i in (1,3,5)), int(value[7:9],16)/255 if len(value)==9 else 1
    match = re.fullmatch(r'rgba?\(([^)]+)\)', value)
    if match:
        parts = [p.strip() for p in re.split(r'[, /]+', match[1]) if p.strip()]
        if len(parts) not in (3,4): return None
        try:
            rgb = tuple(round(float(p[:-1])*2.55) if p.endswith('%') else round(float(p)) for p in parts[:3])
            alpha = float(parts[3][:-1])/100 if len(parts)==4 and parts[3].endswith('%') else float(parts[3]) if len(parts)==4 else 1
            if any(v<0 or v>255 for v in rgb) or not 0<=alpha<=1: return None
            return rgb, alpha
        except ValueError: return None
    return None


def _styles(node):
    return dict(pair.split(':',1) for pair in (s.strip() for s in node.get('style','').split(';')) if ':' in pair)


def _explicit(node, attr):
    return next((v.strip() for k,v in reversed(list(_styles(node).items())) if k.strip()==attr), node.get(attr))


def _set_paint(node, attr, value):
    old = _explicit(node, attr) or ''
    important = ' !important' if '!important' in old else ''
    styles = [s for s in node.get('style','').split(';') if s.strip() and s.split(':',1)[0].strip()!=attr]
    styles.append(f'{attr}:{value}{important}')
    node.set(attr,value)
    node.set('style',';'.join(styles))


def apply_palette(root, config, recipe_dir=None):
    """Apply color_roles to an SVG root and return audit entries.

    Selectors match snapshot colors before any recoloring. keys/ids/colors are AND
    filters; entries within each list are OR. Color-only selectors match explicit
    declarations, while keyed selectors can override inherited paint. No geometry,
    alpha/opacity, text, font or external file is changed.
    """
    choice = config.get('palette')
    if choice == 'original': return []
    roles = config.get('color_roles')
    # No new options: avoid even loading palette code for legacy standalone copies.
    module = _config_module()
    start = config.get('palette_workspace') or os.environ.get('VIVID_WORKSPACE') or Path.cwd()
    workspace = module.workspace_root(start)
    path = workspace / '.vivid/config.json'
    project = module.load_config(workspace) if path.exists() else None
    requested = choice is not None or (project is not None and 'palette' in __import__('json').loads(path.read_text(encoding='utf-8')))
    if not roles:
        if requested: raise ValueError('Architecture palette requested without color_roles. Map semantic roles first, or use palette="original" to preserve the source.')
        return []
    if not isinstance(roles, dict): raise ValueError('color_roles must be an object keyed by semantic role name')
    settings = dict(project or {})
    if choice not in (None, 'project'):
        settings['palette'] = choice
        if choice == 'custom': settings['colors'] = config.get('colors', settings.get('colors'))
    else: settings.setdefault('palette', module.registry()['default'])
    if settings.get('palette') == 'custom':
        colors = settings.get('colors')
        if not isinstance(colors,list) or len(colors)<2 or any(not isinstance(c,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',c) for c in colors):
            raise ValueError('Custom palette requires at least two #RRGGBB colors')
    colors = module.categorical_colors(settings)
    nodes = list(root.iter())
    parents = {child:parent for parent in nodes for child in parent}
    keys = {n.get('data-asset-key') for n in nodes if n.get('data-asset-key')}
    ids = {n.get('id') for n in nodes if n.get('id')}
    def inherited(node, attr):
        while node is not None:
            value = _explicit(node,attr)
            if value is not None and value.strip()!='inherit': return value
            node = parents.get(node)
        return {'fill':'black','stroke':'none','stop-color':'black'}[attr]
    snapshot = {(node,attr):inherited(node,attr) for node in nodes for attr in PAINTS}
    proposals = {}; records = []
    for role, spec in sorted(roles.items(), key=lambda item: not (isinstance(item[1],dict) and item[1].get('preserve',False))):
        if not isinstance(spec,dict): raise ValueError(f'Invalid color role: {role}')
        preserve = spec.get('preserve',False)
        if not preserve:
            slot = spec.get('slot')
            if isinstance(slot,bool) or not isinstance(slot,int) or not 0<=slot<len(colors): raise ValueError(f'Role {role}: slot must be 0..{len(colors)-1}; slots never wrap')
            tone = spec.get('tone',0)
            if isinstance(tone,bool) or not isinstance(tone,(int,float)) or not -1<=tone<=1: raise ValueError(f'Role {role}: tone must be -1..1')
            base = _paint(colors[slot])[0]
            target = tuple(round(v+(255-v)*tone) if tone>=0 else round(v*(1+tone)) for v in base)
        selectors = spec.get('selectors')
        if not isinstance(selectors,list) or not selectors: raise ValueError(f'Role {role}: selectors must be a nonempty list')
        count = 0
        for selector in selectors:
            if not isinstance(selector,dict) or not any(selector.get(k) for k in ('keys','ids','colors')): raise ValueError(f'Role {role}: specify keys, ids or colors')
            for field,known in [('keys',keys),('ids',ids)]:
                if field in selector and (not isinstance(selector[field],list) or not selector[field] or any(not isinstance(v,str) for v in selector[field])): raise ValueError(f'Role {role}: {field} must be a nonempty string list')
                unknown = set(selector.get(field,[]))-known
                if unknown: raise ValueError(f'Role {role}: unknown {field}: {sorted(unknown)}')
            attrs = selector.get('attributes',['fill','stroke','stop-color'])
            if not isinstance(attrs,list) or not attrs or set(attrs)-PAINTS: raise ValueError(f'Role {role}: only fill, stroke and stop-color are supported')
            wanted = []
            if 'colors' in selector:
                if not isinstance(selector['colors'],list) or not selector['colors']: raise ValueError(f'Role {role}: colors must be a nonempty list')
                for color in selector['colors']:
                    parsed = _paint(color) if isinstance(color,str) else None
                    if parsed is None: raise ValueError(f'Role {role}: unsupported selector color {color!r}; use HEX or rgb()')
                    wanted.append(parsed[0])
            hits = 0
            for node in nodes:
                if 'keys' in selector and node.get('data-asset-key') not in selector['keys']: continue
                if 'ids' in selector and node.get('id') not in selector['ids']: continue
                for attr in attrs:
                    # Never invent paint on containers, text or gradient stops just
                    # because another node in the figure used the same source color.
                    if not selector.get('keys') and not selector.get('ids') and _explicit(node,attr) is None: continue
                    if attr=='stop-color' and node.tag.split('}')[-1]!='stop': continue
                    old = snapshot[node,attr]; parsed = _paint(old)
                    if parsed is None or (wanted and parsed[0] not in wanted): continue
                    value = old if preserve else ('#'+''.join(f'{v:02X}' for v in target) if parsed[1]==1 else f'rgba({target[0]},{target[1]},{target[2]},{parsed[1]:.9g})')
                    key = (node,attr)
                    if key in proposals and proposals[key][1]:
                        pass  # An explicit preserve role always wins.
                    elif preserve:
                        proposals[key] = (value,True)
                    elif key in proposals and proposals[key][0]!=value:
                        raise ValueError(f'Conflicting roles for {node.get("data-asset-key") or node.get("id") or node.tag}: {attr}')
                    else: proposals[key] = (value,False)
                    hits += 1
            if not hits: raise ValueError(f'Role {role}: selector matched no supported paint: {selector}')
            count += hits
        records.append({'type':'palette-role','role':role,'palette':module.palette_id(settings.get('palette')),'slot':None if preserve else slot,'tone':None if preserve else tone,'preserve':bool(preserve),'matched_paints':count})
    # Validate everything first; then mutate the tree once.
    for (node,attr),(value,preserve) in proposals.items():
        if not preserve: _set_paint(node,attr,value)
        elif _explicit(node,attr) in (None,'inherit'):
            # Pin inherited paint so recoloring an ancestor cannot bypass a
            # specifically protected child's semantic warning/neutral color.
            _set_paint(node,attr,value.replace('!important','').strip())
    return records
