# Paper Technical Diagram — Draw.io/TikZ (Non-Data Diagram Engine)

Generate deterministic technical, engineering, physical, geometric, architecture, process, and network diagrams with Draw.io or TikZ for: 用户提供的数据与绘图要求

This is a **lightweight sub-step** split from paper-figure. It ONLY handles non-data diagrams (DrawIO + TikZ). Data figures (matplotlib/seaborn) were already generated in the previous paper-figure step.

Execute only the DRAWIO/TIKZ entries selected in the current figure plan or explicitly requested by the user. SVG architecture assets use the separate architecture workflow; an ARCHITECTURE, HTML or MERMAID roadmap already satisfies the planned roadmap role. Do not add another Draw.io roadmap, change its renderer, or infer extra figures from a document filename. If this route has no requested entries, skip it.

## ⚡ 快速模式检测（开头先跑）

```bash
FAST_MODE=0
[ "$(python _utils/vivid_config.py get fast_mode)" = "1" ] && FAST_MODE=1
echo "FAST_MODE=$FAST_MODE"
```

**若 `FAST_MODE=1`（速度优先）：** 仍必须按图表清单产出所有架构/流程图（一张不漏、能导出成 PNG/PDF）。快速模式会**跳过 vision 多轮视觉自检修复循环**（原本最多 3 轮）以省 API——但⛔**跳过由 Step 5.7 / 7.5 的块内代码自动完成，不是让你整块不执行**：这两个块任何模式都要照常跑（块内会 detect FAST_MODE 决定跳不跳，且负责清空标记文件、执行几何/结构自检）。**若 `FAST_MODE=0`（默认）：** 视觉自检修复循环照常执行。

## Constants

- **FIG_DIR = `figures/`**
- **CUSTOM_REQUIREMENTS** — User-specified requirements, highest priority.

## ⛔⛔⛔ Output Contract (highest priority)

**Must produce at least 1 `figures/*.drawio` or `figures/tikz_*.tex` and corresponding PDF, plus updated `figures/latex_includes.tex`**.

⛔ **特殊豁免**：如果 PAPER_PLAN.md 明确无架构图/流程图需求（纯文字论文/数据分析报告），允许跳过此 skill 的产物要求；但仍要保留已有的 `figures/latex_includes.tex` 不破坏。

⛔ **MUST run output verification before ending**:
```bash
PASS=true
mkdir -p figures
PDF_COUNT=$(ls figures/*.pdf 2>/dev/null | wc -l)
DRAWIO_COUNT=$(ls figures/*.drawio 2>/dev/null | wc -l)
TIKZ_COUNT=$(ls figures/tikz_*.tex 2>/dev/null | wc -l)
PLAN_NEEDS_DIAGRAM=$(grep -iE 'drawio|tikz|架构图|流程图|fig_arch|fig_flow|fig_roadmap|fig_er' PAPER_PLAN.md 2>/dev/null | wc -l)

# ⛔ 优先按 FIGURE_MANIFEST 对账: 规划的每张 drawio/tikz 必须产出
PLAN_FILE=""
for f in PROBLEM_ANALYSIS.md PAPER_PLAN.md MODELING_REPORT.md; do
  [ -f "$f" ] && grep -q '<!-- BEGIN FIGURE_MANIFEST -->' "$f" && { PLAN_FILE="$f"; break; }
done

if [ -n "$PLAN_FILE" ]; then
    START=$(grep -n '<!-- BEGIN FIGURE_MANIFEST -->' "$PLAN_FILE" | head -1 | cut -d: -f1)
    END=$(grep -n '<!-- END FIGURE_MANIFEST -->' "$PLAN_FILE" | head -1 | cut -d: -f1)
    MANI=$(sed -n "${START},${END}p" "$PLAN_FILE")
    # ⛔ 按 manifest「流程/架构图章节」标题抓该章节下的全部图名(权威), 不靠文件名前缀白名单。
    #    旧白名单法要求关键词紧跟 fig_(如 fig_pipeline), 会漏掉 fig_data_pipeline/fig_model_arch
    #    这类「关键词在中间」的架构图 → 少画也不报错。按章节抓则一张不漏。
    #    ⛔ 关键词认 html|drawio 双向: 规划文档标题可能写「HTML 流程/架构图」或「DrawIO 流程/架构图」
    #    (取决于用户选的引擎), 与 paper-figure-html 的对账口径对称, 保证任一写法都不漏图。
    EXPECTED_DRAWIO=$(printf '%s\n' "$MANI" | awk '
        /^[[:space:]]*\*\*/ { cap = (tolower($0) ~ /html|drawio/) ? 1 : 0; next }
        cap && match($0, /^[[:space:]]*-[[:space:]]+fig_[a-zA-Z0-9_]+/) {
            s=substr($0, RSTART, RLENGTH); sub(/^[[:space:]]*-[[:space:]]*/, "", s); print s
        }')
    # TikZ 章节(manifest 标注 paper-figure 产出, 但本步骤也兜底对账, 双保险不漏)
    EXPECTED_TIKZ=$(printf '%s\n' "$MANI" | awk '
        /^[[:space:]]*\*\*/ { cap = (tolower($0) ~ /tikz/) ? 1 : 0; next }
        cap && match($0, /^[[:space:]]*-[[:space:]]+tikz_[a-zA-Z0-9_]+/) {
            s=substr($0, RSTART, RLENGTH); sub(/^[[:space:]]*-[[:space:]]*/, "", s); print s
        }')
    drawio_missing=0
    for name in $EXPECTED_DRAWIO; do
        ls figures/${name}.drawio figures/${name}.pdf figures/${name}.png 2>/dev/null | head -1 | grep -q . || { echo "❌ MANIFEST drawio: $name missing"; drawio_missing=$((drawio_missing+1)); }
    done
    tikz_missing=0
    for name in $EXPECTED_TIKZ; do
        ls figures/${name}.pdf figures/${name}.tex 2>/dev/null | head -1 | grep -q . || { echo "❌ MANIFEST tikz: $name missing"; tikz_missing=$((tikz_missing+1)); }
    done
    if [ $drawio_missing -gt 0 ] || [ $tikz_missing -gt 0 ]; then
        echo "⛔ FIGURE_MANIFEST drawio/tikz audit failed (drawio: $drawio_missing, tikz: $tikz_missing missing)"
        PASS=false
    else
        echo "✅ FIGURE_MANIFEST drawio/tikz 全部产出"
    fi
elif [ "$PDF_COUNT" -ge 1 ] || [ "$DRAWIO_COUNT" -ge 1 ] || [ "$TIKZ_COUNT" -ge 1 ]; then
    echo "✅ diagrams: PDF=$PDF_COUNT drawio=$DRAWIO_COUNT tikz=$TIKZ_COUNT"
elif [ "$PLAN_NEEDS_DIAGRAM" -eq 0 ]; then
    echo "✓ 规划无架构图/流程图需求, 跳过"
else
    echo "❌ 规划要求架构图/流程图但未生成"
    PASS=false
fi
[ -f figures/latex_includes.tex ] || touch figures/latex_includes.tex
[ "$PASS" != true ] && echo "⛔ Output verification FAILED — must complete before ending"
```

