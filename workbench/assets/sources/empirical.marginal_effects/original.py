import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

x = np.linspace(0, 1, 200); me = 0.3 - 0.5*x; se = 0.04 + 0.03*x

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

n_layers = 10
for k in range(n_layers, 0, -1):
    frac = k / n_layers
    ax1.fill_between(x, me - frac*1.96*se, me + frac*1.96*se, alpha=0.03, color=PALETTE[0], linewidth=0)

sig_mask = (me - 1.96*se > 0) | (me + 1.96*se < 0)
ax1.fill_between(x, -0.3, 0.5, where=sig_mask, alpha=0.06, color=COLORS['up'], zorder=0, label='Significant')
ax1.fill_between(x, -0.3, 0.5, where=~sig_mask, alpha=0.04, color=COLORS['down'], zorder=0, label='Non-significant')
ax1.plot(x, me, color=PALETTE[0], linewidth=2.5, zorder=5)
ax1.axhline(y=0, color=COLORS['ref_line'], linestyle='--', linewidth=0.8)

cross_idx = np.argmin(np.abs(me)); cross_x = x[cross_idx]
ax1.plot(cross_x, 0, 'o', color=PALETTE[1], markersize=12, zorder=6, markeredgecolor='white', markeredgewidth=2)
ax1.annotate(f'Crossover\nMod = {cross_x:.2f}', xy=(cross_x, 0),
             xytext=(cross_x+0.15, 0.12), fontsize=9, fontweight='bold', color=PALETTE[1],
             arrowprops=dict(arrowstyle='->', color=PALETTE[1], lw=1.5, connectionstyle='arc3,rad=-0.3'),
             bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=PALETTE[1], alpha=0.95))
ax1.set_xlabel('Moderator'); ax1.set_ylabel('Marginal Effect (95% CI)')
ax1.text(-0.1, 1.06, '(a)', transform=ax1.transAxes, fontsize=13, fontweight='bold')
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.legend(fontsize=8, frameon=False, edgecolor=COLORS['grid']); ax1.grid(alpha=0.15, linestyle='--')

x2 = np.linspace(0.3, 0.95, 100); yh = 2.58 + 0.08*x2; yl = 2.52 + 0.04*x2; se2 = 0.015
for k in range(8, 0, -1):
    frac = k / 8
    ax2.fill_between(x2, yh-frac*1.96*se2, yh+frac*1.96*se2, alpha=0.03, color=PALETTE[0], linewidth=0)
    ax2.fill_between(x2, yl-frac*1.96*se2, yl+frac*1.96*se2, alpha=0.03, color=PALETTE[1], linewidth=0)
ax2.plot(x2, yh, '-', color=PALETTE[0], linewidth=2.5, label='High (+1SD)')
ax2.plot(x2, yl, '--', color=PALETTE[1], linewidth=2.5, label='Low (−1SD)')
ax2.set_xlabel('Independent Variable'); ax2.set_ylabel('Predicted DV')
ax2.text(-0.1, 1.06, '(b)', transform=ax2.transAxes, fontsize=13, fontweight='bold')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9); ax2.grid(alpha=0.15, linestyle='--')

fig.tight_layout()
save_fig(fig, 'figures/fig_moderation.pdf')
