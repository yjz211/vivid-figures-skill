from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()
import matplotlib.pyplot as plt
import numpy as np

methods = ['Ours', 'LSTM', 'Random Forest', 'Linear Reg']
metrics = ['MAE↓', 'RMSE↓', 'R²↑', 'Speed↑', 'Stability↑']
# All normalized to [0,1] where 1=best
data = np.array([
    [0.95, 0.92, 0.987, 0.85, 0.90],
    [0.45, 0.50, 0.812, 0.60, 0.65],
    [0.88, 0.82, 0.965, 0.92, 0.78],
    [0.10, 0.15, 0.421, 0.98, 0.55],
])

fig, ax = plt.subplots(figsize=(9, 5))
x = np.arange(len(metrics))

# Subtle grid
ax.grid(axis='y', alpha=0.15, linestyle='-', color=COLORS['grid'])
ax.set_axisbelow(True)

# Optimal region shading per axis (top 20%)
for j in range(len(metrics)):
    ax.fill_between([j - 0.3, j + 0.3], 0.8, 1.0, alpha=0.06,
                     color=COLORS['up'], zorder=0)
    ax.text(j, 0.82, '最优区', ha='center', fontsize=6, color=COLORS['up'],
            alpha=0.6, fontstyle='italic')

# Draw simple lines per method
for i, (method, row) in enumerate(zip(methods, data)):
    is_ours = (i == 0)

    if is_ours:
        # Thick solid line for "Ours"
        ax.plot(x, row, '-', color=PALETTE[0], linewidth=3.5, zorder=5,
                solid_capstyle='round')
        # Markers
        ax.scatter(x, row, color=PALETTE[0], s=100, zorder=6,
                   edgecolors='white', linewidths=1.5, marker='o')
        # Value labels
        for j, v in enumerate(row):
            ax.text(j, v + 0.04, f'{v:.2f}', ha='center', fontsize=8.5,
                    color=PALETTE[0], fontweight='bold')
        # Highlight label
        ax.text(x[-1] + 0.25, row[-1], f'★ {method}', va='center', fontsize=10,
                color=PALETTE[0], fontweight='bold')
    else:
        # Simple line for other methods
        ax.plot(x, row, '-', color=PALETTE[i], linewidth=1.5, alpha=0.6,
                solid_capstyle='round')
        ax.scatter(x, row, color=PALETTE[i], s=50, zorder=4, alpha=0.7,
                   edgecolors='white', linewidths=0.8)
        ax.text(x[-1] + 0.25, row[-1], method, va='center', fontsize=8.5,
                color=PALETTE[i], alpha=0.8)

ax.set_xticks(x)
ax.set_xticklabels(metrics, fontsize=10.5)
ax.set_ylabel('归一化得分 (1=最优)', fontsize=11)
ax.set_ylim(0, 1.12)
ax.set_xlim(-0.4, len(metrics) - 0.3)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_parallel_coords.pdf')
