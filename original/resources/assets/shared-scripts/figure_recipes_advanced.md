# Advanced Figure Recipes — Clean Academic Edition

High-impact, SCI-quality figure types with clean, publication-ready styling.
Every recipe features: solid colors, single-layer semi-transparent fills, annotation boxes,
subtle grids (alpha=0.15), and minimal decoration. Titles are handled by LaTeX captions.

> **配色规范**: 所有配方统一使用 `PALETTE[n]`（主色系列）或 `COLORS['xxx']`（语义色，如 `_lighten()` 浅色填充）。禁止硬编码 hex 色值。
> **标题规范**: 所有配方不使用 `set_title()`，而由 LaTeX `\caption{}` 处理。
> **格式规范**: 统一去掉 top/right spines；标注框统一用 `bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=..., alpha=0.9)`。
> **曲线原则**: 不使用多段拟合模拟（n_seg=30/40/50/60/80），而用简单的 `plot()`/`hlines()`/`fill_between()`。

---

## 1. Lollipop Chart — 棒棒糖图（渐变色茎 + 排名徽章 + 中位数参考线）

**样式保真强要求（绘制时执行）**：使用本配方时，必须以尽可能复现原版样式为目标，保留连续渐变配色、随得分变化的茎线粗细与端点大小、排名徽章、首名背景高亮及中位数参考线与标注；配色需适配当前风格时仍保留连续渐变和层次关系，不要直接改成普通离散配色、等粗线条的棒棒糖图。仅按真实数据语义和可读性作必要调整，不虚构排名或统计值；原代码出现颜色类型不兼容、圆形徽章变形或裁切时，应修正实现并保留视觉意图，不要以删除或简化这些元素代替修正。

**场景**: 按单一指标对方法/方案排名。比柱状图更简洁，常见于 Nature/Science。
**防重叠**: 使用 `smart_labels()` 自动推开重叠的数值标签。
**风格**: 渐变色从紫罗兰（高分）过渡到珊瑚橙（低分）；线粗、圆点大小也随分数渐变。前三名有排名徽章。中位数参考线分割图面。
**⚠ 关键要点**: 茎线从 x=0 开始；颜色按 HSL 明度线性渐变（避免相邻项同色）；前三名实心圆徽章。

```python
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten, smart_labels
setup_style()
import matplotlib.pyplot as plt
import matplotlib.colors as mc
import numpy as np
import colorsys

methods = ['Ours', 'Baseline-A', 'Baseline-B', 'Baseline-C', 'Baseline-D']
scores = [0.923, 0.887, 0.862, 0.841, 0.815]

n = len(methods)
score_min, score_max = min(scores), max(scores)
score_range = score_max - score_min if score_max > score_min else 1

# ── 渐变配色：从紫罗兰 → 珊瑚橙（明度和色相同时渐变）
color_top = '#7B6BA5'     # 紫罗兰（高分，偏冷一点）
color_bottom = '#E08B74'  # 珊瑚橙（低分，偏暖）

def interpolate_color(c1, c2, t):
    """HSL 空间插值：t=0 返回 c1，t=1 返回 c2"""
    r1, g1, b1 = mc.to_rgb(c1)
    r2, g2, b2 = mc.to_rgb(c2)
    h1, l1, s1 = colorsys.rgb_to_hls(r1, g1, b1)
    h2, l2, s2 = colorsys.rgb_to_hls(r2, g2, b2)
    if abs(h2 - h1) > 0.5:
        if h1 < h2: h1 += 1.0
        else: h2 += 1.0
    h = (h1 + (h2 - h1) * t) % 1.0
    l = l1 + (l2 - l1) * t
    s = s1 + (s2 - s1) * t
    return colorsys.hls_to_rgb(h, l, s)

item_colors = [interpolate_color(color_top, color_bottom, i / (n - 1) if n > 1 else 0) for i in range(n)]

# ── 自适应高度（每项 0.46 高度 + 上下留白）
_fig_h = max(4, n * 0.46 + 1.8)
fig, ax = plt.subplots(figsize=(7.5, _fig_h))
y_pos = np.arange(n)

# 极浅网格线
ax.grid(axis='x', alpha=0.12, linestyle='-', color=COLORS['grid'])
ax.set_axisbelow(True)

# 中位数参考线（置于底层）
median_val = np.median(scores)
ax.axvline(median_val, color=COLORS['ref_line'], linestyle=':', linewidth=1.0, alpha=0.5, zorder=1)

# ── 主体：渐变色茎线 + 渐变圆点
for i, (m, s) in enumerate(zip(methods, scores)):
    c = item_colors[i]
    ratio = (s - score_min) / score_range
    lw = 1.6 + 2.0 * ratio

    # 茎线从 0 开始
    ax.plot([0, s], [y_pos[i], y_pos[i]],
            color=c, linewidth=lw, zorder=3, solid_capstyle='round')

    # 端点圆点 —— 大小随分数渐变
    dot_size = 55 + 120 * ratio
    ax.scatter(s, y_pos[i], color=c, s=dot_size, zorder=5,
               edgecolors='white', linewidths=1.8)

    # 数值标签
    ax.text(s + score_range * 0.03, y_pos[i], f'{s:.3f}',
            fontsize=8.5, fontweight='bold' if i < 3 else 'normal',
            color=c, va='center', ha='left')

    # ── 排名徽章区域
    badge_x = -score_range * 0.065
    rank = i + 1
    if rank <= 3:
        badge = plt.Circle((badge_x, y_pos[i]), 0.3,
                            color=_lighten(c, 0.15), zorder=6,
                            transform=ax.transData)
        ax.add_patch(badge)
        ax.text(badge_x, y_pos[i], str(rank),
                fontsize=8.5, fontweight='bold', color='white',
                ha='center', va='center', zorder=7)
    else:
        ax.text(badge_x, y_pos[i], str(rank),
                fontsize=7.5, color=_lighten(c, 0.2),
                ha='center', va='center', fontweight='bold')

# 第一名背景高亮条
ax.axhspan(y_pos[0] - 0.42, y_pos[0] + 0.42, alpha=0.06,
           color=item_colors[0], zorder=0)

# 中位数标注 —— 置于图的顶部
ax.text(median_val, -0.9, f'中位数 {median_val:.3f}',
        fontsize=8, color=COLORS['ref_line'], ha='center', va='bottom',
        bbox=dict(boxstyle='round,pad=0.25', facecolor='white',
                  edgecolor=COLORS['ref_line'], alpha=0.85))

ax.set_yticks(y_pos)
ax.set_yticklabels(methods, fontsize=10)
ax.set_xlabel('F1 Score', fontsize=11)
ax.set_xlim(-score_range * 0.13, score_max + score_range * 0.15)
ax.set_ylim(n - 0.5, -1.4)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_lollipop.pdf')
```

**⚠ 易踩的坑（棒棒糖图专用）：**
```python
# 1. ylim 上方留空：ax.set_ylim(n-0.5, -1.4)，给中位数标注留空间
# 2. xlim 右侧留余量（score_max + score_range*0.15），给数值标签留空间
# 3. xlim 左侧留负值（-score_range*0.13），给排名徽章留空间
# 4. 数值标签偏移用相对值（score_range*0.03），不要用固定像素偏移
# 5. 排名徽章用 plt.Circle + transData，确保圆形不变形
# 6. 中位数标注放在 y=-0.9（图面上方），需要配合上方留空设置
# 7. 当条目数 >15 时，_fig_h 公式自动增高（每项 0.46 高度不会挤压）
```

---

## 2. Dumbbell Chart — 哑铃图（连接线 + 变化率 + 显著性标记）

**场景**: 前后对比、两组差异。比分组柱状图更直观。

```python
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()
import matplotlib.pyplot as plt
import numpy as np

metrics = ['Accuracy', 'Precision', 'Recall', 'F1', 'AUC']
before = [0.82, 0.79, 0.85, 0.81, 0.88]
after = [0.91, 0.88, 0.90, 0.89, 0.94]

# ── 自适应高度
_fig_h = max(3.5, len(metrics) * 0.7 + 1)
fig, ax = plt.subplots(figsize=(8, _fig_h))
y = np.arange(len(metrics))

# Subtle grid
ax.grid(axis='x', alpha=0.15, linestyle='-', color=COLORS['grid'])
ax.set_axisbelow(True)

# Simple connector lines + arrow heads
for i in range(len(metrics)):
    delta = after[i] - before[i]
    pct_change = delta / before[i] * 100
    # Simple connector line
    ax.plot([before[i], after[i]], [y[i], y[i]],
            color=PALETTE[2], linewidth=2.0, solid_capstyle='round')
    # Arrow head at the "after" end
    ax.annotate('', xy=(after[i], y[i]), xytext=(after[i] - 0.012, y[i]),
                arrowprops=dict(arrowstyle='->', color=PALETTE[0], lw=2.0))

    # Before / After dots
    ax.scatter(before[i], y[i], color=PALETTE[3], s=80, zorder=3,
               edgecolors='white', linewidths=1.0, label='Before' if i == 0 else '')
    ax.scatter(after[i], y[i], color=PALETTE[0], s=80, zorder=3,
               edgecolors='white', linewidths=1.0, label='After' if i == 0 else '')

    # % change label
    ax.text(after[i] + 0.015, y[i] - 0.15, f'+{delta:.2f} ({pct_change:+.1f}%)',
            va='center', fontsize=8, color=PALETTE[0], fontweight='bold')

    # Significance marker (stars)
    if pct_change > 8:
        sig = '***'
    elif pct_change > 5:
        sig = '**'
    else:
        sig = '*'
    ax.text(after[i] + 0.015, y[i] + 0.2, sig, va='center', fontsize=9,
            color=COLORS['down'], fontweight='bold')

ax.set_yticks(y)
ax.set_yticklabels(metrics, fontsize=10)
ax.set_xlabel('Score', fontsize=11)
ax.legend(loc='lower right', frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9,
          fancybox=True, shadow=False)
ax.invert_yaxis()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_dumbbell.pdf')
```

**⚠ 易踩的坑（哑铃图专用）：**
```python
# 1. % change 标签和星号分两行（y 偏移 -0.15 和 +0.2），不要放在一行
# 2. xlim 右侧留 15% 余量，给 % change 标签和星号留空间
# 3. 当 before/after 值很接近（差 <0.02）时，标签会重叠 → 只标注 after 值
# 4. 图例放 lower right（因为通常数据在上方，不会遮挡）
```

---

## 3. Slope Chart — 斜率图（颜色编码线 + 排名变化标注）

**场景**: 跨条件的排名/趋势变化。比分组柱状图更清晰地展示交叉变化。

```python
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()
import matplotlib.pyplot as plt
import numpy as np

methods = ['Method-A', 'Method-B', 'Method-C', 'Method-D']
dataset1 = [0.92, 0.88, 0.85, 0.90]
dataset2 = [0.87, 0.91, 0.89, 0.86]

fig, ax = plt.subplots(figsize=(6, 5.5))

# Subtle grid
ax.grid(axis='y', alpha=0.15, linestyle='-', color=COLORS['grid'])
ax.set_axisbelow(True)

# Compute ranks
rank1 = list(np.argsort(np.argsort([-v for v in dataset1])) + 1)
rank2 = list(np.argsort(np.argsort([-v for v in dataset2])) + 1)

for i, m in enumerate(methods):
    diff = dataset2[i] - dataset1[i]
    # Green = improve, Red = decline
    base_color = COLORS['up'] if diff >= 0 else COLORS['down']

    # Simple line connecting two points
    ax.plot([0, 1], [dataset1[i], dataset2[i]], color=base_color,
            linewidth=2.5, solid_capstyle='round')

    # Endpoints
    ax.scatter([0], [dataset1[i]], color=base_color, s=90, zorder=5,
               edgecolors='white', linewidths=1.2)
    ax.scatter([1], [dataset2[i]], color=base_color, s=90, zorder=5,
               edgecolors='white', linewidths=1.2)

    # Value labels
    ax.text(-0.08, dataset1[i], f'{dataset1[i]:.2f}', ha='right', va='center',
            fontsize=9, color=base_color)
    ax.text(1.08, dataset2[i], f'{dataset2[i]:.2f}', ha='left', va='center',
            fontsize=9, color=base_color)

    # Rank change annotation
    rank_delta = rank1[i] - rank2[i]  # positive = improved rank
    if rank_delta != 0:
        arrow_sym = '↑' if rank_delta > 0 else '↓'
        rank_color = COLORS['up'] if rank_delta > 0 else COLORS['down']
        ax.text(1.22, dataset2[i], f'{m} {arrow_sym}{abs(rank_delta)}',
                ha='left', va='center', fontsize=8, color=rank_color,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=rank_color, alpha=0.9))
    else:
        ax.text(1.22, dataset2[i], f'{m} →', ha='left', va='center',
                fontsize=8, color=COLORS['ref_line'])

ax.set_xticks([0, 1])
ax.set_xticklabels(['Dataset-1', 'Dataset-2'], fontsize=11)
ax.set_xlim(-0.35, 1.65)
ax.set_ylim(min(dataset1 + dataset2) - 0.03, max(dataset1 + dataset2) + 0.03)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_slope.pdf')
```

**⚠ 易踩的坑（Slope Chart 专用）：**
```python
# 1. 当多条数值标签重叠时，只标注变化最大的 2-3 条线，其余省略
# 2. 右侧排名变化标注用 bbox 白底，防止与数值标签混在一起
# 3. xlim 左侧留 0.35，给标签留空间（ax.set_xlim(-0.35, 1.65)）
# 4. 值域较窄（如数值在 0.85-0.92 之间）时，ylim 不要从 0 开始，放大差异
```


---

## 4. Bump Chart — 凹凸图（色带高亮 + 两端排名标签 + "本文"高亮）

**场景**: 跟踪跨数据集/指标的排名变化。比表格更直观。

```python
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
import matplotlib.pyplot as plt
import numpy as np

methods = ['Ours', 'BERT', 'GPT', 'RoBERTa']
datasets = ['MNLI', 'QQP', 'SST-2', 'QNLI']
ranks = [[1, 1, 2, 1], [3, 2, 1, 3], [2, 3, 3, 2], [4, 4, 4, 4]]

fig, ax = plt.subplots(figsize=(8, 5))
x = np.arange(len(datasets))

# Subtle grid
ax.grid(axis='y', alpha=0.15, linestyle='-', color=COLORS['grid'])
ax.set_axisbelow(True)

for i, (m, r) in enumerate(zip(methods, ranks)):
    is_ours = (i == 0)
    lw = 3.5 if is_ours else 1.8
    alpha_line = 1.0 if is_ours else 0.55
    ms = 14 if is_ours else 9

    # Gradient ribbon for "Ours"
    if is_ours:
        for k in range(len(x) - 1):
            x_fill = np.linspace(x[k], x[k + 1], 50)
            y_fill = np.interp(x_fill, x, r)
            ax.fill_between(x_fill, y_fill - 0.15, y_fill + 0.15,
                            alpha=0.15, color=PALETTE[0])

    # Line
    ax.plot(x, r, 'o-', color=PALETTE[i], linewidth=lw, markersize=ms,
            label=m, zorder=3 + (1 if is_ours else 0), alpha=alpha_line,
            markeredgecolor='white', markeredgewidth=1.5 if is_ours else 0.8)

    # Rank labels at both ends
    ax.text(x[0] - 0.2, r[0], f'#{r[0]} {m}', va='center', ha='right',
            fontsize=9, color=PALETTE[i],
            fontweight='bold' if is_ours else 'normal')
    ax.text(x[-1] + 0.2, r[-1], f'#{r[-1]} {m}', va='center', ha='left',
            fontsize=9, color=PALETTE[i],
            fontweight='bold' if is_ours else 'normal')

# Highlight box for "Ours"
ax.annotate('★ Ours: Rank #1 in 3/4 datasets',
            xy=(x[0], ranks[0][0]), xytext=(x[0] + 0.5, ranks[0][0] - 0.6),
            fontsize=8.5, color=PALETTE[0], fontweight='bold',
            arrowprops=dict(arrowstyle='->', color=PALETTE[0], lw=1.2),
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                      edgecolor=PALETTE[0], alpha=0.9))

ax.set_xticks(x)
ax.set_xticklabels(datasets, fontsize=10)
ax.set_yticks([1, 2, 3, 4])
ax.set_yticklabels(['1st', '2nd', '3rd', '4th'], fontsize=10)
ax.set_ylabel('Rank', fontsize=11)
ax.invert_yaxis()
ax.set_xlim(-0.6, len(datasets) - 0.4)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_bump.pdf')
```

**⚠ 易踩的坑（Bump Chart 专用）：**
```python
# 1. 两端排名标签用 ha='right'/ha='left'，不要用 ha='center'（会与线重叠）
# 2. xlim 左侧留 0.6，给两端标签留空间
# 3. 高亮标注不要与排名标签重叠：xytext 偏移至少 0.5 个单位
# 4. 方法数 >6 时，只标注首尾两端，省略中间（减少图面杂乱）
```

---

## 5. Sankey Diagram — 桑基图（D3 风格，矩形节点 + 贝塞尔流带）

**场景**: 资源分配、数据流向、能量流、用户路径。矩形节点（高度=流量）+ 半透明贝塞尔曲线连接带（按 source 分色）。

⛔ **不要用 `matplotlib.sankey.Sankey`**——它出来是"动物形状/箭头风格"，标签重叠、比例失真、整体丑。下面这套用 path + Bezier 手写，是 D3.js / Plotly 风格的现代 Sankey。

```python
import shutil, os
os.makedirs('_utils', exist_ok=True)
for f in ['plot_utils.py']:
    src = os.path.join(os.path.dirname(__file__), f)
    if os.path.exists(src):
        shutil.copy2(src, f'_utils/{f}')

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch, Rectangle
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()


def draw_sankey(ax, source_nodes, target_nodes, flows,
                source_colors=None, target_colors=None,
                left_x=0.10, right_x=0.90,
                node_width=0.025, node_gap=0.03,
                title_top=None):
    """D3 风格 Sankey 图（矩形节点 + 贝塞尔流带）。

    Args:
        source_nodes: list of (name, total_value)，例如 [('国产', 1473), ('俄罗斯', 1500)]
        target_nodes: list of (name, total_value)，例如 [('总供给', 3000)]
        flows: list of dict {source_idx: int, target_idx: int, value: float}
        source_colors / target_colors: 可选，None 时自动按 PALETTE 分色
        node_width: 矩形宽度（相对坐标 0-1）
        node_gap: 同侧节点间垂直间距
        title_top: 顶部副标题（如"流量守恒 (万 m³)"）
    """
    total_src = sum(v for _, v in source_nodes)
    total_tgt = sum(v for _, v in target_nodes)
    if abs(total_src - total_tgt) > 1e-3:
        raise ValueError(f'流量不守恒：source 合计 {total_src} ≠ target 合计 {total_tgt}')

    Y_MARGIN = 0.08
    avail_h_src = (1 - 2 * Y_MARGIN) - node_gap * max(0, len(source_nodes) - 1)
    avail_h_tgt = (1 - 2 * Y_MARGIN) - node_gap * max(0, len(target_nodes) - 1)

    src_ranges = []
    y = 1 - Y_MARGIN
    for _, v in source_nodes:
        h = v / total_src * avail_h_src
        src_ranges.append((y - h, y))
        y = y - h - node_gap

    tgt_ranges = []
    y = 1 - Y_MARGIN
    for _, v in target_nodes:
        h = v / total_tgt * avail_h_tgt
        tgt_ranges.append((y - h, y))
        y = y - h - node_gap

    if source_colors is None:
        source_colors = [PALETTE[i % len(PALETTE)] for i in range(len(source_nodes))]
    if target_colors is None:
        target_colors = [COLORS.get('text', '#444444')] * len(target_nodes)

    # 左侧节点矩形 + 标签
    for i, ((name, v), (y0, y1)) in enumerate(zip(source_nodes, src_ranges)):
        rect = Rectangle((left_x - node_width / 2, y0), node_width, y1 - y0,
                         facecolor=source_colors[i], edgecolor='none', alpha=0.92, zorder=3)
        ax.add_patch(rect)
        ax.text(left_x - node_width / 2 - 0.012, (y0 + y1) / 2,
                f'{name}\n{v:g}',
                ha='right', va='center', fontsize=9,
                color=COLORS.get('text', '#222'), fontweight='bold')

    # 右侧节点矩形 + 标签
    for i, ((name, v), (y0, y1)) in enumerate(zip(target_nodes, tgt_ranges)):
        rect = Rectangle((right_x - node_width / 2, y0), node_width, y1 - y0,
                         facecolor=target_colors[i], edgecolor='none', alpha=0.92, zorder=3)
        ax.add_patch(rect)
        ax.text(right_x + node_width / 2 + 0.012, (y0 + y1) / 2,
                f'{name}\n{v:g}',
                ha='left', va='center', fontsize=9,
                color=COLORS.get('text', '#222'), fontweight='bold')

    # 贝塞尔流带
    src_top_used = [r[1] for r in src_ranges]
    tgt_top_used = [r[1] for r in tgt_ranges]

    for flow in flows:
        si, ti, val = flow['source_idx'], flow['target_idx'], flow['value']
        s_h = val / total_src * avail_h_src
        t_h = val / total_tgt * avail_h_tgt
        s_y_top = src_top_used[si]; s_y_bot = s_y_top - s_h; src_top_used[si] = s_y_bot
        t_y_top = tgt_top_used[ti]; t_y_bot = t_y_top - t_h; tgt_top_used[ti] = t_y_bot

        mid_x = (left_x + right_x) / 2
        path_data = [
            (Path.MOVETO,    (left_x + node_width / 2, s_y_top)),
            (Path.CURVE4,    (mid_x, s_y_top)),
            (Path.CURVE4,    (mid_x, t_y_top)),
            (Path.CURVE4,    (right_x - node_width / 2, t_y_top)),
            (Path.LINETO,    (right_x - node_width / 2, t_y_bot)),
            (Path.CURVE4,    (mid_x, t_y_bot)),
            (Path.CURVE4,    (mid_x, s_y_bot)),
            (Path.CURVE4,    (left_x + node_width / 2, s_y_bot)),
            (Path.CLOSEPOLY, (left_x + node_width / 2, s_y_top)),
        ]
        codes, verts = zip(*path_data)
        flow_color = flow.get('color', source_colors[si])
        patch = PathPatch(Path(verts, codes),
                          facecolor=flow_color, edgecolor='none', alpha=0.42, zorder=2)
        ax.add_patch(patch)

    if title_top:
        ax.text(0.5, 0.98, title_top, ha='center', va='top',
                fontsize=10, color=COLORS.get('text', '#444'), fontweight='bold')

    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_aspect('auto'); ax.axis('off')


# ── 示例 1: 多 source → 单 target（资源分配场景）
fig, ax = plt.subplots(figsize=(9, 5))
source_nodes = [('国产', 1473), ('俄罗斯', 1500), ('卡塔尔', 27)]
target_nodes = [('总供给 = 需求 (万 m³)', 3000)]
flows = [
    {'source_idx': 0, 'target_idx': 0, 'value': 1473},
    {'source_idx': 1, 'target_idx': 0, 'value': 1500},
    {'source_idx': 2, 'target_idx': 0, 'value': 27},
]
draw_sankey(ax, source_nodes, target_nodes, flows,
            title_top='问题一 最优供应量分配（流量守恒，万 m³）')

auto_rate = 1473 / 3000 * 100
import_rate = (1500 + 27) / 3000 * 100
ax.text(0.05, 0.04,
        f'自给率 = {auto_rate:.1f}%   进口依赖 = {import_rate:.1f}%',
        ha='left', va='bottom', fontsize=8.5,
        color=COLORS.get('text', '#444'),
        bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                  edgecolor='#cccccc', linewidth=0.5))

fig.tight_layout()
save_fig(fig, 'figures/fig_sankey_supply.pdf')


# ── 示例 2: 单 source → 多 target（数据分流场景）
fig, ax = plt.subplots(figsize=(10, 5.5))
source_nodes = [('原始数据', 1000)]
target_nodes = [('训练集', 600), ('测试集', 300), ('验证集', 100)]
flows = [
    {'source_idx': 0, 'target_idx': 0, 'value': 600, 'color': PALETTE[0]},
    {'source_idx': 0, 'target_idx': 1, 'value': 300, 'color': PALETTE[1]},
    {'source_idx': 0, 'target_idx': 2, 'value': 100, 'color': PALETTE[2]},
]
draw_sankey(ax, source_nodes, target_nodes, flows,
            target_colors=[PALETTE[0], PALETTE[1], PALETTE[2]],
            title_top='数据集划分')
fig.tight_layout()
save_fig(fig, 'figures/fig_sankey_split.pdf')


# ── 示例 3: 多对多
fig, ax = plt.subplots(figsize=(10.5, 6))
source_nodes = [('来源A', 500), ('来源B', 300), ('来源C', 200)]
target_nodes = [('去向X', 400), ('去向Y', 350), ('去向Z', 150), ('去向W', 100)]
flows = [
    {'source_idx': 0, 'target_idx': 0, 'value': 300},
    {'source_idx': 0, 'target_idx': 1, 'value': 150},
    {'source_idx': 0, 'target_idx': 2, 'value':  50},
    {'source_idx': 1, 'target_idx': 0, 'value': 100},
    {'source_idx': 1, 'target_idx': 1, 'value': 150},
    {'source_idx': 1, 'target_idx': 3, 'value':  50},
    {'source_idx': 2, 'target_idx': 1, 'value':  50},
    {'source_idx': 2, 'target_idx': 2, 'value': 100},
    {'source_idx': 2, 'target_idx': 3, 'value':  50},
]
draw_sankey(ax, source_nodes, target_nodes, flows,
            title_top='多对多流向分析')
fig.tight_layout()
save_fig(fig, 'figures/fig_sankey_many.pdf')
```

**⛔ 易踩的坑（Sankey Diagram 专用）：**

