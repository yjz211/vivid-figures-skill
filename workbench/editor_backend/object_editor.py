"""Declarative edits to native figures. No user code is evaluated here.

The original figure is retained; SVG gids expose its own objects to the browser.
Structure fingerprints intentionally invalidate edits after schema/category changes.
"""
import hashlib,json,math,re
from pathlib import Path

def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,default=str).encode()).hexdigest()[:20]

def structure_guard(project,folder):
    tables=dict(project.get('tables') or {'data':project['table']})
    if project.get('active_table'):tables[project['active_table']]=project['table']
    shape={k:[t['headers'],len(t['rows']),sorted({str(v) for row in t['rows'] for v in row if isinstance(v,str) and not _numeric(v)})] for k,t in tables.items()}
    return digest([project['template'],hashlib.sha256((Path(folder)/'source.py').read_bytes()).hexdigest(),shape,project.get('mapping'),project.get('column_mappings')])

def _numeric(v):
    try:float(v);return True
    except (TypeError,ValueError):return False

def validate(project):
    edits=project.get('object_edits',{})
    if not isinstance(edits,dict) or len(edits)>600:raise ValueError('图形对象修改最多 600 项。')
    for key,entry in edits.items():
        if not isinstance(key,str) or not isinstance(entry,dict) or not isinstance(entry.get('guard'),str) or not isinstance(entry.get('props'),dict):raise ValueError('图形对象修改格式无效。')
        for prop,v in entry['props'].items():
            if prop in ['text','label']:
                if not isinstance(v,str) or len(v)>300:raise ValueError('对象文字最多 300 字。')
            elif prop=='color':
                if not isinstance(v,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',v):raise ValueError('对象颜色需要六位 HEX 颜色。')
            elif prop=='loc':
                if v not in ['best','upper right','upper left','lower right','lower left','center right','center left','upper center','lower center','center']:raise ValueError('图例位置无效。')
            elif prop in ['visible','frame']:
                if not isinstance(v,bool):raise ValueError('对象开关需要布尔值。')
            elif prop in ['fontsize','rotation','min','max','linewidth','alpha','ncols','offset_x','offset_y']:
                if isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v):raise ValueError('对象参数需要有限数值。')
                bounds={'fontsize':(4,72),'rotation':(-180,180),'linewidth':(.1,12),'alpha':(0,1),'ncols':(1,12),'offset_x':(-720,720),'offset_y':(-720,720)}
                if prop in bounds and not bounds[prop][0]<=v<=bounds[prop][1]:raise ValueError('对象参数超出范围：'+prop)
                if prop=='ncols' and int(v)!=v:raise ValueError('图例列数需要整数。')
            else:raise ValueError('不支持的对象属性：'+prop)
        p=entry['props']
        if 'min' in p and 'max' in p and p['min']==p['max']:raise ValueError('坐标范围的起点与终点不能相同。')
    view=project.get('plotly_view',{})
    if not isinstance(view,dict) or len(view)>40:raise ValueError('视图参数无效。')
    for key,v in view.items():
        if re.fullmatch(r'scene\d*\.camera',key):
            if not isinstance(v,dict) or set(v)-{'eye','center','up','projection'}:raise ValueError('三维相机参数无效。')
            for part,coords in v.items():
                if part=='projection':
                    if not isinstance(coords,dict) or set(coords)!={'type'} or coords['type'] not in ['perspective','orthographic']:raise ValueError('投影参数无效。')
                elif not isinstance(coords,dict) or set(coords)-{'x','y','z'} or any(not isinstance(n,(int,float)) or not math.isfinite(n) or abs(n)>1e6 for n in coords.values()):raise ValueError('相机坐标无效。')
        elif re.fullmatch(r'(?:[xy]axis\d*|scene\d*\.[xyz]axis)\.(range|autorange)',key):
            if key.endswith('autorange'):
                if not isinstance(v,bool):raise ValueError('自动范围参数无效。')
            elif not isinstance(v,list) or len(v)!=2 or any(not isinstance(n,(int,float,str)) or isinstance(n,(int,float)) and not math.isfinite(n) for n in v):raise ValueError('坐标范围无效。')
        else:raise ValueError('不支持的视图参数。')

def start(project,folder):
    validate(project)
    return {'version':1,'guard':structure_guard(project,folder),'renderer':'matplotlib','objects':[],'skipped':[]}

def props_for(project,manifest,oid,allowed):
    edit=project.get('object_edits',{}).get(oid)
    if not edit:return {}
    if edit['guard']!=manifest['guard']:
        manifest['skipped'].append(oid);return {}
    props=edit['props']
    if set(props)-set(allowed):raise ValueError('该对象不支持这些属性：'+oid)
    return props

