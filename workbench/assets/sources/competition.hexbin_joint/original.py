import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
np.random.seed(42)

n = 2000
x = np.random.normal(0, 2, n)
y = 0.5*x + np.random.normal(0, 1.5, n)

fig = plt.figure(figsize=(7, 7))
gs = gridspec.GridSpec(2, 2, width_ratios=[4, 1], height_ratios=[1, 4],
                       hspace=0.05, wspace=0.05)
ax_main = fig.add_subplot(gs[1, 0])
ax_top = fig.add_subplot(gs[0, 0], sharex=ax_main)
ax_right = fig.add_subplot(gs[1, 1], sharey=ax_main)

# 主图：hexbin
hb = ax_main.hexbin(x, y, gridsize=25, cmap='YlOrRd', mincnt=1, edgecolors='white', linewidths=0.3)
# 回归线
z = np.polyfit(x, y, 1)
p = np.poly1d(z)
x_line = np.linspace(x.min(), x.max(), 100)
ax_main.plot(x_line, p(x_line), '--', color=PALETTE[1], linewidth=1.8,
            label=f'$\\hat{{Y}}={z[0]:.3f}X{z[1]:+.1f}$')
ax_main.legend(loc='lower right', fontsize=9, framealpha=0.9)
ax_main.set_xlabel('X 变量', fontsize=11); ax_main.set_ylabel('Y 变量', fontsize=11)

# 上方直方图
ax_top.hist(x, bins=40, color=PALETTE[0], alpha=0.5, edgecolor='white', linewidth=0.5)
plt.setp(ax_top.get_xticklabels(), visible=False)
ax_top.set_ylabel('频数', fontsize=9)

# 右方直方图
ax_right.hist(y, bins=40, orientation='horizontal', color=PALETTE[1], alpha=0.5,
             edgecolor='white', linewidth=0.5)
plt.setp(ax_right.get_yticklabels(), visible=False)
ax_right.set_xlabel('频数', fontsize=9)

for a in [ax_main, ax_top, ax_right]:
    a.spines['top'].set_visible(False); a.spines['right'].set_visible(False)

fig.colorbar(hb, ax=ax_right, shrink=0.6, label='样本数')
fig.tight_layout()
save_fig(fig, 'figures/fig_hexbin_joint.pdf')
