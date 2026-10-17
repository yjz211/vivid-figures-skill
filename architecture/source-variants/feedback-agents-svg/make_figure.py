"""VA-004 editable SVG asset; read TEMPLATE.md and labels.json."""
from pathlib import Path
import sys
try:
    from source_asset import run
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
    from source_asset import run

def customize(root, context):
    # Edit the existing SVG tree. Stable objects: context['elements'];
    # semantic parts: context['parts']; source geometry: context['geometry'].
    pass

if __name__ == '__main__':
    run(__file__, customize)
