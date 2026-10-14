"""嵌套环形图
Restored/adapted from supplied screenshots [60, 61, 62].
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
colors=['#dc9eb5','#b8b2b9','#b0a3c0','#e3d0d7','#ebe8f0']
main_name=['类别A','类别B','类别C']
sub_name=['子类A-1','子类A-2','子类B-1','子类C-1','子类C-2','子类C-3']
value_list=[[100.,120.],[37.],[29.,10.,20.]]
fig,ax=plt.subplots(subplot_kw={'projection':'polar'},figsize=(8,5),dpi=150)
size=.2
ax.set_ylim(0,.8);ax.set_axis_off()
sum_vals=sum(map(sum,value_list))
main_divided=[sum(v)/sum_vals*2*np.pi for v in value_list]
main_x=np.cumsum([0]+main_divided[:-1])
main_colors=colors[:len(value_list)]
main_bars=ax.bar(main_x,width=main_divided,bottom=size,height=size,color=main_colors,edgecolor='white',linewidth=1,align='edge')
sub_values=[v for group in value_list for v in group]
sub_divided=[v/sum_vals*2*np.pi for v in sub_values]
sub_x=np.cumsum([0]+sub_divided[:-1])
sub_colors=[main_colors[i] for i,group in enumerate(value_list) for _ in group]
sub_bars=ax.bar(sub_x,width=sub_divided,bottom=2*size,height=size*.5,color=sub_colors,alpha=.5,edgecolor='white',linewidth=2,align='edge')
for bars,names,values,offset,face in [(main_bars,main_name,list(map(sum,value_list)),-.1,'#75879655'),(sub_bars,sub_name,sub_values,.1,'#75879677')]:
    for bar,label,val in zip(bars,names,values):
        angle=bar.get_x()+bar.get_width()/2
        distance=bar.get_height()+bar.get_y()+offset
        ax.text(angle,distance,f'{label}\n{val/sum_vals*100:.1f}% | {val:.0f}',color='white',fontsize=8,ha='center',va='center',fontweight='bold',bbox=dict(facecolor=face,edgecolor='none',boxstyle='round,pad=.5'))
fig.text(.16,.5,'嵌套环形图',fontsize=23,ha='center',va='center',fontweight='bold',color='#515a85')
fig.subplots_adjust(left=.28,right=1,top=1,bottom=.02)
plt.show()

