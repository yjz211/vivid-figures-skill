# 实证/计量经济学 图表代码范例（SCI 出版质量）

For: statistics modeling contests, econometrics theses, empirical papers.
Palette: soft (default), nejm (elegant for medical/stats). All recipes use `setup_style()`.
Style: Layered visuals — gradient fills, KDE backgrounds, annotation boxes, marginal distributions.

---

## 1. Forest Plot (Stata/SCI style)

**Scene**: Regression coefficients with CI. Alternating row shading, diamond pooled estimate, I² heterogeneity annotation, weight column, right-side numeric columns.
**要点**：交替行阴影、权重比例圆点（显著=实心/不显著=空心）、菱形 pooled estimate、I² 标注框、右侧数值列（系数 [95% CI]）、显著性★标记。

```python
import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

labels = ['低固定资产组', '高固定资产组', '低负债组', '高负债组',
          '低资产负债率组', '高资产负债率组', '低流动性组', '高流动性组']
coefs  = np.array([-0.028,-0.042,-0.030,-0.031,-0.035,-0.025,-0.032,-0.033])
ci_lo  = np.array([-0.048,-0.058,-0.055,-0.052,-0.052,-0.010,-0.048,-0.046])
ci_hi  = np.array([-0.008,-0.026,-0.005,-0.010,-0.018,-0.040,-0.016,-0.020])
weights = np.array([12.8, 14.2, 10.5, 11.3, 13.1, 9.7, 14.6, 13.8])
significant = [True, True, False, False, True, True, False, False]

pooled_coef = np.average(coefs, weights=weights)
pooled_se   = 0.004
pooled_lo   = pooled_coef - 1.96 * pooled_se
pooled_hi   = pooled_coef + 1.96 * pooled_se

# ★ 自适应高度：变量多时不会过度拉伸
_fig_h = max(5, len(labels) * 0.7 + 2)
fig, ax = plt.subplots(figsize=(11, _fig_h))
y = np.arange(len(labels)) * 1.4

# 交替行阴影
for i in range(len(labels)):
    if i % 2 == 0:
        ax.axhspan(y[i] - 0.55, y[i] + 0.55, color=COLORS['bg_box'], zorder=0)

# 零线参考
ax.axvline(x=0, color=COLORS['down'], linestyle='--', linewidth=1.5, alpha=0.7, zorder=1)

for i, (c, lo, hi, lbl, sig, wt) in enumerate(zip(coefs, ci_lo, ci_hi, labels, significant, weights)):
    # CI 线 + 端点帽
    ax.plot([lo, hi], [y[i], y[i]], color=COLORS['text'], linewidth=1.2, zorder=2, solid_capstyle='round')
    ax.plot([lo, lo], [y[i]-0.12, y[i]+0.12], color=COLORS['text'], linewidth=1.0)
    ax.plot([hi, hi], [y[i]-0.12, y[i]+0.12], color=COLORS['text'], linewidth=1.0)

    # 权重比例圆点（显著=实心，不显著=空心）
    fc = PALETTE[0] if sig else 'white'
    ec = PALETTE[0] if sig else COLORS['ref_line']
    ms = 5 + wt / 4
    ax.plot(c, y[i], 'o', color=fc, markersize=ms, markeredgecolor=ec,
            markeredgewidth=1.3, zorder=3)

    # 左侧标签
    ax.text(-0.065, y[i], lbl, ha='right', va='center', fontsize=9, color=COLORS['text'])

    # 右侧数值列：系数 [95% CI] + 显著性★
    sig_mark = '***' if sig else ''
    ax.text(0.085, y[i], f'{c:.3f} [{lo:.3f}, {hi:.3f}]{sig_mark}',
            ha='left', va='center', fontsize=8, fontfamily='monospace',
            color=PALETTE[0] if sig else COLORS['ref_line'],
            fontweight='bold' if sig else 'normal')

    # 权重列
    ax.text(0.16, y[i], f'{wt:.1f}%', ha='right', va='center',
            fontsize=8, color=COLORS['text'])

# 列标题
ax.text(-0.065, max(y) + 1.0, '分组', ha='right', va='center',
        fontsize=9.5, fontweight='bold', color=COLORS['text'])
ax.text(0.085, max(y) + 1.0, '系数 [95% CI]', ha='left', va='center',
        fontsize=9.5, fontweight='bold', color=COLORS['text'])
ax.text(0.16, max(y) + 1.0, '权重', ha='right', va='center',
        fontsize=9.5, fontweight='bold', color=COLORS['text'])

# 菱形 pooled estimate
diamond_y = -1.5
dh = 0.35
diamond_x = [pooled_lo, pooled_coef, pooled_hi, pooled_coef]
diamond_yy = [diamond_y, diamond_y + dh, diamond_y, diamond_y - dh]
ax.fill(diamond_x, diamond_yy, color=PALETTE[1], alpha=0.85, zorder=4)
ax.plot(diamond_x + [diamond_x[0]], diamond_yy + [diamond_yy[0]],
        color=COLORS['text'], linewidth=0.8, zorder=5)
ax.text(-0.065, diamond_y, 'Pooled', ha='right', va='center',
        fontsize=9.5, fontweight='bold', color=PALETTE[1])
ax.text(0.085, diamond_y, f'{pooled_coef:.3f} [{pooled_lo:.3f}, {pooled_hi:.3f}]***',
        ha='left', va='center', fontsize=8, fontfamily='monospace',
        fontweight='bold', color=PALETTE[1])

# I² 异质性标注框
i2_text = 'I² = 42.3%, Q = 13.8 (p = 0.055)'
ax.text(0.0, diamond_y - 1.0, i2_text, ha='center', va='top', fontsize=8.5,
        bbox=dict(boxstyle='round,pad=0.4', facecolor=_lighten(COLORS['highlight'], 0.85),
                  edgecolor=_lighten(COLORS['highlight'], 0.4), alpha=0.95),
        color=COLORS['text'])

ax.set_yticks([])
ax.set_xlabel('回归系数', fontsize=12)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.set_ylim(diamond_y - 1.8, max(y) + 1.5)
ax.set_xlim(-0.07, 0.17)
ax.invert_yaxis()
ax.grid(axis='x', alpha=0.15, linestyle='--')
fig.tight_layout()
save_fig(fig, 'figures/fig_forest.pdf')
```

**★ 防遮挡技巧（森林图专用）：**
```python
# 1. 保留模板已有标签列；密集时可按需用 smart_labels() 或位置调整
# 2. 按标签列和最终显示尺寸留出空间，不固定值域余量
# 3. 零线标注放在图顶部或底部：不要放在数据密集的中间
# 4. 置信区间线很短时（CI 窄）：标签偏移量按值域比例计算，不要用固定像素
# 5. 长变量名按实际尺寸调整画布、字号或缩写，并保留可查全称
# 6. 自适应高度：_fig_h = max(4, n_vars*0.5+1.5)
# 7. 分组分隔线（如果有变量分组）：用 axhline + 淡灰色，不要用粗黑线
```

---

## 2. Parallel Trends (DID)

**Scene**: Treatment vs control pre/post trends. Gradient CI bands, treatment effect annotation arrow, pre/post period labels with background boxes.

```python
import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

periods = np.arange(-5, 6)
treat = np.array([.02, -.01, .03, -.02, .01, .15, .28, .35, .42, .50, .55])
ctrl  = np.array([.01, .00, .02, -.01, .00, .02, .03, .01, .02, .00, .01])
se_t  = np.full(11, .04)
se_c  = np.full(11, .03)

fig, ax = plt.subplots(figsize=(9, 5.5))

for x_start, x_end, c_base, lbl in [(-5.5, -0.5, _lighten(COLORS['up'], 0.8), 'Pre-Treatment'),
                                      (-0.5, 5.5, _lighten(COLORS['highlight'], 0.8), 'Post-Treatment')]:
    ax.axvspan(x_start, x_end, color=c_base, alpha=0.25, zorder=0)
    cx = (x_start + x_end) / 2
    ax.text(cx, -0.15, lbl, ha='center', va='bottom', fontsize=9, color=COLORS['ref_line'],
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                      edgecolor=COLORS['grid'], alpha=0.9))

ax.axvline(x=-0.5, color=COLORS['down'], linestyle='--', linewidth=1.3, alpha=0.7)
ax.text(-0.5, 0.62, 'Treatment', ha='center', va='bottom', fontsize=9,
        color=COLORS['down'], fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.25', facecolor=COLORS['bg_box'],
                  edgecolor=COLORS['down'], alpha=0.9))

n_layers = 8
for k in range(n_layers, 0, -1):
    frac = k / n_layers
    ax.fill_between(periods, treat - frac*1.96*se_t, treat + frac*1.96*se_t,
                    alpha=0.04, color=PALETTE[0], linewidth=0)
    ax.fill_between(periods, ctrl - frac*1.96*se_c, ctrl + frac*1.96*se_c,
                    alpha=0.04, color=PALETTE[1], linewidth=0)

ax.plot(periods, treat, 'o-', color=PALETTE[0], markersize=7, linewidth=2.2,
        label='Treatment', markeredgecolor='white', markeredgewidth=1, zorder=5)
ax.plot(periods, ctrl, 's--', color=PALETTE[1], markersize=6, linewidth=1.8,
        label='Control', markeredgecolor='white', markeredgewidth=1, zorder=5)

ax.annotate(f'ATT = {treat[-1]-ctrl[-1]:.2f}',
            xy=(periods[-1], treat[-1]),
            xytext=(periods[-1] - 1.5, treat[-1] + 0.12),
            fontsize=9, fontweight='bold', color=PALETTE[0],
            arrowprops=dict(arrowstyle='->', color=PALETTE[0], lw=1.5,
                            connectionstyle='arc3,rad=-0.2'),
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                      edgecolor=PALETTE[0], alpha=0.9))

ax.set_xlabel('Period', fontsize=11); ax.set_ylabel('Outcome', fontsize=11)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='upper left')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(alpha=0.15, linestyle='--')
fig.tight_layout()
save_fig(fig, 'figures/fig_parallel.pdf')
```


---

## 3. Event Study

**Scene**: Dynamic treatment effects. Gradient-colored CI bars (pre=gray, post=colored), cumulative effect line overlay, significance stars.

