"""三维网格散点场
Restored/adapted from supplied screenshots [38].
Source: 小明的代码美学 (as shown in supplied screenshots).
This is a runnable restoration, not a byte-for-byte original source file.
See SOURCE.md for missing inputs and documented corrections.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize, to_hex
from matplotlib.cm import ScalarMappable
from pathlib import Path
# Missing .mplstyle files are replaced only by explicit, portable display defaults.
plt.rcParams.update({'font.sans-serif':['Microsoft YaHei','DejaVu Sans'],
 'axes.unicode_minus':False,'figure.facecolor':'white','axes.facecolor':'white',
 'axes.spines.top':False,'axes.spines.right':False,'font.size':9})
import plotly.graph_objects as go
rows, cols = 32, 22
x = np.linspace(-1, 1, cols)
y = np.linspace(-1.7, 1.3, rows)
X, Y = np.meshgrid(x, y)
Z = np.exp(-((X+.5)**2+(Y+.5)**2)/.7)*1.5 + np.exp(-((X-.5)**2+(Y-.5)**2)/.3)
colorscale_custom = [[0., '#2f648e'], [.5, '#e9d1ab'], [1., '#c3476a']]

fig=go.Figure(go.Scatter3d(x=X.flatten(),y=Y.flatten(),z=Z.flatten(),mode='markers',marker=dict(size=4,color=Z.flatten(),colorscale=colorscale_custom,colorbar=dict(title='Color Scale'))))
fig.update_layout(scene=dict(xaxis_title='X',yaxis_title='Y',zaxis_title='Z'),margin=dict(l=0,r=0,t=0,b=0))
# Export-safe frame leaves room for outer 3D ticks.
fig.update_layout(margin=dict(l=30,r=30,t=30,b=35))
fig.update_layout(scene_camera=dict(eye=dict(x=1.65,y=1.65,z=1.5)))
fig.show()

