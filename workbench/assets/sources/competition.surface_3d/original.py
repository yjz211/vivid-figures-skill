import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()

x = np.linspace(-3, 3, 100); y = np.linspace(-3, 3, 100)
X, Y = np.meshgrid(x, y)
Z = np.sin(X)*np.cos(Y) + 0.5*np.sin(2*X)*np.cos(2*Y) + np.random.normal(0, 0.02, X.shape)

fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection='3d')
surf = ax.plot_surface(X, Y, Z, cmap='coolwarm', alpha=0.85, edgecolor='none', antialiased=True)
ax.contour(X, Y, Z, zdir='z', offset=Z.min()-0.3, cmap='coolwarm', alpha=0.3, levels=15)

# 最优点标注
min_idx = np.unravel_index(Z.argmin(), Z.shape)
ax.scatter([X[min_idx]], [Y[min_idx]], [Z[min_idx]], color=COLORS['down'], s=80,
           edgecolor='white', linewidth=1.5, zorder=10, label=f'最优点 ({X[min_idx]:.1f}, {Y[min_idx]:.1f})')

ax.set_xlabel('参数 $x_1$', fontsize=10, labelpad=6)
ax.set_ylabel('参数 $x_2$', fontsize=10, labelpad=6)
ax.set_zlabel('目标函数值', fontsize=10, labelpad=6)
ax.view_init(elev=30, azim=135); ax.tick_params(labelsize=8)
ax.legend(fontsize=9, loc='best')
fig.colorbar(surf, shrink=0.45, aspect=15, pad=0.12)
fig.tight_layout()
save_fig(fig, 'figures/fig_3d_surface.pdf')
