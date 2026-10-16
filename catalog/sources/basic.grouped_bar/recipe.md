## 1. 分组柱状图（Grouped Bar）— 淡色填充 + 原色边框 + 参考线 + 顶部数值 + 最优高亮

**场景**：多方法在多指标上的对比，如不同模型在 Accuracy/F1/Recall 上的得分对比。
**要点**：淡色填充+原色边框柱体、水平参考线标注均值、顶部数值标注、最优值★高亮、误差线、淡色背景渐变 + 柱子阴影。

```python
import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

categories = ['指标A', '指标B', '指标C', '指标D']
groups = {
    '本文方法': [85.2, 78.3, 92.1, 88.5],
    '方法B':   [82.1, 80.5, 88.7, 85.2],
    '方法C':   [79.8, 75.2, 85.3, 82.0],
}
stds = {
    '本文方法': [1.2, 1.5, 0.8, 1.0],
    '方法B':   [1.8, 2.0, 1.3, 1.5],
    '方法C':   [2.1, 2.5, 1.6, 1.8],
}

fig, ax = plt.subplots(figsize=(9, 5.5))
highlight_index = 0  # 重点系列的位置，与显示名称无关
x = np.arange(len(categories))
n = len(groups)
width = 0.22

# 淡蓝背景渐变
ax.axhspan(0, max(max(v) for v in groups.values()) * 1.2, alpha=0.03, color=PALETTE[0], zorder=0)

for i, (name, vals) in enumerate(groups.items()):
    offset = (i - n / 2 + 0.5) * width
    is_ours = i == highlight_index
    # 柱子阴影
    ax.bar(x + offset + 0.02, vals, width, color='#cccccc', alpha=0.08, zorder=1)
    # ★ 主柱子：淡色填充 + 原色边框
    bars = ax.bar(x + offset, vals, width, yerr=stds[name], capsize=3,
                  color=_lighten(PALETTE[i], 0.4), edgecolor=PALETTE[i],
                  linewidth=1.5 if is_ours else 1.2,
                  label=name, zorder=2,
                  error_kw={'elinewidth': 0.8, 'capthick': 0.6, 'color': COLORS['text']})

    for j, (bar, v, s) in enumerate(zip(bars, vals, stds[name])):
        all_vals_j = [groups[g][j] for g in groups]
        is_best = (v == max(all_vals_j))
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + s + 0.5,
                f'{"★" if is_best else ""}{v:.1f}',
                ha='center', va='bottom', fontsize=7.5,
                fontweight='bold' if is_best else 'normal',
                color=PALETTE[i] if is_best else COLORS['text'],
                bbox=dict(boxstyle='round,pad=0.1', facecolor='white', edgecolor='none', alpha=0.7) if is_best else {})

# 水平参考线：全局均值
global_mean = np.mean([v for vals in groups.values() for v in vals])
ax.axhline(y=global_mean, color=COLORS['ref_line'], linestyle='--', linewidth=0.8, alpha=0.4)
ax.text(len(categories) - 0.3, global_mean + 0.5, f'均值 {global_mean:.1f}',
        fontsize=8, color=COLORS['ref_line'], ha='right', style='italic',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='none', alpha=0.8))

ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=10)
ax.set_ylabel('得分', fontsize=11)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='best')
ax.set_ylim(0, max(max(v) for v in groups.values()) * 1.2)
ax.grid(axis='y', alpha=0.12, linestyle='--', color=COLORS['grid'])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_grouped_bar.pdf')
```

**★ 防遮挡技巧（分组柱状图专用）：**
```python
# 1. 顶部数值标签：bar_height + 0.01，不要放在柱子内部（柱子矮时会溢出）
# 2. 柱子多（>6 组 × 4 指标）时：fontsize 降到 7，或只标注最优值
# 3. ylim 上方留 15%：ax.set_ylim(0, max_val * 1.15)，给标签留空间
# 4. x 轴标签长（中文>4 字）：rotation=15, ha='right'，防止重叠
# 5. 图例放在图外上方：bbox_to_anchor=(0.5, 1.12), loc='center', ncol=N
# 6. 参考线标注放在图右边缘：x=len(categories)-0.5，不要放在数据密集区
```

---
