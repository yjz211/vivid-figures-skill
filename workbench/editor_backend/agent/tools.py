"""Validated tools over Vivid's existing data contracts, transforms and renderer."""
from pathlib import Path
import copy, json, math, re, shutil, subprocess
from schema import SPECS, sample, prepare
import object_editor
from . import store

WEB=Path(__file__).resolve().parents[2]
_CATALOG=None

def catalog():
    global _CATALOG
    if _CATALOG is None:
        source=(WEB/'assets/catalog.js').read_text(encoding='utf8')
        data=json.loads(source[source.index('{'):].strip().removesuffix(';'))
        keep={'id','number','display_name','tags','aliases','purpose','data_requirements','visual_features','adaptation_notes','composition','categories','previews','bundle'}
        _CATALOG={'cards':[{k:v for k,v in c.items() if k in keep} for c in data['cards']], 'categories':data['categories']}
    return _CATALOG

def search(query='',limit=8):
    words=re.findall(r'[a-z0-9_]+|[\u4e00-\u9fff]',query.lower())
    cards=catalog()['cards']
    scored=[]
    for c in cards:
        hay=json.dumps(c,ensure_ascii=False).lower()
        score=sum(1 for w in words if w in hay)+ (30 if query and query.lower() in c['display_name'].lower() else 0)
        scored.append((score,c))
    return [c for n,c in sorted(scored,key=lambda v:-v[0])[:min(int(limit),30)] if n>0 or not words]

def validate_table(t):
    if not isinstance(t,dict):raise ValueError('数据表需要对象。')
    h=t.get('headers');rows=t.get('rows')
    if not isinstance(h,list) or not 1<=len(h)<=256 or not isinstance(rows,list) or not 1<=len(rows)<=20000 or len(h)*len(rows)>500000:raise ValueError('数据表需为 1–256 列、1–20000 行，最多 500000 个单元格。')
    if any(not isinstance(x,str) or not x.strip() or len(x)>150 for x in h) or len(set(h))!=len(h):raise ValueError('列名需要非空且不重复。')
    for row in rows:
        if not isinstance(row,list) or len(row)!=len(h):raise ValueError('数据行与表头宽度不一致。')
        if any(isinstance(v,(dict,list)) or len(str(v))>500 or isinstance(v,float) and not math.isfinite(v) for v in row):raise ValueError('单元格需要有限数值或短文本。')
    return t

def profile(table):
    validate_table(table);out=[]
    for i,name in enumerate(table['headers']):
        vals=[r[i] for r in table['rows']];nonempty=[v for v in vals if v is not None and str(v).strip()]
        nums=[]
        for v in nonempty:
            try:
                n=float(v)
                if math.isfinite(n):nums.append(n)
            except (ValueError,TypeError):pass
        item={'name':name,'index':i,'type':'number' if len(nums)==len(nonempty) and nums else 'text','missing':len(vals)-len(nonempty),'unique':len(set(map(str,nonempty)))}
        if nums:item.update(min=min(nums),max=max(nums))
        item['examples']=list(dict.fromkeys(map(str,nonempty)))[:4];out.append(item)
    return {'rows':len(table['rows']),'columns':out,'sample':table['rows'][:4]}

