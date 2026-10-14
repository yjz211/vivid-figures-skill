import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

models = ['Ours', 'ViT-B', 'ViT-L', 'ResNet-50', 'ResNet-101', 'DeiT-S', 'Swin-T', 'EfficientNet']
flops = np.array([4.2, 17.6, 61.6, 4.1, 7.8, 4.6, 4.5, 0.4])
acc = np.array([92.3, 91.2, 92.0, 89.5, 90.8, 90.1, 91.5, 88.2])
params = np.array([25, 86, 307, 25, 44, 22, 28, 5])

fig, ax = plt.subplots(figsize=(8, 5.5))

# Iso-efficiency contours (acc/flops = const)
flops_grid = np.linspace(0.1, 70, 200)
for eff in [5, 10, 20, 40]:
    acc_iso = eff * np.sqrt(flops_grid)
    mask = acc_iso <= 96
    ax.plot(flops_grid[mask], acc_iso[mask], '-', color=COLORS['grid'], linewidth=0.6, alpha=0.5)
ax.text(65, 86, 'iso-efficiency\ncurves', fontsize=6.5, color=COLORS['grid'], ha='right', style='italic')

# Scatter bubbles
for i, model in enumerate(models):
    c = PALETTE[0] if model == 'Ours' else PALETTE[2]
    alpha = 1.0 if model == 'Ours' else 0.55
    s = params[i] * 3
    ax.scatter(flops[i], acc[i], s=s, color=c, alpha=alpha, edgecolor='white',
               linewidth=1, zorder=3)
    offset = (8, 8) if model not in ['ViT-L', 'EfficientNet'] else (-15, -12)
    ax.annotate(model, xy=(flops[i], acc[i]), xytext=offset, textcoords='offset points',
                fontsize=8, fontweight='bold' if model == 'Ours' else 'normal',
                color=PALETTE[0] if model == 'Ours' else 'grey')

# Ours highlight ring
ours_idx = models.index('Ours')
ax.scatter(flops[ours_idx], acc[ours_idx], s=params[ours_idx] * 3 + 120, facecolor='none',
           edgecolor=PALETTE[0], linewidth=2.5, zorder=4)

# Pareto frontier
# Find Pareto-optimal points (lower flops, higher acc)
pareto_mask = np.ones(len(models), dtype=bool)
for i in range(len(models)):
    for j in range(len(models)):
        if i != j and flops[j] <= flops[i] and acc[j] >= acc[i] and (
                flops[j] < flops[i] or acc[j] > acc[i]):
            pareto_mask[i] = False
            break

pareto_flops = flops[pareto_mask]
pareto_acc = acc[pareto_mask]
sort_idx = np.argsort(pareto_flops)
pareto_flops = pareto_flops[sort_idx]
pareto_acc = pareto_acc[sort_idx]

# Smooth Pareto line
if len(pareto_flops) >= 3:
    f_smooth = np.linspace(pareto_flops.min(), pareto_flops.max(), 100)
    try:
        spl = make_interp_spline(pareto_flops, pareto_acc, k=min(3, len(pareto_flops) - 1))
        a_smooth = spl(f_smooth)
        ax.plot(f_smooth, a_smooth, '-', color=PALETTE[0], linewidth=1.5, alpha=0.6,
                label='Pareto frontier')
    except Exception:
        ax.plot(pareto_flops, pareto_acc, '-', color=PALETTE[0], linewidth=1.5, alpha=0.6,
                label='Pareto frontier')
else:
    ax.plot(pareto_flops, pareto_acc, '-', color=PALETTE[0], linewidth=1.5, alpha=0.6,
            label='Pareto frontier')

# "Better" direction arrow
ax.annotate('', xy=(1, 94), xytext=(15, 87),
            arrowprops=dict(arrowstyle='->', color=COLORS['up'], lw=2, connectionstyle='arc3,rad=0.1'))
ax.text(5, 93.5, 'Better', fontsize=10, fontweight='bold', color=COLORS['up'],
        style='italic', rotation=15)

# Bubble size legend
for ps in [10, 50, 200]:
    ax.scatter([], [], s=ps * 3, color=COLORS['ref_line'], alpha=0.3, edgecolor='white', label=f'{ps}M params')

ax.set_xlabel('GFLOPs', fontsize=11)
ax.set_ylabel('Top-1 Accuracy (%)', fontsize=11)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8, loc='lower right', title='Model Size')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(alpha=0.15, linestyle='--')
fig.tight_layout()
save_fig(fig, 'figures/fig_efficiency.pdf')
