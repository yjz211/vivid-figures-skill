# 数学建模竞赛 专用图表代码范例

适用于数学建模竞赛（国赛/美赛/MathorCup/统计建模等）。包含收敛曲线、灵敏度分析、Pareto 前沿、雷达图、甘特图、网络路径等竞赛高频图表。
所有范例假设已执行 `from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten; setup_style()`。

图例、标注和画布以各配方的完整源码为底稿，替换数据后再做必要的局部适配。
尺寸统一按 [figure_layout_reference.md](figure_layout_reference.md) 的“figsize 与最终显示尺寸”检查，
不套用固定画布宽度、字号下限或图例位置。`loc='best'` 也不能替代实际看图。

`save_fig` 保留现有布局，不自动移动标注、裁回轴内或调用 `tight_layout`。
注释放在轴外时需明确留出画布空间；共用色条沿用模板的 `ax=axes` 或独立 `cax`，按实图核对。

---

## 1. 收敛曲线对比图

**场景**：多算法迭代优化过程对比，展示收敛速度和最终目标值。优化类问题必备。
**要点**：本文方法用粗线+填充区域突出、其他方法用细线+低透明度、终点数值标注用 smart_labels 防重叠、收敛点箭头标注。

```python
import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()

np.random.seed(42)
iters = np.arange(0, 501, 5)
methods = {
    '遗传算法 (GA)': 100*np.exp(-0.008*iters) + 5 + np.random.normal(0,0.5,len(iters))*0.5,
    '粒子群 (PSO)': 100*np.exp(-0.012*iters) + 3 + np.random.normal(0,0.4,len(iters))*0.5,
    '模拟退火 (SA)': 100*np.exp(-0.006*iters) + 8 + np.random.normal(0,0.6,len(iters))*0.5,
    '本文算法': 100*np.exp(-0.018*iters) + 1.5 + np.random.normal(0,0.2,len(iters))*0.3,
}

fig, ax = plt.subplots(figsize=(7, 4.5))
highlight_index = min(3, len(methods) - 1)  # 重点系列的位置，与显示名称无关
ax.grid(True, linestyle='--', alpha=0.15, color=COLORS['grid']); ax.set_axisbelow(True)

_end_xs, _end_ys, _end_texts, _end_colors = [], [], [], []
for i, (name, vals) in enumerate(methods.items()):
    lw = 2.5 if i == highlight_index else 1.5
    alpha = 1.0 if i == highlight_index else 0.55
    ax.plot(iters, vals, color=PALETTE[i], linewidth=lw, label=name, alpha=alpha, zorder=3)
    _end_xs.append(iters[-1]); _end_ys.append(vals[-1])
    _end_texts.append(f'{vals[-1]:.1f}'); _end_colors.append(PALETTE[i])
# ★ 终点标注用 smart_labels 防重叠
from _utils.plot_utils import save_fig, smart_labels
smart_labels(ax, _end_xs, _end_ys, _end_texts, colors=_end_colors, fontsize=8, offset=(8, 0))

# 本文算法的下方填充区域（强调单独）
ours = list(methods.values())[highlight_index]
ax.fill_between(iters, ours, alpha=0.10, color=PALETTE[highlight_index], linewidth=0, zorder=1)

# 收敛点标注
diff = np.abs(np.diff(ours))
conv_idx = np.argmax(diff < 0.15) + 1
ax.annotate('收敛点', xy=(iters[conv_idx], ours[conv_idx]),
            xytext=(iters[conv_idx]+60, ours[conv_idx]+12),
            fontsize=10, color=COLORS['down'], fontweight='bold',
            arrowprops=dict(arrowstyle='->', color=COLORS['down'], lw=1.5), zorder=5)
ax.scatter([iters[conv_idx]], [ours[conv_idx]], color=COLORS['down'], s=50, zorder=5, edgecolors='white')

ax.set_xlabel('迭代次数', fontsize=11); ax.set_ylabel('目标函数值', fontsize=11)
# ★ 图例用 loc='best' 自适应，不要硬编码 'upper right'（避免数据在右上角时遮挡图例）
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='best')
ax.set_xlim(0, 520)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_convergence.pdf')
```

**⚠ 收敛曲线定制生成注意事项：**
```python
# 1. 终点数值标注用 smart_labels()，多条曲线终点值接近时自动推开防重叠
# 2. 收敛点标注箭头要指向曲线的拐点区域，方向朝空白处
# 3. 本文算法的填充区域 alpha 用 0.10（太深会遮挡其他曲线）
# 4. 收敛曲线的下降趋势：图例放 'upper right' 可能遮挡
#    - 最小化问题（曲线从高到低）：图例放 'upper right' 右上空
#    - 最大化问题（曲线从低到高）：图例放 'lower right' 右下空
#    - 不确定方向时用 loc='best' 让 matplotlib 自动选择
#    - 或者把图例放到图外：bbox_to_anchor=(1.02, 1), loc='upper left'
# 5. 曲线数 >4 条时，考虑本文方法用粗线 alpha=1.0 突出，其他用细线 alpha=0.55 降低视觉权重
# 6. 标注文字不要和图例重叠（标注放在曲线空白处，图例在另一侧）
```

**图例位置选择辅助函数：**
```python
# 根据数据分布选择图例位置（不要硬编码 'upper right'）
# 对于收敛曲线等场景的图表：
def smart_legend_loc(ax):
    """根据数据分布自动选择图例位置"""
    # 简单方案：直接用 matplotlib 的 best
    ax.legend(loc='best', frameon=False, edgecolor='#DDD', fontsize=9)
    # 如果 best 不够好的话可以把图例移到图外
    # ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', frameon=False, fontsize=9)
```

---

## 2. 灵敏度图（Tornado / Sensitivity）

**场景**：参数灵敏度分析，展示各参数对目标函数的正负影响幅度。优化/决策类问题必备。
**要点**：双向水平条形图、淡色填充+原色边框、按影响幅度排序、数值标签左右分列、基准线标注。

```python
import numpy as np, matplotlib.pyplot as plt
import matplotlib.colors as mc
import colorsys
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

params = ['学习率 η', '批量 B', '种群大小 N', '交叉概率 Pc', '变异概率 Pm', '初始温度 T₀']
low_impact = np.array([-12.1, -8.5, -6.4, -5.2, -3.8, -2.1])
high_impact = np.array([15.3, 7.2, 5.9, 4.8, 3.1, 1.8])

# 按影响幅度排序
total_range = high_impact - low_impact
sort_idx = np.argsort(total_range)
params = [params[i] for i in sort_idx]
low_impact, high_impact = low_impact[sort_idx], high_impact[sort_idx]
total_range = total_range[sort_idx]
max_range = total_range.max() if total_range.max() > 0 else 1

# ★ 正负方向用不同色系
color_pos = '#5B8DB8'   # 蓝色系（正向影响）
color_neg = '#D4896A'   # 橙色系（负向影响）

n = len(params)
_fig_h = max(3, n * 0.7 + 1.2)
fig, ax = plt.subplots(figsize=(8, _fig_h))
y = np.arange(n)

ax.grid(axis='x', alpha=0.12, linestyle='-', color=COLORS['grid'])
ax.set_axisbelow(True)

# ★ 交替行背景
for i in range(n):
    if i % 2 == 0:
        ax.axhspan(y[i] - 0.4, y[i] + 0.4, alpha=0.03, color=PALETTE[0], zorder=0)

# ★ 条形（淡色填充 + 原色边框，颜色深浅映射影响幅度比例）
max_abs = max(abs(low_impact).max(), abs(high_impact).max())
for i in range(n):
    intensity = total_range[i] / max_range if max_range > 0 else 0.5
    lighten_amt = 0.5 * (1 - intensity)

    if high_impact[i] > 0:
        c = _lighten(color_pos, lighten_amt)
        ax.barh(y[i], high_impact[i], height=0.52,
                color=_lighten(c, 0.3), edgecolor=c, linewidth=1.3, zorder=3)
    if low_impact[i] < 0:
        c = _lighten(color_neg, lighten_amt)
        ax.barh(y[i], low_impact[i], height=0.52,
                color=_lighten(c, 0.3), edgecolor=c, linewidth=1.3, zorder=3)

    # 连接线
    if low_impact[i] < 0 and high_impact[i] > 0:
        ax.plot([low_impact[i], high_impact[i]], [y[i], y[i]],
                color=COLORS['ref_line'], linewidth=0.5, zorder=1, alpha=0.4)

    # 数值标签
    margin = max_abs * 0.05
    if high_impact[i] > 0:
        ax.text(high_impact[i] + margin, y[i], f'+{high_impact[i]:.1f}%',
                va='center', ha='left', fontsize=8.5, fontweight='bold',
                color=_lighten(color_pos, lighten_amt * 0.5))
    if low_impact[i] < 0:
        ax.text(low_impact[i] - margin, y[i], f'{low_impact[i]:.1f}%',
                va='center', ha='right', fontsize=8.5, fontweight='bold',
                color=_lighten(color_neg, lighten_amt * 0.5))

# 基准线 + 标注
ax.axvline(0, color=COLORS['text'], linewidth=1.0, zorder=2)
ax.text(0, n - 0.1, '基准值', ha='center', va='bottom', fontsize=8,
        color=COLORS['ref_line'],
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                  edgecolor=COLORS['grid'], alpha=0.85))

# 方向标注
ax.text(max_abs * 0.6, -0.7, '参数增大 →', fontsize=8, color=color_pos,
        ha='center', fontstyle='italic', alpha=0.6)
ax.text(-max_abs * 0.6, -0.7, '← 参数减小', fontsize=8, color=color_neg,
        ha='center', fontstyle='italic', alpha=0.6)

ax.set_yticks(y); ax.set_yticklabels(params, fontsize=10)
ax.set_xlabel('目标函数变化 (%)', fontsize=11)
xlim_max = max_abs * 1.35
ax.set_xlim(-xlim_max, xlim_max)
ax.set_ylim(-1.0, n - 0.5)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_tornado.pdf')
```

**⚠ 灵敏度图定制生成注意事项：**
```python
# 1. xlim 对称留出 35% 空间（max_abs * 1.35），给数值标签留够空间
# 2. 数值标签紧贴数值条末端（max_abs * 0.05），不要用固定像素偏移
# 3. 正负值标签分别左右对齐：正值 ha='left'，负值 ha='right'
# 4. 参数名过长（>8字）时缩小字号 fontsize=8.5 或用缩写
# 5. 参数数量 >8 时自适应高度 _fig_h = max(3, n * 0.7 + 1.2)
```

---

## 3. Pareto 前沿图

**场景**：多目标优化的非支配解集展示，标注极端点、膝点解；可行域与非可行解。多目标优化问题必备。
**要点**：可行域浅色填充、Pareto 前沿粗实线、极端解用不同 marker、方向箭头+"优化方向"标识。

