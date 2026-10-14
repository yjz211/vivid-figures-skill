"""多型号价格堆叠面积
Restored/adapted from supplied screenshots [49, 50, 51].
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
def load_data(file_path):
    return pd.read_csv(file_path)
read_custom_data=False
if read_custom_data:
    data=load_data('airplane_price_dataset.csv')
else:
    # The archive does not include aircraft price data. This is a synthetic schema demo.
    rng=np.random.default_rng(48)
    models=['Boeing 777','Boeing 737','Airbus A350','Airbus A330','Bombardier CRJ900','Cessna 172']
    records=[]
    for i,model in enumerate(models):
        for age in range(46):
            for k in range(5):
                price=(4.8e8-i*5.5e7)*(.4+.6*np.exp(-age/12))*rng.uniform(.95,1.05)
                records.append((model,age,price))
    data=pd.DataFrame(records,columns=['Model','Yas','Fiyat ($)'])
plt.rcParams.update({'axes.facecolor':'#f1f5f9','axes.edgecolor':'white','axes.labelcolor':'#515a85','text.color':'#515a85','xtick.color':'#515a85','ytick.color':'#515a85'})
def create_stacked_area_chart(ax,data):
    age_groups=data.groupby(['Model','Yas'])['Fiyat ($)'].mean().reset_index()
    models=age_groups['Model'].unique()
    colors=['#214e81','#6983a2','#8d9eb2','#b59fb1','#dc9fb0','#c2768b']
    ages=np.sort(age_groups['Yas'].unique())
    y_list=[]
    for model in models:
        model_data=age_groups[age_groups.Model==model]
        y_values=model_data.set_index('Yas').reindex(ages)['Fiyat ($)'].values
        if np.isnan(y_values).any():raise ValueError('Missing age/model cells need explicit treatment; not zero filling')
        y_list.append((model,y_values))
    y_list.sort(key=lambda x:np.sum(x[1]),reverse=True)
    bottom=np.zeros(len(ages))
    for i,(model,y_values) in enumerate(y_list):
        ax.fill_between(ages,bottom,bottom+y_values,label=model,color=colors[i],alpha=.6,edgecolor='white',linewidth=1)
        bottom+=y_values
    ax.set(xlabel='使用年限（年）',ylabel='各型号均价的累计值（$）',xlim=(ages.min(),ages.max()),ylim=(0,max(2e9,bottom.max()*1.1)))
    ax.legend(loc='upper right',bbox_to_anchor=(.98,.98),ncol=2,fontsize=8)
fig,ax=plt.subplots(figsize=(8,5),dpi=150)
create_stacked_area_chart(ax,data)
plt.tight_layout();plt.show()

