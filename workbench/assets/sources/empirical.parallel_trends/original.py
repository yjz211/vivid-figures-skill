import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

periods = np.arange(-5, 6)
treat = np.array([.02, -.01, .03, -.02, .01, .15, .28, .35, .42, .50, .55])
ctrl  = np.array([.01, .00, .02, -.01, .00, .02, .03, .01, .02, .00, .01])
se_t  = np.full(11, .04)
se_c  = np.full(11, .03)

fig, ax = plt.subplots(figsize=(9, 5.5))

for x_start, x_end, c_base, lbl in [(-5.5, -0.5, _lighten(COLORS['up'], 0.8), 'Pre-Treatment'),
                                      (-0.5, 5.5, _lighten(COLORS['highlight'], 0.8), 'Post-Treatment')]:
    ax.axvspan(x_start, x_end, color=c_base, alpha=0.25, zorder=0)
    cx = (x_start + x_end) / 2
    ax.text(cx, -0.15, lbl, ha='center', va='bottom', fontsize=9, color=COLORS['ref_line'],
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                      edgecolor=COLORS['grid'], alpha=0.9))

ax.axvline(x=-0.5, color=COLORS['down'], linestyle='--', linewidth=1.3, alpha=0.7)
ax.text(-0.5, 0.62, 'Treatment', ha='center', va='bottom', fontsize=9,
        color=COLORS['down'], fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.25', facecolor=COLORS['bg_box'],
                  edgecolor=COLORS['down'], alpha=0.9))

n_layers = 8
for k in range(n_layers, 0, -1):
    frac = k / n_layers
    ax.fill_between(periods, treat - frac*1.96*se_t, treat + frac*1.96*se_t,
                    alpha=0.04, color=PALETTE[0], linewidth=0)
    ax.fill_between(periods, ctrl - frac*1.96*se_c, ctrl + frac*1.96*se_c,
                    alpha=0.04, color=PALETTE[1], linewidth=0)

ax.plot(periods, treat, 'o-', color=PALETTE[0], markersize=7, linewidth=2.2,
        label='Treatment', markeredgecolor='white', markeredgewidth=1, zorder=5)
ax.plot(periods, ctrl, 's--', color=PALETTE[1], markersize=6, linewidth=1.8,
        label='Control', markeredgecolor='white', markeredgewidth=1, zorder=5)

ax.annotate(f'ATT = {treat[-1]-ctrl[-1]:.2f}',
            xy=(periods[-1], treat[-1]),
            xytext=(periods[-1] - 1.5, treat[-1] + 0.12),
            fontsize=9, fontweight='bold', color=PALETTE[0],
            arrowprops=dict(arrowstyle='->', color=PALETTE[0], lw=1.5,
                            connectionstyle='arc3,rad=-0.2'),
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                      edgecolor=PALETTE[0], alpha=0.9))

ax.set_xlabel('Period', fontsize=11); ax.set_ylabel('Outcome', fontsize=11)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='upper left')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(alpha=0.15, linestyle='--')
fig.tight_layout()
save_fig(fig, 'figures/fig_parallel.pdf')
