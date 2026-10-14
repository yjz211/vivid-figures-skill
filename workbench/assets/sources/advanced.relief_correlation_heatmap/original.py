"""Oblique relief correlation matrix reconstructed from a user reference image.
Square cell faces retain matrix layout; two shaded walls connect to the base.
Color encodes signed Pearson r. Extrusion length is 0.12 + 1.4*(r+1)/2;
this height rule is a declared template choice, not recovered from the image.
"""
from pathlib import Path
import argparse
import csv
import json
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.colors import Normalize, LinearSegmentedColormap
from matplotlib.cm import ScalarMappable

for base in (Path.cwd(), *Path.cwd().parents, *Path(__file__).resolve().parents):
    found=next((p for p in (base/'_utils',base/'original/resources/assets/shared-scripts')
                if (p/'vivid_config.py').is_file()),None)
    if found is not None:
        sys.path.insert(0,str(found));break
else:
    raise RuntimeError('Run Vivid bootstrap in the workspace before using this recipe.')
from plot_utils import setup_style
from palette_maps import palette_cmap


def validate_correlation(matrix, labels):
    matrix=np.asarray(matrix,dtype=float)
    if (matrix.ndim!=2 or matrix.shape[0]!=matrix.shape[1]
            or not 2<=matrix.shape[0]<=40 or len(labels)!=len(matrix)):
        raise ValueError('Provide a square correlation matrix of 2–40 labeled variables.')
    if len(set(labels))!=len(labels) or any(not str(label).strip() for label in labels):
        raise ValueError('Variable labels must be nonempty and unique.')
    if not np.isfinite(matrix).all() or np.any(np.abs(matrix)>1+1e-8):
        raise ValueError('Correlations must be finite and within [-1,1].')
    if not np.allclose(matrix,matrix.T,atol=1e-8,rtol=0) or not np.allclose(np.diag(matrix),1,atol=1e-8,rtol=0):
        raise ValueError('Correlation matrices must be symmetric with diagonal 1.')
    if np.linalg.eigvalsh(matrix).min() < -1e-6:
        raise ValueError('The supplied matrix is not positive semidefinite; verify its source.')
    return matrix


def from_samples(samples, labels):
    values=np.asarray(samples,dtype=float)
    if (values.ndim!=2 or values.shape[0]<3 or values.shape[1]!=len(labels)
            or not np.isfinite(values).all() or np.any(values.std(axis=0)==0)):
        raise ValueError('Supply at least three complete observations and nonconstant numeric columns.')
    return validate_correlation(np.corrcoef(values,rowvar=False),labels)


def cell_geometry(row, col, size, r, relief=1.):
    """Return the two side walls and the colored square face, in draw order."""
    if not np.isfinite(relief) or relief<0:
        raise ValueError('Relief must be finite and nonnegative.')
    x,y=float(col),float(size-1-row)
    base=np.array([[x,y],[x+1,y],[x+1,y+1],[x,y+1]])
    height=relief*(.12+1.4*(float(r)+1)/2)
    face=base+height*np.array([.58,.98])
    bottom=np.array([base[0],base[1],face[1],face[0]])
    left=np.array([base[0],base[3],face[3],face[0]])
    return bottom,left,face,height


def plot_chart(matrix, labels, *, cmap=None, relief=1., note=None):
    """Deterministic 2.5D oblique projection; full N×N matrix, no smoothing.

    Only square faces use the exact colorbar mapping. Side walls are shaded
    for geometry and must not be used to read correlation values.
    """
    matrix=validate_correlation(matrix,labels)
    n=len(labels)
    setup_style()
    cmap=palette_cmap('diverging') if cmap is None else cmap
    norm=Normalize(-1,1)
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','Microsoft YaHei','DejaVu Sans'],
                         'pdf.fonttype':42,'axes.unicode_minus':False})
    fig=plt.figure(figsize=(11.4,10.2),facecolor='white')
    ax=fig.add_axes([.18,.19,.71,.76])
    # Rows at the top/back first, columns right to left: nearer cells cover
    # hidden parts of farther walls while every complete matrix cell is kept.
    faces=[]
    for row in range(n):
        for col in range(n-1,-1,-1):
            r=float(matrix[row,col]);rgb=np.asarray(cmap(norm(r))[:3])
            bottom,left,face,height=cell_geometry(row,col,n,r,relief)
            for points,color in ((bottom,rgb*.77),(left,rgb*.87),(face,rgb)):
                polygon=Polygon(points,closed=True,facecolor=color,
                                edgecolor='#273641',linewidth=.62,joinstyle='miter')
                ax.add_patch(polygon)
            faces.append(dict(row=row,col=col,r=r,height=height,face_color=rgb.tolist()))
    max_height=relief*1.52
    ax.set_xlim(-.02,n+.58*max_height+.06)
    ax.set_ylim(-.02,n+.98*max_height+.06)
    ax.set_aspect('equal')
    ax.set_xticks(np.arange(n)+.5,labels,rotation=90,fontsize=7.4 if n>16 else 9)
    ax.set_yticks(n-np.arange(n)-.5,labels,fontsize=7.4 if n>16 else 9)
    ax.tick_params(axis='both',which='both',length=0,pad=3)
    ax.grid(False)
    for spine in ax.spines.values():spine.set_visible(False)
    # Fixed limits and an unshaded colorbar preserve the sign and magnitude.
    cax=fig.add_axes([.925,.455,.013,.13])
    colorbar=fig.colorbar(ScalarMappable(norm=norm,cmap=cmap),cax=cax,
                         ticks=[-1,-.5,0,.5,1])
    cax.set_title('Pearson r',loc='left',fontsize=9,fontweight='bold',pad=5)
    colorbar.ax.tick_params(labelsize=8,length=2,pad=2)
    colorbar.outline.set_visible(False)
    if note:fig.text(.18,.04,note,fontsize=8,color='#444444')
    return fig,dict(matrix=matrix.tolist(),labels=list(labels),faces=faces,
                    height_rule='relief * (0.12 + 1.4 * (r + 1) / 2)',projection=[.58,.98])


