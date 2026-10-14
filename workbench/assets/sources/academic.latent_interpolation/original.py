import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

categories = ['Accuracy', 'Precision', 'Recall', 'F1', 'Speed', 'Memory']
N = len(categories)
angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist() + [0]

methods = {
    'Ours': [0.95, 0.93, 0.91, 0.92, 0.70, 0.65],
    'Transformer': [0.92, 0.90, 0.88, 0.89, 0.50, 0.40],
    'CNN': [0.88, 0.85, 0.90, 0.87, 0.85, 0.80],
}

def polygon_area(vals, angles_list):
    """Calculate polygon area for radar chart"""
    n = len(vals)
    area = 0
    for i in range(n):
        j = (i + 1) % n
        area += vals[i] * vals[j] * np.sin(angles_list[j] - angles_list[i])
    return abs(area) / 2

fig, ax = plt.subplots(figsize=(6.5, 6), subplot_kw=dict(polar=True))

# Threshold ring at 0.8
threshold = 0.8
ax.plot(angles, [threshold] * (N + 1), '--', color=COLORS['ref_line'], linewidth=1, alpha=0.4)
ax.text(0.02, 0.02, f'Baseline ({threshold})', fontsize=7, color=COLORS['ref_line'],
        transform=ax.transAxes, ha='left', va='bottom')

areas = {}
for i, (name, vals) in enumerate(methods.items()):
    vc = vals + vals[:1]
    lw = 2.5 if name == 'Ours' else 1.5
    alpha_fill = 0.18 if name == 'Ours' else 0.06
    ax.plot(angles, vc, 'o-', linewidth=lw, markersize=5, color=PALETTE[i], label=name,
            markeredgecolor='white', markeredgewidth=0.8)
    ax.fill(angles, vc, alpha=alpha_fill, color=PALETTE[i])

    # Value labels at each vertex — only label "Ours" to avoid overlap
    if name == 'Ours':
        for j, (ang, val) in enumerate(zip(angles[:-1], vals)):
            offset_r = 0.08
            ax.text(ang, val + offset_r, f'{val:.2f}', fontsize=7, ha='center', va='bottom',
                    color=PALETTE[i], fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                              edgecolor=PALETTE[i], alpha=0.85, linewidth=0.4))

    areas[name] = polygon_area(vals, angles[:-1])

# Area ratio annotation in center
ours_area = areas['Ours']
ratios = [f'{name}: {ours_area / a:.2f}×' for name, a in areas.items() if name != 'Ours']
ax.text(0, 0, f'Area ratio\nvs Ours:\n' + '\n'.join(ratios),
        ha='center', va='center', fontsize=7, color=COLORS['text'],
        transform=ax.transData,
        bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                  edgecolor=COLORS['grid'], alpha=0.9))

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=9)
ax.set_ylim(0, 1.05)
ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
ax.set_yticklabels(['', '0.4', '0.6', '0.8', '1.0'], fontsize=7, color=COLORS['ref_line'])
ax.legend(loc='best', bbox_to_anchor=(1.35, 1.1), frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9)
fig.tight_layout()
save_fig(fig, 'figures/fig_radar.pdf')
