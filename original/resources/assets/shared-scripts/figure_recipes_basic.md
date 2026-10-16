# 通用基础图表 — 高级美化代码范例（升级版）

适用于所有场景（竞赛/学术/统计建模）。灵感来自顶级中文学术期刊的高端可视化风格：渐变填充、KDE 等高线背景、Rain Cloud 分布图、箭头标注框等。
所有范例假设已执行 `from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten; setup_style()`。

---

## 1. 分组柱状图（Grouped Bar）— 淡色填充 + 原色边框 + 参考线 + 顶部数值 + 最优高亮

**场景**：多方法在多指标上的对比，如不同模型在 Accuracy/F1/Recall 上的得分对比。
**要点**：淡色填充+原色边框柱体、水平参考线标注均值、顶部数值标注、最优值★高亮、误差线、淡色背景渐变 + 柱子阴影。

```python
import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

categories = ['指标A', '指标B', '指标C', '指标D']
groups = {
    '本文方法': [85.2, 78.3, 92.1, 88.5],
    '方法B':   [82.1, 80.5, 88.7, 85.2],
    '方法C':   [79.8, 75.2, 85.3, 82.0],
}
stds = {
    '本文方法': [1.2, 1.5, 0.8, 1.0],
    '方法B':   [1.8, 2.0, 1.3, 1.5],
    '方法C':   [2.1, 2.5, 1.6, 1.8],
}

fig, ax = plt.subplots(figsize=(9, 5.5))
highlight_index = 0  # 重点系列的位置，与显示名称无关
x = np.arange(len(categories))
n = len(groups)
width = 0.22

# 淡蓝背景渐变
ax.axhspan(0, max(max(v) for v in groups.values()) * 1.2, alpha=0.03, color=PALETTE[0], zorder=0)

for i, (name, vals) in enumerate(groups.items()):
    offset = (i - n / 2 + 0.5) * width
    is_ours = i == highlight_index
    # 柱子阴影
    ax.bar(x + offset + 0.02, vals, width, color='#cccccc', alpha=0.08, zorder=1)
    # ★ 主柱子：淡色填充 + 原色边框
    bars = ax.bar(x + offset, vals, width, yerr=stds[name], capsize=3,
                  color=_lighten(PALETTE[i], 0.4), edgecolor=PALETTE[i],
                  linewidth=1.5 if is_ours else 1.2,
                  label=name, zorder=2,
                  error_kw={'elinewidth': 0.8, 'capthick': 0.6, 'color': COLORS['text']})

    for j, (bar, v, s) in enumerate(zip(bars, vals, stds[name])):
        all_vals_j = [groups[g][j] for g in groups]
        is_best = (v == max(all_vals_j))
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + s + 0.5,
                f'{"★" if is_best else ""}{v:.1f}',
                ha='center', va='bottom', fontsize=7.5,
                fontweight='bold' if is_best else 'normal',
                color=PALETTE[i] if is_best else COLORS['text'],
                bbox=dict(boxstyle='round,pad=0.1', facecolor='white', edgecolor='none', alpha=0.7) if is_best else {})

# 水平参考线：全局均值
global_mean = np.mean([v for vals in groups.values() for v in vals])
ax.axhline(y=global_mean, color=COLORS['ref_line'], linestyle='--', linewidth=0.8, alpha=0.4)
ax.text(len(categories) - 0.3, global_mean + 0.5, f'均值 {global_mean:.1f}',
        fontsize=8, color=COLORS['ref_line'], ha='right', style='italic',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='none', alpha=0.8))

ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=10)
ax.set_ylabel('得分', fontsize=11)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='best')
ax.set_ylim(0, max(max(v) for v in groups.values()) * 1.2)
ax.grid(axis='y', alpha=0.12, linestyle='--', color=COLORS['grid'])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_grouped_bar.pdf')
```

**★ 防遮挡技巧（分组柱状图专用）：**
```python
# 1. 顶部数值标签：bar_height + 0.01，不要放在柱子内部（柱子矮时会溢出）
# 2. 柱子多（>6 组 × 4 指标）时：fontsize 降到 7，或只标注最优值
# 3. ylim 上方留 15%：ax.set_ylim(0, max_val * 1.15)，给标签留空间
# 4. x 轴标签长（中文>4 字）：rotation=15, ha='right'，防止重叠
# 5. 图例放在图外上方：bbox_to_anchor=(0.5, 1.12), loc='center', ncol=N
# 6. 参考线标注放在图右边缘：x=len(categories)-0.5，不要放在数据密集区
```

---

## 2. 堆叠柱状图（Stacked Bar）— 淡色填充 + 原色边框 + 趋势线 + 自动对比度标签 + 同比变化

**场景**：展示各部分占总量的构成变化，如产业结构变迁、各类别占比随年份变化。
**要点**：淡色填充+原色边框堆叠柱、顶部趋势折线、自动对比度百分比标签（深色块白字/浅色块黑字）、末端同比变化标注、微妙网格。