## Workflow

### Step 0: 恢复检查（断线重跑必读）

⛔ **本步骤可能因为断线/手动重跑被多次启动**。每次启动前**必须**先扫描已有产物：

```bash
echo "=== 工作区扫描 ==="
HAS_DRAWIO=$(ls figures/*.drawio 2>/dev/null | wc -l)
HAS_TIKZ_TEX=$(ls figures/tikz_*.tex 2>/dev/null | wc -l)
HAS_TIKZ_PDF=$(ls figures/tikz_*.pdf 2>/dev/null | wc -l)
HAS_FIG_PDF_FROM_DRAWIO=$(ls figures/fig_*.pdf 2>/dev/null | wc -l)
echo "  *.drawio: $HAS_DRAWIO, tikz_*.tex: $HAS_TIKZ_TEX, tikz_*.pdf: $HAS_TIKZ_PDF"
echo "  fig_*.pdf (含 drawio 导出): $HAS_FIG_PDF_FROM_DRAWIO"
```

**根据扫描结果决定行动**：

| 状态 | 行动 |
|---|---|
| 规划要求的所有 drawio + tikz 都已生成（含 .drawio + 对应 .pdf） | **跳到 Step 8 (latex_includes 核对)**，验证通过即完成 |
| 部分已生成 | **只生成缺失的**（已有的不要重画） |
| 啥都没有 | 从 Step 1 开始 |

⛔ **铁律**：已有 `figures/*.drawio` / `figures/tikz_*.tex` / `figures/tikz_*.pdf` 不要重写。

### Step 1: Read existing state + DrawIO plan

1. Check what already exists from the previous paper-figure step:
```bash
echo "=== Existing figures ==="
ls -la figures/*.pdf 2>/dev/null | head -30
echo ""
echo "=== Existing .drawio files ==="
ls -la figures/*.drawio 2>/dev/null
echo ""
echo "=== latex_includes.tex exists? ==="
[ -f figures/latex_includes.tex ] && echo "YES" || echo "NO"
```

