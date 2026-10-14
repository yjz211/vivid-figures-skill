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
