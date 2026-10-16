"""Small, explicit display-language helpers; never translate source data in place.

Call ``localize_figure`` before the source's final layout/save. Only known whole
labels and bounded numeric annotation formats are translated automatically.
Pass data-derived names as ``protected_texts`` and user-approved display names
as ``labels``. Explicit display names take precedence over protection.
"""
from __future__ import annotations

import re
from collections.abc import Mapping

try:
    from .vivid_config import normalize_language
except ImportError:
    from vivid_config import normalize_language


# Exact display strings only. No substring replacement or fuzzy translation.
ENGLISH_LABELS = {
    '年份': 'Year', '时间': 'Time', '日期': 'Date', '月份': 'Month',
    '天数': 'Days', '小时': 'Hour', '时间 (s)': 'Time (s)',
    '时间（s）': 'Time (s)', '时间 (h)': 'Time (h)',
    '时间步': 'Time step', '迭代次数': 'Iterations', '轮次': 'Epoch',
    '得分': 'Score', '分数': 'Score', '数值': 'Value', '值': 'Value',
    '累计值': 'Cumulative value', '均值': 'Mean', '中位数': 'Median',
    '标准差': 'Standard deviation', '方差': 'Variance',
    '最大值': 'Maximum', '最小值': 'Minimum', '总计': 'Total',
    '数量': 'Count', '频次': 'Count', '频数': 'Frequency', '频率': 'Frequency',
    '密度': 'Density', '概率密度': 'Probability density', '概率': 'Probability',
    '累积概率': 'Cumulative probability', '累计概率': 'Cumulative probability',
    '占比': 'Share', '比例': 'Proportion', '百分比': 'Percentage',
    '准确率': 'Accuracy', '准确率 (%)': 'Accuracy (%)', '准确率（%）': 'Accuracy (%)',
    '精确率': 'Precision', '召回率': 'Recall', '损失': 'Loss',
    '误差': 'Error', '残差': 'Residual', '误差 (%)': 'Error (%)',
    '标准化残差': 'Standardized residual', '列聚类': 'Column clustering',
    '轮廓系数': 'Silhouette score', '平均轮廓系数': 'Mean silhouette score',
    '峰值': 'Peak', '临界螺距': 'Critical pitch',
    '真实值': 'Observed value', '实际值': 'Observed value',
    '预测值': 'Predicted value', '拟合值': 'Fitted value',
    '相关系数': 'Correlation', '相关性': 'Correlation',
    '相关系数 r': 'Correlation r', '皮尔逊相关系数': 'Pearson correlation',
    '权重': 'Weight', '重要性': 'Importance', '特征重要性': 'Feature importance',
    '特征值': 'Feature value', '贡献度': 'Contribution',
    '特征': 'Feature', '变量': 'Variable', '指标': 'Metric', '类别': 'Category',
    '分类': 'Class', '分组': 'Group', '样本': 'Sample', '样本编号': 'Sample index',
    '样本数': 'Sample count', '方法': 'Method', '模型': 'Model',
    '实验组': 'Treatment', '对照组': 'Control', '训练集': 'Training set',
    '测试集': 'Test set', '验证集': 'Validation set',
    '本文方法': 'Our method', '本文模型': 'Our model', '基线方法': 'Baseline',
    '基准方法': 'Baseline', '方案对比': 'Method comparison',
    '运行时间 (s)': 'Runtime (s)', '运行时间': 'Runtime',
    '效率': 'Efficiency', '成本': 'Cost', '收益': 'Return',
    '距离': 'Distance', '温度': 'Temperature', '条件': 'Condition',
    '综合得分': 'Overall score', '性能': 'Performance',
    '最优解': 'Optimum', '帕累托前沿': 'Pareto front',
    '目标1': 'Objective 1', '目标2': 'Objective 2', '目标3': 'Objective 3',
}

# Finite demo names, rather than patterns that might translate real entities.
for _prefix, _english in (
    ('方法', 'Method'), ('模型', 'Model'), ('指标', 'Metric'),
    ('特征', 'Feature'), ('变量', 'Variable'), ('方案', 'Method'),
    ('类别', 'Category'), ('分组', 'Group'),
):
    for _letter in 'ABCDEFGH':
        ENGLISH_LABELS[_prefix + _letter] = _english + ' ' + _letter
