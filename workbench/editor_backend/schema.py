"""Explicit data contracts. No user data is interpreted as Python code."""
import json, math, ast
from pathlib import Path
import numpy as np

DEFINITIONS = [
 ('basic.grouped_bar','分组柱状对比','wide', [9,5.5]),
 ('basic.line','多序列折线与区间带','wide',[8,5]),
 ('basic.scatter_regression','散点回归与双边际密度','xy',[7,6]),
 ('advanced.cluster_heatmap','聚类矩阵热图','matrix',[10,8]),
 ('basic.raincloud_violin','小提琴与箱线组合','samples',[8,5.5]),
 ('advanced.ridgeline','堆叠山脊密度','samples',[8,6]),
 ('competition.radar','多方案雷达','wide',[6.5,6.5]),
 ('advanced.radar_ridgeline','雷达山脊融合图','wide',[9,7.7]),
 ('advanced.grouped_bar_3d','三维分组渐变柱状图','matrix',[14.4,12.8]),
 ('competition.surface_3d','三维曲面与底部等高线','xyz',[8,6]),
]
SPECS={tid:dict(id=tid,name=name,family=family,size=size) for tid,name,family,size in DEFINITIONS}
from catalog_data import CONTRACTS
for _tid,_c in CONTRACTS.items():
    SPECS[_tid]={k:_c[k] for k in ['id','name','family','size']}
    SPECS[_tid]['tables']=[{k:t[k] for k in ['key','title','kind','headers']} for t in _c['tables']]
    SPECS[_tid]['notes']=_c.get('notes',[])
    # Display the same requirements used by validation, without maintaining a second rule list.
    SPECS[_tid]['requirements']=list(dict.fromkeys(
        node.msg.value for node in ast.walk(ast.parse(_c['setup']))
        if isinstance(node,ast.Assert) and isinstance(node.msg,ast.Constant) and isinstance(node.msg.value,str)
    ))

for _tid,_text in {
    'basic.grouped_bar':'分类行可增减，最多200行；最多12个数值系列。',
    'basic.line':'需要2–200个横轴点，最多12个数值系列；按数据行顺序连接。',
    'basic.scatter_regression':'至少4个非共线样本，坐标列不能恒定。',
    'advanced.cluster_heatmap':'需要2–100行、2–12个数值变量。',
    'basic.raincloud_violin':'需要2–12组，每组至少3个样本且数值不能全部相同。',
    'advanced.ridgeline':'需要2–12组，每组至少3个样本且数值不能全部相同。',
    'competition.radar':'需要3–16个指标、最多8个方案；数值须在0至径向上限之间。',
    'advanced.radar_ridgeline':'需要5–16个指标、2–4个数据层。',
    'advanced.grouped_bar_3d':'支持1–10行、1–12个数值系列；每个交叉位置一根柱，数值必须非负。',
    'competition.surface_3d':'X和Y方向各需2–100个坐标；每个X、Y组合必须有一个Z值。',
}.items():SPECS[_tid]['requirements']=[_text]

# Only categorical layouts with known axes receive automatic canvas growth.
for _mode,_ids in {
    'horizontal':['advanced.dumbbell','advanced.back_to_back_bar','advanced.diverging_bar','competition.feature_importance','competition.tornado','competition.gantt','empirical.psm_balance','advanced.dot_ci','empirical.forest'],
    'vertical':['basic.grouped_bar','basic.stacked_bar','advanced.lollipop','basic.pareto','academic.ablation','advanced.waterfall','competition.waterfall'],
    'groups':['basic.raincloud_violin','basic.raincloud','academic.confusion_matrix'],
    'ridges':['advanced.ridgeline','empirical.raincloud','empirical.prediction_error_raincloud'],
    'matrix':['advanced.cluster_heatmap','competition.spatiotemporal_heatmap','academic.attention_heatmap','competition.confusion_matrix','advanced.method_heatmap','empirical.prediction_accuracy_heatmap'],
    'bars3d':['advanced.grouped_bar_3d'],
}.items():
    for _tid in _ids:
        if _tid in SPECS:SPECS[_tid]['layout_growth']=_mode

