"""双向峰形河流图
Restored/adapted from supplied screenshots [8, 88, 89, 90].
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
from matplotlib.colors import ListedColormap, BoundaryNorm
def generate_single_weighted_random(scale=1.5,lower=1,upper=10):
    return np.clip(np.random.exponential(scale)+lower,lower,upper)
def create_smooth_peak_data(x,start,peak,end,max_value):
    y=np.zeros_like(x)
    rising=(x>=start)&(x<=peak);sigma_rise=(peak-start)/3
    y[rising]=max_value*np.exp(-((x[rising]-peak)**2)/(2*sigma_rise**2))
    falling=(x>peak)&(x<=end);sigma_fall=(end-peak)/3
    y[falling]=max_value*np.exp(-((x[falling]-peak)**2)/(2*sigma_fall**2))
    return y
hex_colors=['#214e81','#456991','#6983a2','#8d9eb2','#dc9fb0','#cf8b9e','#c2768b','#a55d75']
thresholds=[5,7.5,8,12,15,20,25]
def assign_color(value):return hex_colors[sum(value>t for t in thresholds)]
np.random.seed(30)
x=np.linspace(0,800,800)
y_list,color_list,categories=[],[],[]
def generate_data(num_categories,start_base,peak_base,end_base,interval,direction):
    for i in range(num_categories):
        offset=i*interval if direction=='forward' else -i*interval
        max_value=generate_single_weighted_random(6,1,10000)
        y_list.append(create_smooth_peak_data(x,start_base+offset,peak_base+offset,end_base+offset,max_value))
        color_list.append(assign_color(max_value));categories.append(f'类别{len(categories)+1}')
generate_data(72,720,740,820,10,'backward');generate_data(72,0,20,100,10,'forward')
y_list=np.array(y_list)
fig,ax=plt.subplots(figsize=(10,5),dpi=150)
polys=ax.stackplot(x,y_list,colors=color_list,labels=categories,zorder=10,alpha=1,baseline='wiggle')
for poly in polys:
    verts=poly.get_paths()[0].vertices
    ax.plot(verts[:,0],verts[:,1],color='white',zorder=20,linewidth=.5)
# Colors are discrete peak-amplitude bins in the original; show matching bin boundaries.
cmap=ListedColormap(hex_colors);norm=BoundaryNorm([0,*thresholds,40],cmap.N)
cb=fig.colorbar(ScalarMappable(norm=norm,cmap=cmap),ax=ax,orientation='vertical',pad=.01,fraction=.05,extend='max')
cb.set_label('序列峰值分档');cb.ax.tick_params(size=0)
ax.grid(axis='x',which='major',linestyle='-',linewidth=1,color='white')
ax.xaxis.set_major_locator(ticker.MultipleLocator(100))
ax.set_xticks(range(0,801,100),range(2020,2029));ax.set(ylim=(-75,75),yticks=[])
ax.set_title('双向峰形河流图',loc='left')
plt.tight_layout();plt.show()

