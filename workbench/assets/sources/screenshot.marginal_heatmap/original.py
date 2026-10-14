"""带边际柱形的表格热图
Restored/adapted from supplied screenshots [79, 80, 81, 82, 83].
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
from matplotlib.gridspec import GridSpec
plt.rcParams.update({'axes.edgecolor':'white','xtick.major.size':0,'ytick.major.size':0,'xtick.labelsize':7,'ytick.labelsize':7,'text.color':'#3680ae','xtick.color':'#3680ae','ytick.color':'#3680ae'})
cmap=LinearSegmentedColormap.from_list('custom',palette_stops('diverging',count=5),N=300)
years=np.arange(1985,2021)
months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
np.random.seed(10)
data=np.random.uniform(-1,1,(len(months),len(years)))
for i in range(len(months)):data[i]+=np.linspace(-1,2,len(years))
data+=np.random.uniform(-1.5,1.5,data.shape)
bar_data_year=data.sum(axis=0);bar_data_month=data.sum(axis=1)
fig=plt.figure(figsize=(12,6),dpi=150)
gs=GridSpec(2,2,width_ratios=[10,1.5],height_ratios=[1,2],wspace=.04,hspace=.05)
ax_heatmap=fig.add_subplot(gs[1,0])
ax_heatmap.imshow(data,cmap=cmap,aspect='auto',vmin=-np.max(np.abs(data)),vmax=np.max(np.abs(data)))
for i in range(data.shape[0]):
    for j in range(data.shape[1]):
        v=data[i,j];color=contrast_text(cmap((v/np.max(np.abs(data))+1)/2))
        ax_heatmap.text(j,i,f'{v:.1f}',ha='center',va='center',fontsize=6,color=color,fontweight='bold')
for i in range(data.shape[0]+1):ax_heatmap.plot([-.5,data.shape[1]-.5],[i-.5]*2,color='white',linewidth=1)
for j in range(data.shape[1]+1):ax_heatmap.plot([j-.5]*2,[-.5,data.shape[0]-.5],color='white',linewidth=1)
ax_heatmap.set_xticks(np.arange(len(years)),years,rotation=90,fontweight='bold')
ax_heatmap.set_yticks(np.arange(len(months)),months,fontweight='bold')
ax_top=fig.add_subplot(gs[0,0],sharex=ax_heatmap)
ax_top.bar(np.arange(len(years)),bar_data_year,color=[palette_stops('diverging')[0] if v<0 else palette_stops('diverging')[-1] for v in bar_data_year])
ax_top.tick_params(axis='both',bottom=False,left=False,labelbottom=False,labelleft=False)
ax_top.grid(False)
ax_right=fig.add_subplot(gs[1,1],sharey=ax_heatmap)
ax_right.barh(np.arange(len(months)),bar_data_month,color=[palette_stops('diverging')[0] if v<0 else palette_stops('diverging')[-1] for v in bar_data_month])
ax_right.tick_params(axis='both',bottom=False,left=False,labelbottom=False,labelleft=False)
ax_right.grid(False)
for i,v in enumerate(bar_data_year):
    ax_top.text(i,v+(.2 if v>0 else -.8),f'{v:.1f}',ha='center',va='bottom' if v>0 else 'top',fontsize=6,color=palette_stops('diverging')[-1] if v>0 else palette_stops('diverging')[0],fontweight='bold')
ax_top.margins(y=.25)
for i,v in enumerate(bar_data_month):
    ax_right.text(v-1 if v>0 else v+1,i,f'{v:.1f}',ha='right' if v>0 else 'left',va='center',fontsize=7,color='white',fontweight='bold')
fig.suptitle('表格热图与边际汇总',x=.06,y=.98,ha='left',fontsize=22,color='#3680ae')
fig.subplots_adjust(left=.06,bottom=.14,right=.97,top=.88)
plt.show()

