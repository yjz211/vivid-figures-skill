"""Real Chinese render: glyph fallback and direct edits survive font refresh."""
from pathlib import Path
import copy
import json
import re
import shutil
import subprocess
import sys

import fitz

WEB = Path(__file__).resolve().parents[1]
BACKEND = WEB/'editor_backend'
OUT = WEB/'verification/typography/editor-zh'
sys.path.insert(0, str(BACKEND))
from schema import sample
from object_editor import structure_guard


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    project = sample('basic.grouped_bar')
    project['settings'].update(language='zh', title='中文字体示例 2026')
    original_table = copy.deepcopy(project['table'])
    source = WEB/'assets/sources/basic.grouped_bar'
    shutil.copy2(source/'preview.py', OUT/'source.py')
    shutil.copy2(source/'original.py', OUT/'original.py')
    guard = structure_guard(project, OUT)
    title = dict(text='编辑后标题 2026', fontsize=16, offset_x=10, offset_y=4)
    project['object_edits'] = {
        'vivid-title': {'guard': guard, 'props': title},
        'vivid-ax0-legend': {'guard': guard, 'props': {'ncols': 2, 'fontsize': 9}},
    }
    (OUT/'project.json').write_text(json.dumps(project,ensure_ascii=False),encoding='utf8')
    result = subprocess.run([sys.executable,'-B','-X','utf8',str(BACKEND/'worker.py'),str(OUT)],
                            cwd=OUT,capture_output=True,text=True,encoding='utf8',timeout=180,
                            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    log = result.stdout + result.stderr
    (OUT/'render.log').write_text(log,encoding='utf8')
    status = json.loads((OUT/'status.json').read_text('utf8'))
    assert result.returncode == 0 and status['state'] == 'done', status
    assert not re.search(r'Glyph .*missing from|findfont: Font family', log), log[-2000:]
    assert json.loads((OUT/'project.json').read_text('utf8'))['table'] == original_table
    objects = json.loads((OUT/'objects.json').read_text('utf8'))
    assert not objects['skipped'], objects['skipped']
    by_id = {obj['id']:obj for obj in objects['objects']}
    assert all(by_id['vivid-title']['props'][key] == value for key,value in title.items())
    assert by_id['vivid-ax0-legend']['props']['ncols'] == 2
    assert by_id['vivid-ax0-legend']['props']['fontsize'] == 9
    with fitz.open(OUT/'figure.pdf') as document:
        fonts = sorted({font[3] for page in document for font in page.get_fonts()})
        text = ''.join(page.get_text() for page in document)
        for page in document:
            assert all(0 <= word[0] < word[2] <= page.rect.width + .5 and
                       0 <= word[1] < word[3] <= page.rect.height + .5
                       for word in page.get_text('words')), 'Clipped text after legend repack'
    assert '编辑后标题' in text and '2026' in text, text
    assert '本文方法' in text, 'Repacked legend was lost from the PDF'
    report = dict(passed=True, pdf_fonts=fonts, missing_glyph_warnings=0,
                  title_drag_and_size_preserved=True, legend_repack_preserved=True,
                  original_data_preserved=True)
    (OUT/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(report,ensure_ascii=False))


if __name__ == '__main__':
    main()
