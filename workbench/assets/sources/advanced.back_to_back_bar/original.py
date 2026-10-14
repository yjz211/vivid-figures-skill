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
