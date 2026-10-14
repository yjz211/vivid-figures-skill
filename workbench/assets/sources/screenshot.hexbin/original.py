"""六边形空间热图
Restored/adapted from supplied screenshots [104, 105].
Source: 小明的代码美学 (as shown in supplied screenshots).
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
def create_gaussian_points(center,amplitude,sigma_x,sigma_y,num_points):
    x=np.random.normal(center[0],sigma_x,num_points)
    y=np.random.normal(center[1],sigma_y,num_points)
    z=amplitude*np.exp(-((x-center[0])**2/(2*sigma_x**2)+(y-center[1])**2/(2*sigma_y**2)))
    return x,y,z
np.random.seed(2);num_points=5000
x1,y1,z1=create_gaussian_points((10,7),-50,28,25,num_points)
x2,y2,z2=create_gaussian_points((25,12),50,27,26,num_points)
x=np.concatenate([x1,x2]);y=np.concatenate([y1,y2])
z=np.concatenate([z1,z2])+np.random.uniform(-25,25,2*num_points)
cmap=LinearSegmentedColormap.from_list('custom',palette_stops('diverging',count=5),N=256)
fig,ax=plt.subplots(figsize=(10,6),dpi=150)
hb=ax.hexbin(x,y,C=z,gridsize=50,cmap=cmap,reduce_C_function=np.mean,edgecolors='white',linewidths=.5)
cb=fig.colorbar(hb,ax=ax,orientation='vertical',pad=.01,fraction=.05)
cb.set_label('格内测量值均值')
ax.set(title='六边形空间热图',xlim=(-60,90),ylim=(-40,50),xlabel='X 轴',ylabel='Y 轴')
plt.tight_layout();plt.show()

