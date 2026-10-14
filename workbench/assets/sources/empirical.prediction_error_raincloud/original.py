import numpy as np, matplotlib.pyplot as plt
from scipy.stats import gaussian_kde, ttest_1samp
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
models = ['Ours','LSTM','ARIMA','Prophet']
errors = [np.random.normal(0,1.5,200), np.random.normal(0.5,3,200),
          np.random.normal(1,4,200), np.random.normal(0.3,2.5,200)]

# ★ 自适应高度
_fig_h = max(4, len(models) * 1.2 + 1)
fig, ax = plt.subplots(figsize=(9, _fig_h))
for i, (model, err) in enumerate(zip(models, errors)):
    y_pos = i * 1.5
    kde = gaussian_kde(err)
    x_kde = np.linspace(err.min(), err.max(), 200)
    y_kde = kde(x_kde); y_kde_norm = y_kde / y_kde.max() * 0.5

    n_layers = 12
    for k in range(n_layers, 0, -1):
        frac = k / n_layers
        ax.fill_between(x_kde, y_pos, y_pos + y_kde_norm*frac, alpha=0.03, color=PALETTE[i], linewidth=0)
    ax.fill_between(x_kde, y_pos, y_pos + y_kde_norm, alpha=0.2, color=PALETTE[i], linewidth=0)
    ax.plot(x_kde, y_pos + y_kde_norm, color=PALETTE[i], linewidth=1.2)

    ax.boxplot([err], positions=[y_pos], vert=False, widths=0.18, patch_artist=True,
               boxprops=dict(facecolor=_lighten(PALETTE[i], 0.4), edgecolor=PALETTE[i], linewidth=1.2),
               medianprops=dict(color=COLORS['text'], linewidth=1.5),
               whiskerprops=dict(color=PALETTE[i]), capprops=dict(color=PALETTE[i]),
               flierprops=dict(marker='.', markersize=2, alpha=0.3))

    jitter = np.random.uniform(-0.1, -0.4, len(err))
    ax.scatter(err[::4], y_pos + jitter[:len(err[::4])], s=5, alpha=0.25, color=PALETTE[i], zorder=2)

    q1, q3 = np.percentile(err, [25, 75]); iqr = q3 - q1
    outlier_mask = (err < q1-2.5*iqr) | (err > q3+2.5*iqr)
    outliers = err[outlier_mask]
    if len(outliers) > 0:
        ax.scatter(outliers, [y_pos]*len(outliers), s=30, color=COLORS['down'], marker='x', zorder=6, linewidth=1.5)
        for ov in outliers[:3]:
            ax.text(ov, y_pos+0.6, f'{ov:.1f}', ha='center', va='bottom', fontsize=7, color=COLORS['down'], fontweight='bold')

    t_stat, p_val = ttest_1samp(err, 0)
    sig_str = '***' if p_val < 0.001 else ('**' if p_val < 0.01 else ('*' if p_val < 0.05 else 'ns'))
    ax.text(err.max()+1, y_pos, f't={t_stat:.2f} {sig_str}', ha='left', va='center', fontsize=8, color=COLORS['text'],
            bbox=dict(boxstyle='round,pad=0.2', facecolor=COLORS['bg_box'], edgecolor=COLORS['grid'], alpha=0.9))

ax.axvline(0, color=COLORS['down'], linestyle='--', linewidth=1.0, alpha=0.6)
ax.text(0, len(models)*1.5-0.3, 'Zero Error', ha='center', va='bottom', fontsize=8, color=COLORS['down'],
        bbox=dict(boxstyle='round,pad=0.2', facecolor=COLORS['bg_box'], edgecolor=COLORS['down'], alpha=0.9))
ax.set_yticks([i*1.5 for i in range(len(models))]); ax.set_yticklabels(models, fontsize=10)
ax.set_xlabel('Prediction Error', fontsize=11); ax.grid(axis='x', alpha=0.15, linestyle='--')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_error_raincloud.pdf')