2. Extract the DrawIO/TikZ plan from planning docs:
```bash
# 自动选择规划文档（按存在性优先级）：
#   PROBLEM_ANALYSIS.md（数模竞赛/科研流程） > PROPOSAL.md（开题报告）
#   > PAPER_PLAN.md（论文写作/课程报告） > LITERATURE_REVIEW.md（文献综述，跳过）
PLAN_DOC=""
for f in PROBLEM_ANALYSIS.md PROPOSAL.md PAPER_PLAN.md; do
    if [ -f "$f" ]; then
        PLAN_DOC="$f"
        break
    fi
done
echo "=== 使用规划文档: $PLAN_DOC ==="

# 文献综述工作流不需要架构图，直接跳过
if [ -f LITERATURE_REVIEW.md ] && [ -z "$PLAN_DOC" ]; then
    echo "✅ 文献综述工作流不需要架构图，已跳过"
    exit 0
fi

# 没有规划文档时只处理用户明确请求的图，不自行增加兜底路线图。
if [ -z "$PLAN_DOC" ]; then
    echo "无规划文档：按用户明确请求确定本步骤图件；无请求则跳过。"
    PLAN_DOC=""
fi

echo "=== DrawIO plan from $PLAN_DOC ==="
grep -A 50 'DrawIO' "$PLAN_DOC" 2>/dev/null | grep -E 'DrawIO-[0-9]|^\- \[ \] fig_(arch|er|flow|module|roadmap|pipeline|framework|index|gantt|network)' || echo "No DrawIO plan found in $PLAN_DOC"
echo ""
echo "=== TikZ plan ==="
grep -E 'TikZ-[0-9]|模型架构|变量关系|因果路径|算法流程|几何示意' "$PLAN_DOC" 2>/dev/null || echo "No TikZ plan found"
echo ""
echo "=== GPT Image failures (need DrawIO fallback) ==="
# 按规划中的 DRAWIO/TIKZ 分类生成，不读取旧插图工具状态。
# Determine language（注意：comp_apmcm_zh 是中文赛项，必须先排除）
DRAWIO_LANG=$(python _utils/vivid_config.py get language)
echo "DrawIO language: $DRAWIO_LANG"
```

**⛔ 读完规划后，必须输出一个 DRAWIO PLAN CHECKLIST（后续步骤对照用）：**

工作流类型决定数量：
- **数模竞赛 / 科研流程**（有 PROBLEM_ANALYSIS.md）：**严格按 DrawIO 清单生成，一张不多一张不少**。
  ⛔ **清单里没有 `fig_flow_q1/q2/…` 就一张都不要画，也不要"补齐每个问题"**——子问题流程图默认关闭
  （用户可在前端开启，开启时清单里自然会有），清单没列即用户不要，自作主张补齐属于违规超产。
- **开题报告**（有 PROPOSAL.md）：只生成当前计划中分配给 DRAWIO/TIKZ 的图，不根据文档类型自行补图。
- **课程论文/报告**（有 PAPER_PLAN.md，无 PROBLEM_ANALYSIS.md）：按 PAPER_PLAN.md 中 `## 架构图（drawio）规划` 段落列出的 fig_arch/fig_er/fig_flow_* 生成
- **论文写作**（有 PAPER_PLAN.md，无 PROBLEM_ANALYSIS.md）：按 PAPER_PLAN.md 列出的图生成

```
DRAWIO PLAN CHECKLIST (from $PLAN_DOC):
[ ] 1. fig_roadmap — 技术路线图 (DrawIO)
[ ] 2. fig_flow_q1 — 问题一求解流程图 (DrawIO)
[ ] 3. fig_flow_q2 — 问题二求解流程图 (DrawIO)
[ ] 4. fig_pipeline — 数据处理 Pipeline (DrawIO)
[ ] 5. tikz_architecture — 模型架构图 (TikZ, if planned)
Total: N DrawIO + M TikZ
```
**每一条都必须在后续步骤中生成。规划清单就是合同。**

**⛔ DrawIO 图中所有文字必须与论文语言一致。**

**完整论文的总路线图由主计划按用途和所选格式安排；本步骤仅执行其中的 DRAWIO/TIKZ 条目，不要求总路线图必须使用 DrawIO。**

**开题报告 / 文献综述也按用户需求和当前计划执行，不因套用示例文件名而添加数模专用图。**

**⛔ 如果规划清单里有 N 条 DrawIO 图，本步骤结束时必须有 N 个 .drawio 文件和 N 个对应的 .pdf。缺一不可。**

### Step 2: Read DrawIO rules

**MANDATORY**: Read the DrawIO rules before writing ANY .drawio XML:
```bash
cat _utils/drawio_rules.md 2>/dev/null || cat skills/shared-scripts/drawio_rules.md
```

### Step 3: Generate .drawio XML files

**⛔ CRITICAL: DrawIO XML 文件很大（200-500行），必须分段写入，防止输出截断导致空工具调用。**

**正确写法（分 3 段写入）：**
```bash
# 第 1 段：写文件头 + 前半部分节点
cat << 'XMLEOF' > figures/fig_roadmap.drawio
<mxfile>
  <diagram name="Page-1">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- 前半部分节点（顶部标题栏 + 左栏 + 前几个阶段） -->
XMLEOF

# 第 2 段：追加中间节点
cat << 'XMLEOF' >> figures/fig_roadmap.drawio
        <!-- 中间部分节点（核心阶段 + 右栏方法） -->
XMLEOF

# 第 3 段：追加剩余节点 + 连线 + 闭合标签
cat << 'XMLEOF' >> figures/fig_roadmap.drawio
        <!-- 连线和底部 -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
XMLEOF
```

