"""Read-only style evidence and differences; findings are review hints, never a visual verdict.

Does not import or execute a plotting script. Only literal arithmetic and bounded
literal loops are interpreted; data-dependent expressions remain unknown.
"""
from __future__ import annotations
import argparse
import ast
from collections import defaultdict
import difflib
import json
from pathlib import Path
import sys
from review_attention import (AXIS_CALLS, BANDS, value_names, geometry_dependencies,
                              focused_findings, finding_priority, summary_lines)

UNKNOWN = object()
LAYOUT = set('figure subplots subplot add_subplot add_axes GridSpec add_gridspec set_size_inches subplots_adjust tight_layout set_position'.split())
DRAW = set('plot scatter bar barh hist stairs step fill fill_between fill_betweenx violinplot boxplot heatmap imshow pcolormesh contour contourf plot_surface plot_trisurf pie hexbin quiver streamplot errorbar hlines vlines axhline axvline axhspan axvspan annotate text colorbar add_patch add_collection add_collection3d set_alpha set_facecolor set_edgecolor set_linewidth'.split())
DRAW.update('PathPatch Rectangle Polygon Ellipse Circle FancyArrowPatch PolyCollection Poly3DCollection LineCollection kdeplot histplot regplot stackplot _lighten'.split())
DRAW.update('Sunburst Scatter Scatter3d Cone Isosurface Volume Surface Mesh3d add_trace initialize_from_matrix'.split())
DRAW.update(LAYOUT)
DRAW.update({'set_fontsize', 'set_fontweight', 'set_fontfamily'})
DRAW.update(AXIS_CALLS)
PARAMS = set('alpha linewidth linewidths lw edgecolor edgecolors marker markeredgecolor markeredgewidth linestyle linestyles ls fill hatch cmap levels zdir center vmin vmax mask annot yerr xerr showmeans showmedians showextrema zorder'.split())
PARAMS.update('opacity colorscale cmin cmax isomin isomax surface_count sizeref sizemode textinfo stackgroup baseline caps contours flatshading'.split())
PARAMS.update('figsize width_ratios height_ratios left right top bottom wspace hspace fontsize size fontweight weight fontfamily pad labelpad ncols nrows loc xy xytext textcoords xycoords ha va rotation boxstyle facecolor'.split())
PARAMS.update({'sharex', 'sharey', 'bbox_to_anchor', 'markersize'})
PARAMS.update({'orientation', 'axis', 'labelleft', 'labelright', 'labelbottom', 'labeltop'})
DATA_KEYS = {'levels', 'vmin', 'vmax', 'center', 'mask', 'yerr', 'xerr'}
STYLE_DICTS = {'boxprops', 'medianprops', 'whiskerprops', 'capprops', 'flierprops', 'wedgeprops', 'arrowprops'}
STYLE_DICTS.update({'bbox', 'fontdict', 'gridspec_kw', 'marker', 'line', 'link_kws', 'label_kws'})


def literal(node, env):
    if node is None:
        return UNKNOWN
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return env.get(node.id, UNKNOWN)
    if isinstance(node, (ast.List, ast.Tuple)):
        # Preserve known opacity/width fields even when a tuple's color is dynamic.
        return [literal(n, env) for n in node.elts]
    if isinstance(node, ast.UnaryOp):
        value = literal(node.operand, env)
        if type(value) in (int, float):
            if isinstance(node.op, ast.USub): return -value
            if isinstance(node.op, ast.UAdd): return value
    if isinstance(node, ast.BinOp):
        a, b = literal(node.left, env), literal(node.right, env)
        if type(a) in (int, float) and type(b) in (int, float):
            try:
                if isinstance(node.op, ast.Add): return a + b
                if isinstance(node.op, ast.Sub): return a - b
                if isinstance(node.op, ast.Mult): return a * b
                if isinstance(node.op, ast.Div): return a / b
            except (ZeroDivisionError, OverflowError): pass
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        args = [literal(n, env) for n in node.args]
        if node.func.id == 'range' and 1 <= len(args) <= 3 and all(type(v) is int and abs(v) <= 1000 for v in args):
            try:
                values = range(*args)
                if len(values) <= 64: return list(values)
            except ValueError: pass
        if node.func.id == 'enumerate' and len(args) == 1 and isinstance(args[0], list):
            return list(enumerate(args[0]))
    return UNKNOWN


