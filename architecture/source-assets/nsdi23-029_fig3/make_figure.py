"""VA-136: editable Vivid architecture design example.
Edit example.json for text/styles/translations; customize() for structural changes.
Example labels and values must be adapted to the current research task.
"""
from pathlib import Path
import sys
try:
    from source_asset import run
except ModuleNotFoundError:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'lib'))
    from source_asset import run

def customize(root,context):
    # Actual SVG objects, component memberships and geometry are available here.
    pass

if __name__=='__main__':run(__file__,customize)
