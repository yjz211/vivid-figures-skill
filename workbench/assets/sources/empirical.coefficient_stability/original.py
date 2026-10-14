import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

# === Example data (replace with actual regression results) ===
specs = ['基准', '+经济水平', '+城镇化', '+人力资本', '+FDI', '+金融发展', '+基础设施', '全控制']
coefs = [0.045, 0.042, 0.041, 0.039, 0.040, 0.038, 0.037, 0.036]
ci_lower = [0.032, 0.030, 0.029, 0.027, 0.028, 0.026, 0.025, 0.024]
ci_upper = [0.058, 0.054, 0.053, 0.051, 0.052, 0.050, 0.049, 0.048]
n_controls = list(range(len(specs)))

fig, ax = plt.subplots(figsize=(9, 5))

# CI band (gradient fill)
ax.fill_between(n_controls, ci_lower, ci_upper, alpha=0.15, color=PALETTE[0])
ax.fill_between(n_controls, [c - (c - cl) * 0.5 for c, cl in zip(coefs, ci_lower)],
                [c + (cu - c) * 0.5 for c, cu in zip(coefs, ci_upper)],
                alpha=0.25, color=PALETTE[0])

# Coefficient line + markers
ax.plot(n_controls, coefs, 'o-', color=PALETTE[0], linewidth=2.5, markersize=8,
        markeredgecolor='white', markeredgewidth=1.5, zorder=5)

# Value labels
for i, (x, y) in enumerate(zip(n_controls, coefs)):
    ax.text(x, y + 0.002, f'{y:.3f}', ha='center', va='bottom', fontsize=8,
            fontweight='bold', color=PALETTE[0])

# Zero reference line
ax.axhline(0, color=COLORS['ref_line'], linewidth=0.8, linestyle='--', alpha=0.5)

# Baseline reference band
baseline = coefs[0]
ax.axhspan(baseline * 0.9, baseline * 1.1, alpha=0.05, color=PALETTE[3],
           label=f'基准±10% ({baseline*0.9:.3f}~{baseline*1.1:.3f})')

ax.set_xticks(n_controls)
ax.set_xticklabels(specs, fontsize=8, rotation=30, ha='right')
ax.set_ylabel('核心系数估计值', fontsize=11)
ax.set_xlabel('模型设定（逐步加入控制变量）', fontsize=11)
ax.legend(fontsize=8, frameon=False, labelspacing=0.35, handlelength=1.6, loc='best')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_coef_stability.pdf')
