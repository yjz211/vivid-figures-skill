import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

labels = ['类别A', '类别B', '类别C', '类别D', '类别E']
sizes = [35, 25, 20, 12, 8]
prev_sizes = [32, 27, 19, 14, 8]  # 上期数据（用于计算变化率）
explode = [0.03] * len(labels)

fig, ax = plt.subplots(figsize=(7, 6))

# ★ 淡色填充 + 原色边框
wedge_colors = [_lighten(PALETTE[i], 0.4) for i in range(len(labels))]
edge_colors = [PALETTE[i] for i in range(len(labels))]

wedges, texts = ax.pie(
    sizes, labels=None, startangle=90,
    colors=wedge_colors, explode=explode,
    wedgeprops=dict(width=0.45, edgecolor='white', linewidth=0),
    pctdistance=0.75)

# 原色边框（单独绘制，避免白色分隔线被覆盖）
for wedge, ec in zip(wedges, edge_colors):
    wedge.set_edgecolor(ec)
    wedge.set_linewidth(1.5)

# 外部连线标签 + 变化率
for i, (wedge, label, size, prev) in enumerate(zip(wedges, labels, sizes, prev_sizes)):
    ang = (wedge.theta2 + wedge.theta1) / 2
    x_label = np.cos(np.radians(ang)) * 1.35
    y_label = np.sin(np.radians(ang)) * 1.35
    x_conn = np.cos(np.radians(ang)) * 1.05
    y_conn = np.sin(np.radians(ang)) * 1.05

    # 连线
    ax.plot([x_conn, x_label], [y_conn, y_label], '-', color=PALETTE[i],
            linewidth=0.8, alpha=0.6)

    # 标签 + 百分比 + 变化率
    change = size - prev
    sign = '+' if change >= 0 else ''
    change_color = COLORS['up'] if change >= 0 else COLORS['down']
    ha = 'left' if x_label > 0 else 'right'
    ax.text(x_label, y_label,
            f'{label}\n{size}% ({sign}{change}%)',
            ha=ha, va='center', fontsize=9, color=PALETTE[i],
            fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                      edgecolor=PALETTE[i], alpha=0.8, linewidth=0.5))

# 中心文字
ax.text(0, 0, '总计\n100%', ha='center', va='center', fontsize=14,
        fontweight='bold', color=COLORS['text'])

ax.set_aspect('equal')
fig.tight_layout()
save_fig(fig, 'figures/fig_donut.pdf')