```python
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

categories = ['2019', '2020', '2021', '2022', '2023']
components = {
    '第一产业': [8.2, 7.8, 7.5, 7.2, 6.9],
    '第二产业': [38.5, 37.2, 36.8, 36.1, 35.5],
    '第三产业': [53.3, 55.0, 55.7, 56.7, 57.6],
}

fig, ax = plt.subplots(figsize=(8, 5.5))
x = np.arange(len(categories))
bottom = np.zeros(len(categories))
bar_width = 0.55

for i, (name, vals) in enumerate(components.items()):
    vals_arr = np.array(vals)
    # ★ 淡色填充 + 原色边框
    bars = ax.bar(x, vals_arr, bar_width, bottom=bottom,
                  color=_lighten(PALETTE[i], 0.4), edgecolor=PALETTE[i],
                  linewidth=1.2, label=name, zorder=2)

    # 自动对比度标签：深色块白字 / 浅色块黑字
    for bar, v, b in zip(bars, vals_arr, bottom):
        if v > 5:
            r, g, b_c = mcolors.to_rgb(_lighten(PALETTE[i], 0.4))
            luminance = 0.299 * r + 0.587 * g + 0.114 * b_c
            text_color = 'white' if luminance < 0.6 else COLORS['text']
            ax.text(bar.get_x() + bar.get_width() / 2, b + v / 2,
                    f'{v:.1f}%', ha='center', va='center', fontsize=8,
                    color=text_color, fontweight='bold')
    bottom += vals_arr

# 顶部趋势折线（总量）
totals = bottom
ax.plot(x, totals, 'o-', color=COLORS['text'], linewidth=1.5, markersize=5,
        markeredgecolor='white', markeredgewidth=1, zorder=3)
for xi, t in zip(x, totals):
    ax.text(xi, t + 1.0, f'{t:.1f}', ha='center', va='bottom', fontsize=8,
            fontweight='bold', color=COLORS['text'])

# 末端同比变化标注
for i, (name, vals) in enumerate(components.items()):
    change = vals[-1] - vals[-2]
    sign = '+' if change >= 0 else ''
    color = COLORS['up'] if change >= 0 else COLORS['down']
    y_pos = sum(components[n][-1] for n in list(components.keys())[:i]) + vals[-1] / 2
    ax.annotate(f'{sign}{change:.1f}%', xy=(len(categories) - 1 + 0.35, y_pos),
                fontsize=7, color=color, fontweight='bold', va='center',
                bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                          edgecolor=color, alpha=0.8, linewidth=0.5))

ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=10)
ax.set_ylabel('占比 (%)', fontsize=11)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='upper left')
ax.grid(axis='y', alpha=0.12, linestyle='--', color=COLORS['grid'])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_stacked_bar.pdf')
```

**★ 防遮挡技巧（堆叠柱状图专用）：**
```python
# 1. 百分比标签只在块高度 >5% 时显示：太小的块标签会溢出
# 2. 趋势折线标注放在柱子上方：不要和堆叠块内的标签重叠
# 3. 同比变化标注放在最右侧柱子外：x = len(categories) - 1 + 0.35
# 4. 图例放在左上角：因为通常数据在右侧增长，左上角空间最大
```

---

## 3. 折线图（渐变填充 + 极值标注箭头 + 微妙网格）

**场景**：时序趋势展示、多方法性能随参数/epoch 变化、年度指标对比。
**要点**：渐变填充置信带、极值点★标注+箭头、白色描边标记点、微妙网格背景。

```python
import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

x = np.arange(2015, 2025)
series = {
    '本文方法': np.array([72, 75, 78, 80, 83, 85, 87, 89, 91, 92]),
    '方法B':    np.array([70, 73, 76, 79, 81, 82, 84, 86, 88, 89]),
    '方法C':    np.array([68, 70, 72, 75, 77, 79, 80, 82, 83, 84]),
}
markers = ['o', 's', '^']
stds = {k: np.random.uniform(1.5, 3.0, len(v)) for k, v in series.items()}

fig, ax = plt.subplots(figsize=(8, 5))
highlight_index = 0  # 重点系列的位置，与显示名称无关

# 淡色背景渐变
ax.axhspan(min(min(v) for v in series.values()) - 5,
           max(max(v) for v in series.values()) + 5,
           alpha=0.02, color=PALETTE[0], zorder=0)

for i, (name, y) in enumerate(series.items()):
    is_ours = i == highlight_index
    noise = stds[name]

    # 渐变填充置信带
    for layer, alpha in enumerate([0.15, 0.08, 0.03]):
        ax.fill_between(x, y - noise * (1 - layer * 0.2), y + noise * (1 - layer * 0.2),
                        alpha=alpha, color=PALETTE[i], linewidth=0)

    # 主折线
    ax.plot(x, y, f'{markers[i]}-', color=PALETTE[i],
            linewidth=2.5 if is_ours else 1.8, markersize=7 if is_ours else 5,
            markeredgecolor='white', markeredgewidth=1.2, label=name, zorder=3)

    # 极值标注（最大值）
    max_idx = np.argmax(y)
    ax.scatter(x[max_idx], y[max_idx], s=120 if is_ours else 80, color=PALETTE[i],
               edgecolor='white', linewidth=2, zorder=4, marker='*')
    if is_ours:
        ax.annotate(f'★ {y[max_idx]:.1f}',
                    xy=(x[max_idx], y[max_idx]),
                    xytext=(x[max_idx] - 1.5, y[max_idx] + 3),
                    fontsize=9, fontweight='bold', color=PALETTE[i],
                    arrowprops=dict(arrowstyle='->', color=PALETTE[i], lw=1.2),
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                              edgecolor=PALETTE[i], alpha=0.9))

ax.set_xlabel('年份', fontsize=11)
ax.set_ylabel('准确率 (%)', fontsize=11)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='best')
ax.set_xticks(x)
ax.grid(alpha=0.12, linestyle='--', color=COLORS['grid'])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_line.pdf')
```

