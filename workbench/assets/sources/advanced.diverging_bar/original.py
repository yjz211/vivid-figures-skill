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
