import numpy as np, matplotlib.pyplot as plt; from _utils.palette_maps import palette_cmap, palette_stops, contrast_text
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

models = ['LSTM','GRU','Transformer','ARIMA','Prophet','Ours']
metrics = ['MAE↓','RMSE↓','MAPE(%)↓','R²↑']
data = np.array([[3.21,4.15,5.8,0.921],[3.45,4.38,6.2,0.908],[2.98,3.87,5.1,0.935],
                  [5.12,6.73,9.4,0.842],[4.67,5.92,8.1,0.867],[2.45,3.21,4.3,0.952]])

norm = np.zeros_like(data)
for j in range(data.shape[1]):
    col = data[:, j]
    if '↓' in metrics[j]: norm[:, j] = (col-col.min())/(col.max()-col.min()+1e-10)
    else: norm[:, j] = 1 - (col-col.min())/(col.max()-col.min()+1e-10)

avg_score = norm.mean(axis=1); sort_idx = np.argsort(avg_score)
data = data[sort_idx]; norm = norm[sort_idx]; models = [models[i] for i in sort_idx]
rank_symbols = ['①','②','③','④','⑤','⑥']

fig, ax = plt.subplots(figsize=(8, 5))
im = ax.imshow(norm, cmap=palette_cmap('sequential'), aspect='auto', vmin=0, vmax=1)

for j in range(data.shape[1]):
    col = data[:, j]
    ranks = np.argsort(np.argsort(col)) if '↓' in metrics[j] else np.argsort(np.argsort(-col))
    best_idx = np.argmin(col) if '↓' in metrics[j] else np.argmax(col)
    for i in range(data.shape[0]):
        txt_color = contrast_text(im.cmap(im.norm(norm[i, j])))
        w = 'bold' if i == best_idx else 'normal'
        rank_str = f' {rank_symbols[ranks[i]]}' if ranks[i] < 3 else ''
        ax.text(j, i, f'{data[i,j]:.2f}{rank_str}', ha='center', va='center',
                fontsize=9.5, fontweight=w, color=txt_color)
        if i == best_idx:
            ax.add_patch(plt.Rectangle((j-0.5, i-0.5), 1, 1, linewidth=2.5,
                                        edgecolor=COLORS['up'], facecolor='none', zorder=5))

ax.set_xticks(range(len(metrics))); ax.set_xticklabels(metrics, fontsize=10.5)
ax.set_yticks(range(len(models))); ax.set_yticklabels(models, fontsize=10.5)
cbar = fig.colorbar(im, ax=ax, shrink=0.7, pad=0.20)
cbar.set_label('Normalized Score\n(0=Best, 1=Worst)', fontsize=9)
ax.spines[:].set_visible(False)
ax.tick_params(top=True, bottom=False, labeltop=True, labelbottom=False)
for i in range(len(models)):
    ax.text(len(metrics)-0.25, i, f'Avg: {avg_score[sort_idx[i]]:.2f}', ha='left', va='center', fontsize=8, color=COLORS['text'])
fig.tight_layout()
save_fig(fig, 'figures/fig_model_accuracy_heatmap.pdf')
