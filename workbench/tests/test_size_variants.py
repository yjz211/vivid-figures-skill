"""Exercise real template rendering after changing data cardinality, not just values."""
from pathlib import Path
import sys,json,copy,subprocess,concurrent.futures,shutil,hashlib
WEB=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(WEB/'editor_backend'))
from schema import SPECS,CONTRACTS,sample,prepare,serial
OUT=WEB/'verification/size-variants';OUT.mkdir(exist_ok=True)

def tabs(p):return p.get('tables',{'data':p['table']})
def sync(p):
    if 'tables' in p:p['table']=p['tables'][p['active_table']]
    elif 'values' in p['mapping']:
        p['mapping']['values']=list(range(1,len(p['table']['headers'])))
        p['mapping']['errors']={}
    return p
def numeric(x):
    try:return float(x)
    except (TypeError,ValueError):return None
def next_label(values):
    a=[numeric(v) for v in values]
    if all(v is not None for v in a):return max(a)+max((max(a)-min(a))/max(len(a)-1,1),1)
    s=str(values[-1])+'（新增）'
    while s in values:s+='新'
    return s
def shape(p):return {k:[len(t['rows']),len(t['headers'])] for k,t in tabs(p).items()}

def variant(base,mode):
    p=copy.deepcopy(base);tt=tabs(p);tid=p['template'];first=next(iter(tt.values()));n=len(first['rows']);h=first['headers'];labels=[r[0] for r in first['rows']]
    if tid=='competition.surface_3d' and mode.startswith('rows'):
        ys=list(dict.fromkeys(r[1] for r in first['rows']))
        if mode=='rows_less':first['rows']=[r for r in first['rows'] if r[1]!=ys[-1]]
        else:first['rows'] += [[r[0],next_label(ys),r[2]] for r in list(first['rows']) if r[1]==ys[-1]]
        return sync(p)
    if mode.startswith('groups'):
        if not isinstance(labels[0],str) or len(set(labels))==n:return None
        groups=list(dict.fromkeys(labels));g=groups[-1]
        if mode=='groups_less':
            if len(groups)<2:return None
            for t in tt.values():
                if any(r[0]==g for r in t['rows']):t['rows']=[r for r in t['rows'] if r[0]!=g]
        else:
            new=next_label(groups)
            for t in tt.values():
                if any(r[0]==g for r in t['rows']):t['rows'] += [[new,*r[1:]] for r in list(t['rows']) if r[0]==g]
        return sync(p)
    if mode.startswith('rows'):
        if n<2:return None
        affected=[t for t in tt.values() if len(t['rows'])==n and [r[0] for r in t['rows']]==labels]
        # Shortening all aligned tables preserves sample identities. Square matrices need both axes.
        for t in affected:
            square=len(t['headers'])==n+1 and [str(r[0]) for r in t['rows']]==list(map(str,t['headers'][1:]))
            if mode=='rows_less':
                indices=[i for i in range(n) if i%4!=3] if n>8 else list(range(n-1))
                t['rows']=[t['rows'][i] for i in indices]
                if square:
                    t['headers']=[t['headers'][0],*[t['headers'][i+1] for i in indices]]
                    t['rows']=[[r[0],*[r[i+1] for i in indices]] for r in t['rows']]
            else:
                unique=len(set(map(str,labels)))==n
                if unique:
                    name=next_label(labels);row=[name,*t['rows'][-1][1:]]
                    t['rows'].append(row)
                    if square:
                        t['headers'].append(str(name))
                        for r in t['rows']:r.append(r[-1])
                else:t['rows']+=copy.deepcopy(t['rows'][::max(1,n//max(2,n//4))])
        return sync(p)
    specs=CONTRACTS[tid]['tables'] if tid in CONTRACTS else [{'key':'data','kind':'matrix' if SPECS[tid]['family'] in ['wide','matrix'] else 'columns'}]
    if specs[0]['kind']!='matrix' or len(h)<3:return None
    for spec in specs:
        t=tt[spec['key']]
        if spec['kind']!='matrix' or t['headers']!=h:continue
        # Use the original header snapshot; otherwise modifying the first table breaks alignment.
        if mode=='cols_less':
            t['headers']=t['headers'][:-1];t['rows']=[r[:-1] for r in t['rows']]
        else:
            t['headers']=[*t['headers'],str(next_label(t['headers'][1:]))]
            t['rows']=[[*r,r[-1]] for r in t['rows']]
    return sync(p)

def digest(x):return hashlib.sha256(json.dumps(serial(x),ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def run_case(tid,mode,p):
    dest=OUT/tid/mode;dest.mkdir(parents=True,exist_ok=True)
    result={'id':tid,'case':mode,'original_shape':shape(sample(tid)),'changed_shape':shape(p)}
    try:
        expected=prepare(copy.deepcopy(p))[0]
    except Exception as e:
        result.update(state='rejected',message=str(e));(dest/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');return result
    try:
        (dest/'project.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf8')
        for a,b in [('preview.py','source.py'),('original.py','original.py')]:shutil.copy2(WEB/'assets/sources'/tid/a,dest/b)
        with (dest/'render.log').open('w',encoding='utf8') as log:
            proc=subprocess.run([sys.executable,'-X','utf8',str(Path(__file__)), '--worker',str(dest)],stdout=log,stderr=log,timeout=180)
        if proc.returncode:raise RuntimeError((dest/'render.log').read_text(encoding='utf8')[-2000:])
        actual=json.loads((dest/'data_used.json').read_text(encoding='utf8'))['inputs']
        assert digest(actual)==digest(expected),'实际绘图输入与调整后的数据不一致'
        assert (dest/'preview.png').stat().st_size>1000
        result.update(state='passed',actual_inputs_match=True)
    except Exception as e:result.update(state='error',message=str(e))
    (dest/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(tid,mode,result['state'],flush=True);return result

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--worker':
        from matplotlib.figure import Figure
        original_save=Figure.savefig
        def audited_save(fig,*a,**kw):
            audit=[{'lines':[len(line.get_xdata()) for line in ax.lines], 'patches':len(ax.patches), 'xticks':len(ax.get_xticks()),'texts':len(ax.texts),'visible_texts':sum(t.get_visible() for t in ax.texts),'width':fig.get_figwidth(),'height':fig.get_figheight()} for ax in fig.axes]
            (Path(sys.argv[2])/'artist-audit.json').write_text(json.dumps(audit),encoding='utf8')
            return original_save(fig,*a,**kw)
        Figure.savefig=audited_save
        from engine import render_project
        render_project(Path(sys.argv[2]));sys.exit(0)
    ids=[x for x in sys.argv[1:] if not x.startswith('--')] or list(SPECS)
    cases=[];plan=[]
    for tid in ids:
        b=sample(tid)
        for mode in ['rows_less','rows_more','cols_less','cols_more','groups_less','groups_more']:
            p=variant(b,mode)
            if p is None or shape(p)==shape(b):continue
            if '--retry' in sys.argv:
                report=OUT/tid/mode/'result.json'
                if not report.exists() or json.loads(report.read_text(encoding='utf8'))['state']!='error':continue
            cases.append((tid,mode,p))
            try:prepare(copy.deepcopy(p));state='accepted';msg=''
            except Exception as e:state='rejected';msg=str(e)
            plan.append({'id':tid,'case':mode,'state':state,'message':msg,'shape':shape(p)})
    (OUT/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf8')
    from collections import Counter
    print('PLAN',len(cases),dict(Counter(r['state'] for r in plan)),flush=True)
    if '--plan' not in sys.argv:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(lambda a:run_case(*a),cases))
        (OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
        print('RESULT',dict(Counter(r['state'] for r in results)),flush=True)
