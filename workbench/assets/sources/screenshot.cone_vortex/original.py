"""三维涡旋向量图
Restored/adapted from supplied screenshots [28].
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
# vortex.csv is absent from the archive. This analytic demo is explicitly synthetic.
read_custom_data=False
if read_custom_data:
    df=pd.read_csv('vortex.csv')
else:
    a=np.linspace(-4,4,9);b=np.linspace(-4,4,9);c=np.linspace(0,5,5)
    X,Y,Z=np.meshgrid(a,b,c,indexing='ij')
    df=pd.DataFrame(dict(x=X.ravel(),y=Y.ravel(),z=Z.ravel(),u=(-Y).ravel(),v=X.ravel(),w=np.full(X.size,1.5)))
fig=go.Figure(go.Cone(x=df.x,y=df.y,z=df.z,u=df.u,v=df.v,w=df.w,
    colorscale=['#ffffff','#e9d1ab','#c3476a'],sizemode='absolute',sizeref=1.3))
# The screenshot uses sizeref=60 for its unavailable dataset; 1.3 fits demo vector units.
fig.update_layout(margin=dict(l=0,r=0,t=0,b=0),scene=dict(
    xaxis=dict(title='X',backgroundcolor='#f7eff0'),yaxis=dict(title='Y',backgroundcolor='#f7eff0'),
    zaxis=dict(title='Z',backgroundcolor='#f7eff0'),aspectratio=dict(x=.7,y=1,z=.5)))
# Export-safe frame leaves room for outer 3D ticks.
fig.update_layout(margin=dict(l=30,r=30,t=30,b=35))
fig.update_layout(scene_camera=dict(eye=dict(x=1.65,y=1.65,z=1.5)))
fig.show()

