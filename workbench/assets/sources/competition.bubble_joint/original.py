import numpy as np, matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
np.random.seed(42)

n = 150
x = np.random.normal(5, 2, n)
y = 0.6*x + np.random.normal(0, 1.5, n)
z = np.random.uniform(10, 80, n)

fig = plt.figure(figsize=(7, 7))
gs = fig.add_gridspec(2, 2, width_ratios=[4, 1], height_ratios=[1, 4],
                      hspace=0.05, wspace=0.05)
ax_main = fig.add_subplot(gs[1, 0])
ax_top = fig.add_subplot(gs[0, 0], sharex=ax_main)
ax_right = fig.add_subplot(gs[1, 1], sharey=ax_main)

# 主图：气泡
sc = ax_main.scatter(x, y, s=z*3, c=z, cmap='YlOrRd', alpha=0.6,
                     edgecolor='white', linewidth=0.5)
ax_main.set_xlabel('变量 X', fontsize=11); ax_main.set_ylabel('变量 Y', fontsize=11)

# 上方 KDE
kde_x = gaussian_kde(x)
xx = np.linspace(x.min()-1, x.max()+1, 200)
ax_top.fill_between(xx, kde_x(xx), alpha=0.3, color=PALETTE[0])
ax_top.plot(xx, kde_x(xx), color=PALETTE[0], linewidth=1.5)
ax_top.set_ylabel('密度', fontsize=9)
plt.setp(ax_top.get_xticklabels(), visible=False)

# 右方 KDE
kde_y = gaussian_kde(y)
yy = np.linspace(y.min()-1, y.max()+1, 200)
ax_right.fill_betweenx(yy, kde_y(yy), alpha=0.3, color=PALETTE[1])
ax_right.plot(kde_y(yy), yy, color=PALETTE[1], linewidth=1.5)
ax_right.set_xlabel('密度', fontsize=9)
plt.setp(ax_right.get_yticklabels(), visible=False)

for a in [ax_main, ax_top, ax_right]:
    a.spines['top'].set_visible(False); a.spines['right'].set_visible(False)

fig.colorbar(sc, ax=ax_right, shrink=0.6, label='气泡大小 Z')
fig.tight_layout()
save_fig(fig, 'figures/fig_bubble_joint.pdf')