```python
import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

periods = np.arange(-4, 5)
coefs   = np.array([.01, -.02, .01, .00, .12, .25, .31, .38, .42])
se      = np.array([.04, .03, .04, .03, .05, .05, .06, .06, .07])

fig, ax = plt.subplots(figsize=(8, 5))
ax.axhline(y=0, color=COLORS['ref_line'], linewidth=0.6, alpha=0.5)
ax.axvline(x=-0.5, color=COLORS['down'], linestyle='--', linewidth=1.0, alpha=0.6)
ax.axvspan(-4.5, -0.5, color=COLORS['bg_box'], alpha=0.3, zorder=0)
ax.axvspan(-0.5, 4.5, color=_lighten(COLORS['highlight'], 0.85), alpha=0.3, zorder=0)

for t_val, c, s in zip(periods, coefs, se):
    lo, hi = c - 1.96 * s, c + 1.96 * s
    base_color = COLORS['ref_line'] if t_val < 0 else PALETTE[0]
    n_layers = 6
    for k in range(n_layers, 0, -1):
        frac = k / n_layers
        ax.plot([t_val, t_val], [c - frac*1.96*s, c + frac*1.96*s],
                color=base_color, linewidth=3.5 - k*0.3, alpha=0.08 + 0.04*(n_layers-k) + 0.3,
                solid_capstyle='round')
    ax.plot([t_val, t_val], [lo, hi], color=base_color, linewidth=2.5,
            solid_capstyle='round', alpha=0.8)
    ax.plot(t_val, c, 'o', color=base_color, markersize=8,
            markeredgecolor='white', markeredgewidth=1.2, zorder=5)
    if abs(c) > 1.96 * s:
        star = '***' if abs(c) > 2.576 * s else '**'
        ax.text(t_val, hi + 0.02, star, ha='center', va='bottom',
                fontsize=8, color=base_color, fontweight='bold')

post_mask = periods >= 0
cum_effect = np.cumsum(coefs[post_mask])
ax2 = ax.twinx()
ax2.plot(periods[post_mask], cum_effect, '--', color=PALETTE[1], linewidth=1.5,
         alpha=0.7, label='Cumulative Effect')
ax2.set_ylabel('Cumulative Effect', fontsize=10, color=PALETTE[1])
ax2.tick_params(axis='y', labelcolor=PALETTE[1])
ax2.legend(loc='upper left', frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8)

ax.set_xlabel('Period Relative to Treatment', fontsize=11)
ax.set_ylabel('Coefficient', fontsize=11); ax.set_xticks(periods)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(alpha=0.15, linestyle='--')
fig.tight_layout()
save_fig(fig, 'figures/fig_event.pdf')
```

**★ 防遮挡技巧（Event Study 专用）：**
```python
# 1. 显著性星号放在 CI bar 上方：不要放在 bar 内部
# 2. 累积效应折线用 twin axis 上：和主轴 CI bars 不会直接重叠
# 3. 事件时点标注（t=0 竖线）的标签放在图顶部：不要放在数据区域
# 4. x 轴标签多时：只标注关键时点（-5, 0, 5, 10）
```

---

## 4. Placebo Test

**Scene**: Permutation-based placebo distribution. Gradient fill under KDE, p-value annotation box, percentile markers (5th, 95th).

```python
import numpy as np, matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
fake = np.random.normal(0, 0.08, 500); real = -0.291

fig, ax = plt.subplots(figsize=(8, 5))
kde = gaussian_kde(fake)
xk = np.linspace(fake.min() - 0.08, fake.max() + 0.08, 300)
yk = kde(xk)

n_layers = 20
for k in range(n_layers):
    ax.fill_between(xk, 0, yk * (1 - k*0.02), alpha=0.03, color=PALETTE[0], linewidth=0)
ax.fill_between(xk, 0, yk, alpha=0.15, color=PALETTE[0], linewidth=0)
ax.plot(xk, yk, color=PALETTE[0], linewidth=2.5, zorder=4)
ax.hist(fake, bins=45, density=True, color=_lighten(PALETTE[0], 0.4), alpha=0.5, edgecolor=PALETTE[0], linewidth=0.8, zorder=2)

for pval_pct, plabel in [(np.percentile(fake, 5), '5th'), (np.percentile(fake, 95), '95th')]:
    ax.axvline(x=pval_pct, color=COLORS['ref_line'], linestyle=':', linewidth=1.0, alpha=0.7)
    ax.text(pval_pct, max(yk)*0.92, plabel, ha='center', va='bottom', fontsize=8, color=COLORS['text'],
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=COLORS['grid'], alpha=0.8))

ax.axvline(x=real, color=PALETTE[1], linewidth=2.5, zorder=5)
ax.annotate(f'Real = {real:.3f}', xy=(real, max(yk)*0.15),
            xytext=(real - 0.12, max(yk)*0.65), fontsize=10, fontweight='bold', color=PALETTE[1],
            arrowprops=dict(arrowstyle='->', color=PALETTE[1], lw=1.5, connectionstyle='arc3,rad=0.2'),
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor=PALETTE[1], alpha=0.95))

p_value = np.mean(np.abs(fake) >= np.abs(real))
ax.text(0.97, 0.95, f'Permutations: 500\np-value = {p_value:.3f}', transform=ax.transAxes,
        fontsize=8.5, va='top', ha='right',
        bbox=dict(boxstyle='round,pad=0.5', facecolor=COLORS['bg_box'], edgecolor=COLORS['grid'], alpha=0.95), color=COLORS['text'])

ax.set_xlabel('Placebo Coefficients', fontsize=11); ax.set_ylabel('Density', fontsize=11)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(alpha=0.15, linestyle='--')
fig.tight_layout()
save_fig(fig, 'figures/fig_placebo.pdf')
```

---

## 5. Correlation Heatmap

**Scene**: Lower-triangle heatmap with hierarchical clustering dendrogram, significance stars in cells, variable grouping color bars.

```python
import numpy as np, matplotlib.pyplot as plt, seaborn as sns; from _utils.palette_maps import palette_cmap, palette_stops, contrast_text
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.stats import pearsonr
from _utils.plot_utils import setup_style, save_fig, COLORS, _lighten
setup_style()

np.random.seed(42)
labels = ['GDP', 'Digital', 'HumanCap', 'Urban', 'FDI', 'R&D']
n_vars = len(labels)
raw = np.random.randn(n_vars, 100)
raw[1] += 0.6*raw[0]; raw[2] += 0.4*raw[0]; raw[4] += 0.5*raw[3]; raw[5] += 0.7*raw[1]
corr = np.corrcoef(raw)

pvals = np.zeros((n_vars, n_vars))
for i in range(n_vars):
    for j in range(n_vars):
        if i != j: _, pvals[i, j] = pearsonr(raw[i], raw[j])

Z = linkage(1 - np.abs(corr), method='ward')
fig = plt.figure(figsize=(10, 9))
gs = fig.add_gridspec(2, 1, height_ratios=[1, 7], hspace=0.02)

# 顶部树状图（只保留顶部，不用左侧，避免挡标签）
ax_dendro = fig.add_subplot(gs[0])
dendrogram(Z, labels=labels, ax=ax_dendro, leaf_rotation=0, color_threshold=0, above_threshold_color=COLORS['ref_line'])
ax_dendro.set_xticks([]); ax_dendro.spines[:].set_visible(False)
ax_dendro.tick_params(left=False, labelleft=False, bottom=False)

ax_heat = fig.add_subplot(gs[1])
mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
sns.heatmap(corr, mask=mask, annot=False, cmap=palette_cmap('diverging'), center=0, square=True,
            linewidths=1.0, linecolor='white', xticklabels=labels, yticklabels=labels,
            cbar_kws={'shrink': 0.7, 'label': 'Correlation'}, ax=ax_heat, vmin=-1, vmax=1)

for i in range(n_vars):
    for j in range(n_vars):
        if j <= i:
            val = corr[i, j]
            p = pvals[i, j] if i != j else 0
            stars = '***' if p < 0.001 else ('**' if p < 0.01 else ('*' if p < 0.05 else ''))
            txt_color = contrast_text(ax_heat.collections[0].cmap(ax_heat.collections[0].norm(val)))
            ax_heat.text(j + 0.5, i + 0.5, f'{val:.2f}{stars}', ha='center', va='center',
                         fontsize=8.5, color=txt_color, fontweight='bold' if i == j else 'normal')

fig.tight_layout()
save_fig(fig, 'figures/fig_corr.pdf')
```

---

## 6. Distribution (Rain Cloud with Gradient KDE)

**Scene**: Full rain cloud — gradient KDE fill, jittered strip, boxplot, percentile markers, Shapiro-Wilk annotation.

