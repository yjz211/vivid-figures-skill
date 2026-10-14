import numpy as np; from _utils.vivid_config import palette_colors
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.colors import LinearSegmentedColormap
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style(); scale_colors = palette_colors()
np.random.seed(42)

# === 模拟 2 个变量在 30×30 网格上的取值 ===
N = 30
y, x = np.mgrid[0:N, 0:N]
var_a = np.exp(-((x - 10)**2 + (y - 12)**2) / 100) + 0.3 * np.random.rand(N, N)
var_b = np.exp(-((x - 20)**2 + (y - 22)**2) / 120) + 0.3 * np.random.rand(N, N)
var_a = (var_a - var_a.min()) / (var_a.max() - var_a.min())
var_b = (var_b - var_b.min()) / (var_b.max() - var_b.min())

# === 3×3 双变量配色（X 维度用 scale_colors[0] 渐变，Y 维度用 scale_colors[1] 渐变，组合产生中间色）===
def bivariate_color(a, b):
    """a, b in [0,1] -> RGB. 用两个主色的加权混合。"""
    c1 = np.array([int(scale_colors[0].lstrip('#')[i:i+2], 16)/255 for i in (0,2,4)])  # 蓝
    c2 = np.array([int(scale_colors[1].lstrip('#')[i:i+2], 16)/255 for i in (0,2,4)])  # 橙
    base = np.array([0.97, 0.97, 0.97])  # 浅灰底
    return base * (1 - 0.5*a - 0.5*b) + c1 * 0.5*a + c2 * 0.5*b

# 量化到 3×3 等级
qa = np.clip(np.digitize(var_a, np.quantile(var_a, [0.33, 0.67])), 0, 2)
qb = np.clip(np.digitize(var_b, np.quantile(var_b, [0.33, 0.67])), 0, 2)

# 构造 RGB 图像
rgb = np.zeros((N, N, 3))
for i in range(N):
    for j in range(N):
        rgb[i, j] = bivariate_color(qa[i, j] / 2, qb[i, j] / 2)

# === 主图 + 右下小图例（3×3 矩阵）===
fig = plt.figure(figsize=(7.5, 5))
gs = GridSpec(1, 2, width_ratios=[3, 1], wspace=0.15)
ax_main = fig.add_subplot(gs[0, 0])
ax_main.imshow(rgb, origin='lower', interpolation='nearest')
ax_main.set_xlabel('经度网格', fontsize=10)
ax_main.set_ylabel('纬度网格', fontsize=10)
ax_main.set_title('双变量空间分布', fontsize=11, color=COLORS['text'], pad=6)
ax_main.tick_params(labelsize=8)
for sp in ax_main.spines.values(): sp.set_edgecolor(COLORS['grid']); sp.set_linewidth(0.5)

# === 3×3 图例矩阵 ===
ax_leg = fig.add_subplot(gs[0, 1])
legend_grid = np.zeros((3, 3, 3))
for i in range(3):
    for j in range(3):
        legend_grid[2-i, j] = bivariate_color(j / 2, i / 2)
ax_leg.imshow(legend_grid, origin='lower', interpolation='nearest')
ax_leg.set_xticks([0, 1, 2]); ax_leg.set_yticks([0, 1, 2])
ax_leg.set_xticklabels(['低', '中', '高'], fontsize=8)
ax_leg.set_yticklabels(['低', '中', '高'], fontsize=8)
ax_leg.set_xlabel('变量 A →', fontsize=9, color=scale_colors[0], fontweight='bold')
ax_leg.set_ylabel('变量 B →', fontsize=9, color=scale_colors[1], fontweight='bold')
ax_leg.set_title('图例', fontsize=9, color=COLORS['text'], pad=4)
for sp in ax_leg.spines.values(): sp.set_edgecolor(COLORS['grid']); sp.set_linewidth(0.5)
ax_leg.tick_params(length=0)

# 在图例每格中标"AaBb"短标识
for i in range(3):
    for j in range(3):
        ax_leg.text(j, 2-i, f'A{j+1}B{i+1}', ha='center', va='center',
                    fontsize=7, color=COLORS['text'], fontweight='bold')

fig.tight_layout()
save_fig(fig, 'figures/fig_bivariate.pdf')
