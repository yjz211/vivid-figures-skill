import numpy as np, matplotlib.pyplot as plt, matplotlib.colors as mc
import colorsys
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

categories = ['成本', '效率', '可靠性', '安全性', '灵活性', '可扩展性']
N = len(categories)
angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist() + [0]

methods = {
    '本文方法': [0.95, 0.88, 0.92, 0.90, 0.85, 0.91],
    '方案A':   [0.80, 0.82, 0.78, 0.85, 0.70, 0.75],
    '方案B':   [0.85, 0.75, 0.88, 0.72, 0.90, 0.68],
    '方案C':   [0.70, 0.90, 0.65, 0.80, 0.60, 0.82],
}

fig, ax = plt.subplots(figsize=(6.5, 6.5), subplot_kw=dict(polar=True))
ax.set_facecolor('white')
ax.set_ylim(0, 1.12)  # 留出标注空间

# ★ 渐变环色背景 + 自定义同心圆网格
ring_levels = [0.2, 0.4, 0.6, 0.8, 1.0]
theta_fill = np.linspace(0, 2*np.pi, 100)
for k, r in enumerate(ring_levels):
    r_prev = ring_levels[k-1] if k > 0 else 0
    if k % 2 == 0:
        ax.fill_between(theta_fill, r_prev, r, alpha=0.025, color=PALETTE[0], zorder=0)
    ax.plot(theta_fill, [r]*len(theta_fill), color='#E5E5E5', linewidth=0.5, zorder=1)
ax.set_yticks(ring_levels)
ax.set_yticklabels(['0.2','0.4','0.6','0.8','1.0'], fontsize=7, color='#C0C0C0')

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=10.5, color=COLORS['text'])
ax.tick_params(axis='x', pad=18)

for i, (name, vals) in enumerate(methods.items()):
    values = vals + [vals[0]]
    is_ours = '本文' in name
    lw = 2.5 if is_ours else 1.2
    alpha_line = 1.0 if is_ours else 0.5
    alpha_fill = 0.15 if is_ours else 0.04
    ax.plot(angles, values, color=PALETTE[i], linewidth=lw, label=name, alpha=alpha_line, zorder=3)
    ax.fill(angles, values, color=PALETTE[i], alpha=alpha_fill, zorder=1)
    # 本文方法顶部数值标注
    if is_ours:
        for j, (a, v) in enumerate(zip(angles[:-1], vals)):
            r_label = v + 0.08
            ax.text(a, r_label, f'{v:.2f}', ha='center', va='bottom', fontsize=7.5,
                    fontweight='bold', color=PALETTE[i],
                    bbox=dict(facecolor='white', alpha=0.9, edgecolor='none', pad=1))

ax.legend(loc='best', bbox_to_anchor=(1.28, 1.06),
          frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, facecolor='white')
fig.tight_layout()
save_fig(fig, 'figures/fig_radar.pdf')