**★ 防遮挡技巧（折线图专用）：**
```python
# 1. 极值标注箭头方向：根据数据走势选择 xytext 偏移方向，避免和折线重叠
# 2. 置信带层数 3 层渐变：按源码由外向内叠加 alpha=0.15、0.08、0.03；内层累计叠色更深
# 3. 多系列（>4 条）时：只标注本文方法的极值，其余省略
# 4. x 轴标签密集时：每隔 2 个标注一次，或 rotation=30
```

---

## 4. 散点图（KDE 等高线 + 柔和边际密度 + 回归公式框 + 年份标签）

**场景**：两变量相关性探索、模型预测值 vs 实际值、数据初步探索。
**要点**：KDE 等高线背景、边际密度分布、拟合线+置信带、R² 标注框、半透明散点防重叠。

```python
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.stats import gaussian_kde
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
n = 150
x = np.random.uniform(1, 10, n)
y = 2.5 * x + np.random.normal(0, 3, n)

fig = plt.figure(figsize=(7, 6))
gs = gridspec.GridSpec(2, 2, width_ratios=[4, 1], height_ratios=[1, 4],
                       wspace=0.05, hspace=0.05)

ax_main = fig.add_subplot(gs[1, 0])
ax_top = fig.add_subplot(gs[0, 0], sharex=ax_main)
ax_right = fig.add_subplot(gs[1, 1], sharey=ax_main)

# KDE 等高线背景
xy = np.vstack([x, y])
kde = gaussian_kde(xy, bw_method=0.3)
xg = np.linspace(x.min() - 1, x.max() + 1, 80)
yg = np.linspace(y.min() - 3, y.max() + 3, 80)
Xg, Yg = np.meshgrid(xg, yg)
Z = kde(np.vstack([Xg.ravel(), Yg.ravel()])).reshape(Xg.shape)
ax_main.contourf(Xg, Yg, Z, levels=8, cmap='Blues', alpha=0.15)
ax_main.contour(Xg, Yg, Z, levels=5, colors=PALETTE[0], alpha=0.2, linewidths=0.5)

# 散点
ax_main.scatter(x, y, s=30, alpha=0.5, color=PALETTE[0], edgecolor='white', linewidth=0.5, zorder=3)

# 拟合线 + 置信带
z = np.polyfit(x, y, 1)
p = np.poly1d(z)
x_fit = np.linspace(x.min(), x.max(), 100)
ax_main.plot(x_fit, p(x_fit), color=PALETTE[1], linewidth=2, zorder=4)
residuals = y - p(x)
se = residuals.std()
for layer, alpha in enumerate([0.15, 0.08, 0.03]):
    ax_main.fill_between(x_fit, p(x_fit) - 1.96 * se * (0.3 + layer * 0.1),
                         p(x_fit) + 1.96 * se * (0.3 + layer * 0.1),
                         alpha=alpha, color=PALETTE[1], linewidth=0)

# R² 标注框
r2 = 1 - np.sum(residuals ** 2) / np.sum((y - y.mean()) ** 2)
ax_main.text(0.05, 0.92, f'R² = {r2:.3f}\ny = {z[0]:.2f}x + {z[1]:.2f}\nn = {n}',
             transform=ax_main.transAxes, fontsize=9, verticalalignment='top',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                       edgecolor=PALETTE[0], alpha=0.9, linewidth=0.8))

# 边际密度（顶部）
kde_x = gaussian_kde(x, bw_method=0.3)
xd = np.linspace(x.min() - 1, x.max() + 1, 200)
ax_top.fill_between(xd, kde_x(xd), alpha=0.2, color=PALETTE[0])
ax_top.plot(xd, kde_x(xd), color=PALETTE[0], linewidth=1.2)
ax_top.set_yticks([])
ax_top.spines['top'].set_visible(False)
ax_top.spines['right'].set_visible(False)
ax_top.spines['left'].set_visible(False)
plt.setp(ax_top.get_xticklabels(), visible=False)

# 边际密度（右侧）
kde_y = gaussian_kde(y, bw_method=0.3)
yd = np.linspace(y.min() - 3, y.max() + 3, 200)
ax_right.fill_betweenx(yd, kde_y(yd), alpha=0.2, color=PALETTE[0])
ax_right.plot(kde_y(yd), yd, color=PALETTE[0], linewidth=1.2)
ax_right.set_xticks([])
ax_right.spines['top'].set_visible(False)
ax_right.spines['right'].set_visible(False)
ax_right.spines['bottom'].set_visible(False)
plt.setp(ax_right.get_yticklabels(), visible=False)

ax_main.set_xlabel('自变量 X', fontsize=11)
ax_main.set_ylabel('因变量 Y', fontsize=11)
ax_main.grid(alpha=0.12, linestyle='--', color=COLORS['grid'])
ax_main.spines['top'].set_visible(False)
ax_main.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_scatter.pdf')
```

**★ 防遮挡技巧（散点图专用）：**
```python
# 1. R² 标注框放在左上角：因为拟合线通常从左下到右上，左上角空间最大
# 2. KDE 等高线用极淡色（alpha=0.15）：不要遮挡散点
# 3. 散点数 >500 时：降低 alpha 到 0.3，或用 hexbin 替代
# 4. 边际密度图高度控制在主图的 1/5：不要喧宾夺主
```

---

## 5. 热力图（fig.add_axes 手动布局 + 聚类树状图 + 下三角遮罩 + 分组色条）