class Invalid(ValueError):
    def __init__(self,message,row=None,col=None):
        super().__init__(message);self.detail=dict(message=message,row=row,col=col)

def defaults(tid):
    spec=SPECS[tid]
    return dict(title='',xlabel='',ylabel='',zlabel='',palette='pastel-girl',font_size=10,
                width=spec['size'][0],height=spec['size'][1],legend=True,labels=True,
                highlight=0,radar_max=1,overlap=.6,elev=27 if tid=='advanced.grouped_bar_3d' else 30,
                azim=-56 if tid=='advanced.grouped_bar_3d' else 135,suffix='',view_template=True)

def sample(tid):
    if tid in CONTRACTS:
        from catalog_data import sample as catalog_sample
        return catalog_sample(tid)
    rng=np.random.RandomState(42)
    if tid=='basic.grouped_bar':
        headers=['指标','本文方法','方法B','方法C'];rows=[['指标A',85.2,82.1,79.8],['指标B',78.3,80.5,75.2],['指标C',92.1,88.7,85.3],['指标D',88.5,85.2,82]]
    elif tid=='basic.line':
        headers=['年份','本文方法','方法B','方法C'];rows=[[2015+i,*v] for i,v in enumerate(zip([72,75,78,80,83,85,87,89,91,92],[70,73,76,79,81,82,84,86,88,89],[68,70,72,75,77,79,80,82,83,84]))]
    elif tid=='basic.scatter_regression':
        x=rng.uniform(1,10,150);y=2.5*x+rng.normal(0,3,150);headers=['投入','产出'];rows=np.column_stack([x,y]).round(4).tolist()
    elif tid=='advanced.cluster_heatmap':
        headers=['样本']+[f'特征{i+1}' for i in range(8)];rows=[[f'样本{i+1}',*r] for i,r in enumerate(rng.randn(10,8).round(3).tolist())]
    elif tid in ['basic.raincloud_violin','advanced.ridgeline']:
        headers=['分组','数值'];rows=[]
        for i,(mean,std) in enumerate([(80,5),(85,3),(78,8),(90,4)]):
            rows.extend([[f'{chr(65+i)}组',round(float(v),4)] for v in rng.normal(mean,std,80)])
    elif tid=='competition.radar':
        headers=['指标','本文方法','方案A','方案B'];rows=[[name,*v] for name,v in zip(['成本','效率','可靠性','安全性','灵活性','可扩展性'],zip([.95,.88,.92,.9,.85,.91],[.8,.82,.78,.85,.7,.75],[.85,.75,.88,.72,.9,.68]))]
    elif tid=='advanced.radar_ridgeline':
        headers=['指标','测试组','训练组','总体'];rows=[[name,*v] for name,v in zip(['精度','效率','鲁棒','泛化','稳定','响应','能耗','成本','扩展','安全'],zip([32.8,25.4,29.7,18.9,24.6,21.3,16.8,22.5,27.9,19.7],[38.6,31.1,35.8,27.6,33.2,29.5,25.1,28.7,34.6,26.4],[44.7,36.2,42.1,34.5,39.8,37.4,31.6,35.2,41.3,33.8]))]
    elif tid=='advanced.grouped_bar_3d':
        headers=['样本','条件1','条件2','条件3','条件4','条件5'];rows=[[f'样本{i+1}',*[round(float(v),2) for v in r]] for i,r in enumerate(rng.uniform(2,45,(5,5))) ]
    else:
        headers=['X','Y','Z'];rows=[[round(float(x),3),round(float(y),3),round(float(np.sin(x)*np.cos(y)+.5*np.sin(2*x)*np.cos(2*y)),5)] for y in np.linspace(-3,3,17) for x in np.linspace(-3,3,17)]
    family=SPECS[tid]['family']
    mapping={'category':0,'values':list(range(1,len(headers))),'errors':{}} if family in ['wide','matrix'] else {'group':0,'value':1} if family=='samples' else {'x':0,'y':1,**({'z':2} if family=='xyz' else {})}
    return dict(schema=1,template=tid,name=SPECS[tid]['name'],table=dict(headers=headers,rows=rows),mapping=mapping,settings=defaults(tid))