**每段不超过 150 行。** 一张技术路线图分 3 段，一张流程图分 2-3 段。

**⛔ 不要用 Write 工具写大 XML——Write 工具的 content 参数也会被截断。用 Bash heredoc 分段追加最可靠。**

按规划清单逐条生成，每张图一个 `.drawio` 文件：

**⛔ 配色与风格自由发挥原则：**
- 根据论文主题自主选择柔和高级的配色方案，不要每次都用默认学术蓝
- 不同子问题的流程图用不同配色，形成视觉区分
- 推荐风格：低饱和度渐变色（莫兰迪色系）、柔和的暖色/冷色搭配
- 技术路线图：鼓励在三栏结构基础上自由发挥阶段配色、子框样式、箭头形态
- 求解流程图：鼓励使用多种节点形状（六边形=数据处理、平行四边形=输入输出、圆柱=数据源、菱形=判断），不要全用圆角矩形
- 布局可以灵活：纵向、横向、L 形拐弯、泳道分区都可以，根据内容选最合适的
- **核心约束不变**：三栏结构（技术路线图）、判断分支+并行+循环（流程图）、双行节点、html=1、无 shadow

| 图类型 | 文件名示例 | 内容要点 |
|--------|-----------|---------|
| 技术路线图 | `fig_roadmap.drawio` | ⛔ 随机选模板 A 或 B（见 drawio_rules.md），保持三栏结构。节点居中分布 |
| 子问题求解流程图 | `fig_flow_q1.drawio` | ⛔ 必须包含：(1) 判断分支（菱形+是/否）(2) 并行分叉 (3) 循环反馈箭头 (4) 节点双行。**不要画右侧工具/方法注释栏**（技术路线图才需要） |
| 数据处理 Pipeline | `fig_pipeline.drawio` | 横向多阶段、每阶段工具/方法标注 |
| 概念框架图 | `fig_framework.drawio` | 理论模块分层展示，层间大箭头 |
| 指标体系层次图 | `fig_index_hierarchy.drawio` | 目标层→准则层→指标层的树形结构 |
| 模型选择决策树 | `fig_model_decision.drawio` | 从数据特征出发的分支判断 |
| 甘特图/调度方案图 | `fig_gantt.drawio` | 横轴时间+纵轴任务/资源 |
| 网络拓扑/路径图 | `fig_network.drawio` | 节点+边的网络结构 |

⛔ 以下图类型**不要用 DrawIO**，用 TikZ 生成：模型架构图、变量关系图、算法流程图（带公式）、几何示意图。

**⛔ 完整 XML 示例**：生成前先**随机选**一个模板参考其 XML 结构。当前有 4 个模板可选：
- `example_roadmap_stats.drawio`（B：粉色冷色，简版四阶段）
- `example_roadmap_stats_warm.drawio`（B-warm：暖橙紫色，简版四阶段）
- `example_roadmap_hex.drawio`（C：粉色冷色，完整六阶段，信息密度高）
- `example_roadmap_hex_cool.drawio`（C-cool：蓝色高对比，完整六阶段）

**⛔ 生成技术路线图前必须执行：**
```bash
echo "=== 随机选择技术路线图模板（4 选 1，确保不同论文风格有差异）==="
TEMPLATE=$(python3 -c "import random; print(random.choice(['B','B-warm','C','C-cool']))" 2>/dev/null || echo "C")
echo "本次使用模板: $TEMPLATE"
case "$TEMPLATE" in
  B)      FILE=example_roadmap_stats.drawio ;;
  B-warm) FILE=example_roadmap_stats_warm.drawio ;;
  C)      FILE=example_roadmap_hex.drawio ;;
  C-cool) FILE=example_roadmap_hex_cool.drawio ;;
esac
echo "--- 参考模板: $FILE ---"
cat _utils/$FILE 2>/dev/null | head -80
echo "... (参考完整 XML 结构和配色后再生成 fig_roadmap.drawio)"
```

⛔ **配色不要混搭**：选定模板后，整张图沿用该模板的配色方案，不要把不同模板的颜色混在一起。

**⛔ 生成求解流程图前必须执行：**
```bash
echo "=== 读取求解流程图示例 ==="
cat _utils/example_flow.drawio 2>/dev/null | head -50
echo "... (参考完整 XML 结构后再生成)"
```

**⛔ 每张图生成后立即验证文件存在：**
```bash
[ -f figures/fig_roadmap.drawio ] && echo "✅ fig_roadmap.drawio created" || echo "❌ MISSING"
```

### Step 4: 导出与检查

使用 `python "<RES>/scripts/export_drawio.py" figures/fig_name.drawio --format pdf`。需要 PNG 预览时再使用 `--format png`。源码有更改时重新导出，成功的已有图不重复生成。修复次数以检查与修复规则为准。

**自检清单（每轮都过一遍）：**

