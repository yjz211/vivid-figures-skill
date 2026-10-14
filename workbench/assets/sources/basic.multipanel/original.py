import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
fig, axes = plt.subplots(2, 2, figsize=(5.0, 4.9))   # 示例尺寸；保留模板比例，按实际显示尺寸检查字号与布局

# (a) 折线图 — 渐变填充
ax = axes[0, 0]
for i in range(3):
    y = np.cumsum(np.random.randn(10))
    ax.plot(range(10), y, 'o-', color=PALETTE[i], linewidth=1.8, markersize=5,
            markeredgecolor='white', markeredgewidth=0.8, label=f'系列{i + 1}')
    ax.fill_between(range(10), y - 1, y + 1, alpha=0.08, color=PALETTE[i])
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8)
ax.set_ylabel('累计值', fontsize=10)
ax.grid(alpha=0.12, linestyle='--', color=COLORS['grid'])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# (b) 分组柱状图 — 淡色填充 + 原色边框
ax = axes[0, 1]
x = np.arange(5)
for i, label in enumerate(['方法A', '方法B']):
    vals = np.random.uniform(60, 95, 5)
    offset = (i - 0.5) * 0.3
    ax.bar(x + offset, vals, 0.28, color=_lighten(PALETTE[i], 0.4),
           edgecolor=PALETTE[i], linewidth=1.2, label=label)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8)
ax.set_ylabel('得分', fontsize=10)
ax.grid(axis='y', alpha=0.12, linestyle='--', color=COLORS['grid'])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# (c) 散点图 — KDE 等高线背景
ax = axes[1, 0]
for i in range(3):
    pts = np.random.randn(30, 2)
    ax.scatter(pts[:, 0], pts[:, 1], s=25, alpha=0.6, color=PALETTE[i],
               edgecolor='white', linewidth=0.5, label=f'类{i + 1}')
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8)
ax.grid(alpha=0.12, linestyle='--', color=COLORS['grid'])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# (d) 直方图 — 淡色填充 + 原色边框
ax = axes[1, 1]
for i in range(3):
    vals = np.random.normal(i * 2, 1, 200)
    ax.hist(vals, bins=20, alpha=0.5, color=_lighten(PALETTE[i], 0.4),
            edgecolor=PALETTE[i], linewidth=0.8, label=f'分布{i + 1}')
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8)
ax.set_ylabel('频次', fontsize=10)
ax.grid(axis='y', alpha=0.12, linestyle='--', color=COLORS['grid'])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# ★ 带背景框子图标签（用 set_title 紧贴子图顶部）
for i, ax in enumerate(axes.flat):
    ax.set_title(f'({chr(97 + i)})', fontsize=12, fontweight='bold', loc='left', pad=3)

fig.tight_layout(pad=0.5)
save_fig(fig, 'figures/fig_subplots.pdf')
