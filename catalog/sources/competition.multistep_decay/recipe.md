## 17. 多步预测衰减图

**场景**：时间序列多步预测精度随预测步长的衰减趋势。
**要点**：多模型对比、置信区间带、终点数值标注、阈值参考线。

```python
import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
np.random.seed(42)

steps = np.arange(1, 13)
models = {
    '本文模型': 0.95 * np.exp(-0.08 * steps) + 0.02 * np.random.randn(len(steps)),
    'LSTM': 0.90 * np.exp(-0.10 * steps) + 0.03 * np.random.randn(len(steps)),
    'ARIMA': 0.85 * np.exp(-0.15 * steps) + 0.04 * np.random.randn(len(steps)),
}

fig, ax = plt.subplots(figsize=(7, 4.5))
highlight_index = 0  # 重点系列的位置，与显示名称无关
ax.grid(True, linestyle='--', alpha=0.15); ax.set_axisbelow(True)

for i, (name, vals) in enumerate(models.items()):
    is_ours = i == highlight_index
    lw = 2.5 if is_ours else 1.5
    alpha = 1.0 if is_ours else 0.6
    ax.plot(steps, vals, color=PALETTE[i], linewidth=lw, marker='o', markersize=5,
            markeredgecolor='white', markeredgewidth=1, label=name, alpha=alpha, zorder=3)
    if is_ours:
        std = 0.03 * np.sqrt(steps)
        ax.fill_between(steps, vals-std, vals+std, alpha=0.12, color=PALETTE[i])

# 阈值线
ax.axhline(0.5, color=COLORS['ref_line'], linewidth=0.8, linestyle='--', alpha=0.5)
ax.text(steps[-1]+0.3, 0.5, '可用阈值', fontsize=8, color=COLORS['ref_line'], va='center')

ax.set_xlabel('预测步长', fontsize=11); ax.set_ylabel('R² 分数', fontsize=11)
ax.set_xticks(steps)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='best')
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_multistep_decay.pdf')
```

**⚠ 多步预测衰减图定制生成注意事项：**
```python
# 1. 终点数值标注用 smart_labels()，多条曲线终点值接近时自动推开防重叠
# 2. 衰减率标注放在曲线末端下方，不要和曲线交叉重叠
# 3. 阈值线标签放在图右边缘：ax.text(x_max+0.3, threshold, ...)
```

---
