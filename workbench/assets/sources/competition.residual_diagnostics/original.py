import numpy as np, matplotlib.pyplot as plt
from scipy import stats
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
np.random.seed(42)
n = 200
y_true = np.random.uniform(10, 100, n)
y_pred = y_true + np.random.normal(0, 5, n)
residuals = y_pred - y_true
std_resid = (residuals - residuals.mean()) / residuals.std()

fig, axes = plt.subplots(2, 2, figsize=(5.0, 4.9))   # 示例尺寸；保留模板比例，按实际显示尺寸检查字号与布局
# (1) 残差 vs 拟合值
ax = axes[0, 0]
ax.scatter(y_pred, std_resid, s=15, alpha=0.5, color=PALETTE[0], edgecolor='white', linewidth=0.3)
ax.axhline(0, color=COLORS['ref_line'], linewidth=0.8, linestyle='--')
ax.axhline(2, color=COLORS['down'], linewidth=0.5, linestyle=':', alpha=0.5)
ax.axhline(-2, color=COLORS['down'], linewidth=0.5, linestyle=':', alpha=0.5)
ax.set_xlabel('拟合值', fontsize=10); ax.set_ylabel('标准化残差', fontsize=10)
ax.set_title('残差 vs 拟合值', fontsize=11)
# (2) Q-Q 图
ax = axes[0, 1]
(osm, osr), (slope, intercept, r) = stats.probplot(std_resid, dist='norm')
ax.scatter(osm, osr, s=15, alpha=0.5, color=PALETTE[1], edgecolor='white', linewidth=0.3)
ax.plot(osm, slope*np.array(osm)+intercept, '--', color=COLORS['down'], linewidth=1.2)
ax.set_xlabel('理论分位数', fontsize=10); ax.set_ylabel('样本分位数', fontsize=10)
ax.set_title('Q-Q 图', fontsize=11)
# (3) 残差直方图
ax = axes[1, 0]
ax.hist(std_resid, bins=25, density=True, color=PALETTE[0], alpha=0.4, edgecolor=PALETTE[0], linewidth=0.8)
xr = np.linspace(-4, 4, 100)
ax.plot(xr, stats.norm.pdf(xr), color=PALETTE[1], linewidth=2, label='正态分布')
ax.set_xlabel('标准化残差', fontsize=10); ax.set_ylabel('密度', fontsize=10)
ax.set_title('残差分布', fontsize=11); ax.legend(fontsize=8)
# (4) 残差自相关
ax = axes[1, 1]
lags = range(1, min(30, n//5))
acf = [np.corrcoef(std_resid[:-l], std_resid[l:])[0,1] for l in lags]
ax.bar(list(lags), acf, color=PALETTE[2], alpha=0.6, edgecolor=PALETTE[2], linewidth=0.8)
ci = 1.96 / np.sqrt(n)
ax.axhline(ci, color=COLORS['down'], linewidth=0.5, linestyle='--', alpha=0.5)
ax.axhline(-ci, color=COLORS['down'], linewidth=0.5, linestyle='--', alpha=0.5)
ax.axhline(0, color=COLORS['ref_line'], linewidth=0.5)
ax.set_xlabel('滞后阶数', fontsize=10); ax.set_ylabel('自相关系数', fontsize=10)
ax.set_title('残差自相关', fontsize=11)
for a in axes.flat:
    a.spines['top'].set_visible(False); a.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_residual_diag.pdf')
