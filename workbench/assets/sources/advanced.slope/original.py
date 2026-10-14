from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()
import matplotlib.pyplot as plt
import numpy as np

methods = ['Method-A', 'Method-B', 'Method-C', 'Method-D']
dataset1 = [0.92, 0.88, 0.85, 0.90]
dataset2 = [0.87, 0.91, 0.89, 0.86]

fig, ax = plt.subplots(figsize=(6, 5.5))

# Subtle grid
ax.grid(axis='y', alpha=0.15, linestyle='-', color=COLORS['grid'])
ax.set_axisbelow(True)

# Compute ranks
rank1 = list(np.argsort(np.argsort([-v for v in dataset1])) + 1)
rank2 = list(np.argsort(np.argsort([-v for v in dataset2])) + 1)

for i, m in enumerate(methods):
    diff = dataset2[i] - dataset1[i]
    # Green = improve, Red = decline
    base_color = COLORS['up'] if diff >= 0 else COLORS['down']

    # Simple line connecting two points
    ax.plot([0, 1], [dataset1[i], dataset2[i]], color=base_color,
            linewidth=2.5, solid_capstyle='round')

    # Endpoints
    ax.scatter([0], [dataset1[i]], color=base_color, s=90, zorder=5,
               edgecolors='white', linewidths=1.2)
    ax.scatter([1], [dataset2[i]], color=base_color, s=90, zorder=5,
               edgecolors='white', linewidths=1.2)

    # Value labels
    ax.text(-0.08, dataset1[i], f'{dataset1[i]:.2f}', ha='right', va='center',
            fontsize=9, color=base_color)
    ax.text(1.08, dataset2[i], f'{dataset2[i]:.2f}', ha='left', va='center',
            fontsize=9, color=base_color)

    # Rank change annotation
    rank_delta = rank1[i] - rank2[i]  # positive = improved rank
    if rank_delta != 0:
        arrow_sym = '↑' if rank_delta > 0 else '↓'
        rank_color = COLORS['up'] if rank_delta > 0 else COLORS['down']
        ax.text(1.22, dataset2[i], f'{m} {arrow_sym}{abs(rank_delta)}',
                ha='left', va='center', fontsize=8, color=rank_color,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=rank_color, alpha=0.9))
    else:
        ax.text(1.22, dataset2[i], f'{m} →', ha='left', va='center',
                fontsize=8, color=COLORS['ref_line'])

ax.set_xticks([0, 1])
ax.set_xticklabels(['Dataset-1', 'Dataset-2'], fontsize=11)
ax.set_xlim(-0.35, 1.65)
ax.set_ylim(min(dataset1 + dataset2) - 0.03, max(dataset1 + dataset2) + 0.03)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_slope.pdf')
