"""峰值标注堆叠面积图
Restored/adapted from supplied screenshots [17, 18, 19, 20, 21].
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
import plotly.graph_objects as go
import random
from scipy.signal import find_peaks
read_custom_data = False
def create_data(x,size,n,max_value):
    sigma = size/30
    return max_value*np.exp(-.5*((x-n)/sigma)**2)
if read_custom_data:
    data = pd.read_csv('data.csv')
else:
    random.seed(16)
    size,x_max = 300,80
    x = np.linspace(0,x_max,size)
    peaks = [5,15,23,38,35,48,53,68]
    means = [2.5,1.2,3.,2.5,1.,1.5,2.,2.2]
    data = {'x':x}
    for i in range(4):
        y=np.zeros_like(x)
        for p,m in zip(peaks,means):
            y += create_data(x,x_max,p,m*random.random())
        data[f'类别{i+1}']=y
    data=pd.DataFrame(data)
x=data['x'].values
categories=[c for c in data.columns if c!='x']
colors=['#e7c2cb','#daa2b0','#cd8295','#c0627a']
fig=go.Figure()
for cat,color in zip(categories,colors):
    fig.add_trace(go.Scatter(x=x,y=data[cat],fill='tonexty',mode='none',name=cat,fillcolor=color,stackgroup='one'))
y_stack=np.cumsum(data[categories].T.values,axis=0)
for ys in y_stack:
    fig.add_trace(go.Scatter(x=x,y=ys,mode='lines',line=dict(width=2,color='#ffffff'),showlegend=False))
idx,_=find_peaks(y_stack[-1])
fig.add_trace(go.Scatter(x=x[idx],y=y_stack[-1][idx],mode='markers',marker=dict(symbol='circle',size=8,color='#ffffff',line=dict(width=2,color='#c0627a')),showlegend=False))
for px,py in zip(x[idx],y_stack[-1][idx]):
    fig.add_annotation(x=px,y=py+.3,text=f'{py:.2f}',showarrow=False)
fig.update_layout(xaxis=dict(title='X 轴',range=[0,70]),yaxis=dict(title='值',range=[0,10]),width=800,height=500,
                  legend=dict(orientation='h',y=1.08,x=.5,xanchor='center'))
# Match reference's white plot background; leave room for annotations.
fig.update_layout(margin=dict(l=30,r=30,t=30,b=35))
fig.update_layout(plot_bgcolor='white',paper_bgcolor='white',font=dict(color='#a65c70'),xaxis=dict(showgrid=False,showline=True,linecolor='#c99baa'),yaxis=dict(showgrid=False,showline=True,linecolor='#c99baa'))
fig.show()