def register(manifest,oid,kind,name,props,dom_id=None):
    manifest['objects'].append(dict(id=oid,dom_id=dom_id or oid,kind=kind,name=name,props=props))

def offset_text(obj,fig,dx,dy,text_override=None):
    """Display-plane offsets in points, applied after 3D/axis positioning.

    Every renderer (Agg, PDF, SVG) uses the same native artist. Annotation
    anchors remain in data coordinates; only the text end of an arrow moves.
    Extent queries get the same offset so tight exports include moved labels.
    """
    from matplotlib.transforms import ScaledTranslation
    from matplotlib.text import Annotation,Text
    from contextlib import contextmanager
    from mpl_toolkits.mplot3d.art3d import Text3D
    from mpl_toolkits.mplot3d import proj3d
    import numpy as np
    state={'active':False}
    if (dx or dy) and obj.axes is not None and obj in [obj.axes.title,obj.axes._left_title,obj.axes._right_title]:
        # The automatic title placement would otherwise counteract a downward drag.
        obj.axes._autotitlepos=False
    @contextmanager
    def moved(renderer,project=False):
        transform=obj.get_transform();old_text=obj.get_text();xy=obj.get_position()
        try:
            state['active']=True
            if text_override is not None:obj.set_text(text_override)
            if isinstance(obj,Annotation):
                trans=obj._get_xy_transform(renderer,obj.anncoords)
                delta=np.array([dx,-dy])*renderer.points_to_pixels(1)
                obj.xyann=trans.inverted().transform(trans.transform(obj.xyann)+delta)
            else:
                obj.set_transform(transform+ScaledTranslation(dx/72,-dy/72,fig.dpi_scale_trans))
                if project and isinstance(obj,Text3D):
                    x,y,_=proj3d.proj_transform(obj._x,obj._y,obj._z,obj.axes.get_proj())
                    obj._x,obj._y=x,y
            yield
        finally:
            obj.set_transform(transform);obj.set_position(xy);obj.set_text(old_text);state['active']=False
    for name in ['draw','get_window_extent','get_tightbbox']:
        original=getattr(obj,name)
        def wrap(*args,_method=original,_name=name,**kwargs):
            if state['active']:return _method(*args,**kwargs)
            renderer=args[0] if args else kwargs.get('renderer')
            if renderer is None:renderer=fig.canvas.get_renderer()
            with moved(renderer,project=_name!='draw'):
                if isinstance(obj,Text3D) and _name!='draw':return Text.get_window_extent(obj,renderer=renderer)
                return _method(*args,**kwargs)
        setattr(obj,name,wrap)