def read_csv(path, matrix_input=False):
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:rows=list(csv.reader(stream))
    if len(rows)<2 or any(len(row)!=len(rows[0]) for row in rows):
        raise ValueError('CSV must be rectangular with a header row.')
    if matrix_input:
        labels=rows[0][1:]
        if [r[0] for r in rows[1:]]!=labels:
            raise ValueError('Matrix row and column labels and ordering must match.')
        matrix=np.array([[float(v) for v in row[1:]] for row in rows[1:]])
        return validate_correlation(matrix,labels),labels,None
    labels=rows[0];samples=np.array([[float(v) for v in row] for row in rows[1:]])
    return from_samples(samples,labels),labels,samples


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    inputs=parser.add_mutually_exclusive_group()
    inputs.add_argument('--data',type=Path,help='Observations CSV; numeric columns with variable names')
    inputs.add_argument('--matrix',type=Path,help='Square correlation CSV with row and column labels')
    parser.add_argument('--reference-colors',action='store_true',help='Explicit blue reference-style ramp')
    parser.add_argument('--relief',type=float,default=1.)
    parser.add_argument('--output',type=Path,default=Path('figures/fig_relief_correlation_heatmap'))
    args=parser.parse_args()
    if args.data or args.matrix:
        matrix,labels,samples=read_csv(args.matrix or args.data,matrix_input=args.matrix is not None)
        note=None
    else:
        # Domain labels follow the reference only to demonstrate its dense layout.
        # All observations are synthetic latent-factor data, not recovered study data.
        labels=['ACs','T-SOD','MPNs','DTPNs','CAT','GSH-PX','Unique AAs','Non-Essential AAs',
                'Essential AAs','Conditionally Essential AAs','SpNDs','Ketone compounds',
                'Hydrocarbon compounds','Alcohol compounds','MDA','T-AOC','Hardness',
                'Springiness','POD','Gumminess','Chewiness','Cohesiveness','Elasticity']
        rng=np.random.default_rng(20260916)
        latent=rng.normal(size=(360,4))
        # Heterogeneous loadings produce varied relief instead of uniform blocks.
        loadings=rng.normal(0,.3,size=(23,4))
        loadings[:,0]=rng.uniform(.3,1.2,size=23)
        loadings[:,1]+=.65*np.sin(np.arange(23)*.85)
        loadings[:,2]+=.55*np.cos(np.arange(23)*.6)
        loadings[10:15,0]*=-1
        noise=rng.uniform(.18,.58,size=23)
        samples=latent@loadings.T+rng.normal(size=(360,23))*noise
        matrix=from_samples(samples,labels)
        note='Synthetic data. Face color = Pearson r; relief increases linearly with r.'
    cmap=None
    if args.reference_colors:
        cmap=LinearSegmentedColormap.from_list('reference_blue',
                     ['#F5FCFC','#CFEAF0','#AAC5E4','#6B9FCB','#399DCB'])
    fig,stats=plot_chart(matrix,labels,cmap=cmap,relief=args.relief,note=note)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    for suffix in ('png','pdf'):
        fig.savefig(args.output.with_suffix('.'+suffix),dpi=300,facecolor='white',
                    bbox_inches='tight',pad_inches=.12)
    args.output.with_suffix('.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf8')
    with args.output.with_suffix('.csv').open('w',encoding='utf8',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(['variable',*labels])
        writer.writerows([label,*row] for label,row in zip(labels,matrix))
    if args.data is None and args.matrix is None:
        with args.output.with_name(args.output.name+'-samples.csv').open('w',encoding='utf8',newline='') as stream:
            writer=csv.writer(stream);writer.writerow(labels);writer.writerows(samples)
    plt.close(fig)
    print('Saved PNG, vector PDF, matrix CSV and geometry:',args.output)


if __name__=='__main__':main()
