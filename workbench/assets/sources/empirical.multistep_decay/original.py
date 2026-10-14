import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
steps = np.arange(1, 13)
models_data = {'Ours': 0.95*np.exp(-0.03*steps)+np.random.randn(12)*0.005,
               'LSTM': 0.92*np.exp(-0.05*steps)+np.random.randn(12)*0.008,
               'GRU': 0.91*np.exp(-0.045*steps)+np.random.randn(12)*0.007,
               'ARIMA': 0.88*np.exp(-0.08*steps)+np.random.randn(12)*0.01}

fig, ax = plt.subplots(figsize=(9, 5))
all_vals = np.array(list(models_data.values()))
best_line, worst_line = all_vals.max(axis=0), all_vals.min(axis=0)

n_layers = 15
for k in range(n_layers, 0, -1):
    frac = k / n_layers
    ax.fill_between(steps, worst_line, worst_line+frac*(best_line-worst_line),
                    alpha=0.02, color=PALETTE[0], linewidth=0)
ax.fill_between(steps, worst_line, best_line, alpha=0.06, color=PALETTE[0], linewidth=0, label='Model Spread')

threshold = 0.80
ax.axhline(y=threshold, color=COLORS['up'], linestyle='--', linewidth=1.2, alpha=0.7)
ax.axhspan(0, threshold, color=COLORS['bg_box'], alpha=0.15, zorder=0)
ax.axhspan(threshold, 1.0, color=_lighten(COLORS['up'], 0.8), alpha=0.1, zorder=0)
ax.text(12.3, threshold, 'Acceptable\nThreshold', ha='left', va='center', fontsize=8, color=COLORS['up'],
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=COLORS['up'], alpha=0.9))

markers = ['o','s','D','^']
for i, (name, acc) in enumerate(models_data.items()):
    lw = 2.5 if name == 'Ours' else 1.5; ms = 7 if name == 'Ours' else 5
    ax.plot(steps, acc, f'{markers[i]}-', color=PALETTE[i], linewidth=lw, markersize=ms,
            label=name, markeredgecolor='white', markeredgewidth=0.8, zorder=5)
    if name in ['Ours', 'ARIMA']:
        decay_rate = (acc[0]-acc[-1])/acc[0]*100
        ax.annotate(f'Decay: {decay_rate:.1f}%', xy=(steps[-1], acc[-1]),
                    xytext=(steps[-1]-2.5, acc[-1]-0.04), fontsize=8, color=PALETTE[i],
                    arrowprops=dict(arrowstyle='->', color=PALETTE[i], lw=1.0, connectionstyle='arc3,rad=0.2'),
                    bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor=PALETTE[i], alpha=0.9))

ax.set_xlabel('Prediction Horizon (steps ahead)', fontsize=11); ax.set_ylabel('R² Score', fontsize=11)
ax.set_xticks(steps); ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='lower left', ncol=2)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(alpha=0.15, linestyle='--'); ax.set_ylim(0.55, 1.0)
fig.tight_layout()
save_fig(fig, 'figures/fig_multistep_decay.pdf')