for _prefix, _english in (
    ('系列', 'Series'), ('类', 'Class'), ('分布', 'Distribution'),
    ('组', 'Group'), ('特征', 'Feature'), ('指标', 'Metric'),
):
    for _number in range(1, 17):
        ENGLISH_LABELS[_prefix + str(_number)] = _english + ' ' + str(_number)

_CJK = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]')
_NUMBER = r'[-+−]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?'
_NUMERIC_ANNOTATION = re.compile(
    r'(均值|中位数|最大值|最小值|标准差|轮廓系数|平均轮廓系数|峰值|临界螺距)'
    r'(\s*[:：=]\s*|\s+)(' + _NUMBER + r'%?)'
)
_LABEL_VALUE_ANNOTATION = re.compile(
    r'([^\r\n]+)(\n(?:' + _NUMBER + r'%?(?: \(' + _NUMBER + r'%\))?|'
    + _NUMBER + r'% \| ' + _NUMBER + r'))'
)

# Complete numeric display formats used by the templates. Captured numbers,
# signs, percentages, math punctuation and line breaks are never recomputed.
# This deliberately excludes error messages and arbitrary prose substitutions.
_DYNAMIC_ANNOTATIONS = (
    (re.compile(r'(\d+(?:\.\d+)?%) 跨度\n(' + _NUMBER + r')'),
     lambda m: m[1] + ' span\n' + m[2]),
    (re.compile(r'拐点(\n\(x=' + _NUMBER + r'\))'),
     lambda m: 'Turning point' + m[1]),
    (re.compile(r'自给率([ \t]*=[ \t]*' + _NUMBER + r'%)([ \t]+)进口依赖([ \t]*=[ \t]*' + _NUMBER + r'%)'),
     lambda m: 'Self-sufficiency' + m[1] + m[2] + 'Import dependence' + m[3]),
    (re.compile(r'(起点|终点)( \(\d{4}\))'),
     lambda m: ('Start' if m[1] == '起点' else 'End') + m[2]),
    (re.compile(r'最优点( \(' + _NUMBER + r', ' + _NUMBER + r'\))'),
     lambda m: 'Optimum' + m[1]),
    (re.compile(r'基准(±\d+(?:\.\d+)?% \(' + _NUMBER + r'~' + _NUMBER + r'\))'),
     lambda m: 'Baseline' + m[1]),
    (re.compile(r'(高高聚集|低低聚集|低高异常|高低异常|不显著)( \(\d+\))'),
     lambda m: {'高高聚集': 'High–high cluster', '低低聚集': 'Low–low cluster',
                '低高异常': 'Low–high outlier', '高低异常': 'High–low outlier',
                '不显著': 'Not significant'}[m[1]] + m[2]),
    (re.compile(r'LISA 聚类( \(p < ' + _NUMBER + r'\))'),
     lambda m: 'LISA clusters' + m[1]),
)


def _display_labels(labels):
    if labels is None:
        return {}
    if not isinstance(labels, Mapping) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in labels.items()
    ):
        raise ValueError('Display labels must map original text to display text')
    return labels


def translate_text(text, language='zh', labels=None, protected_texts=()):
    """Translate one complete display string; leave unknown/user text intact."""
    language = normalize_language(language)
    labels = _display_labels(labels)
    if not isinstance(text, str) or language != 'en':
        return text
    if text in labels:
        return labels[text]
    if text in protected_texts:
        return text
    if text in ENGLISH_LABELS:
        return ENGLISH_LABELS[text]
    match = _NUMERIC_ANNOTATION.fullmatch(text)
    if match:
        separator = match[2].replace('：', ':')
        return ENGLISH_LABELS[match[1]] + separator + match[3]
    match = _LABEL_VALUE_ANNOTATION.fullmatch(text)
    if match and match[1] not in protected_texts:
        display = labels.get(match[1], ENGLISH_LABELS.get(match[1]))
        if display is not None:
            return display + match[2]
    for pattern, replacement in _DYNAMIC_ANNOTATIONS:
        match = pattern.fullmatch(text)
        if match:
            return replacement(match)
    return text


