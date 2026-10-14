"""Two complete SHAP compositions reconstructed from image-only references.

The demo is a synthetic prediction model with exact interventional
SHAP values against an empirical marginal background, not a fitted study.
Real inputs must supply X and SHAP for the same samples and model output.
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
from matplotlib.colors import LinearSegmentedColormap, Normalize, to_rgb
from matplotlib.cm import ScalarMappable
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator

for base in (Path.cwd(), *Path.cwd().parents, *Path(__file__).resolve().parents):
    found = next((p for p in (base/'_utils', base/'original/resources/assets/shared-scripts')
                  if (p/'vivid_config.py').is_file()), None)
    if found is not None:
        sys.path.insert(0, str(found))
        break
else:
    raise RuntimeError('Run Vivid bootstrap in the workspace first.')
import plot_utils as pu
from palette_maps import palette_cmap


def validate_data(x, shap, names):
    x, shap = np.asarray(x, float), np.asarray(shap, float)
    if x.ndim != 2 or x.shape != shap.shape or x.shape[0] < 3 or x.shape[1] < 2:
        raise ValueError('X and SHAP must be equal-shaped sample-by-feature matrices (at least 3 x 2).')
    if len(names) != x.shape[1] or len(set(names)) != len(names) or any(not str(n).strip() for n in names):
        raise ValueError('Feature names must be nonempty, unique, and match the columns.')
    if not np.isfinite(x).all() or not np.isfinite(shap).all():
        raise ValueError('Resolve missing/nonfinite values before plotting; rows are never silently removed.')
    if not np.any(shap):
        raise ValueError('All SHAP values are zero; relative contribution is undefined.')
    return x, shap


def read_table(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.reader(f))
    if not rows or rows[0][0] != 'sample_id' or len(rows[0]) < 3:
        raise ValueError('CSV needs sample_id followed by at least two feature columns.')
    header = rows[0]
    if len(set(header)) != len(header) or any(not s.strip() for s in header):
        raise ValueError('Duplicate or empty CSV column names.')
    if any(len(row) != len(header) for row in rows[1:]):
        raise ValueError('Ragged CSV rows.')
    ids = [row[0] for row in rows[1:]]
    if len(set(ids)) != len(ids) or any(not s.strip() for s in ids):
        raise ValueError('sample_id must be unique and nonempty.')
    return ids, header[1:], np.asarray([row[1:] for row in rows[1:]], float)


def load_inputs(features, values):
    ids, names, x = read_table(features)
    sid, snames, shap = read_table(values)
    if set(ids) != set(sid) or set(names) != set(snames):
        raise ValueError('Feature and SHAP files must contain the same sample IDs and feature names.')
    # Explicit keyed alignment protects against independently sorted CSVs.
    ri, ci = {s:i for i,s in enumerate(sid)}, {s:i for i,s in enumerate(snames)}
    shap = shap[np.ix_([ri[s] for s in ids], [ci[s] for s in names])]
    x, shap = validate_data(x, shap, names)
    return x, shap, names


def summarize(shap, names, groups=None):
    importance = np.mean(np.abs(shap), axis=0)
    total = float(importance.sum())
    if total <= 0 or not np.isfinite(total):
        raise ValueError('Positive finite total absolute importance required.')
    order = np.argsort(-importance, kind='stable')
    result = dict(importance=importance.tolist(), percent=(100*importance/total).tolist(),
                  order=order.tolist(), names=list(names), denominator='all input features')
    if groups is not None:
        if (not isinstance(groups, dict) or set(groups) != set(names)
                or any(not isinstance(v,str) or not v.strip() for v in groups.values())):
            raise ValueError('Group mapping must assign every feature exactly one nonempty group.')
        group_names = list(dict.fromkeys(groups[n] for n in names))
        result['groups'] = [dict(name=g, importance=float(sum(importance[j] for j,n in enumerate(names) if groups[n]==g)))
                            for g in group_names]
        for g in result['groups']:
            g['percent'] = 100*g['importance']/total
    return result


def normalize_feature(values):
    lo, hi = float(np.min(values)), float(np.max(values))
    return np.full(len(values), .5) if hi == lo else (values-lo)/(hi-lo)


def swarm_offsets(values, bins=45, max_width=.30):
    """Deterministic density packing; never perturbs the SHAP x coordinate."""
    span = np.ptp(values)
    which = np.zeros(len(values), int) if span == 0 else np.minimum(((values-values.min())/span*bins).astype(int), bins-1)
    offsets = np.zeros(len(values))
    for b in np.unique(which):
        ix = np.flatnonzero(which == b)
        # Alternate above/below the exact row, increasing with local density.
        k = np.arange(len(ix))
        offsets[ix] = np.where(k%2, (k+1)//2, -(k//2))
    scale = max(1., np.max(np.abs(offsets)))
    return offsets/scale*max_width


def smooth_trend(x, y):
    """Local linear descriptive smoother; no causal or breakpoint inference."""
    if len(np.unique(x)) < 5:
        return None
    grid = np.linspace(x.min(), x.max(), 90)
    nhood = min(len(x), max(12, int(np.ceil(len(x)*.28))))
    fitted = []
    for at in grid:
        dist = np.abs(x-at)
        radius = np.partition(dist, nhood-1)[nhood-1]
        if radius == 0:
            fitted.append(float(y[dist == 0].mean()))
            continue
        u = np.clip(dist/(radius*1.000001), 0, 1)
        weights = (1-u**3)**3
        design = np.column_stack((np.ones(len(x)), x-at))
        coef = np.linalg.lstsq(design*np.sqrt(weights[:,None]), y*np.sqrt(weights), rcond=None)[0]
        fitted.append(float(coef[0]))
    return grid, np.asarray(fitted)


def validate_thresholds(thresholds, x, names):
    if not isinstance(thresholds, dict) or not set(thresholds).issubset(names):
        raise ValueError('Thresholds must map known feature names to value/method objects.')
    for name, item in thresholds.items():
        if not isinstance(item,dict) or not isinstance(item.get('method'),str) or not item['method'].strip():
            raise ValueError('Every supplied threshold needs a documented method.')
        value = float(item['value'])
        column = x[:,names.index(name)]
        if not np.isfinite(value) or not column.min() <= value <= column.max():
            raise ValueError('Threshold outside observed feature range.')


def theme(mode, reference=False):
    pu.setup_style()
    plt.rcParams.update({'font.family':['Times New Roman','SimSun','DejaVu Serif'],
                         'font.size':8, 'axes.labelsize':8, 'xtick.labelsize':7,
                         'ytick.labelsize':8, 'axes.linewidth':.8, 'axes.grid':False,
                         'pdf.fonttype':42, 'svg.fonttype':'none'})
    if reference:
        # Explicit opt-in reference colors only; the default uses project colors.
        ends = ['#333884','#EEEAF0','#C63F54'] if mode=='dependence' else ['#25237A','#EEEAF0','#9A075C']
        colors = ['#D71063','#008D98','#2E3688']
        cmap = LinearSegmentedColormap.from_list('reference_shap',ends)
    else:
        colors = list(pu.PALETTE)
        cmap = palette_cmap('diverging')
    return cmap, colors


def clean_axis(ax, box=False):
    ax.grid(False)
    ax.spines['top'].set_visible(box)
    ax.spines['right'].set_visible(box)
    ax.tick_params(length=2.5, width=.65, pad=2)
    ax.xaxis.set_major_locator(MaxNLocator(4))


def feature_colorbar(fig, rect, cmap):
    cax = fig.add_axes(rect)
    cb = fig.colorbar(ScalarMappable(norm=Normalize(0,1), cmap=cmap), cax=cax)
    cb.set_ticks([0,1], labels=['Low','High'])
    cb.ax.tick_params(length=0, labelsize=7)
    cb.set_label('Feature value (within feature)', fontsize=8, labelpad=5)
    cb.outline.set_visible(False)


def plot_dependence(x, shap, names, *, top=15, panels=8, thresholds=None, reference=False):
    x, shap = validate_data(x,shap,names)
    if not 1 <= top <= 25 or not 1 <= panels <= 12:
        raise ValueError('top: 1–25; panels: 1–12.')
    thresholds = {} if thresholds is None else thresholds
    validate_thresholds(thresholds,x,names)
    stats = summarize(shap,names)
    order = stats['order'][:top]
    selected = order[:panels]
    cmap, colors = theme('dependence',reference)
    # Intended full-width 180 mm: 8 pt * (180/25.4)/7.1 = 7.99 pt.
    rows = int(np.ceil(len(selected)/2))
    fig = plt.figure(figsize=(7.1,max(4.1,rows*.86+.65)))
    ax = fig.add_axes([.10,.13,.32,.75])
    bars = ax.twiny()
    bars.set_zorder(0); ax.set_zorder(1); ax.patch.set_visible(False)
    imp = np.asarray(stats['importance'])
    barcolors = [cmap(.92-.75*k/max(1,len(order)-1)) for k in range(len(order))]
    bars.barh(np.arange(len(order)),imp[order],height=.63,color=barcolors,
              edgecolor='#333333',linewidth=.85,alpha=.70)
    bars.set_xlim(0,max(imp)*1.13)
    bars.set_xlabel('Importance: mean |SHAP|',fontsize=8,labelpad=7)
    bars.xaxis.set_major_locator(MaxNLocator(3))
    bars.tick_params(axis='x',labelsize=7,length=2)
    ax.axvline(0,color='#666666',lw=.9,zorder=2)
    for row,j in enumerate(order):
        ax.scatter(shap[:,j],row+swarm_offsets(shap[:,j]),c=normalize_feature(x[:,j]),
                   cmap=cmap,vmin=0,vmax=1,s=3.4,alpha=.70,linewidths=0,zorder=3)
    bound = max(float(np.max(np.abs(shap[:,order])))*1.09,.01)
    ax.set_xlim(-bound,bound)
    ax.set_yticks(range(len(order)),[names[j] for j in order])
    ax.set_ylim(len(order)-.4,-.6)
    ax.set_xlabel('SHAP value')
    clean_axis(ax,True)
    fig.text(.04,.94,'(a)',weight='bold',fontsize=10)
    fig.text(.47,.94,'(b)',weight='bold',fontsize=10)
    grid = fig.add_gridspec(rows,2,left=.51,right=.93,bottom=.13,top=.88,wspace=.34,hspace=.64)
    medians, trends = {}, {}
    for k,j in enumerate(selected):
        a = fig.add_subplot(grid[k//2,k%2])
        a.scatter(x[:,j],shap[:,j],c=normalize_feature(x[:,j]),cmap=cmap,vmin=0,vmax=1,
                  s=3.2,alpha=.65,linewidths=0)
        a.axhline(0,color='#CCCCCC',lw=.6,zorder=0)
        med = float(np.median(x[:,j])); medians[names[j]] = med
        a.axvline(med,color='#333333',ls='--',lw=.85)
        trend = smooth_trend(x[:,j],shap[:,j])
        if trend is not None:
            a.plot(*trend,color='#777777',lw=1.1)
            trends[names[j]] = dict(x=trend[0].tolist(),y=trend[1].tolist())
        a.text(.97,.92,f'M={med:.2g}',transform=a.transAxes,ha='right',va='top',fontsize=6)
        if names[j] in thresholds:
            value = float(thresholds[names[j]]['value'])
            a.axvline(value,color=colors[0],ls=':',lw=1.1)
            a.text(.97,.70,f'T={value:.2g}',transform=a.transAxes,ha='right',va='top',fontsize=6,color=colors[0])
        a.set_title(f'({k+1}) {names[j]}',loc='left',fontsize=7.5,pad=3)
        if k%2==0:
            a.set_ylabel('SHAP',fontsize=7,labelpad=1)
        a.yaxis.set_major_locator(MaxNLocator(3))
        a.tick_params(labelsize=6)
        clean_axis(a,True)
    legend = [Line2D([],[],color='#333333',ls='--',lw=.85,label='Median'),
              Line2D([],[],color='#777777',lw=1.1,label='Local trend')]
    if any(names[j] in thresholds for j in selected):
        legend.append(Line2D([],[],color=colors[0],ls=':',label='Supplied threshold'))
    fig.legend(handles=legend,loc='upper center',bbox_to_anchor=(.72,.975),ncol=len(legend),
               frameon=False,fontsize=6.2,handlelength=1.6,columnspacing=.8)
    feature_colorbar(fig,[.95,.16,.012,.68],cmap)
    stats.update(displayed=[names[j] for j in order],medians=medians,thresholds=thresholds,trends=trends)
    return fig, stats


def plot_contribution(x, shap, names, groups, *, top=12, reference=False):
    x, shap = validate_data(x,shap,names)
    if not 1 <= top <= 25:
        raise ValueError('top must be 1–25.')
    stats = summarize(shap,names,groups)
    if not 2 <= len(stats['groups']) <= 6:
        raise ValueError('This grouped composition supports 2–6 meaningful feature groups.')
    cmap, colors = theme('contribution',reference)
    importance = np.asarray(stats['importance']); percent = np.asarray(stats['percent'])
    order = stats['order'][:top]
    group_names = [g['name'] for g in stats['groups']]
    group_colors = {g:colors[i%len(colors)] for i,g in enumerate(group_names)}
    feature_colors = {}
    for group in group_names:
        members = [j for j in stats['order'] if groups[names[j]]==group]
        for k,j in enumerate(members):
            mix = .10+.37*k/max(1,len(members)-1)
            feature_colors[j] = tuple((1-mix)*np.array(to_rgb(group_colors[group]))+mix)
    # 180 mm inclusion gives 8 pt at native width 7.1 in.
    fig = plt.figure(figsize=(7.1,max(3.9,len(order)*.23+.9)))
    ax = fig.add_axes([.10,.14,.50,.77])
    ax.barh(range(len(order)),importance[order],color=[feature_colors[j] for j in order],
            height=.63,edgecolor='white',linewidth=.55)
    for row,j in enumerate(order):
        ax.text(importance[j]+max(importance)*.009,row,
                f'{percent[j]:.2f}%\n({importance[j]:.3f})',va='center',fontsize=6.5,linespacing=.95)
    ax.set_ylim(len(order)-.35,-.65)
    ax.set_yticks(range(len(order)),[names[j] for j in order])
    ax.set_xlim(0,max(importance)*1.30)
    ax.set_xlabel('Mean |SHAP value|')
    clean_axis(ax)
    # Inset occupies the empty right area below the longest ranked bars.
    # Position it from actual bar/annotation extent, so it never hides bars.
    row_start = max(2,int(np.ceil(len(order)*.25)))
    y0 = .21; ring_height = .43
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    lower_labels = ax.texts[row_start:]
    right_edge = max([ax.get_position().x0+.12] +
                     [t.get_window_extent(renderer).transformed(fig.transFigure.inverted()).x1 for t in lower_labels])
    ring_left = max(.30,right_edge+.015)
    ring_width = min(.26,.60-ring_left)
    if ring_width < .18:
        # Flat importance distributions leave no inset space: widen the left
        # axis range (not its bar values) to reserve an honest blank area.
        ax.set_xlim(0,max(importance)*2.15)
        ring_left,ring_width = .35,.25
    ring = fig.add_axes([ring_left,y0,ring_width,ring_height])
    outer = [g['importance'] for g in stats['groups']]
    ring.pie(outer,radius=1,startangle=90,counterclock=False,
             colors=[group_colors[g] for g in group_names],
             wedgeprops=dict(width=.30,edgecolor='white',linewidth=1))
    inner = [j for g in group_names for j in stats['order'] if groups[names[j]]==g]
    ring.pie(importance[inner],radius=.70,startangle=90,counterclock=False,
             colors=[feature_colors[j] for j in inner],
             wedgeprops=dict(width=.23,edgecolor='white',linewidth=.8))
    ring.text(0,0,'Feature\ncontribution',ha='center',va='center',fontsize=7,weight='bold')
    ring.set_aspect('equal')
    # Group labels follow their outer sectors, retaining the reference design.
    angle = 90.
    for g in stats['groups']:
        middle = np.deg2rad(angle-1.8*g['percent'])
        xx, yy = 1.12*np.cos(middle), 1.12*np.sin(middle)
        ring.text(xx,yy,f"{g['name']}\n{g['percent']:.2f}%",
                  ha='left' if xx>.2 else 'right' if xx<-.2 else 'center',
                  va='center',fontsize=6.4,color=group_colors[g['name']],weight='bold')
        angle -= 3.6*g['percent']
    ax2 = fig.add_axes([.68,.14,.25,.77])
    for row,j in enumerate(order):
        ax2.axhline(row,color='#BBBBBB',lw=.45,ls='--',zorder=0)
        ax2.scatter(shap[:,j],row+swarm_offsets(shap[:,j],max_width=.25),
                    c=normalize_feature(x[:,j]),cmap=cmap,vmin=0,vmax=1,
                    s=9,marker='s',alpha=.67,linewidths=0)
    ax2.axvline(0,color='#777777',lw=.8,zorder=0)
    ax2.set_ylim(ax.get_ylim()); ax2.set_yticks([])
    ax2.set_xlabel('SHAP value')
    clean_axis(ax2); ax2.spines['left'].set_visible(False)
    feature_colorbar(fig,[.95,.18,.012,.69],cmap)
    fig.text(.04,.94,'(a)',fontsize=10,weight='bold')
    fig.text(.68,.94,'(b)',fontsize=10,weight='bold')
    stats.update(displayed=[names[j] for j in order],ring_features=[names[j] for j in inner],
                 grouping_rule='sum of feature mean absolute SHAP, not mean absolute grouped signed SHAP')
    return fig,stats


def write_table(path, values, names):
    with Path(path).open('w',encoding='utf8',newline='') as f:
        writer = csv.writer(f); writer.writerow(['sample_id',*names])
        writer.writerows([[f'S{i:04}',*row] for i,row in enumerate(values)])


def demo_data(directory):
    directory = Path(directory); directory.mkdir(parents=True,exist_ok=True)
    rng = np.random.default_rng(20260916)
    names = ['CUR','Aspect','PRE','ELE','EVI','SAVI','LST','TEM','SIL','Slope','NDWI','NDVI']
    x = rng.normal(size=(320,len(names)))
    weights = np.array([.58,.28,.24,.20,.18,.15,.12,.105,.085,.07,.055,.032])
    effects = x*weights
    effects[:,0] = -.7*np.tanh(1.3*x[:,0])
    effects[:,1] = -.35*x[:,1]+.13*np.maximum(x[:,1]-.2,0)
    effects[:,2] = -.29*x[:,2]+.16*np.maximum(x[:,2]-.4,0)
    effects[:,3] = .22*np.tanh(1.4*x[:,3])
    effects[:,4] = .17*(x[:,4]**2-1)
    effects[:,6] = -.14*np.tanh(x[:,6])
    shap = effects-effects.mean(axis=0)
    prediction = 2+effects.sum(axis=1)
    baseline = float(2+effects.mean(axis=0).sum())
    # Exact two-player allocation of pair interactions under the product of
    # empirical marginal backgrounds. This creates genuine interaction spread.
    interactions = [(0,2,.18),(1,3,.10),(4,6,.08),(5,7,.08),(8,9,.03)]
    means = x.mean(axis=0)
    for i,j,coefficient in interactions:
        prediction += coefficient*x[:,i]*x[:,j]
        baseline += coefficient*means[i]*means[j]
        shap[:,i] += coefficient*.5*(x[:,i]-means[i])*(x[:,j]+means[j])
        shap[:,j] += coefficient*.5*(x[:,j]-means[j])*(x[:,i]+means[i])
    groups = {n:('Terrain' if i in [0,1,3,8,9] else 'Climate' if i in [2,6,7] else 'Vegetation') for i,n in enumerate(names)}
    thresholds = {'Aspect':dict(value=.2,method='known hinge in the synthetic additive model'),
                  'PRE':dict(value=.4,method='known hinge in the synthetic additive model')}
    write_table(directory/'features.csv',x,names)
    write_table(directory/'shap.csv',shap,names)
    write_table(directory/'model.csv',np.column_stack((prediction,np.full(len(x),baseline))),['prediction','base_value'])
    for name,data in [('groups',groups),('thresholds',thresholds)]:
        (directory/f'{name}.json').write_text(json.dumps(data,indent=2),encoding='utf8')
    (directory/'PROVENANCE.md').write_text(
        '# Synthetic demonstration\n\nSeed 20260916; 320 independent normal samples, 12 features. '
        'Feature names are layout labels, not measured environmental quantities; x values are standardized synthetic inputs. '
        'The model is f(x)=2+sum(g_j(x_j))+sum(a_ij*x_i*x_j); demo_data defines every term. '
        'Main-term SHAP_j=g_j(x_j)-mean_background(g_j). Each pair contributes '
        'a_ij/2*(x_i-mu_i)*(x_j+mu_j) to i and the symmetric expression to j. '
        'These are exact interventional SHAP under the product of empirical marginal backgrounds. '
        'base_value+sum(SHAP)=prediction. No trained-model accuracy or causal effects are claimed. '
        'Thresholds are known hinges of the synthetic model, not estimated findings.\n',encoding='utf8')
    return x,shap,names,groups,thresholds


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['dependence','contribution'],required=True)
    parser.add_argument('--features',type=Path); parser.add_argument('--shap',type=Path)
    parser.add_argument('--groups-json',type=Path); parser.add_argument('--thresholds-json',type=Path)
    parser.add_argument('--demo',action='store_true')
    parser.add_argument('--reference-colors',action='store_true')
    parser.add_argument('--top',type=int,default=15); parser.add_argument('--panels',type=int,default=8)
    parser.add_argument('--output',type=Path,default=Path('figures/fig_shap_composite'))
    args = parser.parse_args()
    if args.demo and any([args.features,args.shap,args.groups_json,args.thresholds_json]):
        parser.error('--demo cannot be combined with real input files.')
    if args.mode=='contribution' and args.thresholds_json:
        parser.error('Thresholds apply only to dependence mode.')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    try:
        if args.demo:
            x,shap,names,groups,thresholds = demo_data(args.output.parent/'demo-data')
        else:
            if args.features is None or args.shap is None:
                parser.error('Supply --features and --shap, or explicitly select --demo.')
            x,shap,names = load_inputs(args.features,args.shap)
            groups = json.loads(args.groups_json.read_text(encoding='utf-8-sig')) if args.groups_json else None
            thresholds = json.loads(args.thresholds_json.read_text(encoding='utf-8-sig')) if args.thresholds_json else {}
        if args.mode=='dependence':
            fig,stats = plot_dependence(x,shap,names,top=args.top,panels=args.panels,
                                       thresholds=thresholds,reference=args.reference_colors)
        else:
            if groups is None:
                parser.error('Contribution mode requires --groups-json.')
            fig,stats = plot_contribution(x,shap,names,groups,top=args.top,reference=args.reference_colors)
    except (ValueError,KeyError,TypeError) as exc:
        parser.error(str(exc))
    stats.update(mode=args.mode,synthetic_demo=args.demo,reference_colors=args.reference_colors,
                 color_normalization='min/max separately within each feature; constant maps to midpoint',
                 samples=len(x),feature_count=len(names),
                 input_files=None if args.demo else dict(features=str(args.features.resolve()),shap=str(args.shap.resolve())))
    for ext in ['png','pdf']:
        fig.savefig(args.output.with_suffix('.'+ext),dpi=350,facecolor='white',bbox_inches='tight',pad_inches=.06)
    args.output.with_suffix('.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf8')
    plt.close(fig)
    print(f'Saved {args.output} (PNG, PDF, JSON)')


if __name__=='__main__':
    main()
