"""Save exact source starts and inspect their provenance. Not a security boundary."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path

COMPLETE_TEMPLATES = {
    'template.sem_violin_pearson': 'templates/sem-violin-pearson/plot_sem_violin_pearson.py',
    'template.shap_dependence': 'templates/shap-composites/plot_shap_composites.py',
    'template.shap_contribution': 'templates/shap-composites/plot_shap_composites.py',
}


def digest(value):
    return hashlib.sha256(value.encode('utf-8') if isinstance(value, str) else value).hexdigest()


def package_root(workspace=None):
    for parent in Path(__file__).resolve().parents:
        if (parent/'catalog/cards.json').is_file(): return parent
    if workspace:
        runtime = Path(workspace)/'.vivid/runtime.json'
        if runtime.is_file():
            resources = Path(json.loads(runtime.read_text(encoding='utf-8'))['runtime_skill'])
            root = resources.parent.parent
            if (root/'catalog/cards.json').is_file(): return root
    return None


def complete_source(template_id, workspace=None):
    """Resolve complete compositions identically for individual and batch preparation."""
    key = template_id.removeprefix('recipe:')
    if key not in COMPLETE_TEMPLATES:
        raise ValueError('Unknown complete template ID: ' + key)
    root = package_root(workspace)
    if root is None:
        raise ValueError('Complete template package unavailable; bootstrap the workspace with the current package')
    relative = COMPLETE_TEMPLATES[key]
    code = (root / relative).read_text(encoding='utf-8')
    return code, dict(id=key, variant=key.split('.')[-1], file=relative, codeSha256=digest(code))


def workspace_for(candidate, workspace=None):
    if workspace:
        return Path(workspace).resolve()
    for parent in [Path(candidate).resolve().parent, *Path(candidate).resolve().parents]:
        if (parent / '.vivid').is_dir():
            return parent
    return Path.cwd().resolve()


def locations(candidate, workspace=None):
    candidate = Path(candidate).resolve()
    root = workspace_for(candidate, workspace)
    if not candidate.is_relative_to(root) or candidate.suffix != '.py':
        raise ValueError('Script must be a .py file inside the workspace')
    relative = candidate.relative_to(root).as_posix()
    if relative.startswith('.vivid/'):
        raise ValueError('Working scripts must be outside .vivid')
    record = root / '.vivid/template-sources' / (digest(relative)[:24] + '.json')
    return root, candidate, relative, record, record.with_suffix('.py')


def read_record(record, workspace):
    root = Path(workspace).resolve()
    data = json.loads(Path(record).read_text(encoding='utf-8'))
    if data.get('schemaVersion') != 1:
        raise ValueError('Unsupported source record')
    for key in ('candidate', 'baseline'):
        path = (root / data[key]).resolve()
        if not path.is_relative_to(root):
            raise ValueError('Source record path escapes workspace')
        if not path.is_file():
            raise ValueError('Missing tracked file: ' + str(path))
    baseline = (root / data['baseline']).read_text(encoding='utf-8')
    if digest(baseline) != data['source']['codeSha256']:
        raise ValueError('Saved baseline hash mismatch: ' + str(record))
    return data, baseline


def preflight(candidate, code, source, workspace=None):
    ast.parse(code)
    if digest(code) != source['codeSha256']:
        raise ValueError('Source code hash mismatch')
    root, target, relative, record, baseline = locations(candidate, workspace)
    if record.exists():
        data, _ = read_record(record, root)
        if data['candidate'] != relative or data['source'] != source:
            raise ValueError('Existing source/version differs; choose a new script path')
        return 'preserved'
    if target.exists() or baseline.exists():
        raise ValueError('Untracked script or incomplete source record; preserve and reconcile: ' + str(target))
    return 'created'


def materialize(candidate, code, source, workspace=None):
    status = preflight(candidate, code, source, workspace)
    root, target, relative, record, baseline = locations(candidate, workspace)
    if status == 'created':
        target.parent.mkdir(parents=True, exist_ok=True)
        record.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation also protects against an untracked file appearing mid-call.
        with target.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(code)
        with baseline.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(code)
        data = dict(schemaVersion=1, candidate=relative,
                    baseline=baseline.relative_to(root).as_posix(), source=source)
        with record.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
    result = dict(status=status, script=str(target), record=str(record),
                  template=source['id'], variant=source['variant'],
                  requiredInputs=source.get('requiredInputs', []))
    package = package_root(root)
    if package:
        cards = json.loads((package/'catalog/cards.json').read_text(encoding='utf-8'))['cards']
        card = next((c for c in cards if c['id'] == source['id']), {})
        result['checkpoints'] = [{k:p[k] for k in ('preserve','allowed_adaptation')} for p in card.get('fidelity_checkpoints', [])]
    return result
