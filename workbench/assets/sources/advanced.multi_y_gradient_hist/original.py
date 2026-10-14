"""Shared-X gradient histograms, independent colored Y axes and normal fits.
Reconstructed from a user image; default samples are synthetic, not paper data.
Custom CSV uses columns group,value. Normal fits describe data; they do not
establish normality. Independent Y scales do not permit direct height comparison.
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
from matplotlib.collections import PolyCollection
from matplotlib.colors import to_rgb
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator, MultipleLocator

for base in (Path.cwd(), *Path.cwd().parents, *Path(__file__).resolve().parents):
    found = next((p for p in (base/'_utils', base/'original/resources/assets/shared-scripts')
                  if (p/'vivid_config.py').is_file()), None)
    if found is not None:
        sys.path.insert(0, str(found))
        break
else:
    raise RuntimeError('Run Vivid bootstrap in the workspace before using this recipe.')
from vivid_config import categorical_colors
from plot_utils import setup_style


def read_samples(path):
    groups = {}
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        rows = csv.DictReader(stream)
        if not {'group', 'value'}.issubset(rows.fieldnames or []):
            raise ValueError('CSV requires group,value columns.')
        for row in rows:
            name = row['group'].strip()
            if not name:
                raise ValueError('Group labels cannot be empty.')
            groups.setdefault(name, []).append(float(row['value']))
    return groups


def plot_chart(groups, *, bins=14, xlabel='Residual', fit=True, ylimits=None,
               note=None, colors=None, xlim=None, ytick_step=None):
    """One to three groups of raw observations with a shared X scale.

    bins may be shared or a dict of group-specific equal-width bin edges.

    Each normal curve is mean/std(ddof=0) fitted to its own raw sample, scaled
    by sample count * bin width to approximate frequency on that group's axis.
    Optional ylimits supplies one (0, upper) pair per group without clipping.
    """
    if not 1 <= len(groups) <= 3:
        raise ValueError('Use one to three groups to keep the independent axes readable.')
    arrays = {str(name): np.asarray(values, dtype=float) for name, values in groups.items()}
    if len(arrays) != len(groups) or any(not name.strip() for name in arrays):
        raise ValueError('Group labels must be distinct nonempty strings.')
    for name, values in arrays.items():
        if values.ndim != 1 or len(values) < 2 or not np.isfinite(values).all():
            raise ValueError(f'{name}: provide at least two finite raw observations.')
        if fit and values.std(ddof=0) <= 0:
            raise ValueError(f'{name}: zero variance; disable the normal fit.')
    combined = np.concatenate(list(arrays.values()))
    if isinstance(bins, dict) and set(bins) != set(arrays):
        raise ValueError('Group-specific bins must include every group exactly once.')
    bin_edges = {}
    for name, values in arrays.items():
        edges = np.histogram_bin_edges(values if isinstance(bins,dict) else combined,
                                       bins=bins[name] if isinstance(bins,dict) else bins)
        widths = np.diff(edges)
        if (len(widths) < 2 or not np.isfinite(edges).all() or (widths <= 0).any()
                or not np.allclose(widths, widths[0])
                or edges[0] > values.min() or edges[-1] < values.max()):
            raise ValueError('Each group needs equal-width bins covering all its observations.')
        bin_edges[name] = edges
    if ylimits is not None and len(ylimits) != len(arrays):
        raise ValueError('Supply one Y range for every group.')
    if ytick_step is not None and (not np.isfinite(ytick_step) or ytick_step <= 0):
        raise ValueError('Y tick step must be positive and finite.')

    setup_style()
    colors = categorical_colors() if colors is None else colors
    if len(colors) < len(arrays):
        raise ValueError('The selected palette needs at least one color per group.')
    plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'],
                         'font.weight': 'bold', 'axes.labelweight': 'bold',
                         'pdf.fonttype': 42, 'font.size': 11, 'axes.linewidth': 1.25})
    fig, host = plt.subplots(figsize=(9.5, 7.2))
    fig.subplots_adjust(left=.085, right=.86 if len(arrays) == 3 else .92,
                        bottom=.12, top=.975)
    axes = [host] + [host.twinx() for _ in range(len(arrays)-1)]
    extent = (min(e[0] for e in bin_edges.values()), max(e[-1] for e in bin_edges.values()))
    if xlim is not None and (len(xlim)!=2 or not np.isfinite(xlim).all()
                            or xlim[0]>extent[0] or xlim[1]<extent[1]):
        raise ValueError('X range must cover all histogram bins.')
    host.set_xlim(*(extent if xlim is None else xlim))
    host.set_xlabel(xlabel, fontsize=15)
    host.spines['top'].set_visible(True)
    host.tick_params(axis='x', top=True, direction='in', width=1.25, length=6)
    # All data layers live on the host with each group's own data transform.
    # This keeps every dashed fit above all translucent bars across twin axes.
    host.set_zorder(10)
    for ax in axes:
        ax.patch.set_visible(False)
        ax.grid(False)
    legend_bars, legend_fits, stats = [], [], []
    for i, ((name, values), ax) in enumerate(zip(arrays.items(), axes)):
        color = colors[i]
        edges = bin_edges[name]
        widths = np.diff(edges)
        counts, _ = np.histogram(values, bins=edges)
        mu, sigma = float(values.mean()), float(values.std(ddof=0))
        xfit = np.linspace(*host.get_xlim(), 700)
        yfit = (len(values)*widths[0]/(sigma*np.sqrt(2*np.pi))
                * np.exp(-.5*((xfit-mu)/sigma)**2)) if fit else np.zeros_like(xfit)
        peak = max(float(counts.max()), float(yfit.max()), 1.)
        ylim = (0., peak*1.28) if ylimits is None else tuple(ylimits[i])
        if len(ylim) != 2 or not np.isfinite(ylim).all() or ylim[0] != 0 or ylim[1] < peak:
            raise ValueError('Y ranges must start at zero and cover all counts and fitted peaks.')
        ax.set_ylim(*ylim)
        side = 'left' if i == 0 else 'right'
        if i:
            ax.spines['left'].set_visible(False)
            ax.spines['top'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['right'].set_position(('axes', 1.+.12*(i-1)))
        else:
            ax.spines['right'].set_visible(False)
        ax.spines[side].set_color(color)
        ax.spines[side].set_visible(True)
        ax.tick_params(axis='y', colors=color, direction='in', width=1.3, length=6)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=6, integer=True) if ytick_step is None
                                  else MultipleLocator(ytick_step))
        # Reference layout: one black frequency label; group/axis mapping is
        # carried by colored ticks and the matching legend, not repeated titles.
        ax.set_ylabel('Frequency' if i == 0 else '', color='black', fontsize=15, labelpad=6)

        # True alpha gradient: transparent foot to colored cap, not an opaque
        # white rectangle. Earlier groups remain visible through overlaps.
        vertices, facecolors = [], []
        rgb = to_rgb(color)
        for left, width, height in zip(edges[:-1], widths, counts):
            if height == 0:
                continue
            levels = np.linspace(0., float(height), 65)
            for k, (low, high) in enumerate(zip(levels[:-1], levels[1:])):
                x0, x1 = left+.11*width, left+.89*width
                vertices.append([(x0,low),(x1,low),(x1,high),(x0,high)])
                facecolors.append((*rgb, .02+.76*((k+.5)/64)**.85))
        host.add_collection(PolyCollection(vertices, facecolors=facecolors,
                            edgecolors='none', antialiased=False,
                            transform=ax.transData, zorder=2+({0:.1,1:0.,2:.2}[i])), autolim=False)
        legend_bars.append(Patch(facecolor=color, alpha=.75, edgecolor='none',
                                 label=name))
        if fit:
            host.plot(xfit, yfit, color=color, ls='--', lw=2.2,
                      transform=ax.transData, zorder=5)
            legend_fits.append(Line2D([],[],color=color,ls='--',lw=2.2,
                                      label=fr'{name} fit ($\mu={mu:.1f},\ \sigma={sigma:.1f}$)'))
        stats.append(dict(group=name,n=len(values),mean=mu,std_mle=sigma,
                          counts=counts.tolist(),bin_edges=edges.tolist(),
                          color=color,ylim=list(ylim),fit='normal_mle' if fit else None))
    host.legend(handles=legend_bars[::-1]+legend_fits[::-1],loc='upper left',fontsize=8.6,
                handlelength=2.2,labelspacing=.25,borderpad=.4,
                frameon=True,facecolor='white',edgecolor='#aaaaaa',framealpha=.94)
    if note:
        fig.text(.085,.025,note,fontsize=8,color='#444444')
    return fig, stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',type=Path,help='Long CSV: group,value')
    parser.add_argument('--bins',type=int,default=None)
    parser.add_argument('--no-fit',action='store_true')
    parser.add_argument('--reference-colors',action='store_true',help='Explicit screenshot color reproduction; otherwise use the project palette')
    parser.add_argument('--xlabel',default='Residual')
    parser.add_argument('--output',type=Path,default=Path('figures/fig_multi_y_gradient_hist'))
    args = parser.parse_args()
    if args.data:
        groups, note = read_samples(args.data), None
    else:
        groups = {}
        # Controlled synthetic samples match the reference's approximate widths
        # and locations; neither counts nor samples were recovered from the paper.
        for name,n,mu,sigma,seed in [('Group A',90,3.1,14.3,17),
                                     ('Group B',105,-6.5,23.4,53),
                                     ('Group C',100,2.5,10.,11)]:
            sample = np.random.default_rng(seed).normal(size=n)
            groups[name] = (sample-sample.mean())/sample.std()*sigma+mu
        note = 'Synthetic reconstruction; independent colored Y scales.'
    options = {}
    if args.data is None and args.bins is None:
        # Offset bins reproduce the interleaved bars visible in the reference.
        options = dict(bins={'Group A':np.arange(-70.,71.,10.),
                             'Group B':np.arange(-72.,79.,10.),
                             'Group C':np.arange(-68.,77.,8.)},
                       ylimits=[(0,29),(0,27),(0,33.5)],ytick_step=5)
    else:
        options['bins'] = args.bins if args.bins is not None else 14
    if args.reference_colors:
        options['colors'] = ['#E74C3C','#40516D','#22998D']
    fig, stats = plot_chart(groups,xlabel=args.xlabel,fit=not args.no_fit,note=note,**options)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    for suffix in ('png','pdf'):
        fig.savefig(args.output.with_suffix('.'+suffix),dpi=300,facecolor='white',
                    bbox_inches='tight',pad_inches=.2)
    args.output.with_suffix('.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf8')
    if args.data is None:
        with args.output.with_suffix('.csv').open('w',encoding='utf8',newline='') as stream:
            writer=csv.writer(stream);writer.writerow(['group','value'])
            for name,values in groups.items():
                writer.writerows((name,float(v)) for v in values)
    plt.close(fig)
    print('Saved PNG, PDF and statistics:',args.output)


if __name__ == '__main__':
    main()
