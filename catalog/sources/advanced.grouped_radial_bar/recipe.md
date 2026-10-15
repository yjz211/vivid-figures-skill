## 39. 环形分组柱状对比图

用途：在一个环形画布上比较多个任务内的主方案与对比系列，保留原图的分组、外圈层级与强调关系。
输入：2–16个任务×2–8个系列，总柱数不超过96；值须有限非负；大类按任务提供且同名连续，说明可为空。
结构：中心留白标题、每任务一根加宽强调柱与若干比较柱、组间空隙、逐柱数值、外圈任务名及简短说明、最外层分段大类弧、左上图例。
尺度：默认within_task按各任务最小/最大值映射100/300柱长，等值统一200；柱长只在任务内可比，跨任务看原数值。shared模式改用全图共同零基准线性尺度。两模式都不改变原始数值标签和输入顺序。
配色：项目分类色板第二色为强调角色，第一色向白色背景派生比较色阶；粉彩少女展示为紫色主柱及粉色比较柱。
来源：按用户参考图重建；演示中的11任务、55数值及英文说明为图像转录，未独立核验。四个基线列是每个任务内Top1–4，不保证是跨任务固定同一模型。
局限：组内缩放会放大小数值差异，最短柱也不表示零；不适合直接比较不同任务的绝对量或未经处理的不同量纲指标。

