"""Bundle SVG font faces and optionally install them for the current Windows user."""
from pathlib import Path
import ctypes
import hashlib
import json
import os
import shutil
from pptx_text import extract_embedded_fonts


def bundle_fonts(svg, target):
    target=Path(target);target.mkdir(parents=True,exist_ok=True)
    fonts=extract_embedded_fonts(svg,target)
    # Preserve the supplied open-font notices in every transferable font bundle.
    notices=Path(__file__).resolve().parent/'font-notices'
    if notices.exists():shutil.copytree(notices,target/'notices',dirs_exist_ok=True)
    else:
        from fontTools.ttLib import TTFont
        license_rows={}
        for alias,info in fonts.items():
            with TTFont(info['path']) as font:
                license_rows[alias]=list(dict.fromkeys(n.toUnicode() for n in font['name'].names if n.nameID in (0,13,14)))
        (target/'font-license-records.json').write_text(json.dumps(license_rows,ensure_ascii=False,indent=2),encoding='utf-8')
    manifest={alias:{**info,'path':Path(info['path']).name} for alias,info in fonts.items()}
    (target/'fonts.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    shutil.copy2(Path(__file__).with_name('install_pptx_fonts.py'),target/'install_fonts.py')
    (target/'INSTALL.txt').write_text('Windows: select the included .ttf/.otf files and choose Install, or run: python install_fonts.py\nInstall fonts before opening the PPTX. macOS: use Font Book.\nEmbedded fonts are retained in the PPTX, but this font bundle also supports editors and rendering paths that ignore embedding.\n',encoding='utf-8')
    return {'directory':str(target),'fonts':manifest}


def install_user_fonts(bundle):
    from install_pptx_fonts import install
    return install(Path(bundle))
