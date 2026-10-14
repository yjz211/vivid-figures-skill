import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.stats import gaussian_kde
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
np.random.seed(42)

n = 300
x = np.random.uniform(1, 10, n)
y = 2.5*x + np.random.normal(0, 3, n)

fig = plt.figure(figsize=(7, 7))
gs = gridspec.GridSpec(2, 2, width_ratios=[4, 1], height_ratios=[1, 4],
                       hspace=0.05, wspace=0.05)
ax_main = fig.add_subplot(gs[1, 0])
ax_top = fig.add_subplot(gs[0, 0], sharex=ax_main)
ax_right = fig.add_subplot(gs[1, 1], sharey=ax_main)

ax_main.scatter(x, y, s=15, alpha=0.4, color=PALETTE[0], edgecolor='white', linewidth=0.3)
z = np.polyfit(x, y, 1); p = np.poly1d(z)
x_line = np.linspace(x.min(), x.max(), 100)
ax_main.plot(x_line, p(x_line), '--', color=PALETTE[1], linewidth=2, label=f'y={z[0]:.2f}x{z[1]:+.1f}')
ax_main.legend(loc='upper left', fontsize=9)
ax_main.set_xlabel('X 变量', fontsize=11); ax_main.set_ylabel('Y 变量', fontsize=11)

kde_x = gaussian_kde(x)
xx = np.linspace(x.min()-0.5, x.max()+0.5, 200)
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
save_fig(fig, 'figures/fig_scatter_marginal.pdf')
