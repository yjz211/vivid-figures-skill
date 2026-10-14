"""三维体绘制
Restored/adapted from supplied screenshots [36].
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
from scipy import ndimage
np.random.seed(0)
l=30
X,Y,Z=np.mgrid[:l,:l,:l]
vol=np.zeros((l,l,l))
pts=(l*np.random.rand(3,15)).astype(int)
vol[tuple(indices for indices in pts)]=1
vol=ndimage.gaussian_filter(vol,4)
vol/=vol.max()
fig=go.Figure(go.Volume(x=X.flatten(),y=Y.flatten(),z=Z.flatten(),value=vol.flatten(),
    isomin=.2,isomax=.7,opacity=.1,surface_count=25,colorscale=[[0.,'#3768b0'],[.5,'#e9d1ab'],[1.,'#c3476a']] ))
fig.update_layout(scene={a:dict(title=a[0].upper(),backgroundcolor='#f2e2e4') for a in ['xaxis','yaxis','zaxis']},margin=dict(l=0,r=0,t=0,b=0))
# Export-safe frame leaves room for outer 3D ticks.
fig.update_layout(margin=dict(l=30,r=30,t=30,b=35))
fig.update_layout(scene_camera=dict(eye=dict(x=1.65,y=1.65,z=1.5)))
fig.show()

