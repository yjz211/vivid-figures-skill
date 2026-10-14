import numpy as np, matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
fake = np.random.normal(0, 0.08, 500); real = -0.291

fig, ax = plt.subplots(figsize=(8, 5))
kde = gaussian_kde(fake)
xk = np.linspace(fake.min() - 0.08, fake.max() + 0.08, 300)
yk = kde(xk)

n_layers = 20
for k in range(n_layers):
    ax.fill_between(xk, 0, yk * (1 - k*0.02), alpha=0.03, color=PALETTE[0], linewidth=0)
ax.fill_between(xk, 0, yk, alpha=0.15, color=PALETTE[0], linewidth=0)
ax.plot(xk, yk, color=PALETTE[0], linewidth=2.5, zorder=4)
ax.hist(fake, bins=45, density=True, color=_lighten(PALETTE[0], 0.4), alpha=0.5, edgecolor=PALETTE[0], linewidth=0.8, zorder=2)

for pval_pct, plabel in [(np.percentile(fake, 5), '5th'), (np.percentile(fake, 95), '95th')]:
    ax.axvline(x=pval_pct, color=COLORS['ref_line'], linestyle=':', linewidth=1.0, alpha=0.7)
    ax.text(pval_pct, max(yk)*0.92, plabel, ha='center', va='bottom', fontsize=8, color=COLORS['text'],
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=COLORS['grid'], alpha=0.8))

ax.axvline(x=real, color=PALETTE[1], linewidth=2.5, zorder=5)
ax.annotate(f'Real = {real:.3f}', xy=(real, max(yk)*0.15),
            xytext=(real - 0.12, max(yk)*0.65), fontsize=10, fontweight='bold', color=PALETTE[1],
            arrowprops=dict(arrowstyle='->', color=PALETTE[1], lw=1.5, connectionstyle='arc3,rad=0.2'),
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor=PALETTE[1], alpha=0.95))

p_value = np.mean(np.abs(fake) >= np.abs(real))
ax.text(0.97, 0.95, f'Permutations: 500\np-value = {p_value:.3f}', transform=ax.transAxes,
        fontsize=8.5, va='top', ha='right',
        bbox=dict(boxstyle='round,pad=0.5', facecolor=COLORS['bg_box'], edgecolor=COLORS['grid'], alpha=0.95), color=COLORS['text'])

ax.set_xlabel('Placebo Coefficients', fontsize=11); ax.set_ylabel('Density', fontsize=11)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(alpha=0.15, linestyle='--')
fig.tight_layout()
save_fig(fig, 'figures/fig_placebo.pdf')
