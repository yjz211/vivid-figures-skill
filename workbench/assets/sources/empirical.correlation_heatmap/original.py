import numpy as np, matplotlib.pyplot as plt, seaborn as sns; from _utils.palette_maps import palette_cmap, palette_stops, contrast_text
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.stats import pearsonr
from _utils.plot_utils import setup_style, save_fig, COLORS, _lighten
setup_style()

np.random.seed(42)
labels = ['GDP', 'Digital', 'HumanCap', 'Urban', 'FDI', 'R&D']
n_vars = len(labels)
raw = np.random.randn(n_vars, 100)
raw[1] += 0.6*raw[0]; raw[2] += 0.4*raw[0]; raw[4] += 0.5*raw[3]; raw[5] += 0.7*raw[1]
corr = np.corrcoef(raw)

pvals = np.zeros((n_vars, n_vars))
for i in range(n_vars):
    for j in range(n_vars):
        if i != j: _, pvals[i, j] = pearsonr(raw[i], raw[j])

Z = linkage(1 - np.abs(corr), method='ward')
fig = plt.figure(figsize=(10, 9))
gs = fig.add_gridspec(2, 1, height_ratios=[1, 7], hspace=0.02)

# 顶部树状图（只保留顶部，不用左侧，避免挡标签）
ax_dendro = fig.add_subplot(gs[0])
dendrogram(Z, labels=labels, ax=ax_dendro, leaf_rotation=0, color_threshold=0, above_threshold_color=COLORS['ref_line'])
ax_dendro.set_xticks([]); ax_dendro.spines[:].set_visible(False)
ax_dendro.tick_params(left=False, labelleft=False, bottom=False)

ax_heat = fig.add_subplot(gs[1])
mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
sns.heatmap(corr, mask=mask, annot=False, cmap=palette_cmap('diverging'), center=0, square=True,
            linewidths=1.0, linecolor='white', xticklabels=labels, yticklabels=labels,
            cbar_kws={'shrink': 0.7, 'label': 'Correlation'}, ax=ax_heat, vmin=-1, vmax=1)

for i in range(n_vars):
    for j in range(n_vars):
        if j <= i:
            val = corr[i, j]
            p = pvals[i, j] if i != j else 0
            stars = '***' if p < 0.001 else ('**' if p < 0.01 else ('*' if p < 0.05 else ''))
            txt_color = contrast_text(ax_heat.collections[0].cmap(ax_heat.collections[0].norm(val)))
            ax_heat.text(j + 0.5, i + 0.5, f'{val:.2f}{stars}', ha='center', va='center',
                         fontsize=8.5, color=txt_color, fontweight='bold' if i == j else 'normal')

fig.tight_layout()
save_fig(fig, 'figures/fig_corr.pdf')
