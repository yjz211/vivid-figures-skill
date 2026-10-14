"""Three-dimensional grouped gradient bars, adapted from the supplied reproduction.
Default demo heights were transcribed from the reference image; demo errors are
illustrative only. Custom data never receives invented uncertainty.
Run from a bootstrapped Vivid workspace, or directly from the installed catalog.
"""
from pathlib import Path
import argparse
import csv
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm, to_rgb, LinearSegmentedColormap
from matplotlib.colorbar import ColorbarBase
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# Resolve the active workspace utilities or the installed skill's shared bundle.
for base in (Path.cwd(), *Path.cwd().parents, *Path(__file__).resolve().parents):
    candidates = (base / '_utils', base / 'original/resources/assets/shared-scripts')
    found = next((p for p in candidates if (p / 'vivid_config.py').is_file()), None)
    if found is not None:
        sys.path.insert(0, str(found))
        break
else:
    raise RuntimeError('Run Vivid bootstrap in the workspace before using this recipe.')
from vivid_config import palette_colors
from plot_utils import setup_style


def read_matrix(path):
    """Wide CSV: first column row label, remaining column headers are conditions."""
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.reader(stream))
    if len(rows) < 2 or len(rows[0]) < 2 or any(len(r) != len(rows[0]) for r in rows):
        raise ValueError('Expected a rectangular CSV with row and column labels.')
    labels, conditions = [r[0] for r in rows[1:]], rows[0][1:]
    if len(set(labels)) != len(labels) or len(set(conditions)) != len(conditions):
        raise ValueError('Row and column labels must be unique.')
    return np.array([[float(v) for v in r[1:]] for r in rows[1:]]), labels, conditions