```python
import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()
np.random.seed(42)

# Pareto 前沿数据
t = np.linspace(0, 1, 80)
pareto_f1 = 0.8 + 4.8 * t          # 目标1：农业产量（标准化）
pareto_f2 = 4.5 - 4.0 * t**0.7     # 目标2：缺水缺口

fig, ax = plt.subplots(figsize=(7, 6))

# 可行域填充（Pareto 前沿上方）
ax.fill_between(pareto_f1, pareto_f2, 5.5, alpha=0.12, color=PALETTE[0], zorder=0)
ax.text(3.2, 3.5, '可行域', fontsize=13, color=PALETTE[0], fontweight='bold', alpha=0.5)
ax.text(1.5, 1.2, '非可行域', fontsize=11, color=COLORS['ref_line'], alpha=0.5)

# Pareto 前沿线（粗实线）
ax.plot(pareto_f1, pareto_f2, '-', color=COLORS['text'], linewidth=3, zorder=5, label='Pareto 最优前沿')

# 极端解标注 — 不同 marker + 颜色标注框
# 缺水最小极端解（左上）
ax.scatter(pareto_f1[0], pareto_f2[0], marker='s', s=150, color=COLORS['up'],
           edgecolor='white', linewidth=1.5, zorder=6)
ax.annotate('缺水最小极端解\n(min$G_t$，$Z_1$ 最小)',
            xy=(pareto_f1[0], pareto_f2[0]),
            xytext=(pareto_f1[0] + 0.3, pareto_f2[0] + 0.3),
            fontsize=8.5, color=COLORS['up'], fontweight='bold',
            arrowprops=dict(arrowstyle='->', color=COLORS['up'], lw=1.2),
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                      edgecolor=COLORS['up'], alpha=0.9))

# 均衡折中解（中间，五角星）
knee_idx = len(t) // 2 + 5
ax.scatter(pareto_f1[knee_idx], pareto_f2[knee_idx], marker='*', s=300,
           color=COLORS['highlight'], edgecolor='white', linewidth=1.5, zorder=6)
ax.annotate('均衡折中解（膝点）\n$\\omega_1 Z_1 + \\omega_2 G_t$ 最优',
            xy=(pareto_f1[knee_idx], pareto_f2[knee_idx]),
            xytext=(pareto_f1[knee_idx] + 0.5, pareto_f2[knee_idx] + 0.6),
            fontsize=8.5, color=COLORS['highlight'], fontweight='bold',
            arrowprops=dict(arrowstyle='->', color=COLORS['highlight'], lw=1.2),
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                      edgecolor=COLORS['highlight'], alpha=0.9))

# 产量最大化极端解（右下，菱形）
ax.scatter(pareto_f1[-1], pareto_f2[-1], marker='D', s=120, color=COLORS['down'],
           edgecolor='white', linewidth=1.5, zorder=6)
ax.annotate('产量最大化极端解\n(max$Z_1$，$G_t$ 较大)',
            xy=(pareto_f1[-1], pareto_f2[-1]),
            xytext=(pareto_f1[-1] - 1.5, pareto_f2[-1] - 0.5),
            fontsize=8.5, color=COLORS['down'], fontweight='bold',
            arrowprops=dict(arrowstyle='->', color=COLORS['down'], lw=1.2),
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                      edgecolor=COLORS['down'], alpha=0.9))

# 方向箭头
ax.annotate('', xy=(2.0, 0.15), xytext=(0.5, 0.15),
            arrowprops=dict(arrowstyle='->', color=COLORS['ref_line'], lw=1.2, linestyle='--'))
ax.text(1.25, 0.0, '$Z_1$ 增大方向', fontsize=8, color=COLORS['ref_line'], ha='center')
ax.annotate('', xy=(0.3, 1.8), xytext=(0.3, 0.5),
            arrowprops=dict(arrowstyle='->', color=COLORS['ref_line'], lw=1.2, linestyle='--'))
ax.text(0.15, 1.15, '$G_t$ 减小方向', fontsize=8, color=COLORS['ref_line'],
        ha='center', rotation=90)

ax.set_xlabel('农业产量 $Z_1$（标准化值）', fontsize=11)
ax.set_ylabel('缺水缺口 $G_t$（标准化值）', fontsize=11)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='best')
ax.set_xlim(0, 6.2)
ax.set_ylim(0, 5.5)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_pareto.pdf')
```

**⚠ Pareto 前沿图定制生成注意事项：**
```python
# 1. 极端解标注不要互相重叠（3 个标注分别在不同方向：左上/右上/右下）
# 2. 方向标注箭头放在图边缘空白处，不要和 Pareto 前沿线或数据重叠
# 3. 方向箭头放在图边缘空白处，不要让标注超出图表边界
# 4. 非支配解用小圆点（s=20），支配解用更小的点（s=8, alpha=0.3）
# 5. 实际查看 xytext 标注与边界和数据的关系；plot_utils 不会自动解决遮挡或裁切
```

---

## 4. 预测值 vs 实际值（上下放大 + 残差分布图）

**场景**：回归/预测模型的拟合效果展示。上方散点图为预测 vs 实际+对角线，下方为残差分布。
**要点**：45° 对角线参考线、KDE 密度等高线背景、残差直方图+正态拟合、R²/RMSE 标注框。

```python
import numpy as np, matplotlib.pyplot as plt
from scipy.stats import gaussian_kde, norm
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()
np.random.seed(42)
n = 200
actual = np.random.uniform(10, 100, n)
predicted = actual + np.random.normal(0, 5, n)
residuals = predicted - actual
r2 = 1 - np.sum(residuals**2)/np.sum((actual-actual.mean())**2)
rmse = np.sqrt(np.mean(residuals**2))

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 7), height_ratios=[3, 1], sharex=False)
# 上方：预测 vs 实际
ax1.grid(True, linestyle='--', alpha=0.15); ax1.set_axisbelow(True)
kde = gaussian_kde(np.vstack([actual, predicted]))
xg = np.linspace(5, 105, 100); yg = np.linspace(5, 105, 100)
Xg, Yg = np.meshgrid(xg, yg)
Zg = kde(np.vstack([Xg.ravel(), Yg.ravel()])).reshape(Xg.shape)
ax1.contourf(Xg, Yg, Zg, levels=8, cmap='Blues', alpha=0.2, zorder=0)
ax1.scatter(actual, predicted, s=18, alpha=0.5, color=PALETTE[0], edgecolor='white', linewidth=0.3, zorder=2)
ax1.plot([5,105],[5,105], '--', color=COLORS['down'], linewidth=1.2, label='完美拟合线', zorder=3)
ax1.fill_between([5,105],[0,100],[10,110], alpha=0.06, color=PALETTE[0])
ax1.text(0.05, 0.92, f'R² = {r2:.4f}\nRMSE = {rmse:.2f}', transform=ax1.transAxes, fontsize=10,
         verticalalignment='top', bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor=COLORS['grid'], alpha=0.9))
ax1.set_xlabel('实际值', fontsize=11); ax1.set_ylabel('预测值', fontsize=11)
ax1.spines['top'].set_visible(False); ax1.spines['right'].set_visible(False)
ax1.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9)
# 下方：残差分布
ax2.grid(True, linestyle='--', alpha=0.15); ax2.set_axisbelow(True)
ax2.hist(residuals, bins=25, density=True, color=_lighten(PALETTE[0], 0.4), alpha=0.5, edgecolor=PALETTE[0], linewidth=0.8)
xr = np.linspace(residuals.min()-2, residuals.max()+2, 100)
ax2.plot(xr, norm.pdf(xr, residuals.mean(), residuals.std()), color=PALETTE[1], linewidth=2, label='正态拟合')
ax2.axvline(x=0, color=COLORS['ref_line'], linewidth=0.8, linestyle='--')
ax2.set_xlabel('残差', fontsize=11); ax2.set_ylabel('密度', fontsize=11)
ax2.spines['top'].set_visible(False); ax2.spines['right'].set_visible(False)
ax2.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9)
fig.tight_layout()
save_fig(fig, 'figures/fig_pred_vs_actual.pdf')
```

---

## 5. 雷达图（多方案对比 + 渐变背景 + 多维度覆盖 + 顶部数值标注）

**场景**：多方案在多维度指标上的综合对比，如成本/效率/可靠性/安全性等。
**要点**：渐变同心圆背景、本文方法用粗线+填充突出、数值标注在顶部、图例在右上角外侧。

```python
import numpy as np, matplotlib.pyplot as plt, matplotlib.colors as mc
import colorsys
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

categories = ['成本', '效率', '可靠性', '安全性', '灵活性', '可扩展性']
N = len(categories)
angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist() + [0]

methods = {
    '本文方法': [0.95, 0.88, 0.92, 0.90, 0.85, 0.91],
    '方案A':   [0.80, 0.82, 0.78, 0.85, 0.70, 0.75],
    '方案B':   [0.85, 0.75, 0.88, 0.72, 0.90, 0.68],
    '方案C':   [0.70, 0.90, 0.65, 0.80, 0.60, 0.82],
}

fig, ax = plt.subplots(figsize=(6.5, 6.5), subplot_kw=dict(polar=True))
highlight_index = 0  # 重点系列的位置，与显示名称无关
ax.set_facecolor('white')
ax.set_ylim(0, 1.12)  # 留出标注空间

# ★ 渐变环色背景 + 自定义同心圆网格
ring_levels = [0.2, 0.4, 0.6, 0.8, 1.0]
theta_fill = np.linspace(0, 2*np.pi, 100)
for k, r in enumerate(ring_levels):
    r_prev = ring_levels[k-1] if k > 0 else 0
    if k % 2 == 0:
        ax.fill_between(theta_fill, r_prev, r, alpha=0.025, color=PALETTE[0], zorder=0)
    ax.plot(theta_fill, [r]*len(theta_fill), color='#E5E5E5', linewidth=0.5, zorder=1)
ax.set_yticks(ring_levels)
ax.set_yticklabels(['0.2','0.4','0.6','0.8','1.0'], fontsize=7, color='#C0C0C0')

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=10.5, color=COLORS['text'])
ax.tick_params(axis='x', pad=18)

for i, (name, vals) in enumerate(methods.items()):
    values = vals + [vals[0]]
    is_ours = i == highlight_index
    lw = 2.5 if is_ours else 1.2
    alpha_line = 1.0 if is_ours else 0.5
    alpha_fill = 0.15 if is_ours else 0.04
    ax.plot(angles, values, color=PALETTE[i], linewidth=lw, label=name, alpha=alpha_line, zorder=3)
    ax.fill(angles, values, color=PALETTE[i], alpha=alpha_fill, zorder=1)
    # 本文方法顶部数值标注
    if is_ours:
        for j, (a, v) in enumerate(zip(angles[:-1], vals)):
            r_label = v + 0.08
            ax.text(a, r_label, f'{v:.2f}', ha='center', va='bottom', fontsize=7.5,
                    fontweight='bold', color=PALETTE[i],
                    bbox=dict(facecolor='white', alpha=0.9, edgecolor='none', pad=1))

ax.legend(loc='best', bbox_to_anchor=(1.28, 1.06),
          frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, facecolor='white')
fig.tight_layout()
save_fig(fig, 'figures/fig_radar.pdf')
```

