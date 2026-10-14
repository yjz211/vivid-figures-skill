import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

configs = ['Full Model', '- Attention', '- Residual', '- Augment', '- Attn & Res', 'Baseline']
scores = [92.3, 89.1, 90.5, 88.7, 85.2, 82.0]
drops = [0, 3.2, 1.8, 3.6, 7.1, 10.3]

fig, ax = plt.subplots(figsize=(8, 5))

# Gradient coloring: green (high) → red (low)
cmap = plt.cm.YlOrRd
norm = plt.Normalize(min(scores) - 2, max(scores) + 2)
colors = [cmap(norm(s)) for s in scores]

bars = ax.bar(range(len(configs)), scores, color=[_lighten(c, 0.35) for c in colors],
              edgecolor=colors, linewidth=1.2, width=0.65, zorder=3)

# Waterfall connector lines between bars
for j in range(len(configs) - 1):
    ax.plot([j + 0.325, j + 0.675], [scores[j], scores[j]],
            color=COLORS['ref_line'], linewidth=0.8, linestyle='--', alpha=0.5, zorder=2)

# Value labels on top + delta arrows inside bars
for j, (bar, score, drop) in enumerate(zip(bars, scores, drops)):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
            f'{score:.1f}', ha='center', va='bottom', fontsize=9.5, fontweight='bold')
    if drop > 0:
        # Delta arrow annotation
        ax.annotate(f'↓{drop:.1f}',
                    xy=(bar.get_x() + bar.get_width() / 2, bar.get_height() - 1),
                    fontsize=8, ha='center', va='top', color='white', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.15', facecolor=COLORS['down'],
                              alpha=0.7, edgecolor='none'))

# Highlight Full Model and Baseline
for idx in [0, len(configs) - 1]:
    bars[idx].set_edgecolor(PALETTE[0] if idx == 0 else PALETTE[3])
    bars[idx].set_linewidth(2)

ax.set_xticks(range(len(configs)))
ax.set_xticklabels(configs, rotation=18, ha='right', fontsize=9)
ax.set_ylabel('Accuracy (%)', fontsize=11)
ax.set_ylim(78, 96)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='y', alpha=0.15, linestyle='--')

# Dashed line connecting Full → Baseline
ax.plot([0, len(configs) - 1], [scores[0], scores[-1]], '--',
        color=COLORS['ref_line'], linewidth=1, alpha=0.4, zorder=1)
ax.text(0.98, 0.05, f'Total drop: {scores[0] - scores[-1]:.1f}',
        transform=ax.transAxes, fontsize=8, color=COLORS['ref_line'],
        ha='right', va='bottom', style='italic',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                  edgecolor=COLORS['grid'], alpha=0.9))

fig.tight_layout()
save_fig(fig, 'figures/fig_ablation.pdf')