def plot_chart(values, samples, ss, *, errors=None, bounds=None,
               value_label='Value', sample_label='Sample', condition_label='Condition',
               note=None):
    """errors: nonnegative lengths shaped (rows, columns) or (2, rows, columns).

    A 2-D array gives symmetric errors; a 3-D array gives lower/upper lengths.
    None omits error marks. Heights and colorbar share the same explicit bins.
    """
    values = np.asarray(values, dtype=float)
    if (values.ndim != 2 or values.size == 0 or not np.isfinite(values).all()
            or (values < 0).any() or values.shape != (len(samples), len(ss))):
        raise ValueError('Expected finite nonnegative heights matching both label axes.')
    nrows, ncols = values.shape
    lower = upper = np.zeros_like(values)
    if errors is not None:
        error_array = np.asarray(errors, dtype=float)
        if error_array.shape == values.shape:
            lower = upper = error_array
        elif error_array.shape == (2, *values.shape):
            lower, upper = error_array
        else:
            raise ValueError('Error shape must match heights, optionally with lower/upper axis.')
        if (not np.isfinite(error_array).all() or (error_array < 0).any()
                or (lower > values).any()):
            raise ValueError('Errors must be finite, nonnegative and not cross the zero base.')
    if bounds is None:
        # Linear bins for new data; original demo binning is supplied explicitly.
        bounds = np.linspace(0, max(float(values.max()), 1.0), 12)
    bounds = np.asarray(bounds, dtype=float)
    if (bounds.ndim != 1 or len(bounds) < 3 or not np.isfinite(bounds).all()
            or (np.diff(bounds) <= 0).any()
            or bounds[0] > values.min() or bounds[-1] < values.max()):
        raise ValueError('Increasing bin boundaries must cover every height.')
    setup_style()
    plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'],
                         'font.weight': 'bold', 'axes.labelweight': 'bold', 'font.size': 12,
                         'pdf.fonttype': 42, 'axes.linewidth': 1.2})
    # Numeric bins use the palette's raw ordered scale, not categorical ordering.
    scale = LinearSegmentedColormap.from_list('vivid_ordered', palette_colors())
    colors = scale(np.linspace(0, 1, len(bounds)-1))[:, :3]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(bounds, cmap.N, clip=True)
    fig = plt.figure(figsize=(14.4, 12.8), facecolor='white')
    ax = fig.add_axes([.015, .055, .81, .90], projection='3d', computed_zorder=False)
    ax.view_init(elev=27, azim=-56)
    ax.set_proj_type('ortho')
    ax.set_box_aspect((max(nrows * 1.1, 2), max(ncols * .955, 2), 8))

    # Side faces fade from near-white at the foot to the bin color at the top.
    label_offset = max(float((values + upper).max()), 1.0) * .02
    faces, facecolors = [], []
    w, d = .62, .62
    for i in range(nrows):
        for j in range(ncols):
            h = values[i,j]
            base = np.array(to_rgb(colors[int(norm(h))]))
            x0, x1, y0, y1 = i-w/2, i+w/2, j-d/2, j+d/2
            n = 40 if h > 1.5 else 1
            levels = np.linspace(0, h, n+1)
            for k in range(n):
                z0, z1 = levels[k:k+2]
                t = (k+.5)/n
                c = base if h <= 1.5 else np.ones(3)*(1-t**.65)+base*t**.65
                for points, shade in [([(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)],.98),
                                      ([(x1,y0,z0),(x1,y1,z0),(x1,y1,z1),(x1,y0,z1)],.88),
                                      ([(x1,y1,z0),(x0,y1,z0),(x0,y1,z1),(x1,y1,z1)],.92),
                                      ([(x0,y1,z0),(x0,y0,z0),(x0,y0,z1),(x0,y1,z1)],1.)]:
                    faces.append(points)
                    facecolors.append(np.clip(c*shade,0,1))
            faces.append([(x0,y0,h),(x1,y0,h),(x1,y1,h),(x0,y1,h)])
            facecolors.append(np.clip(base*1.04,0,1))
    ax.add_collection3d(Poly3DCollection(faces, facecolors=facecolors, edgecolors='none',
                                        linewidths=0, antialiased=False, zsort='average', zorder=3))
    # Draw error marks only from the supplied symmetric/asymmetric error lengths.
    for i in range(nrows):
        for j in range(ncols):
            h = values[i,j]
            err = upper[i,j]
            if errors is not None:
                ax.plot([i,i], [j,j], [h-lower[i,j],h+err], c='black', lw=1.25, zorder=5)
                ax.plot([i-.10,i+.10], [j,j], [h+err,h+err], c='black', lw=1.25, zorder=5)
            ax.text(i, j, h+err+label_offset, f'{h:.2f}', ha='center', va='bottom',
                    fontsize=10, zorder=6, bbox=dict(facecolor='white', edgecolor='none', alpha=.87, pad=.15))
    ax.set(xlim=(-.65,nrows-.35), ylim=(-.65,ncols-.35),
           zlim=(0,max(float((values+upper).max()), 1.0) * 1.08))
    ax.set_xticks(range(nrows), samples, rotation=-15)
    ax.set_yticks(range(ncols), ss, rotation=18)
    ax.zaxis.set_major_locator(MaxNLocator(nbins=12))
    ax.set_xlabel(sample_label, labelpad=22, fontsize=19)
    ax.set_ylabel(condition_label, labelpad=24, fontsize=19)
    ax.set_zlabel(value_label, labelpad=20, fontsize=18)
    ax.zaxis._axinfo['juggled'] = (1,2,0)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.set_pane_color((1,1,1,1))
        axis.pane.set_edgecolor('black')
        axis._axinfo['grid'].update(color=(.68,.68,.68,1), linestyle='--', linewidth=.8)
    ax.tick_params(axis='both', labelsize=12, pad=3)
    cax = fig.add_axes([.865,.205,.024,.63])
    cb = ColorbarBase(cax, cmap=cmap, norm=norm, boundaries=bounds, ticks=bounds, spacing='uniform')
    cb.ax.set_yticklabels([f'{v:.3g}' for v in bounds])
    cb.ax.tick_params(labelsize=14, pad=6)
    cb.set_label(value_label, fontsize=18, labelpad=17)
    if note:
        fig.text(.05, .018, note, fontsize=11, color='#444444')
    return fig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, help='Wide CSV of heights')
    parser.add_argument('--errors', type=Path, help='Wide CSV of symmetric error lengths, matching data labels')
    parser.add_argument('--output', type=Path, default=Path('figures/fig_grouped_bar_3d'))
    parser.add_argument('--value-label', default=None)
    args = parser.parse_args()
    if args.data:
        values, samples, conditions = read_matrix(args.data)
        errors = None
        if args.errors:
            errors, error_rows, error_cols = read_matrix(args.errors)
            if samples != error_rows or conditions != error_cols:
                raise ValueError('Error CSV labels and order must match the data CSV.')
        fig = plot_chart(values, samples, conditions, errors=errors,
                         value_label=args.value_label or 'Value')
    else:
        if args.errors:
            parser.error('--errors requires --data')
        # Heights transcribed from the user reference. Errors are illustrative.
        samples = ['C-28', 'C-7', 'C-3', 'C-1', 'U-28', 'U-1']
        conditions = ['SS-0', 'SS-0.1', 'SS-0.2', 'SS-0.3', 'SS-0.4', 'SS-0.5', 'SS-0.6', 'SS-0.7', 'SS-0.8', 'SS-0.9', 'SS-1']
        values = np.array([[0.34, 3.95, 8.36, 13.81, 16.24, 23.39, 32.97, 35.36, 38.44, 46.64, 57.14], [0.33, 3.12, 7.98, 13.09, 14.75, 20.15, 28.26, 31.24, 35.76, 42.32, 55.28], [0.3, 3.01, 6.3, 12.16, 13.12, 18.45, 25.76, 28.29, 33.03, 37.68, 49.88], [0.28, 2.84, 5.48, 9.72, 11.09, 14.44, 22.31, 25.53, 30.48, 34.04, 36.08], [0.33, 2.77, 4.23, 5.52, 6.12, 7.29, 9.26, 10.76, 13.49, 14.24, 17.13], [0.21, 0.55, 0.71, 0.81, 1.12, 1.24, 2.59, 3.54, 3.86, 4.07, 6.31]])
        upper = np.maximum(.10, .025 * values)
        errors = np.stack([.35 * upper, upper])
        bounds = [.21, .35, .58, .97, 1.6, 2.7, 4.5, 7.4, 12.4, 20.6, 34.3, 57.14]
        fig = plot_chart(values, samples, conditions, errors=errors, bounds=bounds,
                         value_label=args.value_label or 'Compressive strength /MPa',
                         condition_label='SS Content',
                         note='Reference-label heights; illustrative error bars (not measured).')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ('png', 'pdf'):
        fig.savefig(args.output.with_suffix('.' + suffix), dpi=300,
                    facecolor='white', bbox_inches='tight', pad_inches=.25)
    plt.close(fig)
    print('Saved PNG and PDF:', args.output)


if __name__ == '__main__':
    main()
