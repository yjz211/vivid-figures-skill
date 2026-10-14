import numpy as np, matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

categories = ['初始值', '原材料', '人工', '运输', '税费', '折旧', '管理费', '利润', '最终值']
values = [100, -15, -20, -8, -12, -5, -3, 0, 0]
# 计算累积值
cumulative = [100]
for v in values[1:-1]:
    cumulative.append(cumulative[-1] + v)
cumulative.append(cumulative[-1])
values[-1] = cumulative[-1]

fig, ax = plt.subplots(figsize=(10, 5))
ax.grid(axis='y', alpha=0.12, linestyle='--'); ax.set_axisbelow(True)

bottoms = []
for i in range(len(categories)):
    if i == 0 or i == len(categories)-1:
        bottoms.append(0)
    else:
        bottoms.append(min(cumulative[i-1], cumulative[i]))

for i in range(len(categories)):
    if i == 0 or i == len(categories)-1:
        c = PALETTE[0]
        h = cumulative[i]
    elif values[i] >= 0:
        c = COLORS['up']
        h = values[i]
    else:
        c = COLORS['down']
        h = abs(values[i])

    ax.bar(i, h, bottom=bottoms[i], width=0.6,
           color=_lighten(c, 0.3), edgecolor=c, linewidth=1.3, zorder=3)

    # 数值标注
    val_y = bottoms[i] + h + 1
    sign = '+' if values[i] > 0 and i > 0 else ''
    ax.text(i, val_y, f'{sign}{values[i] if i < len(categories)-1 else cumulative[i]}',
            ha='center', va='bottom', fontsize=8.5, fontweight='bold', color=c)

    # 连接线
    if i < len(categories) - 1:
        ax.plot([i+0.3, i+0.7], [cumulative[i], cumulative[i]],
                color=COLORS['ref_line'], linewidth=0.8, linestyle='--', alpha=0.5)

ax.set_xticks(range(len(categories)))
ax.set_xticklabels(categories, fontsize=10, rotation=15, ha='right')
ax.set_ylabel('金额（万元）', fontsize=11)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_waterfall.pdf')
