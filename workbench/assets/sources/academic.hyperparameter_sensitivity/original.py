import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

params = {
    'Learning Rate': ([1e-4, 3e-4, 1e-3, 3e-3, 1e-2],
                      [88.2, 91.5, 92.3, 90.1, 85.4],
                      [86.0, 89.8, 90.5, 87.3, 82.1],
                      [90.1, 93.0, 94.0, 92.5, 88.2]),
    'Hidden Dim': ([64, 128, 256, 512, 1024],
                   [87.5, 90.2, 92.3, 92.1, 91.8],
                   [85.2, 88.0, 90.1, 89.8, 89.5],
                   [89.5, 92.0, 94.2, 94.0, 93.8]),
    'Num Layers': ([2, 4, 6, 8, 12],
                   [86.3, 89.8, 92.3, 91.5, 90.2],
                   [83.8, 87.5, 90.0, 89.2, 87.8],
                   [88.5, 91.8, 94.5, 93.5, 92.2]),
    'Dropout': ([0.0, 0.1, 0.2, 0.3, 0.5],
                [89.1, 91.2, 92.3, 91.8, 88.5],
                [86.8, 89.0, 90.1, 89.5, 86.0],
                [91.0, 93.2, 94.2, 93.8, 90.5]),
}

fig, axes = plt.subplots(2, 2, figsize=(5.0, 4.9))   # 示例尺寸；保留模板比例，按实际显示尺寸检查字号与布局
for idx, (name, (x_vals, y_mean, y_min, y_max)) in enumerate(params.items()):
    ax = axes.flat[idx]
    x_pos = range(len(x_vals))

    # Gradient fill between min and max
    for layer, alpha in enumerate([0.20, 0.12, 0.06]):
        shrink = layer * 0.3
        ax.fill_between(x_pos,
                        np.array(y_min) + shrink,
                        np.array(y_max) - shrink,
                        alpha=alpha, color=PALETTE[idx], linewidth=0)

    # Min/max boundary lines
    ax.plot(x_pos, y_min, '--', color=PALETTE[idx], linewidth=0.8, alpha=0.4)
    ax.plot(x_pos, y_max, '--', color=PALETTE[idx], linewidth=0.8, alpha=0.4)

    # Mean line
    ax.plot(x_pos, y_mean, 'o-', color=PALETTE[idx], linewidth=2, markersize=7,
            markeredgecolor='white', markeredgewidth=1.2)

    # Optimal point highlight
    best_i = np.argmax(y_mean)
    ax.scatter(best_i, y_mean[best_i], s=150, color=PALETTE[idx], zorder=5,
               edgecolor='white', linewidth=2.5)

    # Optimal region shading (±1 of best)
    opt_left = max(0, best_i - 1)
    opt_right = min(len(x_vals) - 1, best_i + 1)
    ax.axvspan(opt_left - 0.3, opt_right + 0.3, alpha=0.08, color=COLORS['up'],
               label='Optimal region')

    ax.annotate(f'{y_mean[best_i]:.1f}', xy=(best_i, y_mean[best_i]),
                xytext=(0, 12), textcoords='offset points', fontsize=9, fontweight='bold',
                ha='center', color=PALETTE[idx],
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                          edgecolor=PALETTE[idx], alpha=0.9, linewidth=0.5))

    ax.set_xticks(x_pos)
    ax.set_xticklabels([str(v) for v in x_vals], fontsize=8)
    ax.set_xlabel(name, fontsize=10)
    ax.set_ylabel('Accuracy (%)', fontsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(alpha=0.15, linestyle='--')
    ax.set_title(f'({chr(97 + idx)})', fontsize=12, fontweight='bold', loc='left', pad=3)

fig.tight_layout(pad=0.5)
save_fig(fig, 'figures/fig_hyperparam.pdf')
