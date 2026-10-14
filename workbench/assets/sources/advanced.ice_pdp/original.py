import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()
np.random.seed(42)

# === 模拟 ICE 曲线（200 个样本，特征 x 从 0 到 10）===
n_samples = 200
x_grid = np.linspace(0, 10, 80)
# 每个样本的随机基线 + 非线性形状
baselines = np.random.normal(0.5, 0.15, n_samples)
shape_strength = np.random.normal(1.0, 0.25, n_samples)
ice_curves = np.array([
    baselines[i] + shape_strength[i] * (0.45 / (1 + np.exp(-1.2*(x_grid - 4))) + 0.08 * np.sin(x_grid * 0.6))
    + np.random.normal(0, 0.02, len(x_grid))
    for i in range(n_samples)
])
pdp = ice_curves.mean(axis=0)
pdp_ci_lo = np.percentile(ice_curves, 5, axis=0)
pdp_ci_hi = np.percentile(ice_curves, 95, axis=0)

# 样本特征分布（边际）
x_samples = np.random.beta(2.5, 2.0, n_samples * 3) * 10  # 中心偏左的分布

# === 双面板：上 ICE+PDP，下 边际分布 ===
fig = plt.figure(figsize=(7, 5.2))
gs = GridSpec(2, 1, height_ratios=[4, 1], hspace=0.04)
ax = fig.add_subplot(gs[0])
ax_marg = fig.add_subplot(gs[1], sharex=ax)

# ★ ICE 细线（每条 alpha 极低，重叠出"密度感"）
for i in range(n_samples):
    ax.plot(x_grid, ice_curves[i], color=PALETTE[0], linewidth=0.5, alpha=0.06, zorder=1)

# ★ PDP 95% CI 带（外层浅、内层稍深）
ax.fill_between(x_grid, pdp_ci_lo, pdp_ci_hi, color=_lighten(PALETTE[0], 0.55),
                alpha=0.45, linewidth=0, zorder=2, label='90% 区间')

# ★ PDP 中位数线 — 主信号
ax.plot(x_grid, pdp, color=PALETTE[0], linewidth=2.6, zorder=3, label='PDP (均值)')
# 加白色描边让曲线在 ICE 海里更突出
ax.plot(x_grid, pdp, color='white', linewidth=4.5, zorder=2.5, alpha=0.6)
ax.plot(x_grid, pdp, color=PALETTE[0], linewidth=2.6, zorder=3)

# ★ 拐点标注
turn_idx = np.argmax(np.abs(np.gradient(pdp)))
ax.scatter([x_grid[turn_idx]], [pdp[turn_idx]], s=80, color=COLORS['highlight'],
           edgecolor='white', linewidth=1.5, zorder=5, marker='o')
ax.annotate(f'拐点\n(x={x_grid[turn_idx]:.1f})',
            xy=(x_grid[turn_idx], pdp[turn_idx]),
            xytext=(15, 18), textcoords='offset points',
            fontsize=8, fontweight='bold', color=COLORS['highlight'],
            arrowprops=dict(arrowstyle='->', color=COLORS['highlight'], lw=1.1, alpha=0.7),
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                      edgecolor=COLORS['highlight'], alpha=0.9, linewidth=0.6))

ax.set_ylabel('预测值 (P(y=1))', fontsize=10)
ax.legend(loc='lower right', frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.tick_params(axis='x', labelbottom=False)
ax.grid(axis='y', alpha=0.1, linestyle='--', color=COLORS['grid'])

# ★ 底部 rug + 直方图：告诉读者 PDP 在哪些 x 上有数据
ax_marg.hist(x_samples, bins=40, color=_lighten(PALETTE[0], 0.4), alpha=0.85,
             edgecolor=PALETTE[0], linewidth=0.4)
ax_marg.set_xlabel('特征 x', fontsize=10)
ax_marg.set_ylabel('样本密度', fontsize=8)
ax_marg.spines['top'].set_visible(False)
ax_marg.spines['right'].set_visible(False)
ax_marg.tick_params(axis='y', labelsize=7)

save_fig(fig, 'figures/fig_ice_pdp.pdf')