```
1. [重叠检查] 同行节点：(x1 + width1 + 30) ≤ x2；上下层：(y1 + height1 + 30) ≤ y2
2. [连线遮挡] 所有连线 jumpStyle=arc;jumpSize=6;rounded=1，不穿过节点
3. [文字溢出] 中文 width ≥ 字数×16+40，英文 width ≥ 字符数×8+40，whiteSpace=wrap
4. [间距一致] 同层节点间距差异 ≤ 10px
5. [样式一致] 同类节点 fillColor/strokeColor/fontSize 一致，fontstyle=1
6. [尺寸检查] 总宽度 ≤ pageWidth，总高度 ≤ pageHeight
7. [⛔ 居中检查] 中栏子框和节点必须在虚线框内居中分布，不要左对齐留大片空白。计算：左边距 = (容器宽度 - 内容总宽度) / 2。特别检查：只有 2-3 个节点的行、最后一行（结论阶段）
```

**⛔ 发现问题必须立即修改 XML 并重新导出，不能跳过。3 轮都失败 → 降级到 TikZ 兜底。**

### Step 5: Structure validation loop (⛔ MUST PASS)

对技术路线图和求解流程图运行结构自检脚本。**如果不通过，必须读取示例文件参考后重写，然后重新导出+重新自检，最多 3 轮。**

```bash
# 解析可用 Python：优先用初始化提供的 $VIVID_PYTHON（已排除 Windows 商店占位符 python3），
# 否则在候选里挑一个能真正执行的——占位符跑 -c 会非0退出，自动被淘汰。
PYTHON=""
for _cand in "$VIVID_PYTHON" python python3 "py -3"; do
    [ -z "$_cand" ] && continue
    if $_cand -c "import sys" >/dev/null 2>&1; then PYTHON="$_cand"; break; fi
done
[ -z "$PYTHON" ] && PYTHON=python

# 技术路线图结构检查 + 强制修复循环
if [ -f figures/fig_roadmap.drawio ]; then
    for ROUND in 1 2 3; do
        echo "=== 技术路线图结构自检 (round $ROUND) ==="
        $PYTHON _utils/drawio_check.py figures/fig_roadmap.drawio roadmap
        if [ $? -eq 0 ]; then
            echo "✅ 技术路线图结构合格"
            break
        fi
        if [ $ROUND -lt 3 ]; then
            echo "⛔ 不合格 — 读取示例后重写..."
            echo ">>> cat _utils/example_roadmap_stats.drawio 或 _utils/example_roadmap_hex.drawio 参考结构"
            # 助手: 你必须在这里读取一个示例模板，修改 fig_roadmap.drawio，然后重新导出 PDF
        else
            echo "⛔ 3 轮仍不合格 — 降级到 TikZ"
        fi
    done
fi

# 求解流程图结构检查 + 强制修复循环
for flow in figures/fig_flow_*.drawio; do
    [ -f "$flow" ] || continue
    for ROUND in 1 2 3; do
        echo "=== 求解流程图结构自检: $(basename $flow) (round $ROUND) ==="
        $PYTHON _utils/drawio_check.py "$flow" flow
        if [ $? -eq 0 ]; then
            echo "✅ 流程图结构合格"
            break
        fi
        if [ $ROUND -lt 3 ]; then
            echo "⛔ 不合格 — 读取示例后重写..."
            echo ">>> cat _utils/example_flow.drawio 参考结构"
        else
            echo "⛔ 3 轮仍不合格 — 降级到 TikZ"
        fi
    done
done
```

**⛔ 关键：上面的 bash 脚本只是检测框架。助手 在看到 `⛔ 不合格` 输出后，必须：**
1. **`cat _utils/example_roadmap_stats.drawio` 或 `_utils/example_roadmap_hex.drawio`** 读取完整示例（4 个模板任选一个，与初次生成时所选模板保持一致）
2. **重写 .drawio XML**（修复结构问题）
3. **重新导出 PDF**（`draw.io.exe --export ...`）
4. **重新运行 drawio_check.py** 验证
5. **重复直到通过或 3 轮用完**

**不允许看到 CRITICAL 后跳过不修。**

### Step 5.7:

按 [检查与修复](../../review-policy.md) 逐张打开实际图件，完整检查文字、图例、色条、遮挡、裁切、数据表达和模板保真；先汇总问题再集中修复，修复后复查，轮次与停止条件只由该文件规定。静态检查不能代替实际看图。

### Step 6: Plan reconciliation loop (⛔ 缺一不可)

**逐条对照规划清单，缺失的必须补生成。循环直到全部齐全。**

```bash
echo "=== DrawIO plan reconciliation ==="
echo "Planned:"
grep -E 'DrawIO-[0-9]' PROBLEM_ANALYSIS.md 2>/dev/null
echo ""
echo "Generated:"
ls -1 figures/*.drawio 2>/dev/null
echo ""
echo "Exported PDFs:"
ls -1 figures/fig_roadmap.pdf figures/fig_flow_*.pdf figures/fig_pipeline*.pdf figures/fig_framework*.pdf figures/fig_index_*.pdf figures/fig_model_*.pdf figures/fig_network*.pdf 2>/dev/null
```

