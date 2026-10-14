"""南丁格尔玫瑰图
Restored/adapted from supplied screenshots [57, 58].
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
values=np.array([30,35,40,45,50,55,60,65,70])
labels=[f'类别{i+1}' for i in range(len(values))]
width=2*np.pi*values/sum(values)
colors=['#dc9eb5','#e3d0d7','#b0a3c0']*3
fig,ax=plt.subplots(subplot_kw={'projection':'polar'},figsize=(8,5),dpi=150)
start_x=0
for i,value in enumerate(values):
    start_x+=.5*width[i]
    ax.bar(start_x,value,width=width[i],bottom=10.,linewidth=2,edgecolor='white',color=colors[i])
    # Correct the screenshot's percentage formula (width / 2pi, not width / pi).
    label=f'{labels[i]}\n{value/values.sum()*100:.1f}% | {value}'
    offset=[12,-4,0,0,0,0,0,0,0][i]
    ax.text(start_x,value*.75+10+offset,label,color='white',fontsize=7,ha='center',va='center',fontweight='bold',
            bbox=dict(facecolor='#75879655',edgecolor='none',boxstyle='round,pad=.5'))
    start_x+=.5*width[i]
ax.set(xticks=[],yticks=[],ylim=(0,85))
ax.spines['polar'].set_visible(False)
ax.set_theta_direction(1);ax.set_theta_offset(np.pi*.5)
fig.text(.18,.5,'南丁格尔\n玫瑰图',fontsize=24,ha='center',va='center',fontweight='bold',color='#515a85')
fig.subplots_adjust(left=.32,right=.98,top=.98,bottom=.02)
plt.show()

