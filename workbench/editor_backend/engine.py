"""Adapt the complete checked-in plotting source at explicit data boundaries."""
from pathlib import Path
import json,os,sys,runpy,hashlib,difflib,shutil
import numpy as np
from schema import prepare,serial
import object_editor

def canvas_size(project,settings,notes):
    from schema import SPECS,sample
    spec=SPECS[project['template']];mode=spec.get('layout_growth')
    w,h=settings['width'],settings['height']
    if project['template']=='basic.multipanel' and settings.get('auto_layout',True):
        tables=project.get('tables',{})
        if len(tables.get('line',{}).get('rows',[]))>10 or len(tables.get('bar',{}).get('rows',[]))>5:
            factor=max(1.,9/w,8.8/h);w,h=min(24,w*factor),min(20,h*factor)
            notes.append(f'四联图已按实际数据与标签扩展至 {w:g} × {h:g} 英寸；可关闭自动扩展并手动指定尺寸。')
        return w,h
    if not mode or not settings.get('auto_layout',True):return w,h
    original=sample(project['template'])
    def counts(p):
        key=next(iter(p['tables'])) if p.get('tables') else None
        tab=p['tables'][key] if key else p['table']
        mapping=p.get('mapping',{});bindings=p.get('column_mappings',{}).get(key)
        group_col=bindings[0] if bindings else mapping.get('group',mapping.get('category',0))
        cols=len(mapping['values']) if 'values' in mapping else len(tab['headers'])-1
        return len(tab['rows']),cols,len(set(str(r[group_col]) for r in tab['rows']))
    rows,cols,groups=counts(project);r0,c0,g0=counts(original)
    dr=max(0,rows-r0);dc=max(0,cols-c0);dg=max(0,groups-g0)
    if mode=='horizontal':h+=dr*.36
    elif mode=='vertical':w+=dr*.5
    elif mode=='groups':w+=dg*.75
    elif mode=='ridges':h+=dg*.6
    elif mode=='matrix':w+=dc*.38;h+=dr*.3
    elif mode=='bars3d':w+=dc*.6;h+=dr*.55
    w,h=min(24,w),min(20,h)
    if (w,h)!=(settings['width'],settings['height']):notes.append(f'已按数据量扩展画布至 {w:g} × {h:g} 英寸；可关闭自动扩展并手动指定尺寸。')
    return w,h

def avoid_3d_label_overlap(fig,notes):
    """Keep every bar; suppress only text labels whose projected rectangles collide."""
    from mpl_toolkits.mplot3d import proj3d
    from matplotlib.transforms import Bbox
    fig.canvas.draw();renderer=fig.canvas.get_renderer();hidden=0
    for ax in fig.axes:
        texts=[t for t in ax.texts if t.get_visible() and hasattr(t,'get_position_3d')]
        if len(texts)<=40:continue
        occupied=[]
        for t in sorted(texts,key=lambda t:t.get_position_3d()[2],reverse=True):
            px,py,_=proj3d.proj_transform(*t.get_position_3d(),ax.get_proj())
            sx,sy=ax.transData.transform((px,py))
            w,h,d=renderer.get_text_width_height_descent(t.get_text(),t.get_fontproperties(),ismath=False)
            left=sx-({'center':.5,'right':1}.get(t.get_ha(),0))*w
            bottom=sy-({'center':.5,'top':1,'baseline':.15}.get(t.get_va(),0))*h
            box=Bbox.from_bounds(left-2,bottom-2,w+4,h+d+4)
            if any(box.overlaps(other) for other in occupied):t.set_visible(False);hidden+=1
            else:occupied.append(box)
    if hidden:notes.append(f'柱数较多，已避让 {hidden} 处重叠数值标注；全部柱和数值仍保留。可在模板设置中关闭标注避让。')

def between(code,start,end,replacement):
    if code.count(start)!=1 or code.count(end)!=1:raise RuntimeError('模板源码边界改变，需要重新核对接入代码。')
    a=code.index(start);b=code.index(end,a)
    return code[:a]+replacement+'\n\n'+code[b:]

def radial_reference_caption(inputs,reference):
    """The reference's baseline count describes its exact example, never new data."""
    keys=('task_names','model_names','major_groups','task_details')
    if (inputs['highlight_index']==reference.get('highlight_index',0)
            and all(inputs[key]==reference[key] for key in keys)
            and np.array_equal(inputs['values'],reference['values'])):
        return reference.get('baseline_label')
    return None


