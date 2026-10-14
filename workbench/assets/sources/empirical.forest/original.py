import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

labels = ['低固定资产组', '高固定资产组', '低负债组', '高负债组',
          '低资产负债率组', '高资产负债率组', '低流动性组', '高流动性组']
coefs  = np.array([-0.028,-0.042,-0.030,-0.031,-0.035,-0.025,-0.032,-0.033])
ci_lo  = np.array([-0.048,-0.058,-0.055,-0.052,-0.052,-0.010,-0.048,-0.046])
ci_hi  = np.array([-0.008,-0.026,-0.005,-0.010,-0.018,-0.040,-0.016,-0.020])
weights = np.array([12.8, 14.2, 10.5, 11.3, 13.1, 9.7, 14.6, 13.8])
significant = [True, True, False, False, True, True, False, False]

pooled_coef = np.average(coefs, weights=weights)
pooled_se   = 0.004
pooled_lo   = pooled_coef - 1.96 * pooled_se
pooled_hi   = pooled_coef + 1.96 * pooled_se

# ★ 自适应高度：变量多时不会过度拉伸
_fig_h = max(5, len(labels) * 0.7 + 2)
fig, ax = plt.subplots(figsize=(11, _fig_h))
y = np.arange(len(labels)) * 1.4

# 交替行阴影
for i in range(len(labels)):
    if i % 2 == 0:
        ax.axhspan(y[i] - 0.55, y[i] + 0.55, color=COLORS['bg_box'], zorder=0)

# 零线参考
ax.axvline(x=0, color=COLORS['down'], linestyle='--', linewidth=1.5, alpha=0.7, zorder=1)

for i, (c, lo, hi, lbl, sig, wt) in enumerate(zip(coefs, ci_lo, ci_hi, labels, significant, weights)):
    # CI 线 + 端点帽
    ax.plot([lo, hi], [y[i], y[i]], color=COLORS['text'], linewidth=1.2, zorder=2, solid_capstyle='round')
    ax.plot([lo, lo], [y[i]-0.12, y[i]+0.12], color=COLORS['text'], linewidth=1.0)
    ax.plot([hi, hi], [y[i]-0.12, y[i]+0.12], color=COLORS['text'], linewidth=1.0)

    # 权重比例圆点（显著=实心，不显著=空心）
    fc = PALETTE[0] if sig else 'white'
    ec = PALETTE[0] if sig else COLORS['ref_line']
    ms = 5 + wt / 4
    ax.plot(c, y[i], 'o', color=fc, markersize=ms, markeredgecolor=ec,
            markeredgewidth=1.3, zorder=3)

    # 左侧标签
    ax.text(-0.065, y[i], lbl, ha='right', va='center', fontsize=9, color=COLORS['text'])

    # 右侧数值列：系数 [95% CI] + 显著性★
    sig_mark = '***' if sig else ''
    ax.text(0.085, y[i], f'{c:.3f} [{lo:.3f}, {hi:.3f}]{sig_mark}',
            ha='left', va='center', fontsize=8, fontfamily='monospace',
            color=PALETTE[0] if sig else COLORS['ref_line'],
            fontweight='bold' if sig else 'normal')

    # 权重列
    ax.text(0.16, y[i], f'{wt:.1f}%', ha='right', va='center',
            fontsize=8, color=COLORS['text'])

# 列标题
ax.text(-0.065, max(y) + 1.0, '分组', ha='right', va='center',
        fontsize=9.5, fontweight='bold', color=COLORS['text'])
ax.text(0.085, max(y) + 1.0, '系数 [95% CI]', ha='left', va='center',
        fontsize=9.5, fontweight='bold', color=COLORS['text'])
ax.text(0.16, max(y) + 1.0, '权重', ha='right', va='center',
        fontsize=9.5, fontweight='bold', color=COLORS['text'])

# 菱形 pooled estimate
diamond_y = -1.5
dh = 0.35
diamond_x = [pooled_lo, pooled_coef, pooled_hi, pooled_coef]
diamond_yy = [diamond_y, diamond_y + dh, diamond_y, diamond_y - dh]
ax.fill(diamond_x, diamond_yy, color=PALETTE[1], alpha=0.85, zorder=4)
ax.plot(diamond_x + [diamond_x[0]], diamond_yy + [diamond_yy[0]],
        color=COLORS['text'], linewidth=0.8, zorder=5)
ax.text(-0.065, diamond_y, 'Pooled', ha='right', va='center',
        fontsize=9.5, fontweight='bold', color=PALETTE[1])
ax.text(0.085, diamond_y, f'{pooled_coef:.3f} [{pooled_lo:.3f}, {pooled_hi:.3f}]***',
        ha='left', va='center', fontsize=8, fontfamily='monospace',
        fontweight='bold', color=PALETTE[1])

# I² 异质性标注框
i2_text = 'I² = 42.3%, Q = 13.8 (p = 0.055)'
ax.text(0.0, diamond_y - 1.0, i2_text, ha='center', va='top', fontsize=8.5,
        bbox=dict(boxstyle='round,pad=0.4', facecolor=_lighten(COLORS['highlight'], 0.85),
                  edgecolor=_lighten(COLORS['highlight'], 0.4), alpha=0.95),
        color=COLORS['text'])

ax.set_yticks([])
ax.set_xlabel('回归系数', fontsize=12)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.set_ylim(diamond_y - 1.8, max(y) + 1.5)
ax.set_xlim(-0.07, 0.17)
ax.invert_yaxis()
ax.grid(axis='x', alpha=0.15, linestyle='--')
fig.tight_layout()
save_fig(fig, 'figures/fig_forest.pdf')
