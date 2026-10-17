"""VA-003 — 双侧输入输出包围的多机制平台.
Read TEMPLATE.md for supported edits and component semantics.
See ATTRIBUTION.md for derived geometry and rights.
"""
from pathlib import Path
import sys
try:
    from diagram import Diagram,glyph,run_recipe
except ModuleNotFoundError:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'lib'))
    from diagram import Diagram,glyph,run_recipe


def build(c):
    """Keep coloured internal objects, bookend input/output stacks and a platform frame."""
    d=Diagram(1100,430,c['title'],palette=c.get('palette'))
    d.rect(4,4,1092,422,sw=2.5)
    d.text(105,25,c.get('input_title','Input description'),size=19,weight='bold')
    d.text(999,25,c.get('output_title','Outputs'),size=19,weight='bold')
    for i,item in enumerate(c['inputs']):
        yy=44+i*157
        with d.group(f'input-{i}',(18,yy,172,145),role='object'):
            d.rect(18,yy,172,145,rx=3,sw=1.6)
            d.text(104,yy+20,item['title'],size=19,weight='bold',width=158)
            glyph(d,f'input-object-{i}',31,yy+44,146,87,item['object'])
    modules=c['modules'];n=len(modules)
    if n!=3:raise ValueError('This recipe exposes three distinct subsystem layouts; edit layout code for a different topology')
    with d.group('platform',(218,20,665,390),role='region'):
        d.rect(218,20,665,390,rx=6,stroke='#365971',sw=1.6)
        for i,module in enumerate(modules):
            xx=230+i*215;ww=203
            with d.group(f'module-{i}',(xx,34,ww,332),role='region'):
                d.rect(xx,34,ww,303,rx=4,stroke='#365971',sw=1.4)
                d.rect(xx+10,45,ww-20,28,fill='grey',sw=1.2)
                d.text(xx+ww/2,59,module['heading'],size=18,weight='bold',width=ww-30)
                mode=module['layout']
                if mode=='transform':
                    d.text(xx+ww/2,91,module['section_labels'][0],size=18,weight='bold')
                    with d.group(f'module-{i}-graph',(xx+13,107,ww-26,71),role='object'):
                        d.rect(xx+13,107,ww-26,71,fill=module.get('fill','pink'),sw=1)
                        glyph(d,f'module-{i}-graph-object',xx+23,116,ww-46,49,module['graph'])
                    d.path([(xx+ww/2,180),(xx+ww/2,195)],arrow=True)
                    d.text(xx+ww/2,211,module['section_labels'][1],size=18,weight='bold')
                    glyph(d,f'module-{i}-artifact',xx+21,228,ww-42,70,module['artifact'])
                elif mode=='engines':
                    engines=module['engines']; eh=43
                    for j,engine in enumerate(engines):
                        yy=91+j*59
                        d.node(f'engine-{j}',xx+12,yy,125,eh,engine['label'],fill=engine['color'],size=18)
                        d.path([(xx+138,yy+eh/2),(xx+151,yy+eh/2)],arrow=True,sw=1.2)
                    d.node('fusion',xx+153,91,38,len(engines)*59-16,'',fill='grey')
                    t=d.text(xx+172,91+(len(engines)*59-16)/2,module['fusion'],size=18);t.set('transform',f'rotate(-90 {xx+172} {91+(len(engines)*59-16)/2})')
                    d.node('postprocess',xx+12,282,ww-24,33,module['postprocess'],fill='grey',size=18)
                elif mode=='search':
                    glyph(d,f'module-{i}-search',xx+14,91,ww-28,154,module['graph'])
                    d.node('search-rule',xx+12,259,ww-24,56,module['rule'],fill=module.get('fill','pink'),size=18)
                else:raise ValueError('Unknown subsystem layout '+mode)
                d.text(xx+ww/2,350,module['name'],size=18,weight='bold',width=ww-12)
        d.text(550,389,c['platform_name'],size=20,weight='bold',width=620)
    for i,item in enumerate(c['outputs']):
        yy=44+i*112
        with d.group(f'output-{i}',(912,yy,171,100),role='object'):
            d.rect(912,yy,171,100,rx=3,sw=1.4)
            d.text(997,yy+17,item['title'],size=18,weight='bold',width=158)
            glyph(d,f'output-object-{i}',925,yy+32,145,61,item['object'])
        d.edge(f'platform-output-{i}','platform',f'output-{i}',[(883,yy+47),(910,yy+47)],arrow=True)
    for i,item in enumerate(c['inputs']):
        yy=44+i*157+73
        d.edge(f'platform-input-{i}',f'input-{i}','platform',[(190,yy),(216,yy)],arrow=True)
    return d


if __name__=='__main__':run_recipe(build,__file__)