**⚠ 雷达图定制生成注意事项：**
```python
# 1. ylim 留出余量：ax.set_ylim(0, 1.12) 而不是 (0, 1.0)，给标注留空间
# 2. 标注位置方向一致：r_label = v + 0.08，不要根据数据调整
# 3. 标注加白底 bbox：bbox=dict(facecolor='white', alpha=0.9)，防止和网格线混淆
# 4. 维度数 >6 时减小字号 fontsize=9，维度名过长时用缩写
# 5. 方案数 >4 时只给本文方法加数值标注，其他方案只画线
```

---

## 6. 3D 曲面图（目标函数地形）

**场景**：展示目标函数在二维参数空间上的地形，用于说明优化问题的复杂性（多峰、鞍点等）。
**要点**：曲面+等高线投影、最优点标注、视角选择、色条。

```python
import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()

x = np.linspace(-3, 3, 100); y = np.linspace(-3, 3, 100)
X, Y = np.meshgrid(x, y)
Z = np.sin(X)*np.cos(Y) + 0.5*np.sin(2*X)*np.cos(2*Y) + np.random.normal(0, 0.02, X.shape)

fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection='3d')
surf = ax.plot_surface(X, Y, Z, cmap='coolwarm', alpha=0.85, edgecolor='none', antialiased=True)
ax.contour(X, Y, Z, zdir='z', offset=Z.min()-0.3, cmap='coolwarm', alpha=0.3, levels=15)

# 最优点标注
min_idx = np.unravel_index(Z.argmin(), Z.shape)
ax.scatter([X[min_idx]], [Y[min_idx]], [Z[min_idx]], color=COLORS['down'], s=80,
           edgecolor='white', linewidth=1.5, zorder=10, label=f'最优点 ({X[min_idx]:.1f}, {Y[min_idx]:.1f})')

ax.set_xlabel('参数 $x_1$', fontsize=10, labelpad=6)
ax.set_ylabel('参数 $x_2$', fontsize=10, labelpad=6)
ax.set_zlabel('目标函数值', fontsize=10, labelpad=6)
ax.view_init(elev=30, azim=135); ax.tick_params(labelsize=8)
ax.legend(fontsize=9, loc='best')
fig.colorbar(surf, shrink=0.45, aspect=15, pad=0.12)
fig.tight_layout()
save_fig(fig, 'figures/fig_3d_surface.pdf')
```

---

## 7. 中国省份地图（Choropleth Map）

**场景**：省级指标空间分布可视化，如 GDP、同比增长指标、污染指标、人口密度等。空间分析/区域经济类的必备图。
**要点**：geopandas + 阿里云 DataV GeoJSON、YlOrRd 颜色映射、省份标注、colorbar。
**⚠ 依赖**：优先用 `geopandas`；如果不可用，自动降级为纯 matplotlib 方案（从 GeoJSON 手动解析坐标画 polygon，同样有省份轮廓）。

```python
import os, sys, shutil, json
import numpy as np, matplotlib.pyplot as plt
import matplotlib.colors as mc
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.colors import Normalize

# 初始化 _utils
os.makedirs('_utils', exist_ok=True)
for src in ['plot_utils.py', 'china_provinces.geojson']:
    for search in ['skills/shared-scripts', '../skills/shared-scripts']:
        p = os.path.join(search, src)
        if os.path.isfile(p):
            shutil.copy2(p, f'_utils/{src}'); break
sys.path.insert(0, '.')
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

# ★ 加载 GeoJSON（优先本地，否则自动下载）
GEOJSON = '_utils/china_provinces.geojson'
if not os.path.exists(GEOJSON):
    import urllib.request
    url = "https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json"
    urllib.request.urlretrieve(url, GEOJSON)

with open(GEOJSON, 'r', encoding='utf-8') as f:
    geojson_data = json.load(f)

# ★ 模拟数据（实际使用时替换为 JSON 读取）
province_values = {
    '北京市': 0.85, '天津市': 0.72, '河北省': 0.55, '山西省': 0.48,
    '内蒙古自治区': 0.52, '辽宁省': 0.58, '吉林省': 0.50, '黑龙江省': 0.47,
    '上海市': 0.88, '江苏省': 0.78, '浙江省': 0.82, '安徽省': 0.56,
    '福建省': 0.68, '江西省': 0.51, '山东省': 0.65, '河南省': 0.54,
    '湖北省': 0.60, '湖南省': 0.57, '广东省': 0.75, '广西壮族自治区': 0.45,
    '海南省': 0.53, '重庆市': 0.62, '四川省': 0.58, '贵州省': 0.40,
    '云南省': 0.42, '西藏自治区': 0.35, '陕西省': 0.55, '甘肃省': 0.38,
    '青海省': 0.36, '宁夏回族自治区': 0.43, '新疆维吾尔自治区': 0.44,
    '台湾省': 0.70, '香港特别行政区': 0.80, '澳门特别行政区': 0.78,
}

# 检测 geopandas 是否可用
try:
    import geopandas as gpd
    HAS_GPD = True
except ImportError:
    HAS_GPD = False

fig, ax = plt.subplots(figsize=(10, 8))
vmin, vmax = 0.3, 0.9
cmap = plt.cm.YlOrRd
norm = Normalize(vmin=vmin, vmax=vmax)

if HAS_GPD:
    # ===== 方案 A：geopandas（推荐） =====
    gdf = gpd.read_file(GEOJSON)
    gdf['value'] = gdf['name'].map(province_values)
    gdf_valid = gdf[gdf['value'].notna()]
    gdf_no_data = gdf[gdf['value'].isna()]
    gdf_valid.plot(column='value', cmap='YlOrRd', linewidth=0.5,
                   edgecolor='white', ax=ax, legend=False, vmin=vmin, vmax=vmax)
    if len(gdf_no_data) > 0:
        gdf_no_data.plot(color='#F0F0F0', edgecolor='white', linewidth=0.5, ax=ax)
    # 省份标注
    major = ['北京市','上海市','广东省','浙江省','四川省','新疆维吾尔自治区',
             '西藏自治区','黑龙江省','云南省','湖北省']
    for _, row in gdf_valid.iterrows():
        if row['name'] in major:
            c = row.geometry.centroid
            v = row['value']
            short = row['name'][:2]
            ax.text(c.x, c.y, f'{short}\n{v:.2f}', ha='center', va='center',
                    fontsize=7, fontweight='bold', color='#333333',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                              edgecolor='#999999', linewidth=0.6, alpha=0.92))
else:
    # ===== 方案 B：纯 matplotlib（不依赖 geopandas，同样有省份轮廓） =====
    def _extract_polygons(geometry):
        """从 GeoJSON geometry 提取所有 polygon 坐标环"""
        polys = []
        gtype = geometry['type']
        if gtype == 'Polygon':
            for ring in geometry['coordinates']:
                polys.append(np.array(ring))
        elif gtype == 'MultiPolygon':
            for polygon in geometry['coordinates']:
                for ring in polygon:
                    polys.append(np.array(ring))
        return polys

    for feature in geojson_data['features']:
        name = feature['properties'].get('name', '')
        val = province_values.get(name)
        polys = _extract_polygons(feature['geometry'])
        for coords in polys:
            if len(coords) < 3:
                continue
            if val is not None:
                color = cmap(norm(val))
            else:
                color = '#F0F0F0'
            patch = MplPolygon(coords[:, :2], closed=True,
                               facecolor=color, edgecolor='white',
                               linewidth=0.5, zorder=2)
            ax.add_patch(patch)

    # 省份标注（用质心近似）
    major_short = {'北京市':'北京','上海市':'上海','广东省':'广东','浙江省':'浙江',
                   '四川省':'四川','新疆维吾尔自治区':'新疆','西藏自治区':'西藏',
                   '黑龙江省':'黑龙','云南省':'云南','湖北省':'湖北'}
    for feature in geojson_data['features']:
        name = feature['properties'].get('name', '')
        if name not in major_short:
            continue
        val = province_values.get(name)
        if val is None:
            continue
        # 计算质心
        all_coords = []
        for poly in _extract_polygons(feature['geometry']):
            all_coords.extend(poly.tolist())
        if not all_coords:
            continue
        arr = np.array(all_coords)
        cx, cy = arr[:, 0].mean(), arr[:, 1].mean()
        short = major_short[name]
        ax.text(cx, cy, f'{short}\n{val:.2f}', ha='center', va='center',
                fontsize=7, fontweight='bold', color='#333333',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                          edgecolor='#999999', linewidth=0.6, alpha=0.92))
    ax.set_aspect('equal')
    ax.autoscale_view()

# Colorbar
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, shrink=0.6, pad=0.02, aspect=20)
cbar.set_label('指标值', fontsize=11)
cbar.ax.tick_params(labelsize=9)

ax.set_xlim(73, 136); ax.set_ylim(17, 54)
ax.set_axis_off()
fig.tight_layout()
save_fig(fig, 'figures/fig_china_map.pdf')
```

**⚠ 地图定制生成注意事项：**
```python
# 1. 只标注 8-12 个重要省份，不要 31 个全标（太挤会导致文字重叠）
# 2. 标注用简称（取前两个字），不需要全称："新疆维吾尔自治区"太长了
# 3. 标注加白底 bbox（alpha=0.5-0.7），防止和底色混在一起
# 4. 方案 B（纯 matplotlib）不需要 geopandas，直接从 GeoJSON 解析坐标画 Polygon
# 5. 色条标签用中文（如 '指标值'），不要用英文
# 6. ⛔ 不要用散点代替地图！即使没有 geopandas，也要用方案 B 画省份轮廓
```

---

## 8. 残差诊断四合一图

**场景**：回归模型的残差诊断，包含残差散点、Q-Q 图、残差直方图、残差自相关。
**要点**：2×2 子图布局、参考线、置信区间带。

