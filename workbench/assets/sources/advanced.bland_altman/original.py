from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

np.random.seed(42)
method1 = np.random.normal(50, 10, 100)
method2 = method1 + np.random.normal(0.5, 3, 100)
mean_vals = (method1 + method2) / 2
diff_vals = method1 - method2
mean_diff = np.mean(diff_vals)
std_diff = np.std(diff_vals)

fig, ax = plt.subplots(figsize=(7, 5.5))

# Subtle grid
ax.grid(alpha=0.15, linestyle='-', color=COLORS['grid'])
ax.set_axisbelow(True)

# Gradient CI band (fading from center outward)
x_range = np.linspace(mean_vals.min() - 2, mean_vals.max() + 2, 200)
upper = mean_diff + 1.96 * std_diff
lower = mean_diff - 1.96 * std_diff
# Inner band (darker)
ax.fill_between(x_range, mean_diff - 0.5 * std_diff, mean_diff + 0.5 * std_diff,
                alpha=0.15, color=PALETTE[0], label='±0.5 SD')
# Middle band
ax.fill_between(x_range, mean_diff - 1.0 * std_diff, mean_diff + 1.0 * std_diff,
                alpha=0.10, color=PALETTE[0])
# Outer band (lightest)
ax.fill_between(x_range, lower, upper, alpha=0.06, color=PALETTE[3], label='±1.96 SD (95% CI)')

# Scatter points
ax.scatter(mean_vals, diff_vals, color=PALETTE[0], alpha=0.55, s=30,
           edgecolors='white', linewidths=0.5, zorder=3)

# Mean line
ax.axhline(mean_diff, color=PALETTE[0], linestyle='-', linewidth=1.8,
           label=f'Mean bias: {mean_diff:.2f}')
# Limits of agreement
ax.axhline(upper, color=PALETTE[3], linestyle='--', linewidth=1.2,
           label=f'+1.96 SD: {upper:.2f}')
ax.axhline(lower, color=PALETTE[3], linestyle='--', linewidth=1.2,
           label=f'-1.96 SD: {lower:.2f}')

# Proportional bias regression line
z = np.polyfit(mean_vals, diff_vals, 1)
p = np.poly1d(z)
x_fit = np.linspace(mean_vals.min(), mean_vals.max(), 100)
ax.plot(x_fit, p(x_fit), color=COLORS['highlight'], linewidth=1.5, linestyle='-.',
        label=f'Prop. bias (slope={z[0]:.3f})', zorder=4)

# Outlier labels (points beyond ±1.96 SD)
outliers = np.where((diff_vals > upper) | (diff_vals < lower))[0]
for idx in outliers:
    ax.annotate(f'#{idx}', xy=(mean_vals[idx], diff_vals[idx]),
                xytext=(mean_vals[idx] + 1.5, diff_vals[idx] + 0.8),
                fontsize=7, color=COLORS['down'],
                arrowprops=dict(arrowstyle='->', color=COLORS['down'], lw=0.8),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                          edgecolor=COLORS['down'], alpha=0.9))

ax.set_xlabel('Mean of two methods', fontsize=11)
ax.set_ylabel('Difference (Method 1 − Method 2)', fontsize=11)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=7.5, loc='upper left',
          fancybox=True)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_bland_altman.pdf')
