import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()
np.random.seed(42)

# === 模拟数据：5 个算法在 30 个问题上的求解时间 ===
n_problems = 30
algos = ['本文方法', 'Baseline A', 'Baseline B', 'Baseline C', 'Heuristic']
# 每行一个问题，每列一个算法的求解时间
times = np.abs(np.random.lognormal(0, 0.6, (n_problems, len(algos))))
times[:, 0] *= 0.7   # 本文方法更快
times[10:15, 2] = np.inf  # Baseline B 有 5 个失败
times[5:8, 3] = np.inf    # Baseline C 失败 3 个

# === 计算 performance ratio ===
best = np.nanmin(np.where(np.isinf(times), np.nan, times), axis=1, keepdims=True)
rp = times / best  # 每问题每算法的相对比率
rp[np.isinf(times)] = np.inf

# === 计算累计分布 ρ_s(τ) = #{p : rp(p,s) ≤ τ} / n_problems ===
tau_grid = np.logspace(0, 1.0, 200)  # τ ∈ [1, 10]
rho = np.zeros((len(tau_grid), len(algos)))
for s in range(len(algos)):
    for i, tau in enumerate(tau_grid):
        rho[i, s] = np.mean(rp[:, s] <= tau)

fig, ax = plt.subplots(figsize=(7, 4.5))

markers = ['o', 's', '^', 'D', 'v']
for s, name in enumerate(algos):
    is_self = (s == 0)
    lw = 2.4 if is_self else 1.4
    alpha = 1.0 if is_self else 0.78
    # ★ 阶梯函数 — drawstyle='steps-post' 是 Dolan-Moré 标准
    ax.step(tau_grid, rho[:, s], where='post',
            color=PALETTE[s % len(PALETTE)],
            linewidth=lw, alpha=alpha,
            marker=markers[s % len(markers)], markersize=5,
            markevery=20, markeredgecolor='white', markeredgewidth=0.6,
            label=name + (' ★' if is_self else ''))

# ★ τ=1 处的左端值标注（"找到最优的比例"）
for s, name in enumerate(algos):
    rho0 = rho[0, s]
    if rho0 > 0.05:
        ax.text(1.02, rho0, f'{rho0:.2f}', fontsize=7,
                color=PALETTE[s % len(PALETTE)], va='center', ha='left',
                bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                          edgecolor=PALETTE[s % len(PALETTE)], alpha=0.85, linewidth=0.4))

# ★ "完美求解器"参考线（理论上限 ρ=1）
ax.axhline(1.0, color=COLORS['ref_line'], linestyle=':', linewidth=0.8, alpha=0.5)
ax.text(tau_grid[-1] * 0.95, 1.01, 'Ideal solver (ρ=1)',
        fontsize=7, color=COLORS['ref_line'], ha='right', va='bottom', style='italic')

# ★ 灰色背景区暗示"τ=1 = 全部找到最优"是稀有的
ax.axvspan(1.0, 1.05, alpha=0.08, color=COLORS['highlight'], zorder=0)

ax.set_xscale('log')
ax.set_xlim(1.0, tau_grid[-1])
ax.set_ylim(0, 1.05)
ax.set_xlabel(r'性能比率 $\tau$ (相对最优解的倍数, log scale)', fontsize=10)
ax.set_ylabel(r'$\rho_s(\tau)$  (在 $\tau$ 倍内解出的问题比例)', fontsize=10)
ax.legend(loc='lower right', frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8)
ax.grid(which='both', alpha=0.12, linestyle='--', color=COLORS['grid'])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_perf_profile.pdf')
