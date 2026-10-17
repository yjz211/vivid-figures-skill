---
name: vivid-architecture-diagram-skill
description: 制作与修改模型、系统和方案架构图，以 SVG 资产保留设计风格并适配当前语义；文件型任务支持 A/B 候选、用户选择及原生可编辑 PPTX/SVG/PDF 交付，也按需路由 Draw.io、TikZ、HTML 和 Mermaid 技术图。
---

# Vivid Architecture Diagram Skill · 架构图

这是 Vivid 整包内的架构通道，可直接读取本文件开始任务；共享资产和脚本仍位于包根目录，不单独复制一套。仅加载本次路线所需文档，不加载数据图选型、配色或执行规则。

`<SKILL>` 始终指本文件所在目录向上两级的 **Vivid 包根目录**，即 `../../`，不是 `channels/vivid-architecture-diagram-skill/`；`<RES>` 为 `<SKILL>/original/resources`。工作流中的资源脚本路径相对于 `<RES>`，图件与 `.vivid/` 则相对于用户任务工作区。

新图图内文字默认中文；用户或当前项目明确要求英文时统一使用英文。保留必要的专业缩写、单位、公式和专有名称，不改动真实对象身份。已有作品未要求改语言时保留当前文字。

## 选择当前路线

- **文件型新建 SVG 架构图**：读取 [A/B 工作流](../../architecture/WORKFLOW.md)，按下节生成双候选。196 套资源均以 SVG 工作副本适配，历史 Python 生成器仅作旧工程兼容。
- **已有图件、已选候选、改字换色或单纯导出**：读取 [共同制作与验收](../../architecture/COMMON.md)，从用户当前 SVG 与源码继续，仅做所请修改及必要修复；不重新选择模板或启动 A/B。需要 PPTX 时读取 [导出说明](../../architecture/PPTX.md)。
- **当前网页工作台**：读取 [网页 Agent 边界](../../architecture/AGENT.md) 和 [共同制作与验收](../../architecture/COMMON.md)。网页目前一次保存一个候选，按宿主的当前版本与保存流程执行；不启动文件型 A/B 调度，也不声称网页已经支持双候选。手动编辑使用 [模块编辑器](../../architecture/EDITOR.md)。
- **用户指定其他技术图格式或任务需要精确几何**：按下方替代路线执行，不强制改用 SVG 资产。

## 文件型新图：A/B 到交付

此节只适用于可保存独立图件目录的文件型任务，详细操作以 [WORKFLOW.md](../../architecture/WORKFLOW.md) 为准。

1. 按当前对象、层次、连接与反馈关系检索 [资产目录](../../architecture/catalog.json)，查看真实预览和所选 `TEMPLATE.md`。确定一个共同主资产，保存事实、语言和同宽展示要求；资产中的示例标签、曲线和拓扑不是当前任务事实。
2. 默认独立生成 **A：保留构图** 与 **B：重组构图**。有子代理时使用新上下文，只分发各自的路径文件、共同简报及必要输入，模型设置遵从当前用户要求；两路不互看成图或评价。协调者按工作流分发 [A 路径](../../architecture/paths/A.md) / [B 路径](../../architecture/paths/B.md)，每个生成者只读自己的路径与其引用文档。
3. 两路按 [COMMON.md](../../architecture/COMMON.md) 实际看图、自主修正，再交回可复现源码、SVG/PDF/PNG 和真实矢量部件；不设置固定自改轮数。检查通过即停止，真实缺失输入或环境限制则说明未完成项。用户明确只要单候选时遵从其要求。
4. 展示原图与 A/B 的等宽对照，让用户实际选择；不由协调者代选，也不提前为未选候选批量导出 PPTX。
5. 用户选择即启动最终交付；若有修改，先只改所选版本，再按 [PPTX.md](../../architecture/PPTX.md) 直接交付同版的 **原生可编辑 PPTX、SVG、PDF 和字体包**，不再询问格式或确认。用户明确另有交付要求时从其要求。PPTX 必须含可编辑文字和矢量对象，不能以整图图片或整图 SVG 置入冒充；实际核验可编辑性和视觉结果，如实说明未完成的 Office 验证。

## 制作时保住的设计

[COMMON.md](../../architecture/COMMON.md) 是 SVG 制作与验收的共同规则。每次制作或修改都读取它；以下约束同时适用于 A、B、单候选和网页任务：

- 复用仍适用的真实 SVG 图形和细节。原图有图标、对象轮廓或结构示意时，保留其表达作用；语义改变就自行绘制符合当前对象的可编辑 SVG 图案并编排，不能为省事删成标签或普通文本框。无当前依据的内容不照搬，也不虚构数据或结构。
- 保留字体角色、真实字重、倾斜与字号层次；在相同展示宽度下检查实际文字大小和模块比例。长标签先精简、换行和调整局部布局，不默认缩字，也不靠扩宽画布把主体整体缩小。缺字时按原字体角色选择覆盖所需文字的字体，不改成英文规避。
- 颜色跟随对象身份与状态。保持原有语义配色；用户选择顶层色板时才按 [语义配色](../../architecture/PALETTE.md) 映射角色，不直接套数据图的默认色序。
- 结构、连线端点、对象键、部件归属和当前语义同步。自动检查只是证据，仍需实际查看整图及主要部件；留白、文字层次和图案表达也属于验收。续改的保真基线是当前已接受版本，不回退历史模板。

## 执行与替代路线

SVG 准备、渲染和导出命令见上述工作流。只需安装 [架构依赖](../../requirements-architecture.txt)，首次渲染安装 Chromium：

```text
python -m pip install -r "<SKILL>/requirements-architecture.txt"
python -m playwright install chromium
```

可编辑 PPT 的模块移动不会自动重接箭头，PPT 人工修改也不自动回写 SVG。来源与字体许可随交付保留，见 [资产来源](../../architecture/ATTRIBUTION.md)。资源齐全不代表所有新场景均已通过视觉验证。

以下路线仅在当前任务需要时加载。其资源和脚本共用 `<RES>`；先读 [绘图入口](../../original/resources/ENTRYPOINT.md) 的分类、初始化和对账要求，再仅执行所选路线，已有 SVG 资产任务无需另行初始化它们：

- Draw.io 可编辑技术图或 TikZ 精确数学/物理几何：[技术图工作流](../../original/resources/workflows/paper-technical-diagram.md)。
- 用户明确选择 HTML：[HTML 工作流](../../original/resources/workflows/paper-figure-html.md)。
- 用户明确选择 Mermaid 或文本维护：[Mermaid 工作流](../../original/resources/workflows/mermaid-diagram.md)。

已属于完整图集时保留上游 `FIGURE_MANIFEST` 的类别、事实来源、用途和输出路径。SVG 架构项按 [图集架构执行](../../original/resources/workflows/architecture-assets.md) 对账，A/B 合计一个图项，等待用户选择时仍未完成。单张架构图不因此扩展成整套数据图任务。
