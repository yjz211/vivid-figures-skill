import numpy as np, matplotlib.pyplot as plt
from scipy.stats import gaussian_kde, norm
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()
np.random.seed(42)
n = 200
actual = np.random.uniform(10, 100, n)
predicted = actual + np.random.normal(0, 5, n)
residuals = predicted - actual
r2 = 1 - np.sum(residuals**2)/np.sum((actual-actual.mean())**2)
rmse = np.sqrt(np.mean(residuals**2))

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 7), height_ratios=[3, 1], sharex=False)
# 上方：预测 vs 实际
ax1.grid(True, linestyle='--', alpha=0.15); ax1.set_axisbelow(True)
kde = gaussian_kde(np.vstack([actual, predicted]))
xg = np.linspace(5, 105, 100); yg = np.linspace(5, 105, 100)
Xg, Yg = np.meshgrid(xg, yg)
Zg = kde(np.vstack([Xg.ravel(), Yg.ravel()])).reshape(Xg.shape)
ax1.contourf(Xg, Yg, Zg, levels=8, cmap='Blues', alpha=0.2, zorder=0)
ax1.scatter(actual, predicted, s=18, alpha=0.5, color=PALETTE[0], edgecolor='white', linewidth=0.3, zorder=2)
ax1.plot([5,105],[5,105], '--', color=COLORS['down'], linewidth=1.2, label='完美拟合线', zorder=3)
ax1.fill_between([5,105],[0,100],[10,110], alpha=0.06, color=PALETTE[0])
ax1.text(0.05, 0.92, f'R² = {r2:.4f}\nRMSE = {rmse:.2f}', transform=ax1.transAxes, fontsize=10,
         verticalalignment='top', bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor=COLORS['grid'], alpha=0.9))
ax1.set_xlabel('实际值', fontsize=11); ax1.set_ylabel('预测值', fontsize=11)
ax1.spines['top'].set_visible(False); ax1.spines['right'].set_visible(False)
ax1.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9)
# 下方：残差分布
ax2.grid(True, linestyle='--', alpha=0.15); ax2.set_axisbelow(True)
ax2.hist(residuals, bins=25, density=True, color=_lighten(PALETTE[0], 0.4), alpha=0.5, edgecolor=PALETTE[0], linewidth=0.8)
xr = np.linspace(residuals.min()-2, residuals.max()+2, 100)
ax2.plot(xr, norm.pdf(xr, residuals.mean(), residuals.std()), color=PALETTE[1], linewidth=2, label='正态拟合')
ax2.axvline(x=0, color=COLORS['ref_line'], linewidth=0.8, linestyle='--')
ax2.set_xlabel('残差', fontsize=11); ax2.set_ylabel('密度', fontsize=11)
ax2.spines['top'].set_visible(False); ax2.spines['right'].set_visible(False)
ax2.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9)
fig.tight_layout()
save_fig(fig, 'figures/fig_pred_vs_actual.pdf')