```python
import numpy as np, matplotlib.pyplot as plt
from scipy.stats import gaussian_kde, shapiro
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
groups = ['Group A', 'Group B', 'Group C']
data_all = [np.random.lognormal(2, 0.8, 300), np.random.lognormal(2.2, 0.6, 300),
            np.random.lognormal(1.8, 1.0, 300)]

# ★ 自适应高度
_fig_h = max(4, len(groups) * 1.5 + 1)
fig, ax = plt.subplots(figsize=(10, _fig_h))
for i, (grp, data) in enumerate(zip(groups, data_all)):
    y_center = i * 2.5
    kde = gaussian_kde(data)
    x_kde = np.linspace(data.min()*0.8, np.percentile(data, 99), 200)
    y_kde = kde(x_kde)
    y_kde_norm = y_kde / y_kde.max() * 0.8

    n_layers = 15
    for k in range(n_layers, 0, -1):
        frac = k / n_layers
        ax.fill_between(x_kde, y_center, y_center + y_kde_norm*frac,
                        alpha=0.035, color=PALETTE[i], linewidth=0)
    ax.fill_between(x_kde, y_center, y_center + y_kde_norm, alpha=0.2, color=PALETTE[i], linewidth=0)
    ax.plot(x_kde, y_center + y_kde_norm, color=PALETTE[i], linewidth=1.5)

    ax.boxplot([data], positions=[y_center], vert=False, widths=0.3, patch_artist=True,
               boxprops=dict(facecolor=_lighten(PALETTE[i], 0.4), edgecolor=PALETTE[i], linewidth=1.2),
               medianprops=dict(color=COLORS['text'], linewidth=1.5),
               whiskerprops=dict(color=PALETTE[i], linewidth=1),
               capprops=dict(color=PALETTE[i], linewidth=1),
               flierprops=dict(marker='.', markersize=2, alpha=0.3, markerfacecolor=PALETTE[i]))

    jitter = np.random.uniform(-0.15, -0.55, len(data))
    ax.scatter(data[::3], y_center + jitter[:len(data[::3])], s=4, alpha=0.25, color=PALETTE[i], zorder=2)

    for pct, pct_label in [(25, 'Q1'), (50, 'Median'), (75, 'Q3')]:
        pv = np.percentile(data, pct)
        ax.plot(pv, y_center - 0.7, '|', color=PALETTE[i], markersize=8, markeredgewidth=1.5, zorder=4)
        ax.text(pv, y_center - 0.9, f'{pct_label}\n{pv:.1f}', ha='center', va='top', fontsize=7, color=COLORS['text'])

    stat, p = shapiro(data[:50])
    ax.text(np.percentile(data, 99)*1.02, y_center + 0.3, f'W={stat:.3f}, p={p:.3f}',
            fontsize=7.5, color=COLORS['text'], va='center',
            bbox=dict(boxstyle='round,pad=0.25', facecolor=COLORS['bg_box'], edgecolor=COLORS['grid'], alpha=0.9))

ax.set_yticks([i*2.5 for i in range(len(groups))]); ax.set_yticklabels(groups, fontsize=10)
ax.set_xlabel('Value', fontsize=11); ax.grid(axis='x', alpha=0.15, linestyle='--')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_dist.pdf')
```

**★ 防遮挡技巧（Distribution Rain Cloud 专用）：**
```python
# 1. 百分位标记放在 boxplot 下方：不要和 KDE 曲线重叠
# 2. Shapiro-Wilk 标注框放在 KDE 曲线右端外侧：用 bbox 白底
# 3. 组间 y 间距 ≥ 2.5：太密会导致 KDE + box + strip 互相遮挡
# 4. 自适应高度：_fig_h = max(4, n_groups * 1.5 + 1)
```

---

## 7. Time Series Trend (Dual Y-axis)

**Scene**: Dual-axis time series with gradient fills, event markers for policy changes, correlation annotation box.

```python
import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
years = np.arange(2010, 2024)
gdp = np.cumsum(np.random.normal(0.5, 0.3, 14)) + 10
digital = np.cumsum(np.random.normal(0.8, 0.2, 14)) + 2

fig, ax1 = plt.subplots(figsize=(9, 5)); ax2 = ax1.twinx()

n_layers = 12
for k in range(n_layers, 0, -1):
    frac = k / n_layers
    ax1.fill_between(years, gdp.min()-0.5, gdp-(gdp-gdp.min()+0.5)*(1-frac),
                     alpha=0.02, color=PALETTE[0], linewidth=0)
ax1.fill_between(years, gdp.min()-0.5, gdp, alpha=0.08, color=PALETTE[0], linewidth=0)

for k in range(n_layers, 0, -1):
    frac = k / n_layers
    ax2.fill_between(years, digital.min()-0.5, digital-(digital-digital.min()+0.5)*(1-frac),
                     alpha=0.02, color=PALETTE[1], linewidth=0)
ax2.fill_between(years, digital.min()-0.5, digital, alpha=0.08, color=PALETTE[1], linewidth=0)

ax1.plot(years, gdp, 'o-', color=PALETTE[0], linewidth=2.2, markersize=6,
         label='GDP', markeredgecolor='white', markeredgewidth=1, zorder=5)
ax2.plot(years, digital, 's-', color=PALETTE[1], linewidth=2.2, markersize=6,
         label='Digital Index', markeredgecolor='white', markeredgewidth=1, zorder=5)

for yr, evt in {2015: 'Policy A', 2020: 'Policy B'}.items():
    ax1.axvline(x=yr, color=COLORS['down'], linestyle=':', linewidth=1.0, alpha=0.6)
    ax1.text(yr, gdp.max()+0.3, evt, ha='center', va='bottom', fontsize=8, color=COLORS['down'],
             bbox=dict(boxstyle='round,pad=0.2', facecolor=COLORS['bg_box'], edgecolor=COLORS['down'], alpha=0.85))

corr_val = np.corrcoef(gdp, digital)[0, 1]
ax1.text(0.03, 0.97, f'Pearson r = {corr_val:.3f}', transform=ax1.transAxes, fontsize=9,
         va='top', ha='left', bbox=dict(boxstyle='round,pad=0.5', facecolor=_lighten(PALETTE[0], 0.7),
                                         edgecolor=COLORS['grid'], alpha=0.95), color=COLORS['text'])

ax1.set_xlabel('Year', fontsize=11)
ax1.set_ylabel('GDP', fontsize=11, color=PALETTE[0])
ax2.set_ylabel('Digital Index', fontsize=11, color=PALETTE[1])
l1, lb1 = ax1.get_legend_handles_labels(); l2, lb2 = ax2.get_legend_handles_labels()
ax1.legend(l1+l2, lb1+lb2, loc='lower right', frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9)
ax1.spines['top'].set_visible(False)
ax1.grid(alpha=0.15, linestyle='--')
fig.tight_layout()
save_fig(fig, 'figures/fig_trend.pdf')
```

**★ 防遮挡技巧（Time Series Dual Y 专用）：**
```python
# 1. 事件标记线的标签放在图顶部：rotation=90, va='top'
# 2. 相关性标注框放在图的角落：用 transform=ax.transAxes
# 3. 双轴标签颜色和对应数据系列一致：左轴蓝色，右轴橙色
# 4. 折线交叉区域不要放标注：标注放在趋势明确的区域
```

---

## 8. Residual Diagnostics (4-panel)

**Scene**: Enhanced 4-panel diagnostics. LOWESS smooth, Breusch-Pagan annotation, normal overlay, Cook's D threshold box.

```python
import numpy as np, matplotlib.pyplot as plt
from scipy import stats
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
n = 200; fitted = np.random.uniform(2, 8, n); resid = np.random.normal(0, 0.5, n)

fig, axes = plt.subplots(2, 2, figsize=(5.0, 4.9))   # 示例尺寸；保留模板比例，按实际显示尺寸检查字号与布局

ax = axes[0, 0]
ax.scatter(fitted, resid, alpha=0.45, s=18, color=PALETTE[0], edgecolor='white', linewidth=0.3, zorder=3)
ax.axhline(0, color=COLORS['down'], linestyle='--', linewidth=0.8, alpha=0.7)
z = np.polyfit(fitted, resid, 3); p = np.poly1d(z)
x_smooth = np.linspace(fitted.min(), fitted.max(), 100)
ax.plot(x_smooth, p(x_smooth), color=PALETTE[1], linewidth=2, zorder=4)
ax.text(0.97, 0.97, 'Breusch-Pagan\nχ²=2.14, p=0.143', transform=ax.transAxes, fontsize=7.5,
        va='top', ha='right', color=COLORS['text'],
        bbox=dict(boxstyle='round,pad=0.3', facecolor=_lighten(COLORS['highlight'], 0.85), edgecolor=_lighten(COLORS['highlight'], 0.4), alpha=0.95))
ax.set_xlabel('Fitted Values'); ax.set_ylabel('Residuals')
ax.set_title('(a)', fontsize=12, fontweight='bold', loc='left', pad=3)
ax.grid(alpha=0.15, linestyle='--')

ax = axes[0, 1]
osm, osr = stats.probplot(resid, dist='norm')[:2]
ax.scatter(osm[0], osm[1], alpha=0.5, s=15, color=PALETTE[0], edgecolor='white', linewidth=0.3)
slope, intercept = osr[:2]
x_line = np.array([osm[0].min(), osm[0].max()])
ax.plot(x_line, slope*x_line+intercept, color=COLORS['down'], linewidth=1.2, linestyle='--')
sw_stat, sw_p = stats.shapiro(resid[:100])
ax.text(0.03, 0.97, f'Shapiro-Wilk\nW={sw_stat:.3f}\np={sw_p:.3f}', transform=ax.transAxes,
        fontsize=7.5, va='top', ha='left', color=COLORS['text'],
        bbox=dict(boxstyle='round,pad=0.3', facecolor=_lighten(PALETTE[0], 0.8), edgecolor=_lighten(PALETTE[0], 0.6), alpha=0.95))
ax.set_xlabel('Theoretical Quantiles'); ax.set_ylabel('Sample Quantiles')
ax.set_title('(b)', fontsize=12, fontweight='bold', loc='left', pad=3)
ax.grid(alpha=0.15, linestyle='--')

ax = axes[1, 0]
ax.hist(resid, bins=30, density=True, color=_lighten(PALETTE[0], 0.4), alpha=0.5, edgecolor=PALETTE[0], linewidth=0.8)
x_norm = np.linspace(resid.min()-0.3, resid.max()+0.3, 200)
y_norm = stats.norm.pdf(x_norm, resid.mean(), resid.std())
ax.plot(x_norm, y_norm, color=COLORS['down'], linewidth=2, zorder=4)
for k in range(10, 0, -1):
    ax.fill_between(x_norm, 0, y_norm*(k/10), alpha=0.015, color=COLORS['down'], linewidth=0)
ax.set_xlabel('Residuals'); ax.set_ylabel('Density')
ax.set_title('(c)', fontsize=12, fontweight='bold', loc='left', pad=3)
ax.grid(alpha=0.15, linestyle='--')

ax = axes[1, 1]
cooks = np.random.exponential(0.005, n); cooks[15] = 0.035; cooks[87] = 0.028
threshold = 4/n
ml, sl, bl = ax.stem(range(n), cooks, linefmt='-', markerfmt=',', basefmt='')
plt.setp(sl, linewidth=0.6, color=PALETTE[2], alpha=0.7); plt.setp(bl, linewidth=0)
influential = cooks > threshold
ax.scatter(np.where(influential)[0], cooks[influential], color=COLORS['down'], s=25, zorder=5, edgecolor='white')
for idx in np.where(influential)[0]:
    ax.text(idx, cooks[idx]+0.001, f'#{idx}', fontsize=7, ha='center', color=COLORS['down'], fontweight='bold')
ax.axhline(threshold, color=COLORS['down'], linestyle='--', linewidth=1.0, alpha=0.7)
ax.axhspan(threshold, cooks.max()*1.2, color=COLORS['bg_box'], alpha=0.3, zorder=0)
ax.text(n*0.97, threshold+0.001, f'4/n={threshold:.3f}', ha='right', va='bottom', fontsize=8, color=COLORS['down'],
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=COLORS['down'], alpha=0.9))
ax.set_xlabel('Observation Index'); ax.set_ylabel("Cook's Distance")
ax.set_title('(d)', fontsize=12, fontweight='bold', loc='left', pad=3)
ax.grid(alpha=0.15, linestyle='--')

for ax in axes.flat:
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_diagnostics.pdf')
```


