"""平滑极坐标面积叠加
Restored/adapted from supplied screenshots [118, 119, 120].
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
from scipy.interpolate import make_interp_spline
BASE_RADIUS=50;SMOOTHING_POINTS=300
COLORS=['#529a9f','#d36a87','#ee8d5e']
read_custom_data=False
if read_custom_data:
    df=pd.read_csv('data.csv')
else:
    # Synthetic cyclic series: the original data.csv is not supplied.
    angles=np.arange(0,360,30);theta=np.deg2rad(angles)
    df=pd.DataFrame({'angle':angles})
    for i in range(3):
        df[f'value_{i+1}']=14+8*np.sin(theta*2+i*.9)+4*np.cos(theta*3-i*.7)
series_cols=[col for col in df.columns if 'value' in col]
original_angles=df['angle'].values
if len(original_angles)<4 or np.any(np.diff(original_angles)<=0) or original_angles[0]!=0 or original_angles[-1]>=360:
    raise ValueError('Angles must start at zero, strictly increase, and exclude 360 degrees')
original_theta=np.deg2rad(original_angles)
fig,ax=plt.subplots(figsize=(8,6),dpi=150,subplot_kw={'projection':'polar'})
ax.grid(color='gray',linestyle=':',linewidth=.8,alpha=.5)
ax.spines['polar'].set_visible(False)
LIMIT_RADIUS=BASE_RADIUS+df[series_cols].max().max()*2
for idx,col in enumerate(series_cols):
    values=df[col].values
    theta_closed=np.concatenate([original_theta,[original_theta[0]+2*np.pi]])
    values_closed=np.concatenate([values,[values[0]]])
    # Periodic boundary also matches slope at 0/360 (original only duplicated endpoint).
    spl=make_interp_spline(theta_closed,values_closed,k=3,bc_type='periodic')
    theta_smooth=np.linspace(0,2*np.pi,SMOOTHING_POINTS)
    values_smooth=np.maximum(spl(theta_smooth),0)
    r_values=values_smooth+BASE_RADIUS;color=COLORS[idx%len(COLORS)]
    ax.fill_between(theta_smooth,BASE_RADIUS,r_values,color=color,alpha=.3,label=f'数据系列{idx+1}')
    ax.plot(theta_smooth,r_values,color=color,linewidth=2,alpha=.9)
ax.set_ylim(0,LIMIT_RADIUS)
ax.set_yticks(np.linspace(BASE_RADIUS,LIMIT_RADIUS,4)[1:]);ax.set_yticklabels([])
labels_deg=np.arange(0,360,45)
ax.set_xticks(np.deg2rad(labels_deg),[f'{d}°' for d in labels_deg],fontsize=9,color='#555555')
ax.tick_params(axis='x',pad=12)
# Cover the center using public polar coordinates rather than unused private-transform Circle.
ax.fill_between(np.linspace(0,2*np.pi,300),0,BASE_RADIUS,color='white',zorder=10)
ax.legend(loc='upper center',bbox_to_anchor=(.5,-.1),frameon=False,fontsize=10,ncol=3)
plt.tight_layout();plt.show()

