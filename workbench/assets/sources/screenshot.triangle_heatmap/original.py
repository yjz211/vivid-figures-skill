"""双指标三角热图
Restored/adapted from supplied screenshots [23, 24, 25, 26].
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
from matplotlib.patches import Polygon
plt.rcParams.update({'axes.edgecolor':'white','axes.linewidth':.3,'xtick.major.size':0,'ytick.major.size':0,'xtick.color':'#c0627a','ytick.color':'#c0627a','text.color':'#c0627a','font.size':8})
read_custom_data=False
upper_color_list=palette_stops('diverging',count=5,center='#eeeeee',reverse=True)
lower_color_list=palette_stops('diverging',center='#eeeeee')
color_alpha=.75
def create_colormap(colors):
    return LinearSegmentedColormap.from_list('custom',colors,N=256)
def get_text_color(value,vmax,colors):
    n=value/vmax
    return contrast_text(create_colormap(colors)((n+1)/2),alpha=color_alpha)
if read_custom_data:
    upper_df=pd.read_csv('upper_data.csv',index_col=0)
    lower_df=pd.read_csv('lower_data.csv',index_col=0)
    if not upper_df.index.equals(lower_df.index) or not upper_df.columns.equals(lower_df.columns):
        raise ValueError('Upper/lower matrix labels must match')
    upper_data,lower_data=upper_df.values,lower_df.values
    row_labels,col_labels=list(upper_df.index),list(upper_df.columns)
else:
    np.random.seed(2)
    row_labels=[f'类别{chr(65+i)}' for i in range(8)]
    col_labels=[f'指标{i}' for i in range(1,19)]
    upper_data=np.random.randint(-100,101,(8,18))
    lower_data=np.random.randint(-100,101,(8,18))
num_rows,num_cols=upper_data.shape
fig,ax=plt.subplots(figsize=(11,5.5),dpi=150)
ax.set(xlim=(0,num_cols),ylim=(0,num_rows))
norm=Normalize(-100,100)
upper_cmap,lower_cmap=map(create_colormap,[upper_color_list,lower_color_list])
for i in range(num_rows):
    for j in range(num_cols):
        ax.add_patch(Polygon([[j,i],[j+1,i],[j,i+1]],facecolor=upper_cmap(norm(upper_data[i,j])),edgecolor='white',linewidth=.5,alpha=color_alpha))
        ax.text(j+.1,i+.4,f'{upper_data[i,j]:g}',fontsize=7,fontweight='bold',color=get_text_color(upper_data[i,j],100,upper_color_list))
        ax.add_patch(Polygon([[j+1,i],[j+1,i+1],[j,i+1]],facecolor=lower_cmap(norm(lower_data[i,j])),edgecolor='white',linewidth=.5,alpha=color_alpha))
        ax.text(j+.5,i+.8,f'{lower_data[i,j]:g}',fontsize=7,fontweight='bold',color=get_text_color(lower_data[i,j],100,lower_color_list))
ax.set_xticks(np.arange(num_cols)+.5,col_labels,rotation=90,fontweight='bold')
ax.set_yticks(np.arange(num_rows)+.5,row_labels,fontweight='bold')
ax.invert_yaxis();ax.set_aspect('equal')
fig.subplots_adjust(left=.08,right=.98,bottom=.18,top=.79)
for bounds,cmap,label in [([.1,.88,.38,.03],upper_cmap,'上三角指标'),([.57,.88,.38,.03],lower_cmap,'下三角指标')]:
    cb=fig.colorbar(ScalarMappable(norm=norm,cmap=cmap),cax=fig.add_axes(bounds),orientation='horizontal',alpha=color_alpha)
    cb.ax.set_title(label,fontsize=10)
plt.show()

