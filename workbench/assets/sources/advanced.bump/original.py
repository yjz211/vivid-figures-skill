from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
import matplotlib.pyplot as plt
import numpy as np

methods = ['Ours', 'BERT', 'GPT', 'RoBERTa']
datasets = ['MNLI', 'QQP', 'SST-2', 'QNLI']
ranks = [[1, 1, 2, 1], [3, 2, 1, 3], [2, 3, 3, 2], [4, 4, 4, 4]]

fig, ax = plt.subplots(figsize=(8, 5))
x = np.arange(len(datasets))

# Subtle grid
ax.grid(axis='y', alpha=0.15, linestyle='-', color=COLORS['grid'])
ax.set_axisbelow(True)

for i, (m, r) in enumerate(zip(methods, ranks)):
    is_ours = (i == 0)
    lw = 3.5 if is_ours else 1.8
    alpha_line = 1.0 if is_ours else 0.55
    ms = 14 if is_ours else 9

    # Gradient ribbon for "Ours"
    if is_ours:
        for k in range(len(x) - 1):
            x_fill = np.linspace(x[k], x[k + 1], 50)
            y_fill = np.interp(x_fill, x, r)
            ax.fill_between(x_fill, y_fill - 0.15, y_fill + 0.15,
                            alpha=0.15, color=PALETTE[0])

    # Line
    ax.plot(x, r, 'o-', color=PALETTE[i], linewidth=lw, markersize=ms,
            label=m, zorder=3 + (1 if is_ours else 0), alpha=alpha_line,
            markeredgecolor='white', markeredgewidth=1.5 if is_ours else 0.8)

    # Rank labels at both ends
    ax.text(x[0] - 0.2, r[0], f'#{r[0]} {m}', va='center', ha='right',
            fontsize=9, color=PALETTE[i],
            fontweight='bold' if is_ours else 'normal')
    ax.text(x[-1] + 0.2, r[-1], f'#{r[-1]} {m}', va='center', ha='left',
            fontsize=9, color=PALETTE[i],
            fontweight='bold' if is_ours else 'normal')

# Highlight box for "Ours"
ax.annotate('★ Ours: Rank #1 in 3/4 datasets',
            xy=(x[0], ranks[0][0]), xytext=(x[0] + 0.5, ranks[0][0] - 0.6),
            fontsize=8.5, color=PALETTE[0], fontweight='bold',
            arrowprops=dict(arrowstyle='->', color=PALETTE[0], lw=1.2),
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                      edgecolor=PALETTE[0], alpha=0.9))

ax.set_xticks(x)
ax.set_xticklabels(datasets, fontsize=10)
ax.set_yticks([1, 2, 3, 4])
ax.set_yticklabels(['1st', '2nd', '3rd', '4th'], fontsize=10)
ax.set_ylabel('Rank', fontsize=11)
ax.invert_yaxis()
ax.set_xlim(-0.6, len(datasets) - 0.4)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_bump.pdf')