def prepare(project):
    if not isinstance(project,dict):raise Invalid('项目必须是对象。')
    tid=project.get('template')
    if tid not in SPECS:raise Invalid('此模板尚未接入编辑器。')
    if project.get('schema',1)!=1:raise Invalid('项目格式版本不受支持。')
    if tid in CONTRACTS:
        from catalog_data import prepare as catalog_prepare
        s={**defaults(tid),**project.get('settings',{})}
        for k,lo,hi in [('width',3,24),('height',2,20),('font_size',6,20),('elev',-80,85),('azim',-180,180)]:
            try:s[k]=float(s[k]);assert math.isfinite(s[k]) and lo<=s[k]<=hi
            except Exception:raise Invalid(f'设置 {k} 应在 {lo}–{hi} 之间。')
        registry=json.loads((Path(__file__).parent/'_utils/palettes.json').read_text(encoding='utf8'))['palettes']
        if s['palette'] not in registry:raise Invalid('配色不存在。')
        for k in ['title','xlabel','ylabel','zlabel']:
            if not isinstance(s[k],str) or len(s[k])>150:raise Invalid('文字设置最多150字。')
        return catalog_prepare({**project,'settings':s})
    table=project.get('table',{});headers=table.get('headers',[]);rows=table.get('rows',[])
    if not isinstance(headers,list) or not 2<=len(headers)<=40:raise Invalid('数据表需要 2–40 列。')
    headers=[str(x).strip() for x in headers]
    if any(not x or len(x)>100 for x in headers) or len(set(headers))!=len(headers):raise Invalid('列名须非空、不重复，且不超过 100 字。')
    if not isinstance(rows,list) or not 1<=len(rows)<=10000 or len(rows)*len(headers)>100000:raise Invalid('需要 1–10000 行数据，总单元格不超过 100000 个。')
    for r,row in enumerate(rows):
        if not isinstance(row,list) or len(row)!=len(headers):raise Invalid(f'第 {r+1} 行列数与表头不一致。',r)
        for c,v in enumerate(row):
            if isinstance(v,(dict,list)) or len(str(v))>300:raise Invalid('单元格内容过长或不是标量。',r,c)
    mapping=project.get('mapping',{});settings={**defaults(tid),**project.get('settings',{})}
    palettes=json.loads((Path(__file__).parent/'_utils/palettes.json').read_text(encoding='utf8'))['palettes']
    if settings['palette'] not in palettes:raise Invalid('请选择现有配色。')
    for key,lo,hi in [('width',4,20),('height',3,18),('font_size',6,20),('radar_max',.000001,1e9),('overlap',.25,1.5),('elev',-80,85),('azim',-180,180)]:
        try:value=float(settings[key])
        except (TypeError,ValueError):raise Invalid(f'设置 {key} 必须为数字。')
        if not math.isfinite(value) or not lo<=value<=hi:raise Invalid(f'设置 {key} 范围应为 {lo}–{hi}。')
        settings[key]=value
    for key in ['title','xlabel','ylabel','zlabel','suffix']:
        if not isinstance(settings[key],str) or len(settings[key])>150:raise Invalid('标题、轴名称和单位最多 150 字。')
    for key in ['legend','labels']:
        if not isinstance(settings[key],bool):raise Invalid('图例与标注开关必须为布尔值。')
    def column(key):
        value=mapping.get(key)
        if type(value)!=int or not 0<=value<len(headers):raise Invalid(f'请为「{key}」选择有效的数据列。')
        return value
    def numeric(r,c):
        v=rows[r][c]
        try:
            if v is None or isinstance(v,bool) or not str(v).strip():raise ValueError()
            n=float(v)
            if not math.isfinite(n) or abs(n)>1e12:raise ValueError()
            return n
        except (ValueError,TypeError):raise Invalid(f'第 {r+1} 行「{headers[c]}」需要有限数字；当前为「{v}」。',r,c)
    def labels(c,unique=False):
        out=[str(row[c]).strip() if row[c] is not None else '' for row in rows]
        for r,v in enumerate(out):
            if not v:raise Invalid(f'第 {r+1} 行「{headers[c]}」不能为空。',r,c)
            if unique and v in out[:r]:raise Invalid(f'第 {r+1} 行「{headers[c]}」重复：{v}。',r,c)
        return out
    family=SPECS[tid]['family'];v={};notes=[]
    if family in ['wide','matrix']:
        cat=column('category');cols=mapping.get('values',[])
        if not isinstance(cols,list) or not cols or any(type(c)!=int or not 0<=c<len(headers) or c==cat for c in cols) or len(set(cols))!=len(cols):raise Invalid('请选择不重复的数值列，且不能包含分类列。')
        groups=[headers[c] for c in cols];cats=labels(cat,True)
        arr=np.array([[numeric(r,c) for c in cols] for r in range(len(rows))])
        if len(cols)>12:raise Invalid('此模板最多支持 12 个数值系列。')
        try:highlight=int(settings['highlight'])
        except (ValueError,TypeError):raise Invalid('请选择重点系列。')
        if not 0<=highlight<len(cols):raise Invalid('重点系列已不存在，请重新选择。')
        settings['highlight']=highlight
        v.update(categories=cats,groups=dict(zip(groups,arr.T)),series=dict(zip(groups,arr.T)),methods=dict(zip(groups,arr.T)),data=arr,labels_row=cats,labels_col=groups,highlight=groups[highlight])
        stds={};error_mapping=mapping.get('errors',{})
        if not isinstance(error_mapping,dict):raise Invalid('误差列对应格式错误。')
        for name,c in zip(groups,cols):
            ec=error_mapping.get(str(c))
            if ec is None or ec=='':stds[name]=np.zeros(len(rows));continue
            if type(ec)!=int or not 0<=ec<len(headers) or ec in [cat,*cols]:raise Invalid('误差列须独立于分类列和数值列。')
            errors=np.array([numeric(r,ec) for r in range(len(rows))])
            if (errors<0).any():raise Invalid('对称误差不能为负数。',int(np.where(errors<0)[0][0]),ec)
            stds[name]=errors
        v['stds']=stds
        if tid in ['basic.grouped_bar','basic.line']:
            if len(rows)>200:raise Invalid('此模板最多显示 200 个横轴点。')
            if tid=='basic.line' and len(rows)<2:raise Invalid('折线至少需要两个横轴点。')
            v['x']=np.arange(len(rows),dtype=float)
            if tid=='basic.line':
                try:
                    vx=np.array([float(x) for x in cats]);v['x']=vx if np.isfinite(vx).all() else v['x']
                except ValueError:pass
                notes.append('横轴保留数据行顺序；区间带使用所选对称误差，不自动推断置信区间。')
        elif tid=='advanced.cluster_heatmap':
            if not 2<=len(rows)<=100 or len(cols)<2:raise Invalid('聚类热图需要 2–100 行、至少 2 个数值列。')
            notes.append('列按 Ward 聚类重排；轮廓系数使用实际列聚类结果计算。')
        elif tid=='competition.radar':
            if not 3<=len(rows)<=16 or len(cols)>8:raise Invalid('雷达图需要 3–16 个指标、最多 8 个方案。')
            bad=np.argwhere((arr<0)|(arr>settings['radar_max']))
            if bad.size:
                r,c=bad[0];raise Invalid('雷达数值须在 0 到径向上限之间；请调整径向上限或自行统一量纲。',int(r),cols[int(c)])
            v.update(N=len(cats),angles=np.linspace(0,2*np.pi,len(cats),endpoint=False).tolist()+[0],methods={k:list(a) for k,a in zip(groups,arr.T)},radar_max=settings['radar_max'])
            notes.append('使用输入原值，不自动归一化；成本型指标请事先统一方向。')
        elif tid=='advanced.radar_ridgeline':
            if not 5<=len(rows)<=16 or not 2<=len(cols)<=4:raise Invalid('雷达山脊需要 5–16 个指标、2–4 个数据层。')
            notes.append('峰高按所有输入值的统一最小值与最大值归一化，标签保留原值；该图不是密度估计。')
        elif tid=='advanced.grouped_bar_3d':
            if len(rows)>10 or len(cols)>12:raise Invalid('三维分组柱最多支持 10×12 个柱。')
            if (arr<0).any():
                r,c=np.argwhere(arr<0)[0];raise Invalid('三维渐变柱只支持非负数。',int(r),cols[int(c)])
    elif family=='samples':
        gc,vc=column('group'),column('value')
        if gc==vc:raise Invalid('分组列与数值列必须不同。')
        cats=labels(gc);groups=list(dict.fromkeys(cats))
        if not 2<=len(groups)<=12:raise Invalid('分布图需要 2–12 组样本。')
        all_values=np.array([numeric(r,vc) for r in range(len(rows))]);arrays=[all_values[np.array(cats)==g] for g in groups]
        for g,a in zip(groups,arrays):
            if len(a)<3 or np.ptp(a)==0:raise Invalid(f'「{g}」至少需要 3 个样本，且数值不能全部相同。')
        v.update(groups=groups,data=arrays,n_groups=len(groups),overlap=settings['overlap'])
        if tid=='basic.raincloud_violin':notes.append('显示样本分布、箱线与均值；未进行组间显著性检验。')
        else:notes.append('各组密度独立归一化为相同峰高，不能用面积比较样本量。')
    else:
        keys=['x','y']+(['z'] if family=='xyz' else []);cols=[column(k) for k in keys]
        if len(set(cols))!=len(cols):raise Invalid('坐标列不能重复。')
        arrays=[np.array([numeric(r,c) for r in range(len(rows))]) for c in cols]
        if family=='xy':
            if len(rows)<4 or np.linalg.matrix_rank(np.cov(arrays))<2:raise Invalid('此模板的二维密度需要至少 4 个非共线样本；常数列和完全直线数据不适用。')
            v.update(x=arrays[0],y=arrays[1],n=len(rows));notes.append('拟合带为普通最小二乘均值响应的 95% t 置信区间。')
        else:
            xs,ys=np.unique(arrays[0]),np.unique(arrays[1])
            if not 2<=len(xs)<=100 or not 2<=len(ys)<=100:raise Invalid('曲面 X、Y 方向各需要 2–100 个不同坐标。')
            pairs={}
            for r,(x,y,z) in enumerate(zip(*arrays)):
                if (x,y) in pairs:raise Invalid('同一 X、Y 坐标重复；请先确定聚合方式。',r,cols[0])
                pairs[x,y]=z
            if len(pairs)!=len(xs)*len(ys):raise Invalid('曲面需要完整的矩形网格：每个 X、Y 组合都应有一个 Z 值。')
            X,Y=np.meshgrid(xs,ys);Z=np.array([[pairs[x,y] for x in xs] for y in ys]);v.update(X=X,Y=Y,Z=Z)
            notes.append('按实际 X、Y 网格绘制，不插值补造缺失坐标；标记为采样网格内最低值。')
    v['settings']=settings
    return v,notes

def serial(value):
    import pandas as pd, types
    if isinstance(value,pd.DataFrame):return {'columns':list(value.columns),'index':list(map(str,value.index)),'values':serial(value.values)}
    if isinstance(value,pd.Series):return serial(value.to_numpy())
    if isinstance(value,pd.Index):return serial(value.tolist())
    if isinstance(value,types.ModuleType):return value.__name__
    if isinstance(value,set):return serial(sorted(value,key=str))
    if hasattr(value,'nodes') and hasattr(value,'edges'):return {'nodes':list(value.nodes),'edges':list(value.edges)}
    import datetime
    if isinstance(value,(datetime.date,datetime.datetime)):return value.isoformat()
    if isinstance(value,np.ndarray):return serial(value.tolist())
    if isinstance(value,np.generic):return value.item()
    if isinstance(value,dict):return {str(k):serial(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [serial(v) for v in value]
    return value