def bind(target, value, env):
    if isinstance(target, ast.Name):
        env[target.id] = value
    elif isinstance(target, (ast.Tuple, ast.List)):
        for i, sub in enumerate(target.elts):
            bind(sub, value[i] if isinstance(value, (list, tuple)) and i < len(value) else UNKNOWN, env)


def method(call):
    if isinstance(call.func, ast.Attribute): return call.func.attr
    if isinstance(call.func, ast.Name): return call.func.id
    return ''


def fully_known(value):
    if value is UNKNOWN: return False
    if isinstance(value, (list, tuple)): return all(fully_known(v) for v in value)
    return True


def inspect_source(source):
    tree = ast.parse(source)
    records = []
    expansion = [0]

    def calls(node, env, context, loops):
        for call in ast.walk(node):
            if not isinstance(call, ast.Call) or method(call) not in DRAW: continue
            values = {k.arg: k.value for k in call.keywords if k.arg in PARAMS}
            for keyword in call.keywords:
                if keyword.arg not in STYLE_DICTS: continue
                value = keyword.value
                pairs = []
                if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == 'dict':
                    pairs = [(k.arg, k.value) for k in value.keywords]
                elif isinstance(value, ast.Dict):
                    pairs = [(k.value, v) for k, v in zip(value.keys, value.values) if isinstance(k, ast.Constant)]
                else:
                    values[keyword.arg] = value
                for key, expression in pairs:
                    if key in PARAMS | {'facecolor', 'color', 'width'}:
                        values[f'{keyword.arg}.{key}'] = expression
            setters = {'set_alpha': 'alpha', 'set_linewidth': 'linewidth', 'set_facecolor': 'facecolor', 'set_edgecolor': 'edgecolor'}
            setters.update(set_fontsize='fontsize', set_fontweight='fontweight', set_fontfamily='fontfamily')
            setters.update(set_xlabel='label', set_ylabel='label', set_xticks='ticks', set_yticks='ticks',
                           set_xticklabels='ticklabels', set_yticklabels='ticklabels')
            if method(call) in setters and call.args:
                values[setters[method(call)]] = call.args[0]
            if method(call) == '_lighten' and len(call.args) > 1:
                values['lightening'] = call.args[1]
            if method(call) in LAYOUT:
                for index, argument in enumerate(call.args): values['arg' + str(index)] = argument
            if method(call) in {'text', 'annotate'}:
                index = 2 if method(call) == 'text' else 0
                if len(call.args) > index: values['text'] = call.args[index]
                if method(call) == 'text' and len(call.args) >= 2:
                    values['x'], values['y'] = call.args[:2]
            props = {}
            for key, expression in values.items():
                value = literal(expression, env)
                props[key] = {'known': fully_known(value), 'value': value if fully_known(value) else None,
                              'expression': ast.unparse(expression)}
            band_loop = None
            if method(call) in BANDS:
                geometry = list(call.args[1:3]) + [k.value for k in call.keywords if k.arg in {'y1', 'y2', 'x1', 'x2'}]
                dependencies = set().union(*(value_names(arg) for arg in geometry))
                for loop in reversed(loops):
                    if dependencies & loop['geometry_names']:
                        band_loop = {k: loop[k] for k in ('line', 'count')}
                        break
            records.append({'method': method(call), 'line': call.lineno, 'end_line': call.end_lineno,
                            'code': ast.get_source_segment(source, call), 'context': context,
                            'receiver': ast.unparse(call.func.value) if isinstance(call.func, ast.Attribute) else '',
                            'band_loop': band_loop, 'properties': props})

    def block(statements, env, context=(), loops=()):
        for node in statements:
            # A list built through append/extend is not still its initial literal [].
            # Conservatively discard that value, including mutations inside loops;
            # otherwise later drawing loops can be incorrectly treated as empty.
            for call in ast.walk(node):
                if (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                        and call.func.attr in {'append', 'extend', 'insert', 'pop', 'clear', 'remove', 'sort', 'reverse', 'update', 'setdefault'}
                        and isinstance(call.func.value, ast.Name)):
                    env[call.func.value.id] = UNKNOWN
            if isinstance(node, (ast.For, ast.AsyncFor)):
                values = literal(node.iter, env)
                frame = dict(line=node.lineno, count=len(values) if isinstance(values, (list, tuple)) else None,
                             geometry_names=geometry_dependencies(node))
                if isinstance(values, (list, tuple)) and len(values) <= 64 and expansion[0] + len(values) <= 256:
                    expansion[0] += len(values)
                    for value in values:
                        nested = dict(env); bind(node.target, value, nested)
                        block(node.body, nested, context + (f'for@{node.lineno}',), loops + (frame,))
                else:
                    nested = dict(env); bind(node.target, UNKNOWN, nested)
                    block(node.body, nested, context + (f'data-dependent for@{node.lineno}',), loops + (frame,))
                block(node.orelse, dict(env), context, loops)
            elif isinstance(node, ast.If):
                # Both branches are possible. Do not claim runtime reachability.
                block(node.body, dict(env), context + (f'conditional@{node.lineno}',), loops)
                block(node.orelse, dict(env), context + (f'conditional@{node.lineno}',), loops)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                block(node.body, {}, context + (f'definition:{node.name}',))
            elif isinstance(node, (ast.With, ast.AsyncWith)):
                block(node.body, dict(env), context, loops)
            elif isinstance(node, ast.Try):
                block(node.body, dict(env), context + ('try',), loops)
                for handler in node.handlers: block(handler.body, dict(env), context + ('except',), loops)
                block(node.orelse, dict(env), context, loops)
                block(node.finalbody, dict(env), context, loops)
            else:
                calls(node, env, context, loops)
                if isinstance(node, ast.Assign):
                    for target in node.targets: bind(target, literal(node.value, env), env)
                elif isinstance(node, ast.AnnAssign):
                    bind(node.target, literal(node.value, env), env)
                elif isinstance(node, ast.AugAssign):
                    bind(node.target, UNKNOWN, env)
    block(tree.body, {})
    # rcParams assignments / update calls are style changes even outside drawing calls.
    for node in ast.walk(tree):
        values = {}
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Subscript) and ast.unparse(target.value).endswith('rcParams'):
                    key = literal(target.slice, {})
                    if isinstance(key, str): values[key] = node.value
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'update' and ast.unparse(node.func.value).endswith('rcParams'):
            if node.args and isinstance(node.args[0], ast.Dict):
                values.update({k.value:v for k,v in zip(node.args[0].keys,node.args[0].values) if isinstance(k,ast.Constant) and isinstance(k.value,str)})
            elif node.args: values['dynamic_update'] = node.args[0]
        if values:
            props = {}
            for key, expression in values.items():
                value = literal(expression, {})
                props[key] = {'known': fully_known(value), 'value': value if fully_known(value) else None, 'expression': ast.unparse(expression)}
            records.append({'method': 'rcParams', 'line':node.lineno, 'end_line':node.end_lineno,
                            'code':ast.get_source_segment(source,node), 'context':(), 'properties':props})
    return records


