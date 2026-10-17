---
name: vivid-illustration-skill
description: 科研与数学建模绘图总入口，按任务分派到独立的数据图或架构图子 Skill；支持完整图集规划、数据模板适配、SVG 架构设计及可编辑 PPTX 交付。
---

# Vivid Illustration Skill · 绘图总入口

本入口只负责识别任务与分派。先确定下面的通道，只读取所选子 Skill 及其当前任务需要的引用，不预先加载另一通道。用户直接指定通道、模板或已有作品时沿用选择。

| 当前任务 | 读取的子 Skill |
|---|---|
| 真实数据、统计结果、实验对比、分布、时序、空间数据、完整组合模板 | [数据图 · vivid-figure-skill](channels/vivid-figure-skill/SKILL.md) |
| 系统/模型架构、方法框架、技术路线、结构示意、已有 SVG 修改、架构图可编辑 PPT；用户指定的 Draw.io/TikZ/HTML/Mermaid 技术图 | [架构图 · vivid-architecture-diagram-skill](channels/vivid-architecture-diagram-skill/SKILL.md) |

按要表达的内容分派，不按最终文件扩展名分派：数据曲线即使交付 SVG/PDF，仍属于数据图；包含数值的系统结构图也不因此改走统计绘图。边界不明时先读取用户材料，确认需要表达的是量值证据还是对象关系；无法判断且会改变结果时再澄清。

## 完整图集与混合任务

完整论文或整题图集先读 [上游规划](original/upstream-planning.md) 与 [绘图入口](original/resources/ENTRYPOINT.md)，维护同一份 FIGURE_PLAN / FIGURE_MANIFEST，再按每项类别分派到对应子 Skill。分类、执行顺序、来源与最终对账沿用规划合同。

混合任务共享用户事实、图内语言和项目设置，不共享两条通道的制作限制：数据图按数据图的源码保真与验收；SVG 架构图按架构图的字体/图案与候选交付流程。可以分别执行；给独立生成任务只传其通道、必要输入与输出目录。明确单图或用户限定的小批任务不重启整题规划。

科学场景插图按 [绘图入口](original/resources/ENTRYPOINT.md) 中相应路线处理，不用插图代替数据证据或精确结构。

## 路径与接入

`<SKILL>` 始终指本文件所在的完整包根目录；`<RES>` 为 `<SKILL>/original/resources`，`<WORKSPACE>` 为当前任务工作区。两个子 Skill 位于 `channels/` 内，读取子入口不会改变这些根路径。工作区中的 `_utils/`、`figures/` 和 `.vivid/` 不属于安装目录。

两个通道共用一份资源包，既可从本入口分派，也可直接读取相应子 `SKILL.md`。不要单独复制子目录安装；宿主是否自动发现嵌套 Skill 由其自身决定。安装与直接调用方式见 [安装说明](docs/INSTALL.md)。

[本地工作台](workbench/index.html) 提供图库与编辑入口，操作和自动化范围见 [工作台说明](workbench/README.md)。文件式 Skill 与网页 Agent 的执行边界在对应通道说明中定义。
