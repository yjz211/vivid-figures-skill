"""Copy a complete composition unchanged; its existing CLI remains the renderer."""
from pathlib import Path
import argparse
import json
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'original/resources/assets/shared-scripts'))
from template_sources import COMPLETE_TEMPLATES, complete_source, materialize, workspace_for


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', required=True, choices=list(COMPLETE_TEMPLATES))
    parser.add_argument('--script', required=True, type=Path)
    parser.add_argument('--workspace', type=Path)
    args = parser.parse_args()
    code, source = complete_source(args.id, workspace_for(args.script, args.workspace))
    print(json.dumps(materialize(args.script, code, source, args.workspace), ensure_ascii=False))


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    try: main()
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
