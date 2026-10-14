from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

np.random.seed(42)
bins = np.linspace(0, 1, 11)
bin_centers = (bins[:-1] + bins[1:]) / 2
model_a = np.clip(bin_centers + np.random.uniform(-0.05, 0.05, 10), 0, 1)
model_b = np.clip(bin_centers ** 0.7 + np.random.uniform(-0.03, 0.03, 10), 0, 1)

# Simulated predicted probabilities for histogram
pred_probs_a = np.clip(np.random.beta(2, 2, 500), 0, 1)
pred_probs_b = np.clip(np.random.beta(1.5, 3, 500), 0, 1)

# Brier scores
brier_a = 0.023
brier_b = 0.089

fig = plt.figure(figsize=(6, 7))
gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1], hspace=0.08)

# Top: Calibration curve
ax_cal = fig.add_subplot(gs[0])
ax_cal.grid(alpha=0.15, linestyle='-', color=COLORS['grid'])
ax_cal.set_axisbelow(True)

# Perfect calibration line
ax_cal.plot([0, 1], [0, 1], 'k--', linewidth=0.8, alpha=0.5, label='Perfect')

# Gradient CI band for Model A
ci_width_a = np.random.uniform(0.03, 0.07, 10)
ax_cal.fill_between(bin_centers, model_a - ci_width_a, model_a + ci_width_a,
                     alpha=0.15, color=PALETTE[0])
ax_cal.plot(bin_centers, model_a, 'o-', color=PALETTE[0], linewidth=2.2,
            markersize=7, label=f'Ours (Brier={brier_a:.3f})',
            markeredgecolor='white', markeredgewidth=1.0)

# Gradient CI band for Model B
ci_width_b = np.random.uniform(0.04, 0.09, 10)
ax_cal.fill_between(bin_centers, model_b - ci_width_b, model_b + ci_width_b,
                     alpha=0.12, color=PALETTE[3])
ax_cal.plot(bin_centers, model_b, 's--', color=PALETTE[3], linewidth=2.0,
            markersize=7, label=f'Baseline (Brier={brier_b:.3f})',
            markeredgecolor='white', markeredgewidth=1.0)

# Brier score annotation box
ax_cal.annotate(f'Brier Score\nOurs: {brier_a:.3f}\nBaseline: {brier_b:.3f}',
                xy=(0.05, 0.88), xycoords='axes fraction',
                fontsize=8.5, va='top',
                bbox=dict(boxstyle='round,pad=0.4', facecolor=_lighten(PALETTE[0], 0.7),
                          edgecolor=PALETTE[0], alpha=0.9))

ax_cal.set_ylabel('Fraction of positives', fontsize=11)
ax_cal.set_xlim(0, 1)
ax_cal.set_ylim(0, 1)
ax_cal.set_aspect('equal')
ax_cal.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8.5, loc='lower right')
ax_cal.spines['top'].set_visible(False)
ax_cal.spines['right'].set_visible(False)
ax_cal.set_xticklabels([])

# Bottom: Histogram of predicted probabilities
ax_hist = fig.add_subplot(gs[1])
ax_hist.hist(pred_probs_a, bins=20, alpha=0.5, color=PALETTE[0], label='Ours',
             edgecolor='white', linewidth=0.5)
ax_hist.hist(pred_probs_b, bins=20, alpha=0.4, color=PALETTE[3], label='Baseline',
             edgecolor='white', linewidth=0.5)
ax_hist.set_xlabel('Mean predicted probability', fontsize=11)
ax_hist.set_ylabel('Count', fontsize=10)
ax_hist.set_xlim(0, 1)
ax_hist.legend(frameon=False, fontsize=8)
ax_hist.spines['top'].set_visible(False)
ax_hist.spines['right'].set_visible(False)

fig.tight_layout()
save_fig(fig, 'figures/fig_calibration.pdf')