def transform_table(table,operation):
    """Execute the EXACT pure JS transformer used by the existing table editor."""
    validate_table(table)
    node=shutil.which('node')
    if not node:raise ValueError('数据整理需要 Node.js，请安装后重试。')
    script="const fs=require('fs');const t=require(process.argv[1]);const x=JSON.parse(fs.readFileSync(0,'utf8'));try{process.stdout.write(JSON.stringify(t.compute(x.table,x.operation)))}catch(e){process.stderr.write(e.message);process.exit(1)}"
    p=subprocess.run([node,'-e',script,str(WEB/'frontend/data-transform.js')],input=json.dumps({'table':table,'operation':operation},ensure_ascii=False),text=True,encoding='utf8',capture_output=True,timeout=20,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if p.returncode:raise ValueError(p.stderr[-1000:])
    result=json.loads(p.stdout)['table'];validate_table(result);return result

def template_info(tid):
    if tid not in SPECS:raise ValueError('模板不存在。')
    card=next(c for c in catalog()['cards'] if c['id']==tid)
    p=sample(tid)
    return {'card':card,'contract':SPECS[tid],'example_mapping':p.get('mapping',{}),'table_keys':list(p.get('tables',{'data':p['table']})),'settings':p['settings']}

def bind_template(tid,datasets,bindings,mapping=None,name=None,settings=None):
    if tid not in SPECS:raise ValueError('模板不存在。')
    p=sample(tid);registry={d['id']:d for d in datasets}
    if not bindings:raise ValueError('请选择真实数据表。示例必须通过示例入口明确载入。')
    expected=list(p.get('tables',{'data':p['table']}))
    by_key={b['table_key']:b for b in bindings}
    if set(by_key)!=set(expected):raise ValueError('请提供此模板的全部数据表：'+', '.join(expected))
    tables={}
    for key,b in by_key.items():
        if b['dataset_id'] not in registry:raise ValueError('所选数据表不属于当前项目。')
        tables[key]=copy.deepcopy(registry[b['dataset_id']]['table'])
        contract=next((t for t in SPECS[tid].get('tables',[]) if t['key']==key),None)
        if contract and contract['kind']=='matrix' and b.get('columns') is not None:
            cols=b['columns'];table=tables[key]
            if not isinstance(cols,list) or len(cols)<2 or any(type(c)!=int or not 0<=c<len(table['headers']) for c in cols) or len(set(cols))!=len(cols):raise ValueError('矩阵列需包含一个标签列及至少一个数值列，且不能重复。')
            tables[key]={'headers':[table['headers'][c] for c in cols],'rows':[[r[c] for c in cols] for r in table['rows']]}
    if p.get('tables'):
        p['tables']=tables;p['active_table']=expected[0];p['table']=tables[p['active_table']]
        p['column_mappings']={key:b.get('columns',list(range(len(tables[key]['headers'])))) for key,b in by_key.items()}
    else:p['table']=tables['data']
    if mapping is not None:p['mapping']=mapping
    elif SPECS[tid]['family'] in ['wide','matrix']:
        p['mapping']={'category':0,'values':list(range(1,len(p['table']['headers']))),'errors':{}}
    p['name']=str(name or SPECS[tid]['name'])[:100]
    p['dataset_bindings']=copy.deepcopy(bindings)
    if settings:p['settings'].update(settings)
    prepare(p);return p

def edit_object(p,manifest,oid,props):
    obj=next((o for o in manifest.get('objects',[]) if o['id']==oid),None)
    if not obj:raise ValueError('该对象已不存在，请读取当前图形对象。')
    if set(props)-set(obj['props']):raise ValueError('对象不支持这些属性：'+','.join(set(props)-set(obj['props'])))
    guard=manifest['guard'];edits=p.setdefault('object_edits',{});old=edits.get(oid,{})
    edits[oid]={'guard':guard,'props':{**(old.get('props',{}) if old.get('guard')==guard else {}),**props}}
    object_editor.validate(p)

DESCRIPTIONS=[
 {'name':'search_templates','description':'根据目的/名称/关键词检索模板。参数 query:string, limit:int(最多10)。'},
 {'name':'inspect_template','description':'查看完整数据契约及字段。参数 template_id:string。选定新模板后必须读取一次。'},
 {'name':'inspect_data','description':'查看已有数据表的完整本地计算摘要及有限样例。参数 dataset_id:string。'},
 {'name':'transform_data','description':'调用原工作台的数据整理，保存新表。参数 dataset_id,name,operation。operation: {kind:sort,column:int,descending:bool} 或 {kind:filter,column,operator:eq/ne/contains/gt/gte/lt/lte/empty/nonempty,value} 或 {kind:melt,id:int,values:int[]} 或 {kind:pivot,id,group,value} 或 {kind:aggregate,group:int,value:int,method:mean/sum/std/count} 或 {kind:transpose}。不补造空缺。'},
 {'name':'bind_template','description':'用真实数据建立新图或替换当前图。参数 template_id,name,target:new/current,bindings:[{table_key,dataset_id,columns?:int[]}],mapping?:object,settings?:object。用户要独立图时target必须new；普通改样式不用此工具。普通单表键data；catalog模板必须提供全部table_keys，matrix表的columns可选标签列及数值列。mapping普通宽表{category:int,values:int[],errors:{数值列索引:误差列索引}}；samples:{group:int,value:int}；xy/xyz:{x:int,y:int,z?:int}。'},
 {'name':'update_settings','description':'修改当前图设置。参数 settings:object，允许title,xlabel,ylabel,zlabel,palette,language（仅zh/en）,english_labels（原文到英文显示名的对象，最多500项；不修改原始数据）,width,height,font_size,legend,labels,elev,azim,view_template,overlap,radar_max,highlight,suffix,auto_layout,avoid_label_overlap。保持未提及设置。'},
 {'name':'edit_object','description':'修改现有图形对象。参数 object_id:string,props:object。文字offset_x向右pt,offset_y向下pt；图例loc,ncols；仅允许对象已声明的属性。'},
 {'name':'render','description':'使用完整模板源码验证并绘图。参数为空对象。已有图的修改也需要调用；可与前置修改放同一批。'},
]
