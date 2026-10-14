import shutil, os
os.makedirs('_utils', exist_ok=True)
for f in ['plot_utils.py', 'china_provinces.geojson']:
    src = os.path.join(os.path.dirname(__file__), f)
    if os.path.exists(src):
        shutil.copy2(src, f'_utils/{f}')

import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

import geopandas as gpd
from libpysal.weights import Queen
from esda.moran import Moran_Local

gdf = gpd.read_file('_utils/china_provinces.geojson')

# 模拟有空间自相关的数据
np.random.seed(42)
gdf['centroid_x'] = gdf.geometry.centroid.x
gdf['value'] = 0.3 + 0.005 * (gdf['centroid_x'] - 80) + np.random.randn(len(gdf)) * 0.08
gdf['value'] = gdf['value'].clip(0.1, 0.95)

# 构建空间权重 + 计算 LISA
w = Queen.from_dataframe(gdf, use_index=False)
w.transform = 'r'
lisa = Moran_Local(gdf['value'].values, w, permutations=999)

# LISA 聚类分类
# lisa.q: 1=HH, 2=LH, 3=LL, 4=HL
# lisa.p_sim: p 值
sig_level = 0.05
gdf['lisa_cluster'] = 'NS'
for i in range(len(gdf)):
    if lisa.p_sim[i] <= sig_level:
        q = lisa.q[i]
        if q == 1: gdf.loc[gdf.index[i], 'lisa_cluster'] = 'HH'
        elif q == 2: gdf.loc[gdf.index[i], 'lisa_cluster'] = 'LH'
        elif q == 3: gdf.loc[gdf.index[i], 'lisa_cluster'] = 'LL'
        elif q == 4: gdf.loc[gdf.index[i], 'lisa_cluster'] = 'HL'

cluster_colors = {
    'HH': '#E25B5B',  # 热点（红色）
    'LL': '#5B8DB8',  # 冷点（蓝色）
    'LH': '#A8C4D8',  # 低高异常（浅蓝）
    'HL': '#E0A0A0',  # 高低异常（浅红）
    'NS': '#F0F0F0',  # 不显著（灰色）
}

from collections import Counter
counts = Counter(gdf['lisa_cluster'])

# === 画图 ===
fig, ax = plt.subplots(figsize=(10, 8))

for cluster_type in ['NS', 'HL', 'LH', 'LL', 'HH']:  # NS 先画，显著的后画
    subset = gdf[gdf['lisa_cluster'] == cluster_type]
    if len(subset) > 0:
        subset.plot(color=cluster_colors[cluster_type], edgecolor='white',
                    linewidth=0.5, ax=ax, zorder=2 if cluster_type != 'NS' else 1)

# 省份简称标注（只标注显著的）
provinces_short = {
    '北京市':'北京','天津市':'天津','河北省':'河北','山西省':'山西',
    '内蒙古自治区':'内蒙古','辽宁省':'辽宁','吉林省':'吉林','黑龙江省':'黑龙江',
    '上海市':'上海','江苏省':'江苏','浙江省':'浙江','安徽省':'安徽',
    '福建省':'福建','江西省':'江西','山东省':'山东','河南省':'河南',
    '湖北省':'湖北','湖南省':'湖南','广东省':'广东','广西壮族自治区':'广西',
    '海南省':'海南','重庆市':'重庆','四川省':'四川','贵州省':'贵州',
    '云南省':'云南','西藏自治区':'西藏','陕西省':'陕西','甘肃省':'甘肃',
    '青海省':'青海','宁夏回族自治区':'宁夏','新疆维吾尔自治区':'新疆',
    '台湾省':'台湾','香港特别行政区':'香港','澳门特别行政区':'澳门',
}

for _, row in gdf[gdf['lisa_cluster'] != 'NS'].iterrows():
    c = row.geometry.centroid
    short = provinces_short.get(row['name'], row['name'][:2])
    # ★ 统一用不透明白底 bbox + 深色文字
    ax.text(c.x, c.y, short, ha='center', va='center', fontsize=6.5,
            fontweight='bold', color='#333333',
            bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                      edgecolor='#999999', linewidth=0.6, alpha=0.92))

# 图例
from matplotlib.patches import Patch
legend_labels = {
    'HH': f'高高聚集 ({counts.get("HH", 0)})',
    'LL': f'低低聚集 ({counts.get("LL", 0)})',
    'LH': f'低高异常 ({counts.get("LH", 0)})',
    'HL': f'高低异常 ({counts.get("HL", 0)})',
    'NS': f'不显著 ({counts.get("NS", 0)})',
}
legend_elements = [Patch(facecolor=cluster_colors[k], edgecolor='white',
                         label=legend_labels[k]) for k in ['HH', 'LL', 'LH', 'HL', 'NS']]
ax.legend(handles=legend_elements, loc='lower left', fontsize=8.5,
          frameon=False, labelspacing=0.35, handlelength=1.6, title=f'LISA 聚类 (p < {sig_level})', title_fontsize=9)

ax.set_xlim(73, 136); ax.set_ylim(17, 54)
ax.set_axis_off()

# Moran's I 全局统计标注
ax.text(0.98, 0.98, f"Global Moran's I = {lisa.Is.mean():.4f}\n999 permutations",
        transform=ax.transAxes, fontsize=8.5, ha='right', va='top',
        bbox=dict(boxstyle='round,pad=0.4', facecolor=COLORS['bg_box'],
                  edgecolor=COLORS['grid'], alpha=0.95))

fig.tight_layout()
save_fig(fig, 'figures/fig_lisa_map.pdf')