```python
import numpy as np, matplotlib.pyplot as plt
from scipy import stats
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
np.random.seed(42)
n = 200
y_true = np.random.uniform(10, 100, n)
y_pred = y_true + np.random.normal(0, 5, n)
residuals = y_pred - y_true
std_resid = (residuals - residuals.mean()) / residuals.std()

fig, axes = plt.subplots(2, 2, figsize=(5.0, 4.9))   # 示例尺寸；保留模板比例，按实际显示尺寸检查字号与布局
# (1) 残差 vs 拟合值
ax = axes[0, 0]
ax.scatter(y_pred, std_resid, s=15, alpha=0.5, color=PALETTE[0], edgecolor='white', linewidth=0.3)
ax.axhline(0, color=COLORS['ref_line'], linewidth=0.8, linestyle='--')
ax.axhline(2, color=COLORS['down'], linewidth=0.5, linestyle=':', alpha=0.5)
ax.axhline(-2, color=COLORS['down'], linewidth=0.5, linestyle=':', alpha=0.5)
ax.set_xlabel('拟合值', fontsize=10); ax.set_ylabel('标准化残差', fontsize=10)
ax.set_title('残差 vs 拟合值', fontsize=11)
# (2) Q-Q 图
ax = axes[0, 1]
(osm, osr), (slope, intercept, r) = stats.probplot(std_resid, dist='norm')
ax.scatter(osm, osr, s=15, alpha=0.5, color=PALETTE[1], edgecolor='white', linewidth=0.3)
ax.plot(osm, slope*np.array(osm)+intercept, '--', color=COLORS['down'], linewidth=1.2)
ax.set_xlabel('理论分位数', fontsize=10); ax.set_ylabel('样本分位数', fontsize=10)
ax.set_title('Q-Q 图', fontsize=11)
# (3) 残差直方图
ax = axes[1, 0]
ax.hist(std_resid, bins=25, density=True, color=PALETTE[0], alpha=0.4, edgecolor=PALETTE[0], linewidth=0.8)
xr = np.linspace(-4, 4, 100)
ax.plot(xr, stats.norm.pdf(xr), color=PALETTE[1], linewidth=2, label='正态分布')
ax.set_xlabel('标准化残差', fontsize=10); ax.set_ylabel('密度', fontsize=10)
ax.set_title('残差分布', fontsize=11); ax.legend(fontsize=8)
# (4) 残差自相关
ax = axes[1, 1]
lags = range(1, min(30, n//5))
acf = [np.corrcoef(std_resid[:-l], std_resid[l:])[0,1] for l in lags]
ax.bar(list(lags), acf, color=PALETTE[2], alpha=0.6, edgecolor=PALETTE[2], linewidth=0.8)
ci = 1.96 / np.sqrt(n)
ax.axhline(ci, color=COLORS['down'], linewidth=0.5, linestyle='--', alpha=0.5)
ax.axhline(-ci, color=COLORS['down'], linewidth=0.5, linestyle='--', alpha=0.5)
ax.axhline(0, color=COLORS['ref_line'], linewidth=0.5)
ax.set_xlabel('滞后阶数', fontsize=10); ax.set_ylabel('自相关系数', fontsize=10)
ax.set_title('残差自相关', fontsize=11)
for a in axes.flat:
    a.spines['top'].set_visible(False); a.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_residual_diag.pdf')
```

---

## 9. 特征重要性排序图（渐变柱状图）

**场景**：机器学习模型的特征重要性排序展示，如随机森林、XGBoost 的 feature importance。
**要点**：水平柱状图、按重要性降序排列、渐变色映射重要性、数值标签右对齐。

```python
import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

features = ['人均GDP', '城镇化率', '教育支出', '医疗投入', '交通密度',
            '产业结构', '人口密度', '绿化覆盖', '科技投入', '能源消耗']
importance = np.array([0.182, 0.156, 0.134, 0.112, 0.098, 0.087, 0.076, 0.065, 0.054, 0.036])
sort_idx = np.argsort(importance)
features = [features[i] for i in sort_idx]
importance = importance[sort_idx]

n = len(features)
fig, ax = plt.subplots(figsize=(7, max(4, n*0.45)))
y = np.arange(n)
max_val = importance.max()

for i in range(n):
    ratio = importance[i] / max_val
    c = _lighten(PALETTE[0], 0.5 * (1 - ratio))
    ax.barh(y[i], importance[i], height=0.6,
            color=_lighten(c, 0.3), edgecolor=c, linewidth=1.2, zorder=3)
    ax.text(importance[i] + max_val*0.02, y[i], f'{importance[i]:.3f}',
            va='center', ha='left', fontsize=9, fontweight='bold', color=c)

ax.set_yticks(y); ax.set_yticklabels(features, fontsize=10)
ax.set_xlabel('特征重要性', fontsize=11)
ax.set_xlim(0, max_val * 1.2)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
ax.grid(axis='x', alpha=0.12, linestyle='--')
fig.tight_layout()
save_fig(fig, 'figures/fig_feature_importance.pdf')
```

**⚠ 特征重要性图定制生成注意事项：**
```python
# 1. 数值标签紧贴条形右端（x=val+margin, ha='left'）
# 2. xlim 右侧留 20% 空间给数值标签
# 3. 特征名如果过长（>6 字），用 fontsize=8.5 或缩写
# 4. 特征数 >15 时自适应高度 _fig_h = max(4, n * 0.45)
```

---

## 10. 混淆矩阵热力图

**场景**：分类模型的混淆矩阵可视化，展示各类别的预测准确率。
**要点**：热力图+数值标注、颜色深浅自适应文字颜色、归一化百分比。

```python
import numpy as np, matplotlib.pyplot as plt; from _utils.palette_maps import palette_cmap, palette_stops, contrast_text
import seaborn as sns
from _utils.plot_utils import setup_style, save_fig, PALETTE
setup_style()

classes = ['类别A', '类别B', '类别C', '类别D']
cm = np.array([[85, 5, 7, 3], [4, 90, 3, 3], [6, 4, 82, 8], [2, 3, 5, 90]])
cm_norm = cm / cm.sum(axis=1, keepdims=True) * 100

fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(cm_norm, annot=True, fmt='.1f', cmap=palette_cmap('sequential'), xticklabels=classes,
            yticklabels=classes, linewidths=0.5, linecolor='white',
            cbar_kws={'label': '预测准确率 (%)'}, ax=ax)
ax.set_xlabel('预测类别', fontsize=11); ax.set_ylabel('真实类别', fontsize=11)
ax.set_xticklabels(classes, fontsize=10); ax.set_yticklabels(classes, fontsize=10, rotation=0)
[t.set_color(contrast_text(ax.collections[0].cmap(ax.collections[0].norm(float(t.get_text()))))) for t in ax.texts]; fig.tight_layout()
save_fig(fig, 'figures/fig_confusion_matrix.pdf')
```

**⚠ 混淆矩阵定制生成注意事项：**
```python
# 1. 数值标注颜色自适应底色深浅：深色格子用白色文字，浅色格子用深色文字
#    color = 'white' if val > threshold else COLORS['text']（threshold 取 colormap 中间值）
# 2. 类别名过长时：rotation=45, ha='right'（x 轴），fontsize=8
# 3. 类别数 >6 时减小字号，>10 时考虑只标注对角线数值
```

---

## 11. ROC 曲线 + AUC 对比

**场景**：多分类模型的 ROC 曲线对比，展示各模型的判别能力。
**要点**：多条 ROC 曲线、对角线参考线、AUC 值在图例中标注、最优模型用粗线突出。

```python
import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
np.random.seed(42)

models = {
    '本文模型 (AUC=0.952)': (0.952, 2.5),
    '随机森林 (AUC=0.921)': (0.921, 1.5),
    'SVM (AUC=0.887)': (0.887, 1.5),
    '逻辑回归 (AUC=0.845)': (0.845, 1.5),
}

fig, ax = plt.subplots(figsize=(6, 5.5))
highlight_index = 0  # 重点系列的位置，与显示名称无关
ax.grid(True, linestyle='--', alpha=0.15); ax.set_axisbelow(True)
ax.plot([0,1],[0,1], '--', color=COLORS['ref_line'], linewidth=0.8, label='随机猜测')

for i, (name, (auc, lw)) in enumerate(models.items()):
    fpr = np.sort(np.concatenate([[0], np.random.beta(1, auc*10, 50), [1]]))
    tpr = np.sort(np.concatenate([[0], np.random.beta(auc*10, 1, 50), [1]]))
    alpha = 1.0 if i == highlight_index else 0.6
    ax.plot(fpr, tpr, color=PALETTE[i], linewidth=lw, label=name, alpha=alpha, zorder=3)

ax.set_xlabel('假阳性率 (FPR)', fontsize=11); ax.set_ylabel('真阳性率 (TPR)', fontsize=11)
ax.set_xlim(-0.02, 1.02); ax.set_ylim(-0.02, 1.02)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='lower right')
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_roc.pdf')
```

**⚠ ROC 曲线定制生成注意事项：**
```python
# 1. 终点数值标注不要和曲线重叠，xytext 偏移到曲线下方空白处
# 2. 多条 ROC 曲线接近时，本文模型用粗线（lw=2.5），其他用细线（lw=1.5, alpha=0.6）
# 3. 图例放 lower right（ROC 曲线从左下到右上，右下角通常空）
```

---

## 12. 相关性矩阵图（下三角 + 数值标注）

**场景**：变量间相关性分析，展示 Pearson/Spearman 相关系数矩阵。
**要点**：只显示下三角、数值标注、颜色映射 -1 到 1、对角线标注变量名。

```python
import numpy as np, matplotlib.pyplot as plt; from _utils.palette_maps import palette_cmap, palette_stops, contrast_text
import seaborn as sns
from _utils.plot_utils import setup_style, save_fig, PALETTE
setup_style()

np.random.seed(42)
n_vars = 6
var_names = ['人均GDP', '城镇化率', '教育支出', '医疗投入', '交通密度', '产业结构']
data = np.random.randn(100, n_vars)
data[:, 1] = data[:, 0] * 0.8 + np.random.randn(100) * 0.3
data[:, 2] = data[:, 0] * 0.5 + np.random.randn(100) * 0.5
corr = np.corrcoef(data.T)
mask = np.triu(np.ones_like(corr, dtype=bool), k=1)

fig, ax = plt.subplots(figsize=(7, 6))
sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap=palette_cmap('diverging'), center=0,
            vmin=-1, vmax=1, xticklabels=var_names, yticklabels=var_names,
            linewidths=0.5, linecolor='white', square=True,
            cbar_kws={'shrink': 0.8, 'label': '相关系数'}, ax=ax)
ax.set_xticklabels(var_names, fontsize=9, rotation=45, ha='right')
ax.set_yticklabels(var_names, fontsize=9, rotation=0)
[t.set_color(contrast_text(ax.collections[0].cmap(ax.collections[0].norm(float(t.get_text()))))) for t in ax.texts]; fig.tight_layout()
save_fig(fig, 'figures/fig_correlation.pdf')
```

---

## 13. 重心迁移轨迹图

**场景**：时空分析中展示某指标重心随时间的迁移轨迹，如经济重心、人口重心。
**要点**：轨迹线+时间标注、起止点不同标记、KDE 热力背景、方向箭头。

