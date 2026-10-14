import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()
np.random.seed(42)

n_nodes = 10
pos = np.random.rand(n_nodes, 2) * 8
labels = [f'N{i}' for i in range(n_nodes)]

# 随机生成边
edges = []
for i in range(n_nodes):
    for j in range(i+1, n_nodes):
        if np.random.rand() < 0.3:
            w = np.sqrt(np.sum((pos[i]-pos[j])**2))
            edges.append((i, j, w))

# 最优路径（模拟）
path = [0, 3, 7, 5, 9, 2, 6, 1, 8, 4, 0]

fig, ax = plt.subplots(figsize=(8, 7))
ax.grid(True, linestyle='--', alpha=0.1); ax.set_axisbelow(True)

# 普通边（浅色）
for i, j, w in edges:
    ax.plot([pos[i,0], pos[j,0]], [pos[i,1], pos[j,1]],
            color=COLORS['grid'], linewidth=0.8, alpha=0.3, zorder=1)

# 最优路径（粗线）
for k in range(len(path)-1):
    i, j = path[k], path[k+1]
    ax.plot([pos[i,0], pos[j,0]], [pos[i,1], pos[j,1]],
            color=PALETTE[0], linewidth=3, alpha=0.8, zorder=3)
    # 边权标签
    mx, my = (pos[i,0]+pos[j,0])/2, (pos[i,1]+pos[j,1])/2
    w = np.sqrt(np.sum((pos[i]-pos[j])**2))
    ax.text(mx, my, f'{w:.1f}', fontsize=7, ha='center', va='center',
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))

# 节点
for i in range(n_nodes):
    is_depot = (i == 0)
    c = COLORS['down'] if is_depot else PALETTE[0]
    s = 200 if is_depot else 120
    marker = 's' if is_depot else 'o'
    ax.scatter(pos[i,0], pos[i,1], s=s, color=_lighten(c, 0.3), edgecolor=c,
              linewidth=1.5, zorder=5, marker=marker)
    ax.text(pos[i,0], pos[i,1]+0.3, labels[i], ha='center', va='bottom',
            fontsize=9, fontweight='bold',
            bbox=dict(facecolor='white', alpha=0.8, edgecolor=COLORS['grid'], pad=1.5))

ax.set_xlabel('坐标 X', fontsize=11); ax.set_ylabel('坐标 Y', fontsize=11)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
fig.tight_layout()
save_fig(fig, 'figures/fig_network_path.pdf')
