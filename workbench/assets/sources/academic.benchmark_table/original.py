import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from _utils.plot_utils import setup_style, save_fig, PALETTE
setup_style()

np.random.seed(42)
classes = ['Class A', 'Class B', 'Class C']
n_per = 80
all_pts, all_labels = [], []
centers = [np.array([2, 2, 2]), np.array([-2, -1, 3]), np.array([0, -2, -1])]
for i, (cls, center) in enumerate(zip(classes, centers)):
    pts = center + np.random.randn(n_per, 3) * 0.7
    all_pts.append(pts)
    all_labels.extend([cls] * n_per)
all_pts_arr = np.vstack(all_pts)

fig = plt.figure(figsize=(8, 7))
ax = fig.add_subplot(111, projection='3d')

for i, (cls, pts) in enumerate(zip(classes, all_pts)):
    # Scatter points
    ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2], s=12, alpha=0.4,
               color=PALETTE[i], label=cls, edgecolor='none')

    # Semi-transparent convex hull
    try:
        hull = ConvexHull(pts)
        faces = []
        for simplex in hull.simplices:
            face = [pts[s] for s in simplex]
            faces.append(face)
        poly = Poly3DCollection(faces, alpha=0.08, facecolor=PALETTE[i],
                                edgecolor=PALETTE[i], linewidth=0.3)
        ax.add_collection3d(poly)
    except Exception:
        pass

    # 2D projections on walls
    # XY projection (on z wall)
    z_wall = ax.get_zlim()[0] if hasattr(ax, '_zlim') else all_pts_arr[:, 2].min() - 2
    ax.scatter(pts[:, 0], pts[:, 1], np.full(len(pts), all_pts_arr[:, 2].min() - 1.5),
               s=3, alpha=0.1, color=PALETTE[i], edgecolor='none')
    # XZ projection (on y wall)
    ax.scatter(pts[:, 0], np.full(len(pts), all_pts_arr[:, 1].max() + 1.5), pts[:, 2],
               s=3, alpha=0.1, color=PALETTE[i], edgecolor='none')
    # YZ projection (on x wall)
    ax.scatter(np.full(len(pts), all_pts_arr[:, 0].min() - 1.5), pts[:, 1], pts[:, 2],
               s=3, alpha=0.1, color=PALETTE[i], edgecolor='none')

    # Class center label
    cx, cy, cz = pts.mean(axis=0)
    ax.text(cx, cy, cz + 0.5, cls, fontsize=8, fontweight='bold', color=PALETTE[i],
            ha='center', va='bottom')

ax.set_xlabel('Dim 1', fontsize=10, labelpad=6)
ax.set_ylabel('Dim 2', fontsize=10, labelpad=6)
ax.set_zlabel('Dim 3', fontsize=10, labelpad=6)
ax.view_init(elev=20, azim=135)
ax.tick_params(labelsize=8)
ax.legend(fontsize=9, markerscale=3)
fig.tight_layout()
save_fig(fig, 'figures/fig_3d_features.pdf')
