from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten, smart_labels
setup_style()
import matplotlib.pyplot as plt
import matplotlib.colors as mc
import numpy as np
import colorsys

methods = ['Ours', 'Baseline-A', 'Baseline-B', 'Baseline-C', 'Baseline-D']
scores = [0.923, 0.887, 0.862, 0.841, 0.815]

n = len(methods)
score_min, score_max = min(scores), max(scores)
score_range = score_max - score_min if score_max > score_min else 1

# ── 渐变配色：从紫罗兰 → 珊瑚橙（明度和色相同时渐变）
color_top = '#7B6BA5'     # 紫罗兰（高分，偏冷一点）
color_bottom = '#E08B74'  # 珊瑚橙（低分，偏暖）

def interpolate_color(c1, c2, t):
    """HSL 空间插值：t=0 返回 c1，t=1 返回 c2"""
    r1, g1, b1 = mc.to_rgb(c1)
    r2, g2, b2 = mc.to_rgb(c2)
    h1, l1, s1 = colorsys.rgb_to_hls(r1, g1, b1)
    h2, l2, s2 = colorsys.rgb_to_hls(r2, g2, b2)
    if abs(h2 - h1) > 0.5:
        if h1 < h2: h1 += 1.0
        else: h2 += 1.0
    h = (h1 + (h2 - h1) * t) % 1.0
    l = l1 + (l2 - l1) * t
    s = s1 + (s2 - s1) * t
    return colorsys.hls_to_rgb(h, l, s)

item_colors = [interpolate_color(color_top, color_bottom, i / (n - 1) if n > 1 else 0) for i in range(n)]

# ── 自适应高度（每项 0.46 高度 + 上下留白）
_fig_h = max(4, n * 0.46 + 1.8)
fig, ax = plt.subplots(figsize=(7.5, _fig_h))
y_pos = np.arange(n)

# 极浅网格线
ax.grid(axis='x', alpha=0.12, linestyle='-', color=COLORS['grid'])
ax.set_axisbelow(True)

# 中位数参考线（置于底层）
median_val = np.median(scores)
ax.axvline(median_val, color=COLORS['ref_line'], linestyle=':', linewidth=1.0, alpha=0.5, zorder=1)

# ── 主体：渐变色茎线 + 渐变圆点
for i, (m, s) in enumerate(zip(methods, scores)):
    c = item_colors[i]
    ratio = (s - score_min) / score_range
    lw = 1.6 + 2.0 * ratio

    # 茎线从 0 开始
    ax.plot([0, s], [y_pos[i], y_pos[i]],
            color=c, linewidth=lw, zorder=3, solid_capstyle='round')

    # 端点圆点 —— 大小随分数渐变
    dot_size = 55 + 120 * ratio
    ax.scatter(s, y_pos[i], color=c, s=dot_size, zorder=5,
               edgecolors='white', linewidths=1.8)

    # 数值标签
    ax.text(s + score_range * 0.03, y_pos[i], f'{s:.3f}',
            fontsize=8.5, fontweight='bold' if i < 3 else 'normal',
            color=c, va='center', ha='left')

    # ── 排名徽章区域
    badge_x = -score_range * 0.065
    rank = i + 1
    if rank <= 3:
        badge = plt.Circle((badge_x, y_pos[i]), 0.3,
                            color=_lighten(c, 0.15), zorder=6,
                            transform=ax.transData)
        ax.add_patch(badge)
        ax.text(badge_x, y_pos[i], str(rank),
                fontsize=8.5, fontweight='bold', color='white',
                ha='center', va='center', zorder=7)
    else:
        ax.text(badge_x, y_pos[i], str(rank),
                fontsize=7.5, color=_lighten(c, 0.2),
                ha='center', va='center', fontweight='bold')

# 第一名背景高亮条
ax.axhspan(y_pos[0] - 0.42, y_pos[0] + 0.42, alpha=0.06,
           color=item_colors[0], zorder=0)

# 中位数标注 —— 置于图的顶部
ax.text(median_val, -0.9, f'中位数 {median_val:.3f}',
        fontsize=8, color=COLORS['ref_line'], ha='center', va='bottom',
        bbox=dict(boxstyle='round,pad=0.25', facecolor='white',
                  edgecolor=COLORS['ref_line'], alpha=0.85))

ax.set_yticks(y_pos)
ax.set_yticklabels(methods, fontsize=10)
ax.set_xlabel('F1 Score', fontsize=11)
ax.set_xlim(-score_range * 0.13, score_max + score_range * 0.15)
ax.set_ylim(n - 0.5, -1.4)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_lollipop.pdf')
