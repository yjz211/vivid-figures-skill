"""相关矩阵与连线网络
Restored/adapted from supplied screenshots [92, 93, 94, 95, 96, 97].
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
from matplotlib import patches,lines
# Original uses arbitrary random matrix and network statistics. Demo below uses a real
# sample correlation matrix; the r/p network table remains explicitly illustrative.
feature_labels='N P K Ca Mg S Al Fe Mn Zn Mo pH'.split()
feature_count=len(feature_labels);spec_labels=['spec1','spec2','spec3']
np.random.seed(10)
latent=np.random.normal(size=(100,3))
observations=latent@np.random.normal(size=(3,feature_count))+np.random.normal(size=(100,feature_count))*.8
pearson_data=np.corrcoef(observations,rowvar=False)
p_data=np.random.beta(.8,5,(len(spec_labels),feature_count))
r_data=np.random.uniform(-1,1,(len(spec_labels),feature_count))
def calc_p_color(value):return palette_stops('diverging')[-1] if value<.01 else palette_stops('diverging')[0] if value<.05 else '#c7c7c7'
def calc_r_width(value):return 1. if abs(value)<.2 else 2. if abs(value)<.4 else 4.
def gradient_color(min_value,max_value,hex_colors,value):
    if max_value==min_value:return hex_colors[len(hex_colors)//2]
    n=np.clip((value-min_value)/(max_value-min_value),0,1)
    cmap=LinearSegmentedColormap.from_list('corr',hex_colors)
    return to_hex(cmap(float(n)))
fig,ax=plt.subplots(figsize=(10,7),dpi=150)
spec_pos_y=np.linspace(0,feature_count,len(spec_labels)+2).tolist()
for i,spec in enumerate(spec_labels):
    ax.text(spec_pos_y[i+1]-4.5,spec_pos_y[-2-i]-3.5,spec,ha='center',va='center')
    for j in range(feature_count):
        ax.plot([spec_pos_y[i+1]-4,-.5+j],[spec_pos_y[-2-i]-3,feature_count-j-.5],linestyle='-',linewidth=calc_r_width(r_data[i,j]),color=calc_p_color(p_data[i,j]),zorder=1-p_data[i,j],marker='o',markersize=4)
pearson_colors=palette_stops('diverging',center='#ecf4f8')
for i in range(feature_count):
    for j in range(i,feature_count):
        value=pearson_data[i,j];size=abs(value)
        color=gradient_color(-1,1,pearson_colors,value)
        ax.add_patch(patches.Rectangle((feature_count-i-1,j),1,1,linewidth=.25,edgecolor='#999999',facecolor='white'))
        ax.add_patch(patches.Rectangle((feature_count-i-.5-size/2,j+.5-size/2),size,size,linewidth=.5,edgecolor='#999999',facecolor=color))
# Matrix coordinates are reversed in x; labels follow matrix indices.
for i,label in enumerate(feature_labels):
    ax.text(feature_count-i-.5,feature_count+.5,label,ha='center',va='center',fontsize=8)
    ax.text(feature_count+.5,i+.5,label,ha='center',va='center',fontsize=8)
p_handles=[patches.Patch(color=c,label=l) for c,l in zip([palette_stops('diverging')[-1],palette_stops('diverging')[0],'#c7c7c7'],['< 0.01','0.01–0.05','≥ 0.05'])]
leg=ax.legend(handles=p_handles,title='示例关联 p',bbox_to_anchor=(1,.99),frameon=False);ax.add_artist(leg)
r_handles=[lines.Line2D([],[],color='#a9a9a9',linewidth=w,label=l) for w,l in zip([1,2,4],['< 0.2','0.2–0.4','≥ 0.4'])]
leg=ax.legend(handles=r_handles,title='示例 |r|',bbox_to_anchor=(1,.67),frameon=False);ax.add_artist(leg)
cmap=LinearSegmentedColormap.from_list('pearson',pearson_colors)
cb=fig.colorbar(ScalarMappable(norm=Normalize(-1,1),cmap=cmap),cax=fig.add_axes([.81,.13,.025,.19]))
cb.ax.set_title("Pearson's r",fontsize=9)
ax.set(xticks=[],yticks=[],xlim=(-2,feature_count+8),ylim=(-1,feature_count+1));ax.set_aspect('equal')
for s in ax.spines.values():s.set_visible(False)
ax.set_title('相关矩阵与关联网络（合成示例）',pad=20)
fig.subplots_adjust(left=.04,right=.96,top=.9,bottom=.06)
plt.show()

