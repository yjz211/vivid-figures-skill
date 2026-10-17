"""VA-002 — 逐阶段推导与中间产物列.
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
    """Keep the input / transformation / artifact columns and the runtime return path."""
    stages=c['stages'];n=len(stages);rh=112;top=46;H=top+n*rh+32
    d=Diagram(900,H,c['title'],palette=c.get('palette'))
    d.text(150,23,c.get('input_title','Inputs'),size=21,weight='bold')
    d.text(444,23,c.get('planner_title','Execution planner'),size=21,weight='bold')
    d.text(734,23,c.get('artifact_title','Intermediate objects'),size=21,weight='bold')
    with d.group('planner',(306,40,273,n*rh+9),role='region'):
        d.rect(306,40,273,n*rh+9,fill='white',stroke='#a7b0b7',dash='7 4')
        for i,stage in enumerate(stages):
            yy=top+i*rh
            with d.group(f'stage-{i}',(320,yy,250,92),role='component'):
                d.rect(324,yy+5,246,87,fill='#c3c7c8',stroke='none',rx=3)
                d.rect(320,yy,246,87,fill=stage.get('fill','#d9e2dc'),rx=3,sw=1.8)
                d.text(343,yy+17,str(i+1),size=17,fill='#62756c',weight='bold')
                d.text(443,yy+48,stage['name'],size=23,weight='bold',width=214)
            if i:d.edge(f'stage-link-{i}',f'stage-{i-1}',f'stage-{i}',[(443,yy-rh+87),(443,yy)],arrow=True)
    for i,stage in enumerate(stages):
        yy=top+i*rh
        with d.group(f'artifact-{i}',(604,yy,277,96),role='object'):
            d.rect(604,yy,277,96,fill='white',stroke='#9b8e85',dash='3 3',rx=5,sw=1.3)
            d.text(742,yy+17,stage['artifact_title'],size=18,fill=stage.get('accent','#ad4d42'),italic=True,width=254)
            glyph(d,f'artifact-glyph-{i}',627,yy+34,228,53,stage['artifact'])
        d.edge(f'artifact-link-{i}',f'stage-{i}',f'artifact-{i}',[(566,yy+43),(601,yy+43)],arrow=True,color='#74857a')
    for i,item in enumerate(c['inputs']):
        yy=top+item.get('row',i)*rh
        hh=item.get('height',116)
        with d.group(f'input-{i}',(18,yy,253,hh),role='object'):
            d.rect(18,yy,253,hh,fill=item.get('fill','white'),dash='7 4')
            d.text(144,yy+20,item['title'],size=20,width=230)
            glyph(d,f'input-glyph-{i}',36,yy+40,215,hh-53,item['object'])
        target=item.get('target',min(i,n-1));end=top+target*rh+44
        d.edge(f'input-link-{i}',f'input-{i}',f'stage-{target}',[(271,yy+hh/2),(291,yy+hh/2),(291,end),(317,end)],arrow=True)
    yy=top+(n-1)*rh
    d.node('runtime',20,yy,251,87,c['runtime'],fill='#d9e2dc',size=23,weight='bold',rx=3)
    d.edge('execution','stage-'+str(n-1),'runtime',[(320,yy+44),(274,yy+44)],arrow=True)
    d.text(145,yy+109,c.get('runtime_note','Execution environment'),size=17,italic=True,fill='#6c7479')
    return d


if __name__=='__main__':run_recipe(build,__file__)
