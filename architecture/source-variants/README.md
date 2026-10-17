# VA-001–004 的 SVG 资产

正式目录中的 VA-001–004 统一指向这里的 SVG 资产，采用标准 `source_asset` 编辑流程；编号与名称保持不变。其余192套继续使用 `source-assets/` 中的 SVG 资产。

| 编号 | 当前 SVG 资产 |
|---|---|
| VA-001 | `network-inset-svg/` |
| VA-002 | `artifact-pipeline-svg/` |
| VA-003 | `framed-platform-svg/` |
| VA-004 | `feedback-agents-svg/` |

`architecture/templates/` 下的原 Python 生成器保留供旧项目与历史实验兼容，新建任务不再路由到它们。每个 SVG 包保存原生图形、可编辑文字、几何元数据、稳定对象键和部件说明；字体要求见各自 `TEMPLATE.md`。

VA-004 转换以原模板默认输出为底稿，保留全部 71 个原生图元、30 处文字和 21 个语义部件。2026-10-17 在同一环境中比较 1248×1086 的 PNG，差异像素为 0；两个 PDF 均嵌入 ArialMT，且不含位图。

在仓库根目录可生成默认 SVG，再用现有渲染器导出：

```text
python architecture/source-variants/feedback-agents-svg/make_figure.py --config architecture/source-variants/feedback-agents-svg/example.json --out figures/va004-svg --parts
python scripts/render_architecture.py figures/va004-svg/fig.svg
```

VA-002–004 默认依赖系统 Arial，标签替换需显式提供 `font_family: Arial`。VA-001 使用衬线与等宽字体角色，另提供随包 OFL 字体的显式 portable 配置；详见各资产的 `TEMPLATE.md` 和 `FONTS.md`（如有）。

统一准备入口为 `python scripts/prepare_architecture.py --id VA-004 --out figures/va004-svg-work`；VA-001–003 使用相应编号。准备目录必须为空，工具复制 SVG 底稿、运行时、配置、部件信息和所需字体文件。

VA-004 的首次 SVG 对照实验位于同级桌面工作目录：`Vivid-工作文件/skill-first-draft-20261017/sol61-low-svg-group/`。实验使用四版既有规则、相同医院场景和独立的 gpt-6.1-sol / low 代理，最终输出允许自主审图修改；每种条件只有一次样本。VA-001–003 的转换复现与逐像素检查、四资产正式准备验证位于 `Vivid-工作文件/skill-first-draft-20261017/svg-unified-20261017/conversion/`。
