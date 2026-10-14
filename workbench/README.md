# Vivid 绘图工作台

本地选图、导入数据、调整图形并导出。147 个模板（144 个单图配方和 3 套组合）均可编辑，支持 7 套配色；图库统一使用粉彩少女预览，无需接入大模型。

## 开始使用

安装 Python 3.11 或更新版本，在仓库根目录执行：

```sh
cd workbench
python -m pip install -r requirements.txt
python -X utf8 scripts/manage.py serve --open
```

浏览器打开 <http://127.0.0.1:8766/index.html>。Windows 安装依赖后也可双击 `启动工作台.cmd`；启动器优先使用工作台的 `.venv`，随后查找 `py` 或 `python`。服务运行期间保留启动窗口。

只看图库和下载原始模板包时，可直接用浏览器打开 `index.html`。编辑数据和生成新图需要本地 Python 服务。Plotly 静态导出需要 Chrome / Chromium，中文图需要中文字体。

## 使用流程

1. 按分类或关键词找到模板，查看预览和适用数据。
2. 点击「修改数据，使用此模板」，导入 CSV、TSV、XLSX，或直接编辑表格。
3. 核对字段对应和数据格式，更新预览；可切换配色、调整属性，点选和拖动 Matplotlib 图中文字。
4. 导出 PNG、PDF、SVG、CSV、绘图源码或完整复现包；保存项目以便继续编辑。

支持排序、筛选、转置、长宽表转换、分组汇总、多表输入、撤销重做、本地项目与样式保存。需要统计分析结果的模板仍需用户提供相应输入；具体限制见 [使用说明](使用说明.md)。

## 文件位置

| 目录 | 内容 |
| --- | --- |
| `frontend/` | 前端界面、表格、对象交互和样式 |
| `editor_backend/` | Python 服务、数据契约、完整模板源码适配和运行工具 |
| `assets/` | 147 个模板的源码、卡片、预览、下载包和前端依赖 |
| `scripts/`、`tests/` | 维护入口与回归测试 |
| `docs/` | 维护说明、模板来源快照和交互调研 |
| `workspace/` | 运行时创建的用户项目、样式和绘图任务，不进入 Git |
| `verification/` | 运行测试后生成的验证产物，不进入 Git |

工作台随本仓库维护，使用自带模板快照。Skill 入口仍是仓库根目录的 `SKILL.md`；使用工作台无需安装 Skill。

维护方法见 [维护说明](docs/MAINTENANCE.md)，使用许可见仓库 [LICENSE](../LICENSE)。
