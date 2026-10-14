from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()
import matplotlib.pyplot as plt
import numpy as np

np.random.seed(42)
n_studies = 30
effects = np.random.normal(0.5, 0.3, n_studies)
se = np.random.uniform(0.05, 0.4, n_studies)
effects += np.random.normal(0, se)
study_names = [f'Study {i+1}' for i in range(n_studies)]

fig, ax = plt.subplots(figsize=(7, 5.5))

# Subtle grid
ax.grid(alpha=0.15, linestyle='-', color=COLORS['grid'])
ax.set_axisbelow(True)

mean_eff = np.mean(effects)
se_range = np.linspace(0, 0.45, 200)

# Gradient CI bands (99%, 95%, 90%)
ci_levels = [
    (2.576, '99% CI', PALETTE[2], 0.06),
    (1.960, '95% CI', PALETTE[1], 0.08),
    (1.645, '90% CI', PALETTE[0], 0.10),
]
for z_val, label, color, alpha in ci_levels:
    ax.fill_betweenx(se_range,
                      mean_eff - z_val * se_range,
                      mean_eff + z_val * se_range,
                      alpha=alpha, color=color, label=label)

# Pooled effect line
ax.axvline(mean_eff, color=PALETTE[0], linestyle='-', linewidth=1.8, alpha=0.6)

# Study points
ax.scatter(effects, se, color=PALETTE[0], s=50, alpha=0.8, edgecolors='white',
           linewidths=0.8, zorder=4)

# Study labels for outliers (outside 95% CI)
for i in range(n_studies):
    if abs(effects[i] - mean_eff) > 1.96 * se[i] * 1.5:
        ax.annotate(study_names[i],
                    xy=(effects[i], se[i]),
                    xytext=(effects[i] + 0.08, se[i] - 0.03),
                    fontsize=7, color=COLORS['down'],
                    arrowprops=dict(arrowstyle='->', color=COLORS['down'], lw=0.7),
                    bbox=dict(boxstyle='round,pad=0.15', facecolor=COLORS['bg_box'],
                              edgecolor=COLORS['down'], alpha=0.7))

# Egger's test annotation
ax.annotate("Egger's test: t = 1.42, p = 0.167\nNo significant asymmetry",
            xy=(0.02, 0.02), xycoords='axes fraction',
            fontsize=8, va='bottom',
            bbox=dict(boxstyle='round,pad=0.4', facecolor=_lighten(PALETTE[0], 0.7),
                      edgecolor=PALETTE[0], alpha=0.9))

ax.set_xlabel('Effect size', fontsize=11)
ax.set_ylabel('Standard error', fontsize=11)
ax.invert_yaxis()
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8, loc='best',
          fancybox=True)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_funnel.pdf')
