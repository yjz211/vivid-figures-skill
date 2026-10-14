import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.stats import gaussian_kde
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
np.random.seed(42)

n = 500
x = np.concatenate([np.random.normal(2, 1, n//2), np.random.normal(6, 1.5, n//2)])
y = np.concatenate([np.random.normal(4, 1, n//2), np.random.normal(7, 1.2, n//2)])

fig = plt.figure(figsize=(7, 7))
gs = gridspec.GridSpec(2, 2, width_ratios=[4, 1], height_ratios=[1, 4],
                       hspace=0.05, wspace=0.05)
ax_main = fig.add_subplot(gs[1, 0])
ax_top = fig.add_subplot(gs[0, 0], sharex=ax_main)
ax_right = fig.add_subplot(gs[1, 1], sharey=ax_main)

# KDE 热力
kde = gaussian_kde(np.vstack([x, y]))
xg = np.linspace(x.min()-1, x.max()+1, 100)
yg = np.linspace(y.min()-1, y.max()+1, 100)
Xg, Yg = np.meshgrid(xg, yg)
Zg = kde(np.vstack([Xg.ravel(), Yg.ravel()])).reshape(Xg.shape)
ax_main.contourf(Xg, Yg, Zg, levels=12, cmap='Blues', alpha=0.5)
ax_main.scatter(x, y, s=8, alpha=0.3, color=PALETTE[0], edgecolor='none')

# 回归线
z = np.polyfit(x, y, 1)
p = np.poly1d(z)
x_line = np.linspace(x.min(), x.max(), 100)
se_line = np.std(y - p(x)) * np.sqrt(1/n + (x_line - x.mean())**2 / np.sum((x - x.mean())**2))
ax_main.plot(x_line, p(x_line), '--', color=PALETTE[1], linewidth=2, label='回归线')
ax_main.fill_between(x_line, p(x_line) - 1.96*se_line, p(x_line) + 1.96*se_line,
                     alpha=0.15, color=PALETTE[1])
ax_main.legend(loc='upper left', fontsize=10, framealpha=0.9)
ax_main.set_xlabel('X 变量', fontsize=11); ax_main.set_ylabel('Y 变量', fontsize=11)

# 边际 KDE
kde_x = gaussian_kde(x)
xx = np.linspace(x.min()-1, x.max()+1, 200)
ax_top.fill_between(xx, kde_x(xx), alpha=0.3, color=PALETTE[0])
ax_top.plot(xx, kde_x(xx), color=PALETTE[0], linewidth=1.5)
plt.setp(ax_top.get_xticklabels(), visible=False)

kde_y = gaussian_kde(y)
yy = np.linspace(y.min()-1, y.max()+1, 200)
ax_right.fill_betweenx(yy, kde_y(yy), alpha=0.3, color=PALETTE[1])
ax_right.plot(kde_y(yy), yy, color=PALETTE[1], linewidth=1.5)
plt.setp(ax_right.get_yticklabels(), visible=False)

for a in [ax_main, ax_top, ax_right]:
    a.spines['top'].set_visible(False); a.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_kde_joint.pdf')
