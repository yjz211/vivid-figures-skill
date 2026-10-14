from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten; from _utils.vivid_config import palette_colors
setup_style(); scale_colors = palette_colors()
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

try:
    import networkx as nx
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'networkx', '-q'])
    import networkx as nx

from scipy.spatial import ConvexHull

G = nx.karate_club_graph()
communities = list(nx.community.greedy_modularity_communities(G))

# Assign community colors
color_map = {}
for i, comm in enumerate(communities):
    for node in comm:
        color_map[node] = i
node_colors = [PALETTE[color_map[n] % len(PALETTE)] for n in G.nodes()]

# Node sizing by degree
degrees = dict(G.degree())
max_deg = max(degrees.values())
node_sizes = [400 * degrees[n] / max_deg + 80 for n in G.nodes()]

fig, ax = plt.subplots(figsize=(8, 7))
pos = nx.spring_layout(G, seed=42, k=0.5)

# Draw convex hulls for communities
for i, comm in enumerate(communities):
    if len(comm) >= 3:
        points = np.array([pos[n] for n in comm])
        try:
            hull = ConvexHull(points)
            hull_points = points[hull.vertices]
            # Close the polygon
            hull_points = np.vstack([hull_points, hull_points[0]])
            # Expand hull slightly
            centroid = points.mean(axis=0)
            expanded = centroid + 1.15 * (hull_points - centroid)
            ax.fill(expanded[:, 0], expanded[:, 1],
                    color=PALETTE[i % len(PALETTE)], alpha=0.08)
            ax.plot(expanded[:, 0], expanded[:, 1],
                    color=PALETTE[i % len(PALETTE)], linewidth=1.5,
                    linestyle='--', alpha=0.4)
        except Exception:
            pass

# Edge weight gradient
edges = G.edges()
edge_weights = [G[u][v].get('weight', 1) for u, v in edges]
max_w = max(edge_weights) if edge_weights else 1
cmap_edge = mcolors.LinearSegmentedColormap.from_list('ew', [_lighten(scale_colors[0], 0.8), COLORS['ref_line']])
for (u, v), w in zip(edges, edge_weights):
    x0, y0 = pos[u]
    x1, y1 = pos[v]
    norm_w = w / max_w
    ax.plot([x0, x1], [y0, y1], color=cmap_edge(norm_w),
            linewidth=0.5 + 1.5 * norm_w, alpha=0.3 + 0.4 * norm_w, zorder=1)

# Draw nodes
nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, node_size=node_sizes,
                        edgecolors='white', linewidths=1.2, alpha=0.9, zorder=3)

# Labels for high-degree nodes only
high_deg_nodes = {n: str(n) for n in G.nodes() if degrees[n] >= 4}
nx.draw_networkx_labels(G, pos, labels=high_deg_nodes, ax=ax,
                         font_size=7, font_color=COLORS['text'], font_weight='bold')

# Legend for communities
from matplotlib.lines import Line2D
legend_elements = [Line2D([0], [0], marker='o', color='w',
                           markerfacecolor=PALETTE[i % len(PALETTE)],
                           markersize=10, label=f'Community {i+1}')
                   for i in range(len(communities))]
ax.legend(handles=legend_elements, loc='upper left', frameon=False, labelspacing=0.35, handlelength=1.6, fontsize=8, fancybox=True)

ax.set_axis_off()
fig.tight_layout()
save_fig(fig, 'figures/fig_network.pdf')
