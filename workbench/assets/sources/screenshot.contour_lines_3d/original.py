"""三维等高线
Restored/adapted from supplied screenshots [40, 41].
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

cmap=LinearSegmentedColormap.from_list('custom',[col for pos,col in colorscale_custom],N=256)
levels=np.linspace(Z.min(),Z.max(),20)
fig_contour=plt.figure()
cs=plt.contour(X,Y,Z,levels=levels)
plt.close(fig_contour)
fig=go.Figure()
for i,level in enumerate(cs.levels):
    for seg in cs.allsegs[i]:
        if len(seg)==0: continue
        color=to_hex(cmap((level-Z.min())/(Z.max()-Z.min())))
        fig.add_trace(go.Scatter3d(x=seg[:,0],y=seg[:,1],z=[level]*len(seg),mode='lines',line=dict(color=color,width=8),showlegend=False))
fig.update_layout(scene=dict(xaxis_title='X',yaxis_title='Y',zaxis_title='Z'),margin=dict(l=0,r=0,t=0,b=0))
# Export-safe frame leaves room for outer 3D ticks.
fig.update_layout(margin=dict(l=30,r=30,t=30,b=35))
fig.update_layout(scene_camera=dict(eye=dict(x=1.65,y=1.65,z=1.5)))
fig.show()

