import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

# === Example data (replace with actual IRF results) ===
periods = np.arange(0, 16)
responses = {
    '数字经济 → 数字经济': {'irf': [1.0, 0.8, 0.5, 0.3, 0.15, 0.08, 0.04, 0.02, 0.01, 0.005, 0, 0, 0, 0, 0, 0],
                          'lower': None, 'upper': None},
    '算力基础设施 → 数字经济': {'irf': [0, 0.15, 0.25, 0.30, 0.28, 0.22, 0.16, 0.11, 0.07, 0.04, 0.02, 0.01, 0, 0, 0, 0],
                              'lower': None, 'upper': None},
    '数字经济 → 算力基础设施': {'irf': [0, 0.05, 0.12, 0.18, 0.20, 0.18, 0.14, 0.10, 0.07, 0.04, 0.02, 0.01, 0, 0, 0, 0],
                              'lower': None, 'upper': None},
    '算力基础设施 → 算力基础设施': {'irf': [1.0, 0.7, 0.4, 0.2, 0.1, 0.05, 0.02, 0.01, 0, 0, 0, 0, 0, 0, 0, 0],
                                  'lower': None, 'upper': None},
}

# Generate CI bands
for key in responses:
    irf = np.array(responses[key]['irf'])
    noise = np.abs(irf) * 0.3 + 0.02
    responses[key]['lower'] = irf - noise
    responses[key]['upper'] = irf + noise

n_panels = len(responses)
ncols = 2
nrows = (n_panels + 1) // 2
fig, axes = plt.subplots(nrows, ncols, figsize=(10, 4 * nrows), sharex=True)
axes = axes.flatten()

for idx, (title, data) in enumerate(responses.items()):
    ax = axes[idx]
    irf = np.array(data['irf'])
    lower = np.array(data['lower'])
    upper = np.array(data['upper'])

    # Gradient CI bands (3 layers)
    for layer, alpha in enumerate([0.08, 0.15, 0.25]):
        shrink = (1 - layer * 0.3)
        mid = irf
        ax.fill_between(periods, mid - (mid - lower) * shrink, mid + (upper - mid) * shrink,
                        alpha=alpha, color=PALETTE[idx % len(PALETTE)])

    # IRF line
    ax.plot(periods, irf, '-o', color=PALETTE[idx % len(PALETTE)], linewidth=2,
            markersize=4, markeredgecolor='white', markeredgewidth=0.8, zorder=5)

    # Zero reference
    ax.axhline(0, color=COLORS['ref_line'], linewidth=0.8, linestyle='--', alpha=0.5)

    # Significance shading (where CI doesn't cross zero)
    for t in range(len(periods)):
        if lower[t] > 0 or upper[t] < 0:
            ax.axvspan(t - 0.4, t + 0.4, alpha=0.04, color=PALETTE[idx % len(PALETTE)])

    ax.set_title(title, fontsize=9, fontweight='bold', loc='center', pad=3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_ylabel('响应', fontsize=9)

for idx in range(n_panels, len(axes)):
    axes[idx].set_visible(False)

axes[-2].set_xlabel('期数', fontsize=10)
axes[-1].set_xlabel('期数', fontsize=10)
fig.tight_layout()
save_fig(fig, 'figures/fig_irf.pdf')
