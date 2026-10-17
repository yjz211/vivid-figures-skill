"""Refresh the workbench's architecture index from its shared Vivid asset package."""
from pathlib import Path
import argparse, json, re, sys

WEB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WEB / 'editor_backend'))
from architecture_assets import architecture_root

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, help='Architecture directory containing gallery-data.json')
    args = parser.parse_args()
    root = (args.root or architecture_root()).resolve()
    data = json.loads((root / 'gallery-data.json').read_text(encoding='utf-8'))
    assert len(data['assets']) == data['count']
    payload = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')
    (WEB / 'frontend/architecture-data.js').write_text('window.VIVID_ARCHITECTURE = ' + payload + ';\n', encoding='utf-8')
    for name in ['index.html', 'architecture.html']:
        path = WEB / name
        if path.exists():
            html = path.read_text(encoding='utf-8')
            html = re.sub(r'(id="architecture-count">)\d+', lambda m: m[1] + str(data['count']), html)
            path.write_text(html, encoding='utf-8')
    print(json.dumps({'assets': data['count'], 'root': str(root)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
