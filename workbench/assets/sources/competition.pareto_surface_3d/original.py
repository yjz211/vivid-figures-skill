import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
np.random.seed(42)

# 生成三目标 Pareto 前沿
n = 200
t1 = np.random.uniform(0, 1, n)
t2 = np.random.uniform(0, 1-t1, n)
f1 = t1 + 0.05*np.random.randn(n)
f2 = t2 + 0.05*np.random.randn(n)
f3 = 1 - t1 - t2 + 0.05*np.random.randn(n)
f1, f2, f3 = np.clip(f1, 0, 1), np.clip(f2, 0, 1), np.clip(f3, 0, 1)

# 非 Pareto 解
other_f1 = np.random.uniform(0.2, 1.0, 100)
other_f2 = np.random.uniform(0.2, 1.0, 100)
other_f3 = np.random.uniform(0.2, 1.0, 100)

fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection='3d')
# 非支配解
ax.scatter(other_f1, other_f2, other_f3, s=8, alpha=0.15, color=COLORS['neutral'])
# Pareto 前沿
sc = ax.scatter(f1, f2, f3, c=f3, cmap='coolwarm', s=25, alpha=0.7,
                edgecolor='white', linewidth=0.3, zorder=3)

ax.set_xlabel('目标 f₁', fontsize=10, labelpad=6)
ax.set_ylabel('目标 f₂', fontsize=10, labelpad=6)
ax.set_zlabel('目标 f₃', fontsize=10, labelpad=8)
ax.view_init(elev=25, azim=135); ax.tick_params(labelsize=8)
ax.legend(fontsize=9, loc='best')
fig.colorbar(sc, shrink=0.5, aspect=15, pad=0.1, label='f₃ 值')
fig.tight_layout()
save_fig(fig, 'figures/fig_pareto_3d.pdf')