def localize_figure(fig, language='zh', labels=None, protected_texts=()):
    """Localize existing Text artists only; preserve data, styles and geometry.

    Return changed count and up to 20 remaining visible Chinese display strings.
    The caller may show these through its existing review. No layout/size/font
    mutation is performed here; the original template still owns its layout.
    """
    from matplotlib.text import Text
    from matplotlib.ticker import Formatter

    language = normalize_language(language)
    labels = _display_labels(labels)
    protected = set(protected_texts)

    # Materialize original tick labels before replacing their formatter. Keep
    # identity tied to source wording when a user switches display language.
    for axes in fig.axes:
        for dimension in ('xaxis', 'yaxis', 'zaxis'):
            axis = getattr(axes, dimension, None)
            if axis is not None:
                axis.get_ticklabels(minor=False)
                axis.get_ticklabels(minor=True)
    for artist in fig.findobj(match=Text):
        if not hasattr(artist, '_vivid_source_text'):
            artist._vivid_source_text = artist.get_text()

    class DisplayFormatter(Formatter):
        # A redraw asks the formatter for labels again. Forward its locator/
        # offset bookkeeping, translating only the complete display result.
        def __init__(self, original):
            self.original = original

        def __call__(self, value, position=None):
            return translate_text(self.original(value, position), language, labels, protected)

        def set_axis(self, axis):
            super().set_axis(axis)
            self.original.set_axis(axis)

        def set_locs(self, locations):
            super().set_locs(locations)
            self.original.set_locs(locations)

        def get_offset(self):
            return self.original.get_offset()

        def format_data(self, value):
            return self.original.format_data(value)

        def format_data_short(self, value):
            return self.original.format_data_short(value)

    if language == 'en':
        for axes in fig.axes:
            for dimension in ('xaxis', 'yaxis', 'zaxis'):
                axis = getattr(axes, dimension, None)
                if axis is None:
                    continue
                for level in ('major', 'minor'):
                    formatter = getattr(axis, f'get_{level}_formatter')()
                    locations = getattr(axis, f'get_{level}ticklocs')()
                    texts = formatter.format_ticks(locations)
                    if any(translate_text(value, language, labels, protected) != value for value in texts):
                        getattr(axis, f'set_{level}_formatter')(DisplayFormatter(formatter))
    changed = 0
    remaining = []
    for artist in fig.findobj(match=Text):
        if not artist.get_visible():
            continue
        before = artist.get_text()
        after = translate_text(before, language, labels, protected)
        if after != before:
            artist.set_text(after)
            changed += 1
        if language == 'en' and _CJK.search(after) and after not in remaining:
            remaining.append(after)
    return {'changed': changed, 'untranslated': remaining[:20]}


_LOCAL_FONTS_READY = False


def _register_local_fonts():
    """Refresh known local fonts once; no download or system installation."""
    global _LOCAL_FONTS_READY
    if _LOCAL_FONTS_READY:
        return
    from pathlib import Path
    import os
    from matplotlib.font_manager import fontManager

    user_fonts = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local')) / 'Microsoft/Windows/Fonts'
    folders = [user_fonts, Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts',
               Path(__file__).resolve().parent / 'fonts', Path(__file__).resolve().parent,
               Path.cwd() / '_utils', Path.cwd() / 'skills/shared-scripts']
    registered = {str(Path(font.fname).resolve()).casefold() for font in fontManager.ttflist}
    for folder in dict.fromkeys(folders):
        if not folder.is_dir():
            continue
        candidates = [*folder.glob('MiSans*.ttf'), *folder.glob('MiSans*.otf'),
                      folder / 'NotoSansSC-Regular.ttf']
        for path in candidates:
            if not path.is_file() or str(path.resolve()).casefold() in registered:
                continue
            try:
                fontManager.addfont(str(path))
                registered.add(str(path.resolve()).casefold())
            except (OSError, RuntimeError, ValueError):
                continue
    # Keep TrueType MiSans faces before legacy OTF duplicates when their
    # matching scores tie. This only orders this process's font catalogue;
    # installed files and explicit font-file choices remain untouched.
    fontManager.ttflist.sort(key=lambda font: 0 if
                             font.name == 'MiSans' and Path(font.fname).suffix.lower() == '.ttf' else 1)
    fontManager._findfont_cached.cache_clear()
    _LOCAL_FONTS_READY = True


