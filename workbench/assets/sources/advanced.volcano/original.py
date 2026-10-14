from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

np.random.seed(42)
n = 2000
log2fc = np.random.normal(0, 1.5, n)
pvals = 10 ** (-np.abs(log2fc) * np.random.uniform(0.5, 3, n))
neg_log_p = -np.log10(pvals)
gene_names = [f'Gene_{i}' for i in range(n)]

sig_up = (log2fc > 1) & (neg_log_p > 2)
sig_down = (log2fc < -1) & (neg_log_p > 2)
ns = ~sig_up & ~sig_down

fig, ax = plt.subplots(figsize=(7, 5.5))

# Gradient density background (hexbin)
hb = ax.hexbin(log2fc, neg_log_p, gridsize=30, cmap='Blues', alpha=0.25,
               mincnt=1, linewidths=0.0, zorder=0)

# Fold-change threshold shading
ax.axvspan(-1, 1, alpha=0.06, color=COLORS['ref_line'], zorder=0, label='|FC| < 2')
ax.axvspan(1, log2fc.max() + 1, alpha=0.04, color=PALETTE[3], zorder=0)
ax.axvspan(log2fc.min() - 1, -1, alpha=0.04, color=PALETTE[0], zorder=0)

# Subtle grid
ax.grid(alpha=0.15, linestyle='-', color=COLORS['grid'])
ax.set_axisbelow(True)

# Scatter points
ax.scatter(log2fc[ns], neg_log_p[ns], c=COLORS['neutral'], alpha=0.35, s=8,
           label=f'NS ({ns.sum()})', zorder=2)
ax.scatter(log2fc[sig_up], neg_log_p[sig_up], c=PALETTE[3], alpha=0.7, s=15,
           label=f'Up ({sig_up.sum()})', edgecolors='white', linewidths=0.3, zorder=3)
ax.scatter(log2fc[sig_down], neg_log_p[sig_down], c=PALETTE[0], alpha=0.7, s=15,
           label=f'Down ({sig_down.sum()})', edgecolors='white', linewidths=0.3, zorder=3)

# Threshold lines
ax.axhline(2, color=COLORS['ref_line'], linestyle='--', linewidth=0.8, alpha=0.7)
ax.axvline(1, color=COLORS['ref_line'], linestyle='--', linewidth=0.8, alpha=0.7)
ax.axvline(-1, color=COLORS['ref_line'], linestyle='--', linewidth=0.8, alpha=0.7)

# Gene labels for top hits (top 5 by significance)
all_sig = np.where(sig_up | sig_down)[0]
if len(all_sig) > 0:
    top_idx = all_sig[np.argsort(neg_log_p[all_sig])[-5:]]
    for idx in top_idx:
        ax.annotate(gene_names[idx],
                    xy=(log2fc[idx], neg_log_p[idx]),
                    xytext=(log2fc[idx] + 0.3 * np.sign(log2fc[idx]),
                            neg_log_p[idx] + 0.5),
                    fontsize=7, fontstyle='italic',
                    color=COLORS['text'],
                    arrowprops=dict(arrowstyle='->', color=COLORS['text'], lw=0.7),
                    bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                              edgecolor=COLORS['neutral'], alpha=0.85))

ax.set_xlabel('$\\log_2$(Fold Change)', fontsize=11)
ax.set_ylabel('$-\\log_{10}$(p-value)', fontsize=11)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8, loc='best',
          fancybox=True)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_volcano.pdf')