**⛔ 对照上面的输出：**
1. 规划清单中的每一条，是否都有对应的 `.drawio` 文件？
2. 每个 `.drawio` 文件是否都有对应的 `.pdf`？
3. 如果有缺失 → **立即回到 Step 3 补生成该图的 .drawio XML → 导出 PDF → 自检**
4. **重复本步骤直到所有规划项都有 .drawio + .pdf**
5. 如果某张图反复失败（3 轮），启用跨工具兜底：DrawIO 失败 → TikZ，TikZ 失败 → DrawIO（简化版）

**⛔ 校验完成后，更新 DRAWIO PLAN CHECKLIST 状态：**
```
DRAWIO PLAN CHECKLIST (reconciliation):
[✅] 1. fig_roadmap — figures/fig_roadmap.drawio + figures/fig_roadmap.pdf (exists, XXX bytes)
[✅] 2. fig_flow_q1 — figures/fig_flow_q1.drawio + figures/fig_flow_q1.pdf (exists)
[❌] 3. fig_flow_q2 — MISSING — need to generate
[✅] 4. fig_pipeline — figures/fig_pipeline.drawio + figures/fig_pipeline.pdf (exists)
Result: 3/4 complete, 1 MISSING → go back to Step 3 for fig_flow_q2
```

### Step 7: Generate TikZ diagrams (if planned)

**如果规划清单中有 TikZ 类型的图，在此步骤生成。**

⛔⛔ **TikZ 物理尺寸 vs 字号匹配规则（避免"文字撞主图/标注互叠"陷阱）**：

TikZ 默认 1 单位 = 1cm，常见字号物理尺寸：
- `\small` ≈ 0.35 cm
- `\footnotesize` ≈ 0.30 cm
- `\tiny` ≈ 0.20 cm

⛔ **铁律**：任何标注节点的"可用空间"必须 **≥ 字号 × 2**（留 50% 留白）。

❌ **典型陷阱**（每条都会引发布局错乱）：
1. **画 2.20m × 0.30m 板凳直接写 `(0,0) rectangle (2.20, 0.30)`** → 实际 2.2cm × 0.3cm，字号都 0.35cm 比图还高 → 文字撑爆
2. **多层标注间距 < 0.5cm** → 两个 `\small` 字号文字（各 0.35cm）几乎贴一起
3. **`rotate=90` 长文字 + 短 y 跨度** → 文字溢出图形上下边界，叠到主图上
4. **`\resizebox{\textwidth}{!}{tikzpicture}` 后字号被等比放大** → 标注位置不变但文字变大几倍 → 全叠

✅ **正确做法**：
```latex
% 真实尺寸 < 5cm 的几何示意图，scale 必须 ≥ 2.0
\begin{tikzpicture}[scale=2.5, ... ]   % ← 关键：scale 拉开物理距离，字号不变
  \draw (0,0) rectangle (2.20, 0.30);  % 实际渲染 5.5cm × 0.75cm
  % 多层标注每层间距 ≥ 0.5cm（字号 0.35 × 2.5 scale = 0.875 视觉，留白足够）
  \draw (0,-0.30) -- (2.20,-0.30) ...  % 第 1 层
  \draw (0,-0.70) -- (2.20,-0.70) ...  % 第 2 层（间距 0.40 × 2.5 = 1.0cm 视觉）
\end{tikzpicture}
```

❌ **`\adjustbox{max width=\textwidth}` 用法**：图本身 > textwidth 才用，**绝不用来"放大小图"**——会让字撑爆位置

📐 **快速判断公式**：
- 量出你画的图 width/height（单位 cm）
- 如果 min(width, height) < 3cm → **必须** `scale=2.0+`（建议 2.5 或 3）
- 标注层之间间距 < 0.5cm → 标注会撞，必须拉大或减层数

1. Read TikZ rules:
```bash
cat _utils/tikz_rules.md 2>/dev/null || cat skills/shared-scripts/tikz_rules.md
```

2. Write TikZ code to `figures/tikz_diagrams.tex`.

3. **Compile + fix loop (最多 3 轮)：**

```
FOR round = 1 to 3:
  1. Compile: xelatex -interaction=nonstopmode -output-directory=figures figures/tikz_diagrams.tex
  2. If compilation fails:
     - Check: math mode paired? (\usetikzlibrary missing? align= attribute? xelatex for Chinese?)
     - Fix the .tex file
     - CONTINUE to next round
  3. Run tikz_check.sh:
     bash _utils/tikz_check.sh figures/tikz_diagrams.tex
  4. If CRITICAL issues found:
     - Fix the .tex file (color scheme, overlap, text width, edge crossing)
     - CONTINUE to next round
  5. If all pass → BREAK
END FOR
If still failing after 3 rounds → fallback to DrawIO (simplified version, no formulas)
```

