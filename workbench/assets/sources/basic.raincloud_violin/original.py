import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import ttest_ind
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
groups = ['A组', 'B组', 'C组', 'D组']
data = [np.random.normal(m, s, 100) for m, s in [(80, 5), (85, 3), (78, 8), (90, 4)]]

fig, ax = plt.subplots(figsize=(8, 5.5))

# ★ 淡色填充 + 原色边框小提琴
parts = ax.violinplot(data, positions=range(len(groups)), showmeans=False,
                      showmedians=False, showextrema=False)

for i, pc in enumerate(parts['bodies']):
    pc.set_facecolor(_lighten(PALETTE[i], 0.4))
    pc.set_edgecolor(PALETTE[i])
    pc.set_linewidth(1.2)
    pc.set_alpha(0.7)

# 叠加窄箱线图
bp = ax.boxplot(data, positions=range(len(groups)), widths=0.15, patch_artist=True,
                boxprops=dict(facecolor='white', edgecolor=COLORS['text'], linewidth=1.2),
                medianprops=dict(color=COLORS['text'], linewidth=2),
                whiskerprops=dict(linewidth=1.2),
                capprops=dict(linewidth=1.2),
                flierprops=dict(marker='.', markersize=3, alpha=0.3))

# 均值菱形 + 数值标注
for i, d in enumerate(data):
    ax.scatter(i, d.mean(), marker='D', s=40, color=PALETTE[i],
               edgecolor='white', linewidth=1, zorder=5)
    ax.text(i + 0.25, d.mean(), f'{d.mean():.1f}', fontsize=7.5, color=PALETTE[i],
            va='center', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.1', facecolor='white',
                      edgecolor='none', alpha=0.7))

# 显著性括号
def add_significance(ax, x1, x2, y, p_val, h=2):
    ax.plot([x1, x1, x2, x2], [y, y + h, y + h, y], color=COLORS['text'], linewidth=0.8)
    stars = '***' if p_val < 0.001 else '**' if p_val < 0.01 else '*' if p_val < 0.05 else 'n.s.'
    ax.text((x1 + x2) / 2, y + h + 0.3, f'{stars}\np={p_val:.2e}',
            ha='center', va='bottom', fontsize=7, color=COLORS['text'],
            bbox=dict(boxstyle='round,pad=0.15', facecolor=COLORS['bg_box'],
                      edgecolor=COLORS['grid'], alpha=0.9, linewidth=0.3))

y_max = max(d.max() for d in data) + 3
# 比较最优组（D组）与其他组
for idx, comp in enumerate([0, 1, 2]):
    _, p = ttest_ind(data[3], data[comp])
    add_significance(ax, comp, 3, y_max + idx * 6, p)

ax.set_xticks(range(len(groups)))
ax.set_xticklabels(groups, fontsize=10)
ax.set_ylabel('数值', fontsize=11)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='y', alpha=0.12, linestyle='--', color=COLORS['grid'])
fig.tight_layout()
save_fig(fig, 'figures/fig_violin.pdf')
