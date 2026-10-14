import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde, pearsonr
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()
np.random.seed(42)

# === 模拟 4 个变量（含正/负/弱相关）===
n = 250
v1 = np.random.normal(0, 1, n)
v2 = 0.75 * v1 + np.random.normal(0, 0.55, n)        # 强正相关
v3 = -0.55 * v1 + 0.3 * v2 + np.random.normal(0, 0.7, n)  # 中等负相关
v4 = np.random.normal(0, 1, n)                        # 弱相关
data = np.column_stack([v1, v2, v3, v4])
names = ['X1', 'X2', 'X3', 'X4']
N = len(names)

fig, axes = plt.subplots(N, N, figsize=(8.5, 8.5))

for i in range(N):
    for j in range(N):
        ax = axes[i, j]
        if i == j:
            # ★ 对角线：直方图 + KDE
            ax.hist(data[:, i], bins=22, color=_lighten(PALETTE[i % len(PALETTE)], 0.55),
                    edgecolor=PALETTE[i % len(PALETTE)], linewidth=0.5, alpha=0.85)
            ax2 = ax.twinx()
            xg = np.linspace(data[:, i].min(), data[:, i].max(), 200)
            ax2.plot(xg, gaussian_kde(data[:, i])(xg),
                     color=PALETTE[i % len(PALETTE)], linewidth=1.5)
            ax2.set_yticks([])
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            ax2.spines['left'].set_visible(False)
            ax.text(0.05, 0.92, names[i], transform=ax.transAxes,
                    fontsize=11, fontweight='bold', color=PALETTE[i % len(PALETTE)],
                    va='top', ha='left')
        elif i > j:
            # ★ 下三角：散点 + 拟合线
            ax.scatter(data[:, j], data[:, i], s=10, alpha=0.35,
                       color=PALETTE[0], edgecolor='white', linewidth=0.2)
            # 简易线性拟合
            slope, intercept = np.polyfit(data[:, j], data[:, i], 1)
            xfit = np.linspace(data[:, j].min(), data[:, j].max(), 60)
            yfit = slope * xfit + intercept
            ax.plot(xfit, yfit, color=COLORS['highlight'], linewidth=1.4,
                    alpha=0.85, zorder=5)
        else:
            # ★ 上三角：相关系数（按强度上色 + 字号映射强度）
            r, p = pearsonr(data[:, j], data[:, i])
            # 强度映射到背景颜色
            if r > 0:
                bg = _lighten(PALETTE[0], 1 - abs(r) * 0.7)
            else:
                bg = _lighten(COLORS['down'], 1 - abs(r) * 0.7)
            ax.set_facecolor(bg)
            sig = '***' if p < 0.001 else ('**' if p < 0.01 else ('*' if p < 0.05 else ''))
            fs = 10 + abs(r) * 12  # 字号随 |r| 增大
            ax.text(0.5, 0.55, f'{r:+.2f}', transform=ax.transAxes,
                    fontsize=fs, fontweight='bold',
                    color=COLORS['text'], ha='center', va='center')
            if sig:
                ax.text(0.5, 0.18, sig, transform=ax.transAxes,
                        fontsize=11, color=COLORS['text'], ha='center')

        # 仅在最下/最左行留刻度
        if i < N - 1:
            ax.tick_params(axis='x', labelbottom=False)
        else:
            ax.tick_params(labelsize=7)
        if j > 0:
            ax.tick_params(axis='y', labelleft=False)
        else:
            ax.tick_params(labelsize=7)
        if i != j:
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.grid(alpha=0.08, linestyle='--', color=COLORS['grid'])

fig.tight_layout(pad=0.4)
save_fig(fig, 'figures/fig_pair_plot.pdf')