```python
import numpy as np, matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
np.random.seed(42)

years = np.arange(2010, 2024)
cx = np.cumsum(np.random.normal(0.1, 0.3, len(years))) + 116.4
cy = np.cumsum(np.random.normal(-0.05, 0.2, len(years))) + 39.9

fig, ax = plt.subplots(figsize=(7, 6))
ax.grid(True, linestyle='--', alpha=0.15); ax.set_axisbelow(True)

# KDE 热力背景
kde = gaussian_kde(np.vstack([cx, cy]))
xg = np.linspace(cx.min()-0.5, cx.max()+0.5, 80)
yg = np.linspace(cy.min()-0.5, cy.max()+0.5, 80)
Xg, Yg = np.meshgrid(xg, yg)
Zg = kde(np.vstack([Xg.ravel(), Yg.ravel()])).reshape(Xg.shape)
ax.contourf(Xg, Yg, Zg, levels=8, cmap='Blues', alpha=0.15, zorder=0)

# 轨迹线（带箭头）
for i in range(len(years)-1):
    alpha = 0.3 + 0.7 * i / (len(years)-1)
    ax.annotate('', xy=(cx[i+1], cy[i+1]), xytext=(cx[i], cy[i]),
                arrowprops=dict(arrowstyle='->', color=PALETTE[0], lw=1.5, alpha=alpha))

# 起止点
ax.scatter(cx[0], cy[0], s=120, color=COLORS['up'], edgecolor='white', linewidth=2, zorder=5, label=f'起点 ({years[0]})')
ax.scatter(cx[-1], cy[-1], s=120, color=COLORS['down'], edgecolor='white', linewidth=2, zorder=5, marker='*', label=f'终点 ({years[-1]})')

# 时间标注（只标注首尾和中间几个）
for i in [0, len(years)//3, 2*len(years)//3, len(years)-1]:
    ax.text(cx[i]+0.05, cy[i]+0.05, str(years[i]), fontsize=8, fontweight='bold',
            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))

ax.set_xlabel('经度 (°E)', fontsize=11); ax.set_ylabel('纬度 (°N)', fontsize=11)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='best')
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_centroid_migration.pdf')
```

**⚠ 重心迁移图定制生成注意事项：**
```python
# 1. 时间标签只标注起始和终止位置，中间轨迹点不标
# 2. 轨迹箭头用递增 alpha（0.4→1.0），不要让早期轨迹太突出
# 3. KDE 热力背景用浅色（alpha=0.1），不要让轨迹被遮挡
```

---

## 14. 等高线图（双变量参数搜索）

**场景**：展示两个参数对目标函数的联合影响，用于参数搜索可视化。
**要点**：填充等高线+等高线标签、最优点标注、参数搜索路径。

```python
import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()

x = np.linspace(-3, 3, 100); y = np.linspace(-3, 3, 100)
X, Y = np.meshgrid(x, y)
Z = (1-X)**2 + 100*(Y-X**2)**2  # Rosenbrock 函数
Z = np.log10(Z + 1)

fig, ax = plt.subplots(figsize=(7, 6))
cf = ax.contourf(X, Y, Z, levels=20, cmap='YlOrRd', alpha=0.8)
cs = ax.contour(X, Y, Z, levels=10, colors='white', linewidths=0.5, alpha=0.6)
ax.clabel(cs, inline=True, fontsize=7, fmt='%.1f')

# 最优点
ax.scatter([1], [1], s=100, color=COLORS['down'], edgecolor='white', linewidth=2, zorder=5, marker='*')
ax.annotate('全局最优\n(1.0, 1.0)', xy=(1, 1), xytext=(1.8, 2.2),
            fontsize=9, fontweight='bold', color=COLORS['down'],
            arrowprops=dict(arrowstyle='->', color=COLORS['down'], lw=1.2),
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=COLORS['down'], alpha=0.9))

fig.colorbar(cf, ax=ax, shrink=0.8, label='$\\log_{10}(f+1)$')
ax.set_xlabel('参数 $x_1$', fontsize=11); ax.set_ylabel('参数 $x_2$', fontsize=11)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_contour.pdf')
```

---

## 15. 甘特图（彩色条形 + 原色边框 + 里程碑/排斥标记）

**场景**：项目调度/排程问题的时间线展示，如车间调度、任务分配。
**要点**：彩色条形按资源/机器分组、里程碑菱形标记、Makespan 标注线。

```python
import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

tasks = ['任务A', '任务B', '任务C', '任务D', '任务E', '任务F', '任务G', '任务H']
starts = [0, 2, 1, 5, 3, 7, 6, 9]
durations = [3, 4, 2, 3, 5, 2, 4, 3]
machines = [0, 1, 0, 2, 1, 0, 2, 1]
machine_names = ['机器M1', '机器M2', '机器M3']

n = len(tasks)
_fig_h = max(5, n * 0.35 + 1)
fig, ax = plt.subplots(figsize=(10, _fig_h))
ax.grid(axis='x', alpha=0.12, linestyle='--', color=COLORS['grid']); ax.set_axisbelow(True)

for i in range(n):
    c = PALETTE[machines[i] % len(PALETTE)]
    ax.barh(i, durations[i], left=starts[i], height=0.6,
            color=_lighten(c, 0.3), edgecolor=c, linewidth=1.3, zorder=3)
    ax.text(starts[i] + durations[i]/2, i, f'J{i+1}', ha='center', va='center',
            fontsize=8, fontweight='bold', color=c)

# Makespan 标注（放在 axes 内部顶端，避免 tight_layout 压缩导致标注飘远）
makespan = max(s+d for s, d in zip(starts, durations))
ax.axvline(makespan, color=COLORS['down'], linewidth=1.5, linestyle='--', zorder=4)
# ⛔ 不要用 y=1.02 + transform=ax.get_xaxis_transform()（会被 tight_layout 压缩导致标注飘远）
# 改用 axes 内部坐标：放在第一个任务条的上方
ax.text(makespan, -0.8, f'Makespan={makespan}h',
        ha='center', va='center', fontsize=9, fontweight='bold', color=COLORS['down'],
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=COLORS['down'], alpha=0.9))

# 图例
legend_elements = [plt.Rectangle((0,0), 1, 1, facecolor=_lighten(PALETTE[j], 0.3), edgecolor=PALETTE[j], linewidth=1.3)
                   for j, name in enumerate(machine_names)]
ax.legend(handles=legend_elements, labels=machine_names, frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8, ncol=len(machine_names), loc='best')
ax.set_yticks(range(n)); ax.set_yticklabels(tasks, fontsize=10)
ax.set_xlabel('时间 (h)', fontsize=11)
ax.invert_yaxis()
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_gantt.pdf')
```

**⚠ 甘特图定制生成注意事项：**
```python
# 1. 任务标签在条形内部居中（y 轴标签位置），不要放在条形外部导致重叠
# 2. 里程碑用菱形标记（marker='D'），不要用圆点（容易和任务条位置混淆）
# 3. 任务数 >15 时自适应高度 _fig_h = max(5, n_tasks * 0.35 + 1)
# 4. ⛔ Makespan 标注不要用 y=1.02 + transform=ax.get_xaxis_transform()
#    tight_layout() 会为轴外文本压缩绘图区域，导致标注"飘"在图表上方很远
#    正确做法：放在 axes 内部（如 y=-0.8，第一个任务条上方），用数据坐标
# 5. ⛔ 离群任务检测：如果某个任务的结束时间远大于其他任务（如 10 倍以上），
#    说明调度结果可能有问题。此时应该：
#    a) 先检查数据是否合理（打印最大/最小任务时间，看是否有异常值）
#    b) 如果数据确实如此（如某个任务等待时间很长），用断轴（broken axis）展示
#    c) 或者只展示主要任务区间，离群任务单独标注
#    d) 绝对不要让一个离群任务把整个图压缩到角落
# 6. 生成甘特图前先做数据摘要：
#    max_end = max(end times); p90_end = np.percentile(end times, 90)
#    if max_end > p90_end * 3: print("⚠ 离群任务检测：最大结束时间远大于 P90")
```

---

## 16. 网络路径/路线规划图（彩色边 + 原色边框节点）

**场景**：物流配送、TSP 路径、网络流等问题的路径可视化。
**要点**：节点标签+白底框、最优路径用粗线+高 zorder、边权标签只标注最优路径上的边。

```python
import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()
np.random.seed(42)

n_nodes = 10
pos = np.random.rand(n_nodes, 2) * 8
labels = [f'N{i}' for i in range(n_nodes)]

# 随机生成边
edges = []
for i in range(n_nodes):
    for j in range(i+1, n_nodes):
        if np.random.rand() < 0.3:
            w = np.sqrt(np.sum((pos[i]-pos[j])**2))
            edges.append((i, j, w))

# 最优路径（模拟）
path = [0, 3, 7, 5, 9, 2, 6, 1, 8, 4, 0]

fig, ax = plt.subplots(figsize=(8, 7))
ax.grid(True, linestyle='--', alpha=0.1); ax.set_axisbelow(True)

# 普通边（浅色）
for i, j, w in edges:
    ax.plot([pos[i,0], pos[j,0]], [pos[i,1], pos[j,1]],
            color=COLORS['grid'], linewidth=0.8, alpha=0.3, zorder=1)

# 最优路径（粗线）
for k in range(len(path)-1):
    i, j = path[k], path[k+1]
    ax.plot([pos[i,0], pos[j,0]], [pos[i,1], pos[j,1]],
            color=PALETTE[0], linewidth=3, alpha=0.8, zorder=3)
    # 边权标签
    mx, my = (pos[i,0]+pos[j,0])/2, (pos[i,1]+pos[j,1])/2
    w = np.sqrt(np.sum((pos[i]-pos[j])**2))
    ax.text(mx, my, f'{w:.1f}', fontsize=7, ha='center', va='center',
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))

# 节点
for i in range(n_nodes):
    is_depot = (i == 0)
    c = COLORS['down'] if is_depot else PALETTE[0]
    s = 200 if is_depot else 120
    marker = 's' if is_depot else 'o'
    ax.scatter(pos[i,0], pos[i,1], s=s, color=_lighten(c, 0.3), edgecolor=c,
              linewidth=1.5, zorder=5, marker=marker)
    ax.text(pos[i,0], pos[i,1]+0.3, labels[i], ha='center', va='bottom',
            fontsize=9, fontweight='bold',
            bbox=dict(facecolor='white', alpha=0.8, edgecolor=COLORS['grid'], pad=1.5))

ax.set_xlabel('坐标 X', fontsize=11); ax.set_ylabel('坐标 Y', fontsize=11)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_network_path.pdf')
```

**⚠ 网络路径图定制生成注意事项：**
```python
# 1. 节点标签加 bbox 白底，防止和边线混在一起
# 2. 最优路径用粗线（linewidth=3）+ 高 zorder，确保在普通边上层
# 3. 边权标签只标注最优路径上的边，不要每条边都标
```

---

## 17. 多步预测衰减图

**场景**：时间序列多步预测精度随预测步长的衰减趋势。
**要点**：多模型对比、置信区间带、终点数值标注、阈值参考线。