---

## 9. Moderation / Marginal Effects

**Scene**: Marginal effects with gradient CI bands, Johnson-Neyman significance region shading, crossover point annotation.

```python
import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

x = np.linspace(0, 1, 200); me = 0.3 - 0.5*x; se = 0.04 + 0.03*x

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

n_layers = 10
for k in range(n_layers, 0, -1):
    frac = k / n_layers
    ax1.fill_between(x, me - frac*1.96*se, me + frac*1.96*se, alpha=0.03, color=PALETTE[0], linewidth=0)

sig_mask = (me - 1.96*se > 0) | (me + 1.96*se < 0)
ax1.fill_between(x, -0.3, 0.5, where=sig_mask, alpha=0.06, color=COLORS['up'], zorder=0, label='Significant')
ax1.fill_between(x, -0.3, 0.5, where=~sig_mask, alpha=0.04, color=COLORS['down'], zorder=0, label='Non-significant')
ax1.plot(x, me, color=PALETTE[0], linewidth=2.5, zorder=5)
ax1.axhline(y=0, color=COLORS['ref_line'], linestyle='--', linewidth=0.8)

cross_idx = np.argmin(np.abs(me)); cross_x = x[cross_idx]
ax1.plot(cross_x, 0, 'o', color=PALETTE[1], markersize=12, zorder=6, markeredgecolor='white', markeredgewidth=2)
ax1.annotate(f'Crossover\nMod = {cross_x:.2f}', xy=(cross_x, 0),
             xytext=(cross_x+0.15, 0.12), fontsize=9, fontweight='bold', color=PALETTE[1],
             arrowprops=dict(arrowstyle='->', color=PALETTE[1], lw=1.5, connectionstyle='arc3,rad=-0.3'),
             bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=PALETTE[1], alpha=0.95))
ax1.set_xlabel('Moderator'); ax1.set_ylabel('Marginal Effect (95% CI)')
ax1.text(-0.1, 1.06, '(a)', transform=ax1.transAxes, fontsize=13, fontweight='bold')
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.legend(fontsize=8, frameon=False, edgecolor=COLORS['grid']); ax1.grid(alpha=0.15, linestyle='--')

x2 = np.linspace(0.3, 0.95, 100); yh = 2.58 + 0.08*x2; yl = 2.52 + 0.04*x2; se2 = 0.015
for k in range(8, 0, -1):
    frac = k / 8
    ax2.fill_between(x2, yh-frac*1.96*se2, yh+frac*1.96*se2, alpha=0.03, color=PALETTE[0], linewidth=0)
    ax2.fill_between(x2, yl-frac*1.96*se2, yl+frac*1.96*se2, alpha=0.03, color=PALETTE[1], linewidth=0)
ax2.plot(x2, yh, '-', color=PALETTE[0], linewidth=2.5, label='High (+1SD)')
ax2.plot(x2, yl, '--', color=PALETTE[1], linewidth=2.5, label='Low (−1SD)')
ax2.set_xlabel('Independent Variable'); ax2.set_ylabel('Predicted DV')
ax2.text(-0.1, 1.06, '(b)', transform=ax2.transAxes, fontsize=13, fontweight='bold')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9); ax2.grid(alpha=0.15, linestyle='--')

fig.tight_layout()
save_fig(fig, 'figures/fig_moderation.pdf')
```


---

## 10. Subgroup Forest / Heterogeneity

**Scene**: Subgroup forest with diamond pooled estimates per group, heterogeneity annotations, weight-proportional markers.

```python
import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

groups = {
    'By Region': {'color': PALETTE[0],
        'items': [('East',-.035,.006,True,15.2),('Central',-.022,.008,True,12.8),('West',-.015,.009,False,10.5)],
        'pooled': (-.025,.004), 'I2': 38.5, 'Q_p': 0.12},
    'By Size': {'color': PALETTE[1],
        'items': [('Large',-.028,.005,True,16.1),('Medium',-.019,.007,True,13.4),('Small',-.008,.010,False,8.9)],
        'pooled': (-.020,.004), 'I2': 52.1, 'Q_p': 0.04},
    'By Ownership': {'color': PALETTE[2],
        'items': [('SOE',-.012,.008,False,11.2),('Private',-.031,.006,True,14.7),('Foreign',-.025,.007,True,12.2)],
        'pooled': (-.023,.005), 'I2': 45.3, 'Q_p': 0.08},
}

# ★ 自适应高度
_total_items = sum(len(gd['items']) for gd in groups.values()) + len(groups) * 2
_fig_h = max(6, _total_items * 0.65 + 2)
fig, ax = plt.subplots(figsize=(10, _fig_h)); yp = 0
for gn, gd in groups.items():
    gc = gd['color']; yp -= 0.5
    ax.axhspan(yp-0.4, yp+0.4, color=gc, alpha=0.08, zorder=0)
    ax.text(-0.065, yp, f'■ {gn}', ha='left', va='center', fontsize=10.5, fontweight='bold', color=gc)
    yp -= 1.2
    for lb, c, s, sig, wt in gd['items']:
        lo, hi = c-1.96*s, c+1.96*s
        ax.plot([lo, hi], [yp, yp], color=COLORS['text'], linewidth=1.0, zorder=2)
        ax.plot([lo, lo], [yp-.12, yp+.12], color=COLORS['text'], linewidth=1.0)
        ax.plot([hi, hi], [yp-.12, yp+.12], color=COLORS['text'], linewidth=1.0)
        ms = 4 + wt/3; fc = gc if sig else 'white'; ec = gc if sig else COLORS['ref_line']
        ax.plot(c, yp, 'o', color=fc, markersize=ms, markeredgecolor=ec, markeredgewidth=1.2, zorder=3)
        ax.text(-0.065, yp, f'  {lb}', ha='left', va='center', fontsize=9, color=COLORS['text'])
        ax.text(0.065, yp, f'{wt:.1f}%', ha='right', va='center', fontsize=8, color=COLORS['ref_line'])
        yp -= 1.3
    pc, ps = gd['pooled']; plo, phi = pc-1.96*ps, pc+1.96*ps; dh = 0.3
    ax.fill([plo,pc,phi,pc], [yp,yp+dh,yp,yp-dh], color=gc, alpha=0.7, zorder=4)
    ax.plot([plo,pc,phi,pc,plo], [yp,yp+dh,yp,yp-dh,yp], color=gc, linewidth=0.8, zorder=5)
    ax.text(-0.065, yp, '  Pooled', ha='left', va='center', fontsize=9, fontweight='bold', color=gc)
    ax.text(0.065, yp, f'I²={gd["I2"]:.1f}%, Q p={gd["Q_p"]:.3f}', ha='right', va='center',
            fontsize=7.5, color=COLORS['ref_line'], fontstyle='italic')
    yp -= 1.8

ax.axvline(x=0, color=COLORS['down'], linestyle='--', linewidth=1.5, alpha=0.7, zorder=1)
ax.set_yticks([]); ax.set_xlabel('Coefficient', fontsize=12)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False); ax.set_ylim(yp-0.5, 0.5); ax.invert_yaxis()
ax.grid(axis='x', alpha=0.15, linestyle='--')
fig.tight_layout()
save_fig(fig, 'figures/fig_subgroup.pdf')
```

**★ 防遮挡技巧（Subgroup Forest 专用）：**
```python
# 1. 分组标题用粗体 + 灰色背景条：和数据行视觉区分
# 2. I² 标注框放在 diamond 右侧：不要放在 CI 线上
# 3. 自适应高度：_fig_h = max(6, (n_groups * n_items_per_group) * 0.35 + 2)
# 4. 数值标签统一放在 CI 右端外侧：fontsize=7.5（比普通森林图更小）
```

---

## 11. Quantile Regression

**Scene**: Quantile process with gradient fill, OLS comparison band, significance region shading.

```python
import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

q = np.arange(0.1, 1.0, 0.1)
c = np.array([-.35,-.30,-.25,-.20,-.15,-.10,-.05,.02,.08])
se = np.array([.06,.05,.04,.04,.04,.05,.05,.06,.07]); ols = -0.18; ols_se = 0.03

fig, ax = plt.subplots(figsize=(8, 5))
n_layers = 10
for k in range(n_layers, 0, -1):
    frac = k / n_layers
    ax.fill_between(q, c-frac*1.96*se, c+frac*1.96*se, alpha=0.03, color=PALETTE[0], linewidth=0)

ax.fill_between(q, ols-1.96*ols_se, ols+1.96*ols_se, alpha=0.12, color=PALETTE[1], linewidth=0, label='OLS 95% CI')
ax.axhline(y=ols, color=PALETTE[1], linestyle='--', linewidth=1.5, alpha=0.8)

sig_mask = (c-1.96*se > 0) | (c+1.96*se < 0)
for i in range(len(q)):
    if sig_mask[i]: ax.axvspan(q[i]-0.04, q[i]+0.04, color=COLORS['up'], alpha=0.06, zorder=0)

ax.axhline(y=0, color=COLORS['ref_line'], linestyle='-', linewidth=0.5, alpha=0.5)
ax.plot(q, c, 'o-', color=PALETTE[0], linewidth=2.5, markersize=8,
        markeredgecolor='white', markeredgewidth=1.2, label='QR Coefficient', zorder=5)
ax.fill_between(q, c, ols, alpha=0.06, color=PALETTE[2], label='QR−OLS Gap', linewidth=0)

for qi, ci, si in zip(q, c, se):
    if abs(ci) > 1.96*si:
        star = '***' if abs(ci) > 2.576*si else '**'
        ax.text(qi, ci+1.96*si+0.015, star, ha='center', va='bottom', fontsize=8, color=PALETTE[0], fontweight='bold')

ax.annotate(f'τ=0.9: {c[-1]:.3f}', xy=(q[-1], c[-1]),
            xytext=(q[-1]-0.15, c[-1]+0.12), fontsize=9, color=PALETTE[0],
            arrowprops=dict(arrowstyle='->', color=PALETTE[0], lw=1.2),
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=PALETTE[0], alpha=0.9))

ax.set_xlabel('Quantile (τ)', fontsize=11); ax.set_ylabel('Coefficient', fontsize=11)
ax.set_xticks(q); ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='upper left')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(alpha=0.15, linestyle='--')
fig.tight_layout()
save_fig(fig, 'figures/fig_quantile.pdf')
```

