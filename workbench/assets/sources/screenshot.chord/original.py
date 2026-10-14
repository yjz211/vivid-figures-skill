"""透明弦图
Restored/adapted from supplied screenshots [76, 77].
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
from pycirclize import Circos
def generate_random_matrix(size,min_value,max_value,large_value_prob=.1):
    matrix=np.zeros((size,size))
    for i in range(size):
        for j in range(size):
            if i!=j:
                matrix[i,j]=np.random.uniform(max_value*.95,max_value) if np.random.rand()<large_value_prob else np.random.uniform(min_value,max_value*.1)
    return matrix.tolist()
labels=[f'基因{chr(65+i)}' for i in range(10)]
color_map=['#214e81','#c0627a']*5
cmap={label:color+'77' for label,color in zip(labels,color_map)}
np.random.seed(2)
interaction_df=pd.DataFrame(generate_random_matrix(10,1,500,.2),index=labels,columns=labels)
circos=Circos.initialize_from_matrix(interaction_df,space=3,r_lim=(63,70),cmap=cmap,ticks_interval=500,
    label_kws=dict(r=64,size=6,color='white',fontweight='bold'),
    ticks_kws=dict(line_kws=dict(ec='#597cab'),text_kws=dict(weight='bold'),label_size=6),link_kws=dict(alpha=.4))
for sector in circos.sectors:
    sector.tracks[0].axis(ec='white',lw=1.5)
fig=circos.plotfig(figsize=(8,5),dpi=150)
fig.text(.04,.57,'基因关联弦图',fontsize=21,fontweight='bold',color='#515a85')
fig.text(.04,.48,'Synthetic interactions',fontsize=11,fontweight='bold')
fig.subplots_adjust(left=.32,right=1,top=1,bottom=0)
plt.show()

