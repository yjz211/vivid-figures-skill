"""Install bundled fonts for the current Windows user; no administrator required."""
from pathlib import Path
import ctypes
import hashlib
import json
import os
import shutil


def install(directory):
    if os.name!='nt':raise RuntimeError('Use your operating system font manager to install this font bundle')
    import winreg
    directory=Path(directory).resolve()
    fonts=json.loads((directory/'fonts.json').read_text(encoding='utf-8'))
    dest=Path(os.environ['LOCALAPPDATA'])/'Microsoft/Windows/Fonts';dest.mkdir(parents=True,exist_ok=True)
    rows=[]
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows NT\CurrentVersion\Fonts') as key:
        for alias,info in fonts.items():
            source=(directory/info['path']).resolve()
            if not source.is_relative_to(directory):raise ValueError('Font path escapes bundle')
            digest=hashlib.sha256(source.read_bytes()).hexdigest()
            if digest!=info['sha256']:raise ValueError('Font digest mismatch '+source.name)
            target=dest/('Vivid-'+digest[:20]+source.suffix)
            existed=target.exists()
            if not existed:shutil.copy2(source,target)
            elif hashlib.sha256(target.read_bytes()).hexdigest()!=digest:raise ValueError('Conflicting font file '+str(target))
            face=' '.join([info['family'], 'Bold' if info.get('bold') else '', 'Italic' if info.get('italic') else '']).strip()
            value_name='Vivid '+face+' ('+digest[:8]+')'
            try:old=winreg.QueryValueEx(key,value_name)[0]
            except FileNotFoundError:old=None
            if old is not None and old!=str(target):raise ValueError('Font registry collision '+value_name)
            winreg.SetValueEx(key,value_name,0,winreg.REG_SZ,str(target))
            if old is None or not existed:
                if not ctypes.windll.gdi32.AddFontResourceExW(str(target),0,None):raise RuntimeError('Font registration failed '+str(target))
            rows.append({'family':face,'path':str(target),'registry_value':value_name,'new':old is None,'sha256':digest})
    ctypes.windll.user32.SendNotifyMessageW(0xffff,0x001d,0,0)
    (directory/'installed-current-user.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    return rows


if __name__=='__main__':
    import sys
    print(json.dumps(install(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).parent),ensure_ascii=False,indent=2))
