# 完整图集上游规划

适用于完整论文/整题图集的新规划；明确只画一张图或修已接受图片，不重启整套。在整理证据时预规划，执行前补齐和验证。按 review-policy.md 的 figures → writing → review 顺序执行。

新整套先运行 `node --experimental-strip-types "<SKILL>/scripts/figure-plan-cli.mjs" begin --workspace "<WORKSPACE>"`。读取题目、逐问建模、机器结果、验证和证据，先规划后绘制。读 resources/assets/shared-scripts/figure_exemplars.md 的方法套餐及 resources/assets/shared-scripts/figure_selection_reference.md 的数据形态决策表。以真实分析步骤推导图集，不从旧图片倒推，也不复用固定六图清单。

按问题分 reasoning/data/mixed，写每图一句核心信息、具体图型、来源编号、理由、源文件和章节。`recipe` 字段使用普通配方的 `recipe:basic.line`、完整组合的 `template.shap_dependence` 等原始 ID，SVG 架构资产使用 `asset:VA-001`；库外才填 `custom` 并说明理由。先选完整图集，再批量准备普通配方与完整组合，逐图适配；架构资产走独立架构路线。

## 原版约束与适用前提
- DATA 硬底线8张；18–30是整题数据图软参考，不是每问指标，不凑数。用户明确指定更高下限才传 minimum。PNG/PDF同图只计一次，多面板一个figure只计一张。流程/推导图另算。原版按文件扩展名计数可能重复，这里按唯一图id计数。
- 同类图可重复以支持一致比较，不设图型次数配额；每张明确具体类型，不能只写“对比图”。融合图说明同一坐标系中各图层的含义；多面板组合图说明各面板贡献，不能把无关信息拼起来。
- 完整图集含一张 `purpose="roadmap"` 的总技术路线图，名称按语义确定。模型/系统/方案架构默认用 `ARCHITECTURE`（SVG 资产），其他确定性技术图按场景用 DRAWIO/TIKZ；用户明确选定 HTML、Mermaid 或其他已支持格式时遵从该选择，不另加一张 Draw.io 路线图。空间数据应有空间证据图；多个模型比较应按真实指标与不确定性安排互补证据，不为凑图型种类重做已有表达。
- 每个推理密集问题必须有忠实求解过程的 TIKZ 推导构造图；混合题按真实推导需要安排。不能用泛泛示意代替推导，也不能为数据图数量省掉验证、关键结果或灵敏度表达；缺少相关真实结果则在规划解释，不能捏造。
- 推理密集问题的数据图达到硬底线即可，不为18–30硬加重复曲线。图注/正文承载长说明，图内只留必要短标注。
- 默认沿用原版按数据形态选图。统一鼓励：先比较两种合理表达，积极考虑新颖单图及同一坐标系内多图层融合，同时保留对有信息增益的多面板组合的鼓励；不默认多面板优先，不以子图数量衡量新颖，不设融合或组合配额。融合图最终为一套坐标轴，层间共享坐标语义；明亮、舒适、前景与背景层次清楚。不得因此虚构区间、分布或可行域。

## 空间图：二维、三维与工程表达
空间图是由真实空间坐标、位置关系或物理几何结构支撑结论的图，不限于二维分布图、地图、热力图或等高线。逐问主动识别地形/深度/高度、三维轨迹、曲面、实体结构、空间覆盖、受力/场分布、装置布局与工程几何关系，并据此标记 questions[].spatial；不要因未使用 GIS 而漏标。
在保留必要二维定位、分布和剖面证据的基础上，积极规划三维空间图与工程类图像：例如三维地形叠加测线/覆盖面、真实空间轨迹与设备布局、结构或装置轴测图、剖切/分解图、计算网格与真实场量、空间包络或几何约束构造。空间表达可以更积极：有真实三维或工程语义时，优先评估至少一种三维/工程方案，合理采用透视、曲面、透明分层、剖切和同坐标系融合，不能惯性全部退回二维分布图。使用项目配色、清晰标注与透明层次。
三维维度、比例、单位与几何关系须来自已有数据或模型；禁止为视觉效果捏造高度、场量或结构。选择可读视角并处理遮挡，必要时辅以二维投影/剖面。数据驱动的工程/空间结果可计 DATA；纯原理/推导示意仍按 DRAWIO/TIKZ 分类，不计入8张数据图。规划 reason 写明三维或工程表达的信息收益、sources 和实际空间语义，符合条件的 DATA 图标记 spatial=true。无需强制三维数量配额，数据确无三维/工程语义时说明并使用二维证据。

## 唯一机器规划：FIGURE_PLAN.json
示例仅展示字段，不是本题的图型或数量模板：
```json
{"questions":[{"id":"q1","kind":"mixed","spatial":false,"modelCount":1}],"figures":[{"id":"fig_example","class":"DATA","question":"q1","chartType":"分组柱状图","recipe":"recipe:basic.grouped_bar","reason":"实际分组值比较","message":"需要表达的核心信息","section":"问题一结果","sources":["work/q1_results.json"],"layout":"single","finalWidthMm":136,"outputs":["figures/fig_example.pdf","figures/fig_example.png"]}]}
```
完整计划必须满足上述数量与触发规则。路线图加 `purpose="roadmap"`，允许 ARCHITECTURE/DRAWIO/TIKZ/HTML/MERMAID；推导图加 `purpose="derivation"`；空间数据图加 `spatial=true`。每个问题都要被图集覆盖；跨问图用 `question="all"`，不能代替每问覆盖。

执行时按每图类别加载 [数据图子 Skill](../channels/vivid-figure-skill/SKILL.md) 或 [架构图子 Skill](../channels/vivid-architecture-diagram-skill/SKILL.md)，不把两条通道的制作规则一并交给单图生成任务。

`ARCHITECTURE` 按架构通道引用的 [SVG 架构工作流](../architecture/WORKFLOW.md) 生成候选、等待真实选择，再交付所选版本。默认在 `outputs` 登记 `figures/<id>/final/fig.pptx`、`figures/<id>/final/fig.svg`、`figures/<id>/final/fig.pdf`；最终目录可自定，用户明确限定格式时按其要求登记。A/B 候选不算两张计划图；尚待选择时保持该项待完成，不抢先导出两套 PPT 或代用户选优。已有作品或已选版本沿用原流程的单版本修改规则。

写好后运行 `node --experimental-strip-types "<SKILL>/scripts/figure-plan-cli.mjs" validate --workspace "<WORKSPACE>" --plan FIGURE_PLAN.json`。失败只改规划；通过后按 router-contract 派生 PAPER_PLAN.md 中的锚定 FIGURE_MANIFEST，保留每项名称、类别、purpose 与输出格式。HTML/MERMAID 归入 OPTIONAL 节，并用 `renderer=HTML` 或 `renderer=MERMAID` 保留原类别，`format` 只列实际交付格式；用户只要求 PDF/PNG 时不强加原生文件。随后执行分类验证、bootstrap、源码准备、绘图。JSON是主合同，不允许另写不同图集。改JSON后需再次验证。该工具仅验证结构/数量/源文件存在，不声称验证了设计质量或科学真实性。

绘图后按JSON清点每项输出，不能漏项。用户要求只出一轮时，只解决首次导出前的运行错误，成功图不重绘，不做出图后审计，不进入论文撰写。
