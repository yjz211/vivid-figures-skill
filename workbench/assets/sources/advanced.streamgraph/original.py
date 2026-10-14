import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()
np.random.seed(42)

# === 模拟 5 个类别在 50 个时间点的数值 ===
n_t = 50; n_cat = 5
t = np.arange(n_t)
# 每个类别有不同的生命周期形状
shapes = [
    20 + 30 * np.exp(-((t - 20)**2) / 250),                # 凸起在中间
    10 + 15 * (1 / (1 + np.exp(-0.2 * (t - 25)))),         # 后期增长
    25 - 20 * (1 / (1 + np.exp(-0.2 * (t - 15)))) + 5,     # 早期衰退
    18 * np.sin(t * 0.3) ** 2 + 5,                         # 周期波动
    12 + np.random.normal(0, 2, n_t)                        # 平稳基线
]
data = np.array([gaussian_filter1d(s, sigma=2) for s in shapes])
data = np.clip(data, 0.5, None)  # 保证非负

# === 居中基线：每个时刻总值除以 2，作为偏移 ===
total = data.sum(axis=0)
baseline = -total / 2  # 起点放底，向上堆叠
fig, ax = plt.subplots(figsize=(9, 4.5))

names = ['类别 A', '类别 B', '类别 C', '类别 D', '类别 E']
cumsum = baseline.copy()
for i, (vals, name) in enumerate(zip(data, names)):
    color = PALETTE[i % len(PALETTE)]
    ax.fill_between(t, cumsum, cumsum + vals,
                    color=_lighten(color, 0.25), alpha=0.88,
                    edgecolor=color, linewidth=0.5, label=name)
    # ★ 末端标签：放在每条流带末端的中心
    end_mid = cumsum[-1] + vals[-1] / 2
    ax.text(t[-1] + 0.7, end_mid, name, fontsize=8, va='center',
            color=color, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.18', facecolor='white',
                      edgecolor=color, alpha=0.9, linewidth=0.5))
    cumsum += vals

# 中心参考线
ax.axhline(0, color=COLORS['ref_line'], linewidth=0.5, alpha=0.4, linestyle='-')

ax.set_xlabel('时间', fontsize=10)
ax.set_yticks([])  # 居中堆叠图通常省略 y 轴刻度（数值由颜色面积表达）
ax.set_xlim(t[0], t[-1] + 7)
for sp in ['top', 'right', 'left']: ax.spines[sp].set_visible(False)
ax.tick_params(axis='y', length=0)
ax.grid(axis='x', alpha=0.08, linestyle='--', color=COLORS['grid'])

# 顶部小注释解释读法
ax.text(0.02, 0.97, '流带厚度 = 该时刻的数值；垂直位置无意义',
        transform=ax.transAxes, fontsize=7, color=COLORS['text'],
        style='italic', va='top',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                  edgecolor=COLORS['grid'], alpha=0.85, linewidth=0.3))

fig.tight_layout()
save_fig(fig, 'figures/fig_streamgraph.pdf')