**场景**：相关系数矩阵、混淆矩阵、任何二维网格数据的可视化。
**要点**：聚类树状图排序、下三角遮罩（相关矩阵）、分组色条、数值标注自动对比度。

```python
import numpy as np; from _utils.palette_maps import palette_cmap, palette_stops, contrast_text
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
labels = ['特征A', '特征B', '特征C', '特征D', '特征E', '特征F']
n = len(labels)
# 生成相关矩阵
data = np.random.randn(100, n)
corr = np.corrcoef(data.T)

fig = plt.figure(figsize=(8, 7))
gs = gridspec.GridSpec(2, 2, width_ratios=[1, 6], height_ratios=[1, 6],
                       wspace=0.02, hspace=0.02)

# 顶部树状图
ax_dtop = fig.add_subplot(gs[0, 1])
Z = linkage(pdist(corr), method='ward')
dn = dendrogram(Z, ax=ax_dtop, no_labels=True, color_threshold=0,
                above_threshold_color=PALETTE[0])
ax_dtop.set_xticks([])
ax_dtop.set_yticks([])
for spine in ax_dtop.spines.values():
    spine.set_visible(False)

# 左侧树状图
ax_dleft = fig.add_subplot(gs[1, 0])
dendrogram(Z, ax=ax_dleft, orientation='left', no_labels=True,
           color_threshold=0, above_threshold_color=PALETTE[0])
ax_dleft.set_xticks([])
ax_dleft.set_yticks([])
for spine in ax_dleft.spines.values():
    spine.set_visible(False)

# 主热力图（下三角遮罩）
ax_heat = fig.add_subplot(gs[1, 1])
mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
corr_masked = np.ma.array(corr, mask=mask)

im = ax_heat.imshow(corr_masked, cmap=palette_cmap('diverging'), vmin=-1, vmax=1, aspect='auto')
ax_heat.set_xticks(range(n))
ax_heat.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
ax_heat.set_yticks(range(n))
ax_heat.set_yticklabels(labels, fontsize=9)

# 数值标注（自动对比度）
for i in range(n):
    for j in range(n):
        if not mask[i, j]:
            val = corr[i, j]
            text_color = contrast_text(im.cmap(im.norm(val)))
            ax_heat.text(j, i, f'{val:.2f}', ha='center', va='center',
                         fontsize=7.5, color=text_color, fontweight='bold' if abs(val) > 0.7 else 'normal')

# 遮罩上三角为白色
for i in range(n):
    for j in range(i + 1, n):
        ax_heat.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=True,
                                         facecolor='white', edgecolor='white', zorder=2))

fig.colorbar(im, ax=ax_heat, shrink=0.6, label='相关系数', pad=0.08)
fig.tight_layout()
save_fig(fig, 'figures/fig_heatmap.pdf')
```

**★ 防遮挡技巧（热力图专用）：**
```python
# 1. 数值标注字号根据矩阵大小调整：n<=8 用 8pt，n>8 用 6.5pt
# 2. 标签长（中文>3 字）：rotation=45, ha='right'
# 3. 色条标签放在右侧：不要和矩阵标签重叠
# 4. 树状图高度控制在主图的 1/6：不要喧宾夺主
```

---

## 6. 环形图（淡色填充 + 原色边框 + 外部连线标签 + 变化率标注）

**场景**：类别占比展示，如市场份额、数据集类别分布、资源分配比例。
**要点**：淡色填充+原色边框环形、外部连线标签（防重叠）、中心总计文字、变化率标注。

```python
import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

labels = ['类别A', '类别B', '类别C', '类别D', '类别E']
sizes = [35, 25, 20, 12, 8]
prev_sizes = [32, 27, 19, 14, 8]  # 上期数据（用于计算变化率）
explode = [0.03] * len(labels)

fig, ax = plt.subplots(figsize=(7, 6))

# ★ 淡色填充 + 原色边框
wedge_colors = [_lighten(PALETTE[i], 0.4) for i in range(len(labels))]
edge_colors = [PALETTE[i] for i in range(len(labels))]

wedges, texts = ax.pie(
    sizes, labels=None, startangle=90,
    colors=wedge_colors, explode=explode,
    wedgeprops=dict(width=0.45, edgecolor='white', linewidth=0),
    pctdistance=0.75)

# 原色边框（单独绘制，避免白色分隔线被覆盖）
for wedge, ec in zip(wedges, edge_colors):
    wedge.set_edgecolor(ec)
    wedge.set_linewidth(1.5)

# 外部连线标签 + 变化率
for i, (wedge, label, size, prev) in enumerate(zip(wedges, labels, sizes, prev_sizes)):
    ang = (wedge.theta2 + wedge.theta1) / 2
    x_label = np.cos(np.radians(ang)) * 1.35
    y_label = np.sin(np.radians(ang)) * 1.35
    x_conn = np.cos(np.radians(ang)) * 1.05
    y_conn = np.sin(np.radians(ang)) * 1.05

    # 连线
    ax.plot([x_conn, x_label], [y_conn, y_label], '-', color=PALETTE[i],
            linewidth=0.8, alpha=0.6)

    # 标签 + 百分比 + 变化率
    change = size - prev
    sign = '+' if change >= 0 else ''
    change_color = COLORS['up'] if change >= 0 else COLORS['down']
    ha = 'left' if x_label > 0 else 'right'
    ax.text(x_label, y_label,
            f'{label}\n{size}% ({sign}{change}%)',
            ha=ha, va='center', fontsize=9, color=PALETTE[i],
            fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                      edgecolor=PALETTE[i], alpha=0.8, linewidth=0.5))

# 中心文字
ax.text(0, 0, '总计\n100%', ha='center', va='center', fontsize=14,
        fontweight='bold', color=COLORS['text'])

ax.set_aspect('equal')
fig.tight_layout()
save_fig(fig, 'figures/fig_donut.pdf')
```

