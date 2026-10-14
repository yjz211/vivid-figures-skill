import numpy as np, matplotlib.pyplot as plt; from _utils.palette_maps import palette_cmap, palette_stops, contrast_text
import seaborn as sns
from _utils.plot_utils import setup_style, save_fig, PALETTE
setup_style()

np.random.seed(42)
n_vars = 6
var_names = ['人均GDP', '城镇化率', '教育支出', '医疗投入', '交通密度', '产业结构']
data = np.random.randn(100, n_vars)
data[:, 1] = data[:, 0] * 0.8 + np.random.randn(100) * 0.3
data[:, 2] = data[:, 0] * 0.5 + np.random.randn(100) * 0.5
corr = np.corrcoef(data.T)
mask = np.triu(np.ones_like(corr, dtype=bool), k=1)

fig, ax = plt.subplots(figsize=(7, 6))
sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap=palette_cmap('diverging'), center=0,
            vmin=-1, vmax=1, xticklabels=var_names, yticklabels=var_names,
            linewidths=0.5, linecolor='white', square=True,
            cbar_kws={'shrink': 0.8, 'label': '相关系数'}, ax=ax)
ax.set_xticklabels(var_names, fontsize=9, rotation=45, ha='right')
ax.set_yticklabels(var_names, fontsize=9, rotation=0)
[t.set_color(contrast_text(ax.collections[0].cmap(ax.collections[0].norm(float(t.get_text()))))) for t in ax.texts]; fig.tight_layout()
save_fig(fig, 'figures/fig_correlation.pdf')
