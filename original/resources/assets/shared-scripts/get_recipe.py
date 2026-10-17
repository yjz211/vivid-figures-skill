#!/usr/bin/env python3
"""Return an unchanged recipe by stable ID, legacy number, or plan references.

Examples:
  python _utils/get_recipe.py --id academic.tsne_umap
  python _utils/get_recipe.py academic 3
  python _utils/get_recipe.py --plan FIGURE_PLAN.json PAPER_PLAN.md --output _utils/RECIPES_FOR_THIS_PAPER.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import ast
sys.path.insert(0, str(Path(__file__).resolve().parent))
from template_sources import COMPLETE_TEMPLATES, complete_source, digest, materialize, preflight, workspace_for

HEADER = re.compile(r'^## (\d+)\.\s+([^\n]+)$', re.MULTILINE)
ID_REF = re.compile(r'\brecipe:([a-z][a-z0-9_]*\.[a-z][a-z0-9_]*)\b')
COMPLETE_REF = re.compile(r'\b(template\.[a-z][a-z0-9_]*)\b')
LEGACY_REF = re.compile(r'\b(basic|advanced|empirical|competition|academic|comp)\s*#\s*(\d+)((?:\s*[,/+]\s*#\s*\d+)*)')


def sections(text):
    headers = list(HEADER.finditer(text))
    return [(match.group(1), match.group(2), text[match.start():headers[i + 1].start() if i + 1 < len(headers) else len(text)].strip())
            for i, match in enumerate(headers)]


def content_hash(section):
    # Chapter numbers are presentation only. The title and entire body are locked.
    normalized = re.sub(r'^## \d+\.\s+', '', section, count=1)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


class Recipes:
    def __init__(self, root=None, workspace=None):
        # Never search the current directory: registry and recipes form one bundle.
        self.root = Path(root) if root is not None else Path(__file__).resolve().parent
        self.workspace = workspace
        self.registry = json.loads((self.root / 'recipe_registry.json').read_text(encoding='utf-8'))
        if self.registry.get('schemaVersion') != 1:
            raise ValueError('Unsupported recipe registry version')
        self.entries = {}
        self.legacy = {}
        for entry in self.registry['recipes']:
            key = entry['id']
            if key in self.entries or entry['legacy'] in self.legacy:
                raise ValueError('Duplicate recipe identity: ' + key)
            if Path(entry['file']).name != entry['file'] or '/' in entry['file'] or '\\' in entry['file']:
                raise ValueError('Recipe file must be inside the registry directory')
            self.entries[key] = entry
            self.legacy[entry['legacy']] = key

    def legacy_id(self, category, number):
        category = 'competition' if category.lower() == 'comp' else category.lower()
        key = f'{category} #{int(number)}'
        if key not in self.legacy:
            raise ValueError('Unknown legacy recipe: ' + key)
        return self.legacy[key]

    def extract(self, key):
        key = key.removeprefix('recipe:')
        if key.startswith('template.'):
            code, _ = complete_source(key, self.workspace)
            return f'## {key}\n\nComplete composition; keep its original CLI.\n\n```python\n{code.rstrip()}\n```'
        if key not in self.entries:
            raise ValueError('Unknown recipe ID: ' + key)
        entry = self.entries[key]
        text = (self.root / entry['file']).read_text(encoding='utf-8')
        matches = [body for _, title, body in sections(text) if title == entry['title']]
        if len(matches) != 1:
            raise ValueError(f'{key}: expected one matching title, found {len(matches)}')
        if content_hash(matches[0]) != entry['contentSha256']:
            raise ValueError(f'{key}: recipe content differs from this registry; use a matching bundle')
        return matches[0]

    def references(self, text):
        found = [(m.start(), m.group(1)) for m in ID_REF.finditer(text)]
        found.extend((m.start(), m.group(1)) for m in COMPLETE_REF.finditer(text))
        for m in LEGACY_REF.finditer(text):
            for number in [m.group(2), *re.findall(r'#\s*(\d+)', m.group(3))]:
                found.append((m.start(), self.legacy_id(m.group(1), number)))
        return list(dict.fromkeys(key for _, key in sorted(found, key=lambda item: item[0])))

    def script(self, key, variant='main'):
        key = key.removeprefix('recipe:')
        if key.startswith('template.'):
            if variant != 'main':
                raise ValueError('Complete compositions use their original CLI mode, not recipe variants')
            return complete_source(key, self.workspace)
        chapter = self.extract(key)
        entry = self.entries[key]
        variants = entry.get('scripts', {})
        if variant not in variants:
            raise ValueError(f'{key}: unregistered variant {variant}; available: {list(variants)}')
        mapping = variants[variant]
        blocks = re.findall(r'```python[^\n]*\n(.*?)```', chapter, re.S)
        if not mapping.get('blocks') or any(type(i) is not int or not 0 <= i < len(blocks) for i in mapping['blocks']):
            raise ValueError(f'{key}: invalid registered code block mapping')
        code = '\n\n'.join(blocks[i].strip() for i in mapping['blocks']) + '\n'
        if digest(code) != mapping['codeSha256']:
            raise ValueError(f'{key}: registered source differs')
        ast.parse(code)
        source = dict(id=key, variant=variant, codeSha256=digest(code),
                      contentSha256=entry['contentSha256'], file=entry['file'],
                      blocks=mapping['blocks'], requiredInputs=mapping.get('requiredInputs', []))
        return code, source


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('category', nargs='?')
    parser.add_argument('number', nargs='?', type=int)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--id')
    mode.add_argument('--plan', nargs='+', type=Path)
    mode.add_argument('--list', action='store_true')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--script', type=Path, help='Create exact Python source and provenance; preserve existing adaptations')
    parser.add_argument('--scripts-dir', type=Path, help='With --plan, create one working script per selected recipe')
    parser.add_argument('--workspace', type=Path)
    parser.add_argument('--variant', default='main')
    parser.add_argument('--list-variants', action='store_true')
    args = parser.parse_args(argv)
    if (args.id or args.plan or args.list) and (args.category or args.number is not None):
        parser.error('Choose stable ID, plan, list, or legacy category/number')
    workspace_hint = args.script or ((args.scripts_dir / 'figure.py') if args.scripts_dir else Path.cwd() / 'figure.py')
    workspace = workspace_for(workspace_hint, args.workspace)
    recipes = Recipes(workspace=workspace)
    if args.script or args.scripts_dir or args.list_variants:
        if args.output or args.list or (args.script and args.scripts_dir):
            parser.error('Script/variant mode cannot be combined with Markdown output or list')
        if args.scripts_dir:
            if not args.plan: parser.error('--scripts-dir requires --plan')
            keys = list(dict.fromkeys(key for p in args.plan for key in recipes.references(p.read_text(encoding='utf-8'))))
            if not keys: raise ValueError('No recipe references found in the supplied plans')
            jobs = [(key, args.scripts_dir / ('gen_fig_' + key.replace('.', '_') + '.py')) for key in keys]
        else:
            key = args.id or (recipes.legacy_id(args.category, args.number) if args.category and args.number is not None else None)
            if not key: parser.error('--script/--list-variants requires a recipe ID')
            if args.list_variants:
                recipes.extract(key)
                if key.removeprefix('recipe:') in COMPLETE_TEMPLATES:
                    _, source = recipes.script(key)
                    print(json.dumps({'main': source}, ensure_ascii=False, indent=2))
                    return 0
                print(json.dumps(recipes.entries[key.removeprefix('recipe:')].get('scripts', {}), ensure_ascii=False, indent=2))
                return 0
            jobs = [(key, args.script)]
        prepared = [(path, *recipes.script(key, args.variant)) for key, path in jobs]
        for path, code, source in prepared: preflight(path, code, source, args.workspace)
        for path, code, source in prepared:
            print(json.dumps(materialize(path, code, source, args.workspace), ensure_ascii=False))
        return 0
    if args.list:
        result = '\n'.join(f"recipe:{key}\t{entry['title']}" for key, entry in recipes.entries.items())
        result += '\n' + '\n'.join(f'{key}\tComplete composition (original CLI)' for key in COMPLETE_TEMPLATES)
    elif args.plan:
        keys = []
        for path in args.plan:
            keys.extend(recipes.references(path.read_text(encoding='utf-8')))
        keys = list(dict.fromkeys(keys))
        if not keys:
            raise ValueError('No recipe references found in the supplied plans')
        # Resolve every entry before replacing an existing prefetched file.
        result = '\n\n'.join(f'########## recipe:{key} ##########\n{recipes.extract(key)}' for key in keys)
    else:
        key = args.id
        if key is None and args.category and args.number is not None:
            key = recipes.legacy_id(args.category, args.number)
        if key is None:
            parser.error('Supply --id, --plan, --list, or category and number')
        result = recipes.extract(key)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        name = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n', dir=args.output.parent, delete=False) as stream:
                name = stream.name
                stream.write(result + '\n')
            os.replace(name, args.output)
        finally:
            if name and os.path.exists(name):
                os.unlink(name)
    else:
        print(result)
    return 0


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, OSError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        raise SystemExit(1)