1. **流量必须守恒**：source 总和 = target 总和（函数已加 `raise ValueError` 校验，超 1e-3 报错）
2. **节点 ≤ 8 个**：每侧超过 8 节点 → 矩形太薄看不清，改用桑基图 + 滚动条（plotly）或拆成多张图
3. **流 ≤ 15 条**：超过 15 条流 → 视觉混乱，用 Sankey 不合适，改成饼图嵌套或矩阵热力图
4. **图例颜色**：每个 source 用同一颜色，target 矩形可以中性色（灰）或承袭 source 色
5. **数值单位写在 `title_top` 里**（如 "（流量守恒，万 m³）"），不要在每个节点重复
6. **不要用 `matplotlib.sankey.Sankey`**：那个 API 出来是"箭头形状"，标签重叠、比例失真

**⛔ 反例（用户实际踩过的坑）：**

```python
# ❌ 错误：matplotlib.sankey.Sankey 出来是"动物形状"
from matplotlib.sankey import Sankey
sankey = Sankey(ax=ax, scale=0.008, ...)
sankey.add(flows=[1473, 1500, 27, -3000], orientations=[1, 0, -1, 0], ...)
# 结果：3 个 source 从 3 个方向汇聚到 1 个 target → 形状像箭头 / 鱼，不是 Sankey

# ✅ 正确：用上面的 draw_sankey 函数，矩形 + 贝塞尔流带
draw_sankey(ax, source_nodes, target_nodes, flows, title_top='...')
```


---

## 6. Waterfall Chart — 瀑布图（彩色渐变柱图 + 连接线 + 顶部数值标注）

**样式保真强要求（绘制时执行）**：使用本配方时，必须以尽可能复现原版样式为目标，保留各步向右延伸的半透明层叠色带、连续阶梯线、白色描边圆点、累计值标注、总增量标注及贡献图例，不要仅因普通浮动柱瀑布图更容易实现就替换原版设计。按实际正负增量重算层带位置、累计值和标注；发生重叠时先调整透明度、间距、尺寸和标注位置。仅在数据语义不支持或调整后仍妨碍阅读时作必要删改，并说明原因；原代码兼容问题应修正实现，不应成为省略原版样式的理由。

**场景**: 因素分解、消融贡献分析。比柱状图更适合展示增量贡献。
**风格**: 彩色层叠（每步增量形成一层从当前步延伸到右边的色带层）+ 阶梯连线 + 圆点 + 数值标注统一在上方 + 贡献信息图例。比传统瀑布图（仅柱+连线）多了"层叠"视觉隐喻。

```python
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

labels = ['Baseline', '+Attention', '+Augment', '+Pretrain', '-Dropout']
deltas = [0.82,        0.04,          0.02,       0.05,       -0.01]

cum = [deltas[0]]
for d in deltas[1:]:
    cum.append(cum[-1] + d)
final_val = cum[-1]
total_delta = final_val - deltas[0]

layer_colors = [COLORS['up'] if d >= 0 else COLORS['down'] for d in deltas[1:]]
n = len(labels)

fig, ax = plt.subplots(figsize=(9, 5))
ax.grid(axis='y', alpha=0.12, linestyle='-', color=COLORS['grid'])
ax.set_axisbelow(True)

x_positions = np.arange(n)

# ── 色带层叠（每步增量的层带位置，延伸到最右边）
for i in range(1, n):
    c = layer_colors[i - 1]
    bottom = min(cum[i-1], cum[i])
    top = max(cum[i-1], cum[i])
    ax.fill_between([x_positions[i] - 0.5, x_positions[-1] + 0.5], bottom, top,
                    alpha=0.15, color=c, zorder=1 + i)
    ax.plot([x_positions[i] - 0.5, x_positions[-1] + 0.5], [cum[i], cum[i]],
            color=c, linewidth=0.7, linestyle='--', alpha=0.35, zorder=1 + i)

# Baseline 底层
ax.fill_between([x_positions[0] - 0.5, x_positions[-1] + 0.5], 0, cum[0],
                alpha=0.06, color=PALETTE[0], zorder=0)

# ── 阶梯连线
ax.step(x_positions, cum, where='mid', color=PALETTE[0], linewidth=2.8, zorder=10)

# ── 圆点
for i in range(n):
    c = PALETTE[0] if i == 0 else layer_colors[i - 1]
    ax.scatter(x_positions[i], cum[i], color=c, s=90, zorder=11,
               edgecolors='white', linewidths=2.0)

# ── 数值标注 —— 所有步骤都标，统一放在圆点上方
for i in range(n):
    c = PALETTE[0] if i == 0 else layer_colors[i - 1]
    ax.text(x_positions[i], cum[i] + 0.008, f'{cum[i]:.3f}', ha='center', va='bottom',
            fontsize=8.5, fontweight='bold' if (i == 0 or i == n-1) else 'normal',
            color=c,
            bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                      edgecolor=c if (i == 0 or i == n-1) else 'none',
                      alpha=0.9, linewidth=0.5), zorder=12)

# ── 总增量标注（右上角）
ax.text(0.97, 0.95, f'Total: +{total_delta:.2f} (+{total_delta/deltas[0]*100:.1f}%)',
        transform=ax.transAxes, fontsize=9.5, ha='right', va='top',
        fontweight='bold', color=COLORS['up'],
        bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                  edgecolor=COLORS['up'], alpha=0.9, linewidth=1.0), zorder=15)

# ── 贡献图例（将贡献信息全部放在图例，而非图面上标）
legend_patches = []
for i in range(1, n):
    d = deltas[i]
    c = layer_colors[i - 1]
    sign = '+' if d >= 0 else ''
    pct = abs(d) / total_delta * 100
    patch = mpatches.Patch(facecolor=_lighten(c, 0.4), edgecolor=c, linewidth=1.2,
                           label=f'{labels[i]}  {sign}{d:.2f} ({pct:.0f}%)')
    legend_patches.append(patch)
legend = ax.legend(handles=legend_patches, loc='lower right',
                   frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8.5,
                   facecolor='white', title='Contribution', title_fontsize=9,
                   handlelength=1.5, handleheight=1.0)
legend.set_zorder(15)

ax.set_xticks(x_positions)
ax.set_xticklabels(labels, fontsize=10)
ax.set_ylabel('Accuracy', fontsize=11)
ax.set_xlim(-0.7, n - 0.3)
ax.set_ylim(deltas[0] * 0.92, final_val * 1.12)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_waterfall.pdf')
```

**⚠ 易踩的坑（彩色层叠瀑布图专用）：**
```python
# 1. 数值标注统一在圆点上方（va='bottom'），不要放在下方（色带层叠在下方会遮挡）
# 2. 首尾端点有边框 bbox，中间步骤无边框白底（视觉层次分明）
# 3. 贡献信息放图例而非图面：避免色带中间的标注和阶梯线重叠
# 4. ylim 上方留 12%，给最高点的标注留空间
# 5. 总增量标注用 transform=ax.transAxes 固定在右上角，不受数据范围影响
# 6. 色带 alpha=0.15：太深会让标注不清楚，太浅没有层次感
```


---

## 7. SHAP Summary Plot — SHAP 特征重要性图

**场景**: 特征对模型预测的影响。比普通特征重要性柱状图更丰富——同时展示方向和幅度。
**风格**: 浅色填充+原色边框 bars 用于重要性面板，coolwarm beeswarm 用于 SHAP 面板。

```python
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

np.random.seed(42)
features = ['Feature A', 'Feature B', 'Feature C', 'Feature D', 'Feature E']
n_samples = 200

fig = plt.figure(figsize=(9, 5))
gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1], wspace=0.05)

# Left panel: SHAP beeswarm
ax_shap = fig.add_subplot(gs[0])
ax_shap.grid(axis='x', alpha=0.15, linestyle='-', color=COLORS['grid'])
ax_shap.set_axisbelow(True)

mean_abs_shap = []
for i, feat in enumerate(features):
    shap_vals = np.random.randn(n_samples) * (len(features) - i) * 0.12
    feat_vals = np.random.rand(n_samples)
    y_jitter = np.random.uniform(-0.3, 0.3, n_samples) + i
    sc = ax_shap.scatter(shap_vals, y_jitter, c=feat_vals, cmap='coolwarm',
                         s=10, alpha=0.65, vmin=0, vmax=1, edgecolors='none')
    mean_abs_shap.append(np.mean(np.abs(shap_vals)))

ax_shap.set_yticks(range(len(features)))
ax_shap.set_yticklabels(features, fontsize=10)
ax_shap.set_xlabel('SHAP value (impact on prediction)', fontsize=10)
ax_shap.axvline(x=0, color=COLORS['ref_line'], linewidth=0.8, linestyle='--')
ax_shap.spines['top'].set_visible(False)
ax_shap.spines['right'].set_visible(False)

# Colorbar
cbar = plt.colorbar(sc, ax=ax_shap, shrink=0.5, pad=0.02, aspect=20)
cbar.set_label('Feature value', fontsize=8)
cbar.ax.tick_params(labelsize=7)

# Right panel: Mean |SHAP| importance bar —— 浅色填充 + 原色边框
ax_bar = fig.add_subplot(gs[1])
for i, v in enumerate(mean_abs_shap):
    is_top = (v == max(mean_abs_shap))
    c = PALETTE[0] if is_top else PALETTE[2]
    ax_bar.barh(i, v, color=_lighten(c, 0.4), edgecolor=c,
                linewidth=1.5, height=0.5, alpha=0.9)
    ax_bar.text(v + 0.002, i, f'{v:.3f}', va='center', fontsize=8, color=COLORS['text'])
ax_bar.set_yticks([])
ax_bar.set_xlabel('Mean |SHAP|', fontsize=9)
ax_bar.spines['top'].set_visible(False)
ax_bar.spines['right'].set_visible(False)
ax_bar.spines['left'].set_visible(False)

fig.tight_layout()
save_fig(fig, 'figures/fig_shap.pdf')
```

---

## 8. Bland-Altman Plot — Bland-Altman 一致性图（分层 CI 带 + 比例偏差线 + 异常值标签）

**场景**: 两种测量方法的一致性评估。医学/工程论文的标准图。

```python
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

np.random.seed(42)
method1 = np.random.normal(50, 10, 100)
method2 = method1 + np.random.normal(0.5, 3, 100)
mean_vals = (method1 + method2) / 2
diff_vals = method1 - method2
mean_diff = np.mean(diff_vals)
std_diff = np.std(diff_vals)

fig, ax = plt.subplots(figsize=(7, 5.5))

# Subtle grid
ax.grid(alpha=0.15, linestyle='-', color=COLORS['grid'])
ax.set_axisbelow(True)

# Gradient CI band (fading from center outward)
x_range = np.linspace(mean_vals.min() - 2, mean_vals.max() + 2, 200)
upper = mean_diff + 1.96 * std_diff
lower = mean_diff - 1.96 * std_diff
# Inner band (darker)
ax.fill_between(x_range, mean_diff - 0.5 * std_diff, mean_diff + 0.5 * std_diff,
                alpha=0.15, color=PALETTE[0], label='±0.5 SD')
# Middle band
ax.fill_between(x_range, mean_diff - 1.0 * std_diff, mean_diff + 1.0 * std_diff,
                alpha=0.10, color=PALETTE[0])
# Outer band (lightest)
ax.fill_between(x_range, lower, upper, alpha=0.06, color=PALETTE[3], label='±1.96 SD (95% CI)')

# Scatter points
ax.scatter(mean_vals, diff_vals, color=PALETTE[0], alpha=0.55, s=30,
           edgecolors='white', linewidths=0.5, zorder=3)

# Mean line
ax.axhline(mean_diff, color=PALETTE[0], linestyle='-', linewidth=1.8,
           label=f'Mean bias: {mean_diff:.2f}')
# Limits of agreement
ax.axhline(upper, color=PALETTE[3], linestyle='--', linewidth=1.2,
           label=f'+1.96 SD: {upper:.2f}')
ax.axhline(lower, color=PALETTE[3], linestyle='--', linewidth=1.2,
           label=f'-1.96 SD: {lower:.2f}')

# Proportional bias regression line
z = np.polyfit(mean_vals, diff_vals, 1)
p = np.poly1d(z)
x_fit = np.linspace(mean_vals.min(), mean_vals.max(), 100)
ax.plot(x_fit, p(x_fit), color=COLORS['highlight'], linewidth=1.5, linestyle='-.',
        label=f'Prop. bias (slope={z[0]:.3f})', zorder=4)

# Outlier labels (points beyond ±1.96 SD)
outliers = np.where((diff_vals > upper) | (diff_vals < lower))[0]
for idx in outliers:
    ax.annotate(f'#{idx}', xy=(mean_vals[idx], diff_vals[idx]),
                xytext=(mean_vals[idx] + 1.5, diff_vals[idx] + 0.8),
                fontsize=7, color=COLORS['down'],
                arrowprops=dict(arrowstyle='->', color=COLORS['down'], lw=0.8),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                          edgecolor=COLORS['down'], alpha=0.9))

ax.set_xlabel('Mean of two methods', fontsize=11)
ax.set_ylabel('Difference (Method 1 − Method 2)', fontsize=11)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=7.5, loc='upper left',
          fancybox=True)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_bland_altman.pdf')
```

**⚠ 易踩的坑（Bland-Altman Plot 专用）：**
```python
# 1. 异常值标签用 arrowprops 引线，标签不能离点太远也不能紧贴点位置
# 2. 当异常值聚集时，只标注最突出的 3-5 个，其余用红色圆点标记
# 3. 图例放 upper left（因为通常数据在中间偏右，不会遮挡散点）
# 4. CI 带标签放在图右边缘：ax.text(x_max, upper, ..., ha='left')
```

---

## 9. Kaplan-Meier Survival Curve — 生存曲线（CI 带 + 中位数标记 + 风险人数表 + Log-Rank p）

**场景**: 生存分析、设备寿命、用户留存。医学/可靠性论文必备。

```python
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

np.random.seed(42)
t_treat = np.sort(np.random.exponential(20, 50))
t_ctrl = np.sort(np.random.exponential(12, 50))

def km_curve_data(times):
    n = len(times)
    surv = np.ones(n + 1)
    t_plot = np.zeros(n + 1)
    for i, t in enumerate(times):
        surv[i + 1] = surv[i] * (n - i - 1) / (n - i)
        t_plot[i + 1] = t
    return t_plot, surv

def number_at_risk(times, time_points):
    return [np.sum(times >= tp) for tp in time_points]

fig = plt.figure(figsize=(8, 6))
gs = gridspec.GridSpec(2, 1, height_ratios=[4, 1], hspace=0.08)
ax = fig.add_subplot(gs[0])
ax_risk = fig.add_subplot(gs[1])

# Subtle grid
ax.grid(alpha=0.15, linestyle='-', color=COLORS['grid'])
ax.set_axisbelow(True)

# Treatment group
t1, s1 = km_curve_data(t_treat)
ax.step(t1, s1, where='post', color=PALETTE[0], linewidth=2.5, label='Treatment (n=50)')
# Gradient CI band
ci_upper = np.clip(s1 + 0.08 * np.sqrt(np.linspace(1, 0.1, len(s1))), 0, 1)
ci_lower = np.clip(s1 - 0.08 * np.sqrt(np.linspace(1, 0.1, len(s1))), 0, 1)
ax.fill_between(t1, ci_lower, ci_upper, step='post', alpha=0.12, color=PALETTE[0])

# Control group
t2, s2 = km_curve_data(t_ctrl)
ax.step(t2, s2, where='post', color=PALETTE[3], linewidth=2.5, label='Control (n=50)')
ci_upper2 = np.clip(s2 + 0.10 * np.sqrt(np.linspace(1, 0.1, len(s2))), 0, 1)
ci_lower2 = np.clip(s2 - 0.10 * np.sqrt(np.linspace(1, 0.1, len(s2))), 0, 1)
ax.fill_between(t2, ci_lower2, ci_upper2, step='post', alpha=0.12, color=PALETTE[3])

# Median survival markers with dashed lines
def find_median_survival(t_arr, s_arr):
    for i in range(len(s_arr) - 1):
        if s_arr[i] >= 0.5 and s_arr[i + 1] < 0.5:
            return t_arr[i + 1]
    return None

med_treat = find_median_survival(t1, s1)
med_ctrl = find_median_survival(t2, s2)

if med_treat is not None:
    ax.plot([med_treat, med_treat], [0, 0.5], '--', color=PALETTE[0], linewidth=1.0, alpha=0.7)
    ax.plot([0, med_treat], [0.5, 0.5], '--', color=PALETTE[0], linewidth=1.0, alpha=0.7)
    ax.scatter([med_treat], [0.5], color=PALETTE[0], s=60, zorder=5, marker='D',
               edgecolors='white', linewidths=1.0)
    ax.annotate(f'Median = {med_treat:.1f}m', xy=(med_treat, 0.5),
                xytext=(med_treat + 3, 0.58), fontsize=8, color=PALETTE[0],
                arrowprops=dict(arrowstyle='->', color=PALETTE[0], lw=0.8),
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))

if med_ctrl is not None:
    ax.plot([med_ctrl, med_ctrl], [0, 0.5], '--', color=PALETTE[3], linewidth=1.0, alpha=0.7)
    ax.plot([0, med_ctrl], [0.5, 0.5], '--', color=PALETTE[3], linewidth=1.0, alpha=0.7)
    ax.scatter([med_ctrl], [0.5], color=PALETTE[3], s=60, zorder=5, marker='D',
               edgecolors='white', linewidths=1.0)
    ax.annotate(f'Median = {med_ctrl:.1f}m', xy=(med_ctrl, 0.5),
                xytext=(med_ctrl + 3, 0.42), fontsize=8, color=PALETTE[3],
                arrowprops=dict(arrowstyle='->', color=PALETTE[3], lw=0.8),
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))

# Log-rank p-value annotation
ax.annotate('Log-rank p = 0.003',
            xy=(0.98, 0.98), xycoords='axes fraction', ha='right', va='top',
            fontsize=9, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.4', facecolor=_lighten(PALETTE[0], 0.7),
                      edgecolor=PALETTE[0], alpha=0.9))

ax.set_ylabel('Survival probability', fontsize=11)
ax.set_ylim(0, 1.05)
ax.set_xlim(left=0)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='best')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.set_xticklabels([])

# Number-at-risk table
time_points = np.arange(0, max(t_treat.max(), t_ctrl.max()) + 5, 10)
nar_treat = number_at_risk(t_treat, time_points)
nar_ctrl = number_at_risk(t_ctrl, time_points)

ax_risk.set_xlim(ax.get_xlim())
ax_risk.set_ylim(-0.5, 1.5)
for i, tp in enumerate(time_points):
    ax_risk.text(tp, 1, str(nar_treat[i]), ha='center', va='center',
                 fontsize=8, color=PALETTE[0], fontweight='bold')
    ax_risk.text(tp, 0, str(nar_ctrl[i]), ha='center', va='center',
                 fontsize=8, color=PALETTE[3], fontweight='bold')
ax_risk.text(-2, 1, 'Treatment', ha='right', va='center', fontsize=8,
             color=PALETTE[0], fontweight='bold')
ax_risk.text(-2, 0, 'Control', ha='right', va='center', fontsize=8,
             color=PALETTE[3], fontweight='bold')
ax_risk.set_xlabel('Time (months)', fontsize=11)
ax_risk.set_yticks([])
ax_risk.spines['top'].set_visible(False)
ax_risk.spines['right'].set_visible(False)
ax_risk.spines['left'].set_visible(False)
ax_risk.set_title('Number at risk', fontsize=8, loc='left', fontstyle='italic')

fig.tight_layout()
save_fig(fig, 'figures/fig_kaplan_meier.pdf')
```

**⚠ 易踩的坑（Kaplan-Meier Survival 专用）：**
```python
# 1. 中位数标注不要重叠：两组的标注分别放在 0.58 和 0.42 的 y 位置
# 2. log-rank p 值放在右上角，用 xycoords='axes fraction'
# 3. number-at-risk 表紧贴主图下方，用 hspace=0.08
# 4. 图例放 upper right（因为生存曲线从左上角开始下降）
```


---

## 10. Volcano Plot — 火山图（基因差异表达：渐变密度背景 + 基因标签 + 倍数变化阴影）

**场景**: 差异表达、特征选择。生物信息学/组学论文的标准图。

```python
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

np.random.seed(42)
n = 2000
log2fc = np.random.normal(0, 1.5, n)
pvals = 10 ** (-np.abs(log2fc) * np.random.uniform(0.5, 3, n))
neg_log_p = -np.log10(pvals)
gene_names = [f'Gene_{i}' for i in range(n)]

sig_up = (log2fc > 1) & (neg_log_p > 2)
sig_down = (log2fc < -1) & (neg_log_p > 2)
ns = ~sig_up & ~sig_down

fig, ax = plt.subplots(figsize=(7, 5.5))

# Gradient density background (hexbin)
hb = ax.hexbin(log2fc, neg_log_p, gridsize=30, cmap='Blues', alpha=0.25,
               mincnt=1, linewidths=0.0, zorder=0)

# Fold-change threshold shading
ax.axvspan(-1, 1, alpha=0.06, color=COLORS['ref_line'], zorder=0, label='|FC| < 2')
ax.axvspan(1, log2fc.max() + 1, alpha=0.04, color=PALETTE[3], zorder=0)
ax.axvspan(log2fc.min() - 1, -1, alpha=0.04, color=PALETTE[0], zorder=0)

# Subtle grid
ax.grid(alpha=0.15, linestyle='-', color=COLORS['grid'])
ax.set_axisbelow(True)

# Scatter points
ax.scatter(log2fc[ns], neg_log_p[ns], c=COLORS['neutral'], alpha=0.35, s=8,
           label=f'NS ({ns.sum()})', zorder=2)
ax.scatter(log2fc[sig_up], neg_log_p[sig_up], c=PALETTE[3], alpha=0.7, s=15,
           label=f'Up ({sig_up.sum()})', edgecolors='white', linewidths=0.3, zorder=3)
ax.scatter(log2fc[sig_down], neg_log_p[sig_down], c=PALETTE[0], alpha=0.7, s=15,
           label=f'Down ({sig_down.sum()})', edgecolors='white', linewidths=0.3, zorder=3)

# Threshold lines
ax.axhline(2, color=COLORS['ref_line'], linestyle='--', linewidth=0.8, alpha=0.7)
ax.axvline(1, color=COLORS['ref_line'], linestyle='--', linewidth=0.8, alpha=0.7)
ax.axvline(-1, color=COLORS['ref_line'], linestyle='--', linewidth=0.8, alpha=0.7)

# Gene labels for top hits (top 5 by significance)
all_sig = np.where(sig_up | sig_down)[0]
if len(all_sig) > 0:
    top_idx = all_sig[np.argsort(neg_log_p[all_sig])[-5:]]
    for idx in top_idx:
        ax.annotate(gene_names[idx],
                    xy=(log2fc[idx], neg_log_p[idx]),
                    xytext=(log2fc[idx] + 0.3 * np.sign(log2fc[idx]),
                            neg_log_p[idx] + 0.5),
                    fontsize=7, fontstyle='italic',
                    color=COLORS['text'],
                    arrowprops=dict(arrowstyle='->', color=COLORS['text'], lw=0.7),
                    bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                              edgecolor=COLORS['neutral'], alpha=0.85))

ax.set_xlabel('$\\log_2$(Fold Change)', fontsize=11)
ax.set_ylabel('$-\\log_{10}$(p-value)', fontsize=11)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8, loc='best',
          fancybox=True)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_volcano.pdf')
```

**⚠ 易踩的坑（Volcano Plot 专用）：**
```python
# 1. 上调/下调标签建议用 adjustText 或 smart_labels()，避免多个标签重叠遮挡
# 2. 只标注 top-5 最显著的点：不要标注所有显著点
# 3. 标签用 arrowprops 引线 + 白底 bbox，防止与散点混在一起
# 4. 阈值线标签放在图边缘，不要放在数据密集区域
```

---

## 11. Calibration Plot — 校准曲线（渐变 CI 带 + 底部直方图 + Brier Score 标注）

**场景**: 概率校准评估。比 ROC 更能反映模型在实际场景中的可靠性。

```python
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

np.random.seed(42)
bins = np.linspace(0, 1, 11)
bin_centers = (bins[:-1] + bins[1:]) / 2
model_a = np.clip(bin_centers + np.random.uniform(-0.05, 0.05, 10), 0, 1)
model_b = np.clip(bin_centers ** 0.7 + np.random.uniform(-0.03, 0.03, 10), 0, 1)

# Simulated predicted probabilities for histogram
pred_probs_a = np.clip(np.random.beta(2, 2, 500), 0, 1)
pred_probs_b = np.clip(np.random.beta(1.5, 3, 500), 0, 1)

# Brier scores
brier_a = 0.023
brier_b = 0.089

fig = plt.figure(figsize=(6, 7))
gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1], hspace=0.08)

# Top: Calibration curve
ax_cal = fig.add_subplot(gs[0])
ax_cal.grid(alpha=0.15, linestyle='-', color=COLORS['grid'])
ax_cal.set_axisbelow(True)

# Perfect calibration line
ax_cal.plot([0, 1], [0, 1], 'k--', linewidth=0.8, alpha=0.5, label='Perfect')

# Gradient CI band for Model A
ci_width_a = np.random.uniform(0.03, 0.07, 10)
ax_cal.fill_between(bin_centers, model_a - ci_width_a, model_a + ci_width_a,
                     alpha=0.15, color=PALETTE[0])
ax_cal.plot(bin_centers, model_a, 'o-', color=PALETTE[0], linewidth=2.2,
            markersize=7, label=f'Ours (Brier={brier_a:.3f})',
            markeredgecolor='white', markeredgewidth=1.0)

# Gradient CI band for Model B
ci_width_b = np.random.uniform(0.04, 0.09, 10)
ax_cal.fill_between(bin_centers, model_b - ci_width_b, model_b + ci_width_b,
                     alpha=0.12, color=PALETTE[3])
ax_cal.plot(bin_centers, model_b, 's--', color=PALETTE[3], linewidth=2.0,
            markersize=7, label=f'Baseline (Brier={brier_b:.3f})',
            markeredgecolor='white', markeredgewidth=1.0)

# Brier score annotation box
ax_cal.annotate(f'Brier Score\nOurs: {brier_a:.3f}\nBaseline: {brier_b:.3f}',
                xy=(0.05, 0.88), xycoords='axes fraction',
                fontsize=8.5, va='top',
                bbox=dict(boxstyle='round,pad=0.4', facecolor=_lighten(PALETTE[0], 0.7),
                          edgecolor=PALETTE[0], alpha=0.9))

ax_cal.set_ylabel('Fraction of positives', fontsize=11)
ax_cal.set_xlim(0, 1)
ax_cal.set_ylim(0, 1)
ax_cal.set_aspect('equal')
ax_cal.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8.5, loc='lower right')
ax_cal.spines['top'].set_visible(False)
ax_cal.spines['right'].set_visible(False)
ax_cal.set_xticklabels([])

# Bottom: Histogram of predicted probabilities
ax_hist = fig.add_subplot(gs[1])
ax_hist.hist(pred_probs_a, bins=20, alpha=0.5, color=PALETTE[0], label='Ours',
             edgecolor='white', linewidth=0.5)
ax_hist.hist(pred_probs_b, bins=20, alpha=0.4, color=PALETTE[3], label='Baseline',
             edgecolor='white', linewidth=0.5)
ax_hist.set_xlabel('Mean predicted probability', fontsize=11)
ax_hist.set_ylabel('Count', fontsize=10)
ax_hist.set_xlim(0, 1)
ax_hist.legend(frameon=False, fontsize=8)
ax_hist.spines['top'].set_visible(False)
ax_hist.spines['right'].set_visible(False)

fig.tight_layout()
save_fig(fig, 'figures/fig_calibration.pdf')
```

