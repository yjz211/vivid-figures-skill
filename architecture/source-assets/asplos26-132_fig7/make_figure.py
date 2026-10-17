"""VA-049 — 依赖任务到资源日程的三步优化.
Read TEMPLATE.md for supported edits and component semantics.
See ATTRIBUTION.md for derived geometry and rights.
"""
from pathlib import Path
import sys
try:
    from source_asset import run
except ModuleNotFoundError:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'lib'))
    from source_asset import run

def customize(root,context):
    # context: elements keyed by source IDs, semantic parts, geometry, config.
    # Modify actual SVG objects here when labels/styles alone are insufficient.
    pass

if __name__=='__main__':run(__file__,customize)