def rounded(value):
    if isinstance(value, float): return round(value, 10)
    if isinstance(value, (list, tuple)): return [rounded(v) for v in value]
    return value


def repeating_unit(values):
    """Separate repetition count from changes inside an ordered style pattern."""
    for size in range(1, len(values) + 1):
        if len(values) % size == 0 and values == values[:size] * (len(values) // size):
            return values[:size]
    return values


def compare_sources(baseline, candidate, requirements=None):
    original, changed = inspect_source(baseline), inspect_source(candidate)
    old, new = defaultdict(list), defaultdict(list)
    for item in original: old[item['method']].append(item)
    for item in changed: new[item['method']].append(item)
    findings = []
    repetition_changes = set()
    for operation in sorted(old.keys() | new.keys()):
        if operation in AXIS_CALLS: continue
        expected, found = old.get(operation, []), new.get(operation, [])
        if not expected:
            findings.append({'kind': 'call_added', 'method': operation,
                             'candidate_lines': sorted({x['line'] for x in found}),
                             'message': '新增调用；核对数据依据及布局用途，必要适配允许保留。'})
            continue
        if not found:
            findings.append({'kind': 'operation_not_found', 'method': operation,
                             'message': '当前文件未找到此调用；检查是否删除图元、改用等价实现或移入辅助文件。',
                             'source_lines': sorted({x['line'] for x in expected})})
            continue
        old_sites = {(x['line'], x['end_line'], x['code']) for x in expected}
        new_sites = {(x['line'], x['end_line'], x['code']) for x in found}
        if len(old_sites) != len(new_sites):
            findings.append({'kind': 'call_sites_changed', 'method': operation,
                             'before': len(old_sites), 'after': len(new_sites),
                             'source_lines': sorted({x['line'] for x in expected}),
                             'candidate_lines': sorted({x['line'] for x in found}),
                             'message': '独立调用位置数量变化（不是组数展开次数）；核对新增/删除图层。'})
        keys = set().union(*(r['properties'] for r in expected + found))
        for key in sorted(keys):
            a = [r['properties'][key] for r in expected if key in r['properties']]
            b = [r['properties'][key] for r in found if key in r['properties']]
            if not a:
                findings.append({'kind': 'parameter_added', 'method': operation, 'parameter': key,
                                 'after': [v['value'] if v['known'] else v['expression'] for v in b],
                                 'message': '新增显式参数；核对其用途。'})
            elif not b:
                findings.append({'kind': 'parameter_not_found', 'method': operation, 'parameter': key,
                                 'message': '原模板显式参数未在此类调用中找到；核对默认值或等价实现。'})
            elif all(v['known'] for v in a + b):
                av, bv = rounded([v['value'] for v in a]), rounded([v['value'] for v in b])
                if av != bv:
                    if repeating_unit(av) == repeating_unit(bv):
                        repetition_changes.add(operation)
                        continue
                    findings.append({'kind': 'data_mapping_changed' if key in DATA_KEYS else ('palette_changed' if key == 'cmap' else ('layout_changed' if operation in LAYOUT else 'style_changed')),
                                     'method': operation, 'parameter': key, 'before': av, 'after': bv,
                                     'message': '按源码出现/可展开循环顺序比较；结合卡片核对用途，不自动判错。'})
            elif [v['expression'] for v in a] != [v['expression'] for v in b]:
                if repeating_unit([v['expression'] for v in a]) == repeating_unit([v['expression'] for v in b]):
                    repetition_changes.add(operation)
                    continue
                findings.append({'kind': 'unresolved', 'method': operation, 'parameter': key,
                                 'message': '表达式或组织方式改变，静态检查无法确认等价；阅读相关代码。',
                                 'before': [v['expression'] for v in a], 'after': [v['expression'] for v in b]})
    if repetition_changes:
        findings.append({'kind': 'repetition_changed', 'methods': sorted(repetition_changes),
                         'message': '样式值及其周期内顺序相同，重复次数不同；可能来自组数或循环组织变化。若重复用于叠加透明图层，仍需核对层数。'})
    findings = focused_findings(original, changed, requirements) + findings
    for finding in findings:
        operation = finding.get('method')
        if operation:
            finding.setdefault('source_lines', sorted({x['line'] for x in old.get(operation, [])}))
            finding.setdefault('candidate_lines', sorted({x['line'] for x in new.get(operation, [])}))
        finding['severity'] = 'advisory'
        finding['priority'] = 'focus' if finding_priority(finding) == 0 else 'detail'
    findings.sort(key=finding_priority)
    return {'findings': findings, 'baseline_calls': len(original), 'candidate_calls': len(changed),
            'verdict': '仅提供源码差异线索，不判定视觉通过或失败。即使无提示，仍需按现有流程对照实图。',
            'limits': '不执行代码、不判断分支实际运行、不跨辅助文件追踪，不验证坐标语义或最终层次是否可见。'}


def package_root(workspace=None):
    from template_sources import package_root as resolve
    return resolve(workspace)


def review_file(candidate, baseline_path, template_id, checkpoints=None, requirements=None):
    baseline = Path(baseline_path).read_text(encoding='utf-8-sig')
    current = Path(candidate).read_text(encoding='utf-8-sig')
    report = compare_sources(baseline, current, requirements)
    report.update(template_id=template_id, baseline=str(baseline_path), candidate=str(candidate),
                  checkpoints=checkpoints or [],
                  source_diff=''.join(difflib.unified_diff(baseline.splitlines(True),current.splitlines(True),fromfile='template',tofile='adapted')))
    return report


def main(argv=None):
    from template_sources import locations, read_record
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id')
    parser.add_argument('--candidate', type=Path)
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--workspace', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--summary', action='store_true')
    parser.add_argument('--list-candidates', action='store_true', help='List ordinary registered scripts plus legacy figure filenames')
    args = parser.parse_args(argv)
    reports = []
    try:
        if args.list_candidates:
            if not args.workspace or args.candidate or args.output or args.id or args.baseline:
                raise ValueError('--list-candidates needs only --workspace')
            paths = set(args.workspace.glob('figures/gen_fig*.py'))
            for record in (args.workspace/'.vivid/template-sources').glob('*.json'):
                data, _ = read_record(record, args.workspace)
                candidate = args.workspace/data['candidate']
                if data['source']['id'].startswith('template.'):
                    paths.discard(candidate)
                else: paths.add(candidate)
            for candidate in sorted(paths): print(candidate.as_posix())
            return 0
        root = package_root(args.workspace)
        cards = json.loads((root/'catalog/cards.json').read_text(encoding='utf-8'))['cards'] if root else []
        by_id = {c['id']: c for c in cards}
        jobs = []
        if args.candidate:
            inferred = next((p for p in args.candidate.resolve().parents if (p/'.vivid').is_dir()), args.candidate.resolve().parent)
            workspace, candidate, _, record, _ = locations(args.candidate, args.workspace or inferred)
            if record.exists():
                data, _ = read_record(record, workspace)
                tid = data['source']['id']
                if args.id and args.id != tid: raise ValueError('Requested ID differs from tracked source')
                if args.baseline and args.baseline.resolve() != (workspace/data['baseline']).resolve():
                    raise ValueError('Tracked candidate must use its saved baseline')
                jobs.append((candidate, workspace/data['baseline'], tid))
            elif args.baseline and args.id:
                jobs.append((candidate, args.baseline, args.id))
            elif args.id in by_id:
                jobs.append((candidate, root/'catalog'/by_id[args.id]['source']['original_code'], args.id))
            else: raise ValueError('Provide a tracked candidate or --id with a known catalog/source baseline')
        elif args.workspace:
            if args.baseline or args.id: raise ValueError('Workspace review does not accept --id/--baseline')
            for record in sorted((args.workspace/'.vivid/template-sources').glob('*.json')):
                data, _ = read_record(record, args.workspace)
                jobs.append((args.workspace/data['candidate'], args.workspace/data['baseline'], data['source']['id']))
        else: raise ValueError('Supply --candidate or --workspace')
        protected = {Path(path).resolve() for job in jobs for path in job[:2]}
        if args.output and (args.output.resolve() in protected or args.output.suffix != '.json'):
            raise ValueError('Output must be a separate .json report')
        for candidate, baseline, tid in jobs:
            card = by_id.get(tid, {})
            reports.append(review_file(candidate, baseline, tid, card.get('fidelity_checkpoints'), card.get('review_requirements')))
        result = reports[0] if args.candidate else {'reports': reports, 'tracked_scripts': len(reports),
            'limits': 'Only registered scripts are covered; unregistered or helper files need separate review.'}
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if args.summary:
            for report in reports:
                print(f"{report['template_id']}: {len(report['findings'])} advisory findings; {report['candidate']}")
                for point in report['checkpoints']:
                    print('  保留重点: ' + point['preserve'])
                    print('  适配边界: ' + point['allowed_adaptation'])
                for line in summary_lines(report): print(line)
            if not reports: print('No tracked scripts; source comparison not performed.')
            print('Source differences are advisory; data and rendered images still require review.')
        elif not args.output: print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (OSError, ValueError, SyntaxError, KeyError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