---

## 12. Funnel Plot — 漏斗图（Meta 分析：渐变 CI 带 90/95/99% + 研究标签 + Egger 检验）

**场景**: Meta 分析中的发表偏倚检测。医学/社会科学综述必备。

```python
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()
import matplotlib.pyplot as plt
import numpy as np

np.random.seed(42)
n_studies = 30
effects = np.random.normal(0.5, 0.3, n_studies)
se = np.random.uniform(0.05, 0.4, n_studies)
effects += np.random.normal(0, se)
study_names = [f'Study {i+1}' for i in range(n_studies)]

fig, ax = plt.subplots(figsize=(7, 5.5))

# Subtle grid
ax.grid(alpha=0.15, linestyle='-', color=COLORS['grid'])
ax.set_axisbelow(True)

mean_eff = np.mean(effects)
se_range = np.linspace(0, 0.45, 200)

# Gradient CI bands (99%, 95%, 90%)
ci_levels = [
    (2.576, '99% CI', PALETTE[2], 0.06),
    (1.960, '95% CI', PALETTE[1], 0.08),
    (1.645, '90% CI', PALETTE[0], 0.10),
]
for z_val, label, color, alpha in ci_levels:
    ax.fill_betweenx(se_range,
                      mean_eff - z_val * se_range,
                      mean_eff + z_val * se_range,
                      alpha=alpha, color=color, label=label)

# Pooled effect line
ax.axvline(mean_eff, color=PALETTE[0], linestyle='-', linewidth=1.8, alpha=0.6)

# Study points
ax.scatter(effects, se, color=PALETTE[0], s=50, alpha=0.8, edgecolors='white',
           linewidths=0.8, zorder=4)

# Study labels for outliers (outside 95% CI)
for i in range(n_studies):
    if abs(effects[i] - mean_eff) > 1.96 * se[i] * 1.5:
        ax.annotate(study_names[i],
                    xy=(effects[i], se[i]),
                    xytext=(effects[i] + 0.08, se[i] - 0.03),
                    fontsize=7, color=COLORS['down'],
                    arrowprops=dict(arrowstyle='->', color=COLORS['down'], lw=0.7),
                    bbox=dict(boxstyle='round,pad=0.15', facecolor=COLORS['bg_box'],
                              edgecolor=COLORS['down'], alpha=0.7))

# Egger's test annotation
ax.annotate("Egger's test: t = 1.42, p = 0.167\nNo significant asymmetry",
            xy=(0.02, 0.02), xycoords='axes fraction',
            fontsize=8, va='bottom',
            bbox=dict(boxstyle='round,pad=0.4', facecolor=_lighten(PALETTE[0], 0.7),
                      edgecolor=PALETTE[0], alpha=0.9))

ax.set_xlabel('Effect size', fontsize=11)
ax.set_ylabel('Standard error', fontsize=11)
ax.invert_yaxis()
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8, loc='best',
          fancybox=True)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_funnel.pdf')
```


---

## 13. Dot Plot with CI — 点图+置信区间（按显著性渐变着色 + 汇总菱形）

**场景**: 多方法多指标对比。比柱状图信息密度更高——同时展示显著性、汇总估计和各自的置信区间。Nature/Cell 风格。

```python
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten; from _utils.vivid_config import palette_colors
setup_style(); scale_colors = palette_colors()
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

methods = ['Ours', 'BERT', 'GPT-4', 'LLaMA', 'T5']
metrics = ['Acc', 'F1', 'Prec', 'Rec']
scores = np.array([[0.92, 0.90, 0.91, 0.89],
                    [0.88, 0.86, 0.89, 0.84],
                    [0.90, 0.88, 0.87, 0.90],
                    [0.85, 0.83, 0.86, 0.81],
                    [0.87, 0.85, 0.88, 0.83]])
ci = np.random.uniform(0.01, 0.03, scores.shape)

# Compute p-values (simulated) for gradient coloring
np.random.seed(42)
pvals = np.random.uniform(0.001, 0.1, scores.shape)
pvals[0, :] = np.random.uniform(0.001, 0.01, 4)  # Ours is most significant

fig, ax = plt.subplots(figsize=(8, 5))

# Subtle grid
ax.grid(axis='x', alpha=0.15, linestyle='-', color=COLORS['grid'])
ax.set_axisbelow(True)

y_base = np.arange(len(methods))
offsets = np.linspace(-0.25, 0.25, len(metrics))

# Gradient colormap for significance
cmap_sig = mcolors.LinearSegmentedColormap.from_list('sig', [scale_colors[1], scale_colors[4] if len(scale_colors) > 4 else scale_colors[0], scale_colors[2] if len(scale_colors) > 2 else scale_colors[0]])

for j, metric in enumerate(metrics):
    for i in range(len(methods)):
        # Color by significance (lower p = greener)
        sig_norm = min(pvals[i, j] / 0.1, 1.0)
        dot_color = cmap_sig(1 - sig_norm)
        ax.errorbar(scores[i, j], y_base[i] + offsets[j], xerr=ci[i, j],
                     fmt='o', color=dot_color, markersize=8, capsize=3,
                     linewidth=1.5, markeredgecolor='white', markeredgewidth=0.8,
                     label=metric if i == 0 else '', zorder=3)

# Pooled estimate diamond for each method
pooled = np.mean(scores, axis=1)
pooled_ci = np.mean(ci, axis=1)
for i in range(len(methods)):
    diamond_x = [pooled[i] - pooled_ci[i], pooled[i], pooled[i] + pooled_ci[i], pooled[i]]
    diamond_y = [y_base[i] + 0.35, y_base[i] + 0.42, y_base[i] + 0.35, y_base[i] + 0.28]
    ax.fill(diamond_x, diamond_y, color=PALETTE[0] if i == 0 else COLORS['ref_line'],
            alpha=0.7, zorder=4)
    ax.text(pooled[i] + pooled_ci[i] + 0.008, y_base[i] + 0.35,
            f'{pooled[i]:.3f}', fontsize=7, va='center', color=COLORS['text'])

ax.set_yticks(y_base)
ax.set_yticklabels(methods, fontsize=10)
ax.set_xlabel('Score', fontsize=11)

# Custom legend
from matplotlib.lines import Line2D
legend_elements = [Line2D([0], [0], marker='o', color='w', markerfacecolor=PALETTE[j],
                           markersize=8, label=metrics[j]) for j in range(len(metrics))]
legend_elements.append(Line2D([0], [0], marker='D', color='w', markerfacecolor=COLORS['ref_line'],
                               markersize=8, label='Pooled'))
ax.legend(handles=legend_elements, loc='lower right', frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8, ncol=3)
ax.invert_yaxis()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_dot_ci.pdf')
```

**⚠ 易踩的坑（Dot Plot with CI 专用）：**
```python
# 1. 数值标签统一放在 CI 右端再偏右：不要放在 CI 内部
# 2. pooled diamond 的标签放在 diamond 右侧：不要放在上方（避免与数据 CI 重叠）
# 3. 自适应高度：_fig_h = max(5, n_studies * 0.4 + 2)
# 4. 基线指标用虚线 axhline，不要用粗横线
```

---

## 14. Cluster Heatmap — 聚类热力图（带树状图 + 聚类边界 + 轮廓系数标注）

**场景**: 基因表达矩阵、特征相关性 + 层次聚类。增加聚类结构信息。
**⚠ 布局**: 只画列方向树状图（不画行方向树状图），避免遮挡 y 轴标签。使用 `fig.add_axes()` 手动分区（不要用 gridspec）。树状图和热力图的 left/width 参数完全一致。

```python
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten; from _utils.palette_maps import palette_cmap, palette_stops, contrast_text
setup_style()
import matplotlib.pyplot as plt
import numpy as np
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.spatial.distance import pdist

np.random.seed(42)
data = np.random.randn(10, 8)
labels_row = [f'Sample-{i+1}' for i in range(10)]
labels_col = [f'Feat-{i+1}' for i in range(8)]

Z_col = linkage(pdist(data.T), method='ward')
Z_row = linkage(pdist(data), method='ward')

n_clusters = 3
col_clusters = fcluster(Z_col, n_clusters, criterion='maxclust')
row_clusters = fcluster(Z_row, n_clusters, criterion='maxclust')

fig = plt.figure(figsize=(10, 8))

# ── 关键：树状图和热力图的 left 和 width 参数完全一致，否则会对不齐
# ── _left 需要足够容纳色条(左侧) + 间距 + y轴标签区域(至少 0.15)
_left = 0.22   # 长文本标签需要更大左边距
_width = 0.56
_cbar_left = _left + _width + 0.03

# 列树状图（只画列方向，不画行方向，避免遮挡标签）
ax_dendro_top = fig.add_axes([_left, 0.86, _width, 0.10])
dn_col = dendrogram(Z_col, ax=ax_dendro_top, leaf_font_size=0,
                     color_threshold=Z_col[-n_clusters + 1, 2],
                     above_threshold_color=COLORS['ref_line'])
ax_dendro_top.set_axis_off()

# Heatmap —— left 和 width 与树状图完全一致
ax_heat = fig.add_axes([_left, 0.08, _width, 0.76])
col_order = dn_col['leaves']
row_order = list(range(len(labels_row)))
ordered_data = data[row_order][:, col_order]

im = ax_heat.imshow(ordered_data, aspect='auto', cmap=palette_cmap('diverging'), interpolation='nearest')
ax_heat.set_xticks(range(len(labels_col)))
ax_heat.set_xticklabels([labels_col[i] for i in col_order], fontsize=8,
                         rotation=45, ha='right')
ax_heat.set_yticks(range(len(labels_row)))
ax_heat.set_yticklabels([labels_row[i] for i in row_order], fontsize=8)

# Cluster boundary lines
sorted_col_clusters = [col_clusters[i] for i in col_order]
for k in range(1, len(sorted_col_clusters)):
    if sorted_col_clusters[k] != sorted_col_clusters[k - 1]:
        ax_heat.axvline(k - 0.5, color='white', linewidth=2.5)
sorted_row_clusters = [row_clusters[i] for i in row_order]
for k in range(1, len(sorted_row_clusters)):
    if sorted_row_clusters[k] != sorted_row_clusters[k - 1]:
        ax_heat.axhline(k - 0.5, color='white', linewidth=2.5)

# Colorbar
ax_cbar = fig.add_axes([_cbar_left, 0.08, 0.02, 0.76])
cbar = plt.colorbar(im, cax=ax_cbar)
cbar.ax.tick_params(labelsize=8)

# Silhouette score annotation
ax_heat.text(0.98, 0.02, 'Silhouette = 0.42',
             transform=ax_heat.transAxes, fontsize=8, ha='right', va='bottom',
             bbox=dict(boxstyle='round,pad=0.3', facecolor=_lighten(PALETTE[0], 0.7),
                       edgecolor=PALETTE[0], alpha=0.9))

save_fig(fig, 'figures/fig_cluster_heatmap.pdf')
```

**⚠ 易踩的坑（聚类热力图专用）：**
```python
# 1. _left 取 0.22，给 y 轴标签 + 左侧色条留够空间（长文本标签需要更多）
# 2. 左侧色条放在 _left-0.05，色条右边界与热力图左边界之间留 0.025 间距
# 3. 树状图和热力图的 left/width 参数完全一致，否则会对不齐
# 4. ★ 行/样本聚类(需要行树状图)：不要把行标签留在左侧——左侧树状图的叶子连线会横穿标签文字。
#    正确做法：行树状图放最左、行标签移到热力图【右侧】(ax_heat.yaxis.tick_right())，两者彻底分开。
#    完整可跑代码见下方「变体：双向聚类热力图(带行树状图 + 标签移右侧)」。
#    (若只做列聚类、行不聚类，仍按上面主配方：只画列树状图、行标签留左侧即可。)
# 5. 此模板使用 add_axes 手动布局；保留其布局方式，局部调整位置后实际检查。
#    save_fig 不会自动调用 tight_layout 或移动面板，不依赖保存阶段修复间距。
# 6. 数值标注颜色需要适应：abs(val)>0.6 用白色字，其余用深色字
# 7. 长标签按可用空间换行、调整边距或采用有完整对应说明的简称。
#    若使用 auto_truncate_yticklabels，须确认不会损失类别辨识；不按固定字符数自动截断。
#    plot_utils._save 不会自动截断标签或减小字号，生成脚本需处理并检查边界。
# 8. 画布宽度、_left 和字号以原模板为起点，按数据标签与实际显示尺寸联合调整。
#    不设置统一宽度上限；调整后检查标签、树状图、热图和色条是否对齐且清楚。
```

**变体：双向聚类热力图（带行树状图 + 标签移右侧，不糊标签）**

**场景**：需要同时展示**行聚类**(样本/类别聚类)和列聚类，且行标签是中文/长文本。
关键：行树状图放最左，行标签移到热力图**右侧**，两者彻底分开——避免左侧树状图连线横穿标签。

```python
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
import matplotlib.pyplot as plt
import numpy as np
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.spatial.distance import pdist

# data: (n_row, n_col); labels_row 可为中文长标签; z-score 后 vmin/vmax 取 ±2
n_row, n_col = data.shape
Z_row = linkage(pdist(data), method='ward')
Z_col = linkage(pdist(data.T), method='ward')
n_clusters = 3
row_clusters = fcluster(Z_row, n_clusters, criterion='maxclust')
col_clusters = fcluster(Z_col, n_clusters, criterion='maxclust')

fig = plt.figure(figsize=(10, 7))
# 横向分区[左→右]: [行树状图][热力图][右侧标签(自动占位)][色条]
_heat_x, _heat_w, _bottom, _height = 0.19, 0.56, 0.10, 0.72

# 行树状图(左, orientation='left')
ax_dleft = fig.add_axes([0.05, _bottom, 0.12, _height])
dn_row = dendrogram(Z_row, ax=ax_dleft, orientation='left', no_labels=True,
                    color_threshold=Z_row[-n_clusters + 1, 2],
                    above_threshold_color=COLORS['ref_line'])
ax_dleft.invert_yaxis()          # ★ 让叶子[上→下]与 imshow(origin=upper) 同向
ax_dleft.set_axis_off()
row_order = dn_row['leaves']     # ★ invert 后 row_order = leaves 正序(勿加 [::-1]，否则行全错位)

# 列树状图(顶)
ax_dtop = fig.add_axes([_heat_x, 0.84, _heat_w, 0.11])
dn_col = dendrogram(Z_col, ax=ax_dtop, no_labels=True,
                    color_threshold=Z_col[-n_clusters + 1, 2],
                    above_threshold_color=COLORS['ref_line'])
ax_dtop.set_axis_off()
col_order = dn_col['leaves']

# 热力图(left/width 与列树状图完全一致，才对得齐)
ax_heat = fig.add_axes([_heat_x, _bottom, _heat_w, _height])
im = ax_heat.imshow(data[np.ix_(row_order, col_order)], aspect='auto',
                    cmap='coolwarm', interpolation='nearest', vmin=-2, vmax=2)
# ★ 行标签移到右侧，彻底避开左侧树状图连线
ax_heat.set_yticks(range(n_row))
ax_heat.set_yticklabels([labels_row[i] for i in row_order], fontsize=9)
ax_heat.yaxis.tick_right()
ax_heat.yaxis.set_tick_params(length=0)   # 去刻度线只留文字
ax_heat.set_xticks(range(n_col))
ax_heat.set_xticklabels([labels_col[i] for i in col_order], fontsize=8, rotation=45, ha='right')
for s in ax_heat.spines.values():
    s.set_visible(False)

# 聚类分界白线
srow = [row_clusters[i] for i in row_order]
for k in range(1, n_row):
    if srow[k] != srow[k - 1]:
        ax_heat.axhline(k - 0.5, color='white', linewidth=2.5)
scol = [col_clusters[i] for i in col_order]
for k in range(1, n_col):
    if scol[k] != scol[k - 1]:
        ax_heat.axvline(k - 0.5, color='white', linewidth=2.5)

# 色条(最右, 给右侧标签留出 0.75→0.90 的空间)
ax_cbar = fig.add_axes([0.90, _bottom, 0.02, _height])
cbar = plt.colorbar(im, cax=ax_cbar); cbar.ax.tick_params(labelsize=8)
cbar.set_label('成分含量 (列 z-score)', fontsize=9)

save_fig(fig, 'figures/fig_cluster_heatmap.pdf')
```

**⚠ 变体专用坑（已实跑验证）：**
```python
# A. ★★ row_order = dn_row['leaves'] 正序！配 invert_yaxis() 才对齐。
#    误写 leaves[::-1] 会让每一行的标签与数据错位(比"线穿字"更隐蔽、更严重)。
#    自检口诀: 若行有单调趋势(如亮度递增), 出图应看到从上到下大致分组连续。
# B. 行标签一定 yaxis.tick_right()；留在左侧必被树状图连线穿过(用户实测踩坑)。
# C. 右侧中文长标签: 色条左边界(0.90) 与热力图右边界(0.75) 之间留 0.15 给标签。
#    标签更长(>8 中文字)就把色条推到 0.92 或调小 _heat_w。
# D. 行/列树状图的 left/width 必须分别等于热力图的 left/width，否则叶子与格子对不齐。
```

---

## 15. Network Graph — 网络图（节点大小映射度 + 社区凸包 + 边权渐变）

**场景**: 引用网络、知识图谱、社交网络、因果关系。

```python
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten; from _utils.vivid_config import palette_colors
setup_style(); scale_colors = palette_colors()
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

try:
    import networkx as nx
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'networkx', '-q'])
    import networkx as nx

from scipy.spatial import ConvexHull

G = nx.karate_club_graph()
communities = list(nx.community.greedy_modularity_communities(G))

# Assign community colors
color_map = {}
for i, comm in enumerate(communities):
    for node in comm:
        color_map[node] = i
node_colors = [PALETTE[color_map[n] % len(PALETTE)] for n in G.nodes()]

# Node sizing by degree
degrees = dict(G.degree())
max_deg = max(degrees.values())
node_sizes = [400 * degrees[n] / max_deg + 80 for n in G.nodes()]

fig, ax = plt.subplots(figsize=(8, 7))
pos = nx.spring_layout(G, seed=42, k=0.5)

# Draw convex hulls for communities
for i, comm in enumerate(communities):
    if len(comm) >= 3:
        points = np.array([pos[n] for n in comm])
        try:
            hull = ConvexHull(points)
            hull_points = points[hull.vertices]
            # Close the polygon
            hull_points = np.vstack([hull_points, hull_points[0]])
            # Expand hull slightly
            centroid = points.mean(axis=0)
            expanded = centroid + 1.15 * (hull_points - centroid)
            ax.fill(expanded[:, 0], expanded[:, 1],
                    color=PALETTE[i % len(PALETTE)], alpha=0.08)
            ax.plot(expanded[:, 0], expanded[:, 1],
                    color=PALETTE[i % len(PALETTE)], linewidth=1.5,
                    linestyle='--', alpha=0.4)
        except Exception:
            pass

# Edge weight gradient
edges = G.edges()
edge_weights = [G[u][v].get('weight', 1) for u, v in edges]
max_w = max(edge_weights) if edge_weights else 1
cmap_edge = mcolors.LinearSegmentedColormap.from_list('ew', [_lighten(scale_colors[0], 0.8), COLORS['ref_line']])
for (u, v), w in zip(edges, edge_weights):
    x0, y0 = pos[u]
    x1, y1 = pos[v]
    norm_w = w / max_w
    ax.plot([x0, x1], [y0, y1], color=cmap_edge(norm_w),
            linewidth=0.5 + 1.5 * norm_w, alpha=0.3 + 0.4 * norm_w, zorder=1)

# Draw nodes
nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, node_size=node_sizes,
                        edgecolors='white', linewidths=1.2, alpha=0.9, zorder=3)

# Labels for high-degree nodes only
high_deg_nodes = {n: str(n) for n in G.nodes() if degrees[n] >= 4}
nx.draw_networkx_labels(G, pos, labels=high_deg_nodes, ax=ax,
                         font_size=7, font_color=COLORS['text'], font_weight='bold')

# Legend for communities
from matplotlib.lines import Line2D
legend_elements = [Line2D([0], [0], marker='o', color='w',
                           markerfacecolor=PALETTE[i % len(PALETTE)],
                           markersize=10, label=f'Community {i+1}')
                   for i in range(len(communities))]
ax.legend(handles=legend_elements, loc='upper left', frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8, fancybox=True)

ax.set_axis_off()
fig.tight_layout()
save_fig(fig, 'figures/fig_network.pdf')
```

**⚠ 易踩的坑（Network Graph 专用）：**
```python
# 1. 节点标签用 bbox 白底，防止和边线混在一起
# 2. 边权重标签只标注权重 > 中位数的边，不要每条边都标
# 3. 社区凸包用极浅色填充（alpha=0.08），不要遮挡节点和标签
# 4. 节点太密集时，fontsize 缩到 7，且只标注度数 top-5 的节点
```


---

## 16. Method Comparison Heatmap — 方法对比热力图（排名标注 🥇🥈🥉 + 树状图 + 列最优高亮 + 综合排名）

**场景**: 多方法 × 多指标对比矩阵。比柱状图更紧凑。Nature/Cell 风格。
**风格**: YlOrRd heatmap + 浅色填充+原色边框 用于列最优单元格 + 排名奖牌。

```python
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten; from _utils.palette_maps import palette_cmap, palette_stops, contrast_text
setup_style()
import matplotlib.pyplot as plt
import numpy as np
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist

methods = ['Ours', 'LSTM', 'Random Forest', 'Linear Reg']
metrics = ['MAE', 'RMSE', 'R2', 'MAPE(%)', 'Speed']
# Lower is better for MAE/RMSE/MAPE, higher for R2/Speed
data = np.array([
    [0.29, 1.05, 0.987, 2.1, 0.85],
    [72.23, 85.4, 0.812, 15.3, 0.60],
    [0.45, 1.82, 0.965, 3.8, 0.92],
    [137.08, 152.3, 0.421, 48.2, 0.98],
])
higher_better = [False, False, True, False, True]

# Rank medals
rank_symbols = ['🥇', '🥈', '🥉', '④']

# Normalize for color mapping
norm_data = np.zeros_like(data)
for j in range(data.shape[1]):
    col = data[:, j]
    if higher_better[j]:
        norm_data[:, j] = (col - col.min()) / (col.max() - col.min() + 1e-10)
    else:
        norm_data[:, j] = 1 - (col - col.min()) / (col.max() - col.min() + 1e-10)

# Compute overall ranking (average normalized rank)
overall_rank_score = np.mean(norm_data, axis=1)

# Add overall ranking column
metrics_ext = metrics + ['Overall']
data_ext = np.column_stack([data, overall_rank_score])
norm_ext = np.column_stack([norm_data, overall_rank_score / overall_rank_score.max()])

fig = plt.figure(figsize=(9, 4.5))

# Dendrogram on top
ax_dendro = fig.add_axes([0.15, 0.82, 0.65, 0.14])
Z = linkage(pdist(norm_data), method='ward')
dn = dendrogram(Z, labels=methods, ax=ax_dendro, leaf_font_size=0,
                color_threshold=0, above_threshold_color=COLORS['ref_line'])
ax_dendro.set_axis_off()
row_order = dn['leaves']

# Heatmap
ax = fig.add_axes([0.15, 0.12, 0.72, 0.68])
ordered_norm = norm_ext[row_order]
ordered_data = data_ext[row_order]
ordered_methods = [methods[i] for i in row_order]

im = ax.imshow(ordered_norm, cmap=palette_cmap('sequential'), aspect='auto', vmin=0, vmax=1)
ax.set_xticks(range(len(metrics_ext)))
ax.set_xticklabels(metrics_ext, fontsize=10)
ax.set_yticks(range(len(methods)))
ax.set_yticklabels(ordered_methods, fontsize=10)

# Annotate with values, ranks, and 浅色填充+原色边框 for best
for j in range(len(metrics_ext)):
    if j < len(metrics):
        col_vals = data[:, j]
        if higher_better[j]:
            rank_order = np.argsort(-col_vals)
        else:
            rank_order = np.argsort(col_vals)
    else:
        rank_order = np.argsort(-overall_rank_score)

    for i_orig, rank_pos in enumerate(rank_order):
        # Find position in ordered display
        i_display = row_order.index(rank_pos)
        if j < len(metrics):
            val_str = f'{data[rank_pos, j]:.2f}'
        else:
            val_str = f'{overall_rank_score[rank_pos]:.2f}'

        rank_idx = i_orig
        rank_label = rank_symbols[rank_idx] if rank_idx < len(rank_symbols) else ''

        color = contrast_text(im.cmap(im.norm(ordered_norm[i_display, j])))
        weight = 'bold' if rank_idx == 0 else 'normal'

        ax.text(j, i_display, f'{val_str}\n{rank_label}', ha='center', va='center',
                fontsize=8.5, fontweight=weight, color=color)

        # 列最优：浅色填充背景 + 原色粗边框
        if rank_idx == 0:
            rect = plt.Rectangle((j - 0.5, i_display - 0.5), 1, 1,
                                  linewidth=2.5, edgecolor=PALETTE[0],
                                  facecolor=_lighten(PALETTE[0], 0.5),
                                  alpha=0.3, zorder=4)
            ax.add_patch(rect)
            # 原色边框（不透明）
            rect_border = plt.Rectangle((j - 0.5, i_display - 0.5), 1, 1,
                                         linewidth=2.5, edgecolor=PALETTE[0],
                                         facecolor='none', zorder=5)
            ax.add_patch(rect_border)

ax.spines[:].set_visible(False)

# Colorbar
ax_cbar = fig.add_axes([0.89, 0.12, 0.02, 0.68])
cbar = plt.colorbar(im, cax=ax_cbar)
cbar.set_label('Normalized (1=best)', fontsize=8)
cbar.ax.tick_params(labelsize=7)

save_fig(fig, 'figures/fig_method_heatmap.pdf')
```

