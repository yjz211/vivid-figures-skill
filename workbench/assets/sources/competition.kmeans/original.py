import numpy as np, matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from sklearn.datasets import make_blobs
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
np.random.seed(42)

X, y_true = make_blobs(n_samples=300, centers=4, cluster_std=1.0)
from sklearn.cluster import KMeans
km = KMeans(n_clusters=4, random_state=42, n_init=10).fit(X)
labels = km.labels_
centers = km.cluster_centers_

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# 左图：聚类散点
for k in range(4):
    mask = labels == k
    ax1.scatter(X[mask, 0], X[mask, 1], s=20, alpha=0.5, color=PALETTE[k],
               edgecolor='white', linewidth=0.3, label=f'簇 {k+1}')
ax1.scatter(centers[:, 0], centers[:, 1], s=200, color=COLORS['text'], marker='X',
           edgecolor='white', linewidth=2, zorder=5, label='质心')
ax1.set_xlabel('特征维度 1', fontsize=11); ax1.set_ylabel('特征维度 2', fontsize=11)
ax1.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8, loc='best')
ax1.spines['top'].set_visible(False); ax1.spines['right'].set_visible(False)

# 右图：轮廓系数
from sklearn.metrics import silhouette_samples
sil = silhouette_samples(X, labels)
y_lower = 0
for k in range(4):
    cluster_sil = np.sort(sil[labels == k])
    y_upper = y_lower + len(cluster_sil)
    ax2.fill_betweenx(np.arange(y_lower, y_upper), 0, cluster_sil,
                       alpha=0.5, color=PALETTE[k])
    ax2.text(-0.05, y_lower + 0.5 * len(cluster_sil), f'簇{k+1}',
            fontsize=9, fontweight='bold', color=PALETTE[k])
    y_lower = y_upper + 5
avg_sil = np.mean(sil)
ax2.axvline(avg_sil, color=COLORS['down'], linewidth=1.5, linestyle='--',
           label=f'平均轮廓系数={avg_sil:.3f}')
ax2.set_xlabel('轮廓系数', fontsize=11); ax2.set_ylabel('样本索引', fontsize=11)
ax2.legend(fontsize=8, loc='best')
ax2.spines['top'].set_visible(False); ax2.spines['right'].set_visible(False)

fig.tight_layout()
save_fig(fig, 'figures/fig_kmeans_dual.pdf')
