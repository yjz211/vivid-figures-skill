"""扇形小提琴与热图
Restored/adapted from supplied screenshots [6].
Source: 滚筒洗衣机 (as shown in supplied screenshots).
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
# Image-only reference (page 006, 滚筒洗衣机). Entire implementation reconstructed.
from scipy.stats import gaussian_kde
rng=np.random.default_rng(6)
months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
years=np.arange(2000,2028,4)
means=.44+.16*np.sin(np.linspace(-np.pi/2,3*np.pi/2,12))
samples=[np.clip(rng.normal(m,.035,100),.2,.7) for m in means]
heat=np.vstack([np.clip(means+rng.normal(0,.025,12)+(i-3)*.008,.2,.7) for i in range(7)])
cmap=LinearSegmentedColormap.from_list('fan',palette_stops('diverging',center='#f4e5e9',reverse=True))
norm=Normalize(.2,.7)
fig,ax=plt.subplots(figsize=(10,5.5),subplot_kw={'projection':'polar'},dpi=150)
ax.set_theta_zero_location('E');ax.set_theta_direction(1)
ax.set_thetamin(0);ax.set_thetamax(180)
theta_edges=np.linspace(0,np.pi,13)
r_edges=np.linspace(.22,.7,8)
ax.pcolormesh(theta_edges,r_edges,heat[:,::-1],cmap=cmap,norm=norm,edgecolors='#ffffff88',linewidth=.5,shading='flat',alpha=.85)
centers=np.pi-(theta_edges[:-1]+theta_edges[1:])/2
for j,(theta,values) in enumerate(zip(centers,samples)):
    grid=np.linspace(values.min(),values.max(),120)
    density=gaussian_kde(values)(grid)
    halfwidth=density/density.max()*(np.pi/12)*.18
    radial=.83+(grid-.2)/.5*.35
    ax.fill(np.r_[theta-halfwidth,(theta+halfwidth)[::-1]],np.r_[radial,radial[::-1]],color=cmap(norm(np.median(values))),alpha=.85,edgecolor='#ffffff',linewidth=.6)
    for q in np.quantile(values,[.25,.5,.75]):
        w=float(np.interp(q,grid,halfwidth))*.8
        ax.plot([theta-w,theta+w],[.83+(q-.2)/.5*.35]*2,color='white',linestyle='--',linewidth=1.1)
    ax.plot([theta,theta],[.2,1.24],color='#dddddd',linestyle=':',linewidth=.5,zorder=0)
ax.set_xticks(centers,months,fontsize=10,color='#777777')
ax.set_yticks([])
for i in range(0,len(years),2):
    ax.text(np.pi+.05,(r_edges[i]+r_edges[i+1])/2,str(years[i]),fontsize=8,color='#777777',rotation=55,ha='right',va='top',clip_on=False)
ax.set_ylim(0,1.27);ax.grid(False);ax.spines['polar'].set_color('#bbbbbb')
ax.set_title('扇形热图与分布小提琴',pad=24,color='#515a85')
cb=fig.colorbar(ScalarMappable(norm=norm,cmap=cmap),ax=ax,orientation='vertical',fraction=.035,pad=.07,shrink=.65)
cb.set_label('测量值（合成数据）')
plt.tight_layout();plt.show()

