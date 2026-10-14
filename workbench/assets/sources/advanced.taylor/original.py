import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Arc
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten, smart_labels
setup_style()

# === Example data (replace with your model evaluation results) ===
# Reference (observed) statistics
ref_std = 1.0  # normalized

# Model results: (correlation, normalized_std)
models = {
    'Ours':        (0.95, 1.02),
    'LSTM':        (0.88, 0.85),
    'XGBoost':     (0.91, 1.15),
    'SVR':         (0.82, 0.78),
    'Linear Reg':  (0.75, 1.30),
}

fig, ax = plt.subplots(figsize=(7, 7))

# Draw reference arcs (constant correlation lines)
max_std = 1.6
for corr in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]:
    theta = np.arccos(corr)
    r_vals = np.linspace(0, max_std, 100)
    x_arc = r_vals * np.cos(theta)
    y_arc = r_vals * np.sin(theta)
    ax.plot(x_arc, y_arc, color=COLORS['grid'], linewidth=0.5, alpha=0.6)
    ax.text(max_std * np.cos(theta) * 1.03, max_std * np.sin(theta) * 1.03,
            f'{corr}', fontsize=7, color=COLORS['ref_line'], ha='center', va='center',
            rotation=np.degrees(theta) - 90)

# Draw std arcs (centered at origin)
for s in [0.25, 0.5, 0.75, 1.0, 1.25, 1.5]:
    theta_range = np.linspace(0, np.pi / 2, 100)
    ax.plot(s * np.cos(theta_range), s * np.sin(theta_range),
            color=COLORS['grid'], linewidth=0.5, linestyle='--')

# Draw RMSE arcs (centered at reference point) —— 暖橙色
ref_x, ref_y = ref_std, 0
for rmse in [0.25, 0.5, 0.75, 1.0, 1.25]:
    theta_range = np.linspace(0, np.pi, 200)
    cx = ref_x + rmse * np.cos(theta_range)
    cy = rmse * np.sin(theta_range)
    mask = (cx >= 0) & (cy >= 0) & (np.sqrt(cx**2 + cy**2) <= max_std)
    if mask.any():
        ax.plot(cx[mask], cy[mask], color=COLORS['highlight'], linewidth=0.5,
                alpha=0.4, linestyle=':')

# Reference point
ax.scatter(ref_std, 0, s=150, color=COLORS['text'], marker='*', zorder=10, label='Observed')

# ── 绘制模型点：浅色填充+原色边框 标记
label_xs, label_ys, label_texts, label_colors = [], [], [], []
for i, (name, (corr, std)) in enumerate(models.items()):
    theta = np.arccos(corr)
    x = std * np.cos(theta)
    y = std * np.sin(theta)
    color = PALETTE[i % len(PALETTE)]
    marker = 'D' if i == 0 else 'o'
    size = 140 if i == 0 else 90
    # 浅色填充 + 原色边框
    ax.scatter(x, y, s=size, color=_lighten(color, 0.35), marker=marker, zorder=5,
               edgecolors=color, linewidths=1.8, label=name)
    label_xs.append(x); label_ys.append(y)
    label_texts.append(name); label_colors.append(color)

# Smart labels to avoid overlap
smart_labels(ax, label_xs, label_ys, label_texts, colors=label_colors,
             fontsize=8.5, fontweight='bold', offset=(8, 5))

ax.set_xlim(0, max_std)
ax.set_ylim(0, max_std)
ax.set_aspect('equal')
ax.set_xlabel('标准差（归一化）', fontsize=11)
ax.set_ylabel('标准差（归一化）', fontsize=11)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.legend(loc='upper left', fontsize=9, frameon=False, edgecolor=COLORS['grid'])
fig.tight_layout()
save_fig(fig, 'figures/fig_taylor.pdf')
