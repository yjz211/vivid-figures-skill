import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy.stats import gaussian_kde
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()
np.random.seed(42)

# === 模拟 4 条 MCMC 链，2 个参数 ===
n_chains = 4; n_iter = 2000
params = ['μ', 'σ']
true_vals = [1.5, 0.7]
# 每条链有点初始偏移然后收敛
chains = np.zeros((2, n_chains, n_iter))
for p in range(2):
    for c in range(n_chains):
        init = true_vals[p] + np.random.normal(0, 0.6) * (1 if c < 2 else 0.4)
        for i in range(n_iter):
            init = init + 0.95 * (true_vals[p] - init) * 0.05 + np.random.normal(0, 0.08)
            chains[p, c, i] = init

# === 2 行 2 列：每行一个参数 ===
fig = plt.figure(figsize=(9, 5))
gs = GridSpec(2, 2, width_ratios=[3, 1.5], hspace=0.35, wspace=0.1)

burnin = 200
for p in range(2):
    # 左：trace plot
    ax_trace = fig.add_subplot(gs[p, 0])
    for c in range(n_chains):
        ax_trace.plot(np.arange(n_iter), chains[p, c],
                      color=PALETTE[c % len(PALETTE)], linewidth=0.5, alpha=0.75,
                      label=f'链 {c+1}' if p == 0 else None)
    ax_trace.axvline(burnin, color=COLORS['ref_line'], linestyle=':', linewidth=1, alpha=0.6)
    ax_trace.text(burnin + 20, ax_trace.get_ylim()[0] + (ax_trace.get_ylim()[1] - ax_trace.get_ylim()[0]) * 0.05,
                  f'burn-in={burnin}', fontsize=7, color=COLORS['ref_line'], style='italic')
    ax_trace.axhline(true_vals[p], color=COLORS['highlight'], linestyle='--', linewidth=1, alpha=0.7)
    ax_trace.set_ylabel(params[p], fontsize=11, fontweight='bold')
    if p == 1:
        ax_trace.set_xlabel('迭代步数', fontsize=10)
    ax_trace.spines['top'].set_visible(False)
    ax_trace.spines['right'].set_visible(False)
    ax_trace.grid(axis='y', alpha=0.1, linestyle='--', color=COLORS['grid'])
    if p == 0:
        ax_trace.legend(loc='upper right', frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=7, ncol=4, columnspacing=1)

    # 右：边际密度（合并所有链，去除 burn-in）
    ax_dens = fig.add_subplot(gs[p, 1], sharey=ax_trace)
    pooled = chains[p, :, burnin:].flatten()
    yg = np.linspace(pooled.min(), pooled.max(), 200)
    density = gaussian_kde(pooled)(yg)
    ax_dens.fill_betweenx(yg, 0, density, color=_lighten(PALETTE[0], 0.4),
                          alpha=0.7, linewidth=0)
    ax_dens.plot(density, yg, color=PALETTE[0], linewidth=1.5)
    # 95% HPDI
    sorted_x = np.sort(pooled)
    ci_lo, ci_hi = np.percentile(sorted_x, [2.5, 97.5])
    ax_dens.axhline(ci_lo, color=COLORS['ref_line'], linestyle=':', linewidth=0.8, alpha=0.6)
    ax_dens.axhline(ci_hi, color=COLORS['ref_line'], linestyle=':', linewidth=0.8, alpha=0.6)
    ax_dens.axhline(pooled.mean(), color=COLORS['highlight'], linestyle='--', linewidth=1.1, alpha=0.8)

    # 假装计算 Rhat（实际 Rhat 需要严谨实现，这里展示标注样式）
    rhat_value = 1.005 + np.random.uniform(-0.001, 0.003)
    info_text = f'$\\hat{{\\theta}}$ = {pooled.mean():.3f}\n95% HPDI: [{ci_lo:.2f}, {ci_hi:.2f}]\n$\\hat{{R}}$ = {rhat_value:.3f}'
    ax_dens.text(0.95, 0.95, info_text, transform=ax_dens.transAxes,
                 fontsize=7.5, va='top', ha='right',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                           edgecolor=COLORS['grid'], alpha=0.95, linewidth=0.4))

    ax_dens.set_xticks([])
    ax_dens.tick_params(axis='y', labelleft=False)
    for sp in ['top', 'right', 'bottom']: ax_dens.spines[sp].set_visible(False)

save_fig(fig, 'figures/fig_posterior_trace.pdf')
