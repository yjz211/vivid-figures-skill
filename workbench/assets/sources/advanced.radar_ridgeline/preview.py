"""Radar-ridgeline fusion reconstructed from a user reference image.

Each ring has a fixed radial baseline. Local Gaussian ridges at the category
spokes encode scalar values on one shared scale. They are not KDE estimates.
"""
from gallery_theme import P, C, dark, palette_cmap, palette_stops
from pathlib import Path
import argparse
import csv
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

for base in (Path.cwd(), *Path.cwd().parents, *Path(__file__).resolve().parents):
    found = next((p for p in (base/'_utils', base/'original/resources/assets/shared-scripts')
                  if (p/'vivid_config.py').is_file()), None)
    if found is not None:
        sys.path.insert(0, str(found)); break
else:
    raise RuntimeError('Run Vivid bootstrap in the workspace before using this recipe.')
from plot_utils import PALETTE, COLORS, setup_style


def read_wide_csv(path):
    """Read category + 2–4 layer columns from a rectangular wide CSV."""
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.reader(stream))
    if len(rows) < 2 or len(rows[0]) < 3 or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError('CSV must be rectangular: category plus 2–4 value columns.')
    categories = [row[0].strip() for row in rows[1:]]
    layer_names = [name.strip() for name in rows[0][1:]]
    if any(not item for item in categories + layer_names):
        raise ValueError('Category and layer labels must be nonempty.')
    values = np.array([[float(value) for value in row[1:]] for row in rows[1:]], dtype=float).T
    return categories, layer_names, values


def validate_data(categories, layer_names, values):
    values = np.asarray(values, dtype=float)
    if not 5 <= len(categories) <= 16:
        raise ValueError('Use 5–16 ordered categories for a readable radial layout.')
    if not 2 <= len(layer_names) <= 4 or values.shape != (len(layer_names), len(categories)):
        raise ValueError('Values must match 2–4 layers by all categories.')
    if (len(set(categories)) != len(categories) or len(set(layer_names)) != len(layer_names)
            or not np.isfinite(values).all()):
        raise ValueError('Labels must be unique and all values finite.')
    return values


def wrapped_delta(theta, center):
    return np.angle(np.exp(1j * (theta - center)))


def ridge_curve(theta, centers, normalized, baseline, width):
    """Add smooth local peaks to one circular baseline."""
    curve = np.full_like(theta, baseline, dtype=float)
    heights = .18 + .55 * normalized
    for center, height in zip(centers, heights):
        curve += height * np.exp(-.5 * (wrapped_delta(theta, center) / width) ** 2)
    return curve


def label_alignment(theta):
    horizontal = np.sin(theta)
    return 'left' if horizontal > .25 else 'right' if horizontal < -.25 else 'center'


def plot_chart(categories, layer_names, values, *, value_suffix='%', value_format='.1f'):
    """Draw 2–4 concentric ridgeline rings on a radar spoke skeleton.

    All values use one global min/max normalization for comparable peak heights.
    Preprocess cost-type indicators so every category has the same direction.
    """
    values = validate_data(categories, layer_names, values)
    setup_style()
    n_categories, n_layers = len(categories), len(layer_names)
    centers = np.linspace(0, 2*np.pi, n_categories, endpoint=False)
    theta = np.linspace(0, 2*np.pi, 1800, endpoint=True)
    span = float(np.ptp(values))
    normalized = np.full_like(values, .5) if span == 0 else (values-values.min())/span
    baselines = .82 + 1.20*np.arange(n_layers)
    width = .23 * (2*np.pi/n_categories)
    color_order = [1, 3, 0, 4]
    colors = [PALETTE[color_order[i] % len(PALETTE)] for i in range(n_layers)]

    fig = plt.figure(figsize=(9.0, 7.7), facecolor='white')
    ax = fig.add_subplot(111, projection='polar')
    ax.set_theta_zero_location('N'); ax.set_theta_direction(-1); ax.set_facecolor('white')
    curves = []
    for row, (name, baseline, color) in enumerate(zip(layer_names, baselines, colors)):
        curve = ridge_curve(theta, centers, normalized[row], baseline, width)
        curves.append(curve)
        ax.fill_between(theta, baseline, curve, color=color, alpha=.72, linewidth=0, zorder=2)
        ax.plot(theta, curve, color=color, linewidth=1.35, alpha=.95, zorder=3)
        ax.plot(theta, np.full_like(theta, baseline), color=color, linewidth=.65,
                alpha=.38, zorder=1)

    outer_label_radius = baselines[-1] + .18 + .55 + .42
    for angle in centers:
        ax.plot([angle, angle], [.16, outer_label_radius-.17], color=COLORS['ref_line'],
                linewidth=.7, linestyle=(0, (3, 4)), alpha=.72, zorder=0)

    for row, curve in enumerate(curves):
        for column, angle in enumerate(centers):
            idx = int(round(angle/(2*np.pi)*(len(theta)-1)))
            ax.text(angle, curve[idx]+.055,
                    f'{values[row, column]:{value_format}}{value_suffix}', fontsize=6.8,
                    ha='center', va='bottom', color='#30343B', zorder=5)

    for angle, category in zip(centers, categories):
        ax.text(angle, outer_label_radius, category, fontsize=10.2, fontweight='medium',
                ha=label_alignment(angle), va='center', color=COLORS['text'], zorder=6)

    ax.set_ylim(0, outer_label_radius+.38)
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False); ax.spines['polar'].set_visible(False)
    handles = [Patch(facecolor=color, edgecolor='none', alpha=.78, label=name)
               for name, color in zip(layer_names, colors)]
    ax.legend(handles=handles, title='数据层', loc='center left', bbox_to_anchor=(1.03, .52),
              frameon=False, handlelength=1.25, handleheight=1.25, labelspacing=.65,
              fontsize=9.2, title_fontsize=10.2)
    fig.subplots_adjust(left=.04, right=.82, top=.97, bottom=.04)
    return fig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, help='Wide CSV: category plus 2–4 comparable layers')
    parser.add_argument('--output', type=Path, default=Path('figures/fig_radar_ridgeline'))
    parser.add_argument('--suffix', default='%', help='Visible value suffix; use an empty string for none')
    parser.add_argument('--format', default='.1f', help='Python numeric format without braces')
    args = parser.parse_args()
    if args.data:
        categories, layer_names, values = read_wide_csv(args.data)
    else:
        categories = ['精度','效率','鲁棒','泛化','稳定','响应','能耗','成本','扩展','安全']
        layer_names = ['测试组','训练组','总体']
        values = np.array([[32.8,25.4,29.7,18.9,24.6,21.3,16.8,22.5,27.9,19.7],
                           [38.6,31.1,35.8,27.6,33.2,29.5,25.1,28.7,34.6,26.4],
                           [44.7,36.2,42.1,34.5,39.8,37.4,31.6,35.2,41.3,33.8]])
    fig = plot_chart(categories, layer_names, values,
                     value_suffix=args.suffix, value_format=args.format)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ('png', 'pdf'):
        fig.savefig(args.output.with_suffix('.'+suffix), dpi=320, facecolor='white',
                    bbox_inches='tight', pad_inches=.18)
    plt.close(fig)
    print('Saved PNG and PDF:', args.output)


if __name__ == '__main__': main()
