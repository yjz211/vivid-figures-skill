import numpy as np; from _utils.palette_maps import palette_cmap, palette_stops, contrast_text
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
labels = ['特征A', '特征B', '特征C', '特征D', '特征E', '特征F']
n = len(labels)
# 生成相关矩阵
data = np.random.randn(100, n)
corr = np.corrcoef(data.T)

fig = plt.figure(figsize=(8, 7))
gs = gridspec.GridSpec(2, 2, width_ratios=[1, 6], height_ratios=[1, 6],
                       wspace=0.02, hspace=0.02)

# 顶部树状图
ax_dtop = fig.add_subplot(gs[0, 1])
Z = linkage(pdist(corr), method='ward')
dn = dendrogram(Z, ax=ax_dtop, no_labels=True, color_threshold=0,
                above_threshold_color=PALETTE[0])
ax_dtop.set_xticks([])
ax_dtop.set_yticks([])
for spine in ax_dtop.spines.values():
    spine.set_visible(False)

# 左侧树状图
ax_dleft = fig.add_subplot(gs[1, 0])
dendrogram(Z, ax=ax_dleft, orientation='left', no_labels=True,
           color_threshold=0, above_threshold_color=PALETTE[0])
ax_dleft.set_xticks([])
ax_dleft.set_yticks([])
for spine in ax_dleft.spines.values():
    spine.set_visible(False)

# 主热力图（下三角遮罩）
ax_heat = fig.add_subplot(gs[1, 1])
mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
corr_masked = np.ma.array(corr, mask=mask)

im = ax_heat.imshow(corr_masked, cmap=palette_cmap('diverging'), vmin=-1, vmax=1, aspect='auto')
ax_heat.set_xticks(range(n))
ax_heat.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
ax_heat.set_yticks(range(n))
ax_heat.set_yticklabels(labels, fontsize=9)

# 数值标注（自动对比度）
for i in range(n):
    for j in range(n):
        if not mask[i, j]:
            val = corr[i, j]
            text_color = contrast_text(im.cmap(im.norm(val)))
            ax_heat.text(j, i, f'{val:.2f}', ha='center', va='center',
                         fontsize=7.5, color=text_color, fontweight='bold' if abs(val) > 0.7 else 'normal')

# 遮罩上三角为白色
for i in range(n):
    for j in range(i + 1, n):
        ax_heat.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=True,
                                         facecolor='white', edgecolor='white', zorder=2))

fig.colorbar(im, ax=ax_heat, shrink=0.6, label='相关系数', pad=0.08)
fig.tight_layout()
save_fig(fig, 'figures/fig_heatmap.pdf')
