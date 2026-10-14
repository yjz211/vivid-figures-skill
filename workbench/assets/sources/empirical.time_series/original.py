import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
years = np.arange(2010, 2024)
gdp = np.cumsum(np.random.normal(0.5, 0.3, 14)) + 10
digital = np.cumsum(np.random.normal(0.8, 0.2, 14)) + 2

fig, ax1 = plt.subplots(figsize=(9, 5)); ax2 = ax1.twinx()

n_layers = 12
for k in range(n_layers, 0, -1):
    frac = k / n_layers
    ax1.fill_between(years, gdp.min()-0.5, gdp-(gdp-gdp.min()+0.5)*(1-frac),
                     alpha=0.02, color=PALETTE[0], linewidth=0)
ax1.fill_between(years, gdp.min()-0.5, gdp, alpha=0.08, color=PALETTE[0], linewidth=0)

for k in range(n_layers, 0, -1):
    frac = k / n_layers
    ax2.fill_between(years, digital.min()-0.5, digital-(digital-digital.min()+0.5)*(1-frac),
                     alpha=0.02, color=PALETTE[1], linewidth=0)
ax2.fill_between(years, digital.min()-0.5, digital, alpha=0.08, color=PALETTE[1], linewidth=0)

ax1.plot(years, gdp, 'o-', color=PALETTE[0], linewidth=2.2, markersize=6,
         label='GDP', markeredgecolor='white', markeredgewidth=1, zorder=5)
ax2.plot(years, digital, 's-', color=PALETTE[1], linewidth=2.2, markersize=6,
         label='Digital Index', markeredgecolor='white', markeredgewidth=1, zorder=5)

for yr, evt in {2015: 'Policy A', 2020: 'Policy B'}.items():
    ax1.axvline(x=yr, color=COLORS['down'], linestyle=':', linewidth=1.0, alpha=0.6)
    ax1.text(yr, gdp.max()+0.3, evt, ha='center', va='bottom', fontsize=8, color=COLORS['down'],
             bbox=dict(boxstyle='round,pad=0.2', facecolor=COLORS['bg_box'], edgecolor=COLORS['down'], alpha=0.85))

corr_val = np.corrcoef(gdp, digital)[0, 1]
ax1.text(0.03, 0.97, f'Pearson r = {corr_val:.3f}', transform=ax1.transAxes, fontsize=9,
         va='top', ha='left', bbox=dict(boxstyle='round,pad=0.5', facecolor=_lighten(PALETTE[0], 0.7),
                                         edgecolor=COLORS['grid'], alpha=0.95), color=COLORS['text'])

ax1.set_xlabel('Year', fontsize=11)
ax1.set_ylabel('GDP', fontsize=11, color=PALETTE[0])
ax2.set_ylabel('Digital Index', fontsize=11, color=PALETTE[1])
l1, lb1 = ax1.get_legend_handles_labels(); l2, lb2 = ax2.get_legend_handles_labels()
ax1.legend(l1+l2, lb1+lb2, loc='lower right', frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9)
ax1.spines['top'].set_visible(False)
ax1.grid(alpha=0.15, linestyle='--')
fig.tight_layout()
save_fig(fig, 'figures/fig_trend.pdf')
