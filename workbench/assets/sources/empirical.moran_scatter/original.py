import shutil, os
os.makedirs('_utils', exist_ok=True)
for f in ['plot_utils.py', 'china_provinces.geojson']:
    src = os.path.join(os.path.dirname(__file__), f)
    if os.path.exists(src):
        shutil.copy2(src, f'_utils/{f}')

import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten, smart_labels
setup_style()

import geopandas as gpd
from libpysal.weights import Queen
from esda.moran import Moran

# === 加载中国省级 GeoJSON + 模拟数据 ===
gdf = gpd.read_file('_utils/china_provinces.geojson')

np.random.seed(42)
# 模拟一个有空间自相关的变量（东部高、西部低）
gdf['centroid_x'] = gdf.geometry.centroid.x
gdf['value'] = 0.3 + 0.005 * (gdf['centroid_x'] - 80) + np.random.randn(len(gdf)) * 0.08
gdf['value'] = gdf['value'].clip(0.1, 0.95)

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
gdf['short_name'] = gdf['name'].map(provinces_short).fillna(gdf['name'])

# === 用 libpysal 构建空间权重矩阵，用 esda 计算 Moran's I ===
w = Queen.from_dataframe(gdf)
w.transform = 'r'  # 行标准化

y = gdf['value'].values
moran = Moran(y, w)

# 标准化变量和空间滞后
z = (y - y.mean()) / y.std()
wz = np.array([np.sum(w.weights[i] * z[list(w.neighbors[i])]) for i in range(len(z))])

# === 画图 ===
fig, ax = plt.subplots(figsize=(7, 6.5))

xlim = (z.min() - 0.8, z.max() + 0.8)
ylim = (wz.min() - 0.8, wz.max() + 0.8)

# 象限背景
ax.fill_between([0, xlim[1]], 0, ylim[1], alpha=0.06, color=PALETTE[0], zorder=0)
ax.fill_between([xlim[0], 0], ylim[0], 0, alpha=0.06, color=PALETTE[1], zorder=0)
ax.fill_between([xlim[0], 0], 0, ylim[1], alpha=0.06, color=PALETTE[2], zorder=0)
ax.fill_between([0, xlim[1]], ylim[0], 0, alpha=0.06, color=PALETTE[3], zorder=0)

ax.axhline(0, color=COLORS['grid'], linewidth=0.8, zorder=1)
ax.axvline(0, color=COLORS['grid'], linewidth=0.8, zorder=1)

# 散点（按象限着色）
for i in range(len(z)):
    if z[i] >= 0 and wz[i] >= 0: c = PALETTE[0]
    elif z[i] < 0 and wz[i] < 0: c = PALETTE[1]
    elif z[i] < 0 and wz[i] >= 0: c = PALETTE[2]
    else: c = PALETTE[3]
    ax.scatter(z[i], wz[i], c=c, s=60, edgecolors='white', linewidths=0.8, zorder=3, alpha=0.85)

# OLS 拟合线（斜率 = Moran's I）
x_fit = np.linspace(xlim[0], xlim[1], 100)
ax.plot(x_fit, moran.I * x_fit, '--', color=COLORS['text'], linewidth=1.2, alpha=0.6, zorder=2)

# 象限标签
ax.text(xlim[1] - 0.2, ylim[1] - 0.2, 'HH', fontsize=14, ha='right', va='top',
        color=PALETTE[0], fontweight='bold', alpha=0.4)
ax.text(xlim[0] + 0.2, ylim[0] + 0.2, 'LL', fontsize=14, ha='left', va='bottom',
        color=PALETTE[1], fontweight='bold', alpha=0.4)
ax.text(xlim[0] + 0.2, ylim[1] - 0.2, 'LH', fontsize=14, ha='left', va='top',
        color=PALETTE[2], fontweight='bold', alpha=0.4)
ax.text(xlim[1] - 0.2, ylim[0] + 0.2, 'HL', fontsize=14, ha='right', va='bottom',
        color=PALETTE[3], fontweight='bold', alpha=0.4)

# 标注离回归线最远的省份
residuals = np.abs(wz - moran.I * z)
top_idx = np.argsort(residuals)[-7:]
for i in top_idx:
    ax.annotate(gdf['short_name'].iloc[i], xy=(z[i], wz[i]),
                xytext=(6, 4), textcoords='offset points',
                fontsize=7.5, color=COLORS['text'],
                bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                          edgecolor=COLORS['grid'], alpha=0.85))

# Moran's I 标注
sig = '***' if moran.p_sim < 0.01 else '**' if moran.p_sim < 0.05 else '*' if moran.p_sim < 0.1 else ''
ax.text(0.03, 0.97, f"Moran's I = {moran.I:.4f}{sig}\np = {moran.p_sim:.4f}\n(999 permutations)",
        transform=ax.transAxes, fontsize=9, va='top',
        bbox=dict(boxstyle='round,pad=0.4', facecolor=COLORS['bg_box'],
                  edgecolor=COLORS['grid'], alpha=0.95))

ax.set_xlabel('标准化变量 (z)', fontsize=11)
ax.set_ylabel('空间滞后 (Wz)', fontsize=11)
ax.set_xlim(xlim); ax.set_ylim(ylim)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_moran_scatter.pdf')
