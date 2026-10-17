"""Object-continuity evidence for architecture adaptation, not a fidelity score."""
from pathlib import Path
import json,re
import xml.etree.ElementTree as ET
from . import store
import architecture_editor as editor

GEOMETRY={
    'path':('d',),'rect':('width','height','rx','ry'),
    'circle':('r',),'ellipse':('rx','ry'),
    'line':('x1','y1','x2','y2'),'polyline':('points',),'polygon':('points',),
}

def signature(e):
    tag=e.tag.split('}')[-1]
    return (tag,*(re.sub(r'\s+',' ',e.get(k,'').strip()) for k in GEOMETRY.get(tag,())))

def baseline(s):
    from . import architecture as a
    # Current-image edits compare to the immutable saved starting snapshot,
    # never a model-writable current.svg or a historical template.
    if s.get('target')=='current':
        initial=store.run(s['run_id'])['body']['initial']
        p=a.candidate({**initial,'run_id':s['run_id']})
        return (p/'base.svg').read_text(encoding='utf8'),a.read(p/'structure.json'),'current-saved-version'
    aid=s.get('source_work',{}).get('primary') or s.get('project',{}).get('asset')
    if not aid:return None,None,'no-primary'
    item=a.card(aid)
    if item.get('runtime')!='vector':return None,None,'code-template'
    p=a.asset_path(item)
    return (p/'diagram.svg').read_text(encoding='utf8'),a.read(p/'structure.json'),item['display_code']

def inspect(s,path,measurement):
    svg,structure,source=baseline(s)
    if svg is None:
        return {'baseline':source,'status':'source-review-required','blocking':[],
                'note':'代码构图须核对生成器改动与实图；未按矢量编号自动认定复用。'}
    normalized,modules,_=editor.normalize(svg,structure)
    old=ET.fromstring(normalized);new=ET.fromstring((Path(path)/'base.svg').read_text(encoding='utf8'))
    objects=lambda root:{e.get('data-asset-key'):e for e in root.iter() if e.get('data-asset-key')}
    before=objects(old);after=objects(new)
    visible={o['id'] for o in measurement['objects'] if o.get('visible',True)}
    matched={key for key in before.keys() & after.keys() if before[key].tag==after[key].tag}
    shown=matched & visible
    shapes={k for k in before if before[k].tag.split('}')[-1] in GEOMETRY}
    retained_shapes=shown & shapes
    unchanged={k for k in retained_shapes if signature(before[k])==signature(after[k])}
    blocking=[]
    selected=s.get('source_work',{}).get('primary')
    if s.get('target')!='current' and selected and s.get('project',{}).get('asset')!=selected:
        blocking.append('已重新选择主体，但当前候选仍属于旧主体；请从新主体实际底稿完成改造并重新导入，不能把旧候选记为新资产的改造。')
    if not shown:
        blocking.append('未检出仍可见的底稿对象：禁止清空、整体隐藏或替换整图后重画。请回到主体实际 SVG 做局部改造；主体不适合时重新选型。')
    elif shapes and not retained_shapes:
        blocking.append('底稿图形对象已全部删除、隐藏或替换，仅保留文字编号不足以证明沿用；请恢复并改造适用的原图形。')
    return {'baseline':source,'status':'blocked' if blocking else 'review-required',
            'original_objects':len(before),'matched_keys_and_types':len(matched),
            'visible_original_objects':len(shown),'visible_original_shapes':len(retained_shapes),
            'same_local_geometry_shapes':len(unchanged),
            'removed_or_retyped':len(before)-len(matched),'hidden_or_off_canvas':len(matched-shown),
            'new_objects':len(after.keys()-before.keys()),
            'components':[{'id':m['id'],'name':m['name'],'original':len(m['keys']),
                           'visible_retained':sum(k in shown for k in m['keys'])} for m in modules],
            'blocking':blocking,
            'note':'编号/类型/几何匹配仅为复用线索，不证明物理对象身份、遮挡、语义或视觉保真；不设固定保留比例。结合源码与并排实图核对，不能保留少量空壳来凑数。'}

def save(s,path,measurement):
    report=inspect(s,path,measurement)
    (Path(path)/'fidelity-review.json').write_text(store.encode(report),encoding='utf8')
    return report
