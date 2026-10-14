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
ax.grid(True, linestyle='--', alpha=0.15, color=COLORS['grid']); ax.set_axisbelow(True)

_end_xs, _end_ys, _end_texts, _end_colors = [], [], [], []
for i, (name, vals) in enumerate(methods.items()):
    lw = 2.5 if '本文' in name else 1.5
    alpha = 1.0 if '本文' in name else 0.55
    ax.plot(iters, vals, color=PALETTE[i], linewidth=lw, label=name, alpha=alpha, zorder=3)
    _end_xs.append(iters[-1]); _end_ys.append(vals[-1])
    _end_texts.append(f'{vals[-1]:.1f}'); _end_colors.append(PALETTE[i])
# ★ 终点标注用 smart_labels 防重叠
from _utils.plot_utils import save_fig, smart_labels
smart_labels(ax, _end_xs, _end_ys, _end_texts, colors=_end_colors, fontsize=8, offset=(8, 0))

# 本文算法的下方填充区域（强调单独）
ours = methods['本文算法']
ax.fill_between(iters, ours, alpha=0.10, color=PALETTE[3], linewidth=0, zorder=1)

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