---

## 17. Parallel Coordinates — 平行坐标图（实线 + "本文"高亮 + 最优区域阴影）

**场景**: 多方法 × 多指标对比。每个指标是一条纵轴，每个方法是一条折线。交叉和分离一目了然。

```python
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()
import matplotlib.pyplot as plt
import numpy as np

methods = ['Ours', 'LSTM', 'Random Forest', 'Linear Reg']
metrics = ['MAE↓', 'RMSE↓', 'R²↑', 'Speed↑', 'Stability↑']
# All normalized to [0,1] where 1=best
data = np.array([
    [0.95, 0.92, 0.987, 0.85, 0.90],
    [0.45, 0.50, 0.812, 0.60, 0.65],
    [0.88, 0.82, 0.965, 0.92, 0.78],
    [0.10, 0.15, 0.421, 0.98, 0.55],
])

fig, ax = plt.subplots(figsize=(9, 5))
x = np.arange(len(metrics))

# Subtle grid
ax.grid(axis='y', alpha=0.15, linestyle='-', color=COLORS['grid'])
ax.set_axisbelow(True)

# Optimal region shading per axis (top 20%)
for j in range(len(metrics)):
    ax.fill_between([j - 0.3, j + 0.3], 0.8, 1.0, alpha=0.06,
                     color=COLORS['up'], zorder=0)
    ax.text(j, 0.82, '最优区', ha='center', fontsize=6, color=COLORS['up'],
            alpha=0.6, fontstyle='italic')

# Draw simple lines per method
for i, (method, row) in enumerate(zip(methods, data)):
    is_ours = (i == 0)

    if is_ours:
        # Thick solid line for "Ours"
        ax.plot(x, row, '-', color=PALETTE[0], linewidth=3.5, zorder=5,
                solid_capstyle='round')
        # Markers
        ax.scatter(x, row, color=PALETTE[0], s=100, zorder=6,
                   edgecolors='white', linewidths=1.5, marker='o')
        # Value labels
        for j, v in enumerate(row):
            ax.text(j, v + 0.04, f'{v:.2f}', ha='center', fontsize=8.5,
                    color=PALETTE[0], fontweight='bold')
        # Highlight label
        ax.text(x[-1] + 0.25, row[-1], f'★ {method}', va='center', fontsize=10,
                color=PALETTE[0], fontweight='bold')
    else:
        # Simple line for other methods
        ax.plot(x, row, '-', color=PALETTE[i], linewidth=1.5, alpha=0.6,
                solid_capstyle='round')
        ax.scatter(x, row, color=PALETTE[i], s=50, zorder=4, alpha=0.7,
                   edgecolors='white', linewidths=0.8)
        ax.text(x[-1] + 0.25, row[-1], method, va='center', fontsize=8.5,
                color=PALETTE[i], alpha=0.8)

ax.set_xticks(x)
ax.set_xticklabels(metrics, fontsize=10.5)
ax.set_ylabel('归一化得分 (1=最优)', fontsize=11)
ax.set_ylim(0, 1.12)
ax.set_xlim(-0.4, len(metrics) - 0.3)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_parallel_coords.pdf')
```


---

## 18. PCA Biplot — PCA 双标图（载荷箭头 + 智能标签 + 解释方差）

**场景**: 降维可视化、特征贡献分析。多元分析章节常用。
**防重叠**: 使用 `smart_labels()` 自动推开重叠的特征名标签——当多个载荷方向相近时尤为关键。

```python
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from _utils.plot_utils import setup_style, save_fig, PALETTE, smart_labels, auto_legend
setup_style()

# === Example data (replace with your PCA results) ===
np.random.seed(42)
n_samples, n_features = 80, 12
feature_names = ['市场规模', '供应链成熟度', '短期恢复能力', '响应梯度元素',
                 '长期恢复速度', '研发投入强度', '短期恢复弹性', '产能利用率',
                 '短期集中度', '专利授权量', '产业链完整度', '客户集中度']

# Simulated PCA scores and loadings
scores = np.random.randn(n_samples, 2) * 2
loadings = np.random.randn(n_features, 2)
loadings = loadings / np.abs(loadings).max(axis=0) * 3  # scale to [-3, 3]
explained_var = [66.3, 11.4]  # explained variance %

fig, ax = plt.subplots(figsize=(8, 7))

# Scatter: sample scores (gray, semi-transparent)
ax.scatter(scores[:, 0], scores[:, 1], s=25, alpha=0.35, color=COLORS['gray'],
           edgecolors='white', linewidths=0.3, zorder=2)

# Loading arrows
arrow_colors = []
for i, (name, lx, ly) in enumerate(zip(feature_names, loadings[:, 0], loadings[:, 1])):
    magnitude = np.sqrt(lx**2 + ly**2)
    color = PALETTE[0]
    arrow_colors.append(color)
    ax.annotate('', xy=(lx, ly), xytext=(0, 0),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.5, alpha=0.7))

# ── 特征名标签 —— smart_labels 自动推开重叠标签
# Offset labels slightly beyond arrow tips
label_xs = [lx * 1.08 for lx in loadings[:, 0]]
label_ys = [ly * 1.08 for ly in loadings[:, 1]]
smart_labels(ax, label_xs, label_ys, feature_names,
             colors=arrow_colors, fontsize=8.5, fontweight='bold',
             offset=(5, 0),
             bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                       edgecolor=PALETTE[0], alpha=0.8, linewidth=0.5),
             arrowprops=dict(arrowstyle='-', color=COLORS['grid'], lw=0.4),
             force_text=0.8, force_points=0.5)

# Reference lines
ax.axhline(0, color=COLORS['ref_line'], linewidth=0.5, alpha=0.4)
ax.axvline(0, color=COLORS['ref_line'], linewidth=0.5, alpha=0.4)

ax.set_xlabel(f'PC1 ({explained_var[0]:.1f}%)', fontsize=11)
ax.set_ylabel(f'PC2 ({explained_var[1]:.1f}%)', fontsize=11)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(alpha=0.1, linestyle='--')
fig.tight_layout()
save_fig(fig, 'figures/fig_pca_biplot.pdf')
```

**⚠ 易踩的坑（PCA Biplot 专用）：**
```python
# 1. Loading 箭头标签必须用 smart_labels()，箭头方向相近时标签一定会重叠
# 2. 箭头标签用白底 bbox，防止与散点混在一起
# 3. 散点用小尺寸（s=15-25）+ 低 alpha（0.4），给箭头和标签腾出视觉空间
# 4. 特征过多时，只标注最长的箭头，其余用数字 text 标注
```


---

## 19. Taylor Diagram — Taylor 图（多模型对比：相关系数 + 标准差 + RMSE）

**场景**: 在一张图中同时比较多个模型的三个统计指标（相关系数、标准差、RMSE）。气候科学、水文学、环境建模的标准图。比单纯的 RMSE 柱状图信息量大得多。
**风格**: 浅色填充+原色边框 用于模型标记点，RMSE 弧线用暖橙色。

```python
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Arc
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten, smart_labels
setup_style()

# === Example data (replace with your model evaluation results) ===
# Reference (observed) statistics
ref_std = 1.0  # normalized

# Model results: (correlation, normalized_std)
models = {
    'Ours':        (0.95, 1.02),
    'LSTM':        (0.88, 0.85),
    'XGBoost':     (0.91, 1.15),
    'SVR':         (0.82, 0.78),
    'Linear Reg':  (0.75, 1.30),
}

fig, ax = plt.subplots(figsize=(7, 7))

# Draw reference arcs (constant correlation lines)
max_std = 1.6
for corr in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]:
    theta = np.arccos(corr)
    r_vals = np.linspace(0, max_std, 100)
    x_arc = r_vals * np.cos(theta)
    y_arc = r_vals * np.sin(theta)
    ax.plot(x_arc, y_arc, color=COLORS['grid'], linewidth=0.5, alpha=0.6)
    ax.text(max_std * np.cos(theta) * 1.03, max_std * np.sin(theta) * 1.03,
            f'{corr}', fontsize=7, color=COLORS['ref_line'], ha='center', va='center',
            rotation=np.degrees(theta) - 90)

# Draw std arcs (centered at origin)
for s in [0.25, 0.5, 0.75, 1.0, 1.25, 1.5]:
    theta_range = np.linspace(0, np.pi / 2, 100)
    ax.plot(s * np.cos(theta_range), s * np.sin(theta_range),
            color=COLORS['grid'], linewidth=0.5, linestyle='--')

# Draw RMSE arcs (centered at reference point) —— 暖橙色
ref_x, ref_y = ref_std, 0
for rmse in [0.25, 0.5, 0.75, 1.0, 1.25]:
    theta_range = np.linspace(0, np.pi, 200)
    cx = ref_x + rmse * np.cos(theta_range)
    cy = rmse * np.sin(theta_range)
    mask = (cx >= 0) & (cy >= 0) & (np.sqrt(cx**2 + cy**2) <= max_std)
    if mask.any():
        ax.plot(cx[mask], cy[mask], color=COLORS['highlight'], linewidth=0.5,
                alpha=0.4, linestyle=':')

# Reference point
ax.scatter(ref_std, 0, s=150, color=COLORS['text'], marker='*', zorder=10, label='Observed')

# ── 绘制模型点：浅色填充+原色边框 标记
label_xs, label_ys, label_texts, label_colors = [], [], [], []
for i, (name, (corr, std)) in enumerate(models.items()):
    theta = np.arccos(corr)
    x = std * np.cos(theta)
    y = std * np.sin(theta)
    color = PALETTE[i % len(PALETTE)]
    marker = 'D' if i == 0 else 'o'
    size = 140 if i == 0 else 90
    # 浅色填充 + 原色边框
    ax.scatter(x, y, s=size, color=_lighten(color, 0.35), marker=marker, zorder=5,
               edgecolors=color, linewidths=1.8, label=name)
    label_xs.append(x); label_ys.append(y)
    label_texts.append(name); label_colors.append(color)

# Smart labels to avoid overlap
smart_labels(ax, label_xs, label_ys, label_texts, colors=label_colors,
             fontsize=8.5, fontweight='bold', offset=(8, 5))

ax.set_xlim(0, max_std)
ax.set_ylim(0, max_std)
ax.set_aspect('equal')
ax.set_xlabel('标准差（归一化）', fontsize=11)
ax.set_ylabel('标准差（归一化）', fontsize=11)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.legend(loc='upper left', fontsize=9, frameon=False, edgecolor=COLORS['grid'])
fig.tight_layout()
save_fig(fig, 'figures/fig_taylor.pdf')
```

---

## 20. Diverging Bar Chart — 发散柱状图（淡色填充 + 原色边框 + 相对基线 + 颜色编码方向 + 数值标签）

**场景**: 展示每个方法/变体相对于基线的表现（正值=更好，负值=更差）。比分组柱状图更清晰地传达"改进 vs 退化"的信息。常见于消融实验和敏感性分析。
**风格**: 方向性颜色背景区 + 浅色填充+原色边框柱体 + 阴影加粗 + 方向标注。

```python
import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten, smart_labels
setup_style()

methods = ['Ours (full)', 'w/o Attention', 'w/o Pretrain', 'w/o Augment',
           'Baseline-A', 'Baseline-B', 'Baseline-C']
deltas = [+5.2, +3.1, +1.8, +0.5, 0.0, -1.3, -2.7]

# ── 自适应高度
_fig_h = max(4, len(methods) * 0.7 + 1)
fig, ax = plt.subplots(figsize=(8, _fig_h))
y_pos = np.arange(len(methods))

# 方向性颜色背景
ax.axvspan(0, max(deltas)*1.3, alpha=0.05, color=COLORS['up'], zorder=0)
ax.axvspan(min(deltas)*1.3, 0, alpha=0.05, color=COLORS['down'], zorder=0)

# Color: positive = up(green), negative = down(red)
base_colors = [COLORS['up'] if d >= 0 else COLORS['down'] for d in deltas]

# 柱体阴影
ax.barh(y_pos + 0.03, deltas, height=0.5, color='#cccccc', alpha=0.1, zorder=1)
# ── 主柱体：浅色填充 + 原色边框
bars = ax.barh(y_pos, deltas, height=0.5,
               color=[_lighten(c, 0.4) for c in base_colors],
               edgecolor=base_colors, linewidth=1.5, zorder=3)

# Zero reference line
ax.axvline(0, color=COLORS['text'], linewidth=1.2, zorder=2)

# Value labels at bar ends（白底保护）
for i, (bar, d) in enumerate(zip(bars, deltas)):
    x_pos = d + (0.2 if d >= 0 else -0.2)
    ha = 'left' if d >= 0 else 'right'
    sign = '+' if d > 0 else ''
    ax.text(x_pos, y_pos[i], f'{sign}{d:.1f}%', va='center', ha=ha,
            fontsize=9, fontweight='bold', color=base_colors[i],
            bbox=dict(boxstyle='round,pad=0.1', facecolor='white', edgecolor='none', alpha=0.7))

# Highlight "Ours" row
ax.axhspan(y_pos[0]-0.35, y_pos[0]+0.35, alpha=0.06, color=PALETTE[0], zorder=0)
bars[0].set_edgecolor(PALETTE[0]); bars[0].set_linewidth(2.0)

# 方向标注
ax.text(0.98, 0.02, '更优 →', transform=ax.transAxes, fontsize=8, ha='right',
        color=COLORS['up'], fontweight='bold')
ax.text(0.02, 0.02, '← 更差', transform=ax.transAxes, fontsize=8, ha='left',
        color=COLORS['down'], fontweight='bold')

ax.set_yticks(y_pos)
ax.set_yticklabels(methods, fontsize=10)
ax.set_xlabel('Relative Improvement over Baseline (%)', fontsize=11)
ax.invert_yaxis()
ax.grid(axis='x', alpha=0.12, linestyle='--', color=COLORS['grid'])
ax.spines['left'].set_visible(False)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_diverging_bar.pdf')
```

---

## 21. Back-to-Back Bar Chart — 背靠背柱状图（浅色填充 + 原色边框 + 镜像对比 + 共享 Y 轴 + 差值标签）

**场景**: 两组/两种条件的镜像对比。经典"人口金字塔"风格。适合前后对比、男/女、训练/测试或任何二分对比。

```python
import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

categories = ['Accuracy', 'Precision', 'Recall', 'F1', 'AUC', 'MCC']
group_a = [92.3, 89.1, 94.5, 91.7, 96.2, 88.4]  # e.g., "Ours"
group_b = [87.5, 84.2, 90.1, 87.0, 93.1, 82.6]  # e.g., "Baseline"

# ── 自适应高度
_fig_h = max(4, len(categories) * 0.7 + 1)
fig, ax = plt.subplots(figsize=(8, _fig_h))
y_pos = np.arange(len(categories))

# ── 左侧（负方向）= Group B —— 浅色填充 + 原色边框
bars_b = ax.barh(y_pos, [-v for v in group_b], height=0.55,
                 color=_lighten(PALETTE[1], 0.4), edgecolor=PALETTE[1],
                 linewidth=1.2, label='Baseline', zorder=3)
# ── 右侧（正方向）= Group A —— 浅色填充 + 原色边框
bars_a = ax.barh(y_pos, group_a, height=0.55,
                 color=_lighten(PALETTE[0], 0.4), edgecolor=PALETTE[0],
                 linewidth=1.2, label='Ours', zorder=3)

# Value labels
for i in range(len(categories)):
    ax.text(group_a[i] + 0.5, y_pos[i], f'{group_a[i]:.1f}',
            va='center', ha='left', fontsize=8.5, color=PALETTE[0], fontweight='bold')
    ax.text(-group_b[i] - 0.5, y_pos[i], f'{group_b[i]:.1f}',
            va='center', ha='right', fontsize=8.5, color=PALETTE[1], fontweight='bold')
    # Gap label in center
    gap = group_a[i] - group_b[i]
    sign = '+' if gap > 0 else ''
    ax.text(0, y_pos[i], f'{sign}{gap:.1f}', va='center', ha='center',
            fontsize=7.5, fontweight='bold', color=COLORS['text'],
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                      edgecolor=COLORS['grid'], alpha=0.9))

ax.set_yticks(y_pos)
ax.set_yticklabels(categories, fontsize=10)
ax.axvline(0, color=COLORS['text'], linewidth=0.8)
ax.set_xlabel('Score (%)', fontsize=11)
ax.legend(loc='lower right', fontsize=9, frameon=False, edgecolor=COLORS['grid'])

# Clean up x-axis to show absolute values
ticks = ax.get_xticks()
ax.set_xticklabels([f'{abs(t):.0f}' for t in ticks])
ax.invert_yaxis()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='x', alpha=0.1, linestyle='--')
fig.tight_layout()
save_fig(fig, 'figures/fig_back2back.pdf')
```


---

## 22. Paired Dot Plot — 配对点图（个体变化连线 + 均值偏移箭头 + 显著性）

**场景**: 展示配对观测（同一受试者/样本在两种条件下的值）。每条线连接同一实体的前后值，揭示分组柱状图隐藏的个体差异。常见于医学、A/B 测试和实验设计论文。

```python
import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()

np.random.seed(42)
n = 20
labels = ['Before', 'After']
before = np.random.normal(75, 8, n)
after = before + np.random.normal(5, 4, n)  # general improvement with variance

fig, ax = plt.subplots(figsize=(5, 6))

# Individual paired lines
for i in range(n):
    color = PALETTE[0] if after[i] > before[i] else PALETTE[1]
    ax.plot([0, 1], [before[i], after[i]], color=color, alpha=0.35,
            linewidth=1.2, zorder=2)
    ax.scatter([0, 1], [before[i], after[i]], color=color, s=30,
               edgecolors='white', linewidths=0.5, zorder=3, alpha=0.6)

# Mean markers (large, prominent)
mean_before, mean_after = before.mean(), after.mean()
ax.scatter(0, mean_before, s=200, color=PALETTE[1], marker='D',
           edgecolors='white', linewidths=2, zorder=5, label=f'Mean Before: {mean_before:.1f}')
ax.scatter(1, mean_after, s=200, color=PALETTE[0], marker='D',
           edgecolors='white', linewidths=2, zorder=5, label=f'Mean After: {mean_after:.1f}')

# Mean shift arrow
ax.annotate('', xy=(1, mean_after), xytext=(0, mean_before),
            arrowprops=dict(arrowstyle='->', color=COLORS['text'], lw=2.5,
                            connectionstyle='arc3,rad=0.15'))
delta = mean_after - mean_before
ax.text(0.5, (mean_before + mean_after) / 2 + 2,
        f'Δ = +{delta:.1f}', ha='center', fontsize=10, fontweight='bold',
        color=PALETTE[0],
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                  edgecolor=PALETTE[0], alpha=0.9))

# Significance annotation
from scipy import stats
t_stat, p_val = stats.ttest_rel(after, before)
sig_text = f'p = {p_val:.4f}' if p_val >= 0.001 else 'p < 0.001'
ax.text(0.5, max(max(before), max(after)) + 4, sig_text,
        ha='center', fontsize=9, fontstyle='italic', color=COLORS['text'])

ax.set_xticks([0, 1])
ax.set_xticklabels(labels, fontsize=12, fontweight='bold')
ax.set_ylabel('Score', fontsize=11)
ax.set_xlim(-0.4, 1.4)
ax.legend(loc='lower right', fontsize=8, frameon=False, edgecolor=COLORS['grid'])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='y', alpha=0.1, linestyle='--')
fig.tight_layout()
save_fig(fig, 'figures/fig_paired_dot.pdf')
```

**⚠ 易踩的坑（Paired Dot Plot 专用）：**
```python
# 1. 显著性标注不要与数据点重叠：放在 y 位置 = max(data) + offset
# 2. 均值偏移箭头放在图右侧空白区域，不要穿过数据点之间
# 3. 个体变化线用低 alpha（0.3），不要遮挡均值标记
# 4. p 值标注放在数据上方（fontsize=8），不要太大
```

---

## 23. Ridgeline Plot — 山脊图（堆叠分布对比 + 渐变填充 + 中位数线）

**场景**: 在紧凑布局中比较多组（5-15 组）的分布。每组有自己的密度曲线，垂直方向略有重叠。比多个直方图或小提琴图更节省空间。在数据新闻和学术论文中越来越流行。

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
groups = ['Model A', 'Model B', 'Model C', 'Model D', 'Model E',
          'Model F', 'Model G', 'Model H']
n_groups = len(groups)

# Generate sample data (replace with real data)
data = []
for i in range(n_groups):
    center = 70 + i * 3 + np.random.randn() * 2
    spread = 5 + np.random.rand() * 5
    d = np.random.normal(center, spread, 200)
    data.append(d)

fig, ax = plt.subplots(figsize=(8, 6))
overlap = 0.6  # vertical overlap factor
x_grid = np.linspace(min(d.min() for d in data) - 5,
                      max(d.max() for d in data) + 5, 300)

for i in range(n_groups - 1, -1, -1):  # draw back to front
    kde = gaussian_kde(data[i], bw_method=0.3)
    density = kde(x_grid)
    # Normalize density to consistent height
    density = density / density.max() * 0.8

    baseline = i * overlap
    color = PALETTE[i % len(PALETTE)]
    light = _lighten(color, 0.5)

    # Gradient fill
    ax.fill_between(x_grid, baseline, baseline + density,
                    color=light, alpha=0.85, zorder=n_groups - i)
    ax.plot(x_grid, baseline + density, color=color, linewidth=1.5,
            zorder=n_groups - i + 0.5)

    # Median line
    median = np.median(data[i])
    med_density = kde(median)[0] / density.max() * 0.8
    ax.plot([median, median], [baseline, baseline + med_density],
            color=color, linewidth=1.5, linestyle='--', alpha=0.7,
            zorder=n_groups - i + 1)
    ax.text(median, baseline + med_density + 0.02,
            f'{median:.1f}', ha='center', fontsize=7, color=color,
            fontweight='bold', zorder=n_groups + 10)

    # Group label
    ax.text(x_grid[0] - 1, baseline + 0.15, groups[i],
            ha='right', va='center', fontsize=9, fontweight='bold',
            color=color)

ax.set_yticks([])
ax.set_xlabel('Score', fontsize=11)
ax.spines['left'].set_visible(False)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_ridgeline.pdf')
```

**⚠ 易踩的坑（Ridgeline Plot 专用）：**
```python
# 1. 相邻密度曲线的 y 间距 ≥ 2.5：太密会导致曲线互相遮挡
# 2. 中位数线标签放在曲线右侧：不要放在曲线内部
# 3. Shapiro-Wilk 标注放在数据右端再偏右：用 bbox 白底
# 4. 组数 >8 时，自适应高度 _fig_h = max(6, n_groups * 1.2 + 1)
```

---

## 24. Grouped Violin Plot (Multi-Group Distribution Comparison + Median + Quartile Lines)

**Use case**: Compare distribution shapes across 2-4 groups for multiple categories. More compact than Rain Cloud when you have many categories. Shows full distribution shape unlike box plots.

```python
import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
categories = ['Dataset A', 'Dataset B', 'Dataset C', 'Dataset D']
group_names = ['Ours', 'Baseline-1', 'Baseline-2']
n_groups = len(group_names)

# Generate sample data (replace with real results)
all_data = {}
for g, gname in enumerate(group_names):
    all_data[gname] = []
    for c in range(len(categories)):
        center = 80 + g * (-3) + c * 2 + np.random.randn()
        d = np.random.normal(center, 3 + g, 50)
        all_data[gname].append(d)

fig, ax = plt.subplots(figsize=(9, 5))
width = 0.25
positions_base = np.arange(len(categories))

for g, gname in enumerate(group_names):
    positions = positions_base + (g - n_groups / 2 + 0.5) * width
    color = PALETTE[g % len(PALETTE)]
    light = _lighten(color, 0.4)

    parts = ax.violinplot(all_data[gname], positions=positions,
                          widths=width * 0.85, showmeans=False,
                          showmedians=False, showextrema=False)

    for pc in parts['bodies']:
        pc.set_facecolor(light)
        pc.set_edgecolor(color)
        pc.set_linewidth(1.2)
        pc.set_alpha(0.8)

    # Add median + quartile lines manually
    for i, d in enumerate(all_data[gname]):
        q1, med, q3 = np.percentile(d, [25, 50, 75])
        pos = positions[i]
        # Median dot
        ax.scatter(pos, med, color=color, s=30, zorder=5,
                   edgecolors='white', linewidths=0.8)
        # Quartile whisker
        ax.vlines(pos, q1, q3, color=color, linewidth=2.5, zorder=4)

    # Invisible scatter for legend
    ax.scatter([], [], color=color, s=60, label=gname, edgecolors='white')

ax.set_xticks(positions_base)
ax.set_xticklabels(categories, fontsize=10)
ax.set_ylabel('Score', fontsize=11)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='y', alpha=0.1, linestyle='--')
fig.tight_layout()
save_fig(fig, 'figures/fig_grouped_violin.pdf')
```


---

## 25. Performance Profile (Dolan-Moré) — 性能剖面图（多算法跨问题对比标准画法）

**场景**: 优化 / OR / AI 算法对比。横轴 τ 表示"相对最优解的倍数"，纵轴 ρ(τ) 表示"在 τ 倍最优内解出问题的比例"。曲线越靠左上越好。Dolan & Moré (2002) 的事实标准画法。

⛔ **不要画成普通 ECDF**：必须是阶梯函数（step），横轴对数刻度，左端 ρ(1) = "求解器找到最优解的问题比例"。

```python
import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()
np.random.seed(42)