def font_candidates(language='zh', family='sans-serif'):
    """Arial for Latin/numerals, MiSans for CJK, preserving deliberate families.

    A concrete string is an explicit user choice. Lists are template fallback
    stacks: legacy defaults such as DejaVu/YaHei/Open Sans cannot precede the
    preferred fonts. Generic serif and deliberate Times-family designs remain
    serif. Only installed fallback fonts are included.
    """
    from matplotlib.font_manager import fontManager

    normalize_language(language)
    _register_local_fonts()
    families = [family] if isinstance(family, str) else list(family or ['sans-serif'])
    families = [name.strip().strip('"\'') for name in families if isinstance(name, str) and name.strip()]
    generic = {'sans-serif', 'serif', 'monospace', 'cursive', 'fantasy'}
    legacy = {'dejavu sans', 'dejavu serif', 'dejavu sans mono', 'open sans', 'verdana', 'tahoma',
              'arial', 'helvetica', 'liberation sans', 'liberation serif', 'noto sans', 'misans',
              'microsoft yahei', 'microsoftyahei', 'simhei', 'simsun', 'pingfang sc', 'heiti sc',
              'stheiti', 'stsong', 'songti sc', 'kaiti', 'fangsong', 'noto sans cjk sc',
              'noto sans sc', 'noto serif cjk sc', 'source han sans sc', 'source han sans cn',
              'wenquanyi micro hei', 'wenquanyi zen hei', 'droid sans fallback', 'arial unicode ms',
              'segoe ui symbol', 'noto sans symbols', 'noto sans symbols 2'}
    explicit = [name for name in families if name.lower() not in generic and
                (isinstance(family, str) or name.lower() not in legacy)]
    serif_names = {'times new roman', 'times', 'cambria', 'georgia', 'palatino linotype',
                   'book antiqua', 'dejavu serif', 'liberation serif', 'stixgeneral',
                   'simsun', 'songti sc', 'stsong', 'noto serif cjk sc', 'source han serif sc'}
    kind = next((name.lower() for name in families if name.lower() in generic), None)
    if kind is None:
        kind = 'serif' if any(name.lower() in serif_names for name in families) else 'sans-serif'
    available = {font.name for font in fontManager.ttflist}
    cjk_sans = ['MiSans', 'Source Han Sans SC', 'Source Han Sans CN', 'Noto Sans CJK SC',
                'Noto Sans SC', 'Microsoft YaHei', 'PingFang SC', 'Heiti SC',
                'WenQuanYi Micro Hei', 'SimHei', 'Arial Unicode MS']
    if kind == 'serif':
        western = ['Times New Roman', 'Times', 'Liberation Serif', 'Noto Serif', 'STIXGeneral']
        cjk = ['Source Han Serif SC', 'Noto Serif CJK SC', 'Songti SC', 'SimSun', 'STSong'] + cjk_sans
        last_resort = ['DejaVu Serif', 'DejaVu Sans']
    elif kind == 'monospace':
        western = ['Consolas', 'Liberation Mono', 'Noto Sans Mono']
        cjk = ['Noto Sans Mono CJK SC'] + cjk_sans
        last_resort = ['DejaVu Sans Mono', 'DejaVu Sans']
    else:
        western = ['Arial', 'Helvetica', 'Liberation Sans', 'Noto Sans']
        cjk = cjk_sans
        last_resort = ['DejaVu Sans']
    symbols = ['Segoe UI Symbol', 'Noto Sans Symbols 2', 'Noto Sans Symbols']
    # Without a preferred Western font, keep the portable Latin face before
    # CJK fallbacks; otherwise those fonts would also take over English text.
    if not any(name in available for name in western):
        western = [last_resort[0]]
    selected = explicit + [name for name in western + cjk + last_resort + symbols if name in available]
    return list(dict.fromkeys(selected or ['DejaVu Serif' if kind == 'serif' else 'DejaVu Sans']))


def apply_figure_fonts(fig, language='zh', family=None):
    """Apply only font families to a Matplotlib or Plotly figure.

    Default calls respect intentional serif/custom fonts and replace inherited
    library defaults. Passing a concrete ``family`` explicitly overrides the
    default policy. Sizes, weights, math fonts, data and layout are untouched.
    """
    normalize_language(language)
    if hasattr(fig, 'to_plotly_json'):
        payload = fig.to_plotly_json()
        layout = payload.get('layout', {})
        inherited = layout.get('font', {}).get('family') or layout.get('template', {}).get('layout', {}).get('font', {}).get('family') or 'sans-serif'

        def stack(value):
            return [part.strip().strip('"\'') for part in value.split(',') if part.strip()] if isinstance(value, str) else value

        def walk(node, parent=''):
            if isinstance(node, dict):
                result = {key: walk(value, key) for key, value in node.items()}
                if parent.endswith('font') and ('family' in node or family is not None):
                    result['family'] = ', '.join(font_candidates(language, family if family is not None else stack(node['family'])))
                return result
            if isinstance(node, list):
                return [walk(item, parent) for item in node]
            return node

        fig.update(walk(payload))
        fig.update_layout(font_family=', '.join(font_candidates(language, family if family is not None else stack(inherited))))
    else:
        from matplotlib.text import Text
        for artist in fig.findobj(match=Text):
            if family is None and artist.get_fontproperties().get_file():
                continue  # An explicitly supplied font file owns this artist.
            artist.set_fontfamily(font_candidates(language, family if family is not None else artist.get_fontfamily()))
    return fig


