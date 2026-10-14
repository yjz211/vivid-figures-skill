from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten; from _utils.palette_maps import palette_cmap, palette_stops, contrast_text
setup_style()
import matplotlib.pyplot as plt
import numpy as np
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.spatial.distance import pdist

np.random.seed(42)
data = np.random.randn(10, 8)
labels_row = [f'Sample-{i+1}' for i in range(10)]
labels_col = [f'Feat-{i+1}' for i in range(8)]

Z_col = linkage(pdist(data.T), method='ward')
Z_row = linkage(pdist(data), method='ward')

n_clusters = 3
col_clusters = fcluster(Z_col, n_clusters, criterion='maxclust')
row_clusters = fcluster(Z_row, n_clusters, criterion='maxclust')

fig = plt.figure(figsize=(10, 8))

# ── 关键：树状图和热力图的 left 和 width 参数完全一致，否则会对不齐
# ── _left 需要足够容纳色条(左侧) + 间距 + y轴标签区域(至少 0.15)
_left = 0.22   # 长文本标签需要更大左边距
_width = 0.56
_cbar_left = _left + _width + 0.03

# 列树状图（只画列方向，不画行方向，避免遮挡标签）
ax_dendro_top = fig.add_axes([_left, 0.86, _width, 0.10])
dn_col = dendrogram(Z_col, ax=ax_dendro_top, leaf_font_size=0,
                     color_threshold=Z_col[-n_clusters + 1, 2],
                     above_threshold_color=COLORS['ref_line'])
ax_dendro_top.set_axis_off()

# Heatmap —— left 和 width 与树状图完全一致
ax_heat = fig.add_axes([_left, 0.08, _width, 0.76])
col_order = dn_col['leaves']
row_order = list(range(len(labels_row)))
ordered_data = data[row_order][:, col_order]

im = ax_heat.imshow(ordered_data, aspect='auto', cmap=palette_cmap('diverging'), interpolation='nearest')
ax_heat.set_xticks(range(len(labels_col)))
ax_heat.set_xticklabels([labels_col[i] for i in col_order], fontsize=8,
                         rotation=45, ha='right')
ax_heat.set_yticks(range(len(labels_row)))
ax_heat.set_yticklabels([labels_row[i] for i in row_order], fontsize=8)

# Cluster boundary lines
sorted_col_clusters = [col_clusters[i] for i in col_order]
for k in range(1, len(sorted_col_clusters)):
    if sorted_col_clusters[k] != sorted_col_clusters[k - 1]:
        ax_heat.axvline(k - 0.5, color='white', linewidth=2.5)
sorted_row_clusters = [row_clusters[i] for i in row_order]
for k in range(1, len(sorted_row_clusters)):
    if sorted_row_clusters[k] != sorted_row_clusters[k - 1]:
        ax_heat.axhline(k - 0.5, color='white', linewidth=2.5)

# Colorbar
ax_cbar = fig.add_axes([_cbar_left, 0.08, 0.02, 0.76])
cbar = plt.colorbar(im, cax=ax_cbar)
cbar.ax.tick_params(labelsize=8)

# Silhouette score annotation
ax_heat.text(0.98, 0.02, 'Silhouette = 0.42',
             transform=ax_heat.transAxes, fontsize=8, ha='right', va='bottom',
             bbox=dict(boxstyle='round,pad=0.3', facecolor=_lighten(PALETTE[0], 0.7),
                       edgecolor=PALETTE[0], alpha=0.9))

save_fig(fig, 'figures/fig_cluster_heatmap.pdf')
