"""Portable project settings and the single Vivid palette registry."""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path


def registry():
    return json.loads(Path(__file__).with_name('palettes.json').read_text(encoding='utf-8'))


def workspace_root(start=None):
    current = Path(start or os.environ.get('VIVID_WORKSPACE') or Path.cwd()).resolve()
    for parent in (current, *current.parents):
        if (parent / '.vivid/config.json').is_file() or (parent / '.vivid/runtime.json').is_file():
            return parent
    return current


def palette_id(value):
    data = registry()
    if value in ('default', None):
        return data['default']
    if value == 'custom' or value in data['palettes']:
        return value
    for key, item in data['palettes'].items():
        if value == item['name'] or value == '橄榄行踪' and key == 'olive-apricot':
            return key
    raise ValueError(f'Unknown palette: {value}')


def load_config(workspace=None):
    path = workspace_root(workspace) / '.vivid/config.json'
    config = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    if not isinstance(config, dict):
        raise ValueError('Vivid config must be a JSON object')
    config = {'schema': 1, 'palette': registry()['default'], 'style': 'clean_open',
              'language': 'zh', 'output_format': 'pdf', **config}
    config['palette'] = palette_id(config['palette'])
    if config['palette'] == 'custom':
        colors = config.get('colors')
        if not isinstance(colors, list) or len(colors) < 2 or any(
            not isinstance(c, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', c) for c in colors
        ):
            raise ValueError('Custom palette requires at least two #RRGGBB colors')
    return config


def palette_colors(config=None):
    """Original color order, retained for continuous color scales."""
    config = load_config() if config is None else config
    key = palette_id(config.get('palette'))
    return list(config['colors'] if key == 'custom' else registry()['palettes'][key]['colors'])


def categorical_colors(config=None):
    """Fixed category order; custom palettes keep the user's exact order."""
    config = load_config() if config is None else config
    colors = palette_colors(config)
    key = palette_id(config.get('palette'))
    if key == 'custom':
        return colors
    order = registry()['palettes'][key].get('category_order', list(range(len(colors))))
    if sorted(order) != list(range(len(colors))):
        raise ValueError(f'Invalid category_order for palette: {key}')
    return [colors[i] for i in order]


def write_config(workspace, **updates):
    root = workspace_root(workspace)
    config = load_config(root)
    config.update(updates)
    config['palette'] = palette_id(config['palette'])
    if config['palette'] != 'custom':
        config.pop('colors', None)
    # Validate custom colors before changing a valid file.
    if config['palette'] == 'custom':
        colors = config.get('colors')
        if not isinstance(colors, list) or len(colors) < 2 or any(
            not isinstance(c, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', c) for c in colors
        ):
            raise ValueError('Custom palette requires at least two #RRGGBB colors')
    destination = root / '.vivid/config.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    pending = destination.with_suffix('.tmp')
    pending.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    pending.replace(destination)
    return config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['show', 'get', 'set', 'palettes'])
    parser.add_argument('key', nargs='?')
    parser.add_argument('value', nargs='?')
    parser.add_argument('--workspace')
    args = parser.parse_args()
    if args.action == 'palettes':
        result = registry()
    elif args.action == 'set':
        if not args.key or args.value is None:
            parser.error('set requires a key and value (JSON or plain text)')
        try:
            value = json.loads(args.value)
        except json.JSONDecodeError:
            value = args.value
        result = write_config(args.workspace or Path.cwd(), **{args.key: value})
    elif args.action == 'get':
        result = load_config(args.workspace).get(args.key, '')
        if isinstance(result, bool):
            result = int(result)
    else:
        result = load_config(args.workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2) if isinstance(result, (dict, list)) else result)


if __name__ == '__main__':
    main()