**编译命令：**
```bash
xelatex -interaction=nonstopmode -output-directory=figures figures/tikz_diagrams.tex 2>&1 | tail -10
```

**tikz_check.sh 自检（编译成功后必须执行）：**
```bash
for texfile in figures/tikz_*.tex figures/tikz_diagrams.tex; do
    [ -f "$texfile" ] || continue
    echo "=== TikZ 自检: $(basename $texfile) ==="
    # ⛔ 用文件存在判断选版本，别用 ||：tikz_check.sh 报 CRITICAL 时退出非0，
    #    会被 || 误当成"_utils 版不可用"而重复跑一遍备用版 + 甩"找不到文件"噪声。
    if [ -f _utils/tikz_check.sh ]; then
        bash _utils/tikz_check.sh "$texfile" 2>/dev/null
    else
        bash skills/shared-scripts/tikz_check.sh "$texfile" 2>/dev/null
    fi
    if [ $? -gt 0 ]; then
        echo "⛔ 有 CRITICAL 问题 — 必须修复后重新编译"
    fi
done
```

**⛔ tikz_check.sh 报告的所有 CRITICAL 必须修复后重新编译。不允许带着 CRITICAL 完成步骤。**

**手动内容自检（编译成功 + tikz_check 通过后过一遍）：**
- [ ] 所有节点文字完整可见，没有被截断
- [ ] 连线没有穿过其他节点或文字
- [ ] 箭头方向正确（因果关系/数据流向）
- [ ] 数学公式渲染正确（变量名/希腊字母/上下标）
- [ ] 配色与论文整体风格一致（参考 tikz_rules.md 配色方案）
- [ ] 节点间距均匀，整图居中

**如果没有 TikZ 图需要生成 → 跳过此步骤。**

### Step 7.5:

按 [检查与修复](../../review-policy.md) 逐张打开实际图件，完整检查文字、图例、色条、遮挡、裁切、数据表达和模板保真；先汇总问题再集中修复，修复后复查，轮次与停止条件只由该文件规定。静态检查不能代替实际看图。

### Step 8: Update latex_includes.tex

为所有 DrawIO/TikZ 导出的 PDF **追加** LaTeX include 片段到 `figures/latex_includes.tex`。

**⛔ 注意：前一步 paper-figure 已经在 latex_includes.tex 中写入了数据图的 include 片段。本步骤只追加 DrawIO/TikZ 图的片段，不要覆盖已有内容。使用 `>>` 追加而非 `>` 覆盖。**

**⛔ 图片尺寸（width 决定实际大小，height 只是防止极高的图占满整页的上限）：**

> ⚠️ 关键认知：在 `keepaspectratio` 下，最终尺寸取 width / height 两个约束里**更小**的那个。所以 **height 永远只会把图压小，不会放大**。height 设太小（如 `0.38\textheight`）会让竖版/方形的流程图、决策树被压到只有半页宽，看不清。下表的 height 是**宽松的防溢出上限**，正常情况让 width 主导。

| 图类型 | width | height（仅防溢出上限） |
|--------|-------|--------|
| 技术路线图 | `\textwidth` | `0.7\textheight` |
| Pipeline 图 | `\textwidth` | `0.55\textheight` |
| 概念框架图 | `0.9\textwidth` | `0.65\textheight` |
| 求解流程图 | `0.82\textwidth` | `0.55\textheight` |
| 决策树 | `0.82\textwidth` | `0.6\textheight` |
| 指标体系 | `0.9\textwidth` | `0.55\textheight` |
| 网络拓扑 | `0.7\textwidth` | `0.7\textheight` |

⛔ 所有图必须有 `keepaspectratio`。
**⛔⛔ caption 长度铁律（防「流程图名字太长」）**：caption 只写图的类别/主题，≤ 20 个汉字（英文 ≤ 12 词），如「求解流程图」「整体技术路线图」「系统架构图」。禁止把整段方法描述、模型名罗列、步骤枚举塞进 caption。详细说明写进正文。
**⛔⛔ 尺寸铁律（防「流程图占太大」）**：竖向长条流程图按 width 缩放后自然高度常超一页，`keepaspectratio` 下 height 上限会反成实际尺寸→图撑满整页。上表 height 上限已一律压到 ≤ 0.7\textheight，**禁止回调到 0.8/0.85**。更根本的解法在布局：**流程图优先横向（左→右）或泳道/网格布局，不要画成纯竖向长条**；竖向仅在强上下依赖（如迭代循环）时才用，并把并列分支横向摊开压低总高。目标出图宽高比接近 4:3~16:9，不要接近或超过 1:1.5 的瘦高比。

**⛔ Captions must match paper language.**

```latex
% === 技术路线图 ===
\begin{figure}[H]
\centering
\includegraphics[width=\textwidth,height=0.7\textheight,keepaspectratio]{figures/fig_roadmap.pdf}
\caption{整体技术路线图}\label{fig:roadmap}
\end{figure}
```

