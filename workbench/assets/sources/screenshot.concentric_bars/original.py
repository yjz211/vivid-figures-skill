"""同心环形柱状图
Restored/adapted from supplied screenshots [53, 54, 55].
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
from matplotlib.patches import Patch
values=[11,12,12,14,15,20,22,22,24,24,26,27]
max_value=max(values)*1.1
num_rings=len(values)
categories=[f'类别{i+1}' for i in range(num_rings)]
fig,ax=plt.subplots(figsize=(8,5),subplot_kw={'projection':'polar'},dpi=150)
ax.set_theta_direction(-1);ax.set_theta_offset(np.pi/2)
inner_radius_offset=2
for i,(label,value) in enumerate(zip(categories,values)):
    inner_radius=i+inner_radius_offset
    ring_width=.8
    theta_start=0;theta_end=value/max_value*2*np.pi
    rotation=-np.degrees((theta_start+theta_end)/2) if np.degrees(theta_end)<180 else 180-np.degrees((theta_start+theta_end)/2)
    color='#9dc1c5' if value<15 else '#d7a6b3' if value>25 else '#8e93af'
    ax.bar(x=(theta_start+theta_end)/2,height=ring_width,width=theta_end-theta_start,bottom=inner_radius,color=color)
    ax.text((theta_start+theta_end)/2,inner_radius+ring_width/2,f'{value}',ha='center',va='center',color='white',fontsize=6,fontweight='bold',rotation=rotation,rotation_mode='anchor')
handles=[Patch(color=c,label=l) for c,l in zip(['#9dc1c5','#8e93af','#d7a6b3'],['低值','中值','高值'])]
fig.legend(handles=handles,loc='center right',frameon=False)
ax.set_xticks([]);ax.set_yticks(np.arange(num_rings)+inner_radius_offset,categories,fontsize=6)
ax.set_rlabel_position(0)
ax.grid(axis='y',linestyle='-',linewidth=1,color='white')
ax.spines['polar'].set_visible(False)
fig.suptitle('环形柱状图',x=.02,ha='left')
plt.tight_layout();plt.show()

