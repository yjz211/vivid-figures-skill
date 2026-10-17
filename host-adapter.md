# 执行环境与项目配置

`<SKILL>` 是 Skill 安装目录，`<RES>` 是 `<SKILL>/original/resources`，`<WORKSPACE>` 是任务工作区。用当前助手的文件、终端、图像查看及可用的图像生成能力执行工作流。

## 初始化

使用同一个 Python 3.10+ 环境安装 [依赖](requirements.txt)，运行：

```text
python "<RES>/scripts/resolve_runtime.py"
python "<RES>/scripts/bootstrap.py" --workspace "<WORKSPACE>" --profile modeling-competition
```

初始化复制绘图工具及模板，保留用户修改过的文件，并刷新识别到的旧工具副本。生成的 `_utils/`、`skills/shared-scripts/`、`_templates/` 属于任务工作区。后续命令在工作区执行；Bash 片段使用宿主可用的 Bash，Windows 可使用 Git Bash。Bash 请使用 runtime.json 中解析的路径，避免在 Windows 误用 WSL 启动器；`VIVID_BASH` 可显式指定。`VIVID_PYTHON` 可指定同一 Python。

## 配置

- `.vivid/config.json`：项目设置。配色见 [配色选择](color-selection.md)；其他可选字段为 `style`（默认 clean_open）、`style_custom`、`language`（默认 zh，用户要求英文时为 en）、`output_format`（pdf/docx/png 等）、`template`、`title`。保留用户已有字段。读写用 `_utils/vivid_config.py`，支持从子目录查找项目根目录。
- `.vivid/runtime.json`：可执行文件路径及工具复制记录，由初始化生成。
- `.vivid/figure-plan-policy.json`：完整图集的规划校验状态，由规划 CLI 维护。

图内语言沿用本次项目设置；界面语言与图内语言分开。英文适配可直接修改工作源码中的显示文字，或在原保存调用前应用同一份映射：

```python
from _utils.figure_language import localize_figure
english_labels = {"得分": "Score", "实验组": "Treatment"}
localize_figure(fig, language="en", labels=english_labels,
                protected_texts=["实验组"])  # 原始数据名称由明确映射翻译
```

共享工具补齐常见固定文字和英文回退字体；任意数据名称、专业术语与模板特有长句仍按任务明确映射，保留未指定的原始名称。长英文确实挤压时只调整换行、图例位置和必要边距，不改图层设计。映射不更改输入表头、数值或分组键。

### 默认字体

中英文数据图共用字体策略：普通无衬线图的英文与数字优先 Arial，中文优先 MiSans；缺少时按已安装的 Helvetica / Liberation Sans / Noto Sans 和思源黑体 / Noto Sans CJK / 微软雅黑等回退。保留明确设计的 Times New Roman 等衬线风格，以及用户指定的字体、字号、字重、数学符号和位置。字体文件不随模板重复打包，跨机器要求完全一致时应安装相同字体。

本工具使用 MiSans 时，建议安装[官方 TTF](https://hyperos.mi.com/font/zh/download/)的 Regular、Semibold、Bold，保证中文粗体有实际字形。共享工具可识别 Windows 系统和当前用户 Fonts 目录；PDF 使用 TrueType 嵌入。

`setup_style()` 与共享保存函数应用该策略；直接调用 `fig.savefig()` 或 Plotly 导出时，在最后布局前调用 `apply_figure_fonts(fig, language="zh")`（来自 `_utils.figure_language`），英文使用 `"en"`。图库、编辑器和下载包已经接入；旧默认字体不能通过追加回退列表覆盖新默认。

## 渲染工具

- 数据图：Python；保存源脚本、真实输入及实际输出。
- 架构资产：`python "<SKILL>/scripts/render_architecture.py" fig.svg`；用 Chromium 输出 PNG/PDF。原生可编辑 PPTX 用 `scripts/export_architecture_pptx.py`，依赖见 [架构运行环境](requirements-architecture.txt)，流程与 Office 验证边界见 [PPTX 导出](architecture/PPTX.md)。
- Draw.io：`python "<RES>/scripts/export_drawio.py" source.drawio --format pdf`；需要桌面版 Draw.io，路径可用 `DRAWIO_PATH` 指定。
- HTML：`python "<RES>/scripts/render_html.py" source.html --format both`；使用本机 Chrome/Chromium 和 Python Playwright，路径可用 `CHROME_PATH` 指定。公式加 `--render-math`，几何检查加 `--geom-check`。
- TikZ：XeLaTeX；PDF 预览使用 PyMuPDF 或 Poppler。
- Mermaid：`python "<RES>/scripts/render_mermaid.py" source.mmd`；需要 Node.js 和 mmdc。
- 科学场景插图：使用宿主提供或用户已配置的图像生成工具；保留工作流的完整构图提示词。缺少工具时说明缺失能力，不将插图改作数据证据。

视觉检查由当前助手实际打开图件完成。SVG 架构候选按 [共同验收](architecture/COMMON.md)自主修正；其他任务的次数及范围见 [检查与修复](original/review-policy.md)。图集来源用用户提供或确认的数据、模型结果及证据文件；只要求绘图时，在图件完成后停止。
