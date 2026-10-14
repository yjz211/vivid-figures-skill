## 13. Prediction vs Actual with CI Band

**Scene**: Time series prediction with gradient CI band, error histogram on right margin, RMSE/MAE box, train/test gradient background.

```python
import numpy as np, matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy.stats import gaussian_kde
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
t = np.arange(100)
actual = 50 + 10*np.sin(t/10) + np.cumsum(np.random.randn(100)*0.5)
pred = actual + np.random.randn(100)*2
ci_upper = pred + 3 + np.abs(np.random.randn(100))*1.5
ci_lower = pred - 3 - np.abs(np.random.randn(100))*1.5
errors = actual - pred; split_point = 70

fig = plt.figure(figsize=(11, 5))
gs = GridSpec(1, 2, width_ratios=[5, 1], wspace=0.05)
ax = fig.add_subplot(gs[0])

ax.axvspan(0, split_point, color=_lighten(PALETTE[0], 0.8), alpha=0.3, zorder=0)
ax.axvspan(split_point, 100, color=_lighten(COLORS['highlight'], 0.8), alpha=0.3, zorder=0)
ax.axvline(x=split_point, color=COLORS['ref_line'], linestyle=':', linewidth=1.2, alpha=0.6)
ax.text(split_point/2, actual.max()+2, 'Training', ha='center', fontsize=9, color=COLORS['text'],
        bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor=COLORS['grid'], alpha=0.9))
ax.text((split_point+100)/2, actual.max()+2, 'Testing', ha='center', fontsize=9, color=COLORS['text'],
        bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor=COLORS['grid'], alpha=0.9))

n_layers = 12
for k in range(n_layers, 0, -1):
    frac = k / n_layers
    ax.fill_between(t, pred-frac*(pred-ci_lower), pred+frac*(ci_upper-pred),
                    alpha=0.025, color=PALETTE[1], linewidth=0)

ax.plot(t, actual, color=PALETTE[0], linewidth=1.8, label='Actual', zorder=4)
ax.plot(t, pred, color=PALETTE[1], linewidth=1.5, linestyle='--', label='Predicted', zorder=3)

te = actual[split_point:] - pred[split_point:]
rmse = np.sqrt(np.mean(te**2)); mae = np.mean(np.abs(te))
r2 = 1 - np.sum(te**2)/np.sum((actual[split_point:]-actual[split_point:].mean())**2)
ax.text(0.02, 0.03, f'Test Metrics:\nRMSE = {rmse:.3f}\nMAE  = {mae:.3f}\nR²   = {r2:.3f}',
        transform=ax.transAxes, fontsize=8.5, va='bottom', ha='left', color=COLORS['text'], family='monospace',
        bbox=dict(boxstyle='round,pad=0.4', facecolor=COLORS['bg_box'], edgecolor=COLORS['grid'], alpha=0.95))

ax.set_xlabel('Time Step'); ax.set_ylabel('Value (a.u.)')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9); ax.grid(alpha=0.15, linestyle='--')

ax_hist = fig.add_subplot(gs[1])
ax_hist.hist(errors, bins=25, orientation='horizontal', color=_lighten(PALETTE[1], 0.4), alpha=0.5, edgecolor=PALETTE[1], linewidth=0.8, density=True)
kde = gaussian_kde(errors); y_kde = np.linspace(errors.min(), errors.max(), 100)
ax_hist.plot(kde(y_kde), y_kde, color=PALETTE[1], linewidth=1.5)
ax_hist.axhline(0, color=COLORS['ref_line'], linestyle='--', linewidth=0.6, alpha=0.5)
ax_hist.set_xlabel('Density (1/a.u.)', fontsize=9)
ax_hist.set_ylabel('Actual − predicted (a.u.)', fontsize=9)
ax_hist.yaxis.set_label_position('right')
ax_hist.yaxis.tick_right()
ax_hist.tick_params(axis='y', labelsize=8, labelleft=False, labelright=True)
ax_hist.spines['top'].set_visible(False); ax_hist.spines['right'].set_visible(False)

fig.tight_layout()
save_fig(fig, 'figures/fig_prediction_ci.pdf')
```


---
