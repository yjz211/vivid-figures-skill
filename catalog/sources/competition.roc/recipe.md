## 11. ROC 曲线 + AUC 对比

**场景**：多分类模型的 ROC 曲线对比，展示各模型的判别能力。
**要点**：多条 ROC 曲线、对角线参考线、AUC 值在图例中标注、最优模型用粗线突出。

```python
import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS
setup_style()
np.random.seed(42)

models = {
    '本文模型 (AUC=0.952)': (0.952, 2.5),
    '随机森林 (AUC=0.921)': (0.921, 1.5),
    'SVM (AUC=0.887)': (0.887, 1.5),
    '逻辑回归 (AUC=0.845)': (0.845, 1.5),
}

fig, ax = plt.subplots(figsize=(6, 5.5))
highlight_index = 0  # 重点系列的位置，与显示名称无关
ax.grid(True, linestyle='--', alpha=0.15); ax.set_axisbelow(True)
ax.plot([0,1],[0,1], '--', color=COLORS['ref_line'], linewidth=0.8, label='随机猜测')

for i, (name, (auc, lw)) in enumerate(models.items()):
    fpr = np.sort(np.concatenate([[0], np.random.beta(1, auc*10, 50), [1]]))
    tpr = np.sort(np.concatenate([[0], np.random.beta(auc*10, 1, 50), [1]]))
    alpha = 1.0 if i == highlight_index else 0.6
    ax.plot(fpr, tpr, color=PALETTE[i], linewidth=lw, label=name, alpha=alpha, zorder=3)

ax.set_xlabel('假阳性率 (FPR)', fontsize=11); ax.set_ylabel('真阳性率 (TPR)', fontsize=11)
ax.set_xlim(-0.02, 1.02); ax.set_ylim(-0.02, 1.02)
ax.legend(frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=9, loc='lower right')
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_roc.pdf')
```

**⚠ ROC 曲线定制生成注意事项：**
```python
# 1. 终点数值标注不要和曲线重叠，xytext 偏移到曲线下方空白处
# 2. 多条 ROC 曲线接近时，本文模型用粗线（lw=2.5），其他用细线（lw=1.5, alpha=0.6）
# 3. 图例放 lower right（ROC 曲线从左下到右上，右下角通常空）
```

---
