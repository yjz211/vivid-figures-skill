"""No-model browser integration: XLSX sheets and four-table manual binding."""
from pathlib import Path
import io, json, os
import openpyxl
from playwright.sync_api import sync_playwright

WEB = Path(__file__).resolve().parents[1]
OUT = WEB / 'verification/polish'
OUT.mkdir(parents=True, exist_ok=True)
URL = os.environ.get('VIVID_TEST_URL', 'http://127.0.0.1:8767')
errors = []


def xlsx(sheets):
    book = openpyxl.Workbook()
    book.remove(book.active)
    for name, rows in sheets.items():
        sheet = book.create_sheet(name)
        for row in rows:
            sheet.append(row)
    buffer = io.BytesIO()
    book.save(buffer)
    return buffer.getvalue()


line_headers = ['月份', '基线', '优化', '联合', '不用于绘图']
line_rows = [[f'{i + 1}月', 90 + i * 4, 84 + i * 3, 78 + i * 2, 999] for i in range(8)]
bar_headers = ['园区', '0', '优化']
bar_rows = [['滨海', 132, 105], ['北部', 144, 120], ['西部', 126, 99], ['南部', 139, 110]]
scatter_headers = ['算法', '负荷', '能耗']
scatter_rows = [[g, i + 1, (i + 1) * (1.1 + j / 10) + (i % 3)] for j, g in enumerate(['基线', '优化', '联合']) for i in range(18)]
hist_headers = ['策略', '响应时长']
hist_rows = [[g, round(12 + j * 2 + i / 7 + (i % 5) / 3, 4)] for j, g in enumerate(['基线', '优化', '联合']) for i in range(30)]

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe', headless=True)
    page = browser.new_page(viewport={'width': 1600, 'height': 1000})
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(URL + '/agent.html')
    page.wait_for_function('state.session !== null')
    sid = page.evaluate("""async () => {
      const s = await api('/api/agent/sessions', {name:'自测 · Excel 与多表对应'});
      await sessionList(); await openSession(s.id); return s.id;
    }""")

    # An invalid cover sheet must not prevent selecting the second, valid sheet.
    page.locator('#file-input').set_input_files({
        'name': '含封面的工作簿.xlsx',
        'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'buffer': xlsx({'说明封面': [['这是说明封面，数据在下一张工作表']], '月度数据': [line_headers] + line_rows})})
    page.wait_for_selector('#sheet-dialog[open]')
    assert page.locator('#sheet-choice option').all_text_contents() == ['说明封面', '月度数据']
    page.locator('#sheet-choice').select_option(label='月度数据')
    page.screenshot(path=str(OUT / 'excel-select-valid-sheet.png'))
    page.locator('#sheet-confirm').click()
    page.wait_for_function('state.session.datasets.length === 1')
    dataset = page.evaluate('state.session.datasets[0]')
    assert dataset['table'] == {'headers': line_headers, 'rows': line_rows}, dataset
    line_id = dataset['id']
    page.locator('[data-close="dataset-dialog"]').click()

    # Single-sheet XLSX imports directly, retaining numeric zero as a header.
    page.locator('#file-input').set_input_files({
        'name': '单表园区.xlsx',
        'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'buffer': xlsx({'园区数据': [['园区', 0, '优化']] + bar_rows})})
    page.wait_for_function('state.session.datasets.length === 2')
    assert not page.locator('#sheet-dialog').evaluate('(el) => el.open')
    dataset = page.evaluate('state.session.datasets.find(d => d.name.startsWith("单表园区"))')
    assert dataset['table'] == {'headers': bar_headers, 'rows': bar_rows}, dataset
    bar_id = dataset['id']
    page.locator('[data-close="dataset-dialog"]').click()

    extra_ids = page.evaluate("""async (tables) => {
      const ids = [];
      for (const item of tables) ids.push((await api('/api/agent/sessions/' + state.session.id + '/datasets', item)).id);
      await refreshSession(); return ids;
    }""", [
        {'name': '设备观测', 'table': {'headers': scatter_headers, 'rows': scatter_rows}},
        {'name': '响应样本', 'table': {'headers': hist_headers, 'rows': hist_rows}},
    ])

    # Use the actual gallery and all field selectors rather than the bind API.
    page.locator('#gallery-open').click()
    page.locator('#gallery-search').fill('四面板')
    page.locator('[data-choose="basic.multipanel"]').click()
    page.wait_for_selector('#binding-dialog[open]')
    for key, dataset_id in zip(['line', 'bar', 'scatter', 'hist'], [line_id, bar_id, *extra_ids]):
        section = page.locator(f'#binding-tables [data-key="{key}"]')
        section.locator('[data-source]').select_option(dataset_id)
        if key == 'line':
            section.locator('[data-value="4"]').uncheck()
        elif key in ('scatter', 'hist'):
            for column in range(3 if key == 'scatter' else 2):
                section.locator(f'[data-role="{column}"]').select_option(str(column))
    page.locator('#binding-name').fill('四表联动 · 真实字段验证')
    page.screenshot(path=str(OUT / 'multipanel-field-binding.png'), full_page=True)
    page.locator('#binding-create').click()
    page.wait_for_function('state.ready && state.chart?.job', timeout=150000)
    page.evaluate('VividAgent.flush()')
    chart = page.evaluate('state.chart')
    expected = {
        'line': {'headers': line_headers[:4], 'rows': [row[:4] for row in line_rows]},
        'bar': {'headers': bar_headers, 'rows': bar_rows},
        'scatter': {'headers': scatter_headers, 'rows': scatter_rows},
        'hist': {'headers': hist_headers, 'rows': hist_rows},
    }
    assert chart['project']['tables'] == expected, chart['project']['tables']
    assert chart['project']['settings']['palette'] == 'pastel-girl'
    assert chart['project']['settings']['title'] == '四表联动 · 真实字段验证'
    frame = page.locator('#editor-host iframe').element_handle().content_frame()
    frame.wait_for_function('!rendering && !liveRenderPending && lastRender', timeout=150000)
    svg = frame.locator('#object-preview').element_handle().content_frame()
    svg.wait_for_selector('#vivid-title')
    title_layout = svg.evaluate("""() => {
      const bounds = id => {
        const r = document.getElementById(id).getBoundingClientRect();
        return {left:r.left, top:r.top, right:r.right, bottom:r.bottom, width:r.width, height:r.height};
      };
      const title = bounds('vivid-title'), panel = bounds('vivid-ax1-left-title');
      return {title, panel, overlap:Math.max(0, Math.min(title.right,panel.right)-Math.max(title.left,panel.left))*Math.max(0, Math.min(title.bottom,panel.bottom)-Math.max(title.top,panel.top))};
    }""")
    assert title_layout['overlap'] == 0, title_layout
    page.screenshot(path=str(OUT / 'multipanel-bound-result.png'))
    assert not errors, errors
    result = {'passed': True, 'session': sid, 'chart': chart['id'], 'job': chart['job'],
              'excel_cover_sheet_selection': True, 'single_sheet_xlsx': True, 'numeric_zero_header': True,
              'browser_multi_table_binding': True, 'unused_numeric_column_excluded': True,
              'all_project_tables_exact': True, 'title_panel_no_overlap': title_layout,
              'rows': {k: len(t['rows']) for k, t in expected.items()}, 'browser_errors': errors}
    (OUT / 'import-binding-results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(result, ensure_ascii=False), flush=True)
    browser.close()
