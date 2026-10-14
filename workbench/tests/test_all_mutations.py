from pathlib import Path
import sys,json,shutil,subprocess,concurrent.futures,copy,hashlib
WEB=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(WEB/'editor_backend'))
from schema import SPECS,sample,prepare,serial
OUT=WEB/'verification/data-replacement';OUT.mkdir(exist_ok=True)
def digest(v):return hashlib.sha256(json.dumps(serial(v),sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def mutate(tid):
    p=sample(tid);base=digest(prepare(copy.deepcopy(p))[0]);tabs=p.get('tables',{'data':p['table']})
    if tid=='advanced.kaplan_meier':
        q=copy.deepcopy(p);t=q['tables']['data'];g=t['rows'][0][0]
        for row in t['rows']:
            if row[0]==g:row[1]*=.65
        q['table']=t;return q,{'table':'data','change':'第一组随访时间整体缩短35%'}
    if tid in ['empirical.correlation_heatmap','screenshot.streamgraph','screenshot.mesh_surface_3d','screenshot.block_surface_3d','advanced.bivariate_choropleth','competition.feasible_region']:
        q=copy.deepcopy(p);key=next(iter(q['tables']));t=q['tables'][key];nr=len(t['rows']);nc=len(t['headers']);col=nc//2
        if tid=='empirical.correlation_heatmap':
            for i,row in enumerate(t['rows']):row[1]=row[1]*(-1 if i%2 else 1)
        elif tid=='screenshot.streamgraph':
            totals=[sum(float(r[j]) for r in t['rows']) for j in range(1,nc)];col=totals.index(max(totals))+1
            for row in t['rows']:row[col]*=2
        else:
            values=[v for row in t['rows'] for v in row[1:]];lo=min(values);hi=max(values)
            for i in range(nr//3,2*nr//3):
                for j in range(max(1,nc//3),2*nc//3):t['rows'][i][j]=hi+max(hi-lo,1)
        q['table']=q['tables'][q['active_table']];prepare(copy.deepcopy(q));return q,{'table':key,'changed_region':'中部连续数据块或序列','purpose':'使矩阵分档与三维遮挡下的变化可见'}
    for key,tab in tabs.items():
        for r in list(range(min(6,len(tab['rows'])))):
            for col in range(0 if len(tab['headers'])==1 else 1,len(tab['headers'])):
                value=tab['rows'][r][col]
                if not isinstance(value,(int,float)) or isinstance(value,bool):continue
                for replacement in [value*1.17+.013,value*.83,value+.001]:
                    q=copy.deepcopy(p);t=q.get('tables',{'data':q['table']})[key];t['rows'][r][col]=replacement
                    if q.get('active_table')==key:q['table']=t
                    try:
                        changed=digest(prepare(copy.deepcopy(q))[0])
                        if changed!=base:return q,{'table':key,'row':r,'col':col,'before':value,'after':replacement}
                    except Exception:pass
    # Fixed discrete states and percentage compositions: valid numeric permutations.
    for key,tab in tabs.items():
        for r in range(min(8,len(tab['rows']))):
            for col in range(1,len(tab['headers'])-1):
                q=copy.deepcopy(p);t=q.get('tables',{'data':q['table']})[key]
                if t['rows'][r][col]==t['rows'][r][col+1]:continue
                t['rows'][r][col],t['rows'][r][col+1]=t['rows'][r][col+1],t['rows'][r][col]
                if q.get('active_table')==key:q['table']=t
                try:
                    if digest(prepare(copy.deepcopy(q))[0])!=base:return q,{'table':key,'row':r,'swapped_columns':[col,col+1]}
                except Exception:pass
    raise RuntimeError('未找到有效数值替换')

def run(tid):
    folder=OUT/tid;folder.mkdir(exist_ok=True)
    try:
        p,change=mutate(tid);(folder/'project.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf8')
        for a,b in [('preview.py','source.py'),('original.py','original.py')]:shutil.copy2(WEB/'assets/sources'/tid/a,folder/b)
        with (folder/'render.log').open('w',encoding='utf8') as log:
            subprocess.run([sys.executable,'-X','utf8',str(WEB/'editor_backend/worker.py'),str(folder)],stdout=log,stderr=log,timeout=240)
        status=json.loads((folder/'status.json').read_text(encoding='utf8'));assert status['state']=='done',status
        actual=json.loads((folder/'data_used.json').read_text(encoding='utf8'))['inputs'];expected=serial(prepare(copy.deepcopy(p))[0])
        assert digest(actual)==digest(expected),'实际绘图输入与编辑后的数据不一致'
        base=WEB/'verification/catalog-editor'/tid/'preview.png'
        different=not base.exists() or base.read_bytes()!=(folder/'preview.png').read_bytes()
        result=dict(id=tid,state='done',change=change,actual_inputs_match=True,image_changed=different)
        if not different:result['state']='unchanged-image'
    except Exception as e:result=dict(id=tid,state='error',message=str(e))
    (folder/'test-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(tid,result['state'],flush=True);return result
ids=sys.argv[1:] or list(SPECS)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(run,ids))
(OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
print('PASS',sum(r['state']=='done' for r in results),'/',len(results),flush=True)