---

## 12. PSM Balance (Love Plot)

**Scene**: Before/after matching balance with connecting arrows, threshold shading, improvement % labels.

```python
import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

covs = ['GDP per capita','Population','Education','Urbanization','FDI Inflow','R&D Spending','Infrastructure']
before = np.array([.35,.28,.22,.18,.42,.31,.25]); after = np.array([.05,.03,.08,.02,.06,.04,.07])

# ★ 自适应高度
_fig_h = max(4, len(covs) * 0.7 + 1.5)
fig, ax = plt.subplots(figsize=(9, _fig_h)); y = np.arange(len(covs))
ax.axvspan(-0.10, 0.10, color=_lighten(COLORS['up'], 0.8), alpha=0.4, zorder=0, label='Acceptable (|d|<0.10)')
ax.axvline(x=0.10, color=COLORS['up'], linestyle='--', linewidth=0.8, alpha=0.6)

for i in range(len(covs)):
    ax.annotate('', xy=(after[i], y[i]), xytext=(before[i], y[i]),
                arrowprops=dict(arrowstyle='->', color=COLORS['neutral'], lw=1.2))
    improvement = (1 - after[i]/before[i]) * 100
    ax.text((before[i]+after[i])/2, y[i]+0.25, f'↓{improvement:.0f}%', ha='center', va='bottom',
            fontsize=7.5, color=COLORS['up'], fontweight='bold')

ax.scatter(before, y, s=80, color=PALETTE[1], marker='o', zorder=4, label='Before', edgecolor='white')
ax.scatter(after, y, s=80, color=PALETTE[0], marker='D', zorder=4, label='After', edgecolor='white')

ax.set_yticks(y); ax.set_yticklabels(covs, fontsize=10)
ax.set_xlabel('Standardized Mean Difference', fontsize=11); ax.invert_yaxis()

avg_b, avg_a = np.mean(before), np.mean(after)
ax.text(0.97, 0.03, f'Avg |SMD| Before: {avg_b:.3f}\nAvg |SMD| After: {avg_a:.3f}\nReduction: {(1-avg_a/avg_b)*100:.1f}%',
        transform=ax.transAxes, fontsize=8.5, va='bottom', ha='right', color=COLORS['text'],
        bbox=dict(boxstyle='round,pad=0.4', facecolor=COLORS['bg_box'], edgecolor=COLORS['grid'], alpha=0.95))

ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='best')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='x', alpha=0.15, linestyle='--')
fig.tight_layout()
save_fig(fig, 'figures/fig_psm.pdf')
```

**★ 防遮挡技巧（PSM Balance / Love Plot 专用）：**
```python
# 1. 改善率 % 标签放在箭头右侧：不要放在箭头上方（会和相邻变量重叠）
# 2. 阈值线标签放在图顶部：不要放在数据密集区
# 3. 变量名长时：fontsize=8，或用缩写
# 4. 自适应高度：_fig_h = max(5, n_vars * 0.4 + 1.5)
```

---

## 13. Prediction vs Actual with CI Band

**Scene**: Time series prediction with gradient CI band, error histogram on right margin, RMSE/MAE box, train/test gradient background.

```python
import numpy as np, matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy.stats import gaussian_kde
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
t = np.arange(100)
actual = 50 + 10*np.sin(t/10) + np.cumsum(np.random.randn(100)*0.5)
pred = actual + np.random.randn(100)*2
ci_upper = pred + 3 + np.abs(np.random.randn(100))*1.5
ci_lower = pred - 3 - np.abs(np.random.randn(100))*1.5
errors = actual - pred; split_point = 70

fig = plt.figure(figsize=(11, 5))
gs = GridSpec(1, 2, width_ratios=[5, 1], wspace=0.05)
ax = fig.add_subplot(gs[0])

ax.axvspan(0, split_point, color=_lighten(PALETTE[0], 0.8), alpha=0.3, zorder=0)
ax.axvspan(split_point, 100, color=_lighten(COLORS['highlight'], 0.8), alpha=0.3, zorder=0)
ax.axvline(x=split_point, color=COLORS['ref_line'], linestyle=':', linewidth=1.2, alpha=0.6)
ax.text(split_point/2, actual.max()+2, 'Training', ha='center', fontsize=9, color=COLORS['text'],
        bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor=COLORS['grid'], alpha=0.9))
ax.text((split_point+100)/2, actual.max()+2, 'Testing', ha='center', fontsize=9, color=COLORS['text'],
        bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor=COLORS['grid'], alpha=0.9))

n_layers = 12
for k in range(n_layers, 0, -1):
    frac = k / n_layers
    ax.fill_between(t, pred-frac*(pred-ci_lower), pred+frac*(ci_upper-pred),
                    alpha=0.025, color=PALETTE[1], linewidth=0)

ax.plot(t, actual, color=PALETTE[0], linewidth=1.8, label='Actual', zorder=4)
ax.plot(t, pred, color=PALETTE[1], linewidth=1.5, linestyle='--', label='Predicted', zorder=3)

te = actual[split_point:] - pred[split_point:]
rmse = np.sqrt(np.mean(te**2)); mae = np.mean(np.abs(te))
r2 = 1 - np.sum(te**2)/np.sum((actual[split_point:]-actual[split_point:].mean())**2)
ax.text(0.02, 0.03, f'Test Metrics:\nRMSE = {rmse:.3f}\nMAE  = {mae:.3f}\nR²   = {r2:.3f}',
        transform=ax.transAxes, fontsize=8.5, va='bottom', ha='left', color=COLORS['text'], family='monospace',
        bbox=dict(boxstyle='round,pad=0.4', facecolor=COLORS['bg_box'], edgecolor=COLORS['grid'], alpha=0.95))

ax.set_xlabel('Time Step'); ax.set_ylabel('Value (a.u.)')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9); ax.grid(alpha=0.15, linestyle='--')

ax_hist = fig.add_subplot(gs[1])
ax_hist.hist(errors, bins=25, orientation='horizontal', color=_lighten(PALETTE[1], 0.4), alpha=0.5, edgecolor=PALETTE[1], linewidth=0.8, density=True)
kde = gaussian_kde(errors); y_kde = np.linspace(errors.min(), errors.max(), 100)
ax_hist.plot(kde(y_kde), y_kde, color=PALETTE[1], linewidth=1.5)
ax_hist.axhline(0, color=COLORS['ref_line'], linestyle='--', linewidth=0.6, alpha=0.5)
ax_hist.set_xlabel('Density (1/a.u.)', fontsize=9)
ax_hist.set_ylabel('Actual − predicted (a.u.)', fontsize=9)
ax_hist.yaxis.set_label_position('right')
ax_hist.yaxis.tick_right()
ax_hist.tick_params(axis='y', labelsize=8, labelleft=False, labelright=True)
ax_hist.spines['top'].set_visible(False); ax_hist.spines['right'].set_visible(False)

fig.tight_layout()
save_fig(fig, 'figures/fig_prediction_ci.pdf')
```


---

## 14. Multi-Model Prediction Accuracy Heatmap

**Scene**: Multi-model accuracy matrix with rank annotations ①②③, sorted rows, best-in-column bold borders.

```python
import numpy as np, matplotlib.pyplot as plt; from _utils.palette_maps import palette_cmap, palette_stops, contrast_text
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

models = ['LSTM','GRU','Transformer','ARIMA','Prophet','Ours']
metrics = ['MAE↓','RMSE↓','MAPE(%)↓','R²↑']
data = np.array([[3.21,4.15,5.8,0.921],[3.45,4.38,6.2,0.908],[2.98,3.87,5.1,0.935],
                  [5.12,6.73,9.4,0.842],[4.67,5.92,8.1,0.867],[2.45,3.21,4.3,0.952]])

norm = np.zeros_like(data)
for j in range(data.shape[1]):
    col = data[:, j]
    if '↓' in metrics[j]: norm[:, j] = (col-col.min())/(col.max()-col.min()+1e-10)
    else: norm[:, j] = 1 - (col-col.min())/(col.max()-col.min()+1e-10)

avg_score = norm.mean(axis=1); sort_idx = np.argsort(avg_score)
data = data[sort_idx]; norm = norm[sort_idx]; models = [models[i] for i in sort_idx]
rank_symbols = ['①','②','③','④','⑤','⑥']

fig, ax = plt.subplots(figsize=(8, 5))
im = ax.imshow(norm, cmap=palette_cmap('sequential'), aspect='auto', vmin=0, vmax=1)

for j in range(data.shape[1]):
    col = data[:, j]
    ranks = np.argsort(np.argsort(col)) if '↓' in metrics[j] else np.argsort(np.argsort(-col))
    best_idx = np.argmin(col) if '↓' in metrics[j] else np.argmax(col)
    for i in range(data.shape[0]):
        txt_color = contrast_text(im.cmap(im.norm(norm[i, j])))
        w = 'bold' if i == best_idx else 'normal'
        rank_str = f' {rank_symbols[ranks[i]]}' if ranks[i] < 3 else ''
        ax.text(j, i, f'{data[i,j]:.2f}{rank_str}', ha='center', va='center',
                fontsize=9.5, fontweight=w, color=txt_color)
        if i == best_idx:
            ax.add_patch(plt.Rectangle((j-0.5, i-0.5), 1, 1, linewidth=2.5,
                                        edgecolor=COLORS['up'], facecolor='none', zorder=5))

ax.set_xticks(range(len(metrics))); ax.set_xticklabels(metrics, fontsize=10.5)
ax.set_yticks(range(len(models))); ax.set_yticklabels(models, fontsize=10.5)
cbar = fig.colorbar(im, ax=ax, shrink=0.7, pad=0.20)
cbar.set_label('Normalized Score\n(0=Best, 1=Worst)', fontsize=9)
ax.spines[:].set_visible(False)
ax.tick_params(top=True, bottom=False, labeltop=True, labelbottom=False)
for i in range(len(models)):
    ax.text(len(metrics)-0.25, i, f'Avg: {avg_score[sort_idx[i]]:.2f}', ha='left', va='center', fontsize=8, color=COLORS['text'])
fig.tight_layout()
save_fig(fig, 'figures/fig_model_accuracy_heatmap.pdf')
```

