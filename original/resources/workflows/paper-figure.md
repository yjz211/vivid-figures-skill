# 数据图工作流

先进入 [数据图子 Skill](../../../channels/vivid-figure-skill/SKILL.md)，按其引用的 [数据图执行](../references/paper-figure.md) 初始化、运行与核对。只加载本次数据图所需知识，不加载架构图候选与交付规则。

- 选图：包根目录 `figure-selection.md`；指定模板时直接定位卡片及预览。
- 适配：包根目录 `template-fidelity.md`，工具生成完整源码后局部修改。
- 检查：`../review-policy.md`（相对于 resources），源码差异和实际图件共同核对。

保留模板的渐变、透明层次、连续色阶、轮廓及有依据的信息元素；数据语义不支持或阅读确有困难时作必要适配。小样本或大量相同值不能凭空形成密度证据；雨云等结构沿用原有错位关系。

使用工作区 `.vivid/runtime.json` 的执行路径。完整图集保留规划、分类与对账；明确小批图不进入整题规划。
