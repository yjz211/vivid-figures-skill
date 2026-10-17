# 怎么用 Vivid Illustration Skill

[返回首页](../README.md) · [安装指南](INSTALL.md)

## 选择入口与绘图通道

Vivid Illustration Skill 是一个完整资源包，使用轻量总入口和两个按需读取的绘图通道。图件类型明确时直接进入对应通道，不加载另一通道的规则；完整论文、整题或混合图集由总入口先规划，再按图件分派。

| 入口 | 名称 | 使用场景 |
|---|---|---|
| [根 SKILL.md](../SKILL.md) | **Vivid Illustration Skill**<br>`vivid-illustration-skill` | 任务分流、混合图集，以及科学场景插图等路线分派 |
| [数据图子入口](../channels/vivid-figure-skill/SKILL.md) | **Vivid Figure Skill**<br>`vivid-figure-skill` | 数据、统计结果、145 个配方与 3 套完整组合模板 |
| [架构图子入口](../channels/vivid-architecture-diagram-skill/SKILL.md) | **Vivid Architecture Diagram Skill**<br>`vivid-architecture-diagram-skill` | 系统与模型结构、SVG 部件、A/B 与原生可编辑 PPTX；按需使用 Draw.io / TikZ / HTML / Mermaid 技术图路线 |

宿主不一定自动发现子目录里的 Skill。最明确的方式是提供子入口路径；下面的 `<SKILL>` 替换成**完整包根目录**，例如 `D:/agent-skills/vivid-illustration-skill`，不要替换成通道目录。

```text
读取 <SKILL>/channels/vivid-figure-skill/SKILL.md，使用 vivid-figure-skill。
根据 results.csv 比较不同方法的误差分布，用珊瑚青绿配色。
```

```text
读取 <SKILL>/channels/vivid-architecture-diagram-skill/SKILL.md，使用 vivid-architecture-diagram-skill。
根据 system.md 的对象和关系生成系统架构图，按默认 A/B 流程展示候选。
```

