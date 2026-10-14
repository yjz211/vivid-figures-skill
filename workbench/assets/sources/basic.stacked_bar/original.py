import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

categories = ['2019', '2020', '2021', '2022', '2023']
components = {
    '第一产业': [8.2, 7.8, 7.5, 7.2, 6.9],
    '第二产业': [38.5, 37.2, 36.8, 36.1, 35.5],
    '第三产业': [53.3, 55.0, 55.7, 56.7, 57.6],
}

fig, ax = plt.subplots(figsize=(8, 5.5))
x = np.arange(len(categories))
bottom = np.zeros(len(categories))
bar_width = 0.55

for i, (name, vals) in enumerate(components.items()):
    vals_arr = np.array(vals)
    # ★ 淡色填充 + 原色边框
    bars = ax.bar(x, vals_arr, bar_width, bottom=bottom,
                  color=_lighten(PALETTE[i], 0.4), edgecolor=PALETTE[i],
                  linewidth=1.2, label=name, zorder=2)

    # 自动对比度标签：深色块白字 / 浅色块黑字
    for bar, v, b in zip(bars, vals_arr, bottom):
        if v > 5:
            r, g, b_c = mcolors.to_rgb(_lighten(PALETTE[i], 0.4))
            luminance = 0.299 * r + 0.587 * g + 0.114 * b_c
            text_color = 'white' if luminance < 0.6 else COLORS['text']
            ax.text(bar.get_x() + bar.get_width() / 2, b + v / 2,
                    f'{v:.1f}%', ha='center', va='center', fontsize=8,
                    color=text_color, fontweight='bold')
    bottom += vals_arr

# 顶部趋势折线（总量）
totals = bottom
ax.plot(x, totals, 'o-', color=COLORS['text'], linewidth=1.5, markersize=5,
        markeredgecolor='white', markeredgewidth=1, zorder=3)
for xi, t in zip(x, totals):
    ax.text(xi, t + 1.0, f'{t:.1f}', ha='center', va='bottom', fontsize=8,
            fontweight='bold', color=COLORS['text'])

# 末端同比变化标注
for i, (name, vals) in enumerate(components.items()):
    change = vals[-1] - vals[-2]
    sign = '+' if change >= 0 else ''
    color = COLORS['up'] if change >= 0 else COLORS['down']
    y_pos = sum(components[n][-1] for n in list(components.keys())[:i]) + vals[-1] / 2
    ax.annotate(f'{sign}{change:.1f}%', xy=(len(categories) - 1 + 0.35, y_pos),
                fontsize=7, color=color, fontweight='bold', va='center',
                bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                          edgecolor=color, alpha=0.8, linewidth=0.5))

ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=10)
ax.set_ylabel('占比 (%)', fontsize=11)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='upper left')
ax.grid(axis='y', alpha=0.12, linestyle='--', color=COLORS['grid'])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_stacked_bar.pdf')
