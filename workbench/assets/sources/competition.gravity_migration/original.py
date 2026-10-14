import numpy as np, matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
np.random.seed(42)

years = np.arange(2010, 2024)
cx = np.cumsum(np.random.normal(0.1, 0.3, len(years))) + 116.4
cy = np.cumsum(np.random.normal(-0.05, 0.2, len(years))) + 39.9

fig, ax = plt.subplots(figsize=(7, 6))
ax.grid(True, linestyle='--', alpha=0.15); ax.set_axisbelow(True)

# KDE 热力背景
kde = gaussian_kde(np.vstack([cx, cy]))
xg = np.linspace(cx.min()-0.5, cx.max()+0.5, 80)
yg = np.linspace(cy.min()-0.5, cy.max()+0.5, 80)
Xg, Yg = np.meshgrid(xg, yg)
Zg = kde(np.vstack([Xg.ravel(), Yg.ravel()])).reshape(Xg.shape)
ax.contourf(Xg, Yg, Zg, levels=8, cmap='Blues', alpha=0.15, zorder=0)

# 轨迹线（带箭头）
for i in range(len(years)-1):
    alpha = 0.3 + 0.7 * i / (len(years)-1)
    ax.annotate('', xy=(cx[i+1], cy[i+1]), xytext=(cx[i], cy[i]),
                arrowprops=dict(arrowstyle='->', color=PALETTE[0], lw=1.5, alpha=alpha))

# 起止点
ax.scatter(cx[0], cy[0], s=120, color=COLORS['up'], edgecolor='white', linewidth=2, zorder=5, label=f'起点 ({years[0]})')
ax.scatter(cx[-1], cy[-1], s=120, color=COLORS['down'], edgecolor='white', linewidth=2, zorder=5, marker='*', label=f'终点 ({years[-1]})')

# 时间标注（只标注首尾和中间几个）
for i in [0, len(years)//3, 2*len(years)//3, len(years)-1]:
    ax.text(cx[i]+0.05, cy[i]+0.05, str(years[i]), fontsize=8, fontweight='bold',
            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))

ax.set_xlabel('经度 (°E)', fontsize=11); ax.set_ylabel('纬度 (°N)', fontsize=11)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='best')
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_centroid_migration.pdf')
