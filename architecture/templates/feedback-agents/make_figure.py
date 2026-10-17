"""VA-004 — 多主体反馈与共享资源调度.
Read TEMPLATE.md for supported edits and component semantics.
See ATTRIBUTION.md for derived geometry and rights.
"""
from pathlib import Path
import sys
try:
    from diagram import Diagram, run_recipe
except ModuleNotFoundError:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"lib"))
    from diagram import Diagram, run_recipe
from font_assets import apply_font_profile
INK='#000000'
def box(d,x,y,w,h,fill='white',dash=None):
    return d.rect(x,y,w,h,fill=fill,stroke=INK,sw=1.65,dash=dash)
def label(d,x,y,value,size=21,fill=INK,anchor='middle'):
    return d.text(x,y,value,size=size,fill=fill,anchor=anchor)
def component(d,ident,bounds,text,fill='white',size=21):
    x,y,w,h=bounds
    with d.group(ident,bounds):
        box(d,x,y,w,h,fill)
        label(d,x+w/2,y+h/2,text,size)
def build(c):
    """Three per-vSSD agents exchange actions and reward with admission control."""
    if len(c['agents'])!=3 or len(c['resources'])!=2:
        raise ValueError('Reference layout uses 3 agents and 2 resource stacks; edit geometry for other counts.')
    if c.get('font_profile','reference-system')!='reference-system':
        raise ValueError('This asset supports reference-system Arial; no portable sans family is configured.')
    d=Diagram(780,678,c['title'])
    d.root.set('font-family','Arial')
    for i,a in enumerate(c['agents']):
        x=27+i*267; cx=x+99
        component(d,f'workload-{i}',(x+27,18,150,30),a['input'])
        with d.group(f'agent-{i}',(x,69,198,180),role='region'):
            box(d,x,69,198,180,'#fff2cc')
            label(d,cx,85,a['name'])
            with d.group(f'rl-agent-{i}',(x+18,102,162,138),role='region'):
                box(d,x+18,102,162,138,'#d5e8d4')
                label(d,cx,116,'RL Agent')
                component(d,f'monitor-{i}',(x+27,135,144,30),a['monitor'],'#e1d5e7')
                with d.group(f'policy-{i}',(x+27,201,144,30)):
                    box(d,x+27,201,144,30,'#76608a')
                    label(d,cx,216,a['policy'],21,'white')
                d.edge(f'state-{i}',f'monitor-{i}',f'policy-{i}',[(cx,165),(cx,198)],color=INK)
        d.edge(f'workload-flow-{i}',f'workload-{i}',f'agent-{i}',[(cx,48),(cx,67)],color=INK)
    label(d,252,151,'...',25)
    label(d,519,151,'...',25)
    with d.group('shared-system',(21,357,738,297),role='region'):
        box(d,21,357,738,297)
        component(d,'admission',(84,378,594,39),c['admission'],'#f8cecc')
        component(d,'manager',(87,528,234,69),c['manager'],'#dae8fc',23)
        with d.group('resource-pool',(381,486,318,156),role='region'):
            box(d,381,486,318,156,'#ffe6cc','6 4')
            for j,resource in enumerate(c['resources']):
                yy=501+j*69
                with d.group(f'resource-{j}',(420,yy,192,39),role='object',description='Overlapping ghost superblock records'):
                    for dx,dy in [(0,0),(5,5),(10,10)]:
                        box(d,420+dx,yy+dy,182,29,'#8092a2')
                    label(d,521,yy+25,resource,19,'white')
            label(d,540,630,c['pool_name'],20)
        label(d,45,632,c['system_name'],25,anchor='start')
    action_paths=[[(93,249),(135,375)],[(354,249),(354,375)],[(636,249),(585,375)]]
    reward_paths=[[(189,378),(153,252)],[(432,378),(432,252)],[(636,378),(690,252)]]
    for i in range(3):
        d.edge(f'action-{i}',f'agent-{i}','admission',action_paths[i],color=INK)
        d.edge(f'feedback-{i}','admission',f'agent-{i}',reward_paths[i],color=INK)
        label(d,[58,310,568][i],285,c['action_label'])
        label(d,[222,475,704][i],322,c['feedback_label'])
    d.edge('manage','manager','resource-pool',[(321,562),(378,562)],dash='4 3',color=INK)
    d.edge('block','admission','resource-pool',[(513,417),(513,483)],color=INK)
    d.edge('harvesting','resource-pool','admission',[(513,486),(513,420)],color=INK)
    label(d,603,451,c['allocation_label'],24)
    apply_font_profile(d,c.get('font_profile','reference-system'))
    return d
if __name__=='__main__':run_recipe(build,__file__)