```python
import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
np.random.seed(42)

steps = np.arange(1, 13)
models = {
    '本文模型': 0.95 * np.exp(-0.08 * steps) + 0.02 * np.random.randn(len(steps)),
    'LSTM': 0.90 * np.exp(-0.10 * steps) + 0.03 * np.random.randn(len(steps)),
    'ARIMA': 0.85 * np.exp(-0.15 * steps) + 0.04 * np.random.randn(len(steps)),
}

fig, ax = plt.subplots(figsize=(7, 4.5))
highlight_index = 0  # 重点系列的位置，与显示名称无关
ax.grid(True, linestyle='--', alpha=0.15); ax.set_axisbelow(True)

for i, (name, vals) in enumerate(models.items()):
    is_ours = i == highlight_index
    lw = 2.5 if is_ours else 1.5
    alpha = 1.0 if is_ours else 0.6
    ax.plot(steps, vals, color=PALETTE[i], linewidth=lw, marker='o', markersize=5,
            markeredgecolor='white', markeredgewidth=1, label=name, alpha=alpha, zorder=3)
    if is_ours:
        std = 0.03 * np.sqrt(steps)
        ax.fill_between(steps, vals-std, vals+std, alpha=0.12, color=PALETTE[i])

# 阈值线
ax.axhline(0.5, color=COLORS['ref_line'], linewidth=0.8, linestyle='--', alpha=0.5)
ax.text(steps[-1]+0.3, 0.5, '可用阈值', fontsize=8, color=COLORS['ref_line'], va='center')

ax.set_xlabel('预测步长', fontsize=11); ax.set_ylabel('R² 分数', fontsize=11)
ax.set_xticks(steps)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='best')
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_multistep_decay.pdf')
```

**⚠ 多步预测衰减图定制生成注意事项：**
```python
# 1. 终点数值标注用 smart_labels()，多条曲线终点值接近时自动推开防重叠
# 2. 衰减率标注放在曲线末端下方，不要和曲线交叉重叠
# 3. 阈值线标签放在图右边缘：ax.text(x_max+0.3, threshold, ...)
```

---

## 18. 时空经济热力图

**场景**：展示多个区域在时间维度上的指标变化，如各省份 GDP 增长率随年份变化。
**要点**：热力图+时间轴+区域轴、颜色映射数值、关键值标注。

```python
import numpy as np, matplotlib.pyplot as plt; from _utils.palette_maps import palette_cmap, palette_stops, contrast_text
import seaborn as sns
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
np.random.seed(42)

regions = ['北京', '上海', '广东', '浙江', '江苏', '四川', '湖北', '山东']
years = [str(y) for y in range(2015, 2024)]
data = np.random.uniform(3, 12, (len(regions), len(years)))
data = np.round(data, 1)

fig, ax = plt.subplots(figsize=(9, 5))
sns.heatmap(data, annot=True, fmt='.1f', cmap=palette_cmap('sequential'),
            xticklabels=years, yticklabels=regions,
            linewidths=0.3, linecolor='white',
            cbar_kws={'label': 'GDP增长率 (%)', 'shrink': 0.8}, ax=ax)
ax.set_xlabel('年份', fontsize=11); ax.set_ylabel('地区', fontsize=11)
ax.set_yticklabels(regions, rotation=0, fontsize=9)
[t.set_color(contrast_text(ax.collections[0].cmap(ax.collections[0].norm(float(t.get_text()))))) for t in ax.texts]; fig.tight_layout()
save_fig(fig, 'figures/fig_spatiotemporal.pdf')
```

---

## 19. 3D Pareto 曲面（三目标优化）

**场景**：三目标优化的 Pareto 前沿曲面展示，比 2D Pareto 图多一个目标维度。三目标优化问题使用。
**要点**：散点+颜色映射、非支配解突出、视角旋转选择。

```python
import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
np.random.seed(42)

# 生成三目标 Pareto 前沿
n = 200
t1 = np.random.uniform(0, 1, n)
t2 = np.random.uniform(0, 1-t1, n)
f1 = t1 + 0.05*np.random.randn(n)
f2 = t2 + 0.05*np.random.randn(n)
f3 = 1 - t1 - t2 + 0.05*np.random.randn(n)
f1, f2, f3 = np.clip(f1, 0, 1), np.clip(f2, 0, 1), np.clip(f3, 0, 1)

# 非 Pareto 解
other_f1 = np.random.uniform(0.2, 1.0, 100)
other_f2 = np.random.uniform(0.2, 1.0, 100)
other_f3 = np.random.uniform(0.2, 1.0, 100)

fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection='3d')
# 非支配解
ax.scatter(other_f1, other_f2, other_f3, s=8, alpha=0.15, color=COLORS['neutral'])
# Pareto 前沿
sc = ax.scatter(f1, f2, f3, c=f3, cmap='coolwarm', s=25, alpha=0.7,
                edgecolor='white', linewidth=0.3, zorder=3)

ax.set_xlabel('目标 f₁', fontsize=10, labelpad=6)
ax.set_ylabel('目标 f₂', fontsize=10, labelpad=6)
ax.set_zlabel('目标 f₃', fontsize=10, labelpad=8)
ax.view_init(elev=25, azim=135); ax.tick_params(labelsize=8)
ax.legend(fontsize=9, loc='best')
fig.colorbar(sc, shrink=0.5, aspect=15, pad=0.1, label='f₃ 值')
fig.tight_layout()
save_fig(fig, 'figures/fig_pareto_3d.pdf')
```

---

## 20. 瀑布图（彩色渐变柱图 + 连接线 + 顶部数值标注）

**场景**：展示各因素对总量的累积贡献，如成本分解、误差分解。
**要点**：正负贡献用不同颜色、连接线、起止点标注、累积值标注。

```python
import numpy as np, matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

categories = ['初始值', '原材料', '人工', '运输', '税费', '折旧', '管理费', '利润', '最终值']
values = [100, -15, -20, -8, -12, -5, -3, 0, 0]
# 计算累积值
cumulative = [100]
for v in values[1:-1]:
    cumulative.append(cumulative[-1] + v)
cumulative.append(cumulative[-1])
values[-1] = cumulative[-1]

fig, ax = plt.subplots(figsize=(10, 5))
ax.grid(axis='y', alpha=0.12, linestyle='--'); ax.set_axisbelow(True)

bottoms = []
for i in range(len(categories)):
    if i == 0 or i == len(categories)-1:
        bottoms.append(0)
    else:
        bottoms.append(min(cumulative[i-1], cumulative[i]))

for i in range(len(categories)):
    if i == 0 or i == len(categories)-1:
        c = PALETTE[0]
        h = cumulative[i]
    elif values[i] >= 0:
        c = COLORS['up']
        h = values[i]
    else:
        c = COLORS['down']
        h = abs(values[i])

    ax.bar(i, h, bottom=bottoms[i], width=0.6,
           color=_lighten(c, 0.3), edgecolor=c, linewidth=1.3, zorder=3)

    # 数值标注
    val_y = bottoms[i] + h + 1
    sign = '+' if values[i] > 0 and i > 0 else ''
    ax.text(i, val_y, f'{sign}{values[i] if i < len(categories)-1 else cumulative[i]}',
            ha='center', va='bottom', fontsize=8.5, fontweight='bold', color=c)

    # 连接线
    if i < len(categories) - 1:
        ax.plot([i+0.3, i+0.7], [cumulative[i], cumulative[i]],
                color=COLORS['ref_line'], linewidth=0.8, linestyle='--', alpha=0.5)

ax.set_xticks(range(len(categories)))
ax.set_xticklabels(categories, fontsize=10, rotation=15, ha='right')
ax.set_ylabel('金额（万元）', fontsize=11)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_waterfall.pdf')
```

**⚠ 瀑布图定制生成注意事项：**
```python
# 1. 数值标注统一在柱形上方（va='bottom'），不要放在柱形下方（色块遮挡下方的节点）
# 2. 起止点有边框和 bbox，中间步骤无边框白底（视觉层次分明）
# 3. 连接信息在图例或图注标明：用颜色区分正向贡献和负向贡献
```

---

## 21. 气泡图 + KDE 联合分布（Jointplot 风格）

**场景**：展示两个变量的联合分布，气泡大小映射第三变量，边际分布用 KDE。
**要点**：中心散点/气泡图、上方和右方边际 KDE、颜色映射分组。

```python
import numpy as np, matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
np.random.seed(42)

n = 150
x = np.random.normal(5, 2, n)
y = 0.6*x + np.random.normal(0, 1.5, n)
z = np.random.uniform(10, 80, n)

fig = plt.figure(figsize=(7, 7))
gs = fig.add_gridspec(2, 2, width_ratios=[4, 1], height_ratios=[1, 4],
                      hspace=0.05, wspace=0.05)
ax_main = fig.add_subplot(gs[1, 0])
ax_top = fig.add_subplot(gs[0, 0], sharex=ax_main)
ax_right = fig.add_subplot(gs[1, 1], sharey=ax_main)

# 主图：气泡
sc = ax_main.scatter(x, y, s=z*3, c=z, cmap='YlOrRd', alpha=0.6,
                     edgecolor='white', linewidth=0.5)
ax_main.set_xlabel('变量 X', fontsize=11); ax_main.set_ylabel('变量 Y', fontsize=11)

# 上方 KDE
kde_x = gaussian_kde(x)
xx = np.linspace(x.min()-1, x.max()+1, 200)
ax_top.fill_between(xx, kde_x(xx), alpha=0.3, color=PALETTE[0])
ax_top.plot(xx, kde_x(xx), color=PALETTE[0], linewidth=1.5)
ax_top.set_ylabel('密度', fontsize=9)
plt.setp(ax_top.get_xticklabels(), visible=False)

# 右方 KDE
kde_y = gaussian_kde(y)
yy = np.linspace(y.min()-1, y.max()+1, 200)
ax_right.fill_betweenx(yy, kde_y(yy), alpha=0.3, color=PALETTE[1])
ax_right.plot(kde_y(yy), yy, color=PALETTE[1], linewidth=1.5)
ax_right.set_xlabel('密度', fontsize=9)
plt.setp(ax_right.get_yticklabels(), visible=False)

for a in [ax_main, ax_top, ax_right]:
    a.spines['top'].set_visible(False); a.spines['right'].set_visible(False)

fig.colorbar(sc, ax=ax_right, shrink=0.6, label='气泡大小 Z')
fig.tight_layout()
save_fig(fig, 'figures/fig_bubble_joint.pdf')
```

---

## 22. 气泡图 + KDE 叠加

**场景**：展示散点分布密度，用 KDE 等高线叠加在散点上。
**要点**：散点+KDE 等高线、颜色映射密度、边际直方图。

```python
import numpy as np, matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
np.random.seed(42)

n = 300
x = np.concatenate([np.random.normal(3, 1, n//2), np.random.normal(7, 1.5, n//2)])
y = np.concatenate([np.random.normal(5, 1.2, n//2), np.random.normal(3, 1, n//2)])

fig, ax = plt.subplots(figsize=(7, 6))
# KDE 等高线
kde = gaussian_kde(np.vstack([x, y]))
xg = np.linspace(x.min()-1, x.max()+1, 100)
yg = np.linspace(y.min()-1, y.max()+1, 100)
Xg, Yg = np.meshgrid(xg, yg)
Zg = kde(np.vstack([Xg.ravel(), Yg.ravel()])).reshape(Xg.shape)
ax.contourf(Xg, Yg, Zg, levels=10, cmap='Blues', alpha=0.3)
ax.contour(Xg, Yg, Zg, levels=6, colors=PALETTE[0], linewidths=0.8, alpha=0.5)

# 散点
ax.scatter(x, y, s=12, alpha=0.4, color=PALETTE[0], edgecolor='white', linewidth=0.3)

ax.set_xlabel('变量 X', fontsize=11); ax.set_ylabel('变量 Y', fontsize=11)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_bubble_kde.pdf')
```

