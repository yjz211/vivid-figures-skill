from test_size_variants import *
import numpy as np

def matrix_case(tid,n,m):
    p=sample(tid);p['table']={'headers':['分类',*[f'系列{j+1}' for j in range(m)]],'rows':[[f'分类{i+1}',*[float(3+(i*7+j*11)%43) for j in range(m)]] for i in range(n)]}
    p['mapping']={'category':0,'values':list(range(1,m+1)),'errors':{}}
    return p

if __name__=='__main__':
    cases=[]
    for n,m in [(1,1),(3,4),(10,12),(11,12),(10,13)]:cases.append(('advanced.grouped_bar_3d',f'boundary_{n}x{m}',matrix_case('advanced.grouped_bar_3d',n,m)))
    for tid,n,m in [('basic.grouped_bar',24,6),('basic.line',80,5),('advanced.cluster_heatmap',30,12)]:cases.append((tid,f'dense_{n}x{m}',matrix_case(tid,n,m)))
    p=sample('advanced.ridgeline');rng=np.random.default_rng(43)
    p['table']['rows']=[[f'组{j+1}',float(x)] for j in range(12) for x in rng.normal(j,1,25)]
    cases.append(('advanced.ridgeline','dense_12groups',p))
    # Matched pairs of one observation table and its analysis output grow together.
    for tid in ['advanced.method_heatmap','template.shap_contribution','screenshot.fan_violin_heatmap','screenshot.correlation_network']:
        for mode in ['linked_less','linked_more']:
            p=sample(tid);t=p['tables'];grow=mode.endswith('more')
            if tid=='advanced.method_heatmap':
                d=t['data'];r=t['directions'];name=d['headers'][-1]+'新'
                if grow:
                    d['headers'].append(name)
                    for row in d['rows']:row.append(row[-1])
                    r['rows'].append([name,r['rows'][-1][1]])
                else:
                    d['headers'].pop();d['rows']=[r[:-1] for r in d['rows']];r['rows'].pop()
            elif tid=='template.shap_contribution':
                name=t['features']['headers'][-1]+'新'
                for key in ['features','shap']:
                    d=t[key]
                    if grow:
                        d['headers'].append(name);d['rows']=[[*r,r[-1]] for r in d['rows']]
                    else:d['headers'].pop();d['rows']=[r[:-1] for r in d['rows']]
                if grow:t['groups']['rows'].append([name,t['groups']['rows'][-1][1]])
                else:t['groups']['rows'].pop()
            elif tid=='screenshot.fan_violin_heatmap':
                d=t['heat'];last=d['headers'][-1];name=last+'新'
                if grow:
                    d['headers'].append(name);d['rows']=[[*r,r[-1]] for r in d['rows']]
                    t['samples']['rows'] += [[name,r[1]] for r in list(t['samples']['rows']) if r[0]==last]
                else:
                    d['headers'].pop();d['rows']=[r[:-1] for r in d['rows']]
                    t['samples']['rows']=[r for r in t['samples']['rows'] if r[0]!=last]
            else:
                d=t['corr'];name=d['headers'][-1]+'新'
                if grow:d['rows'].append([name,*d['rows'][-1][1:]])
                else:d['rows'].pop()
                for d in t.values():
                    if grow:d['headers'].append(name);d['rows']=[[*r,r[-1]] for r in d['rows']]
                    else:d['headers'].pop();d['rows']=[r[:-1] for r in d['rows']]
            sync(p);cases.append((tid,mode,p))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(lambda a:run_case(*a),cases))
    for r in results:
        expected='rejected' if r['case'] in ['boundary_11x12','boundary_10x13'] else 'passed'
        assert r['state']==expected,r
    (OUT/'boundary-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
    print('Boundary checks passed:',len(results))
