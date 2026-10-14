"""三维螺旋气泡
Restored/adapted from supplied screenshots [33, 34].
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
np.random.seed(42)
n_bubbles=100
t=np.linspace(0,4*np.pi,n_bubbles)
x=np.cos(t)+np.random.normal(scale=.2,size=n_bubbles)
y=np.sin(t)+np.random.normal(scale=.2,size=n_bubbles)
z=t+np.random.normal(scale=.2,size=n_bubbles)
z_normalized=z-z.min()
bubble_sizes=2*z_normalized+10
fig=go.Figure(go.Scatter3d(x=x,y=y,z=z,mode='markers',marker=dict(size=bubble_sizes,color=z,
    colorscale=[[0.,'#2f648e'],[.5,'#e9d1ab'],[1.,'#c3476a']],opacity=.7,colorbar=dict(title='Z 值'))))
fig.update_layout(scene=dict(xaxis_title='X',yaxis_title='Y',zaxis_title='Z'))
# Export-safe frame leaves room for outer 3D ticks.
fig.update_layout(margin=dict(l=30,r=30,t=30,b=35))
fig.update_layout(scene_camera=dict(eye=dict(x=1.65,y=1.65,z=1.5)))
fig.show()

