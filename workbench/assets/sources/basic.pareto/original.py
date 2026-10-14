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
