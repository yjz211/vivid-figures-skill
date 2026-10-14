import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

x = np.linspace(-2, 2, 80)
y = np.linspace(-2, 2, 80)
X, Y = np.meshgrid(x, y)
Z = 0.5 * (X ** 2 + Y ** 2) - 0.3 * np.cos(2 * np.pi * X) * np.cos(2 * np.pi * Y) + 1

fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection='3d')
surf = ax.plot_surface(X, Y, Z, cmap='coolwarm', alpha=0.65, edgecolor='none',
                       antialiased=True, rstride=2, cstride=2)

# Contour projection on floor
ax.contour(X, Y, Z, zdir='z', offset=Z.min() - 0.5, cmap='coolwarm', alpha=0.3, levels=15)

# Optimization trajectory (simulated SGD path)
np.random.seed(42)
traj_x = [1.8]
traj_y = [1.5]
lr = 0.05
for step in range(60):
    gx = traj_x[-1] - 0.3 * 2 * np.pi * np.sin(2 * np.pi * traj_x[-1]) * np.cos(2 * np.pi * traj_y[-1])
    gy = traj_y[-1] - 0.3 * 2 * np.pi * np.cos(2 * np.pi * traj_x[-1]) * np.sin(2 * np.pi * traj_y[-1])
    nx = traj_x[-1] - lr * gx + np.random.normal(0, 0.02)
    ny = traj_y[-1] - lr * gy + np.random.normal(0, 0.02)
    traj_x.append(np.clip(nx, -2, 2))
    traj_y.append(np.clip(ny, -2, 2))

traj_x = np.array(traj_x)
traj_y = np.array(traj_y)
traj_z = 0.5 * (traj_x ** 2 + traj_y ** 2) - 0.3 * np.cos(2 * np.pi * traj_x) * np.cos(
    2 * np.pi * traj_y) + 1 + 0.05

# Gradient-colored trajectory (red→blue)
for k in range(len(traj_x) - 1):
    frac = k / (len(traj_x) - 1)
    color = plt.cm.coolwarm(1 - frac)  # red (early) → blue (late)
    ax.plot(traj_x[k:k + 2], traj_y[k:k + 2], traj_z[k:k + 2],
            color=color, linewidth=1.5, alpha=0.8)

# Start and end markers
ax.scatter([traj_x[0]], [traj_y[0]], [traj_z[0]], color=COLORS['down'], s=80,
           marker='^', edgecolor='white', linewidth=1, zorder=6, label='Start')
ax.scatter([traj_x[-1]], [traj_y[-1]], [traj_z[-1]], color=COLORS['up'], s=80,
           marker='*', edgecolor='white', linewidth=1, zorder=6, label='End')

# Global minimum
ax.scatter([0], [0], [Z.min()], color=COLORS['down'], s=120, marker='*',
           edgecolor='white', zorder=5, label='Global Min')

# Saddle point annotations
saddle_pts = [(-1, 0), (0, -1), (1, 0)]
for sx, sy in saddle_pts:
    sz = 0.5 * (sx ** 2 + sy ** 2) - 0.3 * np.cos(2 * np.pi * sx) * np.cos(2 * np.pi * sy) + 1
    ax.scatter([sx], [sy], [sz], color=PALETTE[2], s=40, marker='o',
               edgecolor='white', zorder=5)
    ax.text(sx, sy, sz + 0.15, 'saddle', fontsize=6, color=COLORS['ref_line'], ha='center')

ax.set_xlabel('θ₁', fontsize=10, labelpad=6)
ax.set_ylabel('θ₂', fontsize=10, labelpad=6)
ax.set_zlabel('Loss', fontsize=10, labelpad=6)
ax.view_init(elev=30, azim=135)
ax.tick_params(labelsize=8)
ax.legend(fontsize=8, loc='best')
fig.colorbar(surf, shrink=0.4, aspect=15, pad=0.12)
fig.tight_layout()
save_fig(fig, 'figures/fig_loss_landscape.pdf')
