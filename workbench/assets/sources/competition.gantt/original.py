import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

tasks = ['任务A', '任务B', '任务C', '任务D', '任务E', '任务F', '任务G', '任务H']
starts = [0, 2, 1, 5, 3, 7, 6, 9]
durations = [3, 4, 2, 3, 5, 2, 4, 3]
machines = [0, 1, 0, 2, 1, 0, 2, 1]
machine_names = ['机器M1', '机器M2', '机器M3']

n = len(tasks)
_fig_h = max(5, n * 0.35 + 1)
fig, ax = plt.subplots(figsize=(10, _fig_h))
ax.grid(axis='x', alpha=0.12, linestyle='--', color=COLORS['grid']); ax.set_axisbelow(True)

for i in range(n):
    c = PALETTE[machines[i] % len(PALETTE)]
    ax.barh(i, durations[i], left=starts[i], height=0.6,
            color=_lighten(c, 0.3), edgecolor=c, linewidth=1.3, zorder=3)
    ax.text(starts[i] + durations[i]/2, i, f'J{i+1}', ha='center', va='center',
            fontsize=8, fontweight='bold', color=c)

# Makespan 标注（放在 axes 内部顶端，避免 tight_layout 压缩导致标注飘远）
makespan = max(s+d for s, d in zip(starts, durations))
ax.axvline(makespan, color=COLORS['down'], linewidth=1.5, linestyle='--', zorder=4)
# ⛔ 不要用 y=1.02 + transform=ax.get_xaxis_transform()（会被 tight_layout 压缩导致标注飘远）
# 改用 axes 内部坐标：放在第一个任务条的上方
ax.text(makespan, -0.8, f'Makespan={makespan}h',
        ha='center', va='center', fontsize=9, fontweight='bold', color=COLORS['down'],
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=COLORS['down'], alpha=0.9))

# 图例
legend_elements = [plt.Rectangle((0,0), 1, 1, facecolor=_lighten(PALETTE[j], 0.3), edgecolor=PALETTE[j], linewidth=1.3)
                   for j, name in enumerate(machine_names)]
ax.legend(handles=legend_elements, labels=machine_names, frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8, ncol=len(machine_names), loc='best')
ax.set_yticks(range(n)); ax.set_yticklabels(tasks, fontsize=10)
ax.set_xlabel('时间 (h)', fontsize=11)
ax.invert_yaxis()
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_gantt.pdf')