def mpl_edit(fig,project,manifest,prefix='',dom_prefix=''):
    from matplotlib.colors import to_hex
    def color(v):
        try:return to_hex(v)
        except (TypeError,ValueError):return '#333333'
    def text(obj,key,name):
        if not obj:return
        oid='vivid-'+prefix+key;obj.set_gid(oid)
        p=props_for(project,manifest,oid,['text','fontsize','color','rotation','visible','offset_x','offset_y'])
        for k,v in p.items():
            if k not in ['offset_x','offset_y']:getattr(obj,'set_'+k)(v)
        dx,dy=p.get('offset_x',0),p.get('offset_y',0)
        if dx or dy or 'text' in p:offset_text(obj,fig,dx,dy,p.get('text'))
        register(manifest,oid,'text',name,dict(text=obj.get_text(),fontsize=obj.get_fontsize(),color=color(obj.get_color()),rotation=float(obj.get_rotation()),visible=obj.get_visible(),offset_x=dx,offset_y=dy),dom_prefix+oid)
    if fig._suptitle:text(fig._suptitle,'title','总标题')
    for i,item in enumerate(fig.texts):
        if item is not fig._suptitle and item.get_text():text(item,f'figure-text-{i}','图注 · '+item.get_text()[:30])
    for i,ax in enumerate(fig.axes):
        base=f'ax{i}';name=f'子图 {i+1}'
        for slot,obj in [('title',ax.title),('left-title',ax._left_title),('right-title',ax._right_title)]:
            if obj.get_text():text(obj,base+'-'+slot,name+' 标题')
        for dim in ['x','y','z']:
            axis=getattr(ax,dim+'axis',None)
            if axis is None:continue
            if not getattr(ax,'_axis3don',ax.axison) or not axis.get_visible():continue
            oid='vivid-'+prefix+base+'-'+dim;axis.set_gid(None)
            colorbar=hasattr(ax,'_colorbar')
            allowed=['label','rotation','fontsize']+([] if colorbar else ['min','max'])
            p=props_for(project,manifest,oid,allowed)
            if 'label' in p:axis.set_label_text(p['label'])
            lo,hi=getattr(ax,'get_'+dim+'lim')()
            if 'min' in p or 'max' in p:
                low,high=p.get('min',lo),p.get('max',hi)
                if low==high:raise ValueError(name+' '+dim+' 轴范围起点与终点不能相同。')
                if getattr(ax,'get_'+dim+'scale')()=='log' and min(low,high)<=0:raise ValueError('对数坐标范围必须为正数。')
                getattr(ax,'set_'+dim+'lim')(low,high)
            for item in axis.get_ticklabels():
                if 'rotation' in p:item.set_rotation(p['rotation'])
                if 'fontsize' in p:item.set_fontsize(p['fontsize'])
            if 'fontsize' in p:axis.label.set_fontsize(p['fontsize'])
            ticks=axis.get_ticklabels();lo,hi=getattr(ax,'get_'+dim+'lim')()
            values=dict(label=axis.label.get_text(),rotation=float(ticks[0].get_rotation()) if ticks else 0,fontsize=float(ticks[0].get_fontsize()) if ticks else 10)
            if not colorbar:values.update(min=float(lo),max=float(hi))
            # Axis groups can include 3D panes and grids and reuse the same gid.
            # Expose the actual axis stroke as the pointer target instead.
            stroke=getattr(axis,'line',None)
            if stroke is None and dim in ['x','y']:
                for side in (['bottom','top'] if dim=='x' else ['left','right']):
                    spine=ax.spines.get(side)
                    if spine is not None and spine.get_visible():stroke=spine;break
            hit_id=oid+'-line'
            if stroke is not None:stroke.set_gid(hit_id)
            register(manifest,oid,'colorbar' if colorbar else 'axis',name+(' 色标 ' if colorbar else ' ')+dim.upper()+' 轴',values,dom_prefix+hit_id)
            if axis.label.get_text():text(axis.label,base+'-'+dim+'-label',name+' '+dim.upper()+' 轴名称')
            for j,tick in enumerate(ticks[:100]):
                if tick.get_text() and tick.get_visible():text(tick,base+'-'+dim+'-tick-'+digest([j,tick.get_text()]),name+' '+dim.upper()+' 刻度 · '+tick.get_text()[:25])
        leg=ax.get_legend()
        if leg:
            oid='vivid-'+prefix+base+'-legend';leg.set_gid(oid)
            p=props_for(project,manifest,oid,['loc','ncols','fontsize','frame','visible'])
            if 'loc' in p:
                leg.set_bbox_to_anchor(None);leg.set_loc(p['loc'])
            if 'ncols' in p:
                # Rebuild the packer using existing handles, retaining original artists/styles.
                handles=leg.legend_handles;labels=[t.get_text() for t in leg.texts];title=leg.get_title().get_text()
                leg.set_ncols(int(p['ncols']));leg._init_legend_box(handles,labels,markerfirst=True)
                leg.set_title(title)
            if 'fontsize' in p:
                for t in leg.texts:t.set_fontsize(p['fontsize'])
            if 'frame' in p:leg.set_frame_on(p['frame'])
            if 'visible' in p:leg.set_visible(p['visible'])
            loc={v:k for k,v in leg.codes.items()}.get(leg._loc,'best')
            register(manifest,oid,'legend',name+' 图例',dict(loc=loc,ncols=leg._ncols,fontsize=leg.texts[0].get_fontsize() if leg.texts else 10,frame=leg.get_frame_on(),visible=leg.get_visible()),dom_prefix+oid)
        seen={}
        for line in ax.lines:
            label=line.get_label()
            if not label or label.startswith('_'):continue
            key=digest(label);seen[key]=seen.get(key,0)+1;oid=f'vivid-{prefix}{base}-line-{key}-{seen[key]}';line.set_gid(oid)
            p=props_for(project,manifest,oid,['color','linewidth','alpha','visible'])
            for k,v in p.items():getattr(line,'set_'+k)(v)
            if leg:
                for handle,t in zip(leg.legend_handles,leg.texts):
                    if t.get_text()==label:
                        for k,v in p.items():
                            if hasattr(handle,'set_'+k):getattr(handle,'set_'+k)(v)
            register(manifest,oid,'line',name+' 曲线 · '+label,dict(color=color(line.get_color()),linewidth=line.get_linewidth(),alpha=line.get_alpha() if line.get_alpha() is not None else 1,visible=line.get_visible()),dom_prefix+oid)
        seen={}
        for t in ax.texts[:150]:
            if not t.get_text():continue
            key=digest(t.get_text());seen[key]=seen.get(key,0)+1
            text(t,f'{base}-text-{key}-{seen[key]}',name+' 标注 · '+t.get_text()[:30])

