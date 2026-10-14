import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()
np.random.seed(42)

# === 模拟时序：历史 24 个月 + 预测 12 个月 ===
n_hist = 24; n_pred = 12
t = np.arange(n_hist + n_pred)
hist = 100 + np.cumsum(np.random.normal(0, 1.5, n_hist))
# 预测：均值随机游走，方差随时间扩散
pred_mean = hist[-1] + np.cumsum(np.random.normal(0.3, 0.5, n_pred))
pred_std = np.sqrt(np.arange(1, n_pred + 1)) * 1.6   # 不确定性随时间增长

# 预测分位数
quantiles = {
    'p05': pred_mean - 1.96 * pred_std, 'p95': pred_mean + 1.96 * pred_std,
    'p10': pred_mean - 1.28 * pred_std, 'p90': pred_mean + 1.28 * pred_std,
    'p25': pred_mean - 0.67 * pred_std, 'p75': pred_mean + 0.67 * pred_std,
}

fig, ax = plt.subplots(figsize=(8, 4.5))

# === 历史段：实线 ===
ax.plot(t[:n_hist], hist, color=COLORS['text'], linewidth=1.8, zorder=4, label='历史值')
ax.scatter(t[n_hist-1], hist[-1], s=50, color=COLORS['text'], zorder=5,
           edgecolor='white', linewidth=1)

# === 预测段：多层 CI 带（外到内 alpha 递增）===
t_pred = t[n_hist-1:]
# 拼接：起点用历史最后值，让带子接续
pred_full = np.concatenate(([hist[-1]], pred_mean))
quant_full = {k: np.concatenate(([hist[-1]], v)) for k, v in quantiles.items()}

# 5%-95%（外层，最浅）
ax.fill_between(t_pred, quant_full['p05'], quant_full['p95'],
                color=_lighten(PALETTE[0], 0.65), alpha=0.55, linewidth=0,
                label='95% 区间', zorder=1)
# 10%-90%
ax.fill_between(t_pred, quant_full['p10'], quant_full['p90'],
                color=_lighten(PALETTE[0], 0.4), alpha=0.7, linewidth=0,
                label='80% 区间', zorder=2)
# 25%-75%（内层，最深）
ax.fill_between(t_pred, quant_full['p25'], quant_full['p75'],
                color=_lighten(PALETTE[0], 0.2), alpha=0.8, linewidth=0,
                label='50% 区间', zorder=3)
# 中位数预测线（虚线区别历史）
ax.plot(t_pred, pred_full, color=PALETTE[0], linewidth=1.8, linestyle='--', zorder=4,
        label='中位数预测')

# === 历史/预测分隔线 ===
ax.axvline(n_hist - 1, color=COLORS['ref_line'], linestyle=':', linewidth=1.1, alpha=0.6)
ax.text(n_hist - 1, ax.get_ylim()[1] * 0.97 if False else hist.max() * 1.02,
        '预测起点', fontsize=8, ha='center', va='bottom',
        color=COLORS['ref_line'], style='italic',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                  edgecolor=COLORS['grid'], alpha=0.9, linewidth=0.4))

# === 终点不确定性范围标注 ===
y_min = quant_full['p05'][-1]; y_max = quant_full['p95'][-1]
ax.annotate('', xy=(t[-1] + 0.2, y_min), xytext=(t[-1] + 0.2, y_max),
            arrowprops=dict(arrowstyle='<->', color=COLORS['highlight'], lw=1.2))
ax.text(t[-1] + 0.8, (y_min + y_max) / 2,
        f'95% 跨度\n{y_max - y_min:.1f}', fontsize=8, va='center',
        color=COLORS['highlight'], fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                  edgecolor=COLORS['highlight'], alpha=0.9, linewidth=0.5))

ax.set_xlabel('时间（月）', fontsize=10)
ax.set_ylabel('指标值', fontsize=10)
ax.legend(loc='upper left', frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8, ncol=2)
ax.grid(axis='y', alpha=0.12, linestyle='--', color=COLORS['grid'])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.set_xlim(0, t[-1] + 3)
fig.tight_layout()
save_fig(fig, 'figures/fig_fan_chart.pdf')
