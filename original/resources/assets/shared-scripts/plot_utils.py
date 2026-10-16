#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""学术级图表工具库 — 统一风格，绘图助手 自由调用。

使用方式：
    from _utils.plot_utils import setup_style, heatmap, forest_plot, trend_plot
    setup_style()  # 初始化学术风格
    heatmap(corr_matrix, output='figures/fig_heatmap.pdf')
"""
import os
import sys
import platform
import numpy as np
try:
    from . import vivid_config as vc
    from .figure_language import font_candidates, apply_figure_fonts, localize_figure, translate_text
except ImportError:
    import vivid_config as vc
    from figure_language import font_candidates, apply_figure_fonts, localize_figure, translate_text

# 延迟导入 matplotlib，避免在没有 GUI 的环境报错
_plt = None
_sns = None

def _get_plt():
    global _plt
    if _plt is None:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        _plt = plt
    return _plt

def _get_sns():
    global _sns
    if _sns is None:
        try:
            import seaborn as sns
            _sns = sns
        except ImportError:
            _sns = None
    return _sns


# ============================================================
# 学术配色方案
# ============================================================
# All user palette definitions are maintained in palettes.json.
_registry = vc.registry()
PALETTES = {k: vc.categorical_colors({'palette': k}) for k in _registry['palettes']}
PALETTE = vc.categorical_colors()
PALETTE_LIGHT = None  # 延迟初始化，在 _lighten 定义后赋值

COLORS = {
    'primary': PALETTE[0] if len(PALETTE)>0 else PALETTE[0],
    'secondary': PALETTE[1] if len(PALETTE)>1 else PALETTE[0],
    'accent': PALETTE[2] if len(PALETTE)>2 else PALETTE[0],
    'gray': '#B8B8B8',
    'light': '#F5F7FA',
    'dark': '#2D2D2D',
    # 语义颜色
    'up': PALETTE[2] if len(PALETTE)>2 else PALETTE[0],
    'down': PALETTE[1] if len(PALETTE)>1 else PALETTE[0],
    'neutral': '#B8B8B8',     # 中性
    'highlight': PALETTE[4] if len(PALETTE)>4 else PALETTE[0],
    'ref_line': '#AAAAAA',    # 参考线
    'grid': '#E0E0E0',        # 网格线（很淡）
    'text': '#4A4A4A',        # 标注文字
    'bg_box': '#F5F7FA',      # 标注框背景
    'bg_fill': None,
    'bg_fill2': None,
}


def _read_palette_marker():
    return vc.load_config()['palette']


def _read_custom_colors():
    return vc.palette_colors()


def _read_style_marker():
    style = vc.load_config()['style']
    if style not in STYLE_FAMILIES:
        raise ValueError(f'Unknown Vivid layout: {style}')
    return style


# 「高级自定义版式」约束档位 —— 每个维度只给几个安全值(取自 STYLE_FAMILIES 验证过的值域),
# 用户任意组合都不会配出丑图。前端/后端/本文件三处的档位键必须一致。
_STYLE_CUSTOM_DIMS = {
    'frame': ('open', 'journal'),          # 边框:极简左下 / 期刊四面
    'grid': ('none', 'y', 'both'),         # 网格:无 / 横向淡 / 全网格淡
    'lw': ('thin', 'mid', 'thick'),        # 线宽:细 / 中 / 粗
    'font': ('small', 'medium', 'large'),  # 字号:小 / 中 / 大(全局 rcParams,必生效)
    'legend': ('noframe', 'framed'),       # 图例:无框 / 有框
    'bg': ('white', 'graytint'),           # 背景:纯白 / 淡灰底
}


def _read_style_custom_marker():
    spec = vc.load_config().get('style_custom')
    if spec is None:
        return None
    if not isinstance(spec, dict):
        raise ValueError('style_custom must be an object')
    for key, value in spec.items():
        if key not in _STYLE_CUSTOM_DIMS or value not in _STYLE_CUSTOM_DIMS[key]:
            raise ValueError(f'Invalid layout setting: {key}={value}')
    return {key: spec.get(key, allowed[0]) for key, allowed in _STYLE_CUSTOM_DIMS.items()}


# ============================================================
# 「成品风格族」—— 每套是一组经审美验证、彼此自洽的完整版式参数。
# 项目配置选择一套完整参数，也可按用户要求使用自定义版式。
# 关键：每套都【显式控制刻度四面】，tick_tr=False 时关掉上/右刻度 = 消灭“上右黑点点”。
# ============================================================
STYLE_FAMILIES = {
    'clean_open':     {'spines': ('left', 'bottom'), 'tick_dir': 'out', 'tick_tr': False,
                       'grid': None, 'legend_frame': False, 'patch_edge': 'white',
                       'lw': 1.8, 'ms': 5, 'axis_color': '#666666'},
    'soft_grid':      {'spines': ('left', 'bottom'), 'tick_dir': 'out', 'tick_tr': False,
                       'grid': {'axis': 'y', 'ls': '--', 'alpha': 0.30, 'color': '#CCCCCC'},
                       'legend_frame': False, 'patch_edge': 'white', 'lw': 1.9, 'ms': 5, 'axis_color': '#666666'},
    'framed_journal': {'spines': ('left', 'bottom', 'top', 'right'), 'tick_dir': 'in', 'tick_tr': True,
                       'grid': {'axis': 'both', 'ls': '-', 'alpha': 0.15, 'color': '#DDDDDD'},
                       'legend_frame': True, 'patch_edge': 'white', 'lw': 1.7, 'ms': 4.5, 'axis_color': '#444444'},
    'minimal_bare':   {'spines': ('left', 'bottom'), 'tick_dir': 'out', 'tick_tr': False,
                       'grid': None, 'legend_frame': False, 'patch_edge': 'none',
                       'lw': 2.0, 'ms': 6, 'axis_color': '#888888'},
    'bold_edge':      {'spines': ('left', 'bottom'), 'tick_dir': 'out', 'tick_tr': False,
                       'grid': None, 'legend_frame': False, 'patch_edge': 'white_bold',
                       'lw': 2.1, 'ms': 6, 'axis_color': '#555555'},
    'crisp_dark':     {'spines': ('left', 'bottom', 'top', 'right'), 'tick_dir': 'in', 'tick_tr': True,
                       'grid': None, 'legend_frame': True, 'patch_edge': 'white',
                       'lw': 1.8, 'ms': 5, 'axis_color': '#333333'},
}
_STYLE_FAMILY_NAMES = list(STYLE_FAMILIES.keys())




def _knobs_from_custom(spec):
    """把「高级自定义」档位 {frame,grid,lw} 映射成完整 knobs（唯一真相源:
    预生成预览图 与 实际出图 都调本函数，杜绝"预览≠实际"）。
    所有取值来自 STYLE_FAMILIES 验证过的值域，任意组合都自洽好看。
    未开放的维度（描边等）用安全固定值。"""
    _frame = {
        'open':    {'spines': ('left', 'bottom'),               'tick_dir': 'out', 'tick_tr': False,
                    'legend_frame': False, 'axis_color': '#666666'},
        'journal': {'spines': ('left', 'bottom', 'top', 'right'), 'tick_dir': 'in',  'tick_tr': True,
                    'legend_frame': True,  'axis_color': '#444444'},
    }
    _grid = {
        'none': None,
        'y':    {'axis': 'y',    'ls': '--', 'alpha': 0.30, 'color': '#CCCCCC'},
        'both': {'axis': 'both', 'ls': '-',  'alpha': 0.15, 'color': '#DDDDDD'},
    }
    _lw = {'thin': (1.7, 4.5), 'mid': (1.9, 5.0), 'thick': (2.1, 6.0)}
    # 字号:(基准 font.size, label, title, tick) —— 全局 rcParams,必生效
    _font = {'small': (9, 10, 11, 8), 'medium': (11, 12, 13, 10), 'large': (13, 14, 16, 12)}
    _bg = {'white': 'white', 'graytint': '#F7F8FA'}
    # 缺失/非法档位回落到第一档（与 _read_style_custom_marker 的补默认一致）
    f = _frame.get(spec.get('frame'), _frame['open'])
    g = _grid.get(spec.get('grid', 'none'), None) if spec.get('grid') != 'none' else None
    lw, ms = _lw.get(spec.get('lw'), _lw['mid'])
    fs = _font.get(spec.get('font'), _font['medium'])
    facecolor = _bg.get(spec.get('bg'), 'white')
    # legend 维显式选了就覆盖 frame 带的默认；没选则跟随 frame
    _leg = spec.get('legend')
    legend_frame = (_leg == 'framed') if _leg in ('framed', 'noframe') else f['legend_frame']
    return {
        'spines': f['spines'], 'tick_dir': f['tick_dir'], 'tick_tr': f['tick_tr'],
        'legend_frame': legend_frame, 'axis_color': f['axis_color'],
        'grid': g, 'patch_edge': 'white', 'lw': lw, 'ms': ms,
        'font_size': fs, 'facecolor': facecolor,   # ★ 新维(setup_style 用 .get 消费,预设路径无此键不受影响)
        '_name': f"custom({spec.get('frame','open')}/{spec.get('grid','none')}/{spec.get('lw','mid')}"
                 f"/{spec.get('font','medium')}/{spec.get('legend','-')}/{spec.get('bg','white')})",
    }


def setup_style(palette='auto', language=None, font_family=None):
    """Load project palette and layout; explicit palette arguments remain supported."""
    plt = _get_plt()
    import matplotlib
    language = vc.normalize_language(vc.load_config()['language'] if language is None else language)
    # Read family before seaborn resets rcParams; preserve a source's serif choice.
    family = font_family if font_family is not None else list(matplotlib.rcParams['font.family'])
    sns = _get_sns()
    _project_mode = palette == 'auto' or palette is None
    _custom_spec = _read_style_custom_marker() if _project_mode else None
    _knobs = (_knobs_from_custom(_custom_spec) if _custom_spec else
              dict(STYLE_FAMILIES[_read_style_marker()])) if _project_mode else None
    if isinstance(palette, list):
        colors = palette
    elif _project_mode:
        colors = vc.categorical_colors()
    elif palette in PALETTES:
        colors = list(PALETTES[palette])
    else:
        raise ValueError(f'Unknown palette: {palette}')

    # 更新全局 PALETTE 供其他函数使用
    global PALETTE, PALETTE_LIGHT, COLORS
    PALETTE[:] = colors
    PALETTE_LIGHT[:] = [_lighten(c, 0.4) for c in colors]
    COLORS['primary'] = colors[0]
    COLORS['secondary'] = colors[1] if len(colors) > 1 else colors[0]
    COLORS['accent'] = colors[2] if len(colors) > 2 else colors[0]
    # 语义颜色跟随配色方案
    COLORS['up'] = colors[2] if len(colors) > 2 else colors[0]       # 上升 = accent 色
    COLORS['down'] = colors[1] if len(colors) > 1 else colors[0]     # 下降 = secondary 色
    COLORS['highlight'] = colors[4] if len(colors) > 4 else colors[0]  # 高亮
    COLORS['bg_fill'] = _lighten(colors[0], 0.8)
    COLORS['bg_fill2'] = _lighten(colors[1] if len(colors)>1 else colors[0], 0.8)

    # 保持既有导出边界设置。
    matplotlib.rcParams['savefig.bbox'] = 'standard'
    matplotlib.rcParams['savefig.pad_inches'] = 0.1

    # 用 seaborn 主题（如果可用）
    if sns:
        sns.set_theme(style='ticks', font_scale=1.0, rc={
            'axes.edgecolor': '#333333',
            'axes.linewidth': 0.8,
        })
    if sns:
        sns.set_palette(colors)

    # One shared font policy for initialization and final export. Local fonts
    # are registered on demand; no platform-specific installation is attempted.
    selected_fonts = font_candidates(language, family)
    sans_fonts = font_candidates(language, 'sans-serif')
    serif_fonts = font_candidates(language, 'serif')

    matplotlib.rcParams.update({
        'font.size': 11,
        'font.family': selected_fonts,
        'font.sans-serif': sans_fonts,
        'font.serif': serif_fonts,
        'font.monospace': font_candidates(language, 'monospace'),
        'axes.unicode_minus': False,
        'axes.labelsize': 12,
        'axes.titlesize': 13,
        'axes.linewidth': 0.8,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'legend.frameon': False,
        'figure.dpi': 300,
        'savefig.dpi': 350,
        'pdf.fonttype': 42,  # Embed TrueType text with Unicode mappings.
        'ps.fonttype': 42,
        'savefig.bbox': 'standard',       # ★ 不用 'tight' — 否则 axes 外文字会撑爆 mediabox
        'savefig.pad_inches': 0.1,        # ★ 配合 standard，留窄边距
        'axes.grid': False,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.facecolor': 'white',
        'figure.facecolor': 'white',
        'text.usetex': False,
        'mathtext.fontset': 'stix',
        'lines.linewidth': 1.8,
        'lines.markersize': 6,
        'patch.edgecolor': 'white',       # 饼图/柱状图块之间白色分隔线
        'patch.linewidth': 1.0,
    })

    # 设置颜色循环 — 这是关键，防止 matplotlib 用默认丑蓝色
    matplotlib.rcParams['axes.prop_cycle'] = matplotlib.cycler(color=colors)

    # ★ 随机模式：按【成品风格族】整套应用版式（自洽、好看；显式控制刻度四面 = 消灭上右黑点）
    if _project_mode and _knobs:
        _f = _knobs
        _ac = _f['axis_color']
        _sp = _f['spines']
        _pe = _f['patch_edge']
        _grid = _f['grid']
        matplotlib.rcParams.update({
            'legend.frameon': bool(_f['legend_frame']),
            'lines.linewidth': _f['lw'],
            'lines.markersize': _f['ms'],
            # 边框：只显示 spines 里列出的面
            'axes.spines.left': ('left' in _sp),
            'axes.spines.bottom': ('bottom' in _sp),
            'axes.spines.top': ('top' in _sp),
            'axes.spines.right': ('right' in _sp),
            'axes.edgecolor': _ac,
            # 刻度：方向 + 是否上/右也画刻度（False=关掉上右刻度=去黑点）+ 颜色 + 长度
            'xtick.direction': _f['tick_dir'], 'ytick.direction': _f['tick_dir'],
            'xtick.top': _f['tick_tr'], 'ytick.right': _f['tick_tr'],
            'xtick.color': _ac, 'ytick.color': _ac,
            'xtick.major.size': 3.5 if _f['tick_dir'] == 'out' else 3,
            'ytick.major.size': 3.5 if _f['tick_dir'] == 'out' else 3,
            # 全局网格：仅 grid.axis=='both' 时全开；'y' 交给制图时按需（gax）。这里设默认样式
            'axes.grid': bool(_grid and _grid.get('axis') == 'both'),
            'grid.linestyle': (_grid or {}).get('ls', '--'),
            'grid.alpha': (_grid or {}).get('alpha', 0.3),
            'grid.color': (_grid or {}).get('color', '#DDDDDD'),
            # 描边：白/加粗白/无
            'patch.edgecolor': {'white': 'white', 'white_bold': 'white', 'none': 'none'}.get(_pe, 'white'),
            'patch.linewidth': {'white': 1.0, 'white_bold': 1.5, 'none': 0.0}.get(_pe, 1.0),
        })
        # ★ 高级自定义新维（字号/背景）——仅 custom 路径的 knobs 有这两键，用 .get 兜底，
        #   预设路径无此键时不覆盖上面设过的默认值（font.size=11 / facecolor=white）。
        _fsz = _f.get('font_size')
        if _fsz:
            _base, _lbl, _ttl, _tk = _fsz
            matplotlib.rcParams.update({
                'font.size': _base, 'axes.labelsize': _lbl, 'axes.titlesize': _ttl,
                'xtick.labelsize': _tk, 'ytick.labelsize': _tk, 'legend.fontsize': _tk,
            })
        _fc = _f.get('facecolor')
        if _fc:
            matplotlib.rcParams['axes.facecolor'] = _fc

    # ★ Hook plt.savefig — 即使不用 save_fig()，也能自动防遮挡
    # Preserve author layout: do not install automatic savefig mutation hooks.


def _hook_savefig(plt):
    """Hook plt.savefig 和 Figure.savefig，在保存前强制修复子图尺寸和文字重叠。"""
    import matplotlib.figure

    if getattr(matplotlib.figure.Figure, '_overlap_hooked', False):
        return  # 已经 hook 过了

    _original_savefig = matplotlib.figure.Figure.savefig

    def _hooked_savefig(self, *args, **kwargs):
        # ★ 强制修复子图尺寸（最高优先级，检测到问题必须修复）
        try:
            _guard_subplot_size(self)
        except Exception:
            pass
        # 防遮挡修复
        try:
            _auto_fix_overlaps(self)
        except Exception:
            pass
        # ★ 防遮挡可能又破坏了布局，再强制检查一次
        try:
            _guard_subplot_size(self)
        except Exception:
            pass
        # ★ 最后一步：确保旋转的刻度标签（斜排长中文）不被画布边缘裁掉
        try:
            _ensure_ticklabels_visible(self)
        except Exception:
            pass
        return _original_savefig(self, *args, **kwargs)

    matplotlib.figure.Figure.savefig = _hooked_savefig
    matplotlib.figure.Figure._overlap_hooked = True


def _has_3d_axes(fig):
    """检测 figure 是否含 3D 轴（Axes3D）。

    含 3D 轴时，所有针对 2D 子图的布局兜底（subplots_adjust / tight_layout /
    set_position 重排）都必须跳过：3D 曲面 + 窄 colorbar 的组合会命中"子图过窄"
    误判，被强行 tight_layout/subplots_adjust 挤塌成一条 colorbar（实测 3D 概率
    曲面图只剩右侧一根竖条）。matplotlib 官方亦声明 tight_layout 不支持 3D 轴。
    """
    try:
        for ax in fig.get_axes():
            if getattr(ax, 'name', '') == '3d' or hasattr(ax, 'get_zlim'):
                return True
    except Exception:
        pass
    return False


def _lighten(hex_color, amount=0.4):
    """将颜色变浅（用于填充区域）。amount=0 不变，amount=1 变白。"""
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r = int(r + (255 - r) * amount)
    g = int(g + (255 - g) * amount)
    b = int(b + (255 - b) * amount)
    return f'#{r:02x}{g:02x}{b:02x}'


# 初始化 PALETTE_LIGHT（必须在 _lighten 定义之后）
PALETTE_LIGHT = [_lighten(c, 0.4) for c in PALETTE]
COLORS["bg_fill"] = _lighten(PALETTE[0], 0.8)
COLORS["bg_fill2"] = _lighten(PALETTE[1], 0.8)


def _pull_back_outside_transaxes_text(fig):
    """无条件检测：ax.text(transAxes, y<0 or y>1) 这种 axes 外子图标题，
    转换成 fig.text(figure coords) 钉在画布底部/顶部，且改写到 figure 坐标系。
    
    理由：science 样式默认 savefig.bbox='tight' 会把 axes 外文字算进 PDF mediabox，
    导致页面被异常拉长。即便我们已经全局关掉 savefig.bbox='tight'，AI 代码仍可能
    显式传 bbox_inches='tight'。把这种文本拉到 axes 内或转 figure 坐标都能解决。
    """
    try:
        axes = [ax for ax in fig.get_axes() if ax.get_visible()]
        for ax in axes:
            ax_pos = ax.get_position()
            for t in list(ax.texts):
                try:
                    if t.get_transform() is not ax.transAxes:
                        continue
                    x, y = t.get_position()
                    if y > 1.0:
                        # 拉回 axes 内顶端
                        t.set_position((x, 0.97))
                        t.set_va('top')
                    elif y < 0.0:
                        # 拉回 axes 内底端
                        t.set_position((x, 0.03))
                        t.set_va('bottom')
                except Exception:
                    pass
    except Exception:
        pass


def _auto_shrink_figsize_if_sparse(fig):
    """检测所有 axes 占 figure 总面积比例，过低时强制重排 + 收缩 figsize。
    
    场景：AI 写了 figsize=(10, 12) 但实际只画 2 个小 panel 在底部/顶部，
    剩下大块白边 → 用户看到的就是"图很小，整页白"。
    
    三阶段策略：
    1. subplots_adjust（对 plt.subplots / add_subplot 创建的 axes 有效）
    2. ★ 直接 set_position 强制重排（对 add_axes / GridSpec 手动布局也有效）
       — 按原始相对位置等比例缩放到撑满 figure 80%
       — 同时把 ax.text(transAxes, y>1.0) 反模式拉回 axes 内部
    3. 仍稀疏 → 收缩 figsize
    
    副作用：触发任一阶段修复时，在 fig 上设 `_layout_fixed_by_plot_utils=True`，
    让 _save 用 bbox_inches=None 防止 transAxes 高位标注异常扩展 PDF mediabox。
    """
    try:
        # ★ 3D 轴豁免：等比例重排/收缩 figsize 会破坏 3D 曲面 + colorbar 布局
        if _has_3d_axes(fig):
            return

        axes = [ax for ax in fig.get_axes()
                if ax.get_visible() and not ax.get_label().startswith('_')]
        if not axes:
            return

        fig_w, fig_h = fig.get_size_inches()
        if fig_w <= 0 or fig_h <= 0:
            return

        def _compute_union():
            x0_min, y0_min, x1_max, y1_max = 1.0, 1.0, 0.0, 0.0
            for ax in axes:
                pos = ax.get_position()
                x0_min = min(x0_min, pos.x0)
                y0_min = min(y0_min, pos.y0)
                x1_max = max(x1_max, pos.x1)
                y1_max = max(y1_max, pos.y1)
            return x0_min, y0_min, x1_max, y1_max

        x0_min, y0_min, x1_max, y1_max = _compute_union()
        if x1_max <= x0_min or y1_max <= y0_min:
            return

        union_w = x1_max - x0_min
        union_h = y1_max - y0_min
        content_ratio = union_w * union_h

        if content_ratio >= 0.50:
            return  # 占比够，不调

        # ★ 阶段 1：先试 subplots_adjust（对 plt.subplots 创建的 axes 有效）
        try:
            fig.subplots_adjust(left=0.10, right=0.96, top=0.93, bottom=0.10,
                                hspace=0.3, wspace=0.3)
            x0_min, y0_min, x1_max, y1_max = _compute_union()
            new_ratio = (x1_max - x0_min) * (y1_max - y0_min)
            if new_ratio >= 0.50:
                fig._layout_fixed_by_plot_utils = True
                return  # 搞定
        except Exception:
            pass

        # ★ 阶段 2：subplots_adjust 失效（add_axes / GridSpec 手动布局），
        #         直接 set_position 强制重排：按原始相对位置等比例缩放撑满
        # 这是修复 "axes 集中在 figure 一侧（如底部 20%），子图标题被推到顶部" 的关键
        try:
            # 重新读 union（subplots_adjust 可能已变化）
            x0_min, y0_min, x1_max, y1_max = _compute_union()
            union_w = x1_max - x0_min
            union_h = y1_max - y0_min

            # 目标：让 union 撑满 figure 的 (0.08-0.94) × (0.10-0.93) 区域
            target_x0, target_y0 = 0.10, 0.10
            target_w, target_h = 0.85, 0.82

            # 缩放比例（保持各 axes 相对位置）
            scale_w = target_w / union_w if union_w > 0.001 else 1.0
            scale_h = target_h / union_h if union_h > 0.001 else 1.0
            # 不要过度放大（>6x 容易让 add_axes 手动布局变形）
            scale_w = min(scale_w, 6.0)
            scale_h = min(scale_h, 6.0)

            for ax in axes:
                pos = ax.get_position()
                # 相对 union 的偏移
                rel_x = (pos.x0 - x0_min) / max(union_w, 0.001)
                rel_y = (pos.y0 - y0_min) / max(union_h, 0.001)
                # 新位置：把整个 union 投影到 target 区域
                new_x0 = target_x0 + rel_x * target_w
                new_y0 = target_y0 + rel_y * target_h
                new_w = pos.width * scale_w
                new_h = pos.height * scale_h
                # 边界保护
                new_x0 = max(0.02, min(new_x0, 0.95))
                new_y0 = max(0.02, min(new_y0, 0.95))
                new_w = max(0.05, min(new_w, 1.0 - new_x0 - 0.02))
                new_h = max(0.05, min(new_h, 1.0 - new_y0 - 0.02))
                ax.set_position([new_x0, new_y0, new_w, new_h])

            # ★ 把 ax.text(transAxes, y>1.0) 反模式拉回 axes 内部
            # 这种 "axes 外标注" 会被 bbox_inches='tight' 算进 PDF mediabox，
            # 导致页面被异常拉长（"标题在顶部、图在底部、中间一大片白"的根因）
            for ax in axes:
                for t in list(ax.texts):
                    try:
                        if t.get_transform() is ax.transAxes:
                            x, y = t.get_position()
                            if y > 1.0:
                                t.set_position((x, 0.95))
                                t.set_va('top')
                            elif y < 0.0:
                                t.set_position((x, 0.05))
                                t.set_va('bottom')
                    except Exception:
                        pass

            x0_min, y0_min, x1_max, y1_max = _compute_union()
            new_ratio = (x1_max - x0_min) * (y1_max - y0_min)
            if new_ratio >= 0.50:
                fig._layout_fixed_by_plot_utils = True
                return
        except Exception:
            pass

        # ★ 阶段 3：仍稀疏 → 收缩 figsize
        new_w_inches = max(3.5, (x1_max - x0_min) * fig_w * 1.18)
        new_h_inches = max(2.5, (y1_max - y0_min) * fig_h * 1.18)
        new_w_inches = min(new_w_inches, fig_w)
        new_h_inches = min(new_h_inches, fig_h)
        if new_w_inches > fig_w * 0.95 and new_h_inches > fig_h * 0.95:
            return
        fig.set_size_inches(new_w_inches, new_h_inches)
        fig._layout_fixed_by_plot_utils = True
    except Exception:
        # 任何异常都静默跳过，不能让兜底逻辑搞坏正常保图
        pass


def _warn_if_wasted_margin(fig, output):
    """成品自检：保存前实测左边距，明显富余就打提示（不阻塞出图）。

    为什么需要：其他 9 道闸都是静态扫源码，而"左边距被撑爆"取决于 renderer 运行时
    实测，静态扫不出来 —— 历史上这个病就是这样潜伏下来的（对数轴幽灵刻度被当成
    越界，左边距一路顶到封顶 0.40，图上 40% 是白的）。

    判据不能拿"左距 > X%"一刀切：横向条形图配长中文 y 标签（特征重要性、方法对比）
    真的需要 25%+ 的左边距，那是合理的。所以拿【实测 y 标签宽度】当基准，
    只有左边距远超标签实际所需时才提示。
    """
    if _has_3d_axes(fig):
        return  # 3D 轴刻度在投影平面上，边距语义不同
    try:
        axes = [ax for ax in fig.get_axes()
                if ax.get_visible() and not ax.get_label().startswith('_')]
        if not axes:
            return
        fig_w_px = fig.get_size_inches()[0] * fig.dpi
        if fig_w_px <= 0:
            return
        left_px = min(ax.get_position().x0 for ax in axes) * fig_w_px
        if left_px <= 0:
            return
        renderer = fig.canvas.get_renderer()
        # y 刻度标签 + y 轴标题 实际占用的宽度
        need_px = 0.0
        for ax in axes:
            for t in _onscreen_tick_labels(ax, which='y'):
                if t.get_visible() and t.get_text().strip():
                    need_px = max(need_px, t.get_window_extent(renderer=renderer).width)
            lbl = ax.yaxis.label
            if lbl is not None and lbl.get_text().strip():
                need_px += lbl.get_window_extent(renderer=renderer).height
        need_px += 0.02 * fig_w_px  # 刻度线 + 呼吸余量
        # 只在"绝对富余够大"且"相对富余明显"时提示，避免误报刷屏
        if left_px - need_px > 0.06 * fig_w_px and left_px > need_px * 1.6:
            print(f"[plot_utils] WARNING {os.path.basename(str(output))} 左边距偏大: "
                  f"实测 {left_px / fig_w_px * 100:.1f}% 图宽，y 标签实际只需 "
                  f"{need_px / fig_w_px * 100:.1f}% —— 疑似空白浪费，检查坐标轴范围与刻度")
    except Exception:
        pass  # 自检永不影响出图


def _warn_if_data_clipped(fig, output):
    """成品自检：大量数据点落在轴范围外 → 几乎总是 xlim/ylim/zlim 写错。

    为什么必须运行时实测：静态扫源码看不出 `set_xlim(0, L)` 到底对不对 —— 那取决于
    数据坐标系的约定。实测起因是把主胞「边长 L=10000」当成了坐标上界，而数据其实以
    原点为中心（[-L/2, +L/2]），于是负坐标那一半（实测 46%~79% 的点）被静默裁到轴外，
    图上只剩挤在角落的一小撮，matplotlib 不报错、任何静态闸也扫不出来。

    阈值取 20%：合法的「裁掉几个离群点」通常远低于 5%，而坐标系写错必然接近 50%。
    """
    try:
        msgs = []
        for ax in fig.get_axes():
            if not ax.get_visible():
                continue
            is3d = getattr(ax, 'name', '') == '3d' or hasattr(ax, 'get_zlim')
            P = _data_points_in_data_space(ax, is3d)
            if P is None or P.shape[0] < 4:
                continue
            # 大数据集抽样：判「是否 >20% 的点落在轴外」不需要全量 —— 5 万样本的统计
            # 误差 <0.4%，而 90 万点全量实测要 1.74s，白加在每次 save_fig 上。
            # 固定 seed 保证同一张图重复跑结论一致（不引入随机抖动）。
            if P.shape[0] > 50000:
                P = P[np.random.default_rng(0).choice(P.shape[0], 50000, replace=False)]
            axinfo = [(ax.get_xlim(), ax.get_xscale()), (ax.get_ylim(), ax.get_yscale())]
            if is3d:
                axinfo.append((ax.get_zlim(),
                               getattr(ax, 'get_zscale', lambda: 'linear')()))
            for k, ((lo, hi), scale) in enumerate(axinfo):
                if k >= P.shape[1]:
                    break
                v = P[:, k]
                v = v[np.isfinite(v)]
                if scale == 'log':
                    v = v[v > 0]      # log 轴上非正值 matplotlib 本就不画，不算被裁
                if v.size < 4:
                    continue
                lo, hi = min(lo, hi), max(lo, hi)
                n_out = int(((v < lo) | (v > hi)).sum())
                if n_out / v.size > 0.20:
                    msgs.append(
                        f"{'xyz'[k]} 轴: {n_out}/{v.size} ({n_out / v.size:.0%}) 个点落在 "
                        f"[{lo:.4g}, {hi:.4g}] 之外，数据实际范围 [{v.min():.4g}, {v.max():.4g}]")
        if msgs:
            print(f"[plot_utils] ⛔ {os.path.basename(str(output))} 有数据被坐标轴裁掉：")
            for m in msgs[:6]:
                print(f"    {m}")
            print("    这几乎总是 set_xlim/set_ylim/set_zlim 写错。最常见的坑：把「边长/总长 L」")
            print("    当成坐标上界写了 (0, L)，而数据坐标系以原点为中心，应为 (-L/2, +L/2)。")
            print("    先打印数据真实 min/max 再定轴范围；别用 figsize / view_init 掩盖 ——")
            print("    被裁的点是真的没画出来。（若确为有意放大局部 inset，可忽略本条）")
    except Exception:
        pass  # 自检永不影响出图


def _flatten_segments(segs):
    """把 LineCollection / Line3DCollection 的 segments 展平成 (N, 2|3)。

    段等长（绝大多数情况，每段 2 点）时 np.asarray 能直接生成 3 维数组，
    实测 20 万段 39ms；退回 Python 列表推导要 133ms。段长不齐时 asarray 抛
    ValueError（numpy 不再允许 ragged），故用 except 兜住走慢路径。
    """
    try:
        a = np.asarray(segs, dtype=float)
        if a.ndim == 3:
            return a.reshape(-1, a.shape[-1])
    except Exception:
        pass
    return np.asarray([p for seg in segs for p in seg], dtype=float)


def _data_points_in_data_space(ax, is3d):
    """收集该 axes 上确实处于「数据坐标系」的点，返回 (N,2) / (N,3) 或 None。

    精确区分 transform 是本函数的全部难点，判据都是实测出来的：
      · Line2D      → get_transform() is ax.transData（axhline/axvline 是 blended，自动排除）
      · scatter     → offsets 走 get_offset_transform()，**不是** get_transform()
                      （实测 2D scatter 的 get_transform() 返回 IdentityTransform，
                        照搬 Line2D 的判据会把所有散点图漏掉）
      · LineCollection/vlines → get_segments() + get_transform() is ax.transData
      · 3D          → get_segments() 在投影前返回空，必须用私有 _segments3d / _offsets3d；
                      3D 的 transData 是投影后的，故 3D 分支不做 transform 判据
    故意跳过 fill_between(PolyCollection) 与 plot_surface(Poly3DCollection)：
    它们的顶点常含 baseline / 示意平面，位置由代码指定而非数据，算进去会误报。
    """
    pts = []
    for l in getattr(ax, 'lines', []):
        try:
            if is3d and hasattr(l, 'get_data_3d'):
                pts.append(np.asarray(l.get_data_3d(), dtype=float).T)
            elif not is3d and l.get_transform() is ax.transData:
                pts.append(np.asarray(l.get_xydata(), dtype=float))
        except Exception:
            pass
    for c in getattr(ax, 'collections', []):
        try:
            if is3d:
                s3 = getattr(c, '_segments3d', None)
                if s3 is not None and len(s3):
                    pts.append(_flatten_segments(s3))
                    continue
                o3 = getattr(c, '_offsets3d', None)
                if o3 is not None and len(o3) == 3:
                    pts.append(np.asarray(o3, dtype=float).T)
                continue
            hit = False
            if hasattr(c, 'get_offsets') and hasattr(c, 'get_offset_transform'):
                if c.get_offset_transform() is ax.transData:
                    o = np.asarray(c.get_offsets(), dtype=float)
                    if o.size:
                        pts.append(o)
                        hit = True
            if not hit and hasattr(c, 'get_segments') and c.get_transform() is ax.transData:
                sg = c.get_segments()
                if len(sg):
                    pts.append(_flatten_segments(sg))
        except Exception:
            pass
    try:
        pts = [p.reshape(-1, p.shape[-1]) for p in pts if getattr(p, 'size', 0)]
        want = 3 if is3d else 2
        pts = [p for p in pts if p.shape[-1] == want]
        return np.vstack(pts) if pts else None
    except Exception:
        return None


def _save(fig, output):
    """Save without changing author layout, labels, axes, or canvas size."""
    # ★ 空 / 仅空白 路径直接拒绝（避免兜底成隐藏文件 ".pdf"）
    if not output or not str(output).strip():
        raise ValueError("save_fig: output path is empty")
    output = str(output)  # 容 pathlib.Path
    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else '.', exist_ok=True)
    # ★ 扩展名兜底：matplotlib.savefig 拿到未知 format（如 'fig_lollipop'）会 raise ValueError。
    # 历史配方里有大量 save_fig(fig, 'figures/fig_xxx') 不带扩展名的写法 —— 自动追加 .pdf（论文场景首选矢量格式）。
    _SUPPORTED_FMTS = ('pdf', 'png', 'svg', 'jpg', 'jpeg', 'eps', 'ps', 'tif', 'tiff', 'webp')
    _basename = os.path.basename(output)
    _maybe_ext = _basename.rsplit('.', 1)[-1].lower() if '.' in _basename else ''
    if _maybe_ext in _SUPPORTED_FMTS:
        _ext = _maybe_ext
    else:
        # 无扩展名 / 不是图像格式（如 'fig.v2'）→ 追加 .pdf
        _ext = 'pdf'
        output = output + '.pdf'
    _save_kwargs = {'format': _ext, 'pad_inches': 0.15}
    # ★ 默认不用 bbox_inches='tight' —— 防止 ax.text(transAxes, y<0 or y>1) 这种
    # axes 外标注让 tight 包围盒爆炸（用户实测过 1496×23966 px 超长条 PNG）。
    # Preserve the requested canvas size; layout is owned by the generator.
    _save_kwargs['bbox_inches'] = None
    if _ext in ('png', 'jpg', 'jpeg'):
        _save_kwargs['dpi'] = 350  # 防中文标签糊（与 docx_export PDF→PNG 兜底链路一致）
    apply_figure_fonts(fig, vc.load_config()['language'])
    # ★ 成品自检：静态闸扫不出的"边距被撑爆"，在这里实测拦一道（只提示，不阻塞）
    _warn_if_wasted_margin(fig, output)
    # ★ 成品自检：数据被轴范围裁掉（坐标系约定写错，静态扫不出来），同样实测拦一道
    _warn_if_data_clipped(fig, output)
    fig.savefig(output, **_save_kwargs)
    _get_plt().close(fig)
    print(f'Saved: {output}')


def _onscreen_tick_labels(ax, which='both'):
    """返回该 axes 上真正落在轴范围内的主刻度标签（Text 对象列表）。

    which: 'both' | 'x' | 'y'，只取对应轴的刻度。

    matplotlib 会为超出 xlim/ylim 的刻度保留 Text 对象——对数轴尤其常见：
    xlim=[10, 2700] 时 10^0（x=1）的刻度对象依然存在，只是不绘制。这种
    "幽灵刻度"的 window_extent 算出来远在画布左侧（实测可达 -457 px），
    若拿去做"标签被画布切掉"的判定，会误判成越界，进而把左边距一路加大
    到封顶值，图上就出现大片空白。

    过滤办法：在轴自身的变换空间里比较（log 轴即 log 空间），只保留位置落在
    [lo, hi] ±0.5% 跨度内的刻度。测不出来时保守保留，维持原有行为。
    """
    # ★ 3D 轴：刻度标签落在投影平面上，get_position() 不是数据坐标，与 xlim/ylim
    #   比对无意义（实测越界量会算出上千万像素的垃圾值）。调用方本就豁免 3D，
    #   这里再兜一层，防止将来别处误用。
    try:
        if getattr(ax, 'name', '') == '3d' or hasattr(ax, 'get_zlim'):
            return []
    except Exception:
        pass

    out = []
    pairs = ((ax.xaxis, True), (ax.yaxis, False))
    if which == 'x':
        pairs = pairs[:1]
    elif which == 'y':
        pairs = pairs[1:]
    for axis, is_x in pairs:
        try:
            labels = [t for t in axis.get_ticklabels() if t.get_text()]
        except Exception:
            continue
        if not labels:
            continue
        # 轴的 scale 变换（log/linear/symlog…），把范围判定统一到线性空间
        bounds = None
        try:
            tr = axis.get_transform()
            lo, hi = ax.get_xlim() if is_x else ax.get_ylim()
            a, b = (float(v) for v in np.asarray(tr.transform([lo, hi])).ravel()[:2])
            if b < a:
                a, b = b, a
            span = b - a
            if np.isfinite(a) and np.isfinite(b) and span > 0:
                tol = 0.005 * span
                bounds = (a - tol, b + tol)
        except Exception:
            bounds = None
        if bounds is None:
            out.extend(labels)  # 拿不到范围就不过滤，保持旧行为
            continue
        for t in labels:
            try:
                pos = t.get_position()
                loc = float(pos[0] if is_x else pos[1])
                v = float(np.asarray(tr.transform([loc])).ravel()[0])
                if not np.isfinite(v):
                    continue  # 非法位置（如 log 轴上的 ≤0）必然不显示
                if bounds[0] <= v <= bounds[1]:
                    out.append(t)
            except Exception:
                out.append(t)  # 测量失败时保守保留
    return out


def _ensure_ticklabels_visible(fig):
    """防护：旋转的 x/y 轴刻度标签（尤其斜排的长中文）常伸出 axes 下方/左侧，
    在 bbox_inches=None（等大裁剪，为防 PDF mediabox 爆炸而刻意采用）下被画布边缘切掉。

    做法：用 renderer 实测每个 axes 的刻度标签像素范围，若标签越过 figure 的
    下边缘/左边缘，就按超出量（换算成 figure 比例 + 安全余量）增大 subplots_adjust
    的 bottom/left，把标签留白让出来。对 add_axes/GridSpec 等无法 subplots_adjust
    的手动布局，退化为直接下压/右移 axes 的 position。

    只增不减，幂等安全；测量失败时静默跳过，绝不破坏原图。
    """
    # ★ 3D 轴豁免：3D 轴的刻度标签在投影平面上，subplots_adjust/set_position 会挤塌曲面
    if _has_3d_axes(fig):
        return
    try:
        renderer = fig.canvas.get_renderer()
    except Exception:
        try:
            fig.canvas.draw()
            renderer = fig.canvas.get_renderer()
        except Exception:
            return

    fig_w_px, fig_h_px = fig.get_size_inches() * fig.dpi
    if fig_w_px <= 0 or fig_h_px <= 0:
        return

    axes = [ax for ax in fig.get_axes()
            if ax.get_visible() and not ax.get_label().startswith('_')]
    if not axes:
        return

    # 统计所有 axes 的刻度标签超出 figure 下边缘/左边缘的最大像素量
    overflow_bottom_px = 0.0
    overflow_left_px = 0.0
    for ax in axes:
        # 只统计落在轴范围内的刻度：轴外的"幽灵刻度"（如 log 轴 xlim=[10,2700]
        # 时残留的 10^0）不会被绘制，却会被误判成越界并撑爆左边距
        try:
            labels = _onscreen_tick_labels(ax)
        except Exception:
            continue
        for t in labels:
            try:
                bb = t.get_window_extent(renderer=renderer)
            except Exception:
                continue
            # figure 坐标系：y=0 在底部，x=0 在左侧
            if bb.y0 < 0:
                overflow_bottom_px = max(overflow_bottom_px, -bb.y0)
            if bb.x0 < 0:
                overflow_left_px = max(overflow_left_px, -bb.x0)

    if overflow_bottom_px <= 1 and overflow_left_px <= 1:
        return  # 没有标签越界，无需处理

    # 换算成 figure 比例，加 1.5% 安全余量
    extra_bottom = overflow_bottom_px / fig_h_px + 0.015
    extra_left = overflow_left_px / fig_w_px + 0.015

    sp = fig.subplotpars
    new_bottom = min(0.45, sp.bottom + extra_bottom)  # 封顶 0.45，防止 axes 被压没
    new_left = min(0.40, sp.left + extra_left)
    # ⚠ 撞顶是异常信号：正常图的标签越界量顶多几十像素，需要 40% 图宽当左边距
    # 说明测量被污染了（历史真实案例：对数轴外的幽灵刻度被算成越界 457px）。
    # 不静默放过，打一行提示便于定位。
    if sp.left + extra_left > 0.40 or sp.bottom + extra_bottom > 0.45:
        print(f"[plot_utils] WARNING 标签越界兜底撞到封顶: "
              f"left {sp.left:.3f}+{extra_left:.3f} bottom {sp.bottom:.3f}+{extra_bottom:.3f} "
              f"(越界实测 左{overflow_left_px:.0f}px 下{overflow_bottom_px:.0f}px) "
              f"—— 若图上出现大片空白，检查是否有轴外刻度/离屏文字污染测量")
    # 保证 bottom < top、left < right，避免非法布局
    new_bottom = min(new_bottom, sp.top - 0.15)
    new_left = min(new_left, sp.right - 0.15)

    applied = False
    try:
        fig.subplots_adjust(
            bottom=max(sp.bottom, new_bottom),
            left=max(sp.left, new_left),
        )
        applied = True
    except Exception:
        applied = False

    # subplots_adjust 对手动布局（add_axes/GridSpec）无效时，直接平移+压缩 axes position
    if not applied or overflow_bottom_px > 2 or overflow_left_px > 2:
        # 重新实测：subplots_adjust 生效后可能已解决
        try:
            fig.canvas.draw()
            renderer = fig.canvas.get_renderer()
        except Exception:
            pass
        for ax in axes:
            try:
                still_bottom = 0.0
                still_left = 0.0
                labels = _onscreen_tick_labels(ax)  # 同样过滤轴外幽灵刻度
                for t in labels:
                    bb = t.get_window_extent(renderer=renderer)
                    if bb.y0 < 0:
                        still_bottom = max(still_bottom, -bb.y0)
                    if bb.x0 < 0:
                        still_left = max(still_left, -bb.x0)
                if still_bottom <= 1 and still_left <= 1:
                    continue
                pos = ax.get_position()
                dy = still_bottom / fig_h_px + 0.01 if still_bottom > 1 else 0.0
                dx = still_left / fig_w_px + 0.01 if still_left > 1 else 0.0
                ax.set_position([
                    pos.x0 + dx,
                    pos.y0 + dy,
                    max(0.1, pos.width - dx),
                    max(0.1, pos.height - dy),
                ])
            except Exception:
                pass


def _guard_subplot_size(fig):
    """防护：检测子图是否被压缩得过小，如果是则强制修复布局。
    
    常见原因：subplot margins 过紧、tight_layout(pad) 过大、
    ax.text(transAxes) 标签被算入空间分配。
    
    强制修复策略：检测到问题 → 重置 margins → 重新 tight_layout(pad=0.3) → 再验证。
    """
    # ★ 3D 轴豁免：3D 曲面 + 窄 colorbar 会被误判"子图过窄"而挤塌，直接跳过
    if _has_3d_axes(fig):
        return

    axes = [ax for ax in fig.get_axes() if ax.get_visible() and not ax.get_label().startswith('_')]
    if not axes:
        return

    fig_w, fig_h = fig.get_size_inches()
    if fig_w <= 0 or fig_h <= 0:
        return

    def _is_too_small():
        """检测是否有子图过小。"""
        for ax in axes:
            pos = ax.get_position()
            ax_w_inch = pos.width * fig_w
            ax_h_inch = pos.height * fig_h
            # 子图面积小于 1.5 平方英寸 → 肯定有问题
            if ax_w_inch * ax_h_inch < 1.5:
                return True
            # 子图高度小于 1 英寸 → 太扁了
            if ax_h_inch < 1.0:
                return True
            # 子图宽度小于 2 英寸 → 太窄了
            if ax_w_inch < 2.0:
                return True
        return False
    
    if not _is_too_small():
        return
    
    # ★ 强制修复第一步：重置 subplot margins
    n_axes = len(axes)
    if n_axes == 1:
        fig.subplots_adjust(left=0.12, right=0.95, top=0.92, bottom=0.12)
    else:
        fig.subplots_adjust(left=0.10, right=0.95, top=0.93, bottom=0.10,
                            hspace=0.3, wspace=0.3)
    
    # ★ 强制修复第二步：用小 pad 重新 tight_layout 覆盖之前的大 pad
    try:
        fig.tight_layout(pad=0.3)
    except Exception:
        pass
    
    # ★ 强制修复第三步：如果还是太小，直接放弃 tight_layout，手动设置合理布局
    if _is_too_small():
        if n_axes == 1:
            fig.subplots_adjust(left=0.12, right=0.95, top=0.92, bottom=0.12)
        elif n_axes <= 4:
            fig.subplots_adjust(left=0.08, right=0.96, top=0.94, bottom=0.08,
                                hspace=0.25, wspace=0.25)
        else:
            fig.subplots_adjust(left=0.06, right=0.97, top=0.95, bottom=0.06,
                                hspace=0.2, wspace=0.2)


def _clamp_texts_to_axes(ax, texts, renderer):
    """将超出 axes 边界的文字/标注拉回 axes 内部。

    帕累托图、灵敏度图等场景中，annotate 的 xytext 用硬编码偏移，
    如果数据点靠近边缘，标注就会超出 axes 区域。
    此函数检测每个 Text 的 bounding box 是否超出 axes 范围，
    如果超出就把它拉回来（保留 4px 内边距）。
    """
    try:
        ax_bbox = ax.get_window_extent(renderer=renderer)
    except Exception:
        return

    pad = 4  # 像素内边距
    inv = ax.transData.inverted()

    for t in texts:
        try:
            t_bbox = t.get_window_extent(renderer=renderer)
        except Exception:
            continue

        dx_px, dy_px = 0.0, 0.0

        # 右边超出
        if t_bbox.x1 > ax_bbox.x1 - pad:
            dx_px = ax_bbox.x1 - pad - t_bbox.x1
        # 左边超出
        if t_bbox.x0 < ax_bbox.x0 + pad:
            dx_px = ax_bbox.x0 + pad - t_bbox.x0
        # 上边超出
        if t_bbox.y1 > ax_bbox.y1 - pad:
            dy_px = ax_bbox.y1 - pad - t_bbox.y1
        # 下边超出
        if t_bbox.y0 < ax_bbox.y0 + pad:
            dy_px = ax_bbox.y0 + pad - t_bbox.y0

        if abs(dx_px) < 0.5 and abs(dy_px) < 0.5:
            continue

        # 像素偏移 → 数据坐标偏移
        x, y = t.get_position()
        p0 = inv.transform((0, 0))
        p1 = inv.transform((dx_px, dy_px))
        t.set_position((x + p1[0] - p0[0], y + p1[1] - p0[1]))


def _auto_fix_overlaps(fig):
    """自动检测并修复 fig 中所有 axes 上的文字重叠。

    策略：
    1. 收集每个 ax 上所有可见的 Text 对象（排除轴标签、标题等）
    2. 计算每对 Text 的 bounding box，检测是否重叠
    3. 如果有重叠，调用 adjustText 自动推开
    4. 同时检测图例是否遮挡数据，如果遮挡则移动图例
    5. 检测 y 轴标签是否被相邻 axes（如分组色条）遮挡
    """
    # ★ 3D 轴豁免：adjustText 基于 2D bbox 推文字，对 3D 投影无意义且可能扰乱布局
    if _has_3d_axes(fig):
        return
    try:
        renderer = fig.canvas.get_renderer()
    except Exception:
        # 某些后端没有 renderer，跳过检测
        return

    for ax in fig.get_axes():
        # 收集用户添加的 Text 对象（排除轴标签、标题、tick labels）
        user_texts = []
        skip_texts = set()
        # 标记要跳过的系统文本
        if ax.xaxis.label:
            skip_texts.add(id(ax.xaxis.label))
        if ax.yaxis.label:
            skip_texts.add(id(ax.yaxis.label))
        if ax.title:
            skip_texts.add(id(ax.title))
        for t in ax.get_xticklabels() + ax.get_yticklabels():
            skip_texts.add(id(t))

        for t in ax.texts:
            if id(t) in skip_texts:
                continue
            if not t.get_visible():
                continue
            txt = t.get_text().strip()
            if not txt:
                continue
            user_texts.append(t)

        # ★ 边界裁剪：检测标注/文字是否超出 axes 范围，拉回来
        # 即使只有 1 个标注也需要检测（帕累托图等场景）
        if user_texts:
            _clamp_texts_to_axes(ax, user_texts, renderer)

        if len(user_texts) < 2:
            continue

        # 检测是否有重叠
        has_overlap = False
        bboxes = []
        for t in user_texts:
            try:
                bb = t.get_window_extent(renderer=renderer)
                bboxes.append(bb)
            except Exception:
                bboxes.append(None)

        for i in range(len(bboxes)):
            if bboxes[i] is None:
                continue
            for j in range(i + 1, len(bboxes)):
                if bboxes[j] is None:
                    continue
                if bboxes[i].overlaps(bboxes[j]):
                    has_overlap = True
                    break
            if has_overlap:
                break

        if not has_overlap:
            continue

        # 有重叠 → 尝试用 adjustText 修复
        adjust_text = _ensure_adjustText()
        if adjust_text:
            try:
                adjust_text(user_texts, ax=ax,
                            force_points=0.3, force_text=0.5,
                            expand_points=(1.5, 1.5),
                            arrowprops=dict(arrowstyle='', lw=0))
            except Exception:
                # adjustText 失败，尝试简易修复
                _simple_spread(ax, user_texts, bboxes, renderer)
        else:
            _simple_spread(ax, user_texts, bboxes, renderer)

        # adjustText 推开后可能又超出边界，再裁剪一次
        _clamp_texts_to_axes(ax, user_texts, renderer)

        # 检测图例是否遮挡数据 → 自动挪位
        # ⛔ 但只在【用户没有显式指定位置】时才动（loc='best' / 未传 loc，matplotlib 记为 _loc==0）。
        #    以前无条件覆盖，会把脚本里写的 loc='center left' 无声改成 'upper right'：
        #    作者本来想用图例填补左侧空白，结果图例被挪到右上、左边露出一大片空白，
        #    而且作者查代码只会看到自己写的 center left，根本对不上（实测踩过，很难排查）。
        #    bbox_to_anchor 也挡不住（set_loc 之后 anchor 语义随之改变），所以必须在这里判断。
        legend = ax.get_legend()
        if legend and legend.get_visible():
            _user_fixed = True
            try:
                # _loc == 0 表示 'best'（含未显式传 loc 的默认情形）→ 视为"作者没指定"
                _user_fixed = getattr(legend, '_loc', 0) != 0
            except Exception:
                _user_fixed = False
            if not _user_fixed:
                try:
                    best_loc = check_legend_overlap(ax)
                    legend.set_loc(best_loc)  # matplotlib 3.x
                except (AttributeError, Exception):
                    try:
                        legend._loc = {
                            'upper right': 1, 'upper left': 2,
                            'lower left': 3, 'lower right': 4,
                            'center right': 7, 'center left': 6,
                        }.get(check_legend_overlap(ax), 1)
                    except Exception:
                        pass

        # ★ 检测 user texts 是否和 tick labels 重叠（如标注和 X 轴刻度重叠）
        tick_bboxes = []
        for t in _onscreen_tick_labels(ax):  # 排除轴外幽灵刻度，避免误判重叠
            if t.get_visible() and t.get_text().strip():
                try:
                    tick_bboxes.append(t.get_window_extent(renderer=renderer))
                except Exception:
                    pass
        for i, ut in enumerate(user_texts):
            if bboxes[i] is None:
                continue
            for tb in tick_bboxes:
                if bboxes[i].overlaps(tb):
                    # user text 和 tick label 重叠 → 把 user text 往上推
                    overlap_y = tb.y1 - bboxes[i].y0 + 4
                    inv = ax.transData.inverted()
                    p0 = inv.transform((0, 0))
                    p1 = inv.transform((0, overlap_y))
                    dy = p1[1] - p0[1]
                    x, y = ut.get_position()
                    ut.set_position((x, y + abs(dy)))
                    try:
                        bboxes[i] = ut.get_window_extent(renderer=renderer)
                    except Exception:
                        pass
                    break

    # ★ 也处理 annotate 创建的标注（ax.texts 不包含 annotate 的文本部分）
    for ax in fig.get_axes():
        annots = [child for child in ax.get_children()
                  if hasattr(child, 'xyann') or (hasattr(child, 'anncoords') and hasattr(child, 'get_text'))]
        if not annots:
            # annotate 创建的对象在 ax.texts 中（matplotlib 3.x），已经处理过
            # 但也检查 ax.patches 中的 FancyArrowPatch
            pass

    # ★ 检测 y 轴标签是否被相邻 axes（如分组色条）遮挡
    _fix_ylabel_overlap(fig, renderer)


def _fix_ylabel_overlap(fig, renderer):
    """检测并修复 y 轴标签被相邻 axes 遮挡的问题（如聚类热力图的左侧色条）。
    
    三阶段策略：
    1. 检测 y label 是否被左侧 axes（色条/树状图）覆盖 → 把左侧 axes 往左推
    2. 推到 figure 边缘还不够 → 自动截断超长 y label 文本（保留前 N 字 + …）
    3. 仍溢出 figure 左边界 → 减小 y label 字号
    """
    all_axes = fig.get_axes()
    if len(all_axes) < 2:
        # 单 axes 也可能有 y label 溢出 figure 边界的问题
        for ax in all_axes:
            _truncate_ylabels_if_overflow(ax, fig, renderer)
        return
    for ax in all_axes:
        ytick_labels = _onscreen_tick_labels(ax, which='y')  # 排除轴外幽灵刻度
        if not ytick_labels:
            continue
        # 获取 y 轴标签的最左边界（display coords）
        leftmost = None
        for lbl in ytick_labels:
            if not lbl.get_visible() or not lbl.get_text().strip():
                continue
            try:
                bb = lbl.get_window_extent(renderer=renderer)
                if leftmost is None or bb.x0 < leftmost:
                    leftmost = bb.x0
            except Exception:
                continue
        if leftmost is None:
            continue
        # 检查是否有其他 axes 的区域覆盖了这些标签
        ax_bbox_disp = ax.get_window_extent(renderer=renderer)
        pushed = False
        for other_ax in all_axes:
            if other_ax is ax:
                continue
            other_bbox = other_ax.get_window_extent(renderer=renderer)
            # ⛔ 同行约束（修复 bug：多行网格子图被误判为"左侧遮挡物"）
            # 之前漏判：只看 x 横向重叠，不看 y 是否同行 → 同列上下堆叠子图会被误推，
            # 导致左上角子图(a) 被左下角(d)的"遮挡判定"挤压变窄+左移。
            # 现在要求：竖直方向必须实质重叠（重叠 > 较小者高度的 50%）才算"左侧遮挡物"。
            overlap_top = min(ax_bbox_disp.y1, other_bbox.y1)
            overlap_bot = max(ax_bbox_disp.y0, other_bbox.y0)
            v_overlap = overlap_top - overlap_bot
            min_h = min(ax_bbox_disp.height, other_bbox.height)
            if v_overlap <= 0 or (min_h > 0 and v_overlap < min_h * 0.5):
                # 不在同一行（竖直无实质重叠）→ 跳过，不算遮挡物
                continue
            # 如果其他 axes 在当前 axes 左侧且与标签区域重叠
            if other_bbox.x1 > leftmost and other_bbox.x0 < ax_bbox_disp.x0:
                # 计算需要左移的量（figure fraction）
                fig_width = fig.get_window_extent(renderer=renderer).width
                overlap_px = other_bbox.x1 - leftmost + 8  # 8px 额外间距
                shift = overlap_px / fig_width
                # 把遮挡的 axes 往左推（但不能推到 figure 外）
                pos = other_ax.get_position()
                new_x0 = max(0.01, pos.x0 - shift)
                new_width = pos.width - (pos.x0 - new_x0) if new_x0 < pos.x0 else pos.width
                other_ax.set_position([new_x0, pos.y0, max(0.01, new_width), pos.height])
                pushed = True
        # ★ 推完仍可能溢出 figure 左边界 → 触发截断/缩字号兜底
        _truncate_ylabels_if_overflow(ax, fig, renderer)


def _truncate_ylabels_if_overflow(ax, fig, renderer):
    """兜底：当 y label 溢出 figure 左边界（x0 < 0）时，自动截断文本 + 减小字号。"""
    try:
        fig_bbox = fig.get_window_extent(renderer=renderer)
    except Exception:
        return

    # 只看真正会绘制的刻度：轴外的"幽灵刻度"（log 轴常见）位置远在画布左侧，
    # 会被误判成溢出，进而把本来放得下的 y 标签截断成省略号并缩小字号
    ytick_labels = [t for t in _onscreen_tick_labels(ax, which='y')
                    if t.get_visible() and t.get_text().strip()]
    if not ytick_labels:
        return

    # 第一步：检测是否溢出 figure 左边界
    overflow_px = 0
    for lbl in ytick_labels:
        try:
            bb = lbl.get_window_extent(renderer=renderer)
            if bb.x0 < fig_bbox.x0:
                overflow_px = max(overflow_px, fig_bbox.x0 - bb.x0)
        except Exception:
            continue
    if overflow_px <= 0:
        return

    # 第二步：尝试截断超长文本（保留前 N 字 + …）
    # 估算可用字符数：原始最长文本字符数 - 溢出像素 / 单字符宽度
    max_text_len = max((len(lbl.get_text()) for lbl in ytick_labels), default=0)
    if max_text_len > 8:
        # 估算单字符宽度（用最长标签 / 字符数）
        longest_lbl = max(ytick_labels, key=lambda t: len(t.get_text()))
        try:
            longest_bb = longest_lbl.get_window_extent(renderer=renderer)
            char_width = longest_bb.width / max(len(longest_lbl.get_text()), 1)
            # 需要砍掉的字符数 = 溢出像素 / 单字符宽度 + 1 字（… 占位）
            chars_to_cut = int(overflow_px / max(char_width, 1)) + 1
            new_max_len = max(6, max_text_len - chars_to_cut)
            # 整批 set_yticklabels（单 set_text 在重绘时会被 formatter 覆盖）
            current_fontsize = ytick_labels[0].get_fontsize()
            new_texts = []
            for lbl in ytick_labels:
                txt = lbl.get_text()
                if len(txt) > new_max_len:
                    new_texts.append(txt[: new_max_len - 1] + '…')
                else:
                    new_texts.append(txt)
            try:
                ax.set_yticks(ax.get_yticks())
                ax.set_yticklabels(new_texts, fontsize=current_fontsize)
            except Exception:
                for lbl, new_txt in zip(ytick_labels, new_texts):
                    lbl.set_text(new_txt)
        except Exception:
            pass

    # 第三步：再检查仍溢出 → 减字号
    try:
        still_overflow = False
        for lbl in ytick_labels:
            bb = lbl.get_window_extent(renderer=renderer)
            if bb.x0 < fig_bbox.x0:
                still_overflow = True
                break
        if still_overflow:
            current_size = ytick_labels[0].get_fontsize()
            new_size = max(6, current_size - 1)
            for lbl in ytick_labels:
                lbl.set_fontsize(new_size)
    except Exception:
        pass


def auto_truncate_yticklabels(ax, max_chars=20, suffix='…'):
    """公开 API：主动截断超长 y tick labels（配方代码可调用，防止 y 轴遮挡）。
    
    用法：
        ax.set_yticklabels(long_method_names, fontsize=10)
        auto_truncate_yticklabels(ax, max_chars=18)  # 超过 18 字符的截断
    
    适用场景：聚类热力图、SHAP 图、特征重要性图 — 这些图 y 轴标签是变量名/方法名，
    遇到长字符串（"average_silhouette_coefficient_2024" 等）会溢出 figure 左边界。
    
    注意：matplotlib 在重绘时可能用 formatter 覆盖单个 Text，所以这里整批 set_yticklabels。
    """
    labels = ax.get_yticklabels()
    if not labels:
        return
    fontsize = labels[0].get_fontsize() if labels else None
    new_texts = []
    for lbl in labels:
        txt = lbl.get_text()
        if len(txt) > max_chars:
            new_texts.append(txt[: max_chars - 1] + suffix)
        else:
            new_texts.append(txt)
    # 用 set_yticklabels 整批替换（同时锁定原 tick 位置避免 matplotlib warning）
    try:
        ax.set_yticks(ax.get_yticks())
        if fontsize is not None:
            ax.set_yticklabels(new_texts, fontsize=fontsize)
        else:
            ax.set_yticklabels(new_texts)
    except Exception:
        # 兜底：单个 set_text
        for lbl, new_txt in zip(labels, new_texts):
            lbl.set_text(new_txt)


def _simple_spread(ax, texts, bboxes, renderer):
    """简易重叠修复：把重叠的文本沿 y 方向推开。"""
    if not texts or not bboxes:
        return

    # 按 y 坐标排序
    indexed = [(i, t) for i, t in enumerate(texts) if bboxes[i] is not None]
    indexed.sort(key=lambda x: x[1].get_position()[1])

    for k in range(1, len(indexed)):
        i_curr = indexed[k][0]
        i_prev = indexed[k - 1][0]
        bb_curr = bboxes[i_curr]
        bb_prev = bboxes[i_prev]
        if bb_curr is None or bb_prev is None:
            continue

        if bb_prev.overlaps(bb_curr):
            # 计算需要的最小偏移（像素）
            overlap_y = bb_prev.y1 - bb_curr.y0 + 2  # 2px padding
            # 转换为数据坐标
            inv = ax.transData.inverted()
            p0 = inv.transform((0, 0))
            p1 = inv.transform((0, overlap_y))
            dy = p1[1] - p0[1]
            # 把当前文本往上推
            x, y = texts[i_curr].get_position()
            texts[i_curr].set_position((x, y + dy))
            # 更新 bbox
            try:
                bboxes[i_curr] = texts[i_curr].get_window_extent(renderer=renderer)
            except Exception:
                pass

# 公开别名，供外部脚本调用
save_fig = _save


# ============================================================
# 标签防遮挡工具
# ============================================================

def _ensure_adjustText():
    """确保 adjustText 库可用，不可用时自动安装。"""
    try:
        from adjustText import adjust_text
        return adjust_text
    except ImportError:
        try:
            import subprocess
            subprocess.check_call(
                [sys.executable, '-m', 'pip', 'install', 'adjustText', '-q'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            from adjustText import adjust_text
            return adjust_text
        except Exception:
            return None


def smart_labels(ax, xs, ys, texts, colors=None, fontsize=9, fontweight='normal',
                 offset=(8, 0), fmt=None, ha='left', va='center',
                 force_points=0.3, force_text=0.5, avoid_self=True,
                 bbox=None, arrowprops=None, max_labels=50):
    """智能标签标注 — 自动检测并推开重叠标签。

    优先使用 adjustText 库做物理模拟推开；如果不可用，退化为
    基于数据间距的简易偏移策略。

    Args:
        ax: matplotlib Axes 对象
        xs: 标签锚点 x 坐标列表
        ys: 标签锚点 y 坐标列表
        texts: 标签文本列表
        colors: 每个标签的颜色（None 则统一用深灰）
        fontsize: 字号
        fontweight: 字重（'bold' / 'normal'）
        offset: (dx, dy) 像素偏移，adjustText 模式下作为初始偏移
        fmt: 格式化字符串，如 '{:.3f}'，传入时 texts 应为数值列表
        ha/va: 水平/垂直对齐
        force_points: adjustText 的点斥力
        force_text: adjustText 的文本斥力
        avoid_self: 是否避免标签之间重叠
        bbox: 标签背景框样式 dict（如 dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7)）
        arrowprops: 箭头样式 dict（如 dict(arrowstyle='->', color='gray', lw=0.5)）
        max_labels: 超过此数量时跳过标注（数据太密集标注无意义）

    Returns:
        list of Text 对象

    用法示例::

        # 棒棒糖图标注
        smart_labels(ax, scores, y_pos, [f'{s:.3f}' for s in scores],
                     colors=[PALETTE[0]]*len(scores), fontweight='bold')

        # 散点图标注（带箭头）
        smart_labels(ax, x_outliers, y_outliers, gene_names,
                     arrowprops=dict(arrowstyle='->', color='gray', lw=0.5))
    """
    if len(xs) > max_labels:
        return []

    plt = _get_plt()
    text_objs = []

    # 格式化文本
    if fmt is not None:
        display_texts = [fmt.format(t) for t in texts]
    else:
        display_texts = [str(t) for t in texts]

    default_color = '#333333'

    # 创建 Text 对象
    for i, (x, y, txt) in enumerate(zip(xs, ys, display_texts)):
        c = colors[i] if colors and i < len(colors) else default_color
        fw = fontweight if isinstance(fontweight, str) else (
            fontweight[i] if i < len(fontweight) else 'normal')
        t = ax.text(x, y, txt, fontsize=fontsize, fontweight=fw,
                    color=c, ha=ha, va=va,
                    bbox=bbox if bbox else None)
        text_objs.append(t)

    # 尝试用 adjustText 自动推开
    adjust_text = _ensure_adjustText()
    if adjust_text and avoid_self and len(text_objs) > 1:
        try:
            arrow_kw = arrowprops or dict(arrowstyle='-', color='#cccccc', lw=0.3)
            adjust_text(text_objs, ax=ax,
                        force_points=force_points,
                        force_text=force_text,
                        expand_points=(1.5, 1.5),
                        arrowprops=arrow_kw)
        except Exception:
            # adjustText 失败时退化为手动偏移
            _fallback_offset(ax, text_objs, xs, ys, offset)
    else:
        # 没有 adjustText，用简易偏移
        _fallback_offset(ax, text_objs, xs, ys, offset)

    return text_objs


def _fallback_offset(ax, text_objs, xs, ys, offset):
    """简易防遮挡：根据数据间距计算偏移方向，密集区域交替上下偏移。"""
    if not text_objs:
        return

    fig = ax.get_figure()
    renderer = fig.canvas.get_renderer() if hasattr(fig.canvas, 'get_renderer') else None

    # 获取数据坐标范围
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    x_range = xlim[1] - xlim[0] if xlim[1] != xlim[0] else 1
    y_range = ylim[1] - ylim[0] if ylim[1] != ylim[0] else 1

    # 估算标签高度（数据坐标）
    label_height = y_range * 0.035  # 约 3.5% 的 y 轴范围

    # 按 y 坐标排序，检测相邻标签是否过近
    indices = list(range(len(text_objs)))
    indices.sort(key=lambda i: ys[i])

    for k in range(len(indices)):
        i = indices[k]
        # 基础偏移
        dx_data = offset[0] * x_range / 500  # 像素偏移转数据坐标（近似）
        dy_data = offset[1] * y_range / 500

        # 检查与前一个标签是否过近
        if k > 0:
            j = indices[k - 1]
            gap = abs(ys[i] - ys[j])
            if gap < label_height * 1.5:
                # 交替上下偏移
                direction = 1 if k % 2 == 0 else -1
                dy_data += direction * label_height * 0.8

        text_objs[i].set_position((xs[i] + dx_data, ys[i] + dy_data))


def check_legend_overlap(ax, preferred_locs=None):
    """自动选择不遮挡数据的图例位置。

    检测数据分布的稀疏区域，把图例放在最空的角落。

    Args:
        ax: matplotlib Axes 对象
        preferred_locs: 优先尝试的位置列表，默认 ['upper right', 'upper left',
                        'lower right', 'lower left', 'center right']

    Returns:
        最佳位置字符串（可直接传给 ax.legend(loc=...)）
    """
    if preferred_locs is None:
        preferred_locs = ['upper right', 'upper left', 'lower right',
                          'lower left', 'center right', 'center left']

    # 收集所有数据点
    all_x, all_y = [], []
    for line in ax.get_lines():
        xd, yd = line.get_xdata(), line.get_ydata()
        if len(xd) > 0:
            all_x.extend(xd)
            all_y.extend(yd)
    for coll in ax.collections:
        offsets = coll.get_offsets()
        if len(offsets) > 0:
            all_x.extend(offsets[:, 0])
            all_y.extend(offsets[:, 1])

    if not all_x:
        return preferred_locs[0]

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    xmid = (xlim[0] + xlim[1]) / 2
    ymid = (ylim[0] + ylim[1]) / 2

    # 统计每个象限的数据点密度
    quadrant_counts = {
        'upper right': 0, 'upper left': 0,
        'lower right': 0, 'lower left': 0,
        'center right': 0, 'center left': 0,
    }
    for x, y in zip(all_x, all_y):
        if y >= ymid:
            if x >= xmid:
                quadrant_counts['upper right'] += 1
            else:
                quadrant_counts['upper left'] += 1
        else:
            if x >= xmid:
                quadrant_counts['lower right'] += 1
            else:
                quadrant_counts['lower left'] += 1
        # center 区域
        if abs(y - ymid) < (ylim[1] - ylim[0]) * 0.25:
            if x >= xmid:
                quadrant_counts['center right'] += 1
            else:
                quadrant_counts['center left'] += 1

    # 在 preferred_locs 中选密度最低的
    best_loc = min(preferred_locs, key=lambda loc: quadrant_counts.get(loc, 999))
    return best_loc


def auto_legend(ax, **kwargs):
    """智能图例：自动选择不遮挡数据的位置。

    用法：用 auto_legend(ax) 替代 ax.legend()

    Args:
        ax: matplotlib Axes 对象
        **kwargs: 传给 ax.legend() 的其他参数
    """
    loc = check_legend_overlap(ax)
    # ⛔ 默认去框：实证对比 94 张真实竞赛图，带灰框图例是"显土"的主要来源之一
    #    （高分图去框率 37% vs 平庸图 0%）。收紧 labelspacing/handlelength 让图例更紧凑。
    #    调用方仍可用 auto_legend(ax, frameon=True) 覆盖。
    defaults = dict(frameon=False, fontsize=9, labelspacing=0.35, handlelength=1.6,
                    borderpad=0.3, fancybox=False, shadow=False)
    defaults.update(kwargs)
    defaults['loc'] = loc
    return ax.legend(**defaults)


# ============================================================
# 图表函数
# ============================================================

def heatmap(data, labels=None, output='figures/fig_heatmap.pdf', title=None,
            annot=True, fmt='.2f', cmap=None, figsize=(8, 6)):
    """相关性热力图（带数值标注）。
    
    Args:
        data: 2D array 或 DataFrame（相关系数矩阵）
        labels: 行列标签
        output: 输出路径
        annot: 是否标注数值
        fmt: 数值格式
    """
    plt = _get_plt()
    sns = _get_sns()
    setup_style()
    try:
        from .palette_maps import palette_cmap, contrast_text
    except ImportError:
        from palette_maps import palette_cmap, contrast_text
    if cmap is None:
        cmap = palette_cmap('diverging')
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    if sns:
        mask = np.triu(np.ones_like(data, dtype=bool), k=1)
        hm = sns.heatmap(data, mask=mask, annot=annot, fmt=fmt, cmap=cmap,
                    center=0, square=True, linewidths=0.5,
                    xticklabels=labels, yticklabels=labels, ax=ax,
                    cbar_kws={'shrink': 0.8})
        # 文字颜色自适应：深色格子用白字，浅色格子用黑字
        if annot and hasattr(hm, 'texts'):
            from matplotlib.colors import Normalize
            flat = np.array(data).flatten()
            flat = flat[~np.isnan(flat)]
            if len(flat) > 0:
                norm = Normalize(vmin=flat.min(), vmax=flat.max())
                for text in hm.texts:
                    try:
                        val = float(text.get_text())
                        mesh = hm.collections[0]
                        text.set_color(contrast_text(mesh.cmap(mesh.norm(val))))
                    except (ValueError, TypeError):
                        pass
    else:
        im = ax.imshow(data, cmap=cmap, aspect='auto', vmin=-1, vmax=1)
        fig.colorbar(im, ax=ax, shrink=0.8)
        if annot:
            for i in range(data.shape[0]):
                for j in range(data.shape[1]):
                    if j <= i:
                        val = data[i, j]
                        color = contrast_text(im.cmap(im.norm(val)))
                        ax.text(j, i, f'{val:{fmt}}', ha='center', va='center', fontsize=8, color=color)
        if labels is not None:
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=45, ha='right')
            ax.set_yticks(range(len(labels)))
            ax.set_yticklabels(labels)

    _save(fig, output)


def forest_plot(coefs, ci_lower, ci_upper, labels, output='figures/fig_forest.pdf',
                figsize=(6, None), xlabel='Coefficient'):
    """回归系数森林图（带置信区间）。
    
    Args:
        coefs: 系数数组
        ci_lower: 置信区间下界
        ci_upper: 置信区间上界
        labels: 变量名列表
        output: 输出路径
    """
    plt = _get_plt()
    setup_style()
    n = len(coefs)
    if figsize[1] is None:
        figsize = (figsize[0], max(3, n * 0.4 + 1))
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    y_pos = np.arange(n)
    xerr = [np.array(coefs) - np.array(ci_lower), np.array(ci_upper) - np.array(coefs)]

    ax.errorbar(coefs, y_pos, xerr=xerr, fmt='o', color=COLORS['primary'],
                ecolor=COLORS['gray'], elinewidth=1.5, capsize=3, markersize=5)
    ax.axvline(x=0, color=COLORS['accent'], linestyle='--', linewidth=0.8, alpha=0.7)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.set_xlabel(xlabel)
    ax.invert_yaxis()

    _save(fig, output)


def trend_plot(x, y, output='figures/fig_trend.pdf', ci=None,
               xlabel='', ylabel='', label=None, figsize=(7, 4)):
    """时间趋势图（可选置信带）。
    
    Args:
        x: x 轴数据
        y: y 轴数据
        ci: (lower, upper) 置信区间元组，可选
        output: 输出路径
    """
    plt = _get_plt()
    setup_style()
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    ax.plot(x, y, color=COLORS['primary'], linewidth=1.5, label=label)
    if ci is not None:
        ax.fill_between(x, ci[0], ci[1], alpha=0.15, color=COLORS['secondary'])
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if label:
        ax.legend()

    _save(fig, output)


def bar_compare(categories, values_dict, output='figures/fig_bar.pdf',
                ylabel='', figsize=(7, 4), show_values=True):
    """分组柱状图（带误差棒，多组对比）。
    
    Args:
        categories: 类别列表 ['A', 'B', 'C']
        values_dict: {'方法1': [v1, v2, v3], '方法2': [v1, v2, v3]}
                     或 {'方法1': {'values': [...], 'errors': [...]}}
        output: 输出路径
    """
    plt = _get_plt()
    setup_style()
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    n_groups = len(categories)
    n_bars = len(values_dict)
    bar_width = 0.8 / n_bars
    x = np.arange(n_groups)

    for i, (name, data) in enumerate(values_dict.items()):
        if isinstance(data, dict):
            vals = data['values']
            errs = data.get('errors', None)
        else:
            vals = data
            errs = None
        offset = (i - n_bars / 2 + 0.5) * bar_width
        bars = ax.bar(x + offset, vals, bar_width, label=name,
                       color=PALETTE[i % len(PALETTE)], yerr=errs,
                       capsize=3, error_kw={'linewidth': 0.8})
        if show_values:
            for bar, val in zip(bars, vals):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01 * max(vals),
                        f'{val:.2f}', ha='center', va='bottom', fontsize=7)

    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_ylabel(ylabel)
    ax.legend()

    _save(fig, output)


def distribution_plot(data, output='figures/fig_dist.pdf', xlabel='', bins=30, figsize=(6, 4)):
    """核密度 + 直方图。"""
    plt = _get_plt()
    sns = _get_sns()
    setup_style()
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    if sns:
        sns.histplot(data, bins=bins, kde=True, color=COLORS['secondary'], ax=ax,
                     edgecolor='white', linewidth=0.5)
    else:
        ax.hist(data, bins=bins, density=True, color=COLORS['secondary'],
                edgecolor='white', linewidth=0.5, alpha=0.7)
    ax.set_xlabel(xlabel)
    ax.set_ylabel('Density')

    _save(fig, output)


def scatter_plot(x, y, output='figures/fig_scatter.pdf', xlabel='', ylabel='',
                 hue=None, fit_line=True, figsize=(6, 5)):
    """散点图（可选回归线）。"""
    plt = _get_plt()
    setup_style()
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    if hue is not None:
        for i, (name, mask) in enumerate(hue.items()):
            ax.scatter(np.array(x)[mask], np.array(y)[mask], s=20, alpha=0.6,
                       color=PALETTE[i % len(PALETTE)], label=name)
        ax.legend()
    else:
        ax.scatter(x, y, s=20, alpha=0.6, color=COLORS['secondary'])

    if fit_line:
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        x_line = np.linspace(min(x), max(x), 100)
        ax.plot(x_line, p(x_line), color=COLORS['accent'], linewidth=1, linestyle='--')

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    _save(fig, output)


def residual_diagnostic(y_true, y_pred, output='figures/fig_residual.pdf', figsize=(10, 8)):
    """残差诊断四图（QQ图、残差散点、残差直方图、拟合值vs残差）。"""
    plt = _get_plt()
    setup_style()
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    residuals = np.array(y_true) - np.array(y_pred)
    std_resid = (residuals - residuals.mean()) / residuals.std()

    # 1. 残差 vs 拟合值
    ax = axes[0, 0]
    ax.scatter(y_pred, residuals, s=15, alpha=0.5, color=COLORS['secondary'])
    ax.axhline(y=0, color=COLORS['accent'], linestyle='--', linewidth=0.8)
    ax.set_xlabel('Fitted Values')
    ax.set_ylabel('Residuals')

    # 2. QQ 图
    ax = axes[0, 1]
    sorted_resid = np.sort(std_resid)
    n = len(sorted_resid)
    theoretical = np.array([_norm_ppf((i + 0.5) / n) for i in range(n)])
    ax.scatter(theoretical, sorted_resid, s=15, alpha=0.5, color=COLORS['secondary'])
    lim = max(abs(theoretical.min()), abs(theoretical.max())) * 1.1
    ax.plot([-lim, lim], [-lim, lim], color=COLORS['accent'], linestyle='--', linewidth=0.8)
    ax.set_xlabel('Theoretical Quantiles')
    ax.set_ylabel('Standardized Residuals')

    # 3. 残差直方图
    ax = axes[1, 0]
    ax.hist(residuals, bins=25, color=COLORS['secondary'], edgecolor='white', linewidth=0.5, density=True)
    ax.set_xlabel('Residuals')
    ax.set_ylabel('Density')

    # 4. Scale-Location
    ax = axes[1, 1]
    ax.scatter(y_pred, np.sqrt(np.abs(std_resid)), s=15, alpha=0.5, color=COLORS['secondary'])
    ax.set_xlabel('Fitted Values')
    ax.set_ylabel('sqrt(|Standardized Residuals|)')

    fig.tight_layout()
    _save(fig, output)


def _norm_ppf(p):
    """简易正态分位数函数（避免依赖 scipy）。"""
    # Abramowitz and Stegun approximation
    if p <= 0:
        return -4.0
    if p >= 1:
        return 4.0
    if p == 0.5:
        return 0.0
    if p > 0.5:
        return -_norm_ppf(1 - p)
    t = np.sqrt(-2 * np.log(p))
    c0, c1, c2 = 2.515517, 0.802853, 0.010328
    d1, d2, d3 = 1.432788, 0.189269, 0.001308
    return -(t - (c0 + c1 * t + c2 * t ** 2) / (1 + d1 * t + d2 * t ** 2 + d3 * t ** 3))


def multi_line_plot(x, ys, labels, output='figures/fig_multi_line.pdf',
                    xlabel='', ylabel='', figsize=(7, 4)):
    """多条线对比图（训练曲线、消融实验等）。

    Args:
        x: x 轴数据
        ys: list of y 数据序列
        labels: 每条线的标签
        output: 输出路径
    """
    plt = _get_plt()
    setup_style()
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    for i, (y, label) in enumerate(zip(ys, labels)):
        ax.plot(x, y, color=PALETTE[i % len(PALETTE)], linewidth=1.5, label=label)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()
    _save(fig, output)


def box_plot(data_dict, output='figures/fig_box.pdf', ylabel='', figsize=(7, 4)):
    """箱线图（分布对比）。

    Args:
        data_dict: {'方法A': [values], '方法B': [values]}
        output: 输出路径
    """
    plt = _get_plt()
    setup_style()
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    labels = list(data_dict.keys())
    data = list(data_dict.values())

    bp = ax.boxplot(data, labels=labels, patch_artist=True, widths=0.5,
                    medianprops={'color': COLORS['dark'], 'linewidth': 1.5})
    for i, patch in enumerate(bp['boxes']):
        patch.set_facecolor(PALETTE_LIGHT[i % len(PALETTE_LIGHT)])
        patch.set_edgecolor(PALETTE[i % len(PALETTE)])

    ax.set_ylabel(ylabel)
    _save(fig, output)


def radar_plot(categories, values_dict, output='figures/fig_radar.pdf', figsize=(6, 6)):
    """雷达图（多维度对比）。

    Args:
        categories: 维度名列表 ['Accuracy', 'Speed', 'Memory', ...]
        values_dict: {'方法A': [v1, v2, ...], '方法B': [v1, v2, ...]}
        output: 输出路径
    """
    plt = _get_plt()
    setup_style()
    fig, ax = plt.subplots(1, 1, figsize=figsize, subplot_kw=dict(polar=True))

    n = len(categories)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]  # 闭合

    for i, (name, vals) in enumerate(values_dict.items()):
        values = list(vals) + [vals[0]]  # 闭合
        ax.plot(angles, values, 'o-', linewidth=1.5, color=PALETTE[i % len(PALETTE)], label=name)
        ax.fill(angles, values, alpha=0.1, color=PALETTE[i % len(PALETTE)])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    _save(fig, output)


def subplot_grid(plot_funcs, nrows, ncols, output='figures/fig_grid.pdf',
                 figsize=None, titles=None):
    """多面板子图网格。

    Args:
        plot_funcs: list of callables, 每个接受 (ax,) 参数
        nrows, ncols: 网格尺寸
        output: 输出路径
        titles: 每个子图的标题列表（可选）
    """
    plt = _get_plt()
    setup_style()
    if figsize is None:
        figsize = (4 * ncols, 3.5 * nrows)
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
    if nrows == 1 and ncols == 1:
        axes = np.array([axes])
    axes_flat = axes.flatten()

    for i, func in enumerate(plot_funcs):
        if i < len(axes_flat):
            func(axes_flat[i])
            if titles and i < len(titles):
                axes_flat[i].set_title(titles[i], fontsize=10)

    # 隐藏多余的子图
    for j in range(len(plot_funcs), len(axes_flat)):
        axes_flat[j].set_visible(False)

    fig.tight_layout()
    _save(fig, output)