---

## 23. K-means 聚类双面板图（外部轮廓 + 内部散点）

**场景**：聚类分析结果展示，左图为聚类散点+质心，右图为轮廓系数。
**要点**：不同聚类用不同颜色、质心标注、轮廓系数柱状图。

```python
import numpy as np, matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from sklearn.datasets import make_blobs
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
np.random.seed(42)

X, y_true = make_blobs(n_samples=300, centers=4, cluster_std=1.0)
from sklearn.cluster import KMeans
km = KMeans(n_clusters=4, random_state=42, n_init=10).fit(X)
labels = km.labels_
centers = km.cluster_centers_

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# 左图：聚类散点
for k in range(4):
    mask = labels == k
    ax1.scatter(X[mask, 0], X[mask, 1], s=20, alpha=0.5, color=PALETTE[k],
               edgecolor='white', linewidth=0.3, label=f'簇 {k+1}')
ax1.scatter(centers[:, 0], centers[:, 1], s=200, color=COLORS['text'], marker='X',
           edgecolor='white', linewidth=2, zorder=5, label='质心')
ax1.set_xlabel('特征维度 1', fontsize=11); ax1.set_ylabel('特征维度 2', fontsize=11)
ax1.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8, loc='best')
ax1.spines['top'].set_visible(False); ax1.spines['right'].set_visible(False)

# 右图：轮廓系数
from sklearn.metrics import silhouette_samples
sil = silhouette_samples(X, labels)
y_lower = 0
for k in range(4):
    cluster_sil = np.sort(sil[labels == k])
    y_upper = y_lower + len(cluster_sil)
    ax2.fill_betweenx(np.arange(y_lower, y_upper), 0, cluster_sil,
                       alpha=0.5, color=PALETTE[k])
    ax2.text(-0.05, y_lower + 0.5 * len(cluster_sil), f'簇{k+1}',
            fontsize=9, fontweight='bold', color=PALETTE[k])
    y_lower = y_upper + 5
avg_sil = np.mean(sil)
ax2.axvline(avg_sil, color=COLORS['down'], linewidth=1.5, linestyle='--',
           label=f'平均轮廓系数={avg_sil:.3f}')
ax2.set_xlabel('轮廓系数', fontsize=11); ax2.set_ylabel('样本索引', fontsize=11)
ax2.legend(fontsize=8, loc='best')
ax2.spines['top'].set_visible(False); ax2.spines['right'].set_visible(False)

fig.tight_layout()
save_fig(fig, 'figures/fig_kmeans_dual.pdf')
```

---

## 24. Hexbin 联合分布图（六边形分箱 + 边际直方图）

**场景**：大样本量的二维分布展示，hexbin 比散点更清晰。
**要点**：六边形分箱+颜色映射密度、边际直方图、回归线。

```python
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
np.random.seed(42)

n = 2000
x = np.random.normal(0, 2, n)
y = 0.5*x + np.random.normal(0, 1.5, n)

fig = plt.figure(figsize=(7, 7))
gs = gridspec.GridSpec(2, 2, width_ratios=[4, 1], height_ratios=[1, 4],
                       hspace=0.05, wspace=0.05)
ax_main = fig.add_subplot(gs[1, 0])
ax_top = fig.add_subplot(gs[0, 0], sharex=ax_main)
ax_right = fig.add_subplot(gs[1, 1], sharey=ax_main)

# 主图：hexbin
hb = ax_main.hexbin(x, y, gridsize=25, cmap='YlOrRd', mincnt=1, edgecolors='white', linewidths=0.3)
# 回归线
z = np.polyfit(x, y, 1)
p = np.poly1d(z)
x_line = np.linspace(x.min(), x.max(), 100)
ax_main.plot(x_line, p(x_line), '--', color=PALETTE[1], linewidth=1.8,
            label=f'$\\hat{{Y}}={z[0]:.3f}X{z[1]:+.1f}$')
ax_main.legend(loc='lower right', fontsize=9, framealpha=0.9)
ax_main.set_xlabel('X 变量', fontsize=11); ax_main.set_ylabel('Y 变量', fontsize=11)

# 上方直方图
ax_top.hist(x, bins=40, color=PALETTE[0], alpha=0.5, edgecolor='white', linewidth=0.5)
plt.setp(ax_top.get_xticklabels(), visible=False)
ax_top.set_ylabel('频数', fontsize=9)

# 右方直方图
ax_right.hist(y, bins=40, orientation='horizontal', color=PALETTE[1], alpha=0.5,
             edgecolor='white', linewidth=0.5)
plt.setp(ax_right.get_yticklabels(), visible=False)
ax_right.set_xlabel('频数', fontsize=9)

for a in [ax_main, ax_top, ax_right]:
    a.spines['top'].set_visible(False); a.spines['right'].set_visible(False)

fig.colorbar(hb, ax=ax_right, shrink=0.6, label='样本数')
fig.tight_layout()
save_fig(fig, 'figures/fig_hexbin_joint.pdf')
```

---

## 25. KDE 热力联合分布图（散点 + 热力图 + 边际密度）

**场景**：展示两个变量的联合密度分布，适合中等样本量。
**要点**：KDE 填充等高线+散点叠加、边际 KDE 曲线。

```python
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.stats import gaussian_kde
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
np.random.seed(42)

n = 500
x = np.concatenate([np.random.normal(2, 1, n//2), np.random.normal(6, 1.5, n//2)])
y = np.concatenate([np.random.normal(4, 1, n//2), np.random.normal(7, 1.2, n//2)])

fig = plt.figure(figsize=(7, 7))
gs = gridspec.GridSpec(2, 2, width_ratios=[4, 1], height_ratios=[1, 4],
                       hspace=0.05, wspace=0.05)
ax_main = fig.add_subplot(gs[1, 0])
ax_top = fig.add_subplot(gs[0, 0], sharex=ax_main)
ax_right = fig.add_subplot(gs[1, 1], sharey=ax_main)

# KDE 热力
kde = gaussian_kde(np.vstack([x, y]))
xg = np.linspace(x.min()-1, x.max()+1, 100)
yg = np.linspace(y.min()-1, y.max()+1, 100)
Xg, Yg = np.meshgrid(xg, yg)
Zg = kde(np.vstack([Xg.ravel(), Yg.ravel()])).reshape(Xg.shape)
ax_main.contourf(Xg, Yg, Zg, levels=12, cmap='Blues', alpha=0.5)
ax_main.scatter(x, y, s=8, alpha=0.3, color=PALETTE[0], edgecolor='none')

# 回归线
z = np.polyfit(x, y, 1)
p = np.poly1d(z)
x_line = np.linspace(x.min(), x.max(), 100)
se_line = np.std(y - p(x)) * np.sqrt(1/n + (x_line - x.mean())**2 / np.sum((x - x.mean())**2))
ax_main.plot(x_line, p(x_line), '--', color=PALETTE[1], linewidth=2, label='回归线')
ax_main.fill_between(x_line, p(x_line) - 1.96*se_line, p(x_line) + 1.96*se_line,
                     alpha=0.15, color=PALETTE[1])
ax_main.legend(loc='upper left', fontsize=10, framealpha=0.9)
ax_main.set_xlabel('X 变量', fontsize=11); ax_main.set_ylabel('Y 变量', fontsize=11)

# 边际 KDE
kde_x = gaussian_kde(x)
xx = np.linspace(x.min()-1, x.max()+1, 200)
ax_top.fill_between(xx, kde_x(xx), alpha=0.3, color=PALETTE[0])
ax_top.plot(xx, kde_x(xx), color=PALETTE[0], linewidth=1.5)
plt.setp(ax_top.get_xticklabels(), visible=False)

kde_y = gaussian_kde(y)
yy = np.linspace(y.min()-1, y.max()+1, 200)
ax_right.fill_betweenx(yy, kde_y(yy), alpha=0.3, color=PALETTE[1])
ax_right.plot(kde_y(yy), yy, color=PALETTE[1], linewidth=1.5)
plt.setp(ax_right.get_yticklabels(), visible=False)

for a in [ax_main, ax_top, ax_right]:
    a.spines['top'].set_visible(False); a.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_kde_joint.pdf')
```

---

## 26. 散点 + 回归 + 边际密度图（通用版）

**场景**：通用的散点+回归+边际分布组合图，适合任何双变量分析。
**要点**：中心散点+回归线+置信区间、上方和右方边际 KDE。

```python
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.stats import gaussian_kde
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
np.random.seed(42)

n = 300
x = np.random.uniform(1, 10, n)
y = 2.5*x + np.random.normal(0, 3, n)

fig = plt.figure(figsize=(7, 7))
gs = gridspec.GridSpec(2, 2, width_ratios=[4, 1], height_ratios=[1, 4],
                       hspace=0.05, wspace=0.05)
ax_main = fig.add_subplot(gs[1, 0])
ax_top = fig.add_subplot(gs[0, 0], sharex=ax_main)
ax_right = fig.add_subplot(gs[1, 1], sharey=ax_main)

ax_main.scatter(x, y, s=15, alpha=0.4, color=PALETTE[0], edgecolor='white', linewidth=0.3)
z = np.polyfit(x, y, 1); p = np.poly1d(z)
x_line = np.linspace(x.min(), x.max(), 100)
ax_main.plot(x_line, p(x_line), '--', color=PALETTE[1], linewidth=2, label=f'y={z[0]:.2f}x{z[1]:+.1f}')
ax_main.legend(loc='upper left', fontsize=9)
ax_main.set_xlabel('X 变量', fontsize=11); ax_main.set_ylabel('Y 变量', fontsize=11)

kde_x = gaussian_kde(x)
xx = np.linspace(x.min()-0.5, x.max()+0.5, 200)
ax_top.fill_between(xx, kde_x(xx), alpha=0.3, color=PALETTE[0])
ax_top.plot(xx, kde_x(xx), color=PALETTE[0], linewidth=1.5)
plt.setp(ax_top.get_xticklabels(), visible=False)

kde_y = gaussian_kde(y)
yy = np.linspace(y.min()-1, y.max()+1, 200)
ax_right.fill_betweenx(yy, kde_y(yy), alpha=0.3, color=PALETTE[1])
ax_right.plot(kde_y(yy), yy, color=PALETTE[1], linewidth=1.5)
plt.setp(ax_right.get_yticklabels(), visible=False)

for a in [ax_main, ax_top, ax_right]:
    a.spines['top'].set_visible(False); a.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_scatter_marginal.pdf')
```

---

## 27. 3D 聚类散点图（彩色分组 + 原色边框点 + 文本标注）

**场景**：高维数据降维后的 3D 聚类可视化，如 PCA/t-SNE 降维到 3D。
**要点**：不同聚类用不同颜色、质心标注、视角选择。

