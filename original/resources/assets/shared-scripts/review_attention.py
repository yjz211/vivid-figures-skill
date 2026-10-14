"""Focused, advisory source checks. No execution or inference of runtime semantics."""
from __future__ import annotations
import ast
from collections import defaultdict

AXIS_CALLS = set('set_xlabel set_ylabel set_xticks set_yticks set_xticklabels set_yticklabels tick_params'.split())
BANDS = {'fill_between', 'fill_betweenx'}


def value_names(node):
    """Ignore subscripts: changing groups is different from changing band geometry."""
    if isinstance(node, ast.Name): return {node.id}
    if isinstance(node, ast.Subscript): return value_names(node.value)
    return set().union(*(value_names(child) for child in ast.iter_child_nodes(node)))


def geometry_dependencies(loop):
    names = {n.id for n in ast.walk(loop.target) if isinstance(n, ast.Name)}
    assignments = [n for statement in loop.body for n in ast.walk(statement)
                   if isinstance(n, (ast.Assign, ast.AnnAssign)) and n.value is not None]
    # Bounded propagation of simple local aliases, e.g. frac = k / n_layers.
    for _ in range(min(len(assignments) + 1, 64)):
        previous = set(names)
        for node in assignments:
            if value_names(node.value) & names:
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                names.update(n.id for target in targets for n in ast.walk(target) if isinstance(n, ast.Name))
        if previous == names: break
    return names


def _sites(records):
    return list({(r['line'], r['end_line'], r['code']): r for r in records}.values())


def _known(record, key, default=None):
    prop = record['properties'].get(key, {})
    return prop.get('value') if prop.get('known') else default


def _axis_state(records, axis):
    positions_empty = labels_empty = False
    low, high = True, False
    label = False
    evidence = []
    for record in sorted(_sites(records), key=lambda r: r['line']):
        op = record['method']
        if op == f'set_{axis}label':
            prop = record['properties'].get('label', {})
            label = not prop.get('known') or bool(str(prop.get('value', '')).strip())
        if op in {f'set_{axis}ticks', f'set_{axis}ticklabels'}:
            prop = record['properties'].get('ticks' if op.endswith('ticks') else 'ticklabels', {})
            if prop.get('known'):
                value = prop['value']
                empty = isinstance(value, (list, tuple)) and (not value or all(str(v).strip() == '' for v in value))
                if op.endswith('ticklabels'): labels_empty = empty
                else: positions_empty = empty
                if empty: evidence.append(record['line'])
        if op == 'tick_params' and _known(record, 'axis', 'both') in {axis, 'both'}:
            lower, upper = ('labelleft', 'labelright') if axis == 'y' else ('labelbottom', 'labeltop')
            low = _known(record, lower, low); high = _known(record, upper, high)
            if not low and not high: evidence.append(record['line'])
    return {'hidden': positions_empty or labels_empty or not (low or high), 'label': label, 'lines': evidence}


