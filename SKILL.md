---
name: vivid-figures-skill
description: 规划、生成、修改和检查数学建模与科研图表；包含145个完整源码配方、3套组合模板、统一配色和来源差异工具，以及Draw.io/TikZ、HTML/Mermaid和科学场景插图。
---

# Vivid Figures Skill

一套绘图指导、一个入口。根据当前任务加载下列资源，已读且未变化的内容复用；阶段划分不要求额外模型调用。

图内文字默认中文，仅在使用者明确要求时使用英文；适配模板时同步替换标题、坐标轴、图例、文字刻度和注释中的示例文字，保留专业缩写、单位、公式和必要的专有名称。

## 数据图

1. **选择**：尚未指定模板时读取 [数据与模板选择](figure-selection.md) 和 [设计目标](original/drawing-guide.md)，按数据与目的检索卡片、查看候选实图。用户指定模板、修图或换色时沿用选择，直接进入适配。
2. **适配**：读取 [源码底稿与保真](template-fidelity.md)，用工具将选定的完整源码写成工作脚本，在这个实际文件上修改。读取所选卡片及预览、[执行环境](host-adapter.md)、[数据图执行](original/resources/references/paper-figure.md)、[配色](color-selection.md) 和 [尺寸预计算](original/fragments/original-size-preflight.md)。只加载本次需要的模板和专题。
3. **检查**：用来源底稿比较当前源码，再按 [检查与修复](original/review-policy.md) 打开实际图件，核对模板特点、数据口径与可读性。差异提示不是视觉通过结论，必要适配不必为消除提示改回演示数据。

所选模板的具体实现决定默认视觉结构；通用技法帮助解决实际问题。数据真实性及用户要求决定需要适配什么；选图阶段的新颖性目标不要求适配阶段重新设计。

## 完整组合模板

- `template.sem_violin_pearson`：[小提琴＋Pearson](templates/sem-violin-pearson/TEMPLATE.md)，保留原版默认样式。
- `template.shap_dependence` / `template.shap_contribution`：[SHAP组合](templates/shap-composites/TEMPLATE.md)，保留完整布局与真实SHAP输入口径。

完整组合使用各自的源码和CLI，并按保真说明保存来源；不拆成普通配方重新拼接。

## 其他任务

- 完整论文或整题图集：先读 [上游规划](original/upstream-planning.md) 和 [绘图入口](original/resources/ENTRYPOINT.md)，保留 FIGURE_MANIFEST 分类、执行顺序与对账。明确单图或用户限定的小批数据图不重启整题规划。
- 技术图、HTML、Mermaid或场景插图：读 [绘图入口](original/resources/ENTRYPOINT.md)，只加载所选路由。数值图不因初始化加载这些指导。
- 需要特定统计、优化、网络或布局知识时，再读相应 `original/fragments/` 或 [知识索引](original/resources/assets/shared-scripts/figure_style_guide.md) 指向的专题。

`<SKILL>` 为本包目录，`<RES>` 为 `original/resources`；`_utils/`、`figures/` 和 `.vivid/` 均相对于任务工作区。工作流中的脚本路径相对于 `<RES>`，使用本包当前资源。
