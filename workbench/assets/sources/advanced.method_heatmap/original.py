from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten; from _utils.palette_maps import palette_cmap, palette_stops, contrast_text
setup_style()
import matplotlib.pyplot as plt
import numpy as np
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist

methods = ['Ours', 'LSTM', 'Random Forest', 'Linear Reg']
metrics = ['MAE', 'RMSE', 'R2', 'MAPE(%)', 'Speed']
# Lower is better for MAE/RMSE/MAPE, higher for R2/Speed
data = np.array([
    [0.29, 1.05, 0.987, 2.1, 0.85],
    [72.23, 85.4, 0.812, 15.3, 0.60],
    [0.45, 1.82, 0.965, 3.8, 0.92],
    [137.08, 152.3, 0.421, 48.2, 0.98],
])
higher_better = [False, False, True, False, True]

# Rank medals
rank_symbols = ['🥇', '🥈', '🥉', '④']

# Normalize for color mapping
norm_data = np.zeros_like(data)
for j in range(data.shape[1]):
    col = data[:, j]
    if higher_better[j]:
        norm_data[:, j] = (col - col.min()) / (col.max() - col.min() + 1e-10)
    else:
        norm_data[:, j] = 1 - (col - col.min()) / (col.max() - col.min() + 1e-10)

# Compute overall ranking (average normalized rank)
overall_rank_score = np.mean(norm_data, axis=1)

# Add overall ranking column
metrics_ext = metrics + ['Overall']
data_ext = np.column_stack([data, overall_rank_score])
norm_ext = np.column_stack([norm_data, overall_rank_score / overall_rank_score.max()])

fig = plt.figure(figsize=(9, 4.5))

# Dendrogram on top
ax_dendro = fig.add_axes([0.15, 0.82, 0.65, 0.14])
Z = linkage(pdist(norm_data), method='ward')
dn = dendrogram(Z, labels=methods, ax=ax_dendro, leaf_font_size=0,
                color_threshold=0, above_threshold_color=COLORS['ref_line'])
ax_dendro.set_axis_off()
row_order = dn['leaves']

# Heatmap
ax = fig.add_axes([0.15, 0.12, 0.72, 0.68])
ordered_norm = norm_ext[row_order]
ordered_data = data_ext[row_order]
ordered_methods = [methods[i] for i in row_order]

im = ax.imshow(ordered_norm, cmap=palette_cmap('sequential'), aspect='auto', vmin=0, vmax=1)
ax.set_xticks(range(len(metrics_ext)))
ax.set_xticklabels(metrics_ext, fontsize=10)
ax.set_yticks(range(len(methods)))
ax.set_yticklabels(ordered_methods, fontsize=10)

# Annotate with values, ranks, and 浅色填充+原色边框 for best
for j in range(len(metrics_ext)):
    if j < len(metrics):
        col_vals = data[:, j]
        if higher_better[j]:
            rank_order = np.argsort(-col_vals)
        else:
            rank_order = np.argsort(col_vals)
    else:
        rank_order = np.argsort(-overall_rank_score)

    for i_orig, rank_pos in enumerate(rank_order):
        # Find position in ordered display
        i_display = row_order.index(rank_pos)
        if j < len(metrics):
            val_str = f'{data[rank_pos, j]:.2f}'
        else:
            val_str = f'{overall_rank_score[rank_pos]:.2f}'

        rank_idx = i_orig
        rank_label = rank_symbols[rank_idx] if rank_idx < len(rank_symbols) else ''

        color = contrast_text(im.cmap(im.norm(ordered_norm[i_display, j])))
        weight = 'bold' if rank_idx == 0 else 'normal'

        ax.text(j, i_display, f'{val_str}\n{rank_label}', ha='center', va='center',
                fontsize=8.5, fontweight=weight, color=color)

        # 列最优：浅色填充背景 + 原色粗边框
        if rank_idx == 0:
            rect = plt.Rectangle((j - 0.5, i_display - 0.5), 1, 1,
                                  linewidth=2.5, edgecolor=PALETTE[0],
                                  facecolor=_lighten(PALETTE[0], 0.5),
                                  alpha=0.3, zorder=4)
            ax.add_patch(rect)
            # 原色边框（不透明）
            rect_border = plt.Rectangle((j - 0.5, i_display - 0.5), 1, 1,
                                         linewidth=2.5, edgecolor=PALETTE[0],
                                         facecolor='none', zorder=5)
            ax.add_patch(rect_border)

ax.spines[:].set_visible(False)

# Colorbar
ax_cbar = fig.add_axes([0.89, 0.12, 0.02, 0.68])
cbar = plt.colorbar(im, cax=ax_cbar)
cbar.set_label('Normalized (1=best)', fontsize=8)
cbar.ax.tick_params(labelsize=7)

save_fig(fig, 'figures/fig_method_heatmap.pdf')