---

## 15. Prediction Error Distribution (Rain Cloud)

**Scene**: Multi-model error rain cloud with gradient violin, zero-line significance test, outlier labels.

```python
import numpy as np, matplotlib.pyplot as plt
from scipy.stats import gaussian_kde, ttest_1samp
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
models = ['Ours','LSTM','ARIMA','Prophet']
errors = [np.random.normal(0,1.5,200), np.random.normal(0.5,3,200),
          np.random.normal(1,4,200), np.random.normal(0.3,2.5,200)]

# ★ 自适应高度
_fig_h = max(4, len(models) * 1.2 + 1)
fig, ax = plt.subplots(figsize=(9, _fig_h))
for i, (model, err) in enumerate(zip(models, errors)):
    y_pos = i * 1.5
    kde = gaussian_kde(err)
    x_kde = np.linspace(err.min(), err.max(), 200)
    y_kde = kde(x_kde); y_kde_norm = y_kde / y_kde.max() * 0.5

    n_layers = 12
    for k in range(n_layers, 0, -1):
        frac = k / n_layers
        ax.fill_between(x_kde, y_pos, y_pos + y_kde_norm*frac, alpha=0.03, color=PALETTE[i], linewidth=0)
    ax.fill_between(x_kde, y_pos, y_pos + y_kde_norm, alpha=0.2, color=PALETTE[i], linewidth=0)
    ax.plot(x_kde, y_pos + y_kde_norm, color=PALETTE[i], linewidth=1.2)

    ax.boxplot([err], positions=[y_pos], vert=False, widths=0.18, patch_artist=True,
               boxprops=dict(facecolor=_lighten(PALETTE[i], 0.4), edgecolor=PALETTE[i], linewidth=1.2),
               medianprops=dict(color=COLORS['text'], linewidth=1.5),
               whiskerprops=dict(color=PALETTE[i]), capprops=dict(color=PALETTE[i]),
               flierprops=dict(marker='.', markersize=2, alpha=0.3))

    jitter = np.random.uniform(-0.1, -0.4, len(err))
    ax.scatter(err[::4], y_pos + jitter[:len(err[::4])], s=5, alpha=0.25, color=PALETTE[i], zorder=2)

    q1, q3 = np.percentile(err, [25, 75]); iqr = q3 - q1
    outlier_mask = (err < q1-2.5*iqr) | (err > q3+2.5*iqr)
    outliers = err[outlier_mask]
    if len(outliers) > 0:
        ax.scatter(outliers, [y_pos]*len(outliers), s=30, color=COLORS['down'], marker='x', zorder=6, linewidth=1.5)
        for ov in outliers[:3]:
            ax.text(ov, y_pos+0.6, f'{ov:.1f}', ha='center', va='bottom', fontsize=7, color=COLORS['down'], fontweight='bold')

    t_stat, p_val = ttest_1samp(err, 0)
    sig_str = '***' if p_val < 0.001 else ('**' if p_val < 0.01 else ('*' if p_val < 0.05 else 'ns'))
    ax.text(err.max()+1, y_pos, f't={t_stat:.2f} {sig_str}', ha='left', va='center', fontsize=8, color=COLORS['text'],
            bbox=dict(boxstyle='round,pad=0.2', facecolor=COLORS['bg_box'], edgecolor=COLORS['grid'], alpha=0.9))

ax.axvline(0, color=COLORS['down'], linestyle='--', linewidth=1.0, alpha=0.6)
ax.text(0, len(models)*1.5-0.3, 'Zero Error', ha='center', va='bottom', fontsize=8, color=COLORS['down'],
        bbox=dict(boxstyle='round,pad=0.2', facecolor=COLORS['bg_box'], edgecolor=COLORS['down'], alpha=0.9))
ax.set_yticks([i*1.5 for i in range(len(models))]); ax.set_yticklabels(models, fontsize=10)
ax.set_xlabel('Prediction Error', fontsize=11); ax.grid(axis='x', alpha=0.15, linestyle='--')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_error_raincloud.pdf')
```

---

## 16. Multi-Step Prediction Decay

**Scene**: Accuracy decay over horizon. Gradient fill between best/worst, decay rate annotation, threshold shading.

```python
import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
steps = np.arange(1, 13)
models_data = {'Ours': 0.95*np.exp(-0.03*steps)+np.random.randn(12)*0.005,
               'LSTM': 0.92*np.exp(-0.05*steps)+np.random.randn(12)*0.008,
               'GRU': 0.91*np.exp(-0.045*steps)+np.random.randn(12)*0.007,
               'ARIMA': 0.88*np.exp(-0.08*steps)+np.random.randn(12)*0.01}

fig, ax = plt.subplots(figsize=(9, 5))
all_vals = np.array(list(models_data.values()))
best_line, worst_line = all_vals.max(axis=0), all_vals.min(axis=0)

n_layers = 15
for k in range(n_layers, 0, -1):
    frac = k / n_layers
    ax.fill_between(steps, worst_line, worst_line+frac*(best_line-worst_line),
                    alpha=0.02, color=PALETTE[0], linewidth=0)
ax.fill_between(steps, worst_line, best_line, alpha=0.06, color=PALETTE[0], linewidth=0, label='Model Spread')

threshold = 0.80
ax.axhline(y=threshold, color=COLORS['up'], linestyle='--', linewidth=1.2, alpha=0.7)
ax.axhspan(0, threshold, color=COLORS['bg_box'], alpha=0.15, zorder=0)
ax.axhspan(threshold, 1.0, color=_lighten(COLORS['up'], 0.8), alpha=0.1, zorder=0)
ax.text(12.3, threshold, 'Acceptable\nThreshold', ha='left', va='center', fontsize=8, color=COLORS['up'],
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=COLORS['up'], alpha=0.9))

markers = ['o','s','D','^']
for i, (name, acc) in enumerate(models_data.items()):
    lw = 2.5 if name == 'Ours' else 1.5; ms = 7 if name == 'Ours' else 5
    ax.plot(steps, acc, f'{markers[i]}-', color=PALETTE[i], linewidth=lw, markersize=ms,
            label=name, markeredgecolor='white', markeredgewidth=0.8, zorder=5)
    if name in ['Ours', 'ARIMA']:
        decay_rate = (acc[0]-acc[-1])/acc[0]*100
        ax.annotate(f'Decay: {decay_rate:.1f}%', xy=(steps[-1], acc[-1]),
                    xytext=(steps[-1]-2.5, acc[-1]-0.04), fontsize=8, color=PALETTE[i],
                    arrowprops=dict(arrowstyle='->', color=PALETTE[i], lw=1.0, connectionstyle='arc3,rad=0.2'),
                    bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor=PALETTE[i], alpha=0.9))

ax.set_xlabel('Prediction Horizon (steps ahead)', fontsize=11); ax.set_ylabel('R² Score', fontsize=11)
ax.set_xticks(steps); ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='lower left', ncol=2)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(alpha=0.15, linestyle='--'); ax.set_ylim(0.55, 1.0)
fig.tight_layout()
save_fig(fig, 'figures/fig_multistep_decay.pdf')
```


---

## 17. Moran's I Scatter Plot (真实空间自相关 + esda 计算 + Queen 权重)

**Scene**: 真实空间自相关可视化。使用 `esda.Moran` + `libpysal.weights.Queen` 计算 Moran's I，四象限着色（HH/LL/LH/HL），OLS 拟合线（斜率 = Moran's I），标注离回归线最远的省份。适用于空间计量经济学论文。

