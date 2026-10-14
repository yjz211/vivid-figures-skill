"""排名圆弧条形图
Restored/adapted from supplied screenshots [64, 65, 66].
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
from faker import Faker
Faker.seed(6);np.random.seed(6)
fake=Faker()
company_name=[fake.company() for _ in range(16)]
growth_data=np.sort(np.random.uniform(0,100,16))
def create_colors(hex_colors,data):
    cmap=LinearSegmentedColormap.from_list('custom',hex_colors)
    sm=ScalarMappable(norm=Normalize(min(data),max(data)),cmap=cmap)
    return [sm.to_rgba(v)[:3] for v in data]
fig,ax=plt.subplots(figsize=(10,8),subplot_kw={'projection':'polar'},dpi=150)
max_value=max(growth_data)*2.75
colors=create_colors(['#214e81','#a55d75'],growth_data)
inner_radius=15
for i,(label,value) in enumerate(zip(company_name,growth_data)):
    inner_radius+=1.7;ring_width=1.5
    theta_start=0;theta_end=value/max_value*2*np.pi
    ax.bar((theta_start+theta_end)/2,height=ring_width,width=theta_end-theta_start,bottom=inner_radius,color=colors[i],alpha=.85)
    attr=dict(color=colors[i],rotation=np.degrees(theta_end)+5,ha='left') if theta_end<np.pi/2 else dict(color='white',rotation=np.degrees(theta_end-np.pi)-5,ha='left')
    ax.text(theta_end,inner_radius+ring_width/2,f' {value:.1f}%',va='center',fontsize=8,fontweight='bold',rotation_mode='anchor',**attr)
    ax.text(-.01,inner_radius+ring_width/2,label,ha='right',va='center',color=colors[i],fontsize=8,fontweight='bold')
ax.set(xticks=[],yticks=[],ylim=(0,inner_radius+3))
ax.grid(False);ax.spines['polar'].set_visible(False)
ax.set_theta_direction(1);ax.set_theta_offset(np.pi*1.5)
fig.text(.06,.91,'公司增长率排名',fontsize=24,fontweight='bold',color='#575864')
fig.text(.06,.86,'合成数据 · 共享角度尺度',fontsize=12,color='#575864')
fig.subplots_adjust(left=.12,right=.99,top=.9,bottom=.06)
plt.show()

