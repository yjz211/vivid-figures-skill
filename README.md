# Vivid Figures · 生动数据图

**从模板出发，把数据变成图表。既可以在本地网页中操作，也可以交给 AI 助手完成。**

面向论文、数学建模和实验报告，包含 **148 个模板（145 个图表配方 + 3 套完整组合）、7 套配色、模板知识卡、效果预览和完整绘图源码**。网页工作台与 Skill 使用同一套模板来源，保留模板的图层、渐变与透明效果。

[下载最新完整源码](https://github.com/yjz211/vivid-figures-skill/archive/refs/heads/main.zip) · [工作台说明](workbench/README.md) · [Skill 安装](docs/INSTALL.md) · [Skill 用法](docs/USAGE.md) · [更新记录](CHANGELOG.md)

> **仅限个人、非商业使用；未经书面许可，禁止二次开发及商业使用**。完整限制见 [LICENSE](LICENSE)。

## 选择使用方式

| | 本地绘图工作台 | AI 绘图 Skill |
|---|---|---|
| 适合 | 自己选模板、编辑数据、调整图形 | 用自然语言描述目标，让助手选图和适配数据 |
| 操作方式 | 浏览器中的图库、表格和图形编辑器 | 在支持文件读写、代码执行和看图的 AI 助手中使用 |
| 是否需要大模型 | 无需接入 | 需要可用的 AI 助手 |
| 入口 | [workbench/](workbench/README.md) | [SKILL.md](SKILL.md) |

## 本地绘图工作台

现已提供 [Agent 工作台](workbench/docs/AGENT-WORKBENCH.md)：使用已有模板进行对话绘图、图片检查、手动修改及版本恢复。复用 LangGraph、AG-UI 和原编辑器；可连接已登录的 Codex CLI 或兼容 API。手动导入数据、对应字段和出图无需模型。

像素风格的本地网页界面，图库统一使用**粉彩少女**预览。支持按类别、图名、别名、知识卡关键词和数据要求找图，查看效果后直接获取源码，或导入自己的数据绘图。

### 启动

下载并解压仓库，安装 **Python 3.11+**，在仓库目录运行：

```sh
cd workbench
python -m pip install -r requirements.txt
python -X utf8 scripts/manage.py serve --open
```

浏览器访问 <http://127.0.0.1:8766/index.html>。Windows 安装依赖后，也可双击 `workbench/启动工作台.cmd`；服务运行期间保留启动窗口。

仅浏览图库和下载原始模板包，可直接打开 `workbench/index.html`。编辑数据和生成新图需要本地 Python 服务。GitHub 提供源码下载，工作台在你自己的电脑上运行。

### 使用流程与功能

1. **选图**：搜索模板，查看预览、适用数据和字段要求；首页可切换中文 / English 模板预览。
2. **换数据**：导入 CSV、TSV、XLSX，或直接编辑表格；核对字段对应，按模板需要提供多张数据表。
3. **调图**：切换配色自动重绘，修改图形属性；Matplotlib 图支持对象点选和文字拖动，Plotly 三维图支持旋转与缩放。
4. **保存与导出**：保存本地项目，导出 PNG、PDF、SVG、CSV、源码或完整复现包。

表格支持排序、筛选、转置、长宽表转换、分组汇总和撤销重做。数据行列数量可按模板的数据要求调整；统计分析类模板需要对应的分析结果输入。具体操作与限制见 [工作台使用说明](workbench/使用说明.md)。

Plotly 静态导出需要 Chrome / Chromium，中文图表需要本机有中文字体。正常启动无需 Node.js；Node.js 用于部分维护检查。用户项目、样式和绘图任务保存在本机 `workbench/workspace/`，不随 Git 上传。

### 中英文图表与字体

首页与模板详情提供**模板语言**选择，默认中文并记住上次选择；缩略图、大图和原图同步切换。新建图表沿用所选语言，编辑器也可通过**图内语言**自动重绘；已有项目保留自己的语言设置。界面仍使用中文。

中英文共用同一套模板源码，保留数据、配色与图层。原始名称不直接改写，需要翻译的专名可通过显示名映射或点选文字修改。下载模板包后运行 `python run_demo.py --language en` 可生成英文示例。

默认字体为**中文 MiSans、英文与数字 Arial**，专门设计的衬线风格保留。图库、编辑器与源码导出使用同一字体策略；PDF 支持嵌入中文 TrueType 字体。需要与图库中文效果一致，请从 [MiSans 官方页面](https://hyperos.mi.com/font/zh/download/) 安装 TTF 格式的 Regular、Semibold、Bold；MiSans 和 Arial 字体文件不随仓库分发，缺少时使用可用字体回退。

148 个模板均已重新生成中英文预览，每种语言 150 张图。完整验证范围见[语言与字体验证报告](workbench/docs/LANGUAGE-REPORT.md)，操作说明见[工作台图内语言](workbench/README.md#图内语言)。

## AI 绘图 Skill

采用 [Agent Skills 开放规范](https://agentskills.io/specification)，根目录 `SKILL.md` 为入口，指导和资源按需加载。开放格式指宿主接口，使用许可仍以 [LICENSE](LICENSE) 为准。

| 你手上的材料 | 可以让 AI 做的事 |
|---|---|
| Excel、CSV、JSON 数据 | 理解字段，根据表达目的选图并适配模板 |
| 实验结果、模型对比 | 画性能对比、误差分布、收敛曲线、置信区间等 |
| 空间坐标、曲面或工程数据 | 画三维曲面、轨迹、地图或工程图 |
| 方法说明、步骤和关系 | 画流程图、技术路线图、精确几何图 |
| 已有图和绘图源码 | 调整颜色、文字、间距或布局，保留模板设计 |

无需先知道图表叫什么，可以直接说“比较这几种方法的结果，选能看清差异的图”。AI 先理解数据与表达目的，再查说明卡、查看候选实图，最后读取完整配方。

内置 [148 张模板说明卡与预览](catalog/index.html)，包括环形分组对比柱状图、三维分组渐变柱状图、多 Y 轴渐变直方图、立体方块相关性热图、雷达山脊融合图，以及 SEM 和两套 SHAP 组合模板。下载后可在浏览器打开图文目录。

新增的[环形分组对比柱状图](catalog/cards/advanced.grouped_radial_bar.md)按参考图复刻空心中心、任务内多系列、组间留白、两层外围标签和大类弧线，图库使用白底与粉彩少女配色。每个任务按组内最小值与最大值独立缩放，**柱长仅可在同一任务内比较**；标签保留原始数值。

## 七套配色

点击图片查看高清示意。每张包含散点簇、小提琴分布、层叠山脊与堆叠色块，展示浅填充、轮廓和透明叠加效果。全部为模拟数据，展示图是配方适配示例；实际绘图仍读取当前完整配方和保真要点。

| 珊瑚青绿 · 7色 | 橄榄杏棕 · 7色 | 蓝粉浅彩 · 5色 |
|:---:|:---:|:---:|
| [![珊瑚青绿配色示意](docs/images/palettes/coral-teal.png)](docs/images/palettes/coral-teal.png) | [![橄榄杏棕配色示意](docs/images/palettes/olive-apricot.png)](docs/images/palettes/olive-apricot.png) | [![蓝粉浅彩配色示意](docs/images/palettes/blue-pink.png)](docs/images/palettes/blue-pink.png) |

| 蓝天绿地 · 8色 | 柔绿森林 · 8色 |
|:---:|:---:|
| [![蓝天绿地配色示意](docs/images/palettes/blue-sky.png)](docs/images/palettes/blue-sky.png) | [![柔绿森林配色示意](docs/images/palettes/soft-forest.png)](docs/images/palettes/soft-forest.png) |

| 粉彩少女 · 8色 | 海洋清风 · 8色 |
|:---:|:---:|
| [![粉彩少女配色示意](docs/images/palettes/pastel-girl.png)](docs/images/palettes/pastel-girl.png) | [![海洋清风配色示意](docs/images/palettes/ocean-breeze.png)](docs/images/palettes/ocean-breeze.png) |

[完整色值](original/resources/assets/shared-scripts/palettes.json) · [高清 PNG / SVG / PDF 与生成源码](examples/palette-posters/README.md)

Skill 未指定配色时默认使用**橄榄杏棕**；工作台图库展示的是**粉彩少女**。七套配色都可用于绘图，也支持自定义颜色。同一任务中的补图和修图沿用已选配色。

配色统一维护于同一份 JSON，分类取色与连续色阶分别使用对应顺序。配色示意使用模拟数据，部分热图的配色视觉效果仍待细调。

## 安装后，直接这样说

在助手中加载整个 Skill 文件夹后，直接说明要使用 `vivid-figures-skill`：

```text
用 vivid-figures-skill 读取 results.csv，比较不同方法的得分分布。
用珊瑚青绿配色。图型你来选，输出 PNG、PDF 和绘图源码。
```

```text
用 vivid-figures-skill 给这份实验结果画一组论文配图。
用珊瑚青绿配色。保留模板的渐变和层次，不要随意简化。
```

```text
继续修改刚才的图：图例移到上方，字号稍微加大。
沿用已经选好的风格和配色，保留其他设计。
```

AI 会读取数据、选择配方、执行绘图、查看生成结果并按需修复。通常在你的任务目录下生成 `figures/`；PNG 方便预览，PDF 方便排版，源码用于复现和继续修改。[更多用法](docs/USAGE.md)。

## 使用 Skill 需要准备什么

- **AI 助手**：能读写文件、运行代码、查看图片；按客户端规则加载整个 Skill 文件夹。
- **Python 3.10+**：安装仓库根目录的 Python 依赖；工作台另需 Python 3.11+ 和其自身依赖。
- **按需工具**：Git 用于克隆更新，Bash 用于随附检查脚本；完整图集规划建议 Node.js 22.6+。
- **可选绘图能力**：Draw.io、TikZ、HTML、Mermaid 和 AI 场景插图各有对应工具，详见安装指南。

第一次使用请按 [安装指南](docs/INSTALL.md) 配置。普通数据图无需额外配置图像生成 API Key；AI 助手自身的账户或模型连接需可用。宿主接口见 [host-adapter.md](host-adapter.md)。图中文字默认中文，可按要求用同一模板生成英文图；工作台提供“图内语言”切换，详见[英文图表](docs/USAGE.md#英文图表)。

## 模板会被 AI 简化吗

Skill 明确要求先读取完整配方，以配方代码为起点适配数据。模板的渐变、透明度层次和关键图形元素应保留，不能为了省代码而随意改成纯色或只留轮廓。修图优先调整位置、间距和尺寸。

每张说明卡列出带源码行号的保留重点和允许适配范围。源码工具直接生成完整工作脚本、原始底稿与来源记录，恢复时保留已有修改；统一检查会提示图层、画布、字体和注释框等实际差异。指导按选择、适配和检查加载，必要的数据及布局调整仍然允许。最终对照实图判断，不靠“脚本没报错”认定保真。见 [源码底稿与保真要点](template-fidelity.md)。

这些是给模型的执行要求，实际效果仍取决于模型是否遵循指导；示例不是每次出图效果的保证。数据不支持某种元素时，AI 应说明调整原因。例如，没有重复试验或区间数据，就不能凭空补一条置信带。

## 最近更新

- **2026-10-16 · 双语图库与图表字体**：首页与编辑器支持中英文切换；148 个模板提供双语预览，下载包支持英文运行。中文默认 MiSans、英文与数字默认 Arial，统一图库与导出的字体；修复图例重排列后偏移，保留手动文字、字号和拖动位置。详见[本次更新记录](CHANGELOG.md)。
- **2026-10-16 · 环形分组图与 Agent 工作台**：新增模板 148，参考图结构复刻、白底粉彩少女预览、完整源码与知识卡；一并发布 Agent 对话绘图、直接字段绑定、版本恢复及出图与交互修正。共 145 个配方和 3 套完整组合。
- **2026-10-14 · 工作台发布**：147 个可编辑模板、7 套配色、数据导入与整理、字段对应、对象编辑和文字拖动、本地项目保存及完整源码导出。包含近期交互与资源路径修复。
- **2026-09-19 · 雷达山脊融合图**：新增[完整模板与知识卡](catalog/cards/advanced.radar_ridgeline.md)，当前共 144 个配方、3 套完整组合模板。
- **2026-09-17 · 源码适配与检查**：从完整模板源码开始改，保留原始底稿和来源记录；增加图层、标签、色带及注释变化提示，修正预测图残差刻度。

[下载当前 main 分支完整源码](https://github.com/yjz211/vivid-figures-skill/archive/refs/heads/main.zip)，包含最新 Skill 和工作台。

[2026-09-15 历史发布包及粉彩少女图集](https://github.com/yjz211/vivid-figures-skill/releases/tag/v2026.09.15)包含当时的 143 张高清单图和 16 张 3×3 九宫格，**不包含后续新增模板和工作台**。

[完整更新记录](CHANGELOG.md) · [仓库文件说明](docs/USAGE.md#仓库里的文件分别做什么) · [工作台维护说明](workbench/docs/MAINTENANCE.md)

## 使用限制

仅限个人、非商业使用。未经版权所有者事先书面许可，禁止修改、改编、二次开发、制作衍生作品、再分发、转售、提供付费服务或用于其他商业用途。第三方组件及材料仍遵循各自的许可证和声明。完整条款见 [LICENSE](LICENSE)。
