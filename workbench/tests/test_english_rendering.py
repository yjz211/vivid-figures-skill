"""Real isolated-worker English renders, input integrity, and standalone export.

Run with the workbench Python environment. Artifacts stay in verification/english.
No API server or model connection is needed. --only accepts template IDs.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image

WEB = Path(__file__).resolve().parents[1]
BACKEND = WEB / 'editor_backend'
OUT = WEB / 'verification/english'
sys.path.insert(0, str(BACKEND))
from schema import prepare, sample, serial

CASES = [
    'basic.grouped_bar', 'basic.line', 'basic.scatter_regression',
    'advanced.cluster_heatmap', 'advanced.grouped_bar_3d', 'basic.multipanel',
    'advanced.grouped_radial_bar', 'screenshot.mesh_surface_3d',
    'template.sem_violin_pearson',
]
CJK = re.compile(r'[\u3400-\u9fff]')


def fixture(tid):
    """Use non-demo labels and values; mappings affect only displayed text."""
    p = sample(tid)
    s = p['settings']
    s.update(language='en', english_labels={}, palette='pastel-girl')
    expected = []
    if tid == 'basic.grouped_bar':
        p['table'] = {'headers':['Evaluation scenario', '改进方法', 'Strong baseline', 'Compact baseline'],
            'rows':[['Short-horizon prediction',86.7,81.3,78.9], ['长期预测',79.8,74.1,71.5],
                    ['Cross-region transfer',91.2,85.6,82.4], ['Noisy observations',83.5,77.9,74.6]]}
        s['english_labels'] = {'改进方法':'Proposed adaptive method', '长期预测':'Long-horizon forecasting'}
        s['title'] = 'Robust prediction across evaluation scenarios'
        s['ylabel'] = 'Prediction score (%)'
        s['width'] = 11
        expected = ['Proposed adaptive method', 'Long-horizon forecasting']
    elif tid == 'basic.line':
        p['table']['headers'] = ['Observation year','改进方法','Seasonal baseline','Linear baseline']
        p['table']['rows'][3][1] = 81.25
        s.update(title='Long-term operational performance', ylabel='Mean response score')
        s['english_labels'] = {'改进方法':'Adaptive forecasting method'}
        expected = ['Adaptive forecasting method','Observation year']
    elif tid == 'basic.scatter_regression':
        p['table']['headers'] = ['标准化投入','Measured production output (units)']
        p['table']['rows'][0][1] += .135
        s['english_labels'] = {'标准化投入':'Standardized investment (index)'}
        s['title'] = 'Investment and measured production response'
        expected = ['Standardized investment (index)','Measured production output (units)']
    elif tid == 'advanced.cluster_heatmap':
        p['table']['headers'] = ['Monitoring location','响应效率','Forecast error','Energy intensity',
                                'System reliability','Transfer capacity','Control stability','Operating cost','Output quality']
        for i,row in enumerate(p['table']['rows']): row[0] = f'Monitoring station {i+1:02d}'
        p['table']['rows'][0][1] = 1.275
        s.update(title='Standardized performance indicators', width=11, height=8)
        s['english_labels'] = {'响应效率':'Response efficiency'}
        expected = ['Response efficiency','Monitoring station 01']
    elif tid == 'advanced.grouped_bar_3d':
        p['table']['headers'] = ['Site','Baseline control','Adaptive control','Peak demand','Low demand','Robust control']
        for i,row in enumerate(p['table']['rows']): row[0] = ['Northern site','Eastern site','Central site','Coastal site','Western site'][i]
        p['table']['rows'][0][1] = 33.75
        s.update(xlabel='Monitoring location', ylabel='Operating condition', zlabel='Response improvement (%)')
        expected = ['Northern site','Adaptive control','Response improvement (%)']
    elif tid == 'basic.multipanel':
        tables=p['tables']
        tables['line']['headers'] = ['Observation interval','Adaptive estimate','Baseline estimate','Robust estimate']
        tables['bar']['headers'] = ['Validation scenario','Adaptive model','Reference model']
        for i,row in enumerate(tables['bar']['rows']): row[0] = f'Case {i+1}'
        tables['scatter']['headers'] = ['Study cohort','Measured input','Measured response']
        tables['hist']['headers'] = ['Study cohort','Residual magnitude']
        names={'组1':'High-load cohort','组2':'Mixed-load cohort','组3':'Low-load cohort'}
        for key in ('scatter','hist'):
            for row in tables[key]['rows']: row[0] = names[row[0]]
        tables['line']['rows'][0][1] = .37
        s.update(title='Operational validation across complementary views',width=11,height=9)
        expected = ['Adaptive estimate','High-load cohort','Residual magnitude']
    elif tid == 'advanced.grouped_radial_bar':
        names=['Detection accuracy','Spatial grounding','Dense prediction','Document layout','Screen interaction','Text recognition']
        p['tables'] = {
            'scores':{'headers':['Task','改进方案','Reference model','Compact model'],
                      'rows':[[name,*vals] for name,vals in zip(names,[[83.4,76.2,71.5],[78.8,75.1,68.6],[69.4,65.7,60.1],[87.5,80.3,77.2],[82.1,84.9,74.6],[75.8,70.2,65.1]])]},
            'labels':{'headers':['Task','Family','Dataset'],
                      'rows':[[name,'Visual understanding' if i<3 else 'Document interaction',f'Evaluation subset {i+1}'] for i,name in enumerate(names)]},
        }
        p['active_table']='scores'
        s.update(title='Adaptive model',english_labels={'改进方案':'Adaptive model'})
        expected = ['Detection accuracy','Visual understanding','Reference model']
    elif tid == 'screenshot.mesh_surface_3d':
        p['tables']['grid']['headers'][0] = 'Sampling coordinate'
        p['tables']['grid']['rows'][0][1] = .0325
        s.update(title='响应曲面',xlabel='Control intensity (standardized)',ylabel='Operating load (standardized)',zlabel='Predicted response',width=8,height=6)
        s['english_labels']={'响应曲面':'Adaptive response surface'}
        expected = ['Adaptive response surface']
    elif tid == 'template.sem_violin_pearson':
        # Four constructs keep the full residual-violin plus Pearson layout clear.
        table=p['tables']['scores']
        table['headers']=['Participant','实际使用','Attitude','Perceived control','Behavioural intention']
        table['rows']=[[f'Participant {i+1:03d}',*row[1:5]] for i,row in enumerate(table['rows'])]
        table['rows'][0][1] += .125
        s.update(width=15,height=7,english_labels={'实际使用':'Actual usage'})
        expected=['Actual usage','Behavioural intention']
    if p.get('tables'):
        p['table']=p['tables'][p['active_table']]
    return p, expected


def display_texts(svg, manifest):
    root=ET.fromstring(svg)
    texts=[''.join(node.itertext()) for node in root.iter() if node.tag.rsplit('}',1)[-1]=='text']
    # Matplotlib stores display strings in comments when using vector glyph paths.
    texts.extend(re.findall(r'<!--(.*?)-->',svg,re.S))
    for item in manifest.get('objects',[]):
        props=item.get('props',{})
        texts.extend(v for k,v in props.items() if k in ('text','label') and isinstance(v,str) and props.get('visible',True))
    return texts, root


def validate(folder,project,expected):
    evidence=json.loads((folder/'data_used.json').read_text('utf8'))
    expected_inputs=serial(prepare(copy.deepcopy(project))[0])
    assert evidence['inputs']==expected_inputs, 'Executed arrays/settings differ from validated original input'
    assert json.loads((folder/'project.json').read_text('utf8'))==project, 'Source data was changed while translating'
    config=json.loads((folder/'.vivid/config.json').read_text('utf8'))
    assert config['language']=='en' and config['english_labels']==project['settings']['english_labels']
    manifest=json.loads((folder/'objects.json').read_text('utf8'))
    svg=(folder/'figure.svg').read_text('utf8')
    texts,root=display_texts(svg,manifest)
    unexpected=[t.strip() for t in texts if CJK.search(t)]
    assert not unexpected, 'Untranslated display text: '+repr(unexpected[:12])
    joined=' '.join(texts).replace('\n',' ')
    for phrase in expected:
        assert phrase in joined, 'Expected English label missing: '+phrase
    if project['template']=='template.sem_violin_pearson':
        # Text presence alone misses clipped vector glyphs at the component edge.
        import fitz
        component_width=float(next(node for node in root if node.tag.endswith('svg')).attrib['width'])
        with fitz.open(folder/'figure.pdf') as pdf:
            words=[word for word in pdf[0].get_text('words') if word[4] in ('Standardized','residual')]
        assert {word[4] for word in words}=={'Standardized','residual'}, 'Residual axis label missing from PDF'
        assert all(word[0]>=0 and word[2]<=component_width+.5 for word in words), 'Residual axis label clipped at component edge'
    tags=[node.tag.rsplit('}',1)[-1] for node in root.iter()]
    layers=sum(tags.count(t) for t in ('path','use','image'))
    assert layers>=15 or tags.count('image')>=1, 'Missing visible chart layers'
    pixels=np.asarray(Image.open(folder/'preview.png').convert('RGB'))
    assert min(pixels.shape[:2])>=500, 'Unexpectedly small preview'
    coverage=float(np.mean(np.min(pixels,axis=2)<235))
    assert coverage>.015, 'Chart is almost empty'
    assert len(manifest['objects'])>=4, 'Editable object inventory is empty'
    with zipfile.ZipFile(folder/'reproduce.zip') as z:
        names=z.namelist()
        for name in ('language_adapter.py','_utils/figure_language.py','project.json','source.py','engine.py'):
            assert name in names, 'Reproduction dependency missing: '+name
    return {'passed':True,'display_texts':len(texts),'editable_objects':len(manifest['objects']),
            'svg_layers':layers,'nonwhite_fraction':round(coverage,4),'original_data_preserved':True,
            'english_labels_present':expected,'notes':evidence['notes']}


def render_case(tid):
    folder=OUT/tid
    folder.mkdir(parents=True,exist_ok=True)
    p,expected=fixture(tid)
    before=copy.deepcopy(p)
    prepare(p)
    assert p==before, 'Input validation mutated the data'
    (folder/'project.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf8')
    source=WEB/'assets/sources'/tid
    shutil.copy2(source/'preview.py',folder/'source.py')
    shutil.copy2(source/'original.py',folder/'original.py')
    started=time.monotonic()
    with (folder/'render.log').open('w',encoding='utf8') as log:
        proc=subprocess.run([sys.executable,'-B','-X','utf8',str(BACKEND/'worker.py'),str(folder)],
            cwd=folder,stdout=log,stderr=log,timeout=240,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    status=json.loads((folder/'status.json').read_text('utf8'))
    assert proc.returncode==0 and status['state']=='done', status
    return {'template':tid,'folder':str(folder),'seconds':round(time.monotonic()-started,2),**validate(folder,p,expected)}


def reproduce():
    folder=OUT/'basic.grouped_bar'
    destination=OUT/'reproduction/basic.grouped_bar'
    destination.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(folder/'reproduce.zip') as archive:
        for name in archive.namelist():
            assert (destination/name).resolve().is_relative_to(destination.resolve()),name
        archive.extractall(destination)
    with (destination/'reproduction.log').open('w',encoding='utf8') as log:
        proc=subprocess.run([sys.executable,'-B','-X','utf8','run.py'],cwd=destination,
            stdout=log,stderr=log,timeout=180,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    assert proc.returncode==0, 'Standalone reproduction failed'
    first=np.asarray(Image.open(folder/'figure.png'))
    second=np.asarray(Image.open(destination/'figure.png'))
    assert first.shape==second.shape and np.array_equal(first,second), 'Standalone PNG pixels differ'
    return {'passed':True,'template':'basic.grouped_bar','pixels_identical':True,
            'language_helpers_bundled':True,'folder':str(destination)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only',nargs='+',choices=CASES)
    parser.add_argument('--skip-reproduce',action='store_true')
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    report_path=OUT/'rendering-results.json'
    report=json.loads(report_path.read_text('utf8')) if args.only and report_path.exists() else {'cases':[]}
    selected=args.only or CASES
    report['cases']=[r for r in report['cases'] if r['template'] not in selected]
    for tid in selected:
        try:result=render_case(tid)
        except Exception as error:result={'template':tid,'passed':False,'error':str(error)}
        report['cases'].append(result)
        print(json.dumps(result,ensure_ascii=False),flush=True)
    report['cases'].sort(key=lambda r:CASES.index(r['template']))
    if not args.skip_reproduce and 'basic.grouped_bar' in selected and any(r['template']=='basic.grouped_bar' and r['passed'] for r in report['cases']):
        try:report['reproduction']=reproduce()
        except Exception as error:report['reproduction']={'passed':False,'error':str(error)}
        print(json.dumps({'reproduction':report['reproduction']},ensure_ascii=False),flush=True)
    report['passed']=all(r['passed'] for r in report['cases']) and report.get('reproduction',{'passed':True})['passed']
    (OUT/'rendering-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    raise SystemExit(0 if report['passed'] else 1)


if __name__=='__main__':
    main()