def adapt(tid,code):
    from catalog_data import CONTRACTS,adapt as catalog_adapt
    if tid in CONTRACTS:return catalog_adapt(tid,code)
    if tid=='basic.grouped_bar':
        code=between(code,'categories = [','fig, ax =','globals().update(V)')
        code=code.replace('width = 0.22','width = 0.8 / n')
        code=code.replace("is_ours = '本文' in name","is_ours = name == highlight")
        # An empty bbox dictionary creates Matplotlib's default solid patch.
        # Only explicit template annotation boxes should have a background.
        code=code.replace("alpha=0.7) if is_best else {})", "alpha=0.7) if is_best else None)")
        code=code.replace("ax.set_ylim(0, max(max(v) for v in groups.values()) * 1.2)","lo=min(0., min(float(np.min(a-stds[k])) for k,a in groups.items())); hi=max(0.,max(float(np.max(a+stds[k])) for k,a in groups.items())); pad=max((hi-lo)*.15,1.); ax.set_ylim(lo-pad*.2,hi+pad)")
    elif tid=='basic.line':
        code=between(code,'x = np.arange','fig, ax =',"globals().update(V)\nmarkers = ['o','s','^','D','v','P','X','*','<','>','h','p']")
        code=code.replace("is_ours = '本文' in name","is_ours = name == highlight")
        code=code.replace("ax.set_xticks(x)","tick_idx=np.unique(np.linspace(0,len(x)-1,min(len(x),max(6,int(settings['width']*1.6)))).astype(int)); ax.set_xticks(x[tick_idx]); ax.set_xticklabels([categories[i] for i in tick_idx])")
    elif tid=='basic.scatter_regression':
        code=between(code,'np.random.seed(42)','fig = plt.figure','globals().update(V)')
        code=code.replace('se = residuals.std()',"from scipy.stats import t\nse = np.sqrt(np.sum(residuals**2)/(n-2))\nci = t.ppf(.975,n-2)*se*np.sqrt(1/n+(x_fit-x.mean())**2/np.sum((x-x.mean())**2))")
        code=code.replace('1.96 * se * (0.3 + layer * 0.1)','ci * (0.6 + layer * 0.2)')
    elif tid=='advanced.cluster_heatmap':
        code=between(code,'np.random.seed(42)','Z_col =','globals().update(V)')
        code=code.replace('n_clusters = 3','n_clusters = min(3, len(labels_col))')
        code=code.replace("'Silhouette = 0.42'",'silhouette_label')
        code=code.replace('# Silhouette score annotation',"# Computed on columns clustered above; unavailable if the partition is degenerate.\nfrom sklearn.metrics import silhouette_score\nsilhouette_label = f'轮廓系数 = {silhouette_score(data.T, col_clusters):.3f}' if 1 < len(set(col_clusters)) < len(labels_col) else '列聚类'\n# Silhouette score annotation")
        code=code.replace("im = ax_heat.imshow", "from matplotlib.colors import TwoSlopeNorm, Normalize\nlimit=max(float(np.abs(ordered_data).max()),1e-9)\ncolor_norm=TwoSlopeNorm(vmin=-limit,vcenter=0,vmax=limit) if ordered_data.min()<0<ordered_data.max() else Normalize(vmin=float(ordered_data.min()),vmax=float(ordered_data.max()) or 1.)\nim = ax_heat.imshow")
        code=code.replace("cmap=palette_cmap('diverging'), interpolation='nearest'", "cmap=palette_cmap('diverging' if ordered_data.min()<0<ordered_data.max() else 'sequential'), norm=color_norm, interpolation='nearest'")
    elif tid=='basic.raincloud_violin':
        code=between(code,'np.random.seed(42)','fig, ax =','globals().update(V)')
        code=between(code,'# 显著性括号','ax.set_xticks', '# 显著性检验需独立指定比较设计；编辑器默认仅显示描述统计。')
    elif tid=='advanced.ridgeline':
        code=between(code,'np.random.seed(42)','fig, ax =','globals().update(V)')
        code=code.replace('overlap = 0.6','overlap = settings["overlap"]')
        code=code.replace('kde(median)[0] / density.max() * 0.8','float(kde(median)[0]) / kde(x_grid).max() * 0.8')
        code=code.replace("ax.set_xlabel('Score'","ax.set_xlabel('数值'")
    elif tid=='competition.radar':
        code=between(code,'categories = [','fig, ax =','globals().update(V)')
        code=code.replace('ax.set_ylim(0, 1.12)','ax.set_ylim(0, radar_max * 1.12)')
        code=code.replace('ring_levels = [0.2, 0.4, 0.6, 0.8, 1.0]','ring_levels = np.linspace(radar_max/5,radar_max,5)')
        code=code.replace("['0.2','0.4','0.6','0.8','1.0']","[f'{v:g}' for v in ring_levels]")
        code=code.replace("is_ours = '本文' in name","is_ours = name == highlight")
        code=code.replace('v + 0.08','v + radar_max * 0.08')
    elif tid=='competition.surface_3d':
        code=between(code,'x = np.linspace','fig = plt.figure','globals().update(V)')
        code=code.replace('最优点','网格最低值')
    # Existing function-based 3D bar and radar-ridge renderers are called as-is.
    code=code.replace('PALETTE[i]', 'PALETTE[i % len(PALETTE)]')
    return code

