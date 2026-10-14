import numpy as np, matplotlib.pyplot as plt
import matplotlib.colors as mc
import colorsys
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

params = ['学习率 η', '批量 B', '种群大小 N', '交叉概率 Pc', '变异概率 Pm', '初始温度 T₀']
low_impact = np.array([-12.1, -8.5, -6.4, -5.2, -3.8, -2.1])
high_impact = np.array([15.3, 7.2, 5.9, 4.8, 3.1, 1.8])

# 按影响幅度排序
total_range = high_impact - low_impact
sort_idx = np.argsort(total_range)
params = [params[i] for i in sort_idx]
low_impact, high_impact = low_impact[sort_idx], high_impact[sort_idx]
total_range = total_range[sort_idx]
max_range = total_range.max() if total_range.max() > 0 else 1

# ★ 正负方向用不同色系
color_pos = '#5B8DB8'   # 蓝色系（正向影响）
color_neg = '#D4896A'   # 橙色系（负向影响）

n = len(params)
_fig_h = max(3, n * 0.7 + 1.2)
fig, ax = plt.subplots(figsize=(8, _fig_h))
y = np.arange(n)

ax.grid(axis='x', alpha=0.12, linestyle='-', color=COLORS['grid'])
ax.set_axisbelow(True)

# ★ 交替行背景
for i in range(n):
    if i % 2 == 0:
        ax.axhspan(y[i] - 0.4, y[i] + 0.4, alpha=0.03, color=PALETTE[0], zorder=0)

# ★ 条形（淡色填充 + 原色边框，颜色深浅映射影响幅度比例）
max_abs = max(abs(low_impact).max(), abs(high_impact).max())
for i in range(n):
    intensity = total_range[i] / max_range if max_range > 0 else 0.5
    lighten_amt = 0.5 * (1 - intensity)

    if high_impact[i] > 0:
        c = _lighten(color_pos, lighten_amt)
        ax.barh(y[i], high_impact[i], height=0.52,
                color=_lighten(c, 0.3), edgecolor=c, linewidth=1.3, zorder=3)
    if low_impact[i] < 0:
        c = _lighten(color_neg, lighten_amt)
        ax.barh(y[i], low_impact[i], height=0.52,
                color=_lighten(c, 0.3), edgecolor=c, linewidth=1.3, zorder=3)

    # 连接线
    if low_impact[i] < 0 and high_impact[i] > 0:
        ax.plot([low_impact[i], high_impact[i]], [y[i], y[i]],
                color=COLORS['ref_line'], linewidth=0.5, zorder=1, alpha=0.4)

    # 数值标签
    margin = max_abs * 0.05
    if high_impact[i] > 0:
        ax.text(high_impact[i] + margin, y[i], f'+{high_impact[i]:.1f}%',
                va='center', ha='left', fontsize=8.5, fontweight='bold',
                color=_lighten(color_pos, lighten_amt * 0.5))
    if low_impact[i] < 0:
        ax.text(low_impact[i] - margin, y[i], f'{low_impact[i]:.1f}%',
                va='center', ha='right', fontsize=8.5, fontweight='bold',
                color=_lighten(color_neg, lighten_amt * 0.5))

# 基准线 + 标注
ax.axvline(0, color=COLORS['text'], linewidth=1.0, zorder=2)
ax.text(0, n - 0.1, '基准值', ha='center', va='bottom', fontsize=8,
        color=COLORS['ref_line'],
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                  edgecolor=COLORS['grid'], alpha=0.85))

# 方向标注
ax.text(max_abs * 0.6, -0.7, '参数增大 →', fontsize=8, color=color_pos,
        ha='center', fontstyle='italic', alpha=0.6)
ax.text(-max_abs * 0.6, -0.7, '← 参数减小', fontsize=8, color=color_neg,
        ha='center', fontstyle='italic', alpha=0.6)

ax.set_yticks(y); ax.set_yticklabels(params, fontsize=10)
ax.set_xlabel('目标函数变化 (%)', fontsize=11)
xlim_max = max_abs * 1.35
ax.set_xlim(-xlim_max, xlim_max)
ax.set_ylim(-1.0, n - 0.5)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_tornado.pdf')
