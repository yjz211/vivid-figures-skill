---
name: vivid-figure-skill
description: 从真实数据规划、生成、修改和检查科研与数学建模数据图；使用145个配方和3套完整组合模板，保留模板设计并适配统计含义、语言和配色。
---

# Vivid Figure Skill · 数据图

处理数值比较、分布、关系、预测、统计、优化及真实空间数据的图件。用户已指定模板、要求修图或换色时沿用当前选择；已有有效源码和结果继续修改，不重新选图。三个阶段是一次任务内的工作步骤，不要求额外模型调用。

本文件随 Vivid Illustration Skill 完整包使用，可由根入口路由或直接读取。`<SKILL>` 指本文件向上两级的包根目录（`../../`），不是 `channels/vivid-figure-skill/`；`<RES>` 为 `<SKILL>/original/resources`。`_utils/`、`figures/` 和 `.vivid/` 相对于任务工作区，资源内的脚本路径按其说明解析，不把文件复制到子通道。

## 选择、适配、检查

1. **选择**：首次选图读取 [数据与模板选择](../../figure-selection.md) 和 [设计目标](../../original/drawing-guide.md)，结合数据含义与表达目的检索卡片，并实际查看候选预览。用户指定模板时直接定位对应卡片、实图及源码；修图与换色跳过重新选择。
2. **适配**：读取 [源码底稿与保真](../../template-fidelity.md)、所选卡片与预览、[执行环境](../../host-adapter.md)、[数据图执行](../../original/resources/references/paper-figure.md)、[配色](../../color-selection.md) 和 [尺寸预计算](../../original/fragments/original-size-preflight.md)。用工具把选定完整源码写成工作脚本，在这个实际文件上替换数据、绑定和标签，再调整确有需要的布局；只加载本次相关模板与专题。
3. **检查**：将当前源码与保存的来源底稿比较，再按 [检查与修复](../../original/review-policy.md) 打开实际输出，核对模板特点、统计口径、文字、图例和裁切。源码差异是检查线索，不是视觉结论；必要适配不必为消除提示改回演示数据。修复后重看受影响图件，遵循该检查策略与用户限定的范围。

所选模板的具体实现决定默认视觉结构；通用技法用于解决实际问题。保留模板的字号层级、图层、填充、渐变、透明度、描边、标记与注释设计。新增组别或长标签可扩展画布、面板和必要间距，不能漏数据，也不为适配数据而整段重写绘图主体。选图阶段的新颖性目标不要求适配阶段重新设计。

## 运行与来源

首次运行先按执行环境确认 Python 3.10+ 及 [依赖](../../requirements.txt)，初始化本次工作区：

```text
python "<RES>/scripts/resolve_runtime.py"
python "<RES>/scripts/bootstrap.py" --workspace "<WORKSPACE>" --profile modeling-competition --capability paper-figure
```

后续在该工作区使用 `.vivid/runtime.json` 记录的运行环境。已有初始化和结果可复用；工具升级按执行环境刷新已知旧副本，保留用户改动。普通配方准备示例：

```text
python _utils/get_recipe.py --id empirical.prediction_ci --script figures/gen_fig_forecast.py
```

工具将完整源码及来源记录保存到工作区；在返回的工作文件上适配，不从预览或印象重写同类型图。运行方式、混合计划批量准备与底稿恢复见 [源码底稿与保真](../../template-fidelity.md)。保存可重跑脚本、输入来源和用户要求的实际图件；逐项确认本脚本的退出状态及预期输出，不能以其他图存在代替本图成功。

## 三套完整组合模板

- `template.sem_violin_pearson`：[小提琴＋Pearson](../../templates/sem-violin-pearson/TEMPLATE.md)。保留整套原版默认样式，按其数据接口适配。
- `template.shap_dependence`：[SHAP组合](../../templates/shap-composites/TEMPLATE.md)的特征重要性与响应模式。
- `template.shap_contribution`：同一 [SHAP组合](../../templates/shap-composites/TEMPLATE.md)的变量及类别贡献模式。

三套组合使用各自完整源码、输入口径和原 CLI，不拆成普通配方重拼，不作为无参数普通配方运行；SHAP 模式需要真实特征值及对应 SHAP 值。可由准备工具单独或随计划保存来源，具体命令见各模板及保真说明。

## 数据与显示默认值

- 绘图数值来自用户输入、模型结果或可追溯的真实计算。明确观测单位、分组/配对、单位、缺失处理及 SD/SE/CI 含义。替换全部演示数据和统计量；不补造样本、阈值、显著性、不确定性或三维结构来填满模板。某层没有证据时按统计含义移除或调整，并简述必要适配。
- 图内文字默认中文（`language: zh`），用户要求英文时设置 `language: en`，两种语言共用模板源码。覆盖标题、坐标轴、图例、文字刻度、色条与注释；显示名映射不改数据键，保留专业缩写、单位、公式和必要专名。
- 中英文共用 [默认字体策略](../../host-adapter.md)：普通无衬线图英文与数字优先 Arial、中文优先 MiSans，缺字按已安装字体回退。保留模板明确设计的衬线风格，以及用户指定字体、字号、字重和位置；不要统一抹平字号层级。使用共享保存函数，直接导出时按执行环境应用字体。
- 配色默认橄榄杏棕（`olive-apricot`），已有选择及用户自定义颜色优先，不增加配色确认环节。分类颜色、连续色阶与正负量配色按 [配色规则](../../color-selection.md) 读取当前项目配置；换色保留所选模板、字体尺寸与图层设计。

## 任务边界与按需加载

- 完整论文或整题图集先回到 [根入口](../../SKILL.md) 的完整图集规划，读取 [上游规划](../../original/upstream-planning.md) 和 [绘图入口](../../original/resources/ENTRYPOINT.md)，按 FIGURE_PLAN / FIGURE_MANIFEST 分类、执行并对账。本通道执行其中 DATA 项；混合图集的架构或技术图交给相应通道，不能用数据图替代或遗漏。单图及用户限定的小批数据图不启动整题规划。
- 请求实际是模型、系统或方案结构而非数值证据时，由 [根入口](../../SKILL.md) 转入架构图通道；数学几何推导及其他格式按绘图入口选择路线。只画数据图时不初始化这些路线。
- 特定统计、优化、网络或空间布局知识按需读取 `original/fragments/` 或 [知识索引](../../original/resources/assets/shared-scripts/figure_style_guide.md) 指向的专题；论文表格、图注和引用仅在相应任务加载。
- 按用户要求交付图件、可复现脚本与来源，简述必要适配和未解决问题。仅图件任务到此结束，不自动生成论文或附加格式。
