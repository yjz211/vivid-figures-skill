"""径向环形热图
Restored/adapted from supplied screenshots [99, 100, 101, 102].
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
np.random.seed(6)
data=np.array([np.random.uniform(5*i,5*(i+1),48) for i in range(12)])
data+=np.random.normal(0,15,data.shape)
colors=palette_stops('diverging',count=5)
cmap=LinearSegmentedColormap.from_list('custom',colors,N=256)
num_columns=data.shape[1];gap_angle=10
width=2*np.pi/num_columns*(360-gap_angle)/360
theta=np.arange(num_columns)*width
vmin,vmax=data.min(),data.max()
fig,ax=plt.subplots(figsize=(8,6),dpi=150,subplot_kw={'polar':True})
for i,row in enumerate(data):
    height=2;radius=height*i+10
    for j,value in enumerate(row):
        ax.bar(theta[j],height,bottom=radius,width=width,color=cmap((value-vmin)/(vmax-vmin)),edgecolor='white',linewidth=.5,align='edge')
    ax.text(theta[-1]+width+np.radians(gap_angle/2),radius+height/2,str(i+1),ha='center',va='center',fontsize=6,rotation=-10)
for angle,label in zip(theta+width/2,range(1,num_columns+1)):
    rotation=np.degrees(angle);flip=90<rotation<270
    ax.text(angle,radius+3,str(label),ha='right' if flip else 'left',va='center',rotation=rotation-180 if flip else rotation,rotation_mode='anchor',fontsize=8)
ax.set(xticks=[],yticks=[],ylim=(0,radius+5));ax.spines['polar'].set_visible(False);ax.grid(False)
cb=fig.colorbar(ScalarMappable(norm=Normalize(vmin,vmax),cmap=cmap),ax=ax,orientation='vertical',pad=.15,fraction=.05)
cb.ax.tick_params(labelsize=8)
ax.text(0,0,'径向热图',ha='center',va='center',fontsize=12,fontweight='bold',color='#c0627a')
plt.tight_layout();plt.show()

