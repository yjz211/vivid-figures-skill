import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

q = np.arange(0.1, 1.0, 0.1)
c = np.array([-.35,-.30,-.25,-.20,-.15,-.10,-.05,.02,.08])
se = np.array([.06,.05,.04,.04,.04,.05,.05,.06,.07]); ols = -0.18; ols_se = 0.03

fig, ax = plt.subplots(figsize=(8, 5))
n_layers = 10
for k in range(n_layers, 0, -1):
    frac = k / n_layers
    ax.fill_between(q, c-frac*1.96*se, c+frac*1.96*se, alpha=0.03, color=PALETTE[0], linewidth=0)

ax.fill_between(q, ols-1.96*ols_se, ols+1.96*ols_se, alpha=0.12, color=PALETTE[1], linewidth=0, label='OLS 95% CI')
ax.axhline(y=ols, color=PALETTE[1], linestyle='--', linewidth=1.5, alpha=0.8)

sig_mask = (c-1.96*se > 0) | (c+1.96*se < 0)
for i in range(len(q)):
    if sig_mask[i]: ax.axvspan(q[i]-0.04, q[i]+0.04, color=COLORS['up'], alpha=0.06, zorder=0)

ax.axhline(y=0, color=COLORS['ref_line'], linestyle='-', linewidth=0.5, alpha=0.5)
ax.plot(q, c, 'o-', color=PALETTE[0], linewidth=2.5, markersize=8,
        markeredgecolor='white', markeredgewidth=1.2, label='QR Coefficient', zorder=5)
ax.fill_between(q, c, ols, alpha=0.06, color=PALETTE[2], label='QR−OLS Gap', linewidth=0)

for qi, ci, si in zip(q, c, se):
    if abs(ci) > 1.96*si:
        star = '***' if abs(ci) > 2.576*si else '**'
        ax.text(qi, ci+1.96*si+0.015, star, ha='center', va='bottom', fontsize=8, color=PALETTE[0], fontweight='bold')

ax.annotate(f'τ=0.9: {c[-1]:.3f}', xy=(q[-1], c[-1]),
            xytext=(q[-1]-0.15, c[-1]+0.12), fontsize=9, color=PALETTE[0],
            arrowprops=dict(arrowstyle='->', color=PALETTE[0], lw=1.2),
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=PALETTE[0], alpha=0.9))

ax.set_xlabel('Quantile (τ)', fontsize=11); ax.set_ylabel('Coefficient', fontsize=11)
ax.set_xticks(q); ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='upper left')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(alpha=0.15, linestyle='--')
fig.tight_layout()
save_fig(fig, 'figures/fig_quantile.pdf')
