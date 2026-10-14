from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

np.random.seed(42)
t_treat = np.sort(np.random.exponential(20, 50))
t_ctrl = np.sort(np.random.exponential(12, 50))

def km_curve_data(times):
    n = len(times)
    surv = np.ones(n + 1)
    t_plot = np.zeros(n + 1)
    for i, t in enumerate(times):
        surv[i + 1] = surv[i] * (n - i - 1) / (n - i)
        t_plot[i + 1] = t
    return t_plot, surv

def number_at_risk(times, time_points):
    return [np.sum(times >= tp) for tp in time_points]

fig = plt.figure(figsize=(8, 6))
gs = gridspec.GridSpec(2, 1, height_ratios=[4, 1], hspace=0.08)
ax = fig.add_subplot(gs[0])
ax_risk = fig.add_subplot(gs[1])

# Subtle grid
ax.grid(alpha=0.15, linestyle='-', color=COLORS['grid'])
ax.set_axisbelow(True)

# Treatment group
t1, s1 = km_curve_data(t_treat)
ax.step(t1, s1, where='post', color=PALETTE[0], linewidth=2.5, label='Treatment (n=50)')
# Gradient CI band
ci_upper = np.clip(s1 + 0.08 * np.sqrt(np.linspace(1, 0.1, len(s1))), 0, 1)
ci_lower = np.clip(s1 - 0.08 * np.sqrt(np.linspace(1, 0.1, len(s1))), 0, 1)
ax.fill_between(t1, ci_lower, ci_upper, step='post', alpha=0.12, color=PALETTE[0])

# Control group
t2, s2 = km_curve_data(t_ctrl)
ax.step(t2, s2, where='post', color=PALETTE[3], linewidth=2.5, label='Control (n=50)')
ci_upper2 = np.clip(s2 + 0.10 * np.sqrt(np.linspace(1, 0.1, len(s2))), 0, 1)
ci_lower2 = np.clip(s2 - 0.10 * np.sqrt(np.linspace(1, 0.1, len(s2))), 0, 1)
ax.fill_between(t2, ci_lower2, ci_upper2, step='post', alpha=0.12, color=PALETTE[3])

# Median survival markers with dashed lines
def find_median_survival(t_arr, s_arr):
    for i in range(len(s_arr) - 1):
        if s_arr[i] >= 0.5 and s_arr[i + 1] < 0.5:
            return t_arr[i + 1]
    return None

med_treat = find_median_survival(t1, s1)
med_ctrl = find_median_survival(t2, s2)

if med_treat is not None:
    ax.plot([med_treat, med_treat], [0, 0.5], '--', color=PALETTE[0], linewidth=1.0, alpha=0.7)
    ax.plot([0, med_treat], [0.5, 0.5], '--', color=PALETTE[0], linewidth=1.0, alpha=0.7)
    ax.scatter([med_treat], [0.5], color=PALETTE[0], s=60, zorder=5, marker='D',
               edgecolors='white', linewidths=1.0)
    ax.annotate(f'Median = {med_treat:.1f}m', xy=(med_treat, 0.5),
                xytext=(med_treat + 3, 0.58), fontsize=8, color=PALETTE[0],
                arrowprops=dict(arrowstyle='->', color=PALETTE[0], lw=0.8),
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))

if med_ctrl is not None:
    ax.plot([med_ctrl, med_ctrl], [0, 0.5], '--', color=PALETTE[3], linewidth=1.0, alpha=0.7)
    ax.plot([0, med_ctrl], [0.5, 0.5], '--', color=PALETTE[3], linewidth=1.0, alpha=0.7)
    ax.scatter([med_ctrl], [0.5], color=PALETTE[3], s=60, zorder=5, marker='D',
               edgecolors='white', linewidths=1.0)
    ax.annotate(f'Median = {med_ctrl:.1f}m', xy=(med_ctrl, 0.5),
                xytext=(med_ctrl + 3, 0.42), fontsize=8, color=PALETTE[3],
                arrowprops=dict(arrowstyle='->', color=PALETTE[3], lw=0.8),
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))

# Log-rank p-value annotation
ax.annotate('Log-rank p = 0.003',
            xy=(0.98, 0.98), xycoords='axes fraction', ha='right', va='top',
            fontsize=9, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.4', facecolor=_lighten(PALETTE[0], 0.7),
                      edgecolor=PALETTE[0], alpha=0.9))

ax.set_ylabel('Survival probability', fontsize=11)
ax.set_ylim(0, 1.05)
ax.set_xlim(left=0)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='best')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.set_xticklabels([])

# Number-at-risk table
time_points = np.arange(0, max(t_treat.max(), t_ctrl.max()) + 5, 10)
nar_treat = number_at_risk(t_treat, time_points)
nar_ctrl = number_at_risk(t_ctrl, time_points)

ax_risk.set_xlim(ax.get_xlim())
ax_risk.set_ylim(-0.5, 1.5)
for i, tp in enumerate(time_points):
    ax_risk.text(tp, 1, str(nar_treat[i]), ha='center', va='center',
                 fontsize=8, color=PALETTE[0], fontweight='bold')
    ax_risk.text(tp, 0, str(nar_ctrl[i]), ha='center', va='center',
                 fontsize=8, color=PALETTE[3], fontweight='bold')
ax_risk.text(-2, 1, 'Treatment', ha='right', va='center', fontsize=8,
             color=PALETTE[0], fontweight='bold')
ax_risk.text(-2, 0, 'Control', ha='right', va='center', fontsize=8,
             color=PALETTE[3], fontweight='bold')
ax_risk.set_xlabel('Time (months)', fontsize=11)
ax_risk.set_yticks([])
ax_risk.spines['top'].set_visible(False)
ax_risk.spines['right'].set_visible(False)
ax_risk.spines['left'].set_visible(False)
ax_risk.set_title('Number at risk', fontsize=8, loc='left', fontstyle='italic')

fig.tight_layout()
save_fig(fig, 'figures/fig_kaplan_meier.pdf')
