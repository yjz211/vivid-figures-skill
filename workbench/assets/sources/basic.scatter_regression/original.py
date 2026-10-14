import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.stats import gaussian_kde
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
n = 150
x = np.random.uniform(1, 10, n)
y = 2.5 * x + np.random.normal(0, 3, n)

fig = plt.figure(figsize=(7, 6))
gs = gridspec.GridSpec(2, 2, width_ratios=[4, 1], height_ratios=[1, 4],
                       wspace=0.05, hspace=0.05)

ax_main = fig.add_subplot(gs[1, 0])
ax_top = fig.add_subplot(gs[0, 0], sharex=ax_main)
ax_right = fig.add_subplot(gs[1, 1], sharey=ax_main)

# KDE 等高线背景
xy = np.vstack([x, y])
kde = gaussian_kde(xy, bw_method=0.3)
xg = np.linspace(x.min() - 1, x.max() + 1, 80)
yg = np.linspace(y.min() - 3, y.max() + 3, 80)
Xg, Yg = np.meshgrid(xg, yg)
Z = kde(np.vstack([Xg.ravel(), Yg.ravel()])).reshape(Xg.shape)
ax_main.contourf(Xg, Yg, Z, levels=8, cmap='Blues', alpha=0.15)
ax_main.contour(Xg, Yg, Z, levels=5, colors=PALETTE[0], alpha=0.2, linewidths=0.5)

# 散点
ax_main.scatter(x, y, s=30, alpha=0.5, color=PALETTE[0], edgecolor='white', linewidth=0.5, zorder=3)

# 拟合线 + 置信带
z = np.polyfit(x, y, 1)
p = np.poly1d(z)
x_fit = np.linspace(x.min(), x.max(), 100)
ax_main.plot(x_fit, p(x_fit), color=PALETTE[1], linewidth=2, zorder=4)
residuals = y - p(x)
se = residuals.std()
for layer, alpha in enumerate([0.15, 0.08, 0.03]):
    ax_main.fill_between(x_fit, p(x_fit) - 1.96 * se * (0.3 + layer * 0.1),
                         p(x_fit) + 1.96 * se * (0.3 + layer * 0.1),
                         alpha=alpha, color=PALETTE[1], linewidth=0)

# R² 标注框
r2 = 1 - np.sum(residuals ** 2) / np.sum((y - y.mean()) ** 2)
ax_main.text(0.05, 0.92, f'R² = {r2:.3f}\ny = {z[0]:.2f}x + {z[1]:.2f}\nn = {n}',
             transform=ax_main.transAxes, fontsize=9, verticalalignment='top',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                       edgecolor=PALETTE[0], alpha=0.9, linewidth=0.8))

# 边际密度（顶部）
kde_x = gaussian_kde(x, bw_method=0.3)
xd = np.linspace(x.min() - 1, x.max() + 1, 200)
ax_top.fill_between(xd, kde_x(xd), alpha=0.2, color=PALETTE[0])
ax_top.plot(xd, kde_x(xd), color=PALETTE[0], linewidth=1.2)
ax_top.set_yticks([])
ax_top.spines['top'].set_visible(False)
ax_top.spines['right'].set_visible(False)
ax_top.spines['left'].set_visible(False)
plt.setp(ax_top.get_xticklabels(), visible=False)

# 边际密度（右侧）
kde_y = gaussian_kde(y, bw_method=0.3)
yd = np.linspace(y.min() - 3, y.max() + 3, 200)
ax_right.fill_betweenx(yd, kde_y(yd), alpha=0.2, color=PALETTE[0])
ax_right.plot(kde_y(yd), yd, color=PALETTE[0], linewidth=1.2)
ax_right.set_xticks([])
ax_right.spines['top'].set_visible(False)
ax_right.spines['right'].set_visible(False)
ax_right.spines['bottom'].set_visible(False)
plt.setp(ax_right.get_yticklabels(), visible=False)

ax_main.set_xlabel('自变量 X', fontsize=11)
ax_main.set_ylabel('因变量 Y', fontsize=11)
ax_main.grid(alpha=0.12, linestyle='--', color=COLORS['grid'])
ax_main.spines['top'].set_visible(False)
ax_main.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_scatter.pdf')
