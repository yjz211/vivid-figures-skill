"""带背景圆环的极坐标散点
Restored/adapted from supplied screenshots [111, 112].
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
np.random.seed(7);n=50
r1=np.random.uniform(30,80,n);theta1=np.random.uniform(0,.75*np.pi,n)
r2=np.random.uniform(40,70,2*n);theta2=np.random.uniform(.5*np.pi,1.5*np.pi,2*n)
r3=np.random.uniform(20,60,n);theta3=np.random.uniform(1.25*np.pi,2*np.pi,n)
colors=['#e97a7a','#5595d1','#e5c679']
fig,ax=plt.subplots(figsize=(8,5),dpi=150,subplot_kw={'projection':'polar'})
for i,(theta,r,color) in enumerate(zip([theta1,theta2,theta3],[r1,r2,r3],colors)):
    ax.scatter(theta,r,s=100,c=color,alpha=.5,label=f'类别{i+1}',zorder=10)
theta=np.linspace(0,2*np.pi,100)
for i in range(4):
    ax.fill_between(theta,20*i+10,20*i+20,color=colors[0],alpha=.15,zorder=1)
ax.set_title('极坐标分组散点图')
ax.legend(loc='center right',bbox_to_anchor=(1.4,.5),frameon=False)
ax.spines['polar'].set_visible(False)
plt.tight_layout();plt.show()

