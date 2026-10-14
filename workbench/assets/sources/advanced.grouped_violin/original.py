import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
categories = ['Dataset A', 'Dataset B', 'Dataset C', 'Dataset D']
group_names = ['Ours', 'Baseline-1', 'Baseline-2']
n_groups = len(group_names)

# Generate sample data (replace with real results)
all_data = {}
for g, gname in enumerate(group_names):
    all_data[gname] = []
    for c in range(len(categories)):
        center = 80 + g * (-3) + c * 2 + np.random.randn()
        d = np.random.normal(center, 3 + g, 50)
        all_data[gname].append(d)

fig, ax = plt.subplots(figsize=(9, 5))
width = 0.25
positions_base = np.arange(len(categories))

for g, gname in enumerate(group_names):
    positions = positions_base + (g - n_groups / 2 + 0.5) * width
    color = PALETTE[g % len(PALETTE)]
    light = _lighten(color, 0.4)

    parts = ax.violinplot(all_data[gname], positions=positions,
                          widths=width * 0.85, showmeans=False,
                          showmedians=False, showextrema=False)

    for pc in parts['bodies']:
        pc.set_facecolor(light)
        pc.set_edgecolor(color)
        pc.set_linewidth(1.2)
        pc.set_alpha(0.8)

    # Add median + quartile lines manually
    for i, d in enumerate(all_data[gname]):
        q1, med, q3 = np.percentile(d, [25, 50, 75])
        pos = positions[i]
        # Median dot
        ax.scatter(pos, med, color=color, s=30, zorder=5,
                   edgecolors='white', linewidths=0.8)
        # Quartile whisker
        ax.vlines(pos, q1, q3, color=color, linewidth=2.5, zorder=4)

    # Invisible scatter for legend
    ax.scatter([], [], color=color, s=60, label=gname, edgecolors='white')

ax.set_xticks(positions_base)
ax.set_xticklabels(categories, fontsize=10)
ax.set_ylabel('Score', fontsize=11)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='y', alpha=0.1, linestyle='--')
fig.tight_layout()
save_fig(fig, 'figures/fig_grouped_violin.pdf')