**★ 防遮挡技巧（环形图专用）：**
```python
# 1. 外部标签用连线引出：不要直接放在扇区上（小扇区会溢出）
# 2. 标签 ha 根据角度自适应：左半圆 ha='right'，右半圆 ha='left'
# 3. 扇区数 >8 时：小于 5% 的扇区合并为"其他"
# 4. 变化率标注用颜色区分：正值绿色、负值红色
```

---

## 7. Rain Cloud 图（淡色填充 + 原色边框 + 半小提琴 + 箱线 + 抖动散点 + 均值菱形）

**场景**：分组数据的分布对比，比箱线图更丰富——同时展示密度、统计量和原始数据。
**要点**：淡色填充+原色边框半小提琴、窄箱线图、抖动散点、均值菱形标记、渐变密度填充。

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
import matplotlib.colors as mcolors
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
groups = ['组A', '组B', '组C', '组D']
data = [np.random.normal(loc, s, 80) for loc, s in [(80, 5), (85, 3), (78, 8), (90, 4)]]

# ★ 自适应高度
_fig_h = max(4, len(groups) * 1.2 + 1)
fig, ax = plt.subplots(figsize=(8, _fig_h))

for i, (name, d) in enumerate(zip(groups, data)):
    pos = i

    # 渐变半小提琴（右侧）
    kde = gaussian_kde(d, bw_method=0.3)
    yr = np.linspace(d.min() - 4, d.max() + 4, 300)
    density = kde(yr)
    density_norm = density / density.max() * 0.35

    for layer in range(6):
        frac = layer / 6
        alpha = 0.35 - frac * 0.05
        ax.fill_betweenx(yr, pos + frac * 0.02, pos + density_norm * (1 - frac * 0.12),
                         alpha=alpha, color=PALETTE[i], linewidth=0)
    # 原色边框轮廓
    ax.plot(pos + density_norm, yr, color=PALETTE[i], linewidth=1.2, alpha=0.8)

    # 箱线图（左侧，窄）
    bp = ax.boxplot(d, positions=[pos - 0.18], widths=0.12, vert=True, patch_artist=True,
                    boxprops=dict(facecolor=_lighten(PALETTE[i], 0.4),
                                  edgecolor=PALETTE[i], linewidth=1.2),
                    medianprops=dict(color=COLORS['text'], linewidth=1.8),
                    whiskerprops=dict(linewidth=1, color=PALETTE[i]),
                    capprops=dict(linewidth=1, color=COLORS['ref_line']),
                    flierprops=dict(marker='', markersize=0))

    # 抖动散点（最左侧）
    jitter = np.random.uniform(-0.08, 0.08, len(d))
    ax.scatter(pos - 0.38 + jitter, d, s=6, alpha=0.2, color=PALETTE[i], edgecolor='none')

    # 均值菱形
    ax.scatter(pos - 0.18, d.mean(), marker='D', s=45, color=PALETTE[i],
               edgecolor='white', linewidth=1.2, zorder=5)

    # 均值数值标注
    ax.text(pos - 0.32, d.mean(), f'{d.mean():.1f}', fontsize=7, color=PALETTE[i],
            ha='right', va='center', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                      edgecolor='none', alpha=0.7))

ax.set_xticks(range(len(groups)))
ax.set_xticklabels(groups, fontsize=10)
ax.set_ylabel('数值', fontsize=11)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='y', alpha=0.12, linestyle='--', color=COLORS['grid'])
fig.tight_layout()
save_fig(fig, 'figures/fig_raincloud.pdf')
```

**★ 防遮挡技巧（Rain Cloud 图专用）：**
```python
# 1. 半小提琴只画右半：左侧留给箱线图和散点
# 2. 均值标注放在箱线图左侧：不要和小提琴重叠
# 3. 组数 >6 时：_fig_h 自动增高（每组 1.2 高度）
# 4. 散点用极小尺寸（s=6）和低 alpha（0.2）：不要遮挡箱线图
```

---

## 8. 面积图（渐变填充 + 事件标记线 + 端点标注）

**场景**：时序数据的构成变化趋势，如渠道占比变迁、能源结构演变、市场份额变化。
**要点**：渐变填充层叠、事件标记竖线+标注、端点数值标注、顶部轮廓线。

```python
import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

years = np.arange(2015, 2025)
data = {
    '线上渠道': np.array([15, 20, 28, 35, 42, 48, 55, 60, 65, 68]),
    '线下门店': np.array([60, 55, 48, 42, 38, 35, 30, 28, 25, 22]),
    '其他渠道': np.array([25, 25, 24, 23, 20, 17, 15, 12, 10, 10]),
}

fig, ax = plt.subplots(figsize=(8, 5))

# 渐变填充层叠
cumsum = np.zeros(len(years))
for i, (name, vals) in enumerate(data.items()):
    # 多层渐变填充
    for layer, alpha in enumerate([0.35, 0.20, 0.10]):
        ax.fill_between(years, cumsum + layer * 0.3, cumsum + vals - layer * 0.3,
                        alpha=alpha, color=PALETTE[i], linewidth=0)
    # 原色边框轮廓线
    ax.plot(years, cumsum + vals, color=PALETTE[i], linewidth=1.5, alpha=0.8, label=name)
    cumsum += vals

