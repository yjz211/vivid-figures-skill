"""三维分层热图
Restored/adapted from supplied screenshots [10].
Source: @Doc mm (as shown in supplied screenshots).
This is a runnable restoration, not a byte-for-byte original source file.
See SOURCE.md for missing inputs and documented corrections.
"""
import numpy as np; from _utils.palette_maps import palette_cmap, palette_stops, contrast_text
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize, to_hex
from matplotlib.cm import ScalarMappable
from pathlib import Path
# Missing .mplstyle files are replaced only by explicit, portable display defaults.
plt.rcParams.update({'font.sans-serif':['Microsoft YaHei','DejaVu Sans'],
 'axes.unicode_minus':False,'figure.facecolor':'white','axes.facecolor':'white',
 'axes.spines.top':False,'axes.spines.right':False,'font.size':9})
# Image-only page 010 (@Doc mm); reconstructed layered heatmap with synthetic inputs.
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
rng=np.random.default_rng(10)
n_layers,n_rows,n_cols=4,5,10
base=np.sin(np.linspace(-np.pi,np.pi,n_cols))[None,:]*.55
matrices=np.clip(base+rng.normal(0,.25,(n_layers,n_rows,n_cols)),-1,1)
cmap=LinearSegmentedColormap.from_list('rc2',palette_stops('diverging',center='#f5f3ed'))
norm=Normalize(-1,1)
fig=plt.figure(figsize=(10,7),dpi=150);ax=fig.add_subplot(projection='3d')
for layer in range(n_layers):
    verts=[];facecolors=[]
    for row in range(n_rows):
        for col in range(n_cols):
            verts.append([(col,row,layer+1),(col+1,row,layer+1),(col+1,row+1,layer+1),(col,row+1,layer+1)])
            facecolors.append(cmap(norm(matrices[layer,row,col])))
    slab=Poly3DCollection(verts,facecolors=facecolors,edgecolors='#dddddd',linewidths=.4,alpha=.86)
    ax.add_collection3d(slab)
ax.set(xlim=(0,n_cols),ylim=(0,n_rows),zlim=(1,n_layers),xlabel='Gene',ylabel='Gradient tier')
ax.set_xticks(np.arange(n_cols)+.5,np.arange(1,n_cols+1));ax.set_yticks(np.arange(n_rows)+.5,np.arange(n_rows));ax.set_zticks(range(1,n_layers+1))
ax.view_init(elev=23,azim=-120);ax.set_box_aspect((1.5,1,1))
for axis in [ax.xaxis,ax.yaxis,ax.zaxis]:axis.pane.fill=False
cb=fig.colorbar(ScalarMappable(norm=norm,cmap=cmap),ax=ax,fraction=.035,pad=.06,shrink=.7)
cb.ax.set_title('RC2')
plt.tight_layout();plt.show()