名称用于标识所选通道，是否支持直接按名称或斜杠调用由宿主决定。两个子入口共用原位的模板、资产、字体与工具，不能仅复制某个通道子目录安装；安装方式见[完整资源包](INSTALL.md#完整资源包)。

混合任务可以这样交给总入口：

```text
读取 <SKILL>/SKILL.md，使用 vivid-illustration-skill 规划这篇论文的配图。
method.md 描述系统结构，results.csv 包含实验结果。
先列出图件清单，再把数据图交给数据通道、架构图交给架构通道。
每张图只读取所属通道的规则，按需要共享本项目的输入与资源。
```

数据图和架构图分别沿用自己的配色、审图与交付规则；例如，架构图的 A/B 流程不应用到普通数据图，数据图的修复轮数也不覆盖文件式架构候选的自主修正流程。下文先介绍数据图，架构图用法见[架构图与 PowerPoint](#架构图与-powerpoint)。

## 给 AI 什么材料

把 CSV、Excel、JSON 或已有实验结果放进当前项目，告诉 AI 文件位置和你想比较什么。只提供结论文字，通常不足以画出可信的数据图。

最简单的请求是：

```text
用 vivid-illustration-skill 读取 experiment.csv。
我想知道各个方法的结果差异和稳定性，帮我选图并绘制。
用珊瑚青绿配色，输出 PNG、PDF 和绘图源码。
```

如果数据里没有重复试验，AI 就没有依据画“试验波动”或置信区间。你可以补充样本数据，也可以让它只画已有结果。

## 英文图表

默认图内中文。直接告诉助手“这组图使用英文，保留模板效果”，即可沿用同一套模板切换语言；专业缩写、单位、公式和专有名称按实际需要保留。

工作台在图形设置中选择 **图内语言 → English**，固定标签和字体自动更新，原数据不改。数据中的专有名称可点选图中文字修改，或让助手提供英文显示名称；不能确定译义的名称会保留并提示。工作台界面仍使用中文。

下载的独立源码包支持 `python run_demo.py --language en`；需要自定义显示名时加 `--labels labels.json`，文件格式例如 `{"实验组":"Treatment","对照组":"Control"}`。模板特有长句或专业名称需要明确映射，语言选择不会替用户推断研究含义。

中英文共用同一份绘图源码、配色、数据和图层。英文长标签在原有排版检查中处理，不增加模型调用或独立审图阶段。

## 指定配色

绘图统一沿用原鲜艳版的指导，只需选择配色：

| 配色名称 | 大致观感 |
|---|---|
| 珊瑚青绿 | 青绿与珊瑚对比，明亮均衡 |
| 橄榄杏棕 | 橄榄绿、杏色与棕色，自然柔和；数据图 Skill 默认配色 |
| 蓝粉浅彩 | 蓝、粉与浅紫，保留层次并提高辨识度 |
| 蓝天绿地 | 蓝、莓红与浅绿、淡黄，冷暖相间 |
| 柔绿森林 | 柔绿、青灰、赭黄与靛蓝 |
| 粉彩少女 | 浅紫、灰粉、杏粉与玫红 |
| 海洋清风 | 薄荷、青蓝与沙金、暖橙 |

直接说“用珊瑚青绿配色”即可。数据图没有指定时使用橄榄杏棕，已有明确选择时沿用，不另加选色确认。工作台图库预览使用粉彩少女；架构图默认保留资产的语义配色，指定项目色板时按对象角色映射。自定义颜色可以提供至少两个十六进制色值。

选色只改变颜色搭配，保持模板的透明度、渐变和图层，也不要求把连续色条统一换成某个主题色。完整配置说明在 [配色选择](../color-selection.md)，一般使用时不需要手动编辑标记。

## 让 AI 自己选图，或指定模板

你可以说清楚要表达的内容，让 AI 判断：

```text
比较这些组的分布：既要看中心位置，也要看离散程度。
用珊瑚青绿配色，图型你来选。
```

也可以直接点名：

```text
把 samples.csv 里的七组数据画成山脊图。
用珊瑚青绿配色，保留渐变填充和中位数标记。
```

Skill 会先结合数据和你想表达的内容，在全库说明卡中寻找候选，再查看候选实图，从选定的完整模板代码出发适配数据。目录包含145个配方（含32个截图恢复模板及5个参考图模板）与3套完整组合模板，全部模板统一检索，按用途、结构和数据要求搜索，并用标签筛选。你可以打开 [模板图文目录](../catalog/index.html) 自己浏览。

数据摘要只描述字段、缺失、数值范围和组内样本数，不自动指定图型。已经掌握的数据事实会复用，指定模板、修图或换色不会重新跑整套选图。模板里依赖特定数据的部分仍需要数据支持，不能为了凑出模板外观而造数。接入细节见 [数据与模板选择](../figure-selection.md)。

选定后会复制完整模板代码，在底稿内适配数据。每张卡片列出带源码行号的保留重点，例如透明色带、浅填充深描边、边际分布或三维投影，并说明可随数据改变的部分。绘制前先看这些要点，修改后继续对照实际图像；可选源码差异工具帮助定位遗漏，不把正常换色和组数调整当成错误。详见 [源码底稿与保真要点](../template-fidelity.md)。

## 修改已有图

最好同时保留图片、数据和绘图源码：

```text
修改 figures/ 里的这张图，把图例移到上方，解决右侧标签遮挡。
沿用当前风格与配色，尽量保留模板结构、渐变和标记。
```

只给截图可以讨论视觉问题；需要准确修改数值、坐标或统计表达时，仍应提供原数据或代码。

数据图默认出图后查看实际图片，汇总问题再修复，每张图最多三轮修复，通过即停止；仍有问题时说明剩余问题。SVG 架构候选按[共同验收](../architecture/COMMON.md)自主修正，不设固定轮数。你也可以明确要求“只生成首轮，先让我看效果”。

## 输出文件在哪里

通常在当前任务目录的 `figures/` 中：

- **PNG**：直接查看、插入幻灯片或文档。
- **PDF**：用于论文排版；普通线条和文字可保留矢量，部分渐变、密集点或图像层可能是栅格内容。
- **Python 源码**：保存数据读取、计算和绘制步骤，便于复现与继续修改。
- **技术图源文件**：按图型可能是 `.drawio` 或 `.tex`。

具体输出取决于你要求的格式和图型。HTML、Mermaid、AI 场景插图需要对应工具，见 [安装指南](INSTALL.md)。

## 仓库里的文件分别做什么

使用者主要看首页和本目录下的安装、使用说明。下面这些文件是给 AI 或工具读取的，不需要你逐个配置：

| 文件或目录 | 作用 |
|---|---|
| `SKILL.md` | 轻量总入口，识别任务、规划混合图集并分派通道 |
| `channels/vivid-figure-skill/SKILL.md` | `vivid-figure-skill` 数据图通道，按需读取数据适配与审图规则 |
| `channels/vivid-architecture-diagram-skill/SKILL.md` | `vivid-architecture-diagram-skill` 架构图通道，按需读取 SVG、A/B 与 PPTX 规则 |
| `color-selection.md` | 配色选项、默认值及项目配置用法 |
| `figure-selection.md` | 如何理解数据、查候选卡片并查看实图 |
| `template-fidelity.md` | 如何在完整源码底稿上适配、保留特点和核对差异 |
| `catalog/` | 148 张说明卡、精简目录及预览与来源快照 |
| `host-adapter.md` | 告诉 AI 如何在当前工具里执行原绘图流程 |
| `original/` | 保留的原绘图指导、145 个配方和辅助脚本 |
| `architecture/` | 196 套 SVG 架构资产、语义部件、字体、逐图说明与架构工作流 |
| `requirements.txt` | Python 依赖清单 |
| `scripts/` | 完整图集规划工具，以及可选的只读数据摘要脚本 |
| `examples/palette-posters/` | README 示例的数据和绘图脚本 |
| `CHANGELOG.md` | 每次更新做了什么 |

任务目录中可能出现 `.vivid/runtime.json`。它保存当前 Python 和渲染工具路径；项目配色等设置保存在 `.vivid/config.json`。

入口拆分不改变资源位置。无论读取哪一个通道，`<SKILL>` 都是整个包根目录；用户图件、源码工作副本和 `.vivid/` 配置仍放在当前任务工作区。

## 架构图与 PowerPoint

明确的架构任务可以直接读取 [channels/vivid-architecture-diagram-skill/SKILL.md](../channels/vivid-architecture-diagram-skill/SKILL.md)，使用 `vivid-architecture-diagram-skill`。从总入口描述同样的需求，也会被分派到该通道，无需先读取数据图规则。

提供系统对象、依赖关系、层级和反馈路径，并说明图内语言。AI从196套 SVG 资产中共同选择一个主体，按 [双候选流程](../architecture/WORKFLOW.md) 分别生成 A（保留构图）与 B（重组构图），使用独立工作副本并自主审图修正。先展示 A/B 预览和原图等宽对照页；用户选择后沿选中版本完成需要的修改，直接交付原生可编辑 PPTX、SVG、PDF，无需再次询问格式。候选源码和具名部件保留。用户明确只要一个候选或正在修改已有图时不另起两张。原始字号和字体按同宽及相同角色核对。VA-001–004 也使用 SVG 版本，历史 Python 生成器仅供兼容。项目色板需填写本图的语义角色映射，见 [配色](../architecture/PALETTE.md)。

```text
读取 <SKILL>/channels/vivid-architecture-diagram-skill/SKILL.md，使用 vivid-architecture-diagram-skill。
画这个系统的英文架构图。
主体保留清晰的分层结构，输出 SVG、PDF，以及能在 PowerPoint 改字和拖动模块的 PPTX。
```

PPT导出入口为 `scripts/export_architecture_pptx.py`，详细参数和字体安装见 [PPTX说明](../architecture/PPTX.md)。输出是原生形状与文字；箭头不会随模块移动自动重接，PPT修改不回写SVG。完整网页工作台已有单候选架构工具，其单画布任务尚未实现独立 A/B 调度和双候选交付，见 [宿主边界](../architecture/AGENT.md)。