# === 模拟数据：5 个算法在 30 个问题上的求解时间 ===
n_problems = 30
algos = ['本文方法', 'Baseline A', 'Baseline B', 'Baseline C', 'Heuristic']
# 每行一个问题，每列一个算法的求解时间
times = np.abs(np.random.lognormal(0, 0.6, (n_problems, len(algos))))
times[:, 0] *= 0.7   # 本文方法更快
times[10:15, 2] = np.inf  # Baseline B 有 5 个失败
times[5:8, 3] = np.inf    # Baseline C 失败 3 个

# === 计算 performance ratio ===
best = np.nanmin(np.where(np.isinf(times), np.nan, times), axis=1, keepdims=True)
rp = times / best  # 每问题每算法的相对比率
rp[np.isinf(times)] = np.inf

# === 计算累计分布 ρ_s(τ) = #{p : rp(p,s) ≤ τ} / n_problems ===
tau_grid = np.logspace(0, 1.0, 200)  # τ ∈ [1, 10]
rho = np.zeros((len(tau_grid), len(algos)))
for s in range(len(algos)):
    for i, tau in enumerate(tau_grid):
        rho[i, s] = np.mean(rp[:, s] <= tau)

fig, ax = plt.subplots(figsize=(7, 4.5))

markers = ['o', 's', '^', 'D', 'v']
for s, name in enumerate(algos):
    is_self = (s == 0)
    lw = 2.4 if is_self else 1.4
    alpha = 1.0 if is_self else 0.78
    # ★ 阶梯函数 — drawstyle='steps-post' 是 Dolan-Moré 标准
    ax.step(tau_grid, rho[:, s], where='post',
            color=PALETTE[s % len(PALETTE)],
            linewidth=lw, alpha=alpha,
            marker=markers[s % len(markers)], markersize=5,
            markevery=20, markeredgecolor='white', markeredgewidth=0.6,
            label=name + (' ★' if is_self else ''))

# ★ τ=1 处的左端值标注（"找到最优的比例"）
for s, name in enumerate(algos):
    rho0 = rho[0, s]
    if rho0 > 0.05:
        ax.text(1.02, rho0, f'{rho0:.2f}', fontsize=7,
                color=PALETTE[s % len(PALETTE)], va='center', ha='left',
                bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                          edgecolor=PALETTE[s % len(PALETTE)], alpha=0.85, linewidth=0.4))

# ★ "完美求解器"参考线（理论上限 ρ=1）
ax.axhline(1.0, color=COLORS['ref_line'], linestyle=':', linewidth=0.8, alpha=0.5)
ax.text(tau_grid[-1] * 0.95, 1.01, 'Ideal solver (ρ=1)',
        fontsize=7, color=COLORS['ref_line'], ha='right', va='bottom', style='italic')

# ★ 灰色背景区暗示"τ=1 = 全部找到最优"是稀有的
ax.axvspan(1.0, 1.05, alpha=0.08, color=COLORS['highlight'], zorder=0)

ax.set_xscale('log')
ax.set_xlim(1.0, tau_grid[-1])
ax.set_ylim(0, 1.05)
ax.set_xlabel(r'性能比率 $\tau$ (相对最优解的倍数, log scale)', fontsize=10)
ax.set_ylabel(r'$\rho_s(\tau)$  (在 $\tau$ 倍内解出的问题比例)', fontsize=10)
ax.legend(loc='lower right', frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8)
ax.grid(which='both', alpha=0.12, linestyle='--', color=COLORS['grid'])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_perf_profile.pdf')
```

**★ 解读要点：**
- **左端 ρ(1)** = 该算法找到全局最优的问题比例 → "鲁棒性"
- **右端 ρ(∞)** = 该算法成功求解的问题比例（不含 inf）→ "稳定性"
- **曲线越靠左上越好**（同样 τ 解出更多问题）
- **两条曲线相交**：交点处说明"宽松的 τ 下 A 更好，严格的 τ 下 B 更好"

**★ 易错点：**
- ⛔ 不要用 `plt.plot` 画平滑线 — 必须 `step(where='post')`，否则会误导读者认为"任意 τ 都有数据"
- ⛔ 不要省略对数横轴 — τ 跨越多个数量级时线性轴会挤成一团
- ⛔ inf 时间必须当成"问题未解出"处理（不参与 best 计算），否则会扭曲曲线

---

## 26. ICE + PDP — 可解释机器学习（多条 ICE 细线 + 粗 PDP 均值线 + 边际分布）

**场景**: 黑箱模型可解释性分析。**ICE (Individual Conditional Expectation)** 显示每个样本随特征变化的预测路径，**PDP (Partial Dependence Plot)** 是 ICE 的均值。配合底部特征分布直方图，告诉读者"PDP 在哪个 x 范围有数据支撑"。

```python
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()
np.random.seed(42)

# === 模拟 ICE 曲线（200 个样本，特征 x 从 0 到 10）===
n_samples = 200
x_grid = np.linspace(0, 10, 80)
# 每个样本的随机基线 + 非线性形状
baselines = np.random.normal(0.5, 0.15, n_samples)
shape_strength = np.random.normal(1.0, 0.25, n_samples)
ice_curves = np.array([
    baselines[i] + shape_strength[i] * (0.45 / (1 + np.exp(-1.2*(x_grid - 4))) + 0.08 * np.sin(x_grid * 0.6))
    + np.random.normal(0, 0.02, len(x_grid))
    for i in range(n_samples)
])
pdp = ice_curves.mean(axis=0)
pdp_ci_lo = np.percentile(ice_curves, 5, axis=0)
pdp_ci_hi = np.percentile(ice_curves, 95, axis=0)

# 样本特征分布（边际）
x_samples = np.random.beta(2.5, 2.0, n_samples * 3) * 10  # 中心偏左的分布

# === 双面板：上 ICE+PDP，下 边际分布 ===
fig = plt.figure(figsize=(7, 5.2))
gs = GridSpec(2, 1, height_ratios=[4, 1], hspace=0.04)
ax = fig.add_subplot(gs[0])
ax_marg = fig.add_subplot(gs[1], sharex=ax)

# ★ ICE 细线（每条 alpha 极低，重叠出"密度感"）
for i in range(n_samples):
    ax.plot(x_grid, ice_curves[i], color=PALETTE[0], linewidth=0.5, alpha=0.06, zorder=1)

# ★ PDP 95% CI 带（外层浅、内层稍深）
ax.fill_between(x_grid, pdp_ci_lo, pdp_ci_hi, color=_lighten(PALETTE[0], 0.55),
                alpha=0.45, linewidth=0, zorder=2, label='90% 区间')

# ★ PDP 中位数线 — 主信号
ax.plot(x_grid, pdp, color=PALETTE[0], linewidth=2.6, zorder=3, label='PDP (均值)')
# 加白色描边让曲线在 ICE 海里更突出
ax.plot(x_grid, pdp, color='white', linewidth=4.5, zorder=2.5, alpha=0.6)
ax.plot(x_grid, pdp, color=PALETTE[0], linewidth=2.6, zorder=3)

# ★ 拐点标注
turn_idx = np.argmax(np.abs(np.gradient(pdp)))
ax.scatter([x_grid[turn_idx]], [pdp[turn_idx]], s=80, color=COLORS['highlight'],
           edgecolor='white', linewidth=1.5, zorder=5, marker='o')
ax.annotate(f'拐点\n(x={x_grid[turn_idx]:.1f})',
            xy=(x_grid[turn_idx], pdp[turn_idx]),
            xytext=(15, 18), textcoords='offset points',
            fontsize=8, fontweight='bold', color=COLORS['highlight'],
            arrowprops=dict(arrowstyle='->', color=COLORS['highlight'], lw=1.1, alpha=0.7),
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                      edgecolor=COLORS['highlight'], alpha=0.9, linewidth=0.6))

ax.set_ylabel('预测值 (P(y=1))', fontsize=10)
ax.legend(loc='lower right', frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.tick_params(axis='x', labelbottom=False)
ax.grid(axis='y', alpha=0.1, linestyle='--', color=COLORS['grid'])

# ★ 底部 rug + 直方图：告诉读者 PDP 在哪些 x 上有数据
ax_marg.hist(x_samples, bins=40, color=_lighten(PALETTE[0], 0.4), alpha=0.85,
             edgecolor=PALETTE[0], linewidth=0.4)
ax_marg.set_xlabel('特征 x', fontsize=10)
ax_marg.set_ylabel('样本密度', fontsize=8)
ax_marg.spines['top'].set_visible(False)
ax_marg.spines['right'].set_visible(False)
ax_marg.tick_params(axis='y', labelsize=7)

save_fig(fig, 'figures/fig_ice_pdp.pdf')
```

**★ 设计要点：**
- **ICE alpha=0.06**：单条几乎看不见，重叠后形成"密度感"，凸显异质性
- **PDP 白色描边 + 主色双层叠加**：在 ICE 海里凸显主信号
- **底部边际分布**：让读者知道"PDP 在 x=8 之后的下降是基于多少数据"

---

## 27. Fan Chart — 预测扇形图（多层 CI 带 + 历史/预测分隔 + 中位数线）

**场景**: 经济预测、能源需求、流行病传播、气候情景。央行（英格兰银行）首创的可视化标准。多层颜色带 50% / 80% / 95% 分位数，历史区实线，预测区虚线/中心。

```python
import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()
np.random.seed(42)

# === 模拟时序：历史 24 个月 + 预测 12 个月 ===
n_hist = 24; n_pred = 12
t = np.arange(n_hist + n_pred)
hist = 100 + np.cumsum(np.random.normal(0, 1.5, n_hist))
# 预测：均值随机游走，方差随时间扩散
pred_mean = hist[-1] + np.cumsum(np.random.normal(0.3, 0.5, n_pred))
pred_std = np.sqrt(np.arange(1, n_pred + 1)) * 1.6   # 不确定性随时间增长

# 预测分位数
quantiles = {
    'p05': pred_mean - 1.96 * pred_std, 'p95': pred_mean + 1.96 * pred_std,
    'p10': pred_mean - 1.28 * pred_std, 'p90': pred_mean + 1.28 * pred_std,
    'p25': pred_mean - 0.67 * pred_std, 'p75': pred_mean + 0.67 * pred_std,
}

fig, ax = plt.subplots(figsize=(8, 4.5))

# === 历史段：实线 ===
ax.plot(t[:n_hist], hist, color=COLORS['text'], linewidth=1.8, zorder=4, label='历史值')
ax.scatter(t[n_hist-1], hist[-1], s=50, color=COLORS['text'], zorder=5,
           edgecolor='white', linewidth=1)

# === 预测段：多层 CI 带（外到内 alpha 递增）===
t_pred = t[n_hist-1:]
# 拼接：起点用历史最后值，让带子接续
pred_full = np.concatenate(([hist[-1]], pred_mean))
quant_full = {k: np.concatenate(([hist[-1]], v)) for k, v in quantiles.items()}

# 5%-95%（外层，最浅）
ax.fill_between(t_pred, quant_full['p05'], quant_full['p95'],
                color=_lighten(PALETTE[0], 0.65), alpha=0.55, linewidth=0,
                label='95% 区间', zorder=1)
# 10%-90%
ax.fill_between(t_pred, quant_full['p10'], quant_full['p90'],
                color=_lighten(PALETTE[0], 0.4), alpha=0.7, linewidth=0,
                label='80% 区间', zorder=2)
# 25%-75%（内层，最深）
ax.fill_between(t_pred, quant_full['p25'], quant_full['p75'],
                color=_lighten(PALETTE[0], 0.2), alpha=0.8, linewidth=0,
                label='50% 区间', zorder=3)
# 中位数预测线（虚线区别历史）
ax.plot(t_pred, pred_full, color=PALETTE[0], linewidth=1.8, linestyle='--', zorder=4,
        label='中位数预测')

# === 历史/预测分隔线 ===
ax.axvline(n_hist - 1, color=COLORS['ref_line'], linestyle=':', linewidth=1.1, alpha=0.6)
ax.text(n_hist - 1, ax.get_ylim()[1] * 0.97 if False else hist.max() * 1.02,
        '预测起点', fontsize=8, ha='center', va='bottom',
        color=COLORS['ref_line'], style='italic',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                  edgecolor=COLORS['grid'], alpha=0.9, linewidth=0.4))

# === 终点不确定性范围标注 ===
y_min = quant_full['p05'][-1]; y_max = quant_full['p95'][-1]
ax.annotate('', xy=(t[-1] + 0.2, y_min), xytext=(t[-1] + 0.2, y_max),
            arrowprops=dict(arrowstyle='<->', color=COLORS['highlight'], lw=1.2))
ax.text(t[-1] + 0.8, (y_min + y_max) / 2,
        f'95% 跨度\n{y_max - y_min:.1f}', fontsize=8, va='center',
        color=COLORS['highlight'], fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                  edgecolor=COLORS['highlight'], alpha=0.9, linewidth=0.5))

ax.set_xlabel('时间（月）', fontsize=10)
ax.set_ylabel('指标值', fontsize=10)
ax.legend(loc='upper left', frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8, ncol=2)
ax.grid(axis='y', alpha=0.12, linestyle='--', color=COLORS['grid'])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.set_xlim(0, t[-1] + 3)
fig.tight_layout()
save_fig(fig, 'figures/fig_fan_chart.pdf')
```

**★ 设计要点：**
- **多层 CI 用 `_lighten(PALETTE[0], k)` 渐变** 而非透明度叠加（避免颜色脏）
- **历史 实线 + 预测 虚线**：让读者一眼区分"已知"和"推断"
- **分隔线 + 文字标签**：明确"哪里开始是预测"

---

## 28. Calendar Heatmap — 日历热图（一年 7×53 网格 + 月份分隔 + 顶部色条）

**场景**: 时序观察（每日数据：交易量、能耗、降雨、用户活跃）。GitHub 贡献图风格。一眼看出周期性 / 节假日 / 异常日。

```python
import numpy as np; from _utils.vivid_config import palette_colors
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.colors import LinearSegmentedColormap
from datetime import date, timedelta
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style(); scale_colors = palette_colors()
np.random.seed(42)

# === 模拟一年的日数据（周末偏低，月底偏高，几个事件峰值）===
start = date(2024, 1, 1)
n_days = 366
daily = np.random.gamma(2.0, 1.2, n_days)  # 基线
for i in range(n_days):
    d = start + timedelta(days=i)
    if d.weekday() >= 5: daily[i] *= 0.55  # 周末
    if d.day >= 28: daily[i] *= 1.3  # 月底
# 几个事件峰值
for ev in [40, 95, 180, 290]:
    daily[ev:ev+3] *= 2.5

# === 转 7×53 矩阵：行=周中第几天（周一-周日），列=年中第几周 ===
grid = np.full((7, 54), np.nan)
month_starts = []  # 记录每月第一天位置（用于画分隔线）
for i in range(n_days):
    d = start + timedelta(days=i)
    week = int(d.strftime('%W'))  # ISO 周
    weekday = d.weekday()  # 0=Mon
    grid[weekday, week] = daily[i]
    if d.day == 1:
        month_starts.append((d.month, week, weekday))

# === 主色调渐变 colormap（用原色序首色的浅→深）===
base = scale_colors[0]
cmap_calendar = LinearSegmentedColormap.from_list(
    'cal', [_lighten(base, 0.92), _lighten(base, 0.5), base, _lighten(base, -0.15) if False else base],
    N=128
)

fig, ax = plt.subplots(figsize=(11, 2.6))
im = ax.imshow(grid, aspect='equal', cmap=cmap_calendar, vmin=0,
               vmax=np.nanpercentile(grid, 98))

# === 月份分隔线 + 月名标注 ===
month_names = ['1月', '2月', '3月', '4月', '5月', '6月',
               '7月', '8月', '9月', '10月', '11月', '12月']
for m, wk, _ in month_starts:
    ax.axvline(wk - 0.5, color=COLORS['grid'], linewidth=0.8, alpha=0.5)
    ax.text(wk + 0.5, -1.0, month_names[m - 1], fontsize=8,
            ha='left', va='center', color=COLORS['text'])

# === Y 轴：仅显示 Mon / Wed / Fri ===
ax.set_yticks([0, 2, 4, 6])
ax.set_yticklabels(['周一', '周三', '周五', '周日'], fontsize=8)
ax.set_xticks([])
ax.tick_params(axis='y', length=0)
for spine in ax.spines.values(): spine.set_visible(False)

# === 顶部 colorbar（横向）===
cbar = fig.colorbar(im, ax=ax, orientation='horizontal', shrink=0.35,
                    pad=0.25, aspect=30)
cbar.set_label('日均值', fontsize=8)
cbar.ax.tick_params(labelsize=7, length=0)
cbar.outline.set_linewidth(0)

# === 异常日（top 1%）标注 ===
threshold = np.nanpercentile(daily, 99)
outliers_idx = np.where(daily > threshold)[0]
for idx in outliers_idx[:5]:  # 最多标 5 个
    d = start + timedelta(days=int(idx))
    wk = int(d.strftime('%W')); wd = d.weekday()
    ax.add_patch(Rectangle((wk - 0.45, wd - 0.45), 0.9, 0.9,
                            fill=False, edgecolor=COLORS['highlight'],
                            linewidth=1.3, zorder=5))

fig.tight_layout()
save_fig(fig, 'figures/fig_calendar_heatmap.pdf')
```

**★ 设计要点：**
- **方形 cell**（`aspect='equal'`）— GitHub 风格视觉一致性
- **月名只标月初**，不要每周一标 — 避免拥挤
- **异常日用 PALETTE 高亮色描边**，不抢色阶主轴

---

## 29. Hovmöller — 时空双轴图（时间纵 + 空间横 + 偏离均值色阶 + 事件标注）

**场景**: 气候 / 海洋 / 水文（厄尔尼诺、海温、降水带迁移）。两个连续轴上的二维量纲。X 轴=空间（如经度、纬度），Y 轴=时间（自上而下递增）。

⛔ **不要画反 Y 轴方向**：Hovmöller 约定时间从上往下（即 `ax.invert_yaxis()` 或直接 `extent` 反过来）。

```python
import numpy as np; from _utils.palette_maps import palette_cmap, palette_stops, contrast_text
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()
np.random.seed(42)

# === 模拟数据：60 个月 × 40 个经度 ===
n_time = 60; n_space = 40
months = np.arange(n_time)
lons = np.linspace(120, 280, n_space)  # 太平洋经度
# 季节波动 + 空间波形 + ENSO 信号 + 噪声
seasonal = 0.6 * np.sin(2 * np.pi * months[:, None] / 12)
spatial = 0.3 * np.cos(2 * np.pi * (lons - 180) / 80)[None, :]
enso = np.zeros((n_time, n_space))
# 模拟两个事件
enso[15:25, 10:30] += 1.8 * np.exp(-((np.arange(10)[:, None] - 5)**2 + (np.arange(20)[None, :] - 10)**2) / 30)
enso[40:48, 20:35] -= 1.3 * np.exp(-((np.arange(8)[:, None] - 4)**2 + (np.arange(15)[None, :] - 7)**2) / 25)
data = seasonal + spatial + enso + np.random.normal(0, 0.18, (n_time, n_space))

fig, ax = plt.subplots(figsize=(7, 5))

# ★ 双向色阶（偏离零）— 用 coolwarm 但反转让暖色=正
v = np.nanmax(np.abs(data))
im = ax.imshow(data, aspect='auto', cmap=palette_cmap('diverging'), vmin=-v, vmax=v,
               extent=[lons[0], lons[-1], months[-1], months[0]],
               interpolation='bilinear')

# ★ 零线等高线（可选，帮助读者定位"基线")
cs = ax.contour(lons, months, data, levels=[0], colors=[COLORS['ref_line']],
                linewidths=0.6, alpha=0.5, linestyles='--')

# ★ 事件标注：用半透明矩形圈出
from matplotlib.patches import Rectangle
ax.add_patch(Rectangle((lons[10], 15), lons[30] - lons[10], 10,
                        fill=False, edgecolor=COLORS['highlight'],
                        linewidth=1.4, linestyle='-', zorder=5))
ax.text(lons[20], 12, 'El Niño 期', fontsize=8, ha='center',
        color=COLORS['highlight'], fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                  edgecolor=COLORS['highlight'], alpha=0.9, linewidth=0.6))

ax.add_patch(Rectangle((lons[20], 40), lons[35] - lons[20], 8,
                        fill=False, edgecolor=PALETTE[0],
                        linewidth=1.4, linestyle='-', zorder=5))
ax.text(lons[27], 53, 'La Niña 期', fontsize=8, ha='center',
        color=PALETTE[0], fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                  edgecolor=PALETTE[0], alpha=0.9, linewidth=0.6))

ax.set_xlabel('经度 (°E)', fontsize=10)
ax.set_ylabel('时间（月）', fontsize=10)
ax.tick_params(labelsize=9)

# ★ 右侧 colorbar
cbar = fig.colorbar(im, ax=ax, shrink=0.7, pad=0.04, aspect=20)
cbar.set_label('SST 距平 (°C)', fontsize=9)
cbar.ax.tick_params(labelsize=8)
cbar.outline.set_linewidth(0.4)
cbar.outline.set_edgecolor(COLORS['grid'])

# 顶部加经度参考标记
ax.axvline(180, color=COLORS['ref_line'], linewidth=0.5, alpha=0.4, linestyle=':')
ax.text(180, -1.5, '日期变更线', fontsize=7, ha='center',
        color=COLORS['ref_line'], style='italic')

fig.tight_layout()
save_fig(fig, 'figures/fig_hovmoller.pdf')
```

**★ 设计要点：**
- **双向 cmap（RdBu_r / coolwarm）+ `vmin=-v, vmax=v`** 让零自动落在中性色
- **时间轴 extent 反向**：让最新数据在底部（约定）
- **事件用矩形框**：不要直接在数据上叠加标签，会遮挡

---


## 30. Pair Plot / Scatter Matrix — 配对图（对角线 KDE + 上三角相关系数 + 下三角散点拟合）

**场景**: 多变量数据探索（统计、社科、生信）。N×N 网格，对角线显示边际分布，下三角散点+回归线，上三角相关系数（按强度上色）。

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde, pearsonr
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()
np.random.seed(42)

# === 模拟 4 个变量（含正/负/弱相关）===
n = 250
v1 = np.random.normal(0, 1, n)
v2 = 0.75 * v1 + np.random.normal(0, 0.55, n)        # 强正相关
v3 = -0.55 * v1 + 0.3 * v2 + np.random.normal(0, 0.7, n)  # 中等负相关
v4 = np.random.normal(0, 1, n)                        # 弱相关
data = np.column_stack([v1, v2, v3, v4])
names = ['X1', 'X2', 'X3', 'X4']
N = len(names)

fig, axes = plt.subplots(N, N, figsize=(8.5, 8.5))

for i in range(N):
    for j in range(N):
        ax = axes[i, j]
        if i == j:
            # ★ 对角线：直方图 + KDE
            ax.hist(data[:, i], bins=22, color=_lighten(PALETTE[i % len(PALETTE)], 0.55),
                    edgecolor=PALETTE[i % len(PALETTE)], linewidth=0.5, alpha=0.85)
            ax2 = ax.twinx()
            xg = np.linspace(data[:, i].min(), data[:, i].max(), 200)
            ax2.plot(xg, gaussian_kde(data[:, i])(xg),
                     color=PALETTE[i % len(PALETTE)], linewidth=1.5)
            ax2.set_yticks([])
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            ax2.spines['left'].set_visible(False)
            ax.text(0.05, 0.92, names[i], transform=ax.transAxes,
                    fontsize=11, fontweight='bold', color=PALETTE[i % len(PALETTE)],
                    va='top', ha='left')
        elif i > j:
            # ★ 下三角：散点 + 拟合线
            ax.scatter(data[:, j], data[:, i], s=10, alpha=0.35,
                       color=PALETTE[0], edgecolor='white', linewidth=0.2)
            # 简易线性拟合
            slope, intercept = np.polyfit(data[:, j], data[:, i], 1)
            xfit = np.linspace(data[:, j].min(), data[:, j].max(), 60)
            yfit = slope * xfit + intercept
            ax.plot(xfit, yfit, color=COLORS['highlight'], linewidth=1.4,
                    alpha=0.85, zorder=5)
        else:
            # ★ 上三角：相关系数（按强度上色 + 字号映射强度）
            r, p = pearsonr(data[:, j], data[:, i])
            # 强度映射到背景颜色
            if r > 0:
                bg = _lighten(PALETTE[0], 1 - abs(r) * 0.7)
            else:
                bg = _lighten(COLORS['down'], 1 - abs(r) * 0.7)
            ax.set_facecolor(bg)
            sig = '***' if p < 0.001 else ('**' if p < 0.01 else ('*' if p < 0.05 else ''))
            fs = 10 + abs(r) * 12  # 字号随 |r| 增大
            ax.text(0.5, 0.55, f'{r:+.2f}', transform=ax.transAxes,
                    fontsize=fs, fontweight='bold',
                    color=COLORS['text'], ha='center', va='center')
            if sig:
                ax.text(0.5, 0.18, sig, transform=ax.transAxes,
                        fontsize=11, color=COLORS['text'], ha='center')

        # 仅在最下/最左行留刻度
        if i < N - 1:
            ax.tick_params(axis='x', labelbottom=False)
        else:
            ax.tick_params(labelsize=7)
        if j > 0:
            ax.tick_params(axis='y', labelleft=False)
        else:
            ax.tick_params(labelsize=7)
        if i != j:
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.grid(alpha=0.08, linestyle='--', color=COLORS['grid'])

fig.tight_layout(pad=0.4)
save_fig(fig, 'figures/fig_pair_plot.pdf')
```

