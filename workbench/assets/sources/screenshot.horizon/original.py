"""正负折叠地平线图
Restored/adapted from supplied screenshots [68, 69, 70].
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
from scipy.interpolate import make_interp_spline
from matplotlib.patches import Patch
def create_data(x,size,n,max_value):
    sigma=size/30
    return max_value*np.exp(-.5*((x-n)/sigma)**2)
np.random.seed(3)
x=np.linspace(0,80,300)
y_list=[]
for i in range(20):
    peaks=np.sort(np.random.uniform(0,80,size=200))
    means=np.random.uniform(-.25,.3,200)
    temp_y=sum(create_data(x,80,p,m) for p,m in zip(peaks,means))
    y_list.append(temp_y)
fig,ax=plt.subplots(figsize=(10,6),dpi=150)
y_offset=.6
for i,y in enumerate(y_list):
    x_smooth=np.linspace(x.min(),x.max(),500)
    y_smooth=make_interp_spline(x,y)(x_smooth)
    for sign,color in [(1,'#e98184'),(-1,'#81b7d9')]:
        y_pos=np.maximum(sign*y_smooth,0)
        for j in range(4):
            y_plot=np.maximum(np.minimum(y_pos,y_offset*(j+1)),y_offset*j)
            y_bottom=y_offset*i
            y_top=y_plot-j*y_offset+y_offset*i
            ax.fill_between(x_smooth,y_bottom,y_top,color=color,alpha=.5)
            ax.plot(x_smooth,y_top,color='white',linewidth=.5)
ax.set(xlim=(0,70),ylim=(0,13))
ax.set_xticks([1.5,10,20,30,40,50,60,68.5],range(2020,2028),fontweight='bold',color='#81b7d9')
ax.set_yticks([.3+i*.6 for i in range(20)],[chr(i) for i in range(65,85)],fontweight='bold',color='#81b7d9')
ax.legend(handles=[Patch(color='#e98184',label='正向偏差'),Patch(color='#81b7d9',label='负向偏差')],loc='upper right',ncols=2,frameon=False)
ax.set_title('正负折叠地平线图',loc='left',color='#3680ae',fontweight='bold')
plt.tight_layout();plt.show()

