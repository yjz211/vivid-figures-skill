from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

labels = ['Baseline', '+Attention', '+Augment', '+Pretrain', '-Dropout']
deltas = [0.82,        0.04,          0.02,       0.05,       -0.01]

cum = [deltas[0]]
for d in deltas[1:]:
    cum.append(cum[-1] + d)
final_val = cum[-1]
total_delta = final_val - deltas[0]

layer_colors = [COLORS['up'] if d >= 0 else COLORS['down'] for d in deltas[1:]]
n = len(labels)

fig, ax = plt.subplots(figsize=(9, 5))
ax.grid(axis='y', alpha=0.12, linestyle='-', color=COLORS['grid'])
ax.set_axisbelow(True)

x_positions = np.arange(n)

# ── 色带层叠（每步增量的层带位置，延伸到最右边）
for i in range(1, n):
    c = layer_colors[i - 1]
    bottom = min(cum[i-1], cum[i])
    top = max(cum[i-1], cum[i])
    ax.fill_between([x_positions[i] - 0.5, x_positions[-1] + 0.5], bottom, top,
                    alpha=0.15, color=c, zorder=1 + i)
    ax.plot([x_positions[i] - 0.5, x_positions[-1] + 0.5], [cum[i], cum[i]],
            color=c, linewidth=0.7, linestyle='--', alpha=0.35, zorder=1 + i)

# Baseline 底层
ax.fill_between([x_positions[0] - 0.5, x_positions[-1] + 0.5], 0, cum[0],
                alpha=0.06, color=PALETTE[0], zorder=0)

# ── 阶梯连线
ax.step(x_positions, cum, where='mid', color=PALETTE[0], linewidth=2.8, zorder=10)

# ── 圆点
for i in range(n):
    c = PALETTE[0] if i == 0 else layer_colors[i - 1]
    ax.scatter(x_positions[i], cum[i], color=c, s=90, zorder=11,
               edgecolors='white', linewidths=2.0)

# ── 数值标注 —— 所有步骤都标，统一放在圆点上方
for i in range(n):
    c = PALETTE[0] if i == 0 else layer_colors[i - 1]
    ax.text(x_positions[i], cum[i] + 0.008, f'{cum[i]:.3f}', ha='center', va='bottom',
            fontsize=8.5, fontweight='bold' if (i == 0 or i == n-1) else 'normal',
            color=c,
            bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                      edgecolor=c if (i == 0 or i == n-1) else 'none',
                      alpha=0.9, linewidth=0.5), zorder=12)

# ── 总增量标注（右上角）
ax.text(0.97, 0.95, f'Total: +{total_delta:.2f} (+{total_delta/deltas[0]*100:.1f}%)',
        transform=ax.transAxes, fontsize=9.5, ha='right', va='top',
        fontweight='bold', color=COLORS['up'],
        bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                  edgecolor=COLORS['up'], alpha=0.9, linewidth=1.0), zorder=15)

# ── 贡献图例（将贡献信息全部放在图例，而非图面上标）
legend_patches = []
for i in range(1, n):
    d = deltas[i]
    c = layer_colors[i - 1]
    sign = '+' if d >= 0 else ''
    pct = abs(d) / total_delta * 100
    patch = mpatches.Patch(facecolor=_lighten(c, 0.4), edgecolor=c, linewidth=1.2,
                           label=f'{labels[i]}  {sign}{d:.2f} ({pct:.0f}%)')
    legend_patches.append(patch)
legend = ax.legend(handles=legend_patches, loc='lower right',
                   frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8.5,
                   facecolor='white', title='Contribution', title_fontsize=9,
                   handlelength=1.5, handleheight=1.0)
legend.set_zorder(15)

ax.set_xticks(x_positions)
ax.set_xticklabels(labels, fontsize=10)
ax.set_ylabel('Accuracy', fontsize=11)
ax.set_xlim(-0.7, n - 0.3)
ax.set_ylim(deltas[0] * 0.92, final_val * 1.12)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_waterfall.pdf')
