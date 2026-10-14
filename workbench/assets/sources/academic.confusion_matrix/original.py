import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde, ttest_ind
import matplotlib.colors as mcolors
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
groups = ['Ours', 'Method A', 'Method B']
data = [np.random.normal(92, 3, 100), np.random.normal(88, 4, 100),
        np.random.normal(85, 5, 100)]

def cohens_d(g1, g2):
    n1, n2 = len(g1), len(g2)
    pooled_std = np.sqrt(((n1 - 1) * g1.std() ** 2 + (n2 - 1) * g2.std() ** 2) / (n1 + n2 - 2))
    return (g1.mean() - g2.mean()) / pooled_std

# ★ 自适应高度
_fig_h = max(4, len(groups) * 1.0 + 1)
fig, ax = plt.subplots(figsize=(8, _fig_h))
for i, (name, d) in enumerate(zip(groups, data)):
    pos = i
    # Gradient half-violin (right side)
    kde = gaussian_kde(d, bw_method=0.3)
    yr = np.linspace(d.min() - 4, d.max() + 4, 300)
    density = kde(yr)
    density_norm = density / density.max() * 0.38
    base_rgb = mcolors.to_rgb(PALETTE[i])
    for layer in range(6):
        frac = layer / 6
        alpha = 0.35 - frac * 0.05
        ax.fill_betweenx(yr, pos + frac * 0.02, pos + density_norm * (1 - frac * 0.12),
                         alpha=alpha, color=PALETTE[i], linewidth=0)
    ax.plot(pos + density_norm, yr, color=PALETTE[i], linewidth=1.2, alpha=0.8)

    # Box plot (left, narrow)
    bp = ax.boxplot(d, positions=[pos - 0.18], widths=0.12, vert=True, patch_artist=True,
                    boxprops=dict(facecolor=_lighten(PALETTE[i], 0.4),
                                  edgecolor=PALETTE[i], linewidth=1.2),
                    medianprops=dict(color=COLORS['text'], linewidth=1.8),
                    whiskerprops=dict(linewidth=1, color=PALETTE[i]),
                    capprops=dict(linewidth=1, color=COLORS['ref_line']),
                    flierprops=dict(marker='', markersize=0))

    # Jittered strip (far left)
    jitter = np.random.uniform(-0.08, 0.08, len(d))
    ax.scatter(pos - 0.38 + jitter, d, s=6, alpha=0.2, color=PALETTE[i], edgecolor='none')

    # Mean diamond
    ax.scatter(pos - 0.18, d.mean(), marker='D', s=45, color=PALETTE[i],
               edgecolor='white', linewidth=1.2, zorder=5)

# Significance brackets with p-values and Cohen's d
def add_bracket(ax, x1, x2, y, p_val, d_val, h=1.5):
    ax.plot([x1, x1, x2, x2], [y, y + h, y + h, y], color=COLORS['text'], linewidth=0.8)
    stars = '***' if p_val < 0.001 else '**' if p_val < 0.01 else '*' if p_val < 0.05 else 'n.s.'
    ax.text((x1 + x2) / 2, y + h + 0.2, f'{stars} (p={p_val:.1e})\nd={d_val:.2f}',
            ha='center', va='bottom', fontsize=7, color=COLORS['text'],
            bbox=dict(boxstyle='round,pad=0.2', facecolor=COLORS['bg_box'],
                      edgecolor=COLORS['grid'], alpha=0.9, linewidth=0.3))

y_max = max(d.max() for d in data) + 2
for idx, (g1, g2) in enumerate([(0, 1), (0, 2)]):
    _, p = ttest_ind(data[g1], data[g2])
    d_val = cohens_d(data[g1], data[g2])
    add_bracket(ax, g1, g2, y_max + idx * 7, p, d_val)

ax.set_xticks(range(len(groups)))
ax.set_xticklabels(groups, fontsize=10)
ax.set_ylabel('Accuracy (%)', fontsize=11)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='y', alpha=0.15, linestyle='--')
fig.tight_layout()
save_fig(fig, 'figures/fig_raincloud.pdf')