**⛔⛔⛔ TikZ 图必须也写进 latex_includes.tex（最常被漏！）：**
TikZ 编译产出 `figures/tikz_diagrams.pdf`（如果分多个 .tex 则是 `figures/tikz_*.pdf`，可能多页）。
**每一个 TikZ PDF 都必须像 DrawIO 一样，在 latex_includes.tex 里有一个 `\includegraphics` 图块**，
否则写作步骤读 latex_includes.tex 时看不到 TikZ 图，论文里就会缺图。

```latex
% === TikZ 几何/算法/架构图 ===
\begin{figure}[H]
\centering
\includegraphics[width=0.85\textwidth,height=0.85\textheight,keepaspectratio]{figures/tikz_diagrams.pdf}
\caption{弦长递推几何关系示意}\label{fig:tikz_geom}
\end{figure}
```
- 如果一个 `tikz_diagrams.tex` 里画了多张图（多个 `\begin{tikzpicture}`），编译出的 PDF 是多页。
  必须先用 `pdfseparate figures/tikz_diagrams.pdf figures/tikz_diagrams_%d.pdf` 拆成单页，
  或在 .tex 里每张图单独 `\newpage`，然后为**每一页/每一张** TikZ 图各写一个 `\includegraphics` 块，
  caption 与规划清单里的 TikZ 条目一一对应。
- ⛔ caption 必须与论文语言一致（中文论文用中文 caption）。

```latex
% === 速度传递算法流程图 ===
\begin{figure}[H]
\centering
\includegraphics[width=0.85\textwidth,height=0.85\textheight,keepaspectratio]{figures/tikz_diagrams_2.pdf}
\caption{速度传递与刚体杆约束求解流程}\label{fig:tikz_algo}
\end{figure}
```

**⛔ 追加后自检：**
```bash
echo "=== latex_includes.tex 追加验证 ==="
# 1. 检查每个 DrawIO PDF 是否都有对应的 \includegraphics
for pdf in figures/fig_roadmap.pdf figures/fig_flow_*.pdf figures/fig_pipeline*.pdf figures/fig_framework*.pdf figures/fig_index_*.pdf figures/fig_network*.pdf; do
    [ -f "$pdf" ] || continue
    bn=$(basename "$pdf")
    if grep -q "$bn" figures/latex_includes.tex 2>/dev/null; then
        echo "✅ $bn has include entry"
    else
        echo "❌ $bn MISSING from latex_includes.tex — must append"
    fi
done
# 1b. ⛔ 检查每个 TikZ PDF（含多页拆分）是否都有 \includegraphics —— 最常被漏
for tpdf in figures/tikz_diagrams.pdf figures/tikz_diagrams_*.pdf figures/tikz_*.pdf; do
    [ -f "$tpdf" ] || continue
    tbn=$(basename "$tpdf")
    if grep -q "$tbn" figures/latex_includes.tex 2>/dev/null; then
        echo "✅ TikZ $tbn has include entry"
    else
        echo "❌ TikZ $tbn MISSING from latex_includes.tex — must append a figure block for it"
    fi
done
# 2. 检查 label 是否有重复
DUPS=$(grep -oh '\\label{[^}]*}' figures/latex_includes.tex 2>/dev/null | sort | uniq -d)
[ -z "$DUPS" ] && echo "✅ No duplicate labels" || echo "❌ Duplicate labels: $DUPS"
```
**如果有 ❌，立即修复（追加缺失的 include 或修复重复 label）。TikZ 的 ❌ 尤其不能放过。**

### Step 9:

对照 FIGURE_MANIFEST 检查每张 Draw.io/TikZ 图的可编辑源码和实际导出文件。运行 `scripts/drawio_check_compat.py`、`_utils/tikz_check.sh` 的适用检查。论文交付时核对引用片段。

按 [检查与修复](../../review-policy.md) 逐张打开实际图件，完整检查文字、图例、色条、遮挡、裁切、数据表达和模板保真；先汇总问题再集中修复，修复后复查，轮次与停止条件只由该文件规定。静态检查不能代替实际看图。

## Key Rules

- DrawIO .drawio files export to PDF via `draw.io.exe --export --format pdf --crop`
- All fonts bold (`fontstyle=1`), line width 3pt
- All edges: `jumpStyle=arc;jumpSize=6;rounded=1`
- ⛔ Edges must NOT cross nodes or obscure text
- Component spacing 30-50px, grid alignment (`gridSize=10`)
- Default color scheme: academic blue `#dae8fc`/`#6c8ebf`
- Each mxCell id must be globally unique
- Chinese text in UTF-8, XML special chars must be escaped
- ⛔ No `shadow=1`, no XML comments, no `shape=callout`
- ⛔ All nodes must have `html=1` (including edge labels)
- ⛔ No in-figure title — titles managed by LaTeX `\caption{}`
- ⛔ 3 rounds DrawIO fail → fallback to TikZ; 3 rounds TikZ fail → fallback to DrawIO