**★ 设计要点：**
- **对角线 KDE 用 twinx** 叠加，避免抢直方图高度
- **上三角相关系数字号映射 |r|**：强相关一眼可见
- **背景色饱和度映射 |r|**：从浅到深直观展示
- **下三角 alpha=0.35** 让密集区显得"实"，稀疏区显得"虚"

---

## 31. Triptych — 三联图（input / 中间表示 / output 横向对比 + 流向箭头）

**场景**: CV / NLP / AI 定性结果展示。三个等宽子图横向并列，子图间用箭头暗示数据流，共享色标（如适用）。

```python
import numpy as np; from _utils.palette_maps import palette_cmap, palette_stops, contrast_text
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyArrowPatch
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()
np.random.seed(42)

# === 模拟数据：输入图 / 注意力图 / 输出图 ===
H, W = 80, 80
y, x = np.mgrid[0:H, 0:W]
input_img = np.exp(-((x - 28)**2 + (y - 32)**2) / 250) + \
            0.6 * np.exp(-((x - 52)**2 + (y - 48)**2) / 200) + \
            np.random.normal(0, 0.04, (H, W))
attention = np.exp(-((x - 40)**2 + (y - 40)**2) / 500) * (input_img > 0.2)
output_img = input_img * attention * 1.6

# === 1 行 3 列 + 上方薄色条 ===
fig = plt.figure(figsize=(9, 4))
gs = GridSpec(2, 3, height_ratios=[0.5, 6], hspace=0.05, wspace=0.12)

titles = ['(a) 输入', '(b) 注意力图', '(c) 重构输出']
images = [input_img, attention, output_img]
v = max(np.max(im) for im in images)

axes_img = []
for col in range(3):
    ax = fig.add_subplot(gs[1, col])
    im = ax.imshow(images[col], cmap=palette_cmap('sequential'), vmin=0, vmax=v,
                   interpolation='bilinear')
    ax.set_title(titles[col], fontsize=11, fontweight='bold',
                 color=COLORS['text'], pad=8)
    ax.axis('off')
    axes_img.append((ax, im))

# === 顶部共享色条 ===
cbar_ax = fig.add_subplot(gs[0, :])
cbar = fig.colorbar(axes_img[0][1], cax=cbar_ax, orientation='horizontal')
cbar.set_label('归一化激活', fontsize=8); cbar.ax.xaxis.set_label_position('top'); cbar.ax.xaxis.set_ticks_position('top')
cbar.ax.tick_params(labelsize=7, length=2)
cbar.outline.set_linewidth(0.4)
cbar.outline.set_edgecolor(COLORS['grid'])

# === 子图间流向箭头（用 figure-level transform）===
def add_arrow(fig, axL, axR, label=None):
    bbL = axL.get_position(); bbR = axR.get_position()
    y_mid = (bbL.y0 + bbL.y1) / 2
    arrow = FancyArrowPatch((bbL.x1 + 0.005, y_mid), (bbR.x0 - 0.005, y_mid),
                             transform=fig.transFigure,
                             arrowstyle='->', mutation_scale=14,
                             color=COLORS['highlight'], linewidth=1.5,
                             clip_on=False)
    fig.patches.append(arrow)
    if label:
        fig.text((bbL.x1 + bbR.x0) / 2, y_mid + 0.04, label,
                 fontsize=8, ha='center', color=COLORS['highlight'],
                 fontweight='bold', style='italic')

add_arrow(fig, axes_img[0][0], axes_img[1][0], 'Encoder')
add_arrow(fig, axes_img[1][0], axes_img[2][0], 'Decoder')

save_fig(fig, 'figures/fig_triptych.pdf')
```

**★ 设计要点：**
- **GridSpec 控制顶部 colorbar + 三子图**：保证 colorbar 跨越三列
- **`axis('off')` + `set_title()`**：图像类子图统一约定
- **箭头用 `fig.transFigure`** 而非 axes 坐标，跨子图绘制
- **`vmin=0, vmax=v` 跨子图统一**：让 colorbar 对所有子图有意义

---

## 32. Posterior Trace + Density — 贝叶斯 MCMC 双面板（多链 trace + 边际密度 + Rhat 标注）

**场景**: 贝叶斯 MCMC 收敛诊断标配。左侧多链 trace（检查混合 & 平稳）、右侧边际密度（合并多链）。

```python
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy.stats import gaussian_kde
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()
np.random.seed(42)

# === 模拟 4 条 MCMC 链，2 个参数 ===
n_chains = 4; n_iter = 2000
params = ['μ', 'σ']
true_vals = [1.5, 0.7]
# 每条链有点初始偏移然后收敛
chains = np.zeros((2, n_chains, n_iter))
for p in range(2):
    for c in range(n_chains):
        init = true_vals[p] + np.random.normal(0, 0.6) * (1 if c < 2 else 0.4)
        for i in range(n_iter):
            init = init + 0.95 * (true_vals[p] - init) * 0.05 + np.random.normal(0, 0.08)
            chains[p, c, i] = init

# === 2 行 2 列：每行一个参数 ===
fig = plt.figure(figsize=(9, 5))
gs = GridSpec(2, 2, width_ratios=[3, 1.5], hspace=0.35, wspace=0.1)

burnin = 200
for p in range(2):
    # 左：trace plot
    ax_trace = fig.add_subplot(gs[p, 0])
    for c in range(n_chains):
        ax_trace.plot(np.arange(n_iter), chains[p, c],
                      color=PALETTE[c % len(PALETTE)], linewidth=0.5, alpha=0.75,
                      label=f'链 {c+1}' if p == 0 else None)
    ax_trace.axvline(burnin, color=COLORS['ref_line'], linestyle=':', linewidth=1, alpha=0.6)
    ax_trace.text(burnin + 20, ax_trace.get_ylim()[0] + (ax_trace.get_ylim()[1] - ax_trace.get_ylim()[0]) * 0.05,
                  f'burn-in={burnin}', fontsize=7, color=COLORS['ref_line'], style='italic')
    ax_trace.axhline(true_vals[p], color=COLORS['highlight'], linestyle='--', linewidth=1, alpha=0.7)
    ax_trace.set_ylabel(params[p], fontsize=11, fontweight='bold')
    if p == 1:
        ax_trace.set_xlabel('迭代步数', fontsize=10)
    ax_trace.spines['top'].set_visible(False)
    ax_trace.spines['right'].set_visible(False)
    ax_trace.grid(axis='y', alpha=0.1, linestyle='--', color=COLORS['grid'])
    if p == 0:
        ax_trace.legend(loc='upper right', frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=7, ncol=4, columnspacing=1)

    # 右：边际密度（合并所有链，去除 burn-in）
    ax_dens = fig.add_subplot(gs[p, 1], sharey=ax_trace)
    pooled = chains[p, :, burnin:].flatten()
    yg = np.linspace(pooled.min(), pooled.max(), 200)
    density = gaussian_kde(pooled)(yg)
    ax_dens.fill_betweenx(yg, 0, density, color=_lighten(PALETTE[0], 0.4),
                          alpha=0.7, linewidth=0)
    ax_dens.plot(density, yg, color=PALETTE[0], linewidth=1.5)
    # 95% HPDI
    sorted_x = np.sort(pooled)
    ci_lo, ci_hi = np.percentile(sorted_x, [2.5, 97.5])
    ax_dens.axhline(ci_lo, color=COLORS['ref_line'], linestyle=':', linewidth=0.8, alpha=0.6)
    ax_dens.axhline(ci_hi, color=COLORS['ref_line'], linestyle=':', linewidth=0.8, alpha=0.6)
    ax_dens.axhline(pooled.mean(), color=COLORS['highlight'], linestyle='--', linewidth=1.1, alpha=0.8)

    # 假装计算 Rhat（实际 Rhat 需要严谨实现，这里展示标注样式）
    rhat_value = 1.005 + np.random.uniform(-0.001, 0.003)
    info_text = f'$\\hat{{\\theta}}$ = {pooled.mean():.3f}\n95% HPDI: [{ci_lo:.2f}, {ci_hi:.2f}]\n$\\hat{{R}}$ = {rhat_value:.3f}'
    ax_dens.text(0.95, 0.95, info_text, transform=ax_dens.transAxes,
                 fontsize=7.5, va='top', ha='right',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                           edgecolor=COLORS['grid'], alpha=0.95, linewidth=0.4))

    ax_dens.set_xticks([])
    ax_dens.tick_params(axis='y', labelleft=False)
    for sp in ['top', 'right', 'bottom']: ax_dens.spines[sp].set_visible(False)

save_fig(fig, 'figures/fig_posterior_trace.pdf')
```

**★ 设计要点：**
- **多链不同 PALETTE 色**：直观看出链间混合度（叠在一起 = 收敛）
- **burn-in 虚线**：明确"前 X 步丢弃"
- **HPDI 横向虚线 + 文字框统一标注**：参数估计可一眼读出
- **`sharey=ax_trace`** 让 density 与 trace 在同一 y 尺度上

---

## 33. Streamgraph — 流图（居中堆叠基线 + 多类别 + 末端标签）

**场景**: 时序中多类别的相对占比变化（话题趋势、技术栈、人口构成）。居中基线让单类别波动看起来"自然"，比传统堆叠图更动态。

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()
np.random.seed(42)

# === 模拟 5 个类别在 50 个时间点的数值 ===
n_t = 50; n_cat = 5
t = np.arange(n_t)
# 每个类别有不同的生命周期形状
shapes = [
    20 + 30 * np.exp(-((t - 20)**2) / 250),                # 凸起在中间
    10 + 15 * (1 / (1 + np.exp(-0.2 * (t - 25)))),         # 后期增长
    25 - 20 * (1 / (1 + np.exp(-0.2 * (t - 15)))) + 5,     # 早期衰退
    18 * np.sin(t * 0.3) ** 2 + 5,                         # 周期波动
    12 + np.random.normal(0, 2, n_t)                        # 平稳基线
]
data = np.array([gaussian_filter1d(s, sigma=2) for s in shapes])
data = np.clip(data, 0.5, None)  # 保证非负

# === 居中基线：每个时刻总值除以 2，作为偏移 ===
total = data.sum(axis=0)
baseline = -total / 2  # 起点放底，向上堆叠
fig, ax = plt.subplots(figsize=(9, 4.5))

names = ['类别 A', '类别 B', '类别 C', '类别 D', '类别 E']
cumsum = baseline.copy()
for i, (vals, name) in enumerate(zip(data, names)):
    color = PALETTE[i % len(PALETTE)]
    ax.fill_between(t, cumsum, cumsum + vals,
                    color=_lighten(color, 0.25), alpha=0.88,
                    edgecolor=color, linewidth=0.5, label=name)
    # ★ 末端标签：放在每条流带末端的中心
    end_mid = cumsum[-1] + vals[-1] / 2
    ax.text(t[-1] + 0.7, end_mid, name, fontsize=8, va='center',
            color=color, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.18', facecolor='white',
                      edgecolor=color, alpha=0.9, linewidth=0.5))
    cumsum += vals

# 中心参考线
ax.axhline(0, color=COLORS['ref_line'], linewidth=0.5, alpha=0.4, linestyle='-')

ax.set_xlabel('时间', fontsize=10)
ax.set_yticks([])  # 居中堆叠图通常省略 y 轴刻度（数值由颜色面积表达）
ax.set_xlim(t[0], t[-1] + 7)
for sp in ['top', 'right', 'left']: ax.spines[sp].set_visible(False)
ax.tick_params(axis='y', length=0)
ax.grid(axis='x', alpha=0.08, linestyle='--', color=COLORS['grid'])

# 顶部小注释解释读法
ax.text(0.02, 0.97, '流带厚度 = 该时刻的数值；垂直位置无意义',
        transform=ax.transAxes, fontsize=7, color=COLORS['text'],
        style='italic', va='top',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                  edgecolor=COLORS['grid'], alpha=0.85, linewidth=0.3))

fig.tight_layout()
save_fig(fig, 'figures/fig_streamgraph.pdf')
```

**★ 设计要点：**
- **居中基线 `baseline = -total / 2`** 是 streamgraph 的关键 — 让单类别波动看起来自然
- **`gaussian_filter1d`** 平滑边界 — 避免毛刺感
- **末端标签** 比 legend 更好看 — 让读者眼睛跟着流走到尽头
- **`set_yticks([])`** — y 轴无意义，强制省略避免误导

---

## 34. Bivariate Choropleth / 双变量热图 — 二维联合分布（3×3 配色矩阵 + 主图 + 图例）

**场景**: 双变量空间分布（社会-经济、风险-暴露、降水-气温）。一个图同时表达两个变量的高/中/低组合。配 3×3 颜色矩阵作图例。

```python
import numpy as np; from _utils.vivid_config import palette_colors
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.colors import LinearSegmentedColormap
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style(); scale_colors = palette_colors()
np.random.seed(42)

# === 模拟 2 个变量在 30×30 网格上的取值 ===
N = 30
y, x = np.mgrid[0:N, 0:N]
var_a = np.exp(-((x - 10)**2 + (y - 12)**2) / 100) + 0.3 * np.random.rand(N, N)
var_b = np.exp(-((x - 20)**2 + (y - 22)**2) / 120) + 0.3 * np.random.rand(N, N)
var_a = (var_a - var_a.min()) / (var_a.max() - var_a.min())
var_b = (var_b - var_b.min()) / (var_b.max() - var_b.min())

# === 3×3 双变量配色（X 维度用 scale_colors[0] 渐变，Y 维度用 scale_colors[1] 渐变，组合产生中间色）===
def bivariate_color(a, b):
    """a, b in [0,1] -> RGB. 用两个主色的加权混合。"""
    c1 = np.array([int(scale_colors[0].lstrip('#')[i:i+2], 16)/255 for i in (0,2,4)])  # 蓝
    c2 = np.array([int(scale_colors[1].lstrip('#')[i:i+2], 16)/255 for i in (0,2,4)])  # 橙
    base = np.array([0.97, 0.97, 0.97])  # 浅灰底
    return base * (1 - 0.5*a - 0.5*b) + c1 * 0.5*a + c2 * 0.5*b

# 量化到 3×3 等级
qa = np.clip(np.digitize(var_a, np.quantile(var_a, [0.33, 0.67])), 0, 2)
qb = np.clip(np.digitize(var_b, np.quantile(var_b, [0.33, 0.67])), 0, 2)

# 构造 RGB 图像
rgb = np.zeros((N, N, 3))
for i in range(N):
    for j in range(N):
        rgb[i, j] = bivariate_color(qa[i, j] / 2, qb[i, j] / 2)

# === 主图 + 右下小图例（3×3 矩阵）===
fig = plt.figure(figsize=(7.5, 5))
gs = GridSpec(1, 2, width_ratios=[3, 1], wspace=0.15)
ax_main = fig.add_subplot(gs[0, 0])
ax_main.imshow(rgb, origin='lower', interpolation='nearest')
ax_main.set_xlabel('经度网格', fontsize=10)
ax_main.set_ylabel('纬度网格', fontsize=10)
ax_main.set_title('双变量空间分布', fontsize=11, color=COLORS['text'], pad=6)
ax_main.tick_params(labelsize=8)
for sp in ax_main.spines.values(): sp.set_edgecolor(COLORS['grid']); sp.set_linewidth(0.5)

# === 3×3 图例矩阵 ===
ax_leg = fig.add_subplot(gs[0, 1])
legend_grid = np.zeros((3, 3, 3))
for i in range(3):
    for j in range(3):
        legend_grid[2-i, j] = bivariate_color(j / 2, i / 2)
ax_leg.imshow(legend_grid, origin='lower', interpolation='nearest')
ax_leg.set_xticks([0, 1, 2]); ax_leg.set_yticks([0, 1, 2])
ax_leg.set_xticklabels(['低', '中', '高'], fontsize=8)
ax_leg.set_yticklabels(['低', '中', '高'], fontsize=8)
ax_leg.set_xlabel('变量 A →', fontsize=9, color=scale_colors[0], fontweight='bold')
ax_leg.set_ylabel('变量 B →', fontsize=9, color=scale_colors[1], fontweight='bold')
ax_leg.set_title('图例', fontsize=9, color=COLORS['text'], pad=4)
for sp in ax_leg.spines.values(): sp.set_edgecolor(COLORS['grid']); sp.set_linewidth(0.5)
ax_leg.tick_params(length=0)

# 在图例每格中标"AaBb"短标识
for i in range(3):
    for j in range(3):
        ax_leg.text(j, 2-i, f'A{j+1}B{i+1}', ha='center', va='center',
                    fontsize=7, color=COLORS['text'], fontweight='bold')

fig.tight_layout()
save_fig(fig, 'figures/fig_bivariate.pdf')
```

**★ 设计要点：**
- **3×3 矩阵图例** 是双变量图的灵魂 — 没图例读者完全不知道颜色含义
- **PALETTE[0] (蓝) + PALETTE[1] (橙) 混合** 自动产生 9 种和谐组合
- **`np.digitize` 量化到 3 等级** — 让色块离散，避免连续色混乱
- **图例每格写 AaBb 标识** — 比纯配色更清楚

---

## 35. 三维分组渐变柱状图

用途：比较两组离散条件交叉组合下的非负测量值，例如材料×掺量、算法×实验条件。
输入：行标签、列标签、对应高度矩阵；可选真实误差长度。CSV 第一列为行标签，第一行为列名。
保留：四面分层渐变柱、独立顶面明暗、正交视角、柱顶数值、误差竖线与帽线、白底虚线网格、同分档侧色条。
配色：从项目 palette_colors() 的原顺序插值为分档颜色，分类取色顺序不用于数值分档；不改变柱面的原有提白曲线。
示例：66个柱高转录自用户参考图；误差棒为原复现的示意长度，已在预览标注，并非真实实验误差。自定义数据未提供误差时不生成误差棒。
适配：plot_chart 支持 (行,列) 对称误差或 (2,行,列) 非对称误差；负值、缺失值与越界色档直接报错，不能填零或静默截断。默认新数据使用线性分档；示例保留原不等宽阈值，色条等高色块代表档位而非线性距离。
局限：三维遮挡会影响密集类别比较；组数过多可按任务减少同屏项或调整视角。该模板不是频数直方图，也不表示连续曲面。

```python
"""Three-dimensional grouped gradient bars, adapted from the supplied reproduction.
Default demo heights were transcribed from the reference image; demo errors are
illustrative only. Custom data never receives invented uncertainty.
Run from a bootstrapped Vivid workspace, or directly from the installed catalog.
"""
from pathlib import Path
import argparse
import csv
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm, to_rgb, LinearSegmentedColormap
from matplotlib.colorbar import ColorbarBase
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# Resolve the active workspace utilities or the installed skill's shared bundle.
for base in (Path.cwd(), *Path.cwd().parents, *Path(__file__).resolve().parents):
    candidates = (base / '_utils', base / 'original/resources/assets/shared-scripts')
    found = next((p for p in candidates if (p / 'vivid_config.py').is_file()), None)
    if found is not None:
        sys.path.insert(0, str(found))
        break
else:
    raise RuntimeError('Run Vivid bootstrap in the workspace before using this recipe.')
from vivid_config import palette_colors
from plot_utils import setup_style


def read_matrix(path):
    """Wide CSV: first column row label, remaining column headers are conditions."""
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.reader(stream))
    if len(rows) < 2 or len(rows[0]) < 2 or any(len(r) != len(rows[0]) for r in rows):
        raise ValueError('Expected a rectangular CSV with row and column labels.')
    labels, conditions = [r[0] for r in rows[1:]], rows[0][1:]
    if len(set(labels)) != len(labels) or len(set(conditions)) != len(conditions):
        raise ValueError('Row and column labels must be unique.')
    return np.array([[float(v) for v in r[1:]] for r in rows[1:]]), labels, conditions


def plot_chart(values, samples, ss, *, errors=None, bounds=None,
               value_label='Value', sample_label='Sample', condition_label='Condition',
               note=None):
    """errors: nonnegative lengths shaped (rows, columns) or (2, rows, columns).

    A 2-D array gives symmetric errors; a 3-D array gives lower/upper lengths.
    None omits error marks. Heights and colorbar share the same explicit bins.
    """
    values = np.asarray(values, dtype=float)
    if (values.ndim != 2 or values.size == 0 or not np.isfinite(values).all()
            or (values < 0).any() or values.shape != (len(samples), len(ss))):
        raise ValueError('Expected finite nonnegative heights matching both label axes.')
    nrows, ncols = values.shape
    lower = upper = np.zeros_like(values)
    if errors is not None:
        error_array = np.asarray(errors, dtype=float)
        if error_array.shape == values.shape:
            lower = upper = error_array
        elif error_array.shape == (2, *values.shape):
            lower, upper = error_array
        else:
            raise ValueError('Error shape must match heights, optionally with lower/upper axis.')
        if (not np.isfinite(error_array).all() or (error_array < 0).any()
                or (lower > values).any()):
            raise ValueError('Errors must be finite, nonnegative and not cross the zero base.')
    if bounds is None:
        # Linear bins for new data; original demo binning is supplied explicitly.
        bounds = np.linspace(0, max(float(values.max()), 1.0), 12)
    bounds = np.asarray(bounds, dtype=float)
    if (bounds.ndim != 1 or len(bounds) < 3 or not np.isfinite(bounds).all()
            or (np.diff(bounds) <= 0).any()
            or bounds[0] > values.min() or bounds[-1] < values.max()):
        raise ValueError('Increasing bin boundaries must cover every height.')
    setup_style()
    plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'],
                         'font.weight': 'bold', 'axes.labelweight': 'bold', 'font.size': 12,
                         'pdf.fonttype': 42, 'axes.linewidth': 1.2})
    # Numeric bins use the palette's raw ordered scale, not categorical ordering.
    scale = LinearSegmentedColormap.from_list('vivid_ordered', palette_colors())
    colors = scale(np.linspace(0, 1, len(bounds)-1))[:, :3]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(bounds, cmap.N, clip=True)
    fig = plt.figure(figsize=(14.4, 12.8), facecolor='white')
    ax = fig.add_axes([.015, .055, .81, .90], projection='3d', computed_zorder=False)
    ax.view_init(elev=27, azim=-56)
    ax.set_proj_type('ortho')
    ax.set_box_aspect((max(nrows * 1.1, 2), max(ncols * .955, 2), 8))

    # Side faces fade from near-white at the foot to the bin color at the top.
    label_offset = max(float((values + upper).max()), 1.0) * .02
    faces, facecolors = [], []
    w, d = .62, .62
    for i in range(nrows):
        for j in range(ncols):
            h = values[i,j]
            base = np.array(to_rgb(colors[int(norm(h))]))
            x0, x1, y0, y1 = i-w/2, i+w/2, j-d/2, j+d/2
            n = 40 if h > 1.5 else 1
            levels = np.linspace(0, h, n+1)
            for k in range(n):
                z0, z1 = levels[k:k+2]
                t = (k+.5)/n
                c = base if h <= 1.5 else np.ones(3)*(1-t**.65)+base*t**.65
                for points, shade in [([(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)],.98),
                                      ([(x1,y0,z0),(x1,y1,z0),(x1,y1,z1),(x1,y0,z1)],.88),
                                      ([(x1,y1,z0),(x0,y1,z0),(x0,y1,z1),(x1,y1,z1)],.92),
                                      ([(x0,y1,z0),(x0,y0,z0),(x0,y0,z1),(x0,y1,z1)],1.)]:
                    faces.append(points)
                    facecolors.append(np.clip(c*shade,0,1))
            faces.append([(x0,y0,h),(x1,y0,h),(x1,y1,h),(x0,y1,h)])
            facecolors.append(np.clip(base*1.04,0,1))
    ax.add_collection3d(Poly3DCollection(faces, facecolors=facecolors, edgecolors='none',
                                        linewidths=0, antialiased=False, zsort='average', zorder=3))
    # Draw error marks only from the supplied symmetric/asymmetric error lengths.
    for i in range(nrows):
        for j in range(ncols):
            h = values[i,j]
            err = upper[i,j]
            if errors is not None:
                ax.plot([i,i], [j,j], [h-lower[i,j],h+err], c='black', lw=1.25, zorder=5)
                ax.plot([i-.10,i+.10], [j,j], [h+err,h+err], c='black', lw=1.25, zorder=5)
            ax.text(i, j, h+err+label_offset, f'{h:.2f}', ha='center', va='bottom',
                    fontsize=10, zorder=6, bbox=dict(facecolor='white', edgecolor='none', alpha=.87, pad=.15))
    ax.set(xlim=(-.65,nrows-.35), ylim=(-.65,ncols-.35),
           zlim=(0,max(float((values+upper).max()), 1.0) * 1.08))
    ax.set_xticks(range(nrows), samples, rotation=-15)
    ax.set_yticks(range(ncols), ss, rotation=18)
    ax.zaxis.set_major_locator(MaxNLocator(nbins=12))
    ax.set_xlabel(sample_label, labelpad=22, fontsize=19)
    ax.set_ylabel(condition_label, labelpad=24, fontsize=19)
    ax.set_zlabel(value_label, labelpad=20, fontsize=18)
    ax.zaxis._axinfo['juggled'] = (1,2,0)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.set_pane_color((1,1,1,1))
        axis.pane.set_edgecolor('black')
        axis._axinfo['grid'].update(color=(.68,.68,.68,1), linestyle='--', linewidth=.8)
    ax.tick_params(axis='both', labelsize=12, pad=3)
    cax = fig.add_axes([.865,.205,.024,.63])
    cb = ColorbarBase(cax, cmap=cmap, norm=norm, boundaries=bounds, ticks=bounds, spacing='uniform')
    cb.ax.set_yticklabels([f'{v:.3g}' for v in bounds])
    cb.ax.tick_params(labelsize=14, pad=6)
    cb.set_label(value_label, fontsize=18, labelpad=17)
    if note:
        fig.text(.05, .018, note, fontsize=11, color='#444444')
    return fig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, help='Wide CSV of heights')
    parser.add_argument('--errors', type=Path, help='Wide CSV of symmetric error lengths, matching data labels')
    parser.add_argument('--output', type=Path, default=Path('figures/fig_grouped_bar_3d'))
    parser.add_argument('--value-label', default=None)
    args = parser.parse_args()
    if args.data:
        values, samples, conditions = read_matrix(args.data)
        errors = None
        if args.errors:
            errors, error_rows, error_cols = read_matrix(args.errors)
            if samples != error_rows or conditions != error_cols:
                raise ValueError('Error CSV labels and order must match the data CSV.')
        fig = plot_chart(values, samples, conditions, errors=errors,
                         value_label=args.value_label or 'Value')
    else:
        if args.errors:
            parser.error('--errors requires --data')
        # Heights transcribed from the user reference. Errors are illustrative.
        samples = ['C-28', 'C-7', 'C-3', 'C-1', 'U-28', 'U-1']
        conditions = ['SS-0', 'SS-0.1', 'SS-0.2', 'SS-0.3', 'SS-0.4', 'SS-0.5', 'SS-0.6', 'SS-0.7', 'SS-0.8', 'SS-0.9', 'SS-1']
        values = np.array([[0.34, 3.95, 8.36, 13.81, 16.24, 23.39, 32.97, 35.36, 38.44, 46.64, 57.14], [0.33, 3.12, 7.98, 13.09, 14.75, 20.15, 28.26, 31.24, 35.76, 42.32, 55.28], [0.3, 3.01, 6.3, 12.16, 13.12, 18.45, 25.76, 28.29, 33.03, 37.68, 49.88], [0.28, 2.84, 5.48, 9.72, 11.09, 14.44, 22.31, 25.53, 30.48, 34.04, 36.08], [0.33, 2.77, 4.23, 5.52, 6.12, 7.29, 9.26, 10.76, 13.49, 14.24, 17.13], [0.21, 0.55, 0.71, 0.81, 1.12, 1.24, 2.59, 3.54, 3.86, 4.07, 6.31]])
        upper = np.maximum(.10, .025 * values)
        errors = np.stack([.35 * upper, upper])
        bounds = [.21, .35, .58, .97, 1.6, 2.7, 4.5, 7.4, 12.4, 20.6, 34.3, 57.14]
        fig = plot_chart(values, samples, conditions, errors=errors, bounds=bounds,
                         value_label=args.value_label or 'Compressive strength /MPa',
                         condition_label='SS Content',
                         note='Reference-label heights; illustrative error bars (not measured).')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ('png', 'pdf'):
        fig.savefig(args.output.with_suffix('.' + suffix), dpi=300,
                    facecolor='white', bbox_inches='tight', pad_inches=.25)
    plt.close(fig)
    print('Saved PNG and PDF:', args.output)