```python
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
np.random.seed(42)

# 生成 3D 聚类数据
centers = np.array([[2,3,4], [6,2,7], [4,7,2], [8,6,5]])
n_per = 60
X = np.vstack([c + np.random.randn(n_per, 3)*0.8 for c in centers])
labels = np.repeat(range(4), n_per)

fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection='3d')

for k in range(4):
    mask = labels == k
    ax.scatter(X[mask,0], X[mask,1], X[mask,2], s=20, alpha=0.5,
              color=PALETTE[k], edgecolor='white', linewidth=0.3, label=f'簇 {k+1}')
    ax.scatter(*centers[k], s=150, color=PALETTE[k], marker='X',
              edgecolor='white', linewidth=2, zorder=5)

ax.set_xlabel('维度 1', fontsize=11, labelpad=6)
ax.set_ylabel('维度 2', fontsize=11, labelpad=6)
ax.set_zlabel('维度 3', fontsize=11, labelpad=8)
ax.view_init(elev=20, azim=45)
ax.legend(loc='upper left', fontsize=10, framealpha=0.9)
fig.tight_layout()
save_fig(fig, 'figures/fig_3d_cluster.pdf')
```

**⚠ 3D 聚类图定制生成注意事项：**
```python
# 1. 约束标签放在约束线的端点附近，不要放在空间中间
# 2. 膝点标注的 arrowprops 用虚线，标注文字远离约束线的空白处
# 3. 等高线标签用 clabel 自动放置，不要手动排（容易和约束线重叠）
```

## 28. 可行域图（约束满足分区 + 边界 + 最优点）

**场景**：约束优化 / 参数搜索里，在**两个决策变量**的平面上画出"哪些组合可行、哪些违反约束"，
并标出可行域边界与最优解。适用：线性规划可行域、参数扫描的达标区、
碰撞/干涉判定的安全区（如"(螺距, 盘入圈数) 平面上是否碰撞"）、多约束交集区。
**要点**：可行域是**离散的可行/不可行二分区**（不是连续目标值——那是等高线 #14）。
用 `contourf` 的两档色 或 `pcolormesh` 掩膜画可行/违反两片，叠约束边界线，标最优点。
⛔ 不要把可行域画成一堆散点或条形——那读不出"区域"和"边界"。

```python
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

# ── 数据：两个决策变量网格 + 每点是否可行（真实项目从求解结果读；此处可复现演示）
# 例：x=螺距 pitch∈[0.35,0.55]m, y=盘入圈数 turns∈[1,16]，可行=不碰撞
px = np.linspace(0.35, 0.55, 120)
ty = np.linspace(1.0, 16.0, 120)
X, Y = np.meshgrid(px, ty)
# feasible[i,j]=1 表示该(pitch,turns)组合满足约束（真实项目用求解器逐点判定）
margin = (X - 0.44) * 40 - (Y - 8.0) * 0.6            # 演示用的约束裕度函数
feasible = (margin >= 0).astype(float)

fig, ax = plt.subplots(figsize=(6.6, 5.2))
# 两档填充：可行=主色浅版、违反=灰浅版（语义清晰，不用花哨渐变）
cmap2 = ListedColormap([_lighten(COLORS['down'], 0.72), _lighten(PALETTE[0], 0.55)])
ax.contourf(X, Y, feasible, levels=[-0.5, 0.5, 1.5], cmap=cmap2, zorder=2)
# 可行域边界线（margin=0 那条）
ax.contour(X, Y, margin, levels=[0], colors=[PALETTE[0]], linewidths=2.0, zorder=4)

# 关键阈值参考线（如题给的临界螺距）+ 线旁短标签（不写文字框）
p_crit = 0.44
ax.axvline(p_crit, ls='--', lw=1.4, color=PALETTE[1], zorder=5)
ax.text(p_crit + 0.003, ty.max(), f'临界螺距 {p_crit}', rotation=90, fontsize=8.4,
        ha='left', va='top', color=PALETTE[1], fontweight='bold')

# 最优点：白描边让它从填充里跳出来 + 一个短标签
opt_x, opt_y = 0.45, 11.5
ax.scatter([opt_x], [opt_y], s=150, marker='*', color=PALETTE[4], zorder=8,
           edgecolors='white', linewidths=1.2)
ax.text(opt_x + 0.004, opt_y, ' 最优', fontsize=8.6, va='center',
        color=PALETTE[4], fontweight='bold')

# 可行/违反用图例说明（不在图内写整句），图例去框
legend_items = [
    Line2D([], [], marker='s', ls='', markersize=10, markerfacecolor=_lighten(PALETTE[0], 0.55),
           markeredgecolor=PALETTE[0], label='可行域'),
    Line2D([], [], marker='s', ls='', markersize=10, markerfacecolor=_lighten(COLORS['down'], 0.72),
           markeredgecolor=COLORS['down'], label='违反约束'),
    Line2D([], [], color=PALETTE[0], lw=2.0, label='可行边界'),
]
ax.legend(handles=legend_items, frameon=False, fontsize=8.6, loc='lower left',
          handlelength=1.6, labelspacing=0.3, borderpad=0.25)

ax.set_xlabel('螺距 $p$ (m)', fontsize=10.4)
ax.set_ylabel('盘入圈数', fontsize=10.4)
ax.set_xticks([0.35, 0.40, 0.44, 0.50, 0.55])        # 临界值 0.44 进刻度
ax.set_yticks([1, 4, 8, 12, 16])
ax.tick_params(labelsize=9.0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.set_title('(a) 参数平面可行域与最优解', fontsize=11.4, fontweight='bold', loc='left', pad=6)

fig.subplots_adjust(left=0.10, right=0.97, bottom=0.10, top=0.93)
save_fig(fig, 'figures/fig_feasible_region.pdf')
```

**注意事项**：
```python
# 1. ⛔ 可行域是"分区"不是"目标值"：用 contourf 两档色 或 pcolormesh 掩膜画可行/违反两片，
#    不要用连续 colormap（那读者分不清哪片可行）；更不要退化成散点/条形（读不出区域和边界）。
# 2. 结论（可行域面积占比、最优解坐标与目标值、临界约束是哪条）写进 LaTeX \caption{}，
#    图内只留：边界线 + 阈值线旁短标签 + 最优点一个短标签。不要在图内写多行结论框。
# 3. 边界线用 contour(margin, levels=[0]) 从裕度函数精确画，不要手描一条近似线。
# 4. 多条约束时：每条约束画一条边界线（不同线型），可行域是它们的交集；
#    约束多于 4 条时考虑只画"起决定作用"的活跃约束，其余进 caption 说明。
# 5. 真实项目的 feasible 矩阵必须来自求解器逐点判定（碰撞检测/约束校验），不要用演示裕度函数编造。
```

## 29. 离散状态栅格图（仿真逐帧/逐时隙状态热图）

**场景**：把离散事件仿真、排队/调度、重传轮次、设备状态机的**逐帧逐单元状态**铺成栅格，
一眼看出"什么时候谁在什么状态"。适用：CSMA/CA 时隙占用、机器加工甘特栅格、
病床/车位占用、重传轮次分布、元胞自动机时空快照。
**要点**：状态是**离散类别**（不是连续值），所以必须用 `ListedColormap` + `BoundaryNorm`
配离散色带，`colorbar` 的刻度标签写成人话（"首传成功/1轮重传/..."）；格子间加白描边分隔。
⛔ 不要用连续 colormap（viridis 之类）画离散状态 —— 读者无法判断色深对应哪一档。

```python
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

# ── 数据：n_unit 行(单元/槽位) × n_frame 列(帧/时隙)，值 = 离散状态编码
#    真实项目里从仿真结果 JSON 读；此处用可复现的随机演示
rng = np.random.default_rng(7)
n_unit, n_frame = 16, 40
Z = rng.choice([0, 1, 2, 3], size=(n_unit, n_frame), p=[0.70, 0.18, 0.09, 0.03])
Z = Z.astype(float)
Z[rng.random(Z.shape) < 0.05] = np.nan          # 空缺单元用 nan，画成空白不画死0

STATE_NAMES = ['0（首传成功）', '1 轮重传', '2 轮', '3 轮']
# 离散色带：低档用浅色、高档用醒目色（语义递进），一律走 PALETTE 派生
CMAP = ListedColormap([_lighten(PALETTE[2], 0.42), _lighten(PALETTE[5], 0.20),
                       PALETTE[1], PALETTE[4]])
BOUNDS = [-0.5, 0.5, 1.5, 2.5, 3.5]            # 每档一个区间，边界卡在半整数
NORM = BoundaryNorm(BOUNDS, CMAP.N)

fig, ax = plt.subplots(figsize=(7.2, 4.4))
pc = ax.pcolormesh(np.arange(n_frame + 1) - 0.5, np.arange(n_unit + 1) - 0.5,
                   np.ma.masked_invalid(Z), cmap=CMAP, norm=NORM,
                   edgecolors='white', linewidth=0.30, zorder=3)

cb = fig.colorbar(pc, ax=ax, shrink=0.82, aspect=16, pad=0.03, ticks=[0, 1, 2, 3])
cb.set_ticklabels(STATE_NAMES)                  # ★ 离散标签写人话，不写 0/1/2/3
cb.set_label('该单元的状态档位', fontsize=10)
cb.ax.tick_params(labelsize=8.4)

ax.set_xlabel('帧 / 时隙序号 $k$', fontsize=10)
ax.set_ylabel('单元 / 槽位序号', fontsize=10)
ax.set_xticks([0, 9, 19, 29, 39]); ax.set_xticklabels(['1', '10', '20', '30', '40'])
ax.set_yticks([0, 3, 7, 11, 15]);  ax.set_yticklabels(['1', '4', '8', '12', '16'])
ax.tick_params(labelsize=9)
ax.set_title('(a) 仿真逐帧状态栅格', fontsize=11, fontweight='bold', loc='left', pad=6)

fig.tight_layout()
save_fig(fig, 'figures/fig_state_grid.pdf')
```

**注意事项**：
```python
# 1. ⛔ 栅格铺满坐标区，图内没有空白可放文字 —— 统计结论（首传成功率/最大重传轮次/丢包数/
#    仿真总帧数）一律写进 LaTeX \caption{}，不要用 ax.text 压在格子上（会盖住首行数据）。
# 2. 展示帧数控制在 30-60 列：真实仿真跑几千帧时取前 N 帧展示，并在 caption 说明
#    "取前 40 帧展示，共运行 1200 帧"，不要把几千列硬塞进一张图（格子细成条纹看不清）。
# 3. 空缺/未定义单元用 np.nan + masked_invalid 画成空白，不要填 0 —— 填 0 会被误读成"状态0"。
# 4. 状态超过 5 档时考虑合并语义相近的档（如"3轮及以上"归一档），离散色带超过 5 色难分辨。
# 5. 若要同时看"状态"和"数值"（如重传轮次+时长），拆成上下两个 panel 共享 x 轴，
#    不要在一个格子里塞两种编码。
```