```python
"""Grouped radial bars with task labels and outer hierarchy arcs.

Reconstructed from a user-supplied reference image. The reference layout uses explicit within-task min/max scaling. Numeric labels
retain the supplied values; shared-scale mode is available for cross-task comparisons.
"""
from pathlib import Path
import argparse
import csv
import sys
import textwrap

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from matplotlib.patches import Patch

for base in (Path.cwd(), *Path.cwd().parents, *Path(__file__).resolve().parents):
    found = next((p for p in (base / '_utils', base / 'original/resources/assets/shared-scripts')
                  if (p / 'vivid_config.py').is_file()), None)
    if found is not None:
        sys.path.insert(0, str(found))
        break
else:
    raise RuntimeError('Run Vivid bootstrap in the workspace before using this recipe.')
from plot_utils import PALETTE, COLORS, setup_style


def _labels(items, name, count=None, unique=False, allow_empty=False):
    if isinstance(items, (str, bytes)):
        raise ValueError(f'{name} must be a list of labels.')
    labels = [str(item).strip() for item in items]
    if count is not None and len(labels) != count:
        raise ValueError(f'{name} must contain {count} labels.')
    if not allow_empty and any(not label for label in labels):
        raise ValueError(f'{name} labels must be nonempty.')
    if unique and len(set(labels)) != len(labels):
        raise ValueError(f'{name} labels must be unique.')
    return labels


def validate_data(task_names, model_names, values, major_groups=None, task_details=None,
                  highlight_index=0):
    tasks = _labels(task_names, 'Task', unique=True)
    models = _labels(model_names, 'Model', unique=True)
    if not 2 <= len(tasks) <= 16 or not 2 <= len(models) <= 8:
        raise ValueError('Use 2–16 tasks and 2–8 models.')
    if len(tasks) * len(models) > 96:
        raise ValueError('At most 96 bars are supported; split a larger comparison into panels.')
    data = np.asarray(values, dtype=float)
    if data.shape != (len(tasks), len(models)):
        raise ValueError('Values must have shape (number of tasks, number of models).')
    if not np.isfinite(data).all() or (data < 0).any():
        raise ValueError('Values must be finite and nonnegative; missing values are not zero.')
    if not isinstance(highlight_index, (int, np.integer)) or not 0 <= highlight_index < len(models):
        raise ValueError('highlight_index must identify an existing model column.')
    groups = None if major_groups is None else _labels(major_groups, 'Major group', len(tasks))
    if groups is not None:
        runs = [group for i, group in enumerate(groups) if i == 0 or group != groups[i-1]]
        if len(runs) != len(set(runs)):
            raise ValueError('Tasks in the same major group must be contiguous; input order is preserved.')
    details = ([''] * len(tasks) if task_details is None else
               _labels(task_details, 'Task detail', len(tasks), allow_empty=True))
    return tasks, models, data, groups, details


def _upright(rotation):
    """Return an equivalent text rotation that is never upside down."""
    return (rotation + 90) % 180 - 90


def _model_styles(count, highlight_index, background):
    """Derive one emphasis color and a four-step comparison tint from the palette."""
    highlight = PALETTE[1 % len(PALETTE)]
    base = np.array(to_rgb(PALETTE[0]))
    pale = np.array(to_rgb(background))
    colors = [None] * count
    colors[highlight_index] = highlight
    comparison = [i for i in range(count) if i != highlight_index]
    for position, column in enumerate(comparison):
        mix = 0.0 if len(comparison) == 1 else .58 * position / (len(comparison) - 1)
        colors[column] = tuple(base * (1 - mix) + pale * mix)
    return colors


def _layout_angles(task_count, model_count, groups, highlight_index):
    """Wider emphasis bars, small task gaps and larger hierarchy gaps."""
    widths = np.ones(model_count)
    widths[highlight_index] = 1.8
    bar_gap, task_gap, hierarchy_gap = .175, 1.1, 3.3
    span = widths.sum() + bar_gap * (model_count - 1)
    boundary = [groups is not None and groups[i] != groups[(i + 1) % task_count]
                for i in range(task_count)]
    gaps = np.array([hierarchy_gap if major else task_gap for major in boundary])
    factor = 2 * np.pi / (task_count * span + gaps.sum())
    cursor = gaps[-1] / 2
    task_centers, angles, starts, ends = [], [], [], []
    for i in range(task_count):
        starts.append(cursor * factor)
        task_centers.append((cursor + span / 2) * factor)
        row = []
        for j, width in enumerate(widths):
            row.append((cursor + width / 2) * factor)
            cursor += width + (bar_gap if j < model_count - 1 else 0)
        angles.append(row)
        ends.append(cursor * factor)
        cursor += gaps[i]
    return np.asarray(angles), np.asarray(task_centers), widths * factor, starts, ends


def plot_chart(task_names, model_names, values, major_groups=None, task_details=None,
               center_label='方案对比', highlight_index=0, *, value_format='.2f',
               value_suffix='', show_values=True, show_legend=True, scale_max=None,
               scale_mode='within_task', baseline_label=None):
    """Reproduce the reference composition without silently changing data semantics.

    within_task: each task maps its minimum/maximum to radial lengths 100/300.
    Equal values use length 200. The visible values always remain the originals.
    shared: lengths are 300 * value / scale_max, with one zero baseline.
    Input row/column order is preserved. Highlighting does not imply first place.
    """
    tasks, models, data, groups, details = validate_data(
        task_names, model_names, values, major_groups, task_details, highlight_index)
    setup_style()
    maximum = float(data.max())
    scale = maximum if scale_max is None else float(scale_max)
    if scale_max is not None and (not np.isfinite(scale) or scale <= 0 or scale < maximum):
        raise ValueError('scale_max must be finite, positive, and cover all values.')
    if scale_mode not in ('within_task', 'shared'):
        raise ValueError("scale_mode must be 'within_task' or 'shared'.")
    if scale_mode == 'within_task' and scale_max is not None:
        raise ValueError('scale_max applies only to shared-scale mode.')
    if scale_mode == 'within_task':
        minima = data.min(axis=1, keepdims=True)
        ranges = np.ptp(data, axis=1, keepdims=True)
        relative = np.divide(data - minima, ranges, out=np.full_like(data, .5), where=ranges != 0)
        lengths = 100 + 200 * relative
    else:
        lengths = 300 * data / (scale if scale > 0 else 1)
    format(0.0, value_format)
    ntasks, nmodels = data.shape
    dense = ntasks * nmodels > 64
    background = '#FFFFFF'
    ink, arc_color = '#725E4D', '#BFB19E'
    from matplotlib.font_manager import fontManager
    available = {font.name for font in fontManager.ttflist}
    fonts = [name for name in ('Times New Roman', 'DejaVu Serif', 'Microsoft YaHei',
                              'Noto Sans CJK SC', 'WenQuanYi Zen Hei') if name in available]
    # Pixel-equivalent reference geometry: 1331 x 1252, center (660, 653), R=570.
    factor = 1.12 if dense else 1.0
    fig = plt.figure(figsize=(13.31 * factor, 12.52 * factor), facecolor=background)
    ax = fig.add_axes([40 / 1331, -21 / 1252, 1240 / 1331, 1240 / 1252], projection='polar')
    ax.set_facecolor(background)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    angles, centers, widths, starts, ends = _layout_angles(ntasks, nmodels, groups, highlight_index)
    colors = _model_styles(nmodels, highlight_index, background)
    bottom = 165.0
    label_size = 8.5 if dense else 10.2
    comparison = [i for i in range(nmodels) if i != highlight_index]
    for task in range(ntasks):
        for model in range(nmodels):
            angle, length, color = angles[task, model], lengths[task, model], colors[model]
            ax.bar(angle, length, width=widths[model], bottom=bottom, color=color,
                   edgecolor='none', linewidth=0, zorder=3)
            if show_values:
                rotation = _upright(90 - np.degrees(angle))
                outward_right = np.cos(np.radians(rotation) - (np.pi / 2 - angle)) > 0
                inside = length >= 75
                radius = bottom + length - 13 if inside else bottom + length + 6
                alignment = ('right' if outward_right else 'left') if inside else (
                    'left' if outward_right else 'right')
                text_color = ('white' if model in (highlight_index, comparison[0]) else ink) if inside else ink
                ax.text(angle, radius, f'{data[task, model]:{value_format}}{value_suffix}',
                        rotation=rotation, rotation_mode='anchor', ha=alignment, va='center',
                        fontsize=label_size, fontfamily=fonts, fontweight='bold', color=text_color, zorder=6)
    wrap_width = max(12, int(240 / ntasks))
    for angle, task, detail in zip(centers, tasks, details):
        rotation = _upright(-np.degrees(angle))
        lower_half = np.cos(angle) < 0
        task_radius, detail_radius = (500, 535) if lower_half else (535, 500)
        ax.text(angle, task_radius, textwrap.fill(task, width=wrap_width), ha='center', va='center',
                rotation=rotation, rotation_mode='anchor', fontfamily=fonts,
                fontsize=14 if dense else 17, fontweight='bold', color=ink, zorder=7)
        if detail:
            detail_font = min(10 if dense else 12.3, 445 / max(30, len(detail)))
            ax.text(angle, detail_radius, detail,
                    ha='center', va='center', rotation=rotation, rotation_mode='anchor',
                    fontfamily=fonts, fontsize=detail_font, color=ink, zorder=7)
    if groups is not None:
        start = 0
        for end in range(1, ntasks + 1):
            if end == ntasks or groups[end] != groups[start]:
                first, last = starts[start] - .035, ends[end - 1] + .035
                theta = np.linspace(first, last, max(32, (end - start) * 40))
                ax.plot(theta, np.full_like(theta, 570), color=arc_color, linewidth=2.5, zorder=1)
                middle = (first + last) / 2
                if middle > 1.5 * np.pi and len(groups[start]) > 18:
                    middle = last - .30 * (last - first)
                # A long group title follows its tangent, exactly as the reference.
                ax.text(middle, 593, groups[start], ha='center', va='center',
                        rotation=_upright(-np.degrees(middle)), rotation_mode='anchor',
                        fontfamily=fonts, fontsize=16 if dense else 19,
                        fontweight='bold', color='#A18E7B', zorder=8)
                start = end
    title = str(center_label)
    title = textwrap.fill(title, width=18) if len(title) > 18 and '\n' not in title else title
    import unicodedata
    longest = max((sum(2 if unicodedata.east_asian_width(char) in ('W', 'F') else 1
                       for char in line) for line in title.splitlines()), default=0)
    fontsize = min(35.5, 35.5 * 11 / max(1, longest))
    ax.text(.5, .5, title, transform=ax.transAxes, ha='center', va='center',
            fontsize=fontsize, fontfamily=fonts, fontweight='bold', color=colors[highlight_index], zorder=9)
    ax.set_ylim(0, 620)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    ax.spines['polar'].set_visible(False)
    if show_legend:
        if baseline_label is not None:
            from matplotlib.legend_handler import HandlerTuple
            class TopAlignedTuple(HandlerTuple):
                def create_artists(self, legend, orig_handle, xdescent, ydescent, width, height, fontsize, trans):
                    items = super().create_artists(legend, orig_handle, xdescent, ydescent,
                                                   width, height, fontsize, trans)
                    offset = max(0, len(str(baseline_label).splitlines()) - 1) * fontsize * .60
                    for item in items:
                        item.set_y(item.get_y() + offset)
                    return items
            handles = [Patch(facecolor=colors[highlight_index], edgecolor='none'),
                       tuple(Patch(facecolor=colors[i], edgecolor='none') for i in comparison)]
            labels = [models[highlight_index], baseline_label]
            legend = fig.legend(handles, labels, handler_map={tuple: TopAlignedTuple(ndivide=None, pad=.10)},
                                loc='upper left', bbox_to_anchor=(.012, .981), borderaxespad=0,
                                frameon=False, fontsize=15.8, handlelength=1.15,
                                handleheight=1.0, labelspacing=.35, handletextpad=.6)
        else:
            handles = [Patch(facecolor=color, edgecolor='none', label=name)
                       for name, color in zip(models, colors)]
            legend = fig.legend(handles=handles, loc='upper left', bbox_to_anchor=(.012, .981),
                                borderaxespad=0, frameon=False, fontsize=12.0 if nmodels > 5 else 14.0,
                                handlelength=1.15, handleheight=1.0, labelspacing=.25)
        for text in legend.get_texts():
            text.set_fontfamily(fonts)
            text.set_color(ink)
    return fig


def read_wide_csv(path):
    """Read task names followed by model value columns, preserving table order."""
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.reader(stream))
    if len(rows) < 3 or len(rows[0]) < 3 or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError('CSV must be rectangular: task plus 2–8 model columns, at least 2 tasks.')
    tasks = [row[0].strip() for row in rows[1:]]
    models = [cell.strip() for cell in rows[0][1:]]
    values = np.array([[float(cell) for cell in row[1:]] for row in rows[1:]])
    validate_data(tasks, models, values)
    return tasks, models, values


def read_metadata_csv(path, task_names):
    """Join task/group/detail metadata by name; never silently reorder task data."""
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.reader(stream))
    if len(rows) < 2 or len(rows[0]) != 3 or any(len(row) != 3 for row in rows):
        raise ValueError('Metadata CSV requires three columns: task, major group, short detail.')
    by_task = {}
    for task, group, detail in rows[1:]:
        task = task.strip()
        if task in by_task:
            raise ValueError(f'Duplicate metadata task: {task}')
        by_task[task] = (group.strip(), detail.strip())
    if set(by_task) != set(task_names):
        raise ValueError('Metadata tasks must match the data tasks exactly.')
    return [by_task[task][0] for task in task_names], [by_task[task][1] for task in task_names]


def demo_data():
    """Values transcribed from the reference image; not independently verified."""
    return dict(
        task_names=['Visual Prompt', 'Grounding', 'Dense', 'Referring', 'Robo Point',
                    'Referring Point', 'Grounding Point', 'Dense Point', 'GUI', 'OCR', 'Layout'],
        model_names=['GroundingPI', 'Top 1 baseline', 'Top 2 baseline', 'Top 3 baseline', 'Top 4 baseline'],
        values=np.array([[73.59, 65.84, 56.52, 54.85, 43.26], [59.50, 58.86, 58.03, 56.80, 56.59],
                         [57.48, 55.24, 51.17, 51.08, 40.98], [84.89, 82.52, 79.02, 78.56, 78.31],
                         [75.12, 81.08, 66.61, 65.39, 63.33], [89.71, 85.51, 84.56, 82.29, 79.96],
                         [82.15, 79.66, 74.89, 70.94, 70.83], [74.37, 76.10, 70.54, 70.26, 67.69],
                         [78.92, 92.58, 77.73, 72.24, 70.09], [54.79, 48.89, 47.34, 45.20, 43.30],
                         [79.95, 74.27, 71.64, 69.06, 61.50]]),
        major_groups=['Bounding Boxes'] * 4 + ['Point'] * 5 + ['Text & Bounding Boxes'] * 2,
        task_details=['FSC147-test, Dense200, COCO, LVIS', 'COCO, LVIS', 'Dense200, VisDrone',
                      'HumanRef, RefCOCOg*5', 'RoboSpatial, RefSpatial*3', 'HumanRef, RefCOCOg*5',
                      'COCO, LVIS', 'Dense200, VisDrone', 'Screenspot-Pro, ScreenSpot-V2, OSWorld-G',
                      'HierText, ICDAR2015, TotalText, SROIE', 'DocLayNet, M6Doc'],
        center_label='GroundingPI',
        baseline_label='Best Four models\nAcross 45 Baselines\nIncluding GPT-6 Astra')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, help='Wide CSV: task followed by model columns')
    parser.add_argument('--metadata', type=Path, help='CSV columns: task, major group, short detail')
    parser.add_argument('--output', type=Path, default=Path('figures/fig_grouped_radial_bar'))
    parser.add_argument('--center-label', default=None)
    parser.add_argument('--highlight-index', type=int, default=0)
    parser.add_argument('--format', default='.2f')
    parser.add_argument('--suffix', default='')
    parser.add_argument('--scale-max', type=float)
    parser.add_argument('--scale-mode', choices=['within_task', 'shared'], default='within_task')
    parser.add_argument('--baseline-label', default=None)
    parser.add_argument('--hide-values', action='store_true')
    parser.add_argument('--hide-legend', action='store_true')
    args = parser.parse_args()
    if args.metadata and not args.data:
        parser.error('--metadata requires --data')
    if args.data:
        tasks, models, values = read_wide_csv(args.data)
        data = dict(task_names=tasks, model_names=models, values=values)
        if args.metadata:
            data['major_groups'], data['task_details'] = read_metadata_csv(args.metadata, tasks)
    else:
        data = demo_data()
    if args.center_label is not None:
        data['center_label'] = args.center_label
    if args.baseline_label is not None:
        data['baseline_label'] = args.baseline_label
    fig = plot_chart(**data, highlight_index=args.highlight_index, value_format=args.format,
                     value_suffix=args.suffix, scale_max=args.scale_max, scale_mode=args.scale_mode,
                     show_values=not args.hide_values, show_legend=not args.hide_legend)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for extension in ('png', 'pdf', 'svg'):
        fig.savefig(args.output.with_suffix('.' + extension), dpi=200, facecolor=fig.get_facecolor(),
                    bbox_inches=None, pad_inches=0)
    plt.close(fig)
    print('Saved PNG, PDF and SVG:', args.output)


if __name__ == '__main__':
    main()
```