# 事件标记线
events = {2020: '疫情爆发', 2022: '政策调整'}
for year, event in events.items():
    ax.axvline(x=year, color=COLORS['ref_line'], linestyle=':', linewidth=1, alpha=0.6)
    ax.text(year + 0.1, cumsum.max() * 0.95, event, fontsize=8, color=COLORS['ref_line'],
            rotation=90, va='top', ha='left',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                      edgecolor=COLORS['ref_line'], alpha=0.8, linewidth=0.5))

# 端点数值标注
cumsum_end = np.zeros(1)
for i, (name, vals) in enumerate(data.items()):
    y_pos = cumsum_end + vals[-1] / 2
    ax.text(years[-1] + 0.3, y_pos[0], f'{vals[-1]}%',
            fontsize=8, color=PALETTE[i], fontweight='bold', va='center',
            bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                      edgecolor=PALETTE[i], alpha=0.8, linewidth=0.5))
    cumsum_end += vals[-1]

ax.set_xlabel('年份', fontsize=11)
ax.set_ylabel('占比 (%)', fontsize=11)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='best')
ax.set_xlim(years[0], years[-1] + 0.8)
ax.grid(alpha=0.12, linestyle='--', color=COLORS['grid'])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_area.pdf')
```

**★ 防遮挡技巧（面积图专用）：**
```python
# 1. 事件标记线标签用 rotation=90：竖排文字不会和面积重叠
# 2. 端点标注放在最右侧外：x = years[-1] + 0.3
# 3. 渐变填充 3 层：最内层 alpha=0.35，最外层 alpha=0.10
# 4. xlim 右侧留余量：给端点标注留空间
```

---

## 9. 竖向帕累托图（柱状图 + 累积百分比折线 + 80% 分界线）

**场景**：质量管理、缺陷分析、关键因素排序。展示"关键少数"原则。
**要点**：淡色填充+原色边框柱、累积百分比折线（右轴）、80% 分界线+阴影区域、排名标签。

```python
import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

items = ['缺陷A', '缺陷B', '缺陷C', '缺陷D', '缺陷E', '缺陷F', '缺陷G', '缺陷H']
values = np.array([45, 32, 18, 12, 8, 5, 3, 2])
# 按值排序
sort_idx = np.argsort(-values)
items = [items[i] for i in sort_idx]
values = values[sort_idx]

cumulative_pct = np.cumsum(values) / values.sum() * 100

fig, ax1 = plt.subplots(figsize=(9, 5.5))
ax2 = ax1.twinx()

x = np.arange(len(items))

# ★ 淡色填充 + 原色边框柱
bars = ax1.bar(x, values, width=0.6,
               color=_lighten(PALETTE[0], 0.4), edgecolor=PALETTE[0],
               linewidth=1.2, zorder=2)

# 80% 分界线之前的柱子高亮
threshold_idx = np.searchsorted(cumulative_pct, 80)
for i in range(threshold_idx + 1):
    bars[i].set_facecolor(_lighten(PALETTE[0], 0.25))
    bars[i].set_linewidth(1.8)

# 顶部数值标注
for bar, v in zip(bars, values):
    ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
             f'{v}', ha='center', va='bottom', fontsize=8, fontweight='bold',
             color=COLORS['text'])

# 累积百分比折线
ax2.plot(x, cumulative_pct, 'o-', color=PALETTE[1], linewidth=2, markersize=6,
         markeredgecolor='white', markeredgewidth=1.2, zorder=3)

# 80% 分界线
ax2.axhline(y=80, color=COLORS['down'], linestyle='--', linewidth=1, alpha=0.6)
ax2.text(len(items) - 0.5, 81, '80%', fontsize=9, color=COLORS['down'],
         fontweight='bold', ha='right',
         bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                   edgecolor=COLORS['down'], alpha=0.8))

# 80% 区域阴影
ax1.axvspan(-0.5, threshold_idx + 0.5, alpha=0.05, color=PALETTE[0], zorder=0)
ax1.text(threshold_idx / 2, max(values) * 0.9, '关键少数 (80%)',
         ha='center', fontsize=9, color=PALETTE[0], style='italic',
         bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                   edgecolor=PALETTE[0], alpha=0.8))

ax1.set_xticks(x)
ax1.set_xticklabels(items, fontsize=9, rotation=15, ha='right')
ax1.set_ylabel('频次', fontsize=11, color=PALETTE[0])
ax2.set_ylabel('累积百分比 (%)', fontsize=11, color=PALETTE[1])
ax1.tick_params(axis='y', labelcolor=PALETTE[0])
ax2.tick_params(axis='y', labelcolor=PALETTE[1])
ax2.set_ylim(0, 105)
ax1.spines['top'].set_visible(False)
ax1.grid(axis='y', alpha=0.12, linestyle='--', color=COLORS['grid'])
fig.tight_layout()
save_fig(fig, 'figures/fig_pareto.pdf')
```

**★ 防遮挡技巧（帕累托图专用）：**
```python
# 1. 柱子顶部数值和累积折线不要重叠：折线在右轴，数值在左轴空间
# 2. 80% 标注放在图右边缘：不要放在柱子密集区
# 3. "关键少数"标注放在阴影区域中间上方
# 4. x 轴标签长时：rotation=15, ha='right'
```

---

## 10. 双轴图（淡色填充 + 原色边框柱 + 渐变填充折线 + 相关性标注框 + 峰值高亮）

**场景**：两种不同量纲的数据在同一图中展示，如数量（柱）+ 增长率（线）、产量 + 价格。
**要点**：淡色填充+原色边框柱、渐变填充折线、合并图例、相关性标注框、峰值高亮。

```python
import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

