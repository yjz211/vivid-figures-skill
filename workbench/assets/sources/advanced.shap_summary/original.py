from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

np.random.seed(42)
features = ['Feature A', 'Feature B', 'Feature C', 'Feature D', 'Feature E']
n_samples = 200

fig = plt.figure(figsize=(9, 5))
gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1], wspace=0.05)

# Left panel: SHAP beeswarm
ax_shap = fig.add_subplot(gs[0])
ax_shap.grid(axis='x', alpha=0.15, linestyle='-', color=COLORS['grid'])
ax_shap.set_axisbelow(True)

mean_abs_shap = []
for i, feat in enumerate(features):
    shap_vals = np.random.randn(n_samples) * (len(features) - i) * 0.12
    feat_vals = np.random.rand(n_samples)
    y_jitter = np.random.uniform(-0.3, 0.3, n_samples) + i
    sc = ax_shap.scatter(shap_vals, y_jitter, c=feat_vals, cmap='coolwarm',
                         s=10, alpha=0.65, vmin=0, vmax=1, edgecolors='none')
    mean_abs_shap.append(np.mean(np.abs(shap_vals)))

ax_shap.set_yticks(range(len(features)))
ax_shap.set_yticklabels(features, fontsize=10)
ax_shap.set_xlabel('SHAP value (impact on prediction)', fontsize=10)
ax_shap.axvline(x=0, color=COLORS['ref_line'], linewidth=0.8, linestyle='--')
ax_shap.spines['top'].set_visible(False)
ax_shap.spines['right'].set_visible(False)

# Colorbar
cbar = plt.colorbar(sc, ax=ax_shap, shrink=0.5, pad=0.02, aspect=20)
cbar.set_label('Feature value', fontsize=8)
cbar.ax.tick_params(labelsize=7)

# Right panel: Mean |SHAP| importance bar —— 浅色填充 + 原色边框
ax_bar = fig.add_subplot(gs[1])
for i, v in enumerate(mean_abs_shap):
    is_top = (v == max(mean_abs_shap))
    c = PALETTE[0] if is_top else PALETTE[2]
    ax_bar.barh(i, v, color=_lighten(c, 0.4), edgecolor=c,
                linewidth=1.5, height=0.5, alpha=0.9)
    ax_bar.text(v + 0.002, i, f'{v:.3f}', va='center', fontsize=8, color=COLORS['text'])
ax_bar.set_yticks([])
ax_bar.set_xlabel('Mean |SHAP|', fontsize=9)
ax_bar.spines['top'].set_visible(False)
ax_bar.spines['right'].set_visible(False)
ax_bar.spines['left'].set_visible(False)

fig.tight_layout()
save_fig(fig, 'figures/fig_shap.pdf')
