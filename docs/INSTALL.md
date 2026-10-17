# 安装 Vivid Illustration Skill

[返回首页](../README.md)

本页介绍 AI Skill 的安装。只使用本地网页绘图，请直接按 [工作台启动说明](../workbench/README.md#开始使用) 操作，无需配置 AI 助手。

安装分两步：先把完整包放到 AI 助手能找到的位置，再给它准备可用的 Python 环境。本仓库采用 [Agent Skills 开放格式](https://agentskills.io/specification)：根目录的 `SKILL.md` 是轻量总入口，`channels/vivid-figure-skill/SKILL.md` 与 `channels/vivid-architecture-diagram-skill/SKILL.md` 分别是数据图和架构图子入口。下面先下载到普通目录，再由你使用的助手导入或配置 Skill 搜索路径。开放格式不规定统一的安装目录，也不保证自动发现这些子目录。

## 完整资源包

仓库完整包包含196套统一采用 SVG 底稿的架构资产及可编辑PPT工具。安装和迁移时保留整个 `architecture/`（包括 `source-assets/`、`source-variants/`、字体和目录）、`scripts/pptx_runtime/`、`requirements-architecture.txt` 和已有数据图资源。VA-001–004 的原 Python 生成器仅为旧项目兼容保留，新任务从目录准备 SVG 版本。

两个绘图通道随**同一个完整仓库包**安装，须同时保留根 `SKILL.md` 和 `channels/`。不要把 `channels/vivid-figure-skill/` 或 `channels/vivid-architecture-diagram-skill/` 单独复制成安装包：它们继续引用包根目录下的模板、资产和脚本。所有文档中的 `<SKILL>` 都指整个 `vivid-illustration-skill` 根目录，不随当前读取的通道改变。

只使用架构/PPT能力时可运行 `python -m pip install -r requirements-architecture.txt`，再运行 `python -m playwright install chromium`。Windows上的Office验证额外需要已安装Microsoft PowerPoint；普通原生PPT生成不依赖Office。字体和跨机限制见 [PPTX说明](../architecture/PPTX.md)。

架构双候选流程还需保留 `architecture/WORKFLOW.md`、`architecture/COMMON.md`、`architecture/paths/` 和 `scripts/compare_architecture_candidates.py`；只复制入口会导致路径规则或对照工具缺失。

安装版附带离线演示工作台；完整源码版附带网页服务与数据图Agent。更新时不要覆盖 `workbench/workspace/` 中的用户项目与会话，也不要复制模型凭据或虚拟环境。

## 1. 准备基础软件

| 软件 | 用途 | 要求 |
|---|---|---|
| 能加载 Agent Skills 的 AI 助手 | 读数据、执行绘图代码、看图与修图 | 需要文件、终端执行和图像读取能力 |
| Python | 运行数据分析和绘图代码 | 3.10+ |
| Git | 下载与更新本仓库 | 使用下方克隆和更新命令时需要 |
| Bash | 运行随附的图表检查脚本 | Windows 推荐 Git for Windows 的 Git Bash；macOS/Linux 通常已有 |
| Node.js | 运行完整图集的规划校验工具 | 建议 22.6+；普通 Matplotlib 绘图不依赖它 |

安装 Python 后，先在终端确认 `python --version`（macOS/Linux 可用 `python3 --version`）能正常显示版本。

## 2. 下载并安装 Python 依赖

下面使用独立虚拟环境，避免与其他项目的 Python 依赖混在一起。命令中的安装目录有空格也可以使用。

### Windows：PowerShell

```powershell
git clone https://github.com/yjz211/vivid-illustration-skill.git "$env:USERPROFILE/agent-skills/vivid-illustration-skill"
python -m venv "$env:USERPROFILE/agent-skills/vivid-illustration-skill/.venv"
& "$env:USERPROFILE/agent-skills/vivid-illustration-skill/.venv/Scripts/python.exe" -m pip install --upgrade pip
& "$env:USERPROFILE/agent-skills/vivid-illustration-skill/.venv/Scripts/python.exe" -m pip install -r "$env:USERPROFILE/agent-skills/vivid-illustration-skill/requirements.txt"
```

这些命令直接调用虚拟环境中的 Python，不需要运行激活脚本。

### macOS / Linux：终端

```bash
git clone https://github.com/yjz211/vivid-illustration-skill.git "$HOME/agent-skills/vivid-illustration-skill"
python3 -m venv "$HOME/agent-skills/vivid-illustration-skill/.venv"
"$HOME/agent-skills/vivid-illustration-skill/.venv/bin/python" -m pip install --upgrade pip
"$HOME/agent-skills/vivid-illustration-skill/.venv/bin/python" -m pip install -r "$HOME/agent-skills/vivid-illustration-skill/requirements.txt"
```

部分 Linux 发行版需要先通过系统包管理器安装 `python3-venv`，才能创建虚拟环境。中文图表需要本机有中文字体；Linux 可安装 Noto Sans CJK，Windows 和 macOS 通常已有可用字体。

`requirements.txt` 包含数据分析、绘图、PDF 预览和空间图表所用的依赖，包括 NumPy、pandas、SciPy、Matplotlib、Seaborn、scikit-learn、Pillow、PyMuPDF 和 GeoPandas 等。第一次完整安装可能需要一些时间。

### 让助手加载 Skill

下载后，在助手的 Skill 管理功能中导入 `vivid-illustration-skill` 文件夹，或将它放到该助手文档指定的个人级/项目级 Skill 目录。

- 导入整个文件夹，保留 `channels/`、`original/`、`catalog/`、`templates/`、`architecture/`、`scripts/` 等相对路径；不要只上传某个 `SKILL.md` 或通道子目录。
- 若助手能读取文件和执行代码，但不支持自动发现 Skill，可明确让它读取安装目录下的根 `SKILL.md`，或按下方写法直接读取所需子入口。
- 文件夹内应直接包含 `SKILL.md`。自动发现和调用语法由具体助手决定，不是所有客户端都使用斜杠命令。

### 选择总入口或直接读取通道

| 任务 | 让助手读取的文件 | 入口名称 |
|---|---|---|
| 尚未确定图型、完整论文或同时包含数据图与架构图 | `<SKILL>/SKILL.md` | **Vivid Illustration Skill**<br>`vivid-illustration-skill` |
| 明确的数据图与完整组合模板任务 | `<SKILL>/channels/vivid-figure-skill/SKILL.md` | **Vivid Figure Skill**<br>`vivid-figure-skill` |
| 明确的架构图、部件改造、可编辑 PPTX 或指定技术图路线 | `<SKILL>/channels/vivid-architecture-diagram-skill/SKILL.md` | **Vivid Architecture Diagram Skill**<br>`vivid-architecture-diagram-skill` |

例如，已经把完整包安装到 `D:/agent-skills/vivid-illustration-skill` 时，可以直接对助手说：

```text
读取 D:/agent-skills/vivid-illustration-skill/channels/vivid-figure-skill/SKILL.md，
按 vivid-figure-skill 处理当前项目的 results.csv。
资源根 <SKILL> 是 D:/agent-skills/vivid-illustration-skill。
```

架构任务改为读取 `channels/vivid-architecture-diagram-skill/SKILL.md`，使用 `vivid-architecture-diagram-skill`；其他系统使用各自的实际绝对路径。子入口名称不等于通用可用的调用命令；如果宿主没有注册该名称，直接读文件即可。

数据图任务只加载数据图规则，架构图任务只加载架构图规则；不为进入一个通道而读取另一个通道。整题混合任务先从总入口规划并分派，各图件在自己的通道中执行。两通道共享的配色文件、模板工具等仍按具体任务需要读取。

## 3. 让 AI 使用正确的 Python

重新打开或刷新你使用的 AI 助手，在放有数据的项目里输入：

```text
使用 vivid-illustration-skill 绘图。
Python 请使用这个 Skill 安装目录下的 .venv 环境。
先检查环境，然后读取我的数据文件。
```

这样可以避免“依赖装好了，AI 却调用另一个 Python”的问题。你也可以提供完整解释器路径。

如果没有识别到 Skill，确认安装文件夹内直接有 `SKILL.md`，而不是多套了一层同名文件夹。支持斜杠调用时可输入 `/vivid-illustration-skill`。

## 4. 按要画的图安装可选工具

| 要画什么 | 额外需要什么 | 备注 |
|---|---|---|
| 流程图、技术路线图、可编辑框图 | draw.io Desktop | 导出 Draw.io 图件时使用 |
| 带公式的精确几何图、TikZ 技术图 | TeX Live 或 MiKTeX，含 XeLaTeX 及中文支持 | 终端需能运行 `xelatex` |
| HTML 图和网页截图 | Chrome 或 Chromium + Python Playwright（已列入依赖） | 未找到时可指定 `CHROME_PATH` 或 `PUPPETEER_EXECUTABLE_PATH` |
| Mermaid 图 | Node.js 与 Mermaid CLI | 安装命令见下方 |
| PDF 转图片的备用方式 | Poppler | 已有 PyMuPDF 时通常不需要 |
| AI 生成的科学场景插图 | 助手提供的图像生成工具，或已配置的图像生成 MCP | 本 Skill 不附送图像生成服务；普通数据图不依赖它 |

Mermaid CLI 安装：

```bash
npm install -g @mermaid-js/mermaid-cli
```

draw.io 路径无法自动找到时，可设置 `DRAWIO_PATH`。Mac 上的应用也可能需要手动指定可执行文件路径。

## 检查与常见问题

让 AI 使用上述虚拟环境，在 Skill 安装目录运行：

```bash
python original/resources/scripts/resolve_runtime.py
```

这里的 `python` 指已选定的虚拟环境解释器。脚本会列出 Python 和可选工具路径，**不会验证所有 Python 包是否已安装**；暂时不用的可选工具显示空值无需处理。

| 遇到的问题 | 处理方法 |
|---|---|
| 根 Skill 可用，但找不到某个通道名称 | 不依赖子目录自动发现；明确提供对应 `channels/.../SKILL.md` 的绝对路径 |
| 直接读取子入口后找不到模板或脚本 | `<SKILL>` 应指完整包根目录；确认没有仅复制 `channels/` 子目录 |
| `ModuleNotFoundError` | 确认 AI 的 Python 与安装依赖的 Python 是同一个 |
| 中文显示成方框 | 安装中文字体后重新启动绘图进程 |
| 找不到 `bash` | Windows 安装 Git for Windows，并让 AI 使用 Git Bash 的可执行文件 |
| 找不到 `xelatex`、draw.io 或 Chrome | 安装当前图型需要的工具，或提供实际路径 |
| 没有图像生成能力 | 仅影响 AI 场景插图；数据图可继续用 Python 绘制 |

## 更新到最新版本

进入 Skill 安装目录后执行：

```bash
git pull --ff-only
```

如果更新记录提到依赖有变化，再使用同一个虚拟环境执行 `python -m pip install -r requirements.txt`。重新打开 AI 会话，以加载新的 Skill 指导。
