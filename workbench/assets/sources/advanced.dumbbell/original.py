from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()
import matplotlib.pyplot as plt
import numpy as np

metrics = ['Accuracy', 'Precision', 'Recall', 'F1', 'AUC']
before = [0.82, 0.79, 0.85, 0.81, 0.88]
after = [0.91, 0.88, 0.90, 0.89, 0.94]

# ── 自适应高度
_fig_h = max(3.5, len(metrics) * 0.7 + 1)
fig, ax = plt.subplots(figsize=(8, _fig_h))
y = np.arange(len(metrics))

# Subtle grid
ax.grid(axis='x', alpha=0.15, linestyle='-', color=COLORS['grid'])
ax.set_axisbelow(True)

# Simple connector lines + arrow heads
for i in range(len(metrics)):
    delta = after[i] - before[i]
    pct_change = delta / before[i] * 100
    # Simple connector line
    ax.plot([before[i], after[i]], [y[i], y[i]],
            color=PALETTE[2], linewidth=2.0, solid_capstyle='round')
    # Arrow head at the "after" end
    ax.annotate('', xy=(after[i], y[i]), xytext=(after[i] - 0.012, y[i]),
                arrowprops=dict(arrowstyle='->', color=PALETTE[0], lw=2.0))

    # Before / After dots
    ax.scatter(before[i], y[i], color=PALETTE[3], s=80, zorder=3,
               edgecolors='white', linewidths=1.0, label='Before' if i == 0 else '')
    ax.scatter(after[i], y[i], color=PALETTE[0], s=80, zorder=3,
               edgecolors='white', linewidths=1.0, label='After' if i == 0 else '')

    # % change label
    ax.text(after[i] + 0.015, y[i] - 0.15, f'+{delta:.2f} ({pct_change:+.1f}%)',
            va='center', fontsize=8, color=PALETTE[0], fontweight='bold')

    # Significance marker (stars)
    if pct_change > 8:
        sig = '***'
    elif pct_change > 5:
        sig = '**'
    else:
        sig = '*'
    ax.text(after[i] + 0.015, y[i] + 0.2, sig, va='center', fontsize=9,
            color=COLORS['down'], fontweight='bold')

ax.set_yticks(y)
ax.set_yticklabels(metrics, fontsize=10)
ax.set_xlabel('Score', fontsize=11)
ax.legend(loc='lower right', frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9,
          fancybox=True, shadow=False)
ax.invert_yaxis()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_dumbbell.pdf')
