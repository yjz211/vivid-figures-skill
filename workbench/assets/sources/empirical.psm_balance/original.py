import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

covs = ['GDP per capita','Population','Education','Urbanization','FDI Inflow','R&D Spending','Infrastructure']
before = np.array([.35,.28,.22,.18,.42,.31,.25]); after = np.array([.05,.03,.08,.02,.06,.04,.07])

# ★ 自适应高度
_fig_h = max(4, len(covs) * 0.7 + 1.5)
fig, ax = plt.subplots(figsize=(9, _fig_h)); y = np.arange(len(covs))
ax.axvspan(-0.10, 0.10, color=_lighten(COLORS['up'], 0.8), alpha=0.4, zorder=0, label='Acceptable (|d|<0.10)')
ax.axvline(x=0.10, color=COLORS['up'], linestyle='--', linewidth=0.8, alpha=0.6)

for i in range(len(covs)):
    ax.annotate('', xy=(after[i], y[i]), xytext=(before[i], y[i]),
                arrowprops=dict(arrowstyle='->', color=COLORS['neutral'], lw=1.2))
    improvement = (1 - after[i]/before[i]) * 100
    ax.text((before[i]+after[i])/2, y[i]+0.25, f'↓{improvement:.0f}%', ha='center', va='bottom',
            fontsize=7.5, color=COLORS['up'], fontweight='bold')

ax.scatter(before, y, s=80, color=PALETTE[1], marker='o', zorder=4, label='Before', edgecolor='white')
ax.scatter(after, y, s=80, color=PALETTE[0], marker='D', zorder=4, label='After', edgecolor='white')

ax.set_yticks(y); ax.set_yticklabels(covs, fontsize=10)
ax.set_xlabel('Standardized Mean Difference', fontsize=11); ax.invert_yaxis()

avg_b, avg_a = np.mean(before), np.mean(after)
ax.text(0.97, 0.03, f'Avg |SMD| Before: {avg_b:.3f}\nAvg |SMD| After: {avg_a:.3f}\nReduction: {(1-avg_a/avg_b)*100:.1f}%',
        transform=ax.transAxes, fontsize=8.5, va='bottom', ha='right', color=COLORS['text'],
        bbox=dict(boxstyle='round,pad=0.4', facecolor=COLORS['bg_box'], edgecolor=COLORS['grid'], alpha=0.95))

ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='best')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='x', alpha=0.15, linestyle='--')
fig.tight_layout()
save_fig(fig, 'figures/fig_psm.pdf')
