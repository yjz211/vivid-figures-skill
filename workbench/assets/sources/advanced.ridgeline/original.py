import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
groups = ['Model A', 'Model B', 'Model C', 'Model D', 'Model E',
          'Model F', 'Model G', 'Model H']
n_groups = len(groups)

# Generate sample data (replace with real data)
data = []
for i in range(n_groups):
    center = 70 + i * 3 + np.random.randn() * 2
    spread = 5 + np.random.rand() * 5
    d = np.random.normal(center, spread, 200)
    data.append(d)

fig, ax = plt.subplots(figsize=(8, 6))
overlap = 0.6  # vertical overlap factor
x_grid = np.linspace(min(d.min() for d in data) - 5,
                      max(d.max() for d in data) + 5, 300)

for i in range(n_groups - 1, -1, -1):  # draw back to front
    kde = gaussian_kde(data[i], bw_method=0.3)
    density = kde(x_grid)
    # Normalize density to consistent height
    density = density / density.max() * 0.8

    baseline = i * overlap
    color = PALETTE[i % len(PALETTE)]
    light = _lighten(color, 0.5)

    # Gradient fill
    ax.fill_between(x_grid, baseline, baseline + density,
                    color=light, alpha=0.85, zorder=n_groups - i)
    ax.plot(x_grid, baseline + density, color=color, linewidth=1.5,
            zorder=n_groups - i + 0.5)

    # Median line
    median = np.median(data[i])
    med_density = kde(median)[0] / density.max() * 0.8
    ax.plot([median, median], [baseline, baseline + med_density],
            color=color, linewidth=1.5, linestyle='--', alpha=0.7,
            zorder=n_groups - i + 1)
    ax.text(median, baseline + med_density + 0.02,
            f'{median:.1f}', ha='center', fontsize=7, color=color,
            fontweight='bold', zorder=n_groups + 10)

    # Group label
    ax.text(x_grid[0] - 1, baseline + 0.15, groups[i],
            ha='right', va='center', fontsize=9, fontweight='bold',
            color=color)

ax.set_yticks([])
ax.set_xlabel('Score', fontsize=11)
ax.spines['left'].set_visible(False)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_ridgeline.pdf')