```python
import shutil, os
os.makedirs('_utils', exist_ok=True)
for f in ['plot_utils.py', 'china_provinces.geojson']:
    src = os.path.join(os.path.dirname(__file__), f)
    if os.path.exists(src):
        shutil.copy2(src, f'_utils/{f}')

import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten, smart_labels
setup_style()

import geopandas as gpd
from libpysal.weights import Queen
from esda.moran import Moran

# === 加载中国省级 GeoJSON + 模拟数据 ===
gdf = gpd.read_file('_utils/china_provinces.geojson')

np.random.seed(42)
# 模拟一个有空间自相关的变量（东部高、西部低）
gdf['centroid_x'] = gdf.geometry.centroid.x
gdf['value'] = 0.3 + 0.005 * (gdf['centroid_x'] - 80) + np.random.randn(len(gdf)) * 0.08
gdf['value'] = gdf['value'].clip(0.1, 0.95)

provinces_short = {
    '北京市':'北京','天津市':'天津','河北省':'河北','山西省':'山西',
    '内蒙古自治区':'内蒙古','辽宁省':'辽宁','吉林省':'吉林','黑龙江省':'黑龙江',
    '上海市':'上海','江苏省':'江苏','浙江省':'浙江','安徽省':'安徽',
    '福建省':'福建','江西省':'江西','山东省':'山东','河南省':'河南',
    '湖北省':'湖北','湖南省':'湖南','广东省':'广东','广西壮族自治区':'广西',
    '海南省':'海南','重庆市':'重庆','四川省':'四川','贵州省':'贵州',
    '云南省':'云南','西藏自治区':'西藏','陕西省':'陕西','甘肃省':'甘肃',
    '青海省':'青海','宁夏回族自治区':'宁夏','新疆维吾尔自治区':'新疆',
    '台湾省':'台湾','香港特别行政区':'香港','澳门特别行政区':'澳门',
}
gdf['short_name'] = gdf['name'].map(provinces_short).fillna(gdf['name'])

# === 用 libpysal 构建空间权重矩阵，用 esda 计算 Moran's I ===
w = Queen.from_dataframe(gdf)
w.transform = 'r'  # 行标准化

y = gdf['value'].values
moran = Moran(y, w)

# 标准化变量和空间滞后
z = (y - y.mean()) / y.std()
wz = np.array([np.sum(w.weights[i] * z[list(w.neighbors[i])]) for i in range(len(z))])

# === 画图 ===
fig, ax = plt.subplots(figsize=(7, 6.5))

xlim = (z.min() - 0.8, z.max() + 0.8)
ylim = (wz.min() - 0.8, wz.max() + 0.8)

# 象限背景
ax.fill_between([0, xlim[1]], 0, ylim[1], alpha=0.06, color=PALETTE[0], zorder=0)
ax.fill_between([xlim[0], 0], ylim[0], 0, alpha=0.06, color=PALETTE[1], zorder=0)
ax.fill_between([xlim[0], 0], 0, ylim[1], alpha=0.06, color=PALETTE[2], zorder=0)
ax.fill_between([0, xlim[1]], ylim[0], 0, alpha=0.06, color=PALETTE[3], zorder=0)

ax.axhline(0, color=COLORS['grid'], linewidth=0.8, zorder=1)
ax.axvline(0, color=COLORS['grid'], linewidth=0.8, zorder=1)

# 散点（按象限着色）
for i in range(len(z)):
    if z[i] >= 0 and wz[i] >= 0: c = PALETTE[0]
    elif z[i] < 0 and wz[i] < 0: c = PALETTE[1]
    elif z[i] < 0 and wz[i] >= 0: c = PALETTE[2]
    else: c = PALETTE[3]
    ax.scatter(z[i], wz[i], c=c, s=60, edgecolors='white', linewidths=0.8, zorder=3, alpha=0.85)

# OLS 拟合线（斜率 = Moran's I）
x_fit = np.linspace(xlim[0], xlim[1], 100)
ax.plot(x_fit, moran.I * x_fit, '--', color=COLORS['text'], linewidth=1.2, alpha=0.6, zorder=2)

# 象限标签
ax.text(xlim[1] - 0.2, ylim[1] - 0.2, 'HH', fontsize=14, ha='right', va='top',
        color=PALETTE[0], fontweight='bold', alpha=0.4)
ax.text(xlim[0] + 0.2, ylim[0] + 0.2, 'LL', fontsize=14, ha='left', va='bottom',
        color=PALETTE[1], fontweight='bold', alpha=0.4)
ax.text(xlim[0] + 0.2, ylim[1] - 0.2, 'LH', fontsize=14, ha='left', va='top',
        color=PALETTE[2], fontweight='bold', alpha=0.4)
ax.text(xlim[1] - 0.2, ylim[0] + 0.2, 'HL', fontsize=14, ha='right', va='bottom',
        color=PALETTE[3], fontweight='bold', alpha=0.4)

# 标注离回归线最远的省份
residuals = np.abs(wz - moran.I * z)
top_idx = np.argsort(residuals)[-7:]
for i in top_idx:
    ax.annotate(gdf['short_name'].iloc[i], xy=(z[i], wz[i]),
                xytext=(6, 4), textcoords='offset points',
                fontsize=7.5, color=COLORS['text'],
                bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                          edgecolor=COLORS['grid'], alpha=0.85))

# Moran's I 标注
sig = '***' if moran.p_sim < 0.01 else '**' if moran.p_sim < 0.05 else '*' if moran.p_sim < 0.1 else ''
ax.text(0.03, 0.97, f"Moran's I = {moran.I:.4f}{sig}\np = {moran.p_sim:.4f}\n(999 permutations)",
        transform=ax.transAxes, fontsize=9, va='top',
        bbox=dict(boxstyle='round,pad=0.4', facecolor=COLORS['bg_box'],
                  edgecolor=COLORS['grid'], alpha=0.95))

ax.set_xlabel('标准化变量 (z)', fontsize=11)
ax.set_ylabel('空间滞后 (Wz)', fontsize=11)
ax.set_xlim(xlim); ax.set_ylim(ylim)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_moran_scatter.pdf')
```

**★ 防遮挡技巧（Moran's I Scatter 专用）：**
```python
# 1. 省份/地区标签必须用 adjustText 或 smart_labels()：四象限内标签密集
# 2. 只标注离回归线最远的 top-8 个点：不要标注所有点
# 3. 标签用 bbox 白底 + arrowprops 连线：防止和散点混在一起
# 4. 象限标签放在四角：fontsize=9, alpha=0.6
```

---

## 18. LISA Cluster Map (真实局部空间自相关 + esda.Moran_Local + 中国省级地图)

**Scene**: 真实局部空间自相关可视化。使用 `esda.Moran_Local` + `libpysal.weights.Queen` 计算 LISA 聚类，基于 `china_provinces.geojson` 绘制中国省级地图，按聚类类型着色（HH=热点红, LL=冷点蓝, LH/HL=空间异常, NS=不显著灰）。适用于空间计量经济学论文。

```python
import shutil, os
os.makedirs('_utils', exist_ok=True)
for f in ['plot_utils.py', 'china_provinces.geojson']:
    src = os.path.join(os.path.dirname(__file__), f)
    if os.path.exists(src):
        shutil.copy2(src, f'_utils/{f}')

import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

import geopandas as gpd
from libpysal.weights import Queen
from esda.moran import Moran_Local

gdf = gpd.read_file('_utils/china_provinces.geojson')

# 模拟有空间自相关的数据
np.random.seed(42)
gdf['centroid_x'] = gdf.geometry.centroid.x
gdf['value'] = 0.3 + 0.005 * (gdf['centroid_x'] - 80) + np.random.randn(len(gdf)) * 0.08
gdf['value'] = gdf['value'].clip(0.1, 0.95)

# 构建空间权重 + 计算 LISA
w = Queen.from_dataframe(gdf, use_index=False)
w.transform = 'r'
lisa = Moran_Local(gdf['value'].values, w, permutations=999)

# LISA 聚类分类
# lisa.q: 1=HH, 2=LH, 3=LL, 4=HL
# lisa.p_sim: p 值
sig_level = 0.05
gdf['lisa_cluster'] = 'NS'
for i in range(len(gdf)):
    if lisa.p_sim[i] <= sig_level:
        q = lisa.q[i]
        if q == 1: gdf.loc[gdf.index[i], 'lisa_cluster'] = 'HH'
        elif q == 2: gdf.loc[gdf.index[i], 'lisa_cluster'] = 'LH'
        elif q == 3: gdf.loc[gdf.index[i], 'lisa_cluster'] = 'LL'
        elif q == 4: gdf.loc[gdf.index[i], 'lisa_cluster'] = 'HL'

cluster_colors = {
    'HH': '#E25B5B',  # 热点（红色）
    'LL': '#5B8DB8',  # 冷点（蓝色）
    'LH': '#A8C4D8',  # 低高异常（浅蓝）
    'HL': '#E0A0A0',  # 高低异常（浅红）
    'NS': '#F0F0F0',  # 不显著（灰色）
}

from collections import Counter
counts = Counter(gdf['lisa_cluster'])

# === 画图 ===
fig, ax = plt.subplots(figsize=(10, 8))

for cluster_type in ['NS', 'HL', 'LH', 'LL', 'HH']:  # NS 先画，显著的后画
    subset = gdf[gdf['lisa_cluster'] == cluster_type]
    if len(subset) > 0:
        subset.plot(color=cluster_colors[cluster_type], edgecolor='white',
                    linewidth=0.5, ax=ax, zorder=2 if cluster_type != 'NS' else 1)

# 省份简称标注（只标注显著的）
provinces_short = {
    '北京市':'北京','天津市':'天津','河北省':'河北','山西省':'山西',
    '内蒙古自治区':'内蒙古','辽宁省':'辽宁','吉林省':'吉林','黑龙江省':'黑龙江',
    '上海市':'上海','江苏省':'江苏','浙江省':'浙江','安徽省':'安徽',
    '福建省':'福建','江西省':'江西','山东省':'山东','河南省':'河南',
    '湖北省':'湖北','湖南省':'湖南','广东省':'广东','广西壮族自治区':'广西',
    '海南省':'海南','重庆市':'重庆','四川省':'四川','贵州省':'贵州',
    '云南省':'云南','西藏自治区':'西藏','陕西省':'陕西','甘肃省':'甘肃',
    '青海省':'青海','宁夏回族自治区':'宁夏','新疆维吾尔自治区':'新疆',
    '台湾省':'台湾','香港特别行政区':'香港','澳门特别行政区':'澳门',
}

for _, row in gdf[gdf['lisa_cluster'] != 'NS'].iterrows():
    c = row.geometry.centroid
    short = provinces_short.get(row['name'], row['name'][:2])
    # ★ 统一用不透明白底 bbox + 深色文字
    ax.text(c.x, c.y, short, ha='center', va='center', fontsize=6.5,
            fontweight='bold', color='#333333',
            bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                      edgecolor='#999999', linewidth=0.6, alpha=0.92))

# 图例
from matplotlib.patches import Patch
legend_labels = {
    'HH': f'高高聚集 ({counts.get("HH", 0)})',
    'LL': f'低低聚集 ({counts.get("LL", 0)})',
    'LH': f'低高异常 ({counts.get("LH", 0)})',
    'HL': f'高低异常 ({counts.get("HL", 0)})',
    'NS': f'不显著 ({counts.get("NS", 0)})',
}
legend_elements = [Patch(facecolor=cluster_colors[k], edgecolor='white',
                         label=legend_labels[k]) for k in ['HH', 'LL', 'LH', 'HL', 'NS']]
ax.legend(handles=legend_elements, loc='lower left', fontsize=8.5,
          frameon=False, labelspacing=0.35, handlelength=1.6, title=f'LISA 聚类 (p < {sig_level})', title_fontsize=9)

ax.set_xlim(73, 136); ax.set_ylim(17, 54)
ax.set_axis_off()

# Moran's I 全局统计标注
ax.text(0.98, 0.98, f"Global Moran's I = {lisa.Is.mean():.4f}\n999 permutations",
        transform=ax.transAxes, fontsize=8.5, ha='right', va='top',
        bbox=dict(boxstyle='round,pad=0.4', facecolor=COLORS['bg_box'],
                  edgecolor=COLORS['grid'], alpha=0.95))

fig.tight_layout()
save_fig(fig, 'figures/fig_lisa_map.pdf')
```

