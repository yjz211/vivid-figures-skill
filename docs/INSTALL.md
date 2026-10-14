# 安装 Vivid Figures

[返回首页](../README.md)

本页介绍 AI Skill 的安装。只使用本地网页绘图，请直接按 [工作台启动说明](../workbench/README.md#开始使用) 操作，无需配置 AI 助手。

安装分两步：先把 Skill 放到 AI 助手能找到的位置，再给它准备可用的 Python 环境。本仓库采用 [Agent Skills 开放格式](https://agentskills.io/specification)：整个文件夹是一个 Skill，根目录的 `SKILL.md` 是入口。下面先下载到普通目录，再由你使用的助手导入或配置 Skill 搜索路径。开放格式不规定统一的安装目录。

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
git clone https://github.com/yjz211/vivid-figures-skill.git "$env:USERPROFILE/agent-skills/vivid-figures-skill"
python -m venv "$env:USERPROFILE/agent-skills/vivid-figures-skill/.venv"
& "$env:USERPROFILE/agent-skills/vivid-figures-skill/.venv/Scripts/python.exe" -m pip install --upgrade pip
& "$env:USERPROFILE/agent-skills/vivid-figures-skill/.venv/Scripts/python.exe" -m pip install -r "$env:USERPROFILE/agent-skills/vivid-figures-skill/requirements.txt"
```

这些命令直接调用虚拟环境中的 Python，不需要运行激活脚本。

### macOS / Linux：终端

```bash
git clone https://github.com/yjz211/vivid-figures-skill.git "$HOME/agent-skills/vivid-figures-skill"
python3 -m venv "$HOME/agent-skills/vivid-figures-skill/.venv"
"$HOME/agent-skills/vivid-figures-skill/.venv/bin/python" -m pip install --upgrade pip
"$HOME/agent-skills/vivid-figures-skill/.venv/bin/python" -m pip install -r "$HOME/agent-skills/vivid-figures-skill/requirements.txt"
```

部分 Linux 发行版需要先通过系统包管理器安装 `python3-venv`，才能创建虚拟环境。中文图表需要本机有中文字体；Linux 可安装 Noto Sans CJK，Windows 和 macOS 通常已有可用字体。

`requirements.txt` 包含数据分析、绘图、PDF 预览和空间图表所用的依赖，包括 NumPy、pandas、SciPy、Matplotlib、Seaborn、scikit-learn、Pillow、PyMuPDF 和 GeoPandas 等。第一次完整安装可能需要一些时间。

### 让助手加载 Skill

下载后，在助手的 Skill 管理功能中导入 `vivid-figures-skill` 文件夹，或将它放到该助手文档指定的个人级/项目级 Skill 目录。

- 导入整个文件夹，保留 `original/`、`catalog/`、`templates/` 等相对路径；不要只上传 `SKILL.md`。
- 若助手能读取文件和执行代码，但不支持自动发现 Skill，可明确让它读取安装目录下的 `SKILL.md` 并按其中引用加载资源。
- 文件夹内应直接包含 `SKILL.md`。自动发现和调用语法由具体助手决定，不是所有客户端都使用斜杠命令。

## 3. 让 AI 使用正确的 Python

重新打开或刷新你使用的 AI 助手，在放有数据的项目里输入：

```text
使用 vivid-figures-skill 绘图。
Python 请使用这个 Skill 安装目录下的 .venv 环境。
先检查环境，然后读取我的数据文件。
```

这样可以避免“依赖装好了，AI 却调用另一个 Python”的问题。你也可以提供完整解释器路径。

如果没有识别到 Skill，确认安装文件夹内直接有 `SKILL.md`，而不是多套了一层同名文件夹。支持斜杠调用时可输入 `/vivid-figures-skill`。

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
