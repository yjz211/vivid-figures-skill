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