def render_project(folder):
    folder=Path(folder).resolve();project=json.loads((folder/'project.json').read_text(encoding='utf8'))
    helpers=Path(__file__).parent/'_utils'
    if helpers.resolve()!=(folder/'_utils').resolve():
        for p in helpers.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix in ['.py','.json','.geojson','.mplstyle']:
                target=folder/'_utils'/p.relative_to(helpers);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    inputs,notes=prepare(project);notes=list(notes);s=inputs['settings'];tid=project['template']
    objects=object_editor.start(project,folder)
    output_width,output_height=canvas_size(project,s,notes)
    os.chdir(folder);os.environ.update(VIVID_WORKSPACE=str(folder),MPLBACKEND='Agg')
    (folder/'.vivid').mkdir(exist_ok=True)
    (folder/'.vivid/config.json').write_text(json.dumps({'palette':s['palette'],'language':'zh'}),encoding='utf8')
    sys.path[:0]=[str(folder),str(Path(__file__).parent),str(Path(__file__).parent/'_utils')]
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from _utils import plot_utils as pu
    pu.setup_style();pu.save_fig=lambda *a,**k:None;pu._save=pu.save_fig
    import plotly.graph_objects as go
    go.Figure.show=lambda *a,**k:None
    plt.show=lambda *a,**k:None
    np.random.seed(42)
    baseline=(folder/'source.py').read_text(encoding='utf-8-sig')
    code=adapt(tid,baseline)
    (folder/'plot.py').write_text(code,encoding='utf8')
    (folder/'source.diff').write_text(''.join(difflib.unified_diff(baseline.splitlines(True),code.splitlines(True),fromfile='source.py',tofile='plot.py')),encoding='utf8')
    import copy
    ns=runpy.run_path(str(folder/'plot.py'),init_globals={'V':copy.deepcopy(inputs)},run_name='vivid_render')
    if tid=='template.sem_violin_pearson':
        export_components(ns['component_figures'],folder,s,project,objects)
        object_editor.finish(objects,project,folder,notes)
        plt.close('all')
        return write_evidence(folder,tid,notes,inputs)
    if tid=='advanced.grouped_bar_3d':
        fig=ns['plot_chart'](inputs['data'],inputs['labels_row'],inputs['labels_col'],errors=None,
                             value_label=s['zlabel'] or '数值',sample_label=s['xlabel'] or '样本',condition_label=s['ylabel'] or '条件')
    elif tid=='advanced.radar_ridgeline':
        fig=ns['plot_chart'](inputs['categories'],inputs['labels_col'],inputs['data'].T,value_suffix=s['suffix'])
    elif tid=='advanced.grouped_radial_bar':
        reference=ns['demo_data']();caption=radial_reference_caption(inputs,reference)
        center=s['title'] or (reference['center_label'] if caption is not None else inputs['model_names'][inputs['highlight_index']])
        fig=ns['plot_chart'](inputs['task_names'],inputs['model_names'],inputs['values'],
                             major_groups=inputs['major_groups'],task_details=inputs['task_details'],
                             center_label=center,highlight_index=inputs['highlight_index'],
                             value_suffix=s.get('suffix',''),show_values=s['labels'],show_legend=s['legend'],
                             scale_mode='within_task',baseline_label=caption)
    else:fig=ns['fig']
    if isinstance(fig,go.Figure):
        fig.update_layout(width=int(s['width']*100),height=int(s['height']*100),font=dict(family='Microsoft YaHei',size=s['font_size']*1.2),showlegend=s['legend'])
        if s['title']:fig.update_layout(title=s['title'])
        if not s['labels']:fig.update_layout(annotations=[])
        if s['xlabel']:fig.update_xaxes(title_text=s['xlabel'])
        if s['ylabel']:fig.update_yaxes(title_text=s['ylabel'])
        if any(getattr(tr,'type','') in ['surface','cone','volume','isosurface','scatter3d','mesh3d'] for tr in fig.data):
            updates={k+'_title':s[v] for k,v in [('xaxis','xlabel'),('yaxis','ylabel'),('zaxis','zlabel')] if s[v]}
            if updates:fig.update_scenes(**updates)
            if not s.get('view_template',True):
                el,az=np.deg2rad([s['elev'],s['azim']]);fig.update_scenes(camera_eye=dict(x=float(2*np.cos(el)*np.cos(az)),y=float(2*np.cos(el)*np.sin(az)),z=float(2*np.sin(el))))
        object_editor.plotly_edit(fig,project,objects)
        object_editor.finish(objects,project,folder,notes)
        for name,scale in [('preview.png',1.2),('figure.png',3),('figure.pdf',1),('figure.svg',1)]:fig.write_image(str(folder/name),scale=scale)
        fig.write_html(str(folder/'interactive.html'),include_plotlyjs=True,post_script=object_editor.BRIDGE,config={'displaylogo':False,'scrollZoom':True,'editable':False})
        return write_evidence(folder,tid,notes,inputs)
    ax=ns.get('ax_main',ns.get('ax_heat',ns.get('ax',fig.axes[0])))
    if s['title'] and tid!='advanced.grouped_radial_bar':fig.suptitle(s['title'],y=1.02,fontsize=14)
    for key in ['xlabel','ylabel','zlabel']:
        if s[key] and hasattr(ax,'set_'+key):getattr(ax,'set_'+key)(s[key])
    # Fill useful axis labels from the user's selected columns, rather than demo words.
    h=project['table']['headers'];m=project['mapping'];family=SPECS_FAMILY(tid)
    if family=='xy':
        if not s['xlabel']:ax.set_xlabel(h[m['x']])
        if not s['ylabel']:ax.set_ylabel(h[m['y']])
    if family=='xyz':
        for key in ['x','y','z']:
            if not s[key+'label']:getattr(ax,'set_'+key+'label')(h[m[key]])
    if tid in ['basic.grouped_bar','basic.line']:
        if not s['xlabel']:ax.set_xlabel(h[m['category']])
        if not s['ylabel']:ax.set_ylabel('数值')
    if family=='samples':
        key='xlabel' if tid=='advanced.ridgeline' else 'ylabel'
        if not s[key]:getattr(ax,'set_'+key)(h[m['value']])
    if hasattr(ax,'view_init') and not s.get('view_template',True):ax.view_init(elev=s['elev'],azim=s['azim'])
    if not s['legend']:
        for axis in fig.axes:
            legend=axis.get_legend()
            if legend:legend.remove()
    if not s['labels'] and tid!='advanced.grouped_radial_bar':
        for axis in fig.axes:
            for text in axis.texts:text.set_visible(False)
    fig.set_size_inches(output_width,output_height)
    from matplotlib.text import Text
    for text in fig.findobj(match=Text):
        if tid!='advanced.grouped_radial_bar':text.set_fontfamily(['Microsoft YaHei','DejaVu Sans'])
        text.set_fontsize(text.get_fontsize()*s['font_size']/10)
        if text.get_text() in [s[k] for k in ['title','xlabel','ylabel','zlabel']] and hasattr(text,'set_parse_math'):text.set_parse_math(False)
    if tid=='basic.multipanel':
        # Measure actual font sizes and reserve title space at every canvas size.
        # A fixed subplot top overrides tight_layout and collides on small figures.
        if s['title']:fig._suptitle.set_y(.99)
        fig.tight_layout(pad=1.5,w_pad=1.6,h_pad=1.8)
    if tid=='advanced.grouped_bar_3d' and s.get('avoid_label_overlap',True) and s['labels']:avoid_3d_label_overlap(fig,notes)
    object_editor.mpl_edit(fig,project,objects)
    object_editor.finish(objects,project,folder,notes)
    for name,dpi in [('preview.png',140),('figure.png',300),('figure.pdf',300),('figure.svg',300)]:
        if tid=='advanced.grouped_radial_bar':
            fig.savefig(folder/name,dpi=dpi,facecolor=fig.get_facecolor(),bbox_inches=None,pad_inches=0)
        else:fig.savefig(folder/name,dpi=dpi,facecolor='white',bbox_inches='tight',pad_inches=.5 if tid=='advanced.grouped_bar_3d' else .18)
    plt.close('all')
    return write_evidence(folder,tid,notes,inputs)