if __name__ == '__main__':
    main()
```

## 36. 多Y轴渐变直方图与正态拟合

用途：比较多个方法或样本群体在共同测量变量上的分布位置、离散程度与形状。
数据：1–3组同一物理量、同单位的原始观测；长表CSV列为group,value。频数由实际样本分箱统计，不能输入已经汇总的频数冒充原始样本。
结构：共享X轴；第一组左Y轴，其余组右Y轴并外移；组别同色刻度、柱体和虚线；每根柱体从透明底部到有色顶部渐变；白底图例列出样本量及正态拟合参数。
保真：保留64层矢量透明渐变、三组重叠、同色轴关联、正态虚线和独立图层顺序。所有曲线置于柱体上方，双轴的数据变换分别绑定，不把第三组曲线错误放到主轴刻度上。
配色：使用当前项目categorical_colors()固定分类顺序，支持七套主题和自定义配色；不同组至少需要同数量的颜色；--reference-colors明确使用参考图红蓝青颜色，其余调用遵循当前项目配色。
统计：组内等宽分箱，允许各组宽度与边界不同；每组拟合mu=mean、sigma=std(ddof=0)，曲线高度为N×箱宽×正态密度，频数仅为箱计数，曲线是预期频数的近似。正态拟合不等于正态性检验；非正态或零方差数据可用fit=False/--no-fit保留直方图。非有限值、缺失组名和不覆盖样本的分箱报错，不静默删除或截断。
注意：独立Y轴的柱高不能直接跨组比较频数；对绝对频数的比较优先使用共Y轴直方图，比较概率形状可用归一化密度。此模板中的Y轴均为频数，不为多种单位的趋势图。
来源：只有用户效果截图，无原始代码、样本数据与可核验作者；按视觉结构重建。演示为固定种子模拟数据，图中明确标注，不冒充截图研究数据。

```python
"""Shared-X gradient histograms, independent colored Y axes and normal fits.
Reconstructed from a user image; default samples are synthetic, not paper data.
Custom CSV uses columns group,value. Normal fits describe data; they do not
establish normality. Independent Y scales do not permit direct height comparison.
"""
from pathlib import Path
import argparse
import csv
import json
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import to_rgb
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator, MultipleLocator

for base in (Path.cwd(), *Path.cwd().parents, *Path(__file__).resolve().parents):
    found = next((p for p in (base/'_utils', base/'original/resources/assets/shared-scripts')
                  if (p/'vivid_config.py').is_file()), None)
    if found is not None:
        sys.path.insert(0, str(found))
        break
else:
    raise RuntimeError('Run Vivid bootstrap in the workspace before using this recipe.')
from vivid_config import categorical_colors
from plot_utils import setup_style


def read_samples(path):
    groups = {}
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        rows = csv.DictReader(stream)
        if not {'group', 'value'}.issubset(rows.fieldnames or []):
            raise ValueError('CSV requires group,value columns.')
        for row in rows:
            name = row['group'].strip()
            if not name:
                raise ValueError('Group labels cannot be empty.')
            groups.setdefault(name, []).append(float(row['value']))
    return groups


def plot_chart(groups, *, bins=14, xlabel='Residual', fit=True, ylimits=None,
               note=None, colors=None, xlim=None, ytick_step=None):
    """One to three groups of raw observations with a shared X scale.

    bins may be shared or a dict of group-specific equal-width bin edges.

    Each normal curve is mean/std(ddof=0) fitted to its own raw sample, scaled
    by sample count * bin width to approximate frequency on that group's axis.
    Optional ylimits supplies one (0, upper) pair per group without clipping.
    """
    if not 1 <= len(groups) <= 3:
        raise ValueError('Use one to three groups to keep the independent axes readable.')
    arrays = {str(name): np.asarray(values, dtype=float) for name, values in groups.items()}
    if len(arrays) != len(groups) or any(not name.strip() for name in arrays):
        raise ValueError('Group labels must be distinct nonempty strings.')
    for name, values in arrays.items():
        if values.ndim != 1 or len(values) < 2 or not np.isfinite(values).all():
            raise ValueError(f'{name}: provide at least two finite raw observations.')
        if fit and values.std(ddof=0) <= 0:
            raise ValueError(f'{name}: zero variance; disable the normal fit.')
    combined = np.concatenate(list(arrays.values()))
    if isinstance(bins, dict) and set(bins) != set(arrays):
        raise ValueError('Group-specific bins must include every group exactly once.')
    bin_edges = {}
    for name, values in arrays.items():
        edges = np.histogram_bin_edges(values if isinstance(bins,dict) else combined,
                                       bins=bins[name] if isinstance(bins,dict) else bins)
        widths = np.diff(edges)
        if (len(widths) < 2 or not np.isfinite(edges).all() or (widths <= 0).any()
                or not np.allclose(widths, widths[0])
                or edges[0] > values.min() or edges[-1] < values.max()):
            raise ValueError('Each group needs equal-width bins covering all its observations.')
        bin_edges[name] = edges
    if ylimits is not None and len(ylimits) != len(arrays):
        raise ValueError('Supply one Y range for every group.')
    if ytick_step is not None and (not np.isfinite(ytick_step) or ytick_step <= 0):
        raise ValueError('Y tick step must be positive and finite.')

    setup_style()
    colors = categorical_colors() if colors is None else colors
    if len(colors) < len(arrays):
        raise ValueError('The selected palette needs at least one color per group.')
    plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'],
                         'font.weight': 'bold', 'axes.labelweight': 'bold',
                         'pdf.fonttype': 42, 'font.size': 11, 'axes.linewidth': 1.25})
    fig, host = plt.subplots(figsize=(9.5, 7.2))
    fig.subplots_adjust(left=.085, right=.86 if len(arrays) == 3 else .92,
                        bottom=.12, top=.975)
    axes = [host] + [host.twinx() for _ in range(len(arrays)-1)]
    extent = (min(e[0] for e in bin_edges.values()), max(e[-1] for e in bin_edges.values()))
    if xlim is not None and (len(xlim)!=2 or not np.isfinite(xlim).all()
                            or xlim[0]>extent[0] or xlim[1]<extent[1]):
        raise ValueError('X range must cover all histogram bins.')
    host.set_xlim(*(extent if xlim is None else xlim))
    host.set_xlabel(xlabel, fontsize=15)
    host.spines['top'].set_visible(True)
    host.tick_params(axis='x', top=True, direction='in', width=1.25, length=6)
    # All data layers live on the host with each group's own data transform.
    # This keeps every dashed fit above all translucent bars across twin axes.
    host.set_zorder(10)
    for ax in axes:
        ax.patch.set_visible(False)
        ax.grid(False)
    legend_bars, legend_fits, stats = [], [], []
    for i, ((name, values), ax) in enumerate(zip(arrays.items(), axes)):
        color = colors[i]
        edges = bin_edges[name]
        widths = np.diff(edges)
        counts, _ = np.histogram(values, bins=edges)
        mu, sigma = float(values.mean()), float(values.std(ddof=0))
        xfit = np.linspace(*host.get_xlim(), 700)
        yfit = (len(values)*widths[0]/(sigma*np.sqrt(2*np.pi))
                * np.exp(-.5*((xfit-mu)/sigma)**2)) if fit else np.zeros_like(xfit)
        peak = max(float(counts.max()), float(yfit.max()), 1.)
        ylim = (0., peak*1.28) if ylimits is None else tuple(ylimits[i])
        if len(ylim) != 2 or not np.isfinite(ylim).all() or ylim[0] != 0 or ylim[1] < peak:
            raise ValueError('Y ranges must start at zero and cover all counts and fitted peaks.')
        ax.set_ylim(*ylim)
        side = 'left' if i == 0 else 'right'
        if i:
            ax.spines['left'].set_visible(False)
            ax.spines['top'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['right'].set_position(('axes', 1.+.12*(i-1)))
        else:
            ax.spines['right'].set_visible(False)
        ax.spines[side].set_color(color)
        ax.spines[side].set_visible(True)
        ax.tick_params(axis='y', colors=color, direction='in', width=1.3, length=6)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=6, integer=True) if ytick_step is None
                                  else MultipleLocator(ytick_step))
        # Reference layout: one black frequency label; group/axis mapping is
        # carried by colored ticks and the matching legend, not repeated titles.
        ax.set_ylabel('Frequency' if i == 0 else '', color='black', fontsize=15, labelpad=6)

        # True alpha gradient: transparent foot to colored cap, not an opaque
        # white rectangle. Earlier groups remain visible through overlaps.
        vertices, facecolors = [], []
        rgb = to_rgb(color)
        for left, width, height in zip(edges[:-1], widths, counts):
            if height == 0:
                continue
            levels = np.linspace(0., float(height), 65)
            for k, (low, high) in enumerate(zip(levels[:-1], levels[1:])):
                x0, x1 = left+.11*width, left+.89*width
                vertices.append([(x0,low),(x1,low),(x1,high),(x0,high)])
                facecolors.append((*rgb, .02+.76*((k+.5)/64)**.85))
        host.add_collection(PolyCollection(vertices, facecolors=facecolors,
                            edgecolors='none', antialiased=False,
                            transform=ax.transData, zorder=2+({0:.1,1:0.,2:.2}[i])), autolim=False)
        legend_bars.append(Patch(facecolor=color, alpha=.75, edgecolor='none',
                                 label=name))
        if fit:
            host.plot(xfit, yfit, color=color, ls='--', lw=2.2,
                      transform=ax.transData, zorder=5)
            legend_fits.append(Line2D([],[],color=color,ls='--',lw=2.2,
                                      label=fr'{name} fit ($\mu={mu:.1f},\ \sigma={sigma:.1f}$)'))
        stats.append(dict(group=name,n=len(values),mean=mu,std_mle=sigma,
                          counts=counts.tolist(),bin_edges=edges.tolist(),
                          color=color,ylim=list(ylim),fit='normal_mle' if fit else None))
    host.legend(handles=legend_bars[::-1]+legend_fits[::-1],loc='upper left',fontsize=8.6,
                handlelength=2.2,labelspacing=.25,borderpad=.4,
                frameon=True,facecolor='white',edgecolor='#aaaaaa',framealpha=.94)
    if note:
        fig.text(.085,.025,note,fontsize=8,color='#444444')
    return fig, stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',type=Path,help='Long CSV: group,value')
    parser.add_argument('--bins',type=int,default=None)
    parser.add_argument('--no-fit',action='store_true')
    parser.add_argument('--reference-colors',action='store_true',help='Explicit screenshot color reproduction; otherwise use the project palette')
    parser.add_argument('--xlabel',default='Residual')
    parser.add_argument('--output',type=Path,default=Path('figures/fig_multi_y_gradient_hist'))
    args = parser.parse_args()
    if args.data:
        groups, note = read_samples(args.data), None
    else:
        groups = {}
        # Controlled synthetic samples match the reference's approximate widths
        # and locations; neither counts nor samples were recovered from the paper.
        for name,n,mu,sigma,seed in [('Group A',90,3.1,14.3,17),
                                     ('Group B',105,-6.5,23.4,53),
                                     ('Group C',100,2.5,10.,11)]:
            sample = np.random.default_rng(seed).normal(size=n)
            groups[name] = (sample-sample.mean())/sample.std()*sigma+mu
        note = 'Synthetic reconstruction; independent colored Y scales.'
    options = {}
    if args.data is None and args.bins is None:
        # Offset bins reproduce the interleaved bars visible in the reference.
        options = dict(bins={'Group A':np.arange(-70.,71.,10.),
                             'Group B':np.arange(-72.,79.,10.),
                             'Group C':np.arange(-68.,77.,8.)},
                       ylimits=[(0,29),(0,27),(0,33.5)],ytick_step=5)
    else:
        options['bins'] = args.bins if args.bins is not None else 14
    if args.reference_colors:
        options['colors'] = ['#E74C3C','#40516D','#22998D']
    fig, stats = plot_chart(groups,xlabel=args.xlabel,fit=not args.no_fit,note=note,**options)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    for suffix in ('png','pdf'):
        fig.savefig(args.output.with_suffix('.'+suffix),dpi=300,facecolor='white',
                    bbox_inches='tight',pad_inches=.2)
    args.output.with_suffix('.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf8')
    if args.data is None:
        with args.output.with_suffix('.csv').open('w',encoding='utf8',newline='') as stream:
            writer=csv.writer(stream);writer.writerow(['group','value'])
            for name,values in groups.items():
                writer.writerows((name,float(v)) for v in values)
    plt.close(fig)
    print('Saved PNG, PDF and statistics:',args.output)


if __name__ == '__main__':
    main()
```

## 37. 立体方块相关性热图

用途：展示多个变量两两之间的正负相关关系，并用浮雕方块突出矩阵结构。
输入：至少3行完整观测的数值表，或已计算的Pearson相关矩阵；2–40个变量及唯一标签。原始数据不允许缺失、非有限值或常数列；相关矩阵须对称、对角线为1、值域[-1,1]且在数值容差内半正定。不能把任意随机方阵当相关矩阵。
结构：完整N×N矩阵，固定斜投影，方形正面加两片阴影侧壁，密集细棱线、顶部阶梯轮廓、左侧行标签、底部竖排列标签与侧边Pearson r色条；PNG和PDF均由确定性矢量多边形绘制。
数据编码：正面颜色严格对应r，色条固定[-1,1]；凸起长度h=relief×(0.12+1.4×(r+1)/2)，随有符号r增加，非abs(r)。高度规则是本模板明确选定的约定，参考图未提供原高度定义。阴影侧面不用于读取相关系数；标签锚定原矩阵基座，正面随凸起向右上平移。
配色：常规调用读取当前主题的发散色阶，保留r=0中性中心；--reference-colors明确选择参考蓝色色阶。不会修改共享热图配色算法。可传入cmap覆盖，正面和色条必须同源。
来源：用户仅提供效果图，无原始代码和数据；按图重建立体结构，示例由固定种子潜在因子样本计算相关矩阵。领域标签沿用截图作版式演示，不代表该研究的实测相关关系。
局限：浮雕遮挡可能削弱逐格精确查值；需要精确读数时配合矩阵CSV或平面热图。布局不是可旋转的三维场景，也不含显著性或因果判断；不平滑、不重排、不填造缺失值。

```python
"""Oblique relief correlation matrix reconstructed from a user reference image.
Square cell faces retain matrix layout; two shaded walls connect to the base.
Color encodes signed Pearson r. Extrusion length is 0.12 + 1.4*(r+1)/2;
this height rule is a declared template choice, not recovered from the image.
"""
from pathlib import Path
import argparse
import csv
import json
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.colors import Normalize, LinearSegmentedColormap
from matplotlib.cm import ScalarMappable

for base in (Path.cwd(), *Path.cwd().parents, *Path(__file__).resolve().parents):
    found=next((p for p in (base/'_utils',base/'original/resources/assets/shared-scripts')
                if (p/'vivid_config.py').is_file()),None)
    if found is not None:
        sys.path.insert(0,str(found));break
else:
    raise RuntimeError('Run Vivid bootstrap in the workspace before using this recipe.')
from plot_utils import setup_style
from palette_maps import palette_cmap


def validate_correlation(matrix, labels):
    matrix=np.asarray(matrix,dtype=float)
    if (matrix.ndim!=2 or matrix.shape[0]!=matrix.shape[1]
            or not 2<=matrix.shape[0]<=40 or len(labels)!=len(matrix)):
        raise ValueError('Provide a square correlation matrix of 2–40 labeled variables.')
    if len(set(labels))!=len(labels) or any(not str(label).strip() for label in labels):
        raise ValueError('Variable labels must be nonempty and unique.')
    if not np.isfinite(matrix).all() or np.any(np.abs(matrix)>1+1e-8):
        raise ValueError('Correlations must be finite and within [-1,1].')
    if not np.allclose(matrix,matrix.T,atol=1e-8,rtol=0) or not np.allclose(np.diag(matrix),1,atol=1e-8,rtol=0):
        raise ValueError('Correlation matrices must be symmetric with diagonal 1.')
    if np.linalg.eigvalsh(matrix).min() < -1e-6:
        raise ValueError('The supplied matrix is not positive semidefinite; verify its source.')
    return matrix


def from_samples(samples, labels):
    values=np.asarray(samples,dtype=float)
    if (values.ndim!=2 or values.shape[0]<3 or values.shape[1]!=len(labels)
            or not np.isfinite(values).all() or np.any(values.std(axis=0)==0)):
        raise ValueError('Supply at least three complete observations and nonconstant numeric columns.')
    return validate_correlation(np.corrcoef(values,rowvar=False),labels)


def cell_geometry(row, col, size, r, relief=1.):
    """Return the two side walls and the colored square face, in draw order."""
    if not np.isfinite(relief) or relief<0:
        raise ValueError('Relief must be finite and nonnegative.')
    x,y=float(col),float(size-1-row)
    base=np.array([[x,y],[x+1,y],[x+1,y+1],[x,y+1]])
    height=relief*(.12+1.4*(float(r)+1)/2)
    face=base+height*np.array([.58,.98])
    bottom=np.array([base[0],base[1],face[1],face[0]])
    left=np.array([base[0],base[3],face[3],face[0]])
    return bottom,left,face,height


def plot_chart(matrix, labels, *, cmap=None, relief=1., note=None):
    """Deterministic 2.5D oblique projection; full N×N matrix, no smoothing.

    Only square faces use the exact colorbar mapping. Side walls are shaded
    for geometry and must not be used to read correlation values.
    """
    matrix=validate_correlation(matrix,labels)
    n=len(labels)
    setup_style()
    cmap=palette_cmap('diverging') if cmap is None else cmap
    norm=Normalize(-1,1)
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','Microsoft YaHei','DejaVu Sans'],
                         'pdf.fonttype':42,'axes.unicode_minus':False})
    fig=plt.figure(figsize=(11.4,10.2),facecolor='white')
    ax=fig.add_axes([.18,.19,.71,.76])
    # Rows at the top/back first, columns right to left: nearer cells cover
    # hidden parts of farther walls while every complete matrix cell is kept.
    faces=[]
    for row in range(n):
        for col in range(n-1,-1,-1):
            r=float(matrix[row,col]);rgb=np.asarray(cmap(norm(r))[:3])
            bottom,left,face,height=cell_geometry(row,col,n,r,relief)
            for points,color in ((bottom,rgb*.77),(left,rgb*.87),(face,rgb)):
                polygon=Polygon(points,closed=True,facecolor=color,
                                edgecolor='#273641',linewidth=.62,joinstyle='miter')
                ax.add_patch(polygon)
            faces.append(dict(row=row,col=col,r=r,height=height,face_color=rgb.tolist()))
    max_height=relief*1.52
    ax.set_xlim(-.02,n+.58*max_height+.06)
    ax.set_ylim(-.02,n+.98*max_height+.06)
    ax.set_aspect('equal')
    ax.set_xticks(np.arange(n)+.5,labels,rotation=90,fontsize=7.4 if n>16 else 9)
    ax.set_yticks(n-np.arange(n)-.5,labels,fontsize=7.4 if n>16 else 9)
    ax.tick_params(axis='both',which='both',length=0,pad=3)
    ax.grid(False)
    for spine in ax.spines.values():spine.set_visible(False)
    # Fixed limits and an unshaded colorbar preserve the sign and magnitude.
    cax=fig.add_axes([.925,.455,.013,.13])
    colorbar=fig.colorbar(ScalarMappable(norm=norm,cmap=cmap),cax=cax,
                         ticks=[-1,-.5,0,.5,1])
    cax.set_title('Pearson r',loc='left',fontsize=9,fontweight='bold',pad=5)
    colorbar.ax.tick_params(labelsize=8,length=2,pad=2)
    colorbar.outline.set_visible(False)
    if note:fig.text(.18,.04,note,fontsize=8,color='#444444')
    return fig,dict(matrix=matrix.tolist(),labels=list(labels),faces=faces,
                    height_rule='relief * (0.12 + 1.4 * (r + 1) / 2)',projection=[.58,.98])


def read_csv(path, matrix_input=False):
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:rows=list(csv.reader(stream))
    if len(rows)<2 or any(len(row)!=len(rows[0]) for row in rows):
        raise ValueError('CSV must be rectangular with a header row.')
    if matrix_input:
        labels=rows[0][1:]
        if [r[0] for r in rows[1:]]!=labels:
            raise ValueError('Matrix row and column labels and ordering must match.')
        matrix=np.array([[float(v) for v in row[1:]] for row in rows[1:]])
        return validate_correlation(matrix,labels),labels,None
    labels=rows[0];samples=np.array([[float(v) for v in row] for row in rows[1:]])
    return from_samples(samples,labels),labels,samples


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    inputs=parser.add_mutually_exclusive_group()
    inputs.add_argument('--data',type=Path,help='Observations CSV; numeric columns with variable names')
    inputs.add_argument('--matrix',type=Path,help='Square correlation CSV with row and column labels')
    parser.add_argument('--reference-colors',action='store_true',help='Explicit blue reference-style ramp')
    parser.add_argument('--relief',type=float,default=1.)
    parser.add_argument('--output',type=Path,default=Path('figures/fig_relief_correlation_heatmap'))
    args=parser.parse_args()
    if args.data or args.matrix:
        matrix,labels,samples=read_csv(args.matrix or args.data,matrix_input=args.matrix is not None)
        note=None
    else:
        # Domain labels follow the reference only to demonstrate its dense layout.
        # All observations are synthetic latent-factor data, not recovered study data.
        labels=['ACs','T-SOD','MPNs','DTPNs','CAT','GSH-PX','Unique AAs','Non-Essential AAs',
                'Essential AAs','Conditionally Essential AAs','SpNDs','Ketone compounds',
                'Hydrocarbon compounds','Alcohol compounds','MDA','T-AOC','Hardness',
                'Springiness','POD','Gumminess','Chewiness','Cohesiveness','Elasticity']
        rng=np.random.default_rng(20260916)
        latent=rng.normal(size=(360,4))
        # Heterogeneous loadings produce varied relief instead of uniform blocks.
        loadings=rng.normal(0,.3,size=(23,4))
        loadings[:,0]=rng.uniform(.3,1.2,size=23)
        loadings[:,1]+=.65*np.sin(np.arange(23)*.85)
        loadings[:,2]+=.55*np.cos(np.arange(23)*.6)
        loadings[10:15,0]*=-1
        noise=rng.uniform(.18,.58,size=23)
        samples=latent@loadings.T+rng.normal(size=(360,23))*noise
        matrix=from_samples(samples,labels)
        note='Synthetic data. Face color = Pearson r; relief increases linearly with r.'
    cmap=None
    if args.reference_colors:
        cmap=LinearSegmentedColormap.from_list('reference_blue',
                     ['#F5FCFC','#CFEAF0','#AAC5E4','#6B9FCB','#399DCB'])
    fig,stats=plot_chart(matrix,labels,cmap=cmap,relief=args.relief,note=note)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    for suffix in ('png','pdf'):
        fig.savefig(args.output.with_suffix('.'+suffix),dpi=300,facecolor='white',
                    bbox_inches='tight',pad_inches=.12)
    args.output.with_suffix('.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf8')
    with args.output.with_suffix('.csv').open('w',encoding='utf8',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(['variable',*labels])
        writer.writerows([label,*row] for label,row in zip(labels,matrix))
    if args.data is None and args.matrix is None:
        with args.output.with_name(args.output.name+'-samples.csv').open('w',encoding='utf8',newline='') as stream:
            writer=csv.writer(stream);writer.writerow(labels);writer.writerows(samples)
    plt.close(fig)
    print('Saved PNG, vector PDF, matrix CSV and geometry:',args.output)


if __name__=='__main__':main()
```

## 38. 雷达山脊融合图

用途：在同一极坐标中比较多个数据层在一组有序指标上的相对高低，并以环形局部峰增强轮廓辨识。
输入：宽表首列为5–16个唯一指标，后接2–4个同尺度数据层；所有数值有限，成本型指标先统一高低优方向。
结构：固定径向虚线形成雷达骨架；每层占一个独立基准圆环，每个指标方向叠加平滑局部峰；半透明填充、同色轮廓、基准圆、逐峰数值、外围指标名和外置图例同时保留。
数据编码：所有层共同使用全局最小值和最大值归一化峰高，数值文本保留输入尺度。峰宽固定，只形成连续标量轮廓，不承载额外数据。
配色：读取当前项目分类配色，换色不改变透明度、轮廓、圆环间距和雷达骨架。
来源：用户只提供效果图，无原始代码和数据；按图重建可见结构，演示值为人工构造。
局限：这里的“山脊”不是KDE，不表示样本分布、概率密度、样本量或不确定性；不同量纲或相反优劣方向须先转换为可比指标。

```python
"""Radar-ridgeline fusion reconstructed from a user reference image.

Each ring has a fixed radial baseline. Local Gaussian ridges at the category
spokes encode scalar values on one shared scale. They are not KDE estimates.
"""
from pathlib import Path
import argparse
import csv
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

for base in (Path.cwd(), *Path.cwd().parents, *Path(__file__).resolve().parents):
    found = next((p for p in (base/'_utils', base/'original/resources/assets/shared-scripts')
                  if (p/'vivid_config.py').is_file()), None)
    if found is not None:
        sys.path.insert(0, str(found)); break
else:
    raise RuntimeError('Run Vivid bootstrap in the workspace before using this recipe.')
from plot_utils import PALETTE, COLORS, setup_style


def read_wide_csv(path):
    """Read category + 2–4 layer columns from a rectangular wide CSV."""
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.reader(stream))
    if len(rows) < 2 or len(rows[0]) < 3 or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError('CSV must be rectangular: category plus 2–4 value columns.')
    categories = [row[0].strip() for row in rows[1:]]
    layer_names = [name.strip() for name in rows[0][1:]]
    if any(not item for item in categories + layer_names):
        raise ValueError('Category and layer labels must be nonempty.')
    values = np.array([[float(value) for value in row[1:]] for row in rows[1:]], dtype=float).T
    return categories, layer_names, values


