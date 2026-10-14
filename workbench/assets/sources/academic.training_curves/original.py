import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
epochs = np.arange(1, 101)
train_loss = 2.5 * np.exp(-0.04 * epochs) + 0.15 + np.random.normal(0, 0.02, 100)
val_loss = 2.5 * np.exp(-0.035 * epochs) + 0.25 + np.random.normal(0, 0.03, 100)
train_acc = (1 - train_loss / 3.0 + np.random.normal(0, 0.005, 100)) * 100
val_acc = (1 - val_loss / 3.0 + np.random.normal(0, 0.008, 100)) * 100

# LR schedule (cosine decay)
lr = 1e-3 * (0.5 * (1 + np.cos(np.pi * epochs / 100)))

fig, ax1 = plt.subplots(figsize=(8, 5))
ax2 = ax1.twinx()

# Loss curves with gradient fill
l1, = ax1.plot(epochs, train_loss, color=PALETTE[0], linewidth=1.8, label='Train Loss')
l2, = ax1.plot(epochs, val_loss, color=PALETTE[0], linewidth=1.8, linestyle='--',
               label='Val Loss', alpha=0.7)
# Gradient fill under train loss
for layer, alpha in enumerate([0.15, 0.08, 0.03]):
    ax1.fill_between(epochs, train_loss.min() - 0.1 + layer * 0.05,
                     train_loss - layer * 0.03,
                     alpha=alpha, color=PALETTE[0], linewidth=0)

# Accuracy curves
l3, = ax2.plot(epochs, train_acc, color=PALETTE[1], linewidth=1.8, label='Train Acc')
l4, = ax2.plot(epochs, val_acc, color=PALETTE[1], linewidth=1.8, linestyle='--',
               label='Val Acc', alpha=0.7)

# Best epoch (min val loss) — star marker
best_epoch = np.argmin(val_loss) + 1
ax1.scatter(best_epoch, val_loss[best_epoch - 1], marker='*', s=200, color=COLORS['down'],
            edgecolor='white', linewidth=1, zorder=6)
ax1.annotate(f'Best: epoch {best_epoch}\nloss={val_loss[best_epoch - 1]:.3f}',
             xy=(best_epoch, val_loss[best_epoch - 1]),
             xytext=(best_epoch + 15, val_loss[best_epoch - 1] + 0.3),
             fontsize=8, fontweight='bold', color=COLORS['down'],
             arrowprops=dict(arrowstyle='->', color=COLORS['down'], lw=1.2),
             bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                       edgecolor=COLORS['down'], alpha=0.9))

# Early stopping line
early_stop = best_epoch + 10
ax1.axvline(x=early_stop, color=COLORS['ref_line'], linestyle=':', linewidth=1, alpha=0.6)
ax1.text(early_stop + 1, ax1.get_ylim()[1] * 0.9, 'Early\nStopping',
         fontsize=7.5, color=COLORS['ref_line'], style='italic')

# LR schedule inset
ax_inset = inset_axes(ax1, width='30%', height='25%', loc='center right',
                      borderpad=2)
ax_inset.plot(epochs, lr * 1000, color=PALETTE[2], linewidth=1.2)
ax_inset.set_xlabel('Epoch', fontsize=6)
ax_inset.set_ylabel('LR (×10⁻³)', fontsize=6)
ax_inset.tick_params(labelsize=5)
ax_inset.set_title('LR Schedule', fontsize=7, fontweight='bold')
ax_inset.grid(alpha=0.15, linestyle='--')
for spine in ax_inset.spines.values():
    spine.set_linewidth(0.5)

ax1.set_xlabel('Epoch', fontsize=11)
ax1.set_ylabel('Loss', fontsize=11, color=PALETTE[0])
ax2.set_ylabel('Accuracy (%)', fontsize=11, color=PALETTE[1])
ax1.tick_params(axis='y', labelcolor=PALETTE[0])
ax2.tick_params(axis='y', labelcolor=PALETTE[1])

lines = [l1, l2, l3, l4]
ax1.legend(lines, [l.get_label() for l in lines], frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='center left')
ax1.grid(alpha=0.15, linestyle='--')
ax1.spines['top'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_training_curve.pdf')
