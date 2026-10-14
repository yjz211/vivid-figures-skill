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

# 淡色背景渐变
ax.axhspan(min(min(v) for v in series.values()) - 5,
           max(max(v) for v in series.values()) + 5,
           alpha=0.02, color=PALETTE[0], zorder=0)

for i, (name, y) in enumerate(series.items()):
    is_ours = '本文' in name
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
