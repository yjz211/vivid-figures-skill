import numpy as np, matplotlib.pyplot as plt
from scipy import stats
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
n = 200; fitted = np.random.uniform(2, 8, n); resid = np.random.normal(0, 0.5, n)

fig, axes = plt.subplots(2, 2, figsize=(5.0, 4.9))   # 示例尺寸；保留模板比例，按实际显示尺寸检查字号与布局

ax = axes[0, 0]
ax.scatter(fitted, resid, alpha=0.45, s=18, color=PALETTE[0], edgecolor='white', linewidth=0.3, zorder=3)
ax.axhline(0, color=COLORS['down'], linestyle='--', linewidth=0.8, alpha=0.7)
z = np.polyfit(fitted, resid, 3); p = np.poly1d(z)
x_smooth = np.linspace(fitted.min(), fitted.max(), 100)
ax.plot(x_smooth, p(x_smooth), color=PALETTE[1], linewidth=2, zorder=4)
ax.text(0.97, 0.97, 'Breusch-Pagan\nχ²=2.14, p=0.143', transform=ax.transAxes, fontsize=7.5,
        va='top', ha='right', color=COLORS['text'],
        bbox=dict(boxstyle='round,pad=0.3', facecolor=_lighten(COLORS['highlight'], 0.85), edgecolor=_lighten(COLORS['highlight'], 0.4), alpha=0.95))
ax.set_xlabel('Fitted Values'); ax.set_ylabel('Residuals')
ax.set_title('(a)', fontsize=12, fontweight='bold', loc='left', pad=3)
ax.grid(alpha=0.15, linestyle='--')

ax = axes[0, 1]
osm, osr = stats.probplot(resid, dist='norm')[:2]
ax.scatter(osm[0], osm[1], alpha=0.5, s=15, color=PALETTE[0], edgecolor='white', linewidth=0.3)
slope, intercept = osr[:2]
x_line = np.array([osm[0].min(), osm[0].max()])
ax.plot(x_line, slope*x_line+intercept, color=COLORS['down'], linewidth=1.2, linestyle='--')
sw_stat, sw_p = stats.shapiro(resid[:100])
ax.text(0.03, 0.97, f'Shapiro-Wilk\nW={sw_stat:.3f}\np={sw_p:.3f}', transform=ax.transAxes,
        fontsize=7.5, va='top', ha='left', color=COLORS['text'],
        bbox=dict(boxstyle='round,pad=0.3', facecolor=_lighten(PALETTE[0], 0.8), edgecolor=_lighten(PALETTE[0], 0.6), alpha=0.95))
ax.set_xlabel('Theoretical Quantiles'); ax.set_ylabel('Sample Quantiles')
ax.set_title('(b)', fontsize=12, fontweight='bold', loc='left', pad=3)
ax.grid(alpha=0.15, linestyle='--')

ax = axes[1, 0]
ax.hist(resid, bins=30, density=True, color=_lighten(PALETTE[0], 0.4), alpha=0.5, edgecolor=PALETTE[0], linewidth=0.8)
x_norm = np.linspace(resid.min()-0.3, resid.max()+0.3, 200)
y_norm = stats.norm.pdf(x_norm, resid.mean(), resid.std())
ax.plot(x_norm, y_norm, color=COLORS['down'], linewidth=2, zorder=4)
for k in range(10, 0, -1):
    ax.fill_between(x_norm, 0, y_norm*(k/10), alpha=0.015, color=COLORS['down'], linewidth=0)
ax.set_xlabel('Residuals'); ax.set_ylabel('Density')
ax.set_title('(c)', fontsize=12, fontweight='bold', loc='left', pad=3)
ax.grid(alpha=0.15, linestyle='--')

ax = axes[1, 1]
cooks = np.random.exponential(0.005, n); cooks[15] = 0.035; cooks[87] = 0.028
threshold = 4/n
ml, sl, bl = ax.stem(range(n), cooks, linefmt='-', markerfmt=',', basefmt='')
plt.setp(sl, linewidth=0.6, color=PALETTE[2], alpha=0.7); plt.setp(bl, linewidth=0)
influential = cooks > threshold
ax.scatter(np.where(influential)[0], cooks[influential], color=COLORS['down'], s=25, zorder=5, edgecolor='white')
for idx in np.where(influential)[0]:
    ax.text(idx, cooks[idx]+0.001, f'#{idx}', fontsize=7, ha='center', color=COLORS['down'], fontweight='bold')
ax.axhline(threshold, color=COLORS['down'], linestyle='--', linewidth=1.0, alpha=0.7)
ax.axhspan(threshold, cooks.max()*1.2, color=COLORS['bg_box'], alpha=0.3, zorder=0)
ax.text(n*0.97, threshold+0.001, f'4/n={threshold:.3f}', ha='right', va='bottom', fontsize=8, color=COLORS['down'],
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=COLORS['down'], alpha=0.9))
ax.set_xlabel('Observation Index'); ax.set_ylabel("Cook's Distance")
ax.set_title('(d)', fontsize=12, fontweight='bold', loc='left', pad=3)
ax.grid(alpha=0.15, linestyle='--')

for ax in axes.flat:
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_diagnostics.pdf')
