import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

periods = np.arange(-4, 5)
coefs   = np.array([.01, -.02, .01, .00, .12, .25, .31, .38, .42])
se      = np.array([.04, .03, .04, .03, .05, .05, .06, .06, .07])

fig, ax = plt.subplots(figsize=(8, 5))
ax.axhline(y=0, color=COLORS['ref_line'], linewidth=0.6, alpha=0.5)
ax.axvline(x=-0.5, color=COLORS['down'], linestyle='--', linewidth=1.0, alpha=0.6)
ax.axvspan(-4.5, -0.5, color=COLORS['bg_box'], alpha=0.3, zorder=0)
ax.axvspan(-0.5, 4.5, color=_lighten(COLORS['highlight'], 0.85), alpha=0.3, zorder=0)

for t_val, c, s in zip(periods, coefs, se):
    lo, hi = c - 1.96 * s, c + 1.96 * s
    base_color = COLORS['ref_line'] if t_val < 0 else PALETTE[0]
    n_layers = 6
    for k in range(n_layers, 0, -1):
        frac = k / n_layers
        ax.plot([t_val, t_val], [c - frac*1.96*s, c + frac*1.96*s],
                color=base_color, linewidth=3.5 - k*0.3, alpha=0.08 + 0.04*(n_layers-k) + 0.3,
                solid_capstyle='round')
    ax.plot([t_val, t_val], [lo, hi], color=base_color, linewidth=2.5,
            solid_capstyle='round', alpha=0.8)
    ax.plot(t_val, c, 'o', color=base_color, markersize=8,
            markeredgecolor='white', markeredgewidth=1.2, zorder=5)
    if abs(c) > 1.96 * s:
        star = '***' if abs(c) > 2.576 * s else '**'
        ax.text(t_val, hi + 0.02, star, ha='center', va='bottom',
                fontsize=8, color=base_color, fontweight='bold')

post_mask = periods >= 0
cum_effect = np.cumsum(coefs[post_mask])
ax2 = ax.twinx()
ax2.plot(periods[post_mask], cum_effect, '--', color=PALETTE[1], linewidth=1.5,
         alpha=0.7, label='Cumulative Effect')
ax2.set_ylabel('Cumulative Effect', fontsize=10, color=PALETTE[1])
ax2.tick_params(axis='y', labelcolor=PALETTE[1])
ax2.legend(loc='upper left', frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8)

ax.set_xlabel('Period Relative to Treatment', fontsize=11)
ax.set_ylabel('Coefficient', fontsize=11); ax.set_xticks(periods)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(alpha=0.15, linestyle='--')
fig.tight_layout()
save_fig(fig, 'figures/fig_event.pdf')