def focused_findings(original, changed, requirements=None):
    findings = []
    for operation in BANDS:
        old = _sites([r for r in original if r['method'] == operation])
        new = _sites([r for r in changed if r['method'] == operation])
        # Compare per drawing site, never multiply by station/model repetitions.
        before = [r['band_loop']['count'] for r in old if r.get('band_loop')]
        after = [r['band_loop']['count'] for r in new if r.get('band_loop')]
        if before and new and before != after:
            known = all(v is not None for v in before + after) and bool(after)
            findings.append(dict(kind='band_layers_changed' if known else 'band_layers_unresolved',
                method=operation, before=before, after=after,
                source_lines=[r['line'] for r in old], candidate_lines=[r['line'] for r in new],
                message=(f'色带几何的叠加循环：{before} → {after} 层（按调用位置，不乘站点/方法数）；核对是否改变透明层次。'
                         if known else '原色带使用叠加循环；当前层数无法静态对应，需查看循环或等价实现。'), priority='focus'))

    for operation in ('text', 'annotate'):
        def boxed(records):
            return _sites([r for r in records if r['method'] == operation and
                           any(k == 'bbox' or k.startswith('bbox.') for k in r['properties'])])
        old, new = boxed(original), boxed(changed)
        if len(new) > len(old):
            findings.append(dict(kind='annotation_box_added', method=operation,
                before=len(old), after=len(new), source_lines=[r['line'] for r in old],
                candidate_lines=[r['line'] for r in new], priority='focus',
                message='带框文字的独立调用位置增加；核对是否新增了可移到随图说明的过程/规则框。模板已有指标框仍允许保留。'))

    # Basic regressions on recognizably the same receiver. Changes to wording or
    # units, newly added labels and unchanged redundant shared-axis labels are fine.
    old_axes, new_axes = defaultdict(list), defaultdict(list)
    for r in original: old_axes[r.get('receiver', '')].append(r)
    for r in changed: new_axes[r.get('receiver', '')].append(r)
    required = set()
    for rule in (requirements or {}).get('quantitative_axes', []):
        for r in changed:
            if r['method'] == rule['method'] and _known(r, 'orientation', 'vertical') == rule.get('orientation', 'vertical'):
                required.add((r.get('receiver', ''), rule['axis']))
    for receiver in new_axes:
        if not receiver: continue
        for axis in ('x', 'y'):
            a, b = _axis_state(old_axes[receiver], axis), _axis_state(new_axes[receiver], axis)
            required_here = (receiver, axis) in required
            if b['hidden'] and (not a['hidden'] or required_here):
                findings.append(dict(kind='axis_ticks_hidden', method=f'{receiver}.{axis}axis',
                    candidate_lines=b['lines'], priority='focus',
                    message=f'{receiver} 的 {axis} 轴数值刻度被显式隐藏；核对定量阅读需要，或确认是否有其他可见共轴刻度。'))
            if not b['label'] and (required_here or a['label']):
                findings.append(dict(kind='axis_label_missing', method=f'{receiver}.set_{axis}label',
                    candidate_lines=sorted({r['line'] for r in new_axes[receiver] if r['method'] not in AXIS_CALLS}),
                    priority='focus', message=f'{receiver} 的 {axis} 轴未找到非空标签；核对变量名称和单位，动态或共享标签需人工确认。'))
    return findings


def finding_priority(finding):
    if finding.get('priority') == 'focus': return 0
    removed = finding['kind'] == 'operation_not_found' or (finding['kind'] == 'call_sites_changed' and finding.get('before', 0) > finding.get('after', 0))
    if removed and finding.get('method') not in {
            'figure', 'subplots', 'subplot', 'add_subplot', 'GridSpec', 'add_axes', 'tight_layout',
            'subplots_adjust', 'text', 'annotate', '_lighten', 'axvspan', 'axhspan', 'axvline', 'axhline'}:
        return 0
    if finding.get('parameter') in {'alpha', 'opacity', 'lightening'}: return 1
    if finding.get('parameter', '').startswith('bbox'): return 1
    return 2


def summary_lines(report):
    """Focus items are never lost to the generic-detail display limit."""
    ordered = sorted(report['findings'], key=finding_priority)
    focus = [f for f in ordered if finding_priority(f) == 0]
    details = [f for f in ordered if finding_priority(f) != 0]
    lines = [f'  优先核对 {len(focus)} 项（仍为提示，不自动判错）：']
    for finding in focus:
        lines.append('    ' + format_finding(finding))
    if details: lines.append('  其他差异：')
    for finding in details[:6]: lines.append('    ' + format_finding(finding))
    if len(details) > 6: lines.append(f'  另有 {len(details)-6} 项常规差异，见详细JSON；组数和布局变化允许按需要保留。')
    return lines


def format_finding(finding):
    target = finding.get('method', ','.join(finding.get('methods', [])))
    if finding.get('parameter'): target += '.' + finding['parameter']
    delta = ''
    if finding_priority(finding) != 0 and ('before' in finding or 'after' in finding):
        def compact(value):
            if isinstance(value, list) and len(value) > 4: return str(value[:4]) + f'…（{len(value)}项）'
            return str(value)
        delta = f" {compact(finding.get('before'))} → {compact(finding.get('after'))}"
    return f"[{finding['kind']}] {target}{delta} @L{finding.get('candidate_lines', [])}: {finding['message']}"
