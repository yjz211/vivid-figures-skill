"""VA-001 — 控制逻辑、异构网络与节点放大.
Read TEMPLATE.md for supported edits and component semantics.
See ATTRIBUTION.md for derived geometry and rights.
"""
from pathlib import Path
import sys
try:
    from diagram import Diagram,run_recipe
except ModuleNotFoundError:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'lib'))
    from diagram import Diagram,run_recipe
from network_parts import piece,label,source_block,source_edge,LAYOUT,SERIF
from font_assets import apply_font_profile


def build(c):
    """Same-content reconstruction: controller, graph, inset and event/legend rail."""
    _,_,w,h=map(float,LAYOUT['source_viewBox'].split())
    d=Diagram(w,h,c['title']);d.root.set('font-family',SERIF);d.root.set('fill','#000000')
    d.root.set('data-template-revision','network-inset-2')
    labels=c.get('labels',{})
    def block(ident,pieces,names=(),role='component'):
        source_block(d,ident,pieces,names,role=role,overrides=labels)
    def edge(ident,a,b,part,kind='flow'):
        source_edge(d,ident,a,b,part,kind=kind)

    with d.group('controller',(0,0,163,127),role='region'):
        piece(d,'controller-frame')
        block('profiler',['profiler-box'],['profiler'])
        block('planner',['planner-box'],['planner'])
        block('scheduler',['scheduler-box'],['scheduler'])
        block('init-worker',[],['init-worker'],role='output')
        block('worker-exec',[],['worker-exec'],role='output')
        edge('profile-to-plan','profiler','planner','profile-to-plan')
        edge('plan-to-schedule','planner','scheduler','plan-to-schedule')
        edge('plan-to-init','planner','init-worker','plan-to-init')
        edge('schedule-to-exec','scheduler','worker-exec','schedule-to-exec')
        label(d,'control-edge-labels',labels);label(d,'controller-title',labels)

    with d.group('cluster',(176,6,192,118),role='region'):
        block('coordinator',['coordinator-box'],['coordinator'])
        for site in 'abdecf':block('site-'+site,['node-'+site],role='object')
        for a,b in [('a','d'),('b','d'),('c','d'),('d','e'),('d','f')]:
            edge(a+'-to-'+b,'site-'+a,'site-'+b,a+'-to-'+b,'example-execution')
        for site in 'abc':edge('dispatch-'+site,'coordinator','site-'+site,'dispatch-'+site)
        for site in 'ef':edge('return-'+site,'site-'+site,'coordinator','return-'+site,'return')
    for which in ['top','bottom']:
        edge('controller-zoom-'+which,'coordinator','controller','controller-zoom-'+which,'expansion-guide')
        edge('node-zoom-'+which,'site-d','node-detail','node-zoom-'+which,'expansion-guide')

    with d.group('node-detail',(381,34,163,88),role='region'):
        piece(d,'detail-frame')
        for i in [1,2,3]:
            block(f'queue-{i}',[f'queue-{i}-box'],[f'queue-{i}'])
            block(f'layer-{i}',[f'layer-{i}-box'],[f'layer-{i}'])
            edge(f'q{i}-l{i}',f'queue-{i}',f'layer-{i}',f'q{i}-l{i}')
            if i<3:edge(f'l{i}-q{i+1}',f'layer-{i}',f'queue-{i+1}',f'l{i}-q{i+1}')
        with d.group('node-output',(537,66,7,7),role='port',export=False):pass
        edge('node-output-edge','layer-3','node-output','node-output')
        label(d,'detail-title',labels)
    block('request-tensor',['tensor-box'],['tensor'],role='input')
    for i in [1,2,3]:edge(f'input-q{i}','request-tensor',f'queue-{i}',f'input-q{i}')

    block('new-request',['request-event-box'],['request-event'],role='input')
    block('worker-finished',['finished-event-box'],['finished-event'],role='input')
    edge('request-to-scheduler','new-request','scheduler','event-to-scheduler')
    block('event-bus',['events-horizontal'],role='connector')
    edge('finished-to-bus','worker-finished','event-bus','finished-join','event-join')
    with d.group('legend',(187,127,311,24),role='legend'):
        piece(d,'legend-frame')
        for name in ['type1','type2','type3','layer']:
            block('legend-'+name,['legend-'+name],['legend-'+name],role='legend-item')
    apply_font_profile(d,c.get('font_profile','reference-system'))
    return d


if __name__=='__main__':run_recipe(build,__file__)
