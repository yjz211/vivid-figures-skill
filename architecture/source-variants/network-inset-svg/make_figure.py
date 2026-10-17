"""VA-001 native SVG asset. No geometry generator is hidden in this wrapper."""
from pathlib import Path
from types import SimpleNamespace
import sys
try:
    from source_asset import run
except ModuleNotFoundError:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'lib'))
    from source_asset import run
from font_assets import apply_font_profile

def customize(root, context):
    # Edit source SVG objects here. Revalidate typography after your edits.
    for node in list(root):
        if node.tag.endswith('}metadata') and node.get('id')=='vivid-font-profile':
            root.remove(node)
    defs=root.find(context['tag']('defs'))
    apply_font_profile(SimpleNamespace(root=root,defs=defs),context['config'].get('font_profile','reference-system'))

if __name__=='__main__':run(__file__,customize)
