"""Optional Windows PowerPoint verification and editable-font embedding."""
import ctypes
import json
import tempfile
import zipfile
from pathlib import Path
from pptx_text import extract_embedded_fonts


def verify_and_embed(pptx_path, svg_path):
    import win32com.client
    pptx_path=Path(pptx_path).resolve()
    target=pptx_path.with_name(pptx_path.stem+'.office-embedded.pptx')
    if target.exists():raise FileExistsError(target)
    registered=[];app=None;pres=None
    with tempfile.TemporaryDirectory(prefix='vivid-pptx-fonts-') as temp:
        fonts=extract_embedded_fonts(svg_path,temp)
        try:
            for info in fonts.values():
                if info.get('fsType',0)&2:raise ValueError('Font license prohibits embedding: '+info['family'])
                path=info['path']
                if path in registered:continue
                if not ctypes.windll.gdi32.AddFontResourceExW(path,0,None):raise RuntimeError('Cannot register font '+path)
                registered.append(path)
            ctypes.windll.user32.SendNotifyMessageW(0xffff,0x001d,0,0)
            app=win32com.client.DispatchEx('PowerPoint.Application')
            pres=app.Presentations.Open(str(pptx_path),ReadOnly=False,Untitled=False,WithWindow=False)
            pres.SaveAs(str(target),24,-1)
            pres.Slides(1).Export(str(pptx_path.with_suffix('.powerpoint.png')),'PNG',1600,0)
            font_names=[pres.Fonts.Item(i).Name for i in range(1,pres.Fonts.Count+1)]
            pres.Close();pres=None
            # Reopen the serialized deliverable as an independent format/read check.
            pres=app.Presentations.Open(str(target),ReadOnly=True,Untitled=False,WithWindow=False)
            pres.Slides(1).Export(str(pptx_path.with_suffix('.powerpoint.png')),'PNG',1600,0)
            pres.SaveAs(str(pptx_path.with_suffix('.powerpoint.pdf')),32)
            pres.Close();pres=None
            with zipfile.ZipFile(target) as z:
                embedded=[n for n in z.namelist() if n.startswith('ppt/fonts/')]
            target.replace(pptx_path)
            return {'rendered':True,'reopened':True,'font_embedding':'embedded' if embedded else 'none',
                    'embedded_font_files':len(embedded),'fonts_in_powerpoint':font_names,
                    'preview':str(pptx_path.with_suffix('.powerpoint.png')),
                    'pdf':str(pptx_path.with_suffix('.powerpoint.pdf')),
                    'font_note':'Embedded fonts are saved; some Office render paths ignore embedding. Install the supplied fonts when needed.'}
        finally:
            if pres is not None:pres.Close()
            if app is not None:app.Quit()
            for path in registered:ctypes.windll.gdi32.RemoveFontResourceExW(path,0,None)
            if registered:ctypes.windll.user32.SendNotifyMessageW(0xffff,0x001d,0,0)
