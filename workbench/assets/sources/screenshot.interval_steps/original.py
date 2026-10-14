"""阶梯折线与区间带
Restored/adapted from supplied screenshots [85, 86].
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
import matplotlib.ticker as ticker
x=np.arange(1860,2020)
np.random.seed(3)
y1=np.random.uniform(20,30,len(x))+10*np.sin(np.linspace(0,3*np.pi,len(x)))
y2=np.random.uniform(50,55,len(x))+5*np.sin(np.linspace(0,3*np.pi,len(x)))
y3=np.random.uniform(80,85,len(x))+7*np.sin(np.linspace(0,3*np.pi,len(x)))
# Widths are synthetic illustration intervals, not estimated confidence intervals.
ci1=np.random.uniform(4,5,len(x));ci2=np.random.uniform(4,7,len(x));ci3=np.random.uniform(5,9,len(x))
line_colors=['#8e93af','#d7a6b3','#eac890'];edge_colors=['#3f51af','#d7607e','#eab159']
fig,ax=plt.subplots(figsize=(10,5),dpi=150)
ax.set_facecolor('#f4f6f8')
for i,(y,ci,fill_color,line_color) in enumerate(zip([y1,y2,y3],[ci1,ci2,ci3],line_colors,edge_colors)):
    ax.step(x,y,label=f'类别{chr(65+i)}',linewidth=1,where='mid',color=line_color,zorder=3)
    ax.fill_between(x,y-ci,y+ci,label=f'示意区间{chr(65+i)}',alpha=.4,step='mid',color=fill_color,zorder=3 if i<2 else 2)
ax.text(1940,5,'低值期',ha='center',color='#3f51af',fontweight='bold')
ax.text(2000,80,'高值期',ha='center',color='#eab159',fontweight='bold')
ax.set(xlim=(1860,2020),ylim=(0,120))
ax.legend(loc='upper right',ncols=3,frameon=False)
ax.grid(axis='y',which='major',linestyle='-',linewidth=1,color='white',zorder=1)
ax.xaxis.set_major_locator(ticker.MultipleLocator(10))
ax.set_title('阶梯趋势及区间带（合成数据）',loc='left')
plt.tight_layout();plt.show()

