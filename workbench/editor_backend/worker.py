from pathlib import Path
import json,sys,traceback,zipfile,csv,shutil
from engine import render_project
folder=Path(sys.argv[1]).resolve()
def status(data):
    p=folder/'status.tmp';p.write_text(json.dumps(data,ensure_ascii=False),encoding='utf8');p.replace(folder/'status.json')
try:
    status({'state':'running','message':'正在执行模板源码'})
    evidence=render_project(folder)
    project=json.loads((folder/'project.json').read_text(encoding='utf8'))
    with (folder/'data.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(project['table']['headers']);w.writerows(project['table']['rows'])
    backend=Path(__file__).parent
    (folder/'run.py').write_text("from pathlib import Path\nfrom engine import render_project\nrender_project(Path(__file__).resolve().parent)\nprint('已生成 figure.png / figure.pdf / figure.svg')\n",encoding='utf8')
    (folder/'README.md').write_text('# 本次绘图项目\n\n安装 Python 3.10+ 后，在解压目录运行：\n\n```\npython -m pip install -r requirements.txt\npython run.py\n```\n\nproject.json 保存本次数据、字段对应与设置；data.csv 可直接用 Excel 打开。\nsource.py 是接入前的完整模板，plot.py 是本次适配后的完整源码；source.diff 记录适配差异。\nengine.py 只在明确的数据入口替换示例值，使用 project.json 生成 plot.py。\n如手动修改绘图主体，请编辑 source.py 对应绘图段，再执行 run.py；直接编辑 plot.py 会在重新运行时被覆盖。\n数据口径及实际绘图数组见 data_used.json。\n字体优先使用微软雅黑，其他系统需安装中文字体。\n',encoding='utf8')
    with (folder/'README.md').open('a', encoding='utf8') as f:
        f.write('\n图形对象修改保存在 project.json 的 object_edits，交互视角保存在 plotly_view。object_editor.py 在原模板绘制后回放这些修改；objects.json 记录可编辑对象和未应用的旧修改。数据结构改变后，旧对象修改可能不再适用。\n')
        f.write('\n多表模板的全部输入 CSV 位于 tables/；data.csv 仅为导出时的当前表。修改数据后重绘，请修改 project.json 中对应数据表，或在工作台打开项目并重新导入 CSV。\nPlotly 静态导出需要 Chrome / Chromium；三维图的 PDF / SVG 可能包含栅格图层。\n')
    (folder/'requirements.txt').write_text('numpy\npandas\nscipy\nmatplotlib\nseaborn\nscikit-learn\nscikit-image\nadjustText\nnetworkx\nplotly\nkaleido\npycirclize\nFaker\ngeopandas\nlibpysal\nesda\nPillow\nopenpyxl\nPyMuPDF\n',encoding='utf8')
    export_tables=project.get('tables',{'data':project['table']}).copy()
    if project.get('active_table') in export_tables:export_tables[project['active_table']]=project['table']
    data_dir=folder/'tables';data_dir.mkdir(exist_ok=True)
    from schema import CONTRACTS
    allowed=[t['key'] for t in CONTRACTS[project['template']]['tables']] if project['template'] in CONTRACTS else ['data']
    for key in allowed:
        tab=export_tables[key]
        with (data_dir/(key+'.csv')).open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.writer(f);w.writerow(tab['headers']);w.writerows(tab['rows'])
    with zipfile.ZipFile(folder/'reproduce.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in ['run.py','README.md','requirements.txt','project.json','data.csv','source.py','original.py','plot.py','source.diff','data_used.json','.vivid/config.json']:
            z.write(folder/name,name)
        for name in ['engine.py','schema.py','gallery_theme.py','catalog_data.py','statistics_helpers.py','object_editor.py']:z.write(backend/name,name)
        z.write(folder/'objects.json','objects.json')
        own={project['template']:CONTRACTS[project['template']]} if project['template'] in CONTRACTS else {}
        z.writestr('catalog-contracts.json',json.dumps(own,ensure_ascii=False,indent=2))
        for p in data_dir.glob('*.csv'):z.write(p,'tables/'+p.name)
        for p in (backend/'_utils').rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix in ['.py','.json','.geojson','.mplstyle']:z.write(p,'_utils/'+p.relative_to(backend/'_utils').as_posix())
        license_path=backend.parent/'模板来源许可.txt'
        if license_path.exists():z.write(license_path,'LICENSE')
    status({'state':'done','notes':evidence['notes'],'message':'预览与导出已就绪'})
except Exception as e:
    traceback.print_exc();status({'state':'error','message':getattr(e,'detail',{}).get('message',str(e)) or '绘图失败，请检查数据。'})
    sys.exit(1)
