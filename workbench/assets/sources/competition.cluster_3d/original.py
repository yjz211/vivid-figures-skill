import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
np.random.seed(42)

# 生成 3D 聚类数据
centers = np.array([[2,3,4], [6,2,7], [4,7,2], [8,6,5]])
n_per = 60
X = np.vstack([c + np.random.randn(n_per, 3)*0.8 for c in centers])
labels = np.repeat(range(4), n_per)

fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection='3d')

for k in range(4):
    mask = labels == k
    ax.scatter(X[mask,0], X[mask,1], X[mask,2], s=20, alpha=0.5,
              color=PALETTE[k], edgecolor='white', linewidth=0.3, label=f'簇 {k+1}')
    ax.scatter(*centers[k], s=150, color=PALETTE[k], marker='X',
              edgecolor='white', linewidth=2, zorder=5)

ax.set_xlabel('维度 1', fontsize=11, labelpad=6)
ax.set_ylabel('维度 2', fontsize=11, labelpad=6)
ax.set_zlabel('维度 3', fontsize=11, labelpad=8)
ax.view_init(elev=20, azim=45)
ax.legend(loc='upper left', fontsize=10, framealpha=0.9)
fig.tight_layout()
save_fig(fig, 'figures/fig_3d_cluster.pdf')
