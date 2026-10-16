"""Language changes affect display text/fonts, never data or template geometry."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

SHARED = Path(__file__).resolve().parents[1] / 'original/resources/assets/shared-scripts'
sys.path.insert(0, str(SHARED))
import vivid_config as vc
from figure_language import font_candidates, localize_figure, localize_plotly, translate_text


class LanguageConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='vivid-language-')
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_language_default_roundtrip_and_labels(self):
        self.assertEqual(vc.load_config(self.root)['language'], 'zh')
        vc.write_config(self.root, language='en', english_labels={'数据组': 'Cohort'})
        self.assertEqual(vc.load_config(self.root)['language'], 'en')
        self.assertEqual(vc.load_config(self.root)['english_labels'], {'数据组': 'Cohort'})

    def test_invalid_language_or_labels_preserve_valid_file(self):
        vc.write_config(self.root, language='en')
        path = self.root / '.vivid/config.json'
        before = path.read_bytes()
        for updates in ({'language': 'de'}, {'language': []}, {'english_labels': []},
                        {'english_labels': {'a': 7}}):
            with self.subTest(updates=updates), self.assertRaises(ValueError):
                vc.write_config(self.root, **updates)
            self.assertEqual(path.read_bytes(), before)

    def test_invalid_stored_language_is_rejected(self):
        (self.root / '.vivid').mkdir()
        (self.root / '.vivid/config.json').write_text('{"language": "English"}', encoding='utf-8')
        with self.assertRaises(ValueError):
            vc.load_config(self.root)

    def test_setup_style_reads_english_and_never_installs_chinese(self):
        import plot_utils as pu
        vc.write_config(self.root, language='en')
        output = io.StringIO()
        with mock.patch.dict(os.environ, {'VIVID_WORKSPACE': str(self.root)}), \
             mock.patch('platform.system', return_value='Linux'), \
             mock.patch('subprocess.run', side_effect=AssertionError('must not install')), \
             matplotlib.rc_context(), contextlib.redirect_stdout(output):
            pu.setup_style(font_family='serif')
            self.assertEqual(matplotlib.rcParams['font.family'], font_candidates('en', 'serif'))
            self.assertIn('DejaVu Serif', matplotlib.rcParams['font.serif'])
            pu.setup_style(font_family='DejaVu Serif')
            self.assertEqual(matplotlib.rcParams['font.family'][0], 'DejaVu Serif')
        self.assertNotIn('Chinese font', output.getvalue())


class DisplayLanguageTests(unittest.TestCase):
    def tearDown(self):
        plt.close('all')

    def test_exact_words_and_bounded_numeric_annotation(self):
        self.assertEqual(translate_text('相关系数', 'en'), 'Correlation')
        self.assertEqual(translate_text('均值 84.6', 'en'), 'Mean 84.6')
        self.assertEqual(translate_text('最大值：-3.8e+2', 'en'), 'Maximum:-3.8e+2')
        self.assertEqual(translate_text('方法A', 'en'), 'Method A')
        self.assertEqual(translate_text('标准化残差', 'en'), 'Standardized residual')
        self.assertEqual(translate_text('列聚类', 'en'), 'Column clustering')
        self.assertEqual(translate_text('轮廓系数 = 0.156', 'en'), 'Silhouette score = 0.156')
        self.assertEqual(translate_text('轮廓系数 = 0.156 dataset', 'en'), '轮廓系数 = 0.156 dataset')
        for text in ('年份调整后', '均值控制组', '均值 12 data', '$\\alpha$', 'μm', 'NaCl'):
            self.assertEqual(translate_text(text, 'en'), text)

    def test_explicit_display_labels_override_protection(self):
        self.assertEqual(translate_text('均值', 'en', protected_texts={'均值'}), '均值')
        self.assertEqual(translate_text('均值', 'en', {'均值': 'Mean cohort'}, {'均值'}), 'Mean cohort')
        self.assertEqual(translate_text('组名', 'en', {'组名': 'Study cohort'}), 'Study cohort')
        self.assertEqual(translate_text('得分', 'zh', {'得分': 'Score'}), '得分')

    def test_localization_preserves_artists_geometry_and_font(self):
        fig, ax = plt.subplots()
        line, = ax.plot([0, 1], [3, 7], label='本文方法', linewidth=3.25)
        bars = ax.bar([0, 1], [1, 2], alpha=.3)
        ax.set_xlabel('年份')
        ax.set_ylabel('得分')
        annotation = ax.text(.5, .7, '均值 5.0', transform=ax.transAxes,
                             rotation=20, fontfamily='DejaVu Serif')
        ax.legend()
        position, limits = ax.get_position().bounds, (ax.get_xlim(), ax.get_ylim())
        vertices = [(bar.get_xy(), bar.get_width(), bar.get_height(), bar.get_alpha()) for bar in bars]
        result = localize_figure(fig, 'en')
        self.assertGreaterEqual(result['changed'], 4)
        self.assertEqual(result['untranslated'], [])
        self.assertEqual(ax.get_xlabel(), 'Year')
        self.assertEqual(ax.get_ylabel(), 'Score')
        self.assertEqual(annotation.get_text(), 'Mean 5.0')
        self.assertEqual(annotation.get_fontfamily(), ['DejaVu Serif'])
        self.assertEqual(annotation.get_rotation(), 20)
        self.assertEqual(ax.get_position().bounds, position)
        self.assertEqual((ax.get_xlim(), ax.get_ylim()), limits)
        self.assertEqual(vertices, [(bar.get_xy(), bar.get_width(), bar.get_height(), bar.get_alpha()) for bar in bars])
        self.assertEqual(line.get_linewidth(), 3.25)
        np.testing.assert_array_equal(line.get_ydata(), [3, 7])

    def test_colorbar_legend_and_visible_leftovers(self):
        fig, ax = plt.subplots()
        image = ax.imshow(np.eye(2))
        colorbar = fig.colorbar(image, ax=ax, label='相关系数')
        ax.text(0, 0, '客户原名')
        ax.text(0, 1, '隐藏文字', visible=False)
        result = localize_figure(fig, 'en', protected_texts={'客户原名'})
        self.assertEqual(colorbar.ax.get_ylabel(), 'Correlation')
        self.assertEqual(result['untranslated'], ['客户原名'])

    def test_default_chinese_does_not_mutate_text(self):
        fig, ax = plt.subplots()
        ax.set_xlabel('年份')
        self.assertEqual(localize_figure(fig), {'changed': 0, 'untranslated': []})
        self.assertEqual(ax.get_xlabel(), '年份')

    def test_tick_translation_survives_redraw_without_changing_locations(self):
        from matplotlib.ticker import FixedFormatter, FixedLocator
        fig, ax = plt.subplots()
        ax.set_xticks([0, 1], ['特征A', '客户原名'])
        ax.yaxis.set_major_locator(FixedLocator([0, 1]))
        ax.yaxis.set_major_formatter(FixedFormatter(['方法A', '方法B']))
        xlocator, ylocator = ax.xaxis.get_major_locator(), ax.yaxis.get_major_locator()
        localize_figure(fig, 'en', labels={'客户原名': 'Cohort'}, protected_texts={'客户原名'})
        fig.canvas.draw()
        self.assertEqual([t.get_text() for t in ax.get_xticklabels()], ['Feature A', 'Cohort'])
        self.assertEqual([t.get_text() for t in ax.get_yticklabels()], ['Method A', 'Method B'])
        self.assertIs(ax.xaxis.get_major_locator(), xlocator)
        self.assertIs(ax.yaxis.get_major_locator(), ylocator)

    def test_font_family_fallbacks_and_explicit_choice(self):
        self.assertIn('DejaVu Serif', font_candidates('en', 'serif'))
        self.assertIn('DejaVu Sans', font_candidates('en', 'sans-serif'))
        self.assertEqual(font_candidates('en', 'Custom Research Font')[0], 'Custom Research Font')
        self.assertEqual(font_candidates('en', ['DejaVu Serif', 'serif'])[0], font_candidates('en', 'serif')[0])
        self.assertNotEqual(font_candidates('en')[0], 'SimHei')
        self.assertEqual(font_candidates('en', ['Microsoft YaHei', 'DejaVu Sans'])[0], font_candidates('en')[0])
        self.assertIn('DejaVu Serif', font_candidates('en', ['SimSun', 'serif']))

    def test_plotly_display_only_preserves_coordinates_and_customdata(self):
        try:
            import plotly.graph_objects as go
        except ImportError:
            self.skipTest('Plotly is an optional renderer')
        fig = go.Figure(go.Scatter(x=['特征A', '特征B'], y=[3, 7], name='本文方法',
                                  text=np.array(['均值 3.0', '客户原名']),
                                  customdata=[['均值'], ['中文原始数据']]))
        fig.update_layout(xaxis_title='年份', yaxis_title='得分',
                          font_family='Microsoft YaHei, DejaVu Sans',
                          title={'text': '方案对比', 'font': {'family': 'Times New Roman, serif'}})
        coordinates = tuple(fig.data[0].x), tuple(fig.data[0].y)
        custom = fig.data[0].customdata
        report = localize_plotly(fig, 'en', {'客户原名': 'Cohort'}, {'客户原名'})
        self.assertEqual((tuple(fig.data[0].x), tuple(fig.data[0].y)), coordinates)
        self.assertEqual(fig.data[0].customdata, custom)
        self.assertEqual(fig.data[0].name, 'Our method')
        self.assertEqual(tuple(fig.data[0].text), ('Mean 3.0', 'Cohort'))
        self.assertEqual(fig.layout.xaxis.title.text, 'Year')
        self.assertTrue(fig.layout.font.family.startswith(font_candidates('en')[0]))
        self.assertTrue(fig.layout.title.font.family.startswith('Times New Roman'))
        self.assertEqual(report['untranslated'], [])


    def test_source_text_identity_is_saved_before_any_translation(self):
        fig, ax = plt.subplots()
        ax.plot([0, 1], [2, 3], label='本文方法')
        ax.set_xticks([0, 1], ['均值', '中位数'])
        note = ax.text(.3, .4, '均值')
        ax.legend()
        localize_figure(fig, 'en')
        fig.canvas.draw()
        self.assertEqual(note._vivid_source_text, '均值')
        self.assertEqual(note.get_text(), 'Mean')
        self.assertEqual(ax.get_xticklabels()[0]._vivid_source_text, '均值')
        self.assertEqual(ax.get_legend().texts[0]._vivid_source_text, '本文方法')
        localize_figure(fig, 'en')
        self.assertEqual(note._vivid_source_text, '均值')

    def test_english_font_stack_has_available_chinese_fallback_after_western(self):
        from types import SimpleNamespace
        available = [SimpleNamespace(name=name) for name in
                     ['DejaVu Sans', 'DejaVu Serif', 'Microsoft YaHei', 'SimSun']]
        with mock.patch('figure_language._register_local_fonts'), \
             mock.patch('matplotlib.font_manager.fontManager.ttflist', available):
            sans = font_candidates('en')
            serif = font_candidates('en', 'serif')
        self.assertLess(sans.index('DejaVu Sans'), sans.index('Microsoft YaHei'))
        self.assertLess(serif.index('DejaVu Serif'), serif.index('SimSun'))
        # On hosts with a Chinese font, exercise the real glyph fallback.
        names = font_candidates('en')
        if 'Microsoft YaHei' in names or 'Noto Sans CJK SC' in names:
            import warnings
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                fig, ax = plt.subplots()
                ax.text(.5, .5, '北京交通站', fontfamily=names)
                fig.canvas.draw()
            self.assertFalse(any('Glyph' in str(item.message) and 'missing' in str(item.message)
                                 for item in caught))

    def test_plotly_original_names_survive_and_are_not_serialized(self):
        try:
            import plotly.graph_objects as go
        except ImportError:
            self.skipTest('Plotly is an optional renderer')
        fig = go.Figure(go.Scatter(x=[0, 1], y=[2, 3], name='本文方法'))
        localize_plotly(fig, 'zh')
        self.assertEqual(fig._vivid_source_names, {0: '本文方法'})
        localize_plotly(fig, 'en')
        self.assertEqual(fig._vivid_source_names, {0: '本文方法'})
        self.assertEqual(fig.data[0].name, 'Our method')
        self.assertNotIn('_vivid_source_names', fig.to_plotly_json())


    def test_sunburst_translates_display_without_changing_tree_identifiers(self):
        try:
            import plotly.graph_objects as go
        except ImportError:
            self.skipTest('Plotly is an optional renderer')
        labels = ['总体', '实验组', '北京交通站']
        parents = ['', '总体', '总体']
        fig = go.Figure(go.Sunburst(labels=labels, parents=parents, ids=['r', 'a', 'b'],
                                   values=[10, 6, 4], textinfo='label+percent parent'))
        report = localize_plotly(fig, 'en', {'总体': 'Total', '实验组': 'Treatment'})
        trace = fig.data[0]
        self.assertEqual(list(trace.labels), labels)
        self.assertEqual(list(trace.parents), parents)
        self.assertEqual(list(trace.ids), ['r', 'a', 'b'])
        self.assertEqual(list(trace.values), [10, 6, 4])
        self.assertEqual(list(trace.text), ['Total', 'Treatment', '北京交通站'])
        self.assertEqual(trace.textinfo, 'text+percent parent')
        self.assertEqual(report['untranslated'], ['北京交通站'])

    def test_treemap_keeps_custom_text_hover_and_percentage_template(self):
        try:
            import plotly.graph_objects as go
        except ImportError:
            self.skipTest('Plotly is an optional renderer')
        fig = go.Figure(go.Treemap(labels=['总体', '实验组'], parents=['', '总体'],
                                  values=[10, 10], text=['Root note', 'Group note'],
                                  texttemplate='%{label}<br>%{text}<br>%{percentParent:.1%}',
                                  hovertemplate='Exact hover: %{label} | %{text}<extra></extra>'))
        hover = fig.data[0].hovertemplate
        localize_plotly(fig, 'en', {'总体': 'Total', '实验组': 'Treatment'})
        trace = fig.data[0]
        self.assertEqual(list(trace.labels), ['总体', '实验组'])
        self.assertEqual(list(trace.parents), ['', '总体'])
        self.assertEqual(list(trace.text), ['Root note', 'Group note'])
        self.assertEqual(trace.hovertemplate, hover)
        self.assertEqual(list(trace.texttemplate), [
            'Total<br>%{text}<br>%{percentParent:.1%}',
            'Treatment<br>%{text}<br>%{percentParent:.1%}'])

    def test_pie_keeps_percent_and_existing_notes(self):
        try:
            import plotly.graph_objects as go
        except ImportError:
            self.skipTest('Plotly is an optional renderer')
        for notes in (None, ['First note', 'Second note']):
            with self.subTest(notes=notes):
                fig = go.Figure(go.Pie(labels=['实验组', '对照组'], values=[6, 4],
                                      text=notes, textinfo='label+text+percent'))
                localize_plotly(fig, 'en')
                trace = fig.data[0]
                self.assertEqual(list(trace.labels), ['实验组', '对照组'])
                self.assertEqual(list(trace.values), [6, 4])
                if notes is None:
                    self.assertEqual(list(trace.text), ['Treatment', 'Control'])
                    self.assertEqual(trace.textinfo, 'text+percent')
                else:
                    self.assertEqual(list(trace.text), notes)
                    self.assertEqual(list(trace.texttemplate), [
                        'Treatment<br>%{text}<br>%{percent:.0%}',
                        'Control<br>%{text}<br>%{percent:.0%}'])

    def test_label_trace_respects_custom_template_without_label_and_reports_unknown(self):
        try:
            import plotly.graph_objects as go
        except ImportError:
            self.skipTest('Plotly is an optional renderer')
        fig = go.Figure(go.Treemap(labels=['实验组', '未知专名'], parents=['', '实验组'],
                                  text=['First', 'Second'], texttemplate='%{text}', values=[4, 4]))
        report = localize_plotly(fig, 'en')
        self.assertEqual(list(fig.data[0].text), ['First', 'Second'])
        self.assertEqual(fig.data[0].texttemplate, '%{text}')
        self.assertEqual(report['untranslated'], ['未知专名'])


    def test_dynamic_numeric_annotations_keep_values_and_display_structure(self):
        examples = {
            '95% 跨度\n12.4': '95% span\n12.4',
            '90.5% 跨度\n3.7e+2': '90.5% span\n3.7e+2',
            '拐点\n(x=-2.5)': 'Turning point\n(x=-2.5)',
            '自给率 = 49.1%   进口依赖 = 50.9%': 'Self-sufficiency = 49.1%   Import dependence = 50.9%',
            '峰值 18.3%': 'Peak 18.3%',
            '临界螺距 0.47': 'Critical pitch 0.47',
            '起点 (2010)': 'Start (2010)',
            '终点 (2024)': 'End (2024)',
            '平均轮廓系数=0.427': 'Mean silhouette score=0.427',
            '最优点 (−1.2, 3.0)': 'Optimum (−1.2, 3.0)',
            '基准±10% (0.045~0.055)': 'Baseline±10% (0.045~0.055)',
            '高高聚集 (5)': 'High–high cluster (5)',
            '低低聚集 (7)': 'Low–low cluster (7)',
            '低高异常 (2)': 'Low–high outlier (2)',
            '高低异常 (3)': 'High–low outlier (3)',
            '不显著 (17)': 'Not significant (17)',
            'LISA 聚类 (p < 0.05)': 'LISA clusters (p < 0.05)',
        }
        for original, english in examples.items():
            with self.subTest(original=original):
                self.assertEqual(translate_text(original, 'en'), english)
                self.assertEqual(translate_text(original, 'zh'), original)

    def test_dynamic_numeric_annotations_respect_mapping_protection_and_boundaries(self):
        source = '自给率 = 63.4%   进口依赖 = 36.6%'
        self.assertEqual(translate_text(source, 'en', protected_texts={source}), source)
        self.assertEqual(translate_text(source, 'en', {source: 'User caption'}, {source}), 'User caption')
        for value in ('Text 峰值 3.0%', '峰值 3.0% extra', '95% 跨度\n12.3\n备注',
                      '拐点\n(x=method)', '终点 (May 2024)', '高高聚集 (5) 站点',
                      '最优点 (1.0, 2.0, 3.0)', 'LISA 聚类 (p < threshold)',
                      '流量不守恒：source 合计 3000 ≠ target 合计 2900'):
            with self.subTest(value=value):
                self.assertEqual(translate_text(value, 'en'), value)

    def test_known_label_with_numeric_tail_is_translated_as_one_bounded_format(self):
        labels = {'俄罗斯': 'Russia', '总供给 = 需求 (万 m³)': 'Total supply = demand (10⁴ m³)'}
        for original, expected in {
            '俄罗斯\n1500': 'Russia\n1500',
            '总供给 = 需求 (万 m³)\n3000': 'Total supply = demand (10⁴ m³)\n3000',
            '训练集\n600': 'Training set\n600',
            '类别A\n35% (+3%)': 'Category A\n35% (+3%)',
            '类别B\n21% (-2.5%)': 'Category B\n21% (-2.5%)',
        }.items():
            with self.subTest(original=original):
                self.assertEqual(translate_text(original, 'en', labels), expected)
        for original in ('未知实体\n30%', '训练集\n600 names', '训练集\n600\n测试集', '训练集\nother words'):
            self.assertEqual(translate_text(original, 'en', labels), original)
        protected = '类别A\n35% (+3%)'
        self.assertEqual(translate_text(protected, 'en', {'类别A': 'Metric'}, {'类别A'}), protected)
        self.assertEqual(translate_text(protected, 'en', {protected: 'Whole custom label'}, {'类别A'}), 'Whole custom label')


    def test_known_label_percentage_pipe_value_keeps_both_numbers(self):
        labels = {'类别1': 'Category 1', '子类A-1': 'Subgroup A-1'}
        for original, expected in {
            '类别1\n6.7% | 30': 'Category 1\n6.7% | 30',
            '类别A\n69.6% | 220': 'Category A\n69.6% | 220',
            '子类A-1\n31.6% | 100': 'Subgroup A-1\n31.6% | 100',
        }.items():
            self.assertEqual(translate_text(original, 'en', labels), expected)
            self.assertEqual(translate_text(original, 'zh', labels), original)
        for original in ('类别A\n31.6 | 100', '类别A\n31.6% | notes',
                         '类别A\n31.6% | 100 | 2', '类别A\n31.6% | 100\n备注',
                         '未知实体\n31.6% | 100'):
            self.assertEqual(translate_text(original, 'en', labels), original)
        original = '子类A-1\n31.6% | 100'
        self.assertEqual(translate_text(original, 'en', labels, {'子类A-1'}), original)
        self.assertEqual(translate_text(original, 'en', {original: 'Custom label'}, {'子类A-1'}), 'Custom label')


if __name__ == '__main__':
    unittest.main()
