import numpy as np, matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
np.random.seed(42)

n = 300
x = np.concatenate([np.random.normal(3, 1, n//2), np.random.normal(7, 1.5, n//2)])
y = np.concatenate([np.random.normal(5, 1.2, n//2), np.random.normal(3, 1, n//2)])

fig, ax = plt.subplots(figsize=(7, 6))
# KDE 等高线
kde = gaussian_kde(np.vstack([x, y]))
xg = np.linspace(x.min()-1, x.max()+1, 100)
yg = np.linspace(y.min()-1, y.max()+1, 100)
Xg, Yg = np.meshgrid(xg, yg)
Zg = kde(np.vstack([Xg.ravel(), Yg.ravel()])).reshape(Xg.shape)
ax.contourf(Xg, Yg, Zg, levels=10, cmap='Blues', alpha=0.3)
ax.contour(Xg, Yg, Zg, levels=6, colors=PALETTE[0], linewidths=0.8, alpha=0.5)

# 散点
ax.scatter(x, y, s=12, alpha=0.4, color=PALETTE[0], edgecolor='white', linewidth=0.3)

ax.set_xlabel('变量 X', fontsize=11); ax.set_ylabel('变量 Y', fontsize=11)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_bubble_kde.pdf')
