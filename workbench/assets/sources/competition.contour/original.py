import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()

x = np.linspace(-3, 3, 100); y = np.linspace(-3, 3, 100)
X, Y = np.meshgrid(x, y)
Z = (1-X)**2 + 100*(Y-X**2)**2  # Rosenbrock 函数
Z = np.log10(Z + 1)

fig, ax = plt.subplots(figsize=(7, 6))
cf = ax.contourf(X, Y, Z, levels=20, cmap='YlOrRd', alpha=0.8)
cs = ax.contour(X, Y, Z, levels=10, colors='white', linewidths=0.5, alpha=0.6)
ax.clabel(cs, inline=True, fontsize=7, fmt='%.1f')

# 最优点
ax.scatter([1], [1], s=100, color=COLORS['down'], edgecolor='white', linewidth=2, zorder=5, marker='*')
ax.annotate('全局最优\n(1.0, 1.0)', xy=(1, 1), xytext=(1.8, 2.2),
            fontsize=9, fontweight='bold', color=COLORS['down'],
            arrowprops=dict(arrowstyle='->', color=COLORS['down'], lw=1.2),
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=COLORS['down'], alpha=0.9))

fig.colorbar(cf, ax=ax, shrink=0.8, label='$\\log_{10}(f+1)$')
ax.set_xlabel('参数 $x_1$', fontsize=11); ax.set_ylabel('参数 $x_2$', fontsize=11)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_contour.pdf')
