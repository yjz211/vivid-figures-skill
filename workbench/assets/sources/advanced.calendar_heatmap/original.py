import numpy as np; from _utils.vivid_config import palette_colors
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.colors import LinearSegmentedColormap
from datetime import date, timedelta
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style(); scale_colors = palette_colors()
np.random.seed(42)

# === 模拟一年的日数据（周末偏低，月底偏高，几个事件峰值）===
start = date(2024, 1, 1)
n_days = 366
daily = np.random.gamma(2.0, 1.2, n_days)  # 基线
for i in range(n_days):
    d = start + timedelta(days=i)
    if d.weekday() >= 5: daily[i] *= 0.55  # 周末
    if d.day >= 28: daily[i] *= 1.3  # 月底
# 几个事件峰值
for ev in [40, 95, 180, 290]:
    daily[ev:ev+3] *= 2.5

# === 转 7×53 矩阵：行=周中第几天（周一-周日），列=年中第几周 ===
grid = np.full((7, 54), np.nan)
month_starts = []  # 记录每月第一天位置（用于画分隔线）
for i in range(n_days):
    d = start + timedelta(days=i)
    week = int(d.strftime('%W'))  # ISO 周
    weekday = d.weekday()  # 0=Mon
    grid[weekday, week] = daily[i]
    if d.day == 1:
        month_starts.append((d.month, week, weekday))

# === 主色调渐变 colormap（用原色序首色的浅→深）===
base = scale_colors[0]
cmap_calendar = LinearSegmentedColormap.from_list(
    'cal', [_lighten(base, 0.92), _lighten(base, 0.5), base, _lighten(base, -0.15) if False else base],
    N=128
)

fig, ax = plt.subplots(figsize=(11, 2.6))
im = ax.imshow(grid, aspect='equal', cmap=cmap_calendar, vmin=0,
               vmax=np.nanpercentile(grid, 98))

# === 月份分隔线 + 月名标注 ===
month_names = ['1月', '2月', '3月', '4月', '5月', '6月',
               '7月', '8月', '9月', '10月', '11月', '12月']
for m, wk, _ in month_starts:
    ax.axvline(wk - 0.5, color=COLORS['grid'], linewidth=0.8, alpha=0.5)
    ax.text(wk + 0.5, -1.0, month_names[m - 1], fontsize=8,
            ha='left', va='center', color=COLORS['text'])

# === Y 轴：仅显示 Mon / Wed / Fri ===
ax.set_yticks([0, 2, 4, 6])
ax.set_yticklabels(['周一', '周三', '周五', '周日'], fontsize=8)
ax.set_xticks([])
ax.tick_params(axis='y', length=0)
for spine in ax.spines.values(): spine.set_visible(False)

# === 顶部 colorbar（横向）===
cbar = fig.colorbar(im, ax=ax, orientation='horizontal', shrink=0.35,
                    pad=0.25, aspect=30)
cbar.set_label('日均值', fontsize=8)
cbar.ax.tick_params(labelsize=7, length=0)
cbar.outline.set_linewidth(0)

# === 异常日（top 1%）标注 ===
threshold = np.nanpercentile(daily, 99)
outliers_idx = np.where(daily > threshold)[0]
for idx in outliers_idx[:5]:  # 最多标 5 个
    d = start + timedelta(days=int(idx))
    wk = int(d.strftime('%W')); wd = d.weekday()
    ax.add_patch(Rectangle((wk - 0.45, wd - 0.45), 0.9, 0.9,
                            fill=False, edgecolor=COLORS['highlight'],
                            linewidth=1.3, zorder=5))

fig.tight_layout()
save_fig(fig, 'figures/fig_calendar_heatmap.pdf')
