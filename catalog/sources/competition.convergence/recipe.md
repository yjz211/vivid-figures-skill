## 1. 收敛曲线对比图

**场景**：多算法迭代优化过程对比，展示收敛速度和最终目标值。优化类问题必备。
**要点**：本文方法用粗线+填充区域突出、其他方法用细线+低透明度、终点数值标注用 smart_labels 防重叠、收敛点箭头标注。

```python
import numpy as np
import matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()

np.random.seed(42)
iters = np.arange(0, 501, 5)
methods = {
    '遗传算法 (GA)': 100*np.exp(-0.008*iters) + 5 + np.random.normal(0,0.5,len(iters))*0.5,
    '粒子群 (PSO)': 100*np.exp(-0.012*iters) + 3 + np.random.normal(0,0.4,len(iters))*0.5,
    '模拟退火 (SA)': 100*np.exp(-0.006*iters) + 8 + np.random.normal(0,0.6,len(iters))*0.5,
    '本文算法': 100*np.exp(-0.018*iters) + 1.5 + np.random.normal(0,0.2,len(iters))*0.3,
}

fig, ax = plt.subplots(figsize=(7, 4.5))
highlight_index = min(3, len(methods) - 1)  # 重点系列的位置，与显示名称无关
ax.grid(True, linestyle='--', alpha=0.15, color=COLORS['grid']); ax.set_axisbelow(True)

_end_xs, _end_ys, _end_texts, _end_colors = [], [], [], []
for i, (name, vals) in enumerate(methods.items()):
    lw = 2.5 if i == highlight_index else 1.5
    alpha = 1.0 if i == highlight_index else 0.55
    ax.plot(iters, vals, color=PALETTE[i], linewidth=lw, label=name, alpha=alpha, zorder=3)
    _end_xs.append(iters[-1]); _end_ys.append(vals[-1])
    _end_texts.append(f'{vals[-1]:.1f}'); _end_colors.append(PALETTE[i])
# ★ 终点标注用 smart_labels 防重叠
from _utils.plot_utils import save_fig, smart_labels
smart_labels(ax, _end_xs, _end_ys, _end_texts, colors=_end_colors, fontsize=8, offset=(8, 0))

# 本文算法的下方填充区域（强调单独）
ours = list(methods.values())[highlight_index]
ax.fill_between(iters, ours, alpha=0.10, color=PALETTE[highlight_index], linewidth=0, zorder=1)

# 收敛点标注
diff = np.abs(np.diff(ours))
conv_idx = np.argmax(diff < 0.15) + 1
ax.annotate('收敛点', xy=(iters[conv_idx], ours[conv_idx]),
            xytext=(iters[conv_idx]+60, ours[conv_idx]+12),
            fontsize=10, color=COLORS['down'], fontweight='bold',
            arrowprops=dict(arrowstyle='->', color=COLORS['down'], lw=1.5), zorder=5)
ax.scatter([iters[conv_idx]], [ours[conv_idx]], color=COLORS['down'], s=50, zorder=5, edgecolors='white')

ax.set_xlabel('迭代次数', fontsize=11); ax.set_ylabel('目标函数值', fontsize=11)
# ★ 图例用 loc='best' 自适应，不要硬编码 'upper right'（避免数据在右上角时遮挡图例）
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='best')
ax.set_xlim(0, 520)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_convergence.pdf')
```

**⚠ 收敛曲线定制生成注意事项：**
```python
# 1. 终点数值标注用 smart_labels()，多条曲线终点值接近时自动推开防重叠
# 2. 收敛点标注箭头要指向曲线的拐点区域，方向朝空白处
# 3. 本文算法的填充区域 alpha 用 0.10（太深会遮挡其他曲线）
# 4. 收敛曲线的下降趋势：图例放 'upper right' 可能遮挡
#    - 最小化问题（曲线从高到低）：图例放 'upper right' 右上空
#    - 最大化问题（曲线从低到高）：图例放 'lower right' 右下空
#    - 不确定方向时用 loc='best' 让 matplotlib 自动选择
#    - 或者把图例放到图外：bbox_to_anchor=(1.02, 1), loc='upper left'
# 5. 曲线数 >4 条时，考虑本文方法用粗线 alpha=1.0 突出，其他用细线 alpha=0.55 降低视觉权重
# 6. 标注文字不要和图例重叠（标注放在曲线空白处，图例在另一侧）
```

**图例位置选择辅助函数：**
```python
# 根据数据分布选择图例位置（不要硬编码 'upper right'）
# 对于收敛曲线等场景的图表：
def smart_legend_loc(ax):
    """根据数据分布自动选择图例位置"""
    # 简单方案：直接用 matplotlib 的 best
    ax.legend(loc='best', frameon=False, edgecolor='#DDD', fontsize=9)
    # 如果 best 不够好的话可以把图例移到图外
    # ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', frameon=False, fontsize=9)
```

---
