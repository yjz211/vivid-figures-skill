import numpy as np, matplotlib.pyplot as plt; from _utils.palette_maps import palette_cmap, palette_stops, contrast_text
import seaborn as sns
from _utils.plot_utils import setup_style, save_fig, PALETTE
setup_style()

classes = ['类别A', '类别B', '类别C', '类别D']
cm = np.array([[85, 5, 7, 3], [4, 90, 3, 3], [6, 4, 82, 8], [2, 3, 5, 90]])
cm_norm = cm / cm.sum(axis=1, keepdims=True) * 100

fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(cm_norm, annot=True, fmt='.1f', cmap=palette_cmap('sequential'), xticklabels=classes,
            yticklabels=classes, linewidths=0.5, linecolor='white',
            cbar_kws={'label': '预测准确率 (%)'}, ax=ax)
ax.set_xlabel('预测类别', fontsize=11); ax.set_ylabel('真实类别', fontsize=11)
ax.set_xticklabels(classes, fontsize=10); ax.set_yticklabels(classes, fontsize=10, rotation=0)
[t.set_color(contrast_text(ax.collections[0].cmap(ax.collections[0].norm(float(t.get_text()))))) for t in ax.texts]; fig.tight_layout()
save_fig(fig, 'figures/fig_confusion_matrix.pdf')
