import numpy as np; from _utils.palette_maps import palette_cmap, palette_stops, contrast_text
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()

np.random.seed(42)
tokens = ['[CLS]', 'The', 'model', 'learns', 'to', 'attend', 'key', 'features', '[SEP]']
n = len(tokens)
attn = np.random.dirichlet(np.ones(n) * 0.5, size=n)
attn += np.eye(n) * 0.3
attn[0, 5:8] += 0.2
attn[3, 6:8] += 0.15
attn = attn / attn.sum(axis=1, keepdims=True)

fig = plt.figure(figsize=(8, 7))
gs = gridspec.GridSpec(2, 2, width_ratios=[1, 6], height_ratios=[1, 6],
                       wspace=0.02, hspace=0.02)

# Top dendrogram
ax_dtop = fig.add_subplot(gs[0, 1])
Z_col = linkage(pdist(attn.T), method='ward')
dendrogram(Z_col, ax=ax_dtop, no_labels=True, color_threshold=0,
           above_threshold_color=PALETTE[0])
ax_dtop.set_xticks([])
ax_dtop.set_yticks([])
for spine in ax_dtop.spines.values():
    spine.set_visible(False)

# Left dendrogram
ax_dleft = fig.add_subplot(gs[1, 0])
Z_row = linkage(pdist(attn), method='ward')
dendrogram(Z_row, ax=ax_dleft, orientation='left', no_labels=True,
           color_threshold=0, above_threshold_color=PALETTE[0])
ax_dleft.set_xticks([])
ax_dleft.set_yticks([])
for spine in ax_dleft.spines.values():
    spine.set_visible(False)

# Main heatmap
ax_heat = fig.add_subplot(gs[1, 1])
im = ax_heat.imshow(attn, cmap=palette_cmap('sequential'), aspect='auto')
ax_heat.set_xticks(range(n))
ax_heat.set_xticklabels(tokens, rotation=45, ha='right', fontsize=8)
ax_heat.set_yticks(range(n))
ax_heat.set_yticklabels(tokens, fontsize=8)
ax_heat.set_xlabel('Key', fontsize=10)
ax_heat.set_ylabel('Query', fontsize=10)

# Value annotations (only > 0.12)
for i in range(n):
    for j in range(n):
        if attn[i, j] > 0.12:
            ax_heat.text(j, i, f'{attn[i, j]:.2f}', ha='center', va='center',
                         fontsize=6.5, color=contrast_text(im.cmap(im.norm(attn[i, j]))))

# Attention entropy annotation (right side)
entropy = -np.sum(attn * np.log(attn + 1e-10), axis=1)
for i, (tok, h) in enumerate(zip(tokens, entropy)):
    ax_heat.text(n + 0.3, i, f'H={h:.2f}', fontsize=6.5, va='center', color=COLORS['ref_line'])

fig.colorbar(im, ax=ax_heat, shrink=0.6, label='Attention Weight', pad=0.12)
fig.tight_layout()
save_fig(fig, 'figures/fig_attention.pdf')
