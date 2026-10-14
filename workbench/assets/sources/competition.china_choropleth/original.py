import os, sys, shutil, json
import numpy as np, matplotlib.pyplot as plt
import matplotlib.colors as mc
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.colors import Normalize

# 初始化 _utils
os.makedirs('_utils', exist_ok=True)
for src in ['plot_utils.py', 'china_provinces.geojson']:
    for search in ['skills/shared-scripts', '../skills/shared-scripts']:
        p = os.path.join(search, src)
        if os.path.isfile(p):
            shutil.copy2(p, f'_utils/{src}'); break
sys.path.insert(0, '.')
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

# ★ 加载 GeoJSON（优先本地，否则自动下载）
GEOJSON = '_utils/china_provinces.geojson'
if not os.path.exists(GEOJSON):
    import urllib.request
    url = "https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json"
    urllib.request.urlretrieve(url, GEOJSON)

with open(GEOJSON, 'r', encoding='utf-8') as f:
    geojson_data = json.load(f)

# ★ 模拟数据（实际使用时替换为 JSON 读取）
province_values = {
    '北京市': 0.85, '天津市': 0.72, '河北省': 0.55, '山西省': 0.48,
    '内蒙古自治区': 0.52, '辽宁省': 0.58, '吉林省': 0.50, '黑龙江省': 0.47,
    '上海市': 0.88, '江苏省': 0.78, '浙江省': 0.82, '安徽省': 0.56,
    '福建省': 0.68, '江西省': 0.51, '山东省': 0.65, '河南省': 0.54,
    '湖北省': 0.60, '湖南省': 0.57, '广东省': 0.75, '广西壮族自治区': 0.45,
    '海南省': 0.53, '重庆市': 0.62, '四川省': 0.58, '贵州省': 0.40,
    '云南省': 0.42, '西藏自治区': 0.35, '陕西省': 0.55, '甘肃省': 0.38,
    '青海省': 0.36, '宁夏回族自治区': 0.43, '新疆维吾尔自治区': 0.44,
    '台湾省': 0.70, '香港特别行政区': 0.80, '澳门特别行政区': 0.78,
}

# 检测 geopandas 是否可用
try:
    import geopandas as gpd
    HAS_GPD = True
except ImportError:
    HAS_GPD = False

fig, ax = plt.subplots(figsize=(10, 8))
vmin, vmax = 0.3, 0.9
cmap = plt.cm.YlOrRd
norm = Normalize(vmin=vmin, vmax=vmax)

if HAS_GPD:
    # ===== 方案 A：geopandas（推荐） =====
    gdf = gpd.read_file(GEOJSON)
    gdf['value'] = gdf['name'].map(province_values)
    gdf_valid = gdf[gdf['value'].notna()]
    gdf_no_data = gdf[gdf['value'].isna()]
    gdf_valid.plot(column='value', cmap='YlOrRd', linewidth=0.5,
                   edgecolor='white', ax=ax, legend=False, vmin=vmin, vmax=vmax)
    if len(gdf_no_data) > 0:
        gdf_no_data.plot(color='#F0F0F0', edgecolor='white', linewidth=0.5, ax=ax)
    # 省份标注
    major = ['北京市','上海市','广东省','浙江省','四川省','新疆维吾尔自治区',
             '西藏自治区','黑龙江省','云南省','湖北省']
    for _, row in gdf_valid.iterrows():
        if row['name'] in major:
            c = row.geometry.centroid
            v = row['value']
            short = row['name'][:2]
            ax.text(c.x, c.y, f'{short}\n{v:.2f}', ha='center', va='center',
                    fontsize=7, fontweight='bold', color='#333333',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                              edgecolor='#999999', linewidth=0.6, alpha=0.92))
else:
    # ===== 方案 B：纯 matplotlib（不依赖 geopandas，同样有省份轮廓） =====
    def _extract_polygons(geometry):
        """从 GeoJSON geometry 提取所有 polygon 坐标环"""
        polys = []
        gtype = geometry['type']
        if gtype == 'Polygon':
            for ring in geometry['coordinates']:
                polys.append(np.array(ring))
        elif gtype == 'MultiPolygon':
            for polygon in geometry['coordinates']:
                for ring in polygon:
                    polys.append(np.array(ring))
        return polys

    for feature in geojson_data['features']:
        name = feature['properties'].get('name', '')
        val = province_values.get(name)
        polys = _extract_polygons(feature['geometry'])
        for coords in polys:
            if len(coords) < 3:
                continue
            if val is not None:
                color = cmap(norm(val))
            else:
                color = '#F0F0F0'
            patch = MplPolygon(coords[:, :2], closed=True,
                               facecolor=color, edgecolor='white',
                               linewidth=0.5, zorder=2)
            ax.add_patch(patch)

    # 省份标注（用质心近似）
    major_short = {'北京市':'北京','上海市':'上海','广东省':'广东','浙江省':'浙江',
                   '四川省':'四川','新疆维吾尔自治区':'新疆','西藏自治区':'西藏',
                   '黑龙江省':'黑龙','云南省':'云南','湖北省':'湖北'}
    for feature in geojson_data['features']:
        name = feature['properties'].get('name', '')
        if name not in major_short:
            continue
        val = province_values.get(name)
        if val is None:
            continue
        # 计算质心
        all_coords = []
        for poly in _extract_polygons(feature['geometry']):
            all_coords.extend(poly.tolist())
        if not all_coords:
            continue
        arr = np.array(all_coords)
        cx, cy = arr[:, 0].mean(), arr[:, 1].mean()
        short = major_short[name]
        ax.text(cx, cy, f'{short}\n{val:.2f}', ha='center', va='center',
                fontsize=7, fontweight='bold', color='#333333',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                          edgecolor='#999999', linewidth=0.6, alpha=0.92))
    ax.set_aspect('equal')
    ax.autoscale_view()

# Colorbar
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, shrink=0.6, pad=0.02, aspect=20)
cbar.set_label('指标值', fontsize=11)
cbar.ax.tick_params(labelsize=9)

ax.set_xlim(73, 136); ax.set_ylim(17, 54)
ax.set_axis_off()
fig.tight_layout()
save_fig(fig, 'figures/fig_china_map.pdf')