def validate_data(categories, layer_names, values):
    values = np.asarray(values, dtype=float)
    if not 5 <= len(categories) <= 16:
        raise ValueError('Use 5–16 ordered categories for a readable radial layout.')
    if not 2 <= len(layer_names) <= 4 or values.shape != (len(layer_names), len(categories)):
        raise ValueError('Values must match 2–4 layers by all categories.')
    if (len(set(categories)) != len(categories) or len(set(layer_names)) != len(layer_names)
            or not np.isfinite(values).all()):
        raise ValueError('Labels must be unique and all values finite.')
    return values


def wrapped_delta(theta, center):
    return np.angle(np.exp(1j * (theta - center)))


def ridge_curve(theta, centers, normalized, baseline, width):
    """Add smooth local peaks to one circular baseline."""
    curve = np.full_like(theta, baseline, dtype=float)
    heights = .18 + .55 * normalized
    for center, height in zip(centers, heights):
        curve += height * np.exp(-.5 * (wrapped_delta(theta, center) / width) ** 2)
    return curve


def label_alignment(theta):
    horizontal = np.sin(theta)
    return 'left' if horizontal > .25 else 'right' if horizontal < -.25 else 'center'


def plot_chart(categories, layer_names, values, *, value_suffix='%', value_format='.1f'):
    """Draw 2–4 concentric ridgeline rings on a radar spoke skeleton.

    All values use one global min/max normalization for comparable peak heights.
    Preprocess cost-type indicators so every category has the same direction.
    """
    values = validate_data(categories, layer_names, values)
    setup_style()
    n_categories, n_layers = len(categories), len(layer_names)
    centers = np.linspace(0, 2*np.pi, n_categories, endpoint=False)
    theta = np.linspace(0, 2*np.pi, 1800, endpoint=True)
    span = float(np.ptp(values))
    normalized = np.full_like(values, .5) if span == 0 else (values-values.min())/span
    baselines = .82 + 1.20*np.arange(n_layers)
    width = .23 * (2*np.pi/n_categories)
    color_order = [1, 3, 0, 4]
    colors = [PALETTE[color_order[i] % len(PALETTE)] for i in range(n_layers)]

    fig = plt.figure(figsize=(9.0, 7.7), facecolor='white')
    ax = fig.add_subplot(111, projection='polar')
    ax.set_theta_zero_location('N'); ax.set_theta_direction(-1); ax.set_facecolor('white')
    curves = []
    for row, (name, baseline, color) in enumerate(zip(layer_names, baselines, colors)):
        curve = ridge_curve(theta, centers, normalized[row], baseline, width)
        curves.append(curve)
        ax.fill_between(theta, baseline, curve, color=color, alpha=.72, linewidth=0, zorder=2)
        ax.plot(theta, curve, color=color, linewidth=1.35, alpha=.95, zorder=3)
        ax.plot(theta, np.full_like(theta, baseline), color=color, linewidth=.65,
                alpha=.38, zorder=1)

    outer_label_radius = baselines[-1] + .18 + .55 + .42
    for angle in centers:
        ax.plot([angle, angle], [.16, outer_label_radius-.17], color=COLORS['ref_line'],
                linewidth=.7, linestyle=(0, (3, 4)), alpha=.72, zorder=0)

    for row, curve in enumerate(curves):
        for column, angle in enumerate(centers):
            idx = int(round(angle/(2*np.pi)*(len(theta)-1)))
            ax.text(angle, curve[idx]+.055,
                    f'{values[row, column]:{value_format}}{value_suffix}', fontsize=6.8,
                    ha='center', va='bottom', color='#30343B', zorder=5)

    for angle, category in zip(centers, categories):
        ax.text(angle, outer_label_radius, category, fontsize=10.2, fontweight='medium',
                ha=label_alignment(angle), va='center', color=COLORS['text'], zorder=6)

    ax.set_ylim(0, outer_label_radius+.38)
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False); ax.spines['polar'].set_visible(False)
    handles = [Patch(facecolor=color, edgecolor='none', alpha=.78, label=name)
               for name, color in zip(layer_names, colors)]
    ax.legend(handles=handles, title='数据层', loc='center left', bbox_to_anchor=(1.03, .52),
              frameon=False, handlelength=1.25, handleheight=1.25, labelspacing=.65,
              fontsize=9.2, title_fontsize=10.2)
    fig.subplots_adjust(left=.04, right=.82, top=.97, bottom=.04)
    return fig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, help='Wide CSV: category plus 2–4 comparable layers')
    parser.add_argument('--output', type=Path, default=Path('figures/fig_radar_ridgeline'))
    parser.add_argument('--suffix', default='%', help='Visible value suffix; use an empty string for none')
    parser.add_argument('--format', default='.1f', help='Python numeric format without braces')
    args = parser.parse_args()
    if args.data:
        categories, layer_names, values = read_wide_csv(args.data)
    else:
        categories = ['精度','效率','鲁棒','泛化','稳定','响应','能耗','成本','扩展','安全']
        layer_names = ['测试组','训练组','总体']
        values = np.array([[32.8,25.4,29.7,18.9,24.6,21.3,16.8,22.5,27.9,19.7],
                           [38.6,31.1,35.8,27.6,33.2,29.5,25.1,28.7,34.6,26.4],
                           [44.7,36.2,42.1,34.5,39.8,37.4,31.6,35.2,41.3,33.8]])
    fig = plot_chart(categories, layer_names, values,
                     value_suffix=args.suffix, value_format=args.format)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ('png', 'pdf'):
        fig.savefig(args.output.with_suffix('.'+suffix), dpi=320, facecolor='white',
                    bbox_inches='tight', pad_inches=.18)
    plt.close(fig)
    print('Saved PNG and PDF:', args.output)


if __name__ == '__main__': main()
```

## 39. 环形分组柱状对比图

用途：在一个环形画布上比较多个任务内的主方案与对比系列，保留原图的分组、外圈层级与强调关系。
输入：2–16个任务×2–8个系列，总柱数不超过96；值须有限非负；大类按任务提供且同名连续，说明可为空。
结构：中心留白标题、每任务一根加宽强调柱与若干比较柱、组间空隙、逐柱数值、外圈任务名及简短说明、最外层分段大类弧、左上图例。
尺度：默认within_task按各任务最小/最大值映射100/300柱长，等值统一200；柱长只在任务内可比，跨任务看原数值。shared模式改用全图共同零基准线性尺度。两模式都不改变原始数值标签和输入顺序。
配色：项目分类色板第二色为强调角色，第一色向白色背景派生比较色阶；粉彩少女展示为紫色主柱及粉色比较柱。
来源：按用户参考图重建；演示中的11任务、55数值及英文说明为图像转录，未独立核验。四个基线列是每个任务内Top1–4，不保证是跨任务固定同一模型。
局限：组内缩放会放大小数值差异，最短柱也不表示零；不适合直接比较不同任务的绝对量或未经处理的不同量纲指标。

```python
"""Grouped radial bars with task labels and outer hierarchy arcs.

Reconstructed from a user-supplied reference image. The reference layout uses explicit within-task min/max scaling. Numeric labels
retain the supplied values; shared-scale mode is available for cross-task comparisons.
"""
from pathlib import Path
import argparse
import csv
import sys
import textwrap

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from matplotlib.patches import Patch

for base in (Path.cwd(), *Path.cwd().parents, *Path(__file__).resolve().parents):
    found = next((p for p in (base / '_utils', base / 'original/resources/assets/shared-scripts')
                  if (p / 'vivid_config.py').is_file()), None)
    if found is not None:
        sys.path.insert(0, str(found))
        break
else:
    raise RuntimeError('Run Vivid bootstrap in the workspace before using this recipe.')
from plot_utils import PALETTE, COLORS, setup_style


def _labels(items, name, count=None, unique=False, allow_empty=False):
    if isinstance(items, (str, bytes)):
        raise ValueError(f'{name} must be a list of labels.')
    labels = [str(item).strip() for item in items]
    if count is not None and len(labels) != count:
        raise ValueError(f'{name} must contain {count} labels.')
    if not allow_empty and any(not label for label in labels):
        raise ValueError(f'{name} labels must be nonempty.')
    if unique and len(set(labels)) != len(labels):
        raise ValueError(f'{name} labels must be unique.')
    return labels


def validate_data(task_names, model_names, values, major_groups=None, task_details=None,
                  highlight_index=0):
    tasks = _labels(task_names, 'Task', unique=True)
    models = _labels(model_names, 'Model', unique=True)
    if not 2 <= len(tasks) <= 16 or not 2 <= len(models) <= 8:
        raise ValueError('Use 2–16 tasks and 2–8 models.')
    if len(tasks) * len(models) > 96:
        raise ValueError('At most 96 bars are supported; split a larger comparison into panels.')
    data = np.asarray(values, dtype=float)
    if data.shape != (len(tasks), len(models)):
        raise ValueError('Values must have shape (number of tasks, number of models).')
    if not np.isfinite(data).all() or (data < 0).any():
        raise ValueError('Values must be finite and nonnegative; missing values are not zero.')
    if not isinstance(highlight_index, (int, np.integer)) or not 0 <= highlight_index < len(models):
        raise ValueError('highlight_index must identify an existing model column.')
    groups = None if major_groups is None else _labels(major_groups, 'Major group', len(tasks))
    if groups is not None:
        runs = [group for i, group in enumerate(groups) if i == 0 or group != groups[i-1]]
        if len(runs) != len(set(runs)):
            raise ValueError('Tasks in the same major group must be contiguous; input order is preserved.')
    details = ([''] * len(tasks) if task_details is None else
               _labels(task_details, 'Task detail', len(tasks), allow_empty=True))
    return tasks, models, data, groups, details


def _upright(rotation):
    """Return an equivalent text rotation that is never upside down."""
    return (rotation + 90) % 180 - 90


def _model_styles(count, highlight_index, background):
    """Derive one emphasis color and a four-step comparison tint from the palette."""
    highlight = PALETTE[1 % len(PALETTE)]
    base = np.array(to_rgb(PALETTE[0]))
    pale = np.array(to_rgb(background))
    colors = [None] * count
    colors[highlight_index] = highlight
    comparison = [i for i in range(count) if i != highlight_index]
    for position, column in enumerate(comparison):
        mix = 0.0 if len(comparison) == 1 else .58 * position / (len(comparison) - 1)
        colors[column] = tuple(base * (1 - mix) + pale * mix)
    return colors


def _layout_angles(task_count, model_count, groups, highlight_index):
    """Wider emphasis bars, small task gaps and larger hierarchy gaps."""
    widths = np.ones(model_count)
    widths[highlight_index] = 1.8
    bar_gap, task_gap, hierarchy_gap = .175, 1.1, 3.3
    span = widths.sum() + bar_gap * (model_count - 1)
    boundary = [groups is not None and groups[i] != groups[(i + 1) % task_count]
                for i in range(task_count)]
    gaps = np.array([hierarchy_gap if major else task_gap for major in boundary])
    factor = 2 * np.pi / (task_count * span + gaps.sum())
    cursor = gaps[-1] / 2
    task_centers, angles, starts, ends = [], [], [], []
    for i in range(task_count):
        starts.append(cursor * factor)
        task_centers.append((cursor + span / 2) * factor)
        row = []
        for j, width in enumerate(widths):
            row.append((cursor + width / 2) * factor)
            cursor += width + (bar_gap if j < model_count - 1 else 0)
        angles.append(row)
        ends.append(cursor * factor)
        cursor += gaps[i]
    return np.asarray(angles), np.asarray(task_centers), widths * factor, starts, ends


def plot_chart(task_names, model_names, values, major_groups=None, task_details=None,
               center_label='方案对比', highlight_index=0, *, value_format='.2f',
               value_suffix='', show_values=True, show_legend=True, scale_max=None,
               scale_mode='within_task', baseline_label=None):
    """Reproduce the reference composition without silently changing data semantics.

    within_task: each task maps its minimum/maximum to radial lengths 100/300.
    Equal values use length 200. The visible values always remain the originals.
    shared: lengths are 300 * value / scale_max, with one zero baseline.
    Input row/column order is preserved. Highlighting does not imply first place.
    """
    tasks, models, data, groups, details = validate_data(
        task_names, model_names, values, major_groups, task_details, highlight_index)
    setup_style()
    maximum = float(data.max())
    scale = maximum if scale_max is None else float(scale_max)
    if scale_max is not None and (not np.isfinite(scale) or scale <= 0 or scale < maximum):
        raise ValueError('scale_max must be finite, positive, and cover all values.')
    if scale_mode not in ('within_task', 'shared'):
        raise ValueError("scale_mode must be 'within_task' or 'shared'.")
    if scale_mode == 'within_task' and scale_max is not None:
        raise ValueError('scale_max applies only to shared-scale mode.')
    if scale_mode == 'within_task':
        minima = data.min(axis=1, keepdims=True)
        ranges = np.ptp(data, axis=1, keepdims=True)
        relative = np.divide(data - minima, ranges, out=np.full_like(data, .5), where=ranges != 0)
        lengths = 100 + 200 * relative
    else:
        lengths = 300 * data / (scale if scale > 0 else 1)
    format(0.0, value_format)
    ntasks, nmodels = data.shape
    dense = ntasks * nmodels > 64
    background = '#FFFFFF'
    ink, arc_color = '#725E4D', '#BFB19E'
    from matplotlib.font_manager import fontManager
    available = {font.name for font in fontManager.ttflist}
    fonts = [name for name in ('Times New Roman', 'DejaVu Serif', 'Microsoft YaHei',
                              'Noto Sans CJK SC', 'WenQuanYi Zen Hei') if name in available]
    # Pixel-equivalent reference geometry: 1331 x 1252, center (660, 653), R=570.
    factor = 1.12 if dense else 1.0
    fig = plt.figure(figsize=(13.31 * factor, 12.52 * factor), facecolor=background)
    ax = fig.add_axes([40 / 1331, -21 / 1252, 1240 / 1331, 1240 / 1252], projection='polar')
    ax.set_facecolor(background)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    angles, centers, widths, starts, ends = _layout_angles(ntasks, nmodels, groups, highlight_index)
    colors = _model_styles(nmodels, highlight_index, background)
    bottom = 165.0
    label_size = 8.5 if dense else 10.2
    comparison = [i for i in range(nmodels) if i != highlight_index]
    for task in range(ntasks):
        for model in range(nmodels):
            angle, length, color = angles[task, model], lengths[task, model], colors[model]
            ax.bar(angle, length, width=widths[model], bottom=bottom, color=color,
                   edgecolor='none', linewidth=0, zorder=3)
            if show_values:
                rotation = _upright(90 - np.degrees(angle))
                outward_right = np.cos(np.radians(rotation) - (np.pi / 2 - angle)) > 0
                inside = length >= 75
                radius = bottom + length - 13 if inside else bottom + length + 6
                alignment = ('right' if outward_right else 'left') if inside else (
                    'left' if outward_right else 'right')
                text_color = ('white' if model in (highlight_index, comparison[0]) else ink) if inside else ink
                ax.text(angle, radius, f'{data[task, model]:{value_format}}{value_suffix}',
                        rotation=rotation, rotation_mode='anchor', ha=alignment, va='center',
                        fontsize=label_size, fontfamily=fonts, fontweight='bold', color=text_color, zorder=6)
    wrap_width = max(12, int(240 / ntasks))
    for angle, task, detail in zip(centers, tasks, details):
        rotation = _upright(-np.degrees(angle))
        lower_half = np.cos(angle) < 0
        task_radius, detail_radius = (500, 535) if lower_half else (535, 500)
        ax.text(angle, task_radius, textwrap.fill(task, width=wrap_width), ha='center', va='center',
                rotation=rotation, rotation_mode='anchor', fontfamily=fonts,
                fontsize=14 if dense else 17, fontweight='bold', color=ink, zorder=7)
        if detail:
            detail_font = min(10 if dense else 12.3, 445 / max(30, len(detail)))
            ax.text(angle, detail_radius, detail,
                    ha='center', va='center', rotation=rotation, rotation_mode='anchor',
                    fontfamily=fonts, fontsize=detail_font, color=ink, zorder=7)
    if groups is not None:
        start = 0
        for end in range(1, ntasks + 1):
            if end == ntasks or groups[end] != groups[start]:
                first, last = starts[start] - .035, ends[end - 1] + .035
                theta = np.linspace(first, last, max(32, (end - start) * 40))
                ax.plot(theta, np.full_like(theta, 570), color=arc_color, linewidth=2.5, zorder=1)
                middle = (first + last) / 2
                if middle > 1.5 * np.pi and len(groups[start]) > 18:
                    middle = last - .30 * (last - first)
                # A long group title follows its tangent, exactly as the reference.
                ax.text(middle, 593, groups[start], ha='center', va='center',
                        rotation=_upright(-np.degrees(middle)), rotation_mode='anchor',
                        fontfamily=fonts, fontsize=16 if dense else 19,
                        fontweight='bold', color='#A18E7B', zorder=8)
                start = end
    title = str(center_label)
    title = textwrap.fill(title, width=18) if len(title) > 18 and '\n' not in title else title
    import unicodedata
    longest = max((sum(2 if unicodedata.east_asian_width(char) in ('W', 'F') else 1
                       for char in line) for line in title.splitlines()), default=0)
    fontsize = min(35.5, 35.5 * 11 / max(1, longest))
    ax.text(.5, .5, title, transform=ax.transAxes, ha='center', va='center',
            fontsize=fontsize, fontfamily=fonts, fontweight='bold', color=colors[highlight_index], zorder=9)
    ax.set_ylim(0, 620)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    ax.spines['polar'].set_visible(False)
    if show_legend:
        if baseline_label is not None:
            from matplotlib.legend_handler import HandlerTuple
            class TopAlignedTuple(HandlerTuple):
                def create_artists(self, legend, orig_handle, xdescent, ydescent, width, height, fontsize, trans):
                    items = super().create_artists(legend, orig_handle, xdescent, ydescent,
                                                   width, height, fontsize, trans)
                    offset = max(0, len(str(baseline_label).splitlines()) - 1) * fontsize * .60
                    for item in items:
                        item.set_y(item.get_y() + offset)
                    return items
            handles = [Patch(facecolor=colors[highlight_index], edgecolor='none'),
                       tuple(Patch(facecolor=colors[i], edgecolor='none') for i in comparison)]
            labels = [models[highlight_index], baseline_label]
            legend = fig.legend(handles, labels, handler_map={tuple: TopAlignedTuple(ndivide=None, pad=.10)},
                                loc='upper left', bbox_to_anchor=(.012, .981), borderaxespad=0,
                                frameon=False, fontsize=15.8, handlelength=1.15,
                                handleheight=1.0, labelspacing=.35, handletextpad=.6)
        else:
            handles = [Patch(facecolor=color, edgecolor='none', label=name)
                       for name, color in zip(models, colors)]
            legend = fig.legend(handles=handles, loc='upper left', bbox_to_anchor=(.012, .981),
                                borderaxespad=0, frameon=False, fontsize=12.0 if nmodels > 5 else 14.0,
                                handlelength=1.15, handleheight=1.0, labelspacing=.25)
        for text in legend.get_texts():
            text.set_fontfamily(fonts)
            text.set_color(ink)
    return fig


def read_wide_csv(path):
    """Read task names followed by model value columns, preserving table order."""
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.reader(stream))
    if len(rows) < 3 or len(rows[0]) < 3 or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError('CSV must be rectangular: task plus 2–8 model columns, at least 2 tasks.')
    tasks = [row[0].strip() for row in rows[1:]]
    models = [cell.strip() for cell in rows[0][1:]]
    values = np.array([[float(cell) for cell in row[1:]] for row in rows[1:]])
    validate_data(tasks, models, values)
    return tasks, models, values


def read_metadata_csv(path, task_names):
    """Join task/group/detail metadata by name; never silently reorder task data."""
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.reader(stream))
    if len(rows) < 2 or len(rows[0]) != 3 or any(len(row) != 3 for row in rows):
        raise ValueError('Metadata CSV requires three columns: task, major group, short detail.')
    by_task = {}
    for task, group, detail in rows[1:]:
        task = task.strip()
        if task in by_task:
            raise ValueError(f'Duplicate metadata task: {task}')
        by_task[task] = (group.strip(), detail.strip())
    if set(by_task) != set(task_names):
        raise ValueError('Metadata tasks must match the data tasks exactly.')
    return [by_task[task][0] for task in task_names], [by_task[task][1] for task in task_names]


def demo_data():
    """Values transcribed from the reference image; not independently verified."""
    return dict(
        task_names=['Visual Prompt', 'Grounding', 'Dense', 'Referring', 'Robo Point',
                    'Referring Point', 'Grounding Point', 'Dense Point', 'GUI', 'OCR', 'Layout'],
        model_names=['GroundingPI', 'Top 1 baseline', 'Top 2 baseline', 'Top 3 baseline', 'Top 4 baseline'],
        values=np.array([[73.59, 65.84, 56.52, 54.85, 43.26], [59.50, 58.86, 58.03, 56.80, 56.59],
                         [57.48, 55.24, 51.17, 51.08, 40.98], [84.89, 82.52, 79.02, 78.56, 78.31],
                         [75.12, 81.08, 66.61, 65.39, 63.33], [89.71, 85.51, 84.56, 82.29, 79.96],
                         [82.15, 79.66, 74.89, 70.94, 70.83], [74.37, 76.10, 70.54, 70.26, 67.69],
                         [78.92, 92.58, 77.73, 72.24, 70.09], [54.79, 48.89, 47.34, 45.20, 43.30],
                         [79.95, 74.27, 71.64, 69.06, 61.50]]),
        major_groups=['Bounding Boxes'] * 4 + ['Point'] * 5 + ['Text & Bounding Boxes'] * 2,
        task_details=['FSC147-test, Dense200, COCO, LVIS', 'COCO, LVIS', 'Dense200, VisDrone',
                      'HumanRef, RefCOCOg*5', 'RoboSpatial, RefSpatial*3', 'HumanRef, RefCOCOg*5',
                      'COCO, LVIS', 'Dense200, VisDrone', 'Screenspot-Pro, ScreenSpot-V2, OSWorld-G',
                      'HierText, ICDAR2015, TotalText, SROIE', 'DocLayNet, M6Doc'],
        center_label='GroundingPI',
        baseline_label='Best Four models\nAcross 45 Baselines\nIncluding GPT-6 Astra')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, help='Wide CSV: task followed by model columns')
    parser.add_argument('--metadata', type=Path, help='CSV columns: task, major group, short detail')
    parser.add_argument('--output', type=Path, default=Path('figures/fig_grouped_radial_bar'))
    parser.add_argument('--center-label', default=None)
    parser.add_argument('--highlight-index', type=int, default=0)
    parser.add_argument('--format', default='.2f')
    parser.add_argument('--suffix', default='')
    parser.add_argument('--scale-max', type=float)
    parser.add_argument('--scale-mode', choices=['within_task', 'shared'], default='within_task')
    parser.add_argument('--baseline-label', default=None)
    parser.add_argument('--hide-values', action='store_true')
    parser.add_argument('--hide-legend', action='store_true')
    args = parser.parse_args()
    if args.metadata and not args.data:
        parser.error('--metadata requires --data')
    if args.data:
        tasks, models, values = read_wide_csv(args.data)
        data = dict(task_names=tasks, model_names=models, values=values)
        if args.metadata:
            data['major_groups'], data['task_details'] = read_metadata_csv(args.metadata, tasks)
    else:
        data = demo_data()
    if args.center_label is not None:
        data['center_label'] = args.center_label
    if args.baseline_label is not None:
        data['baseline_label'] = args.baseline_label
    fig = plot_chart(**data, highlight_index=args.highlight_index, value_format=args.format,
                     value_suffix=args.suffix, scale_max=args.scale_max, scale_mode=args.scale_mode,
                     show_values=not args.hide_values, show_legend=not args.hide_legend)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for extension in ('png', 'pdf', 'svg'):
        fig.savefig(args.output.with_suffix('.' + extension), dpi=200, facecolor=fig.get_facecolor(),
                    bbox_inches=None, pad_inches=0)
    plt.close(fig)
    print('Saved PNG, PDF and SVG:', args.output)


if __name__ == '__main__':
    main()
```
