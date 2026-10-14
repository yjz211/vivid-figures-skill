import numpy as np, matplotlib.pyplot as plt
from scipy.stats import gaussian_kde, shapiro
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
groups = ['Group A', 'Group B', 'Group C']
data_all = [np.random.lognormal(2, 0.8, 300), np.random.lognormal(2.2, 0.6, 300),
            np.random.lognormal(1.8, 1.0, 300)]

# ★ 自适应高度
_fig_h = max(4, len(groups) * 1.5 + 1)
fig, ax = plt.subplots(figsize=(10, _fig_h))
for i, (grp, data) in enumerate(zip(groups, data_all)):
    y_center = i * 2.5
    kde = gaussian_kde(data)
    x_kde = np.linspace(data.min()*0.8, np.percentile(data, 99), 200)
    y_kde = kde(x_kde)
    y_kde_norm = y_kde / y_kde.max() * 0.8

    n_layers = 15
    for k in range(n_layers, 0, -1):
        frac = k / n_layers
        ax.fill_between(x_kde, y_center, y_center + y_kde_norm*frac,
                        alpha=0.035, color=PALETTE[i], linewidth=0)
    ax.fill_between(x_kde, y_center, y_center + y_kde_norm, alpha=0.2, color=PALETTE[i], linewidth=0)
    ax.plot(x_kde, y_center + y_kde_norm, color=PALETTE[i], linewidth=1.5)

    ax.boxplot([data], positions=[y_center], vert=False, widths=0.3, patch_artist=True,
               boxprops=dict(facecolor=_lighten(PALETTE[i], 0.4), edgecolor=PALETTE[i], linewidth=1.2),
               medianprops=dict(color=COLORS['text'], linewidth=1.5),
               whiskerprops=dict(color=PALETTE[i], linewidth=1),
               capprops=dict(color=PALETTE[i], linewidth=1),
               flierprops=dict(marker='.', markersize=2, alpha=0.3, markerfacecolor=PALETTE[i]))

    jitter = np.random.uniform(-0.15, -0.55, len(data))
    ax.scatter(data[::3], y_center + jitter[:len(data[::3])], s=4, alpha=0.25, color=PALETTE[i], zorder=2)

    for pct, pct_label in [(25, 'Q1'), (50, 'Median'), (75, 'Q3')]:
        pv = np.percentile(data, pct)
        ax.plot(pv, y_center - 0.7, '|', color=PALETTE[i], markersize=8, markeredgewidth=1.5, zorder=4)
        ax.text(pv, y_center - 0.9, f'{pct_label}\n{pv:.1f}', ha='center', va='top', fontsize=7, color=COLORS['text'])

    stat, p = shapiro(data[:50])
    ax.text(np.percentile(data, 99)*1.02, y_center + 0.3, f'W={stat:.3f}, p={p:.3f}',
            fontsize=7.5, color=COLORS['text'], va='center',
            bbox=dict(boxstyle='round,pad=0.25', facecolor=COLORS['bg_box'], edgecolor=COLORS['grid'], alpha=0.9))

ax.set_yticks([i*2.5 for i in range(len(groups))]); ax.set_yticklabels(groups, fontsize=10)
ax.set_xlabel('Value', fontsize=11); ax.grid(axis='x', alpha=0.15, linestyle='--')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_dist.pdf')
