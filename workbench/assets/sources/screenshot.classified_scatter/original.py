"""分类散点与决策区域
Restored/adapted from supplied screenshots [107, 108, 109].
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
from sklearn.svm import SVC
from matplotlib.colors import ListedColormap
import matplotlib.ticker as ticker
n=80;np.random.seed(7)
X1=np.random.normal(30,8,n);Y1=np.random.normal(60,18,n)
X2=np.random.normal(70,13,n);Y2=np.random.normal(90,20,n)
X3=np.random.normal(55,15,n);Y3=np.random.normal(50,15,n)
X=np.concatenate([np.column_stack((a,b)) for a,b in [(X1,Y1),(X2,Y2),(X3,Y3)]])
y=np.array([0]*n+[1]*n+[2]*n)
model=SVC(kernel='linear',decision_function_shape='ovo').fit(X,y)
x_max=X[:,0].max()+5;y_max=X[:,1].max()+10
xx,yy=np.meshgrid(np.arange(-5,x_max,.5),np.arange(-10,y_max,.5))
Z=model.predict(np.c_[xx.ravel(),yy.ravel()]).reshape(xx.shape)
colors=['#e97a7a','#5595d1','#e5c679']
fig,ax=plt.subplots(figsize=(9,5.5),dpi=150)
ax.contourf(xx,yy,Z,levels=[-.5,.5,1.5,2.5],alpha=.2,cmap=ListedColormap(colors))
for i,(a,b,c) in enumerate(zip([X1,X2,X3],[Y1,Y2,Y3],colors)):
    ax.scatter(a,b,s=100,c=c,alpha=.5,label=f'类别{i+1}')
    ax.scatter(a,np.zeros(len(a)),marker='|',color=c,alpha=.5,s=300)
    ax.scatter(np.zeros(len(a)),b,marker='_',color=c,alpha=.5,s=300)
ax.xaxis.set_major_locator(ticker.MultipleLocator(10));ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))
ax.yaxis.set_major_locator(ticker.MultipleLocator(20));ax.yaxis.set_minor_locator(ticker.MultipleLocator(2))
ax.set(title='分类散点与拟合决策区域',xlabel='X 轴',ylabel='Y 轴')
ax.legend(loc='upper center',ncols=3,frameon=False)
plt.tight_layout();plt.show()

