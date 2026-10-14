import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from _utils.plot_utils import setup_style, save_fig, PALETTE, smart_labels, auto_legend
setup_style()

# === Example data (replace with your PCA results) ===
np.random.seed(42)
n_samples, n_features = 80, 12
feature_names = ['市场规模', '供应链成熟度', '短期恢复能力', '响应梯度元素',
                 '长期恢复速度', '研发投入强度', '短期恢复弹性', '产能利用率',
                 '短期集中度', '专利授权量', '产业链完整度', '客户集中度']

# Simulated PCA scores and loadings
scores = np.random.randn(n_samples, 2) * 2
loadings = np.random.randn(n_features, 2)
loadings = loadings / np.abs(loadings).max(axis=0) * 3  # scale to [-3, 3]
explained_var = [66.3, 11.4]  # explained variance %

fig, ax = plt.subplots(figsize=(8, 7))

# Scatter: sample scores (gray, semi-transparent)
ax.scatter(scores[:, 0], scores[:, 1], s=25, alpha=0.35, color=COLORS['gray'],
           edgecolors='white', linewidths=0.3, zorder=2)

# Loading arrows
arrow_colors = []
for i, (name, lx, ly) in enumerate(zip(feature_names, loadings[:, 0], loadings[:, 1])):
    magnitude = np.sqrt(lx**2 + ly**2)
    color = PALETTE[0]
    arrow_colors.append(color)
    ax.annotate('', xy=(lx, ly), xytext=(0, 0),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.5, alpha=0.7))

# ── 特征名标签 —— smart_labels 自动推开重叠标签
# Offset labels slightly beyond arrow tips
label_xs = [lx * 1.08 for lx in loadings[:, 0]]
label_ys = [ly * 1.08 for ly in loadings[:, 1]]
smart_labels(ax, label_xs, label_ys, feature_names,
             colors=arrow_colors, fontsize=8.5, fontweight='bold',
             offset=(5, 0),
             bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                       edgecolor=PALETTE[0], alpha=0.8, linewidth=0.5),
             arrowprops=dict(arrowstyle='-', color=COLORS['grid'], lw=0.4),
             force_text=0.8, force_points=0.5)

# Reference lines
ax.axhline(0, color=COLORS['ref_line'], linewidth=0.5, alpha=0.4)
ax.axvline(0, color=COLORS['ref_line'], linewidth=0.5, alpha=0.4)

ax.set_xlabel(f'PC1 ({explained_var[0]:.1f}%)', fontsize=11)
ax.set_ylabel(f'PC2 ({explained_var[1]:.1f}%)', fontsize=11)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(alpha=0.1, linestyle='--')
fig.tight_layout()
save_fig(fig, 'figures/fig_pca_biplot.pdf')