years = np.arange(2016, 2025)
bar_data = np.array([120, 145, 168, 195, 230, 260, 310, 355, 400])
line_data = np.array([15.2, 18.5, 22.1, 25.8, 30.2, 35.5, 38.1, 42.3, 45.0])

fig, ax1 = plt.subplots(figsize=(8, 5.5))
ax2 = ax1.twinx()

# ★ 淡色填充 + 原色边框柱
bars = ax1.bar(years, bar_data, width=0.6,
               color=_lighten(PALETTE[0], 0.4), edgecolor=PALETTE[0],
               linewidth=1.2, label='数量', zorder=2)

# 柱子阴影
ax1.bar(years + 0.03, bar_data, width=0.6, color='#cccccc', alpha=0.08, zorder=1)

# 渐变填充折线
line = ax2.plot(years, line_data, 'o-', color=PALETTE[1], linewidth=2.2, markersize=7,
                markeredgecolor='white', markeredgewidth=1.2, label='增长率', zorder=5)
for layer, alpha in enumerate([0.15, 0.08, 0.03]):
    ax2.fill_between(years, min(line_data) - 2 + layer * 0.5,
                     np.array(line_data) - layer * 0.5,
                     alpha=alpha, color=PALETTE[1], linewidth=0)

# 峰值高亮
peak_idx = np.argmax(line_data)
ax2.scatter(years[peak_idx], line_data[peak_idx], s=150, color=PALETTE[1],
            edgecolor='white', linewidth=2.5, zorder=6)
ax2.annotate(f'峰值 {line_data[peak_idx]:.1f}%',
             xy=(years[peak_idx], line_data[peak_idx]),
             xytext=(years[peak_idx] - 2, line_data[peak_idx] + 3),
             fontsize=9, fontweight='bold', color=PALETTE[1],
             arrowprops=dict(arrowstyle='->', color=PALETTE[1], lw=1.2),
             bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                       edgecolor=PALETTE[1], alpha=0.9))

# 相关性标注框
corr = np.corrcoef(bar_data, line_data)[0, 1]
ax1.text(0.02, 0.95, f'r = {corr:.3f}',
         transform=ax1.transAxes, fontsize=9, va='top',
         bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                   edgecolor=COLORS['grid'], alpha=0.9, linewidth=0.8))

ax1.set_xlabel('年份', fontsize=11)
ax1.set_ylabel('数量 (个)', fontsize=11, color=PALETTE[0])
ax2.set_ylabel('增长率 (%)', fontsize=11, color=PALETTE[1])
ax1.tick_params(axis='y', labelcolor=PALETTE[0])
ax2.tick_params(axis='y', labelcolor=PALETTE[1])

# 合并图例
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='upper left')

ax1.spines['top'].set_visible(False)
ax1.grid(axis='y', alpha=0.12, linestyle='--', color=COLORS['grid'])
fig.tight_layout()
save_fig(fig, 'figures/fig_dual_axis.pdf')
```

**★ 防遮挡技巧（双轴图专用）：**
```python
# 1. 柱子用半透明（alpha=0.7）：不要遮挡折线
# 2. 折线 zorder=5：确保在柱子上方
# 3. 峰值标注箭头方向：根据数据走势选择，避免和柱子重叠
# 4. 双轴标签颜色和对应数据系列一致
```

---

## 11. Rain Cloud 小提琴图（淡色填充 + 原色边框 + 显著性括号 + 完整分布展示）

**场景**：比箱线图更丰富的分布形态展示，适合样本量较大时展示分布的偏态、多峰等特征。
**要点**：淡色填充+原色边框小提琴、叠加窄箱线图、均值菱形、显著性括号+p值。

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import ttest_ind
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
groups = ['A组', 'B组', 'C组', 'D组']
data = [np.random.normal(m, s, 100) for m, s in [(80, 5), (85, 3), (78, 8), (90, 4)]]

fig, ax = plt.subplots(figsize=(8, 5.5))

# ★ 淡色填充 + 原色边框小提琴
parts = ax.violinplot(data, positions=range(len(groups)), showmeans=False,
                      showmedians=False, showextrema=False)

for i, pc in enumerate(parts['bodies']):
    pc.set_facecolor(_lighten(PALETTE[i], 0.4))
    pc.set_edgecolor(PALETTE[i])
    pc.set_linewidth(1.2)
    pc.set_alpha(0.7)

# 叠加窄箱线图
bp = ax.boxplot(data, positions=range(len(groups)), widths=0.15, patch_artist=True,
                boxprops=dict(facecolor='white', edgecolor=COLORS['text'], linewidth=1.2),
                medianprops=dict(color=COLORS['text'], linewidth=2),
                whiskerprops=dict(linewidth=1.2),
                capprops=dict(linewidth=1.2),
                flierprops=dict(marker='.', markersize=3, alpha=0.3))

# 均值菱形 + 数值标注
for i, d in enumerate(data):
    ax.scatter(i, d.mean(), marker='D', s=40, color=PALETTE[i],
               edgecolor='white', linewidth=1, zorder=5)
    ax.text(i + 0.25, d.mean(), f'{d.mean():.1f}', fontsize=7.5, color=PALETTE[i],
            va='center', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.1', facecolor='white',
                      edgecolor='none', alpha=0.7))

# 显著性括号
def add_significance(ax, x1, x2, y, p_val, h=2):
    ax.plot([x1, x1, x2, x2], [y, y + h, y + h, y], color=COLORS['text'], linewidth=0.8)
    stars = '***' if p_val < 0.001 else '**' if p_val < 0.01 else '*' if p_val < 0.05 else 'n.s.'
    ax.text((x1 + x2) / 2, y + h + 0.3, f'{stars}\np={p_val:.2e}',
            ha='center', va='bottom', fontsize=7, color=COLORS['text'],
            bbox=dict(boxstyle='round,pad=0.15', facecolor=COLORS['bg_box'],
                      edgecolor=COLORS['grid'], alpha=0.9, linewidth=0.3))

y_max = max(d.max() for d in data) + 3
# 比较最优组（D组）与其他组
for idx, comp in enumerate([0, 1, 2]):
    _, p = ttest_ind(data[3], data[comp])
    add_significance(ax, comp, 3, y_max + idx * 6, p)

ax.set_xticks(range(len(groups)))
ax.set_xticklabels(groups, fontsize=10)
ax.set_ylabel('数值', fontsize=11)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='y', alpha=0.12, linestyle='--', color=COLORS['grid'])
fig.tight_layout()
save_fig(fig, 'figures/fig_violin.pdf')
```