def write_evidence(folder,tid,notes,inputs):
    evidence=dict(template=tid,notes=notes,inputs=serial(inputs),source_sha256=hashlib.sha256((folder/'source.py').read_bytes()).hexdigest(),plot_sha256=hashlib.sha256((folder/'plot.py').read_bytes()).hexdigest())
    project=json.loads((folder/'project.json').read_text(encoding='utf8'))
    evidence['object_edits']=project.get('object_edits',{});evidence['plotly_view']=project.get('plotly_view',{})
    (folder/'data_used.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf8')
    return evidence

def export_components(figures,folder,s,project,objects):
    """Join native vector components without redrawing their plotting bodies."""
    import fitz,io,xml.etree.ElementTree as ET
    from matplotlib.text import Text
    ratios=[f.get_figwidth()/f.get_figheight() for f in figures]
    docs=[];svgs=[]
    for i,(fig,ratio) in enumerate(zip(figures,ratios)):
        font_scale=min(s['width']*ratio/sum(ratios)/fig.get_figwidth(),s['height']/fig.get_figheight())
        fig.set_size_inches(s['width']*ratio/sum(ratios),s['height'])
        for item in fig.findobj(match=Text):
            item.set_fontfamily(['Microsoft YaHei','DejaVu Sans']);item.set_fontsize(item.get_fontsize()*s['font_size']/10*font_scale)
        if not s['labels']:
            for ax in fig.axes:
                for item in ax.texts:item.set_visible(False)
        if s['title'] and i==0:fig.suptitle(s['title'])
        object_editor.mpl_edit(fig,project,objects,prefix=f'part{i}-',dom_prefix=f'part{i}_')
        buf=io.BytesIO();fig.savefig(buf,format='pdf',bbox_inches='tight');docs.append(fitz.open(stream=buf.getvalue(),filetype='pdf'))
        buf=io.StringIO();fig.savefig(buf,format='svg',bbox_inches='tight');svgs.append(ET.fromstring(buf.getvalue()))
    heights=[d[0].rect.height for d in docs];height=max(heights)
    widths=[d[0].rect.width*height/h for d,h in zip(docs,heights)];width=sum(widths)+16*(len(docs)-1)
    result=fitz.open();page=result.new_page(width=width,height=height);x=0
    root=ET.Element('{http://www.w3.org/2000/svg}svg',width=f'{width}pt',height=f'{height}pt',viewBox=f'0 0 {width} {height}')
    for i,(d,w,svg) in enumerate(zip(docs,widths,svgs)):
        page.show_pdf_page(fitz.Rect(x,0,x+w,height),d,0)
        # Matplotlib assigns identical clip IDs across figures; namespace each one.
        for node in svg.iter():
            if 'id' in node.attrib:node.attrib['id']=f'part{i}_'+node.attrib['id']
            for k,v in list(node.attrib.items()):
                if 'url(#' in v:node.attrib[k]=v.replace('url(#',f'url(#part{i}_')
                elif k.endswith('href') and v.startswith('#'):node.attrib[k]='#'+f'part{i}_'+v[1:]
        svg.set('x',str(x));svg.set('y','0');svg.set('width',str(w));svg.set('height',str(height));root.append(svg);x+=w+16
    result.save(folder/'figure.pdf')
    for name,dpi in [('preview.png',140),('figure.png',300)]:page.get_pixmap(dpi=dpi,alpha=False).save(folder/name)
    ET.ElementTree(root).write(folder/'figure.svg',encoding='utf8',xml_declaration=True)
    for d in docs:d.close()
    result.close()

def SPECS_FAMILY(tid):
    from schema import SPECS
    return SPECS[tid]['family']