def localize_plotly(fig, language='zh', labels=None, protected_texts=()):
    """Translate Plotly display properties, keeping all data coordinates intact."""
    language = normalize_language(language)
    labels = _display_labels(labels)
    protected = set(protected_texts)
    result = {'changed': 0, 'untranslated': []}
    source_names = getattr(fig, '_vivid_source_names', {})
    for index, trace in enumerate(fig.data):
        source_names.setdefault(index, trace.name)
    fig._vivid_source_names = source_names
    if language != 'en':
        apply_figure_fonts(fig, language)
        return result

    def text(value):
        if isinstance(value, str):
            translated = translate_text(value, language, labels, protected)
            result['changed'] += translated != value
            if _CJK.search(translated) and translated not in result['untranslated']:
                result['untranslated'].append(translated)
            return translated
        if hasattr(value, 'tolist'):
            value = value.tolist()
        if isinstance(value, (list, tuple)):
            return [text(item) for item in value]
        return value

    def walk(node, parent=''):
        if isinstance(node, dict):
            converted = {}
            for key, value in node.items():
                if key in ('text', 'name', 'ticktext', 'hovertext', 'label'):
                    converted[key] = text(value)
                elif key == 'title' and isinstance(value, str):
                    converted[key] = text(value)
                elif key in ('x', 'y', 'z', 'values', 'customdata', 'ids', 'source', 'target', 'labels', 'parents'):
                    converted[key] = value
                else:
                    converted[key] = walk(value, key)
            return converted
        if isinstance(node, list):
            return [walk(value, parent) for value in node]
        return node

    def label_displays(trace):
        # Tree labels can also be parent identifiers. Never translate those
        # arrays in place: route translated names through display properties.
        if trace.get('type') not in ('sunburst', 'treemap', 'icicle', 'pie'):
            return
        original = trace.get('labels')
        if original is None:
            return
        original = list(original)
        translated = [text(value) for value in original]
        if translated == original:
            return
        template = trace.get('texttemplate')
        existing_text = trace.get('text')

        # With custom text, use per-node templates so notes/hover references to
        # %{text} still point to the original text data. Escape literal labels
        # so an entity name containing '%{value}' cannot become a template.
        from html import escape
        literals = [escape(str(value), quote=False).replace('%', '&#37;') for value in translated]
        if template is not None and len(template) > 0:
            if isinstance(template, str):
                if '%{label}' in template:
                    trace['texttemplate'] = [template.replace('%{label}', value) for value in literals]
            elif any(isinstance(item, str) and '%{label}' in item for item in template):
                trace['texttemplate'] = [
                    item.replace('%{label}', literals[index])
                    if isinstance(item, str) and index < len(literals) else item
                    for index, item in enumerate(template)
                ]
            return
        info = trace.get('textinfo')
        if info is None:
            info = 'label+percent' if trace.get('type') == 'pie' else 'label+text'
        fields = info.split('+')
        if 'label' not in fields:
            return
        if existing_text is None or (isinstance(existing_text, (list, tuple)) and not existing_text):
            trace['text'] = translated
            trace['textinfo'] = '+'.join(dict.fromkeys('text' if field == 'label' else field for field in fields))
            return
        tokens = {'text': '%{text}', 'value': '%{value}', 'percent': '%{percent:.0%}',
                  'current path': '%{currentPath}', 'percent root': '%{percentRoot:.0%}',
                  'percent entry': '%{percentEntry:.0%}', 'percent parent': '%{percentParent:.0%}'}
        trace['texttemplate'] = ['<br>'.join(value if field == 'label' else tokens[field]
                                             for field in fields) for value in literals]

    payload = walk(fig.to_plotly_json())
    for trace in payload.get('data', []):
        label_displays(trace)
    for frame in payload.get('frames', []):
        for trace in frame.get('data', []):
            label_displays(trace)
    fig.update(payload)
    apply_figure_fonts(fig, language)
    result['untranslated'] = result['untranslated'][:20]
    return result
