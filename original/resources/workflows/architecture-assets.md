# SVG 架构资产工作流

`FIGURE_MANIFEST` 中的 `ARCHITECTURE` 类使用包根目录的 [架构图子 Skill](../../../channels/vivid-architecture-diagram-skill/SKILL.md)，由它进入 [架构工作流](../../../architecture/WORKFLOW.md)。按该通道选择资产、准备 SVG 工作副本、生成并检查候选；不要加载数据图制作规则或再初始化 Draw.io/TikZ 工作流。

新建图默认先生成 A/B 两个候选，让用户实际选择后再完成所选版本的原生可编辑 PPTX、SVG 和 PDF。用户明确单候选、指定交付格式或要求修改已有版本时遵从其范围。候选 A/B 合计为一个清单项；等待选择时该项仍未完成，不能为了清单对账代用户选择。

图集计划保留 `class=ARCHITECTURE`、真实来源和 `purpose`。总技术路线图使用 `purpose=roadmap`，无需命名为 `fig_roadmap`；`recipe` 可记录 `asset:VA-001` 等实际资产编号。文件按计划的实际位置对账，通常位于 `figures/<图id>/final/`。沿用架构共同验收与来源记录，不套用普通配方的 Python 源码检查或三轮修复上限。
