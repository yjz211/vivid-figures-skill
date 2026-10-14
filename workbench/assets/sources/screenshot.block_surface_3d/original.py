"""三维方柱曲面
Restored/adapted from supplied screenshots [43, 44, 45].
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
def hex_to_rgb(hex_color):
    h=hex_color.lstrip('#')
    return tuple(int(h[i:i+2],16) for i in (0,2,4))
def rgb_to_hex(rgb):
    return '#%02x%02x%02x'%tuple(rgb)
def interpolate_color(value,color_list):
    if value<=0:return color_list[0]
    if value>=1:return color_list[-1]
    n=len(color_list)-1
    segment=min(int(value*n),n-1)
    local_t=(value-segment/n)*n
    rgb1,rgb2=map(hex_to_rgb,color_list[segment:segment+2])
    return rgb_to_hex(tuple(int((1-local_t)*a+local_t*b) for a,b in zip(rgb1,rgb2)))
def towers(fig,a,e,pos_x,pos_y,color_list,global_min,global_max):
    x_vals=np.linspace(pos_x-a/2,pos_x+a/2,2)
    y_vals=np.linspace(pos_y-a/2,pos_y+a/2,2)
    x,y,z=np.meshgrid(x_vals,y_vals,[0,e])
    color=interpolate_color((e-global_min)/(global_max-global_min) if global_max!=global_min else 0,color_list)
    fig.add_trace(go.Mesh3d(x=x.flatten(),y=y.flatten(),z=z.flatten(),alphahull=1,flatshading=True,color=color))
    vertices=np.array([[pos_x-a/2,pos_y-a/2,0],[pos_x+a/2,pos_y-a/2,0],
      [pos_x+a/2,pos_y+a/2,0],[pos_x-a/2,pos_y+a/2,0],
      [pos_x-a/2,pos_y-a/2,e],[pos_x+a/2,pos_y-a/2,e],
      [pos_x+a/2,pos_y+a/2,e],[pos_x-a/2,pos_y+a/2,e]])
    edges=[[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]]
    edge_x,edge_y,edge_z=[],[],[]
    for a,b in edges:
        edge_x.extend([vertices[a,0],vertices[b,0],None])
        edge_y.extend([vertices[a,1],vertices[b,1],None])
        edge_z.extend([vertices[a,2],vertices[b,2],None])
    fig.add_trace(go.Scatter3d(x=edge_x,y=edge_y,z=edge_z,mode='lines',line=dict(color='white',width=3)))
rows,cols=16,11
x,y=np.linspace(-1,1,cols),np.linspace(-1.7,1.3,rows)
X,Y=np.meshgrid(x,y)
Z=np.exp(-((X+.5)**2+(Y+.5)**2)/.7)*1.5+np.exp(-((X-.5)**2+(Y-.5)**2)/.3)
color_list=['#214e81','#8d9eb2','#cccccc','#dc9fb0','#c2768b']
fig=go.Figure()
for xv,yv,zv in zip(X.flatten(),Y.flatten(),Z.flatten()):
    towers(fig,.15,zv,xv,yv,color_list,Z.min(),Z.max())
fig.update_layout(showlegend=False,margin=dict(l=0,r=0,t=0,b=0),scene=dict(
    xaxis=dict(title='X',backgroundcolor='#f8f1f1'),yaxis=dict(title='Y',backgroundcolor='#f8f1f1'),
    zaxis=dict(title='Z',backgroundcolor='#f8f1f1'),aspectmode='data'))
# Export-safe frame leaves room for outer 3D ticks.
fig.update_layout(margin=dict(l=30,r=30,t=30,b=35))
fig.update_layout(scene_camera=dict(eye=dict(x=1.65,y=1.65,z=1.5)))
fig.show()