**★ 防遮挡技巧（LISA Cluster Map 专用）：**
```python
# 1. 只标注显著省份（p < 0.05）：不显著的不标
# 2. 标注用简称（前两字）：不要用全称
# 3. 深色聚类（HH/LL）用白字，浅色（LH/HL/NS）用深字
# 4. 图例放左下角：中国地图左下角通常是空白区域
# 5. xlim/ylim 固定为 (73,136)/(17,54)
```

---

## 19. Coefficient Stability Plot (Sequential Control Variable Addition)

**Scene**: Shows how the core coefficient changes as control variables are added one by one. Demonstrates robustness — if the coefficient stays stable, the result is robust. Common in applied econometrics papers.

```python
import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

# === Example data (replace with actual regression results) ===
specs = ['基准', '+经济水平', '+城镇化', '+人力资本', '+FDI', '+金融发展', '+基础设施', '全控制']
coefs = [0.045, 0.042, 0.041, 0.039, 0.040, 0.038, 0.037, 0.036]
ci_lower = [0.032, 0.030, 0.029, 0.027, 0.028, 0.026, 0.025, 0.024]
ci_upper = [0.058, 0.054, 0.053, 0.051, 0.052, 0.050, 0.049, 0.048]
n_controls = list(range(len(specs)))

fig, ax = plt.subplots(figsize=(9, 5))

# CI band (gradient fill)
ax.fill_between(n_controls, ci_lower, ci_upper, alpha=0.15, color=PALETTE[0])
ax.fill_between(n_controls, [c - (c - cl) * 0.5 for c, cl in zip(coefs, ci_lower)],
                [c + (cu - c) * 0.5 for c, cu in zip(coefs, ci_upper)],
                alpha=0.25, color=PALETTE[0])

# Coefficient line + markers
ax.plot(n_controls, coefs, 'o-', color=PALETTE[0], linewidth=2.5, markersize=8,
        markeredgecolor='white', markeredgewidth=1.5, zorder=5)

# Value labels
for i, (x, y) in enumerate(zip(n_controls, coefs)):
    ax.text(x, y + 0.002, f'{y:.3f}', ha='center', va='bottom', fontsize=8,
            fontweight='bold', color=PALETTE[0])

# Zero reference line
ax.axhline(0, color=COLORS['ref_line'], linewidth=0.8, linestyle='--', alpha=0.5)

# Baseline reference band
baseline = coefs[0]
ax.axhspan(baseline * 0.9, baseline * 1.1, alpha=0.05, color=PALETTE[3],
           label=f'基准±10% ({baseline*0.9:.3f}~{baseline*1.1:.3f})')

ax.set_xticks(n_controls)
ax.set_xticklabels(specs, fontsize=8, rotation=30, ha='right')
ax.set_ylabel('核心系数估计值', fontsize=11)
ax.set_xlabel('模型设定（逐步加入控制变量）', fontsize=11)
ax.legend(fontsize=8, frameon=False, labelspacing=0.35, handlelength=1.6, loc='best')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_coef_stability.pdf')
```

**★ 防遮挡技巧（Coefficient Stability 专用）：**
```python
# 1. 变量添加标签放在 x 轴下方：rotation=45, ha='right'
# 2. CI 带用淡色填充（alpha=0.1）：不要遮挡系数线
# 3. 基准系数水平线的标签放在图右边缘：不要放在数据区域
# 4. 系数点之间连线用淡（alpha≤0.4）：不要遮挡 CI 带
```

---

## 20. Variance Decomposition (Stacked Area with Smart Scaling)

**Scene**: VAR/VECM variance decomposition. When one component dominates (>80%), uses dual-panel layout — top panel shows all components, bottom panel zooms into minor components. Solves the "one color fills everything" problem.

```python
import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

# === Example data ===
periods = np.arange(1, 21)
# Variance decomposition (rows = components, cols = periods)
own = np.array([100, 95, 90, 87, 85, 83, 82, 81, 80, 79, 78, 77, 76, 75, 74, 73, 72, 71, 70, 69])
var2 = np.array([0, 3, 5, 7, 8, 9, 9.5, 10, 10.5, 11, 11.5, 12, 12.5, 13, 13.5, 14, 14.5, 15, 15.5, 16])
var3 = 100 - own - var2
names = ['自身冲击', 'GPR指数', 'GSCPI']

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 7), height_ratios=[1, 1], sharex=True)

# Top panel: full stacked area
ax1.stackplot(periods, own, var2, var3,
              colors=[_lighten(PALETTE[0], 0.3), _lighten(PALETTE[1], 0.3), _lighten(PALETTE[2], 0.3)],
              alpha=0.8, labels=names)
ax1.plot(periods, own, color=PALETTE[0], linewidth=1.5)
ax1.plot(periods, own + var2, color=PALETTE[1], linewidth=1.5)
ax1.set_ylabel('方差贡献比例 (%)', fontsize=10)
ax1.set_ylim(0, 100)
ax1.legend(fontsize=8, frameon=False, labelspacing=0.35, handlelength=1.6, loc='center right')
ax1.text(-0.05, 1.06, '(a) 完整方差分解', transform=ax1.transAxes, fontsize=10, fontweight='bold')
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

# Bottom panel: zoom into minor components only
ax2.fill_between(periods, 0, var2, alpha=0.4, color=PALETTE[1], label=names[1])
ax2.fill_between(periods, var2, var2 + var3, alpha=0.4, color=PALETTE[2], label=names[2])
ax2.plot(periods, var2, color=PALETTE[1], linewidth=2, marker='o', markersize=4,
         markeredgecolor='white', markeredgewidth=0.8)
ax2.plot(periods, var2 + var3, color=PALETTE[2], linewidth=2, marker='s', markersize=4,
         markeredgecolor='white', markeredgewidth=0.8)

# Value labels at end
ax2.text(periods[-1] + 0.3, var2[-1], f'{var2[-1]:.1f}%', va='center', fontsize=8,
         color=PALETTE[1], fontweight='bold')
ax2.text(periods[-1] + 0.3, var2[-1] + var3[-1], f'{var3[-1]:.1f}%', va='center', fontsize=8,
         color=PALETTE[2], fontweight='bold')

ax2.set_ylabel('方差贡献比例 (%)', fontsize=10)
ax2.set_xlabel('预测期', fontsize=11)
ax2.legend(fontsize=8, frameon=False, labelspacing=0.35, handlelength=1.6, loc='upper left')
ax2.text(-0.05, 1.06, '(b) 非自身冲击成分（放大）', transform=ax2.transAxes, fontsize=10, fontweight='bold')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

fig.tight_layout()
save_fig(fig, 'figures/fig_variance_decomp.pdf')
```

---

## 21. Impulse Response Function (IRF with Gradient CI + Multi-Panel)

**Scene**: VAR/VECM impulse response functions. Multi-panel layout showing response of each variable to a one-unit shock. Gradient CI bands, zero reference line, significance shading.

```python
import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

# === Example data (replace with actual IRF results) ===
periods = np.arange(0, 16)
responses = {
    '数字经济 → 数字经济': {'irf': [1.0, 0.8, 0.5, 0.3, 0.15, 0.08, 0.04, 0.02, 0.01, 0.005, 0, 0, 0, 0, 0, 0],
                          'lower': None, 'upper': None},
    '算力基础设施 → 数字经济': {'irf': [0, 0.15, 0.25, 0.30, 0.28, 0.22, 0.16, 0.11, 0.07, 0.04, 0.02, 0.01, 0, 0, 0, 0],
                              'lower': None, 'upper': None},
    '数字经济 → 算力基础设施': {'irf': [0, 0.05, 0.12, 0.18, 0.20, 0.18, 0.14, 0.10, 0.07, 0.04, 0.02, 0.01, 0, 0, 0, 0],
                              'lower': None, 'upper': None},
    '算力基础设施 → 算力基础设施': {'irf': [1.0, 0.7, 0.4, 0.2, 0.1, 0.05, 0.02, 0.01, 0, 0, 0, 0, 0, 0, 0, 0],
                                  'lower': None, 'upper': None},
}

# Generate CI bands
for key in responses:
    irf = np.array(responses[key]['irf'])
    noise = np.abs(irf) * 0.3 + 0.02
    responses[key]['lower'] = irf - noise
    responses[key]['upper'] = irf + noise

n_panels = len(responses)
ncols = 2
nrows = (n_panels + 1) // 2
fig, axes = plt.subplots(nrows, ncols, figsize=(10, 4 * nrows), sharex=True)
axes = axes.flatten()

for idx, (title, data) in enumerate(responses.items()):
    ax = axes[idx]
    irf = np.array(data['irf'])
    lower = np.array(data['lower'])
    upper = np.array(data['upper'])

    # Gradient CI bands (3 layers)
    for layer, alpha in enumerate([0.08, 0.15, 0.25]):
        shrink = (1 - layer * 0.3)
        mid = irf
        ax.fill_between(periods, mid - (mid - lower) * shrink, mid + (upper - mid) * shrink,
                        alpha=alpha, color=PALETTE[idx % len(PALETTE)])

    # IRF line
    ax.plot(periods, irf, '-o', color=PALETTE[idx % len(PALETTE)], linewidth=2,
            markersize=4, markeredgecolor='white', markeredgewidth=0.8, zorder=5)

    # Zero reference
    ax.axhline(0, color=COLORS['ref_line'], linewidth=0.8, linestyle='--', alpha=0.5)

    # Significance shading (where CI doesn't cross zero)
    for t in range(len(periods)):
        if lower[t] > 0 or upper[t] < 0:
            ax.axvspan(t - 0.4, t + 0.4, alpha=0.04, color=PALETTE[idx % len(PALETTE)])

    ax.set_title(title, fontsize=9, fontweight='bold', loc='center', pad=3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_ylabel('响应', fontsize=9)

for idx in range(n_panels, len(axes)):
    axes[idx].set_visible(False)

axes[-2].set_xlabel('期数', fontsize=10)
axes[-1].set_xlabel('期数', fontsize=10)
fig.tight_layout()
save_fig(fig, 'figures/fig_irf.pdf')
```