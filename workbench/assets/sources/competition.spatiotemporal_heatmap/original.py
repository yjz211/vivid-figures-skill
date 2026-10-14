import numpy as np, matplotlib.pyplot as plt; from _utils.palette_maps import palette_cmap, palette_stops, contrast_text
import seaborn as sns
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
np.random.seed(42)

regions = ['北京', '上海', '广东', '浙江', '江苏', '四川', '湖北', '山东']
years = [str(y) for y in range(2015, 2024)]
data = np.random.uniform(3, 12, (len(regions), len(years)))
data = np.round(data, 1)

fig, ax = plt.subplots(figsize=(9, 5))
sns.heatmap(data, annot=True, fmt='.1f', cmap=palette_cmap('sequential'),
            xticklabels=years, yticklabels=regions,
            linewidths=0.3, linecolor='white',
            cbar_kws={'label': 'GDP增长率 (%)', 'shrink': 0.8}, ax=ax)
ax.set_xlabel('年份', fontsize=11); ax.set_ylabel('地区', fontsize=11)
ax.set_yticklabels(regions, rotation=0, fontsize=9)
[t.set_color(contrast_text(ax.collections[0].cmap(ax.collections[0].norm(float(t.get_text()))))) for t in ax.texts]; fig.tight_layout()
save_fig(fig, 'figures/fig_spatiotemporal.pdf')