**★ 防遮挡技巧（小提琴图专用）：**
```python
# 1. 显著性括号从最内层开始画：最近的两组先画，跨组的画在外层
# 2. 括号 y 位置逐层递增：每层 +6 个单位
# 3. 均值标注放在小提琴右侧：不要放在内部（会被箱线图遮挡）
# 4. 组数 >6 时：只标注 p < 0.01 的显著性对比
```

---

## 12. 多面板子图（淡色填充 + 原色边框 + 带背景框标签 + 统一风格）

**场景**：多个相关图表组合成一张大图，如同一实验的不同视角、多数据集结果并排展示。
**要点**：(a)(b)(c)(d) 带背景框子图标签、淡色填充+原色边框统一风格、tight_layout 自动对齐。

```python
import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
fig, axes = plt.subplots(2, 2, figsize=(5.0, 4.9))   # 示例尺寸；保留模板比例，按实际显示尺寸检查字号与布局

# (a) 折线图 — 渐变填充
ax = axes[0, 0]
for i in range(3):
    y = np.cumsum(np.random.randn(10))
    ax.plot(range(10), y, 'o-', color=PALETTE[i], linewidth=1.8, markersize=5,
            markeredgecolor='white', markeredgewidth=0.8, label=f'系列{i + 1}')
    ax.fill_between(range(10), y - 1, y + 1, alpha=0.08, color=PALETTE[i])
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8)
ax.set_ylabel('累计值', fontsize=10)
ax.grid(alpha=0.12, linestyle='--', color=COLORS['grid'])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# (b) 分组柱状图 — 淡色填充 + 原色边框
ax = axes[0, 1]
x = np.arange(5)
for i, label in enumerate(['方法A', '方法B']):
    vals = np.random.uniform(60, 95, 5)
    offset = (i - 0.5) * 0.3
    ax.bar(x + offset, vals, 0.28, color=_lighten(PALETTE[i], 0.4),
           edgecolor=PALETTE[i], linewidth=1.2, label=label)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8)
ax.set_ylabel('得分', fontsize=10)
ax.grid(axis='y', alpha=0.12, linestyle='--', color=COLORS['grid'])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# (c) 散点图 — KDE 等高线背景
ax = axes[1, 0]
for i in range(3):
    pts = np.random.randn(30, 2)
    ax.scatter(pts[:, 0], pts[:, 1], s=25, alpha=0.6, color=PALETTE[i],
               edgecolor='white', linewidth=0.5, label=f'类{i + 1}')
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8)
ax.grid(alpha=0.12, linestyle='--', color=COLORS['grid'])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# (d) 直方图 — 淡色填充 + 原色边框
ax = axes[1, 1]
for i in range(3):
    vals = np.random.normal(i * 2, 1, 200)
    ax.hist(vals, bins=20, alpha=0.5, color=_lighten(PALETTE[i], 0.4),
            edgecolor=PALETTE[i], linewidth=0.8, label=f'分布{i + 1}')
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8)
ax.set_ylabel('频次', fontsize=10)
ax.grid(axis='y', alpha=0.12, linestyle='--', color=COLORS['grid'])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# ★ 带背景框子图标签（用 set_title 紧贴子图顶部）
for i, ax in enumerate(axes.flat):
    ax.set_title(f'({chr(97 + i)})', fontsize=12, fontweight='bold', loc='left', pad=3)

fig.tight_layout(pad=0.5)
save_fig(fig, 'figures/fig_subplots.pdf')
```

**★ 防遮挡技巧（多面板子图专用）：**
```python
# 1. 子图标签 (a)(b)(c)(d) 用 ax.set_title(loc='left', pad=3) 紧贴子图顶部
#    ⛔ 不要用 ax.text(transAxes) — set_aspect('equal') 时标注会远离子图
# 2. tight_layout(pad=0.5)：紧凑布局，子图不会被压缩
#    ⛔ 不要用 pad=2.0 — 紧凑布局下会导致子图极小
# 3. 每个子图的图例放在各自内部：不要用全局图例
# 4. 统一 fontsize：标题 10pt，标签 8pt，刻度 8pt
# 5. 统一配色：所有子图使用相同的 PALETTE 序列
```