def plotly_edit(fig,project,manifest):
    manifest['renderer']='plotly'
    oid='vivid-title';p=props_for(project,manifest,oid,['text','fontsize','color'])
    if p:fig.update_layout(title=dict(**({'text':p['text']} if 'text' in p else {}),font={k:v for k,v in [('size',p.get('fontsize')),('color',p.get('color'))] if v is not None}))
    title=fig.layout.title
    register(manifest,oid,'text','总标题',dict(text=title.text or '',fontsize=title.font.size or 18,color=title.font.color or '#333333'))
    layout=fig.layout.to_plotly_json()
    paths=[k for k in layout if re.fullmatch('[xy]axis\\d*',k)]
    for k in layout:
        if re.fullmatch('scene\\d*',k):paths.extend(k+'.'+d+'axis' for d in 'xyz')
    for path in paths:
        obj=fig.layout
        for part in path.split('.'):obj=obj[part]
        oid='vivid-'+path.replace('.','-');p=props_for(project,manifest,oid,['label','min','max','rotation','fontsize'])
        if 'label' in p:obj.title.text=p['label']
        if 'rotation' in p:obj.tickangle=p['rotation']
        if 'fontsize' in p:obj.tickfont.size=p['fontsize'];obj.title.font.size=p['fontsize']
        if 'min' in p or 'max' in p:
            limits=obj.range or [None,None];obj.range=[p.get('min',limits[0]),p.get('max',limits[1])];obj.autorange=False
        values=dict(label=obj.title.text or '',rotation=obj.tickangle or 0,fontsize=obj.tickfont.size or 12)
        if obj.range:
            for key,val in zip(['min','max'],obj.range):
                if isinstance(val,(int,float)):values[key]=val
        register(manifest,oid,'axis',path.upper()+' 轴',values)
    oid='vivid-legend';p=props_for(project,manifest,oid,['fontsize','visible'])
    if 'fontsize' in p:fig.layout.legend.font.size=p['fontsize']
    if 'visible' in p:fig.layout.showlegend=p['visible']
    register(manifest,oid,'legend','图例',dict(fontsize=fig.layout.legend.font.size or 12,visible=fig.layout.showlegend is not False))
    for i,tr in enumerate(fig.data):
        oid=f'vivid-trace-{i}-{digest([tr.name,tr.type])}'
        p=props_for(project,manifest,oid,['alpha','visible'])
        if 'alpha' in p:tr.opacity=p['alpha']
        if 'visible' in p:tr.visible=p['visible']
        register(manifest,oid,'trace',tr.name or f'系列 {i+1}',dict(alpha=tr.opacity if tr.opacity is not None else 1,visible=tr.visible is not False))
    # The UI removes a saved range when its numeric property is edited.
    view=dict(project.get('plotly_view',{}))
    if view:fig.update_layout(view)
    manifest['view']=view
    for item in manifest['objects']:
        if item['kind']!='axis':continue
        axis=fig.layout
        for part in item['id'][6:].replace('-','.').split('.'):axis=axis[part]
        if axis.range:
            for key,val in zip(['min','max'],axis.range):
                if isinstance(val,(int,float)):item['props'][key]=val

BRIDGE="""
(function(){const gd=document.getElementById('{plot_id}');
function send(type,data){if(parent!==window&&/^https?:/.test(location.protocol))parent.postMessage({vivid:true,type,data},location.origin);}
gd.on('plotly_relayout',()=>{const view={};const l=gd.layout;
Object.keys(l).forEach(k=>{if(/^scene\\d*$/.test(k)&&l[k].camera)view[k+'.camera']=l[k].camera;
if(/^[xy]axis\\d*$/.test(k)){if(l[k].range)view[k+'.range']=l[k].range;view[k+'.autorange']=!!l[k].autorange;}
if(/^scene\\d*$/.test(k))['xaxis','yaxis','zaxis'].forEach(a=>{if(l[k][a]?.range)view[k+'.'+a+'.range']=l[k][a].range;});});
send('view',view);});gd.on('plotly_click',e=>{if(e.points?.length)send('trace',e.points[0].curveNumber);});})();
"""

def finish(manifest,project,folder,notes):
    ids={o['id'] for o in manifest['objects']}
    manifest['skipped']=sorted(set(manifest['skipped']) | (project.get('object_edits',{}).keys()-ids))
    if manifest['skipped']:notes.append(f"数据结构或图形对象已变化，{len(manifest['skipped'])} 项旧对象修改未应用；可在对象面板清理并重新设置。")
    (Path(folder)/'objects.json').write_text(json.dumps(manifest,ensure_ascii=False,allow_nan=False,indent=2),encoding='utf8')
