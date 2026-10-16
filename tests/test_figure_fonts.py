"""Font policy changes family only and keeps user/template typography intent."""
from pathlib import Path
import copy
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import warnings

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np

SHARED = Path(__file__).resolve().parents[1] / 'original/resources/assets/shared-scripts'
sys.path.insert(0, str(SHARED))
import figure_language as fl
import plot_utils as pu


class FontPolicyTests(unittest.TestCase):
    def tearDown(self):
        plt.close('all')

    def test_legacy_stacks_use_selected_defaults_and_keep_serif(self):
        names = ['Arial', 'MiSans', 'Times New Roman', 'SimSun', 'Microsoft YaHei',
                 'DejaVu Sans', 'DejaVu Serif', 'Open Sans', 'Segoe UI Symbol']
        with mock.patch.object(fl, '_register_local_fonts'), mock.patch.object(
                font_manager.fontManager, 'ttflist', [SimpleNamespace(name=name) for name in names]):
            for language in ('zh', 'en'):
                for stack in (['sans-serif', 'Microsoft YaHei', 'DejaVu Sans'],
                              ['Microsoft YaHei', 'SimHei', 'DejaVu Sans'],
                              ['Open Sans', 'Verdana', 'Arial', 'sans-serif']):
                    self.assertEqual(fl.font_candidates(language, stack)[:2], ['Arial', 'MiSans'])
                for stack in (['serif', 'Microsoft YaHei', 'DejaVu Sans'],
                              ['DejaVu Serif', 'serif'], ['Times New Roman', 'DejaVu Serif']):
                    self.assertEqual(fl.font_candidates(language, stack)[0], 'Times New Roman')
                self.assertEqual(fl.font_candidates(language, 'DejaVu Serif')[0], 'DejaVu Serif')
                self.assertEqual(fl.font_candidates(language, 'Custom Research Font')[0], 'Custom Research Font')

    def test_portable_western_fallback_precedes_chinese(self):
        names = ['DejaVu Sans', 'DejaVu Serif', 'MiSans', 'SimSun']
        with mock.patch.object(fl, '_register_local_fonts'), mock.patch.object(
                font_manager.fontManager, 'ttflist', [SimpleNamespace(name=name) for name in names]):
            self.assertEqual(fl.font_candidates('en')[0], 'DejaVu Sans')
            self.assertEqual(fl.font_candidates('zh', 'serif')[0], 'DejaVu Serif')

    def test_misans_is_registered_from_existing_files_once(self):
        # Simulate an installed local file absent from Matplotlib's old cache.
        with tempfile.TemporaryDirectory(prefix='vivid-font-registration-') as root:
            fonts = Path(root) / 'Fonts'
            fonts.mkdir()
            font_path = fonts / 'MiSans-Regular.otf'
            font_path.write_bytes(b'local-font-fixture')
            with mock.patch.dict('os.environ', {'WINDIR': root}), \
                 mock.patch.object(fl, '_LOCAL_FONTS_READY', False), \
                 mock.patch.object(font_manager.fontManager, 'addfont') as add, \
                 mock.patch('subprocess.run', side_effect=AssertionError('No installation allowed')):
                fl._register_local_fonts()
                fl._register_local_fonts()
            self.assertEqual(sum(Path(call.args[0]) == font_path for call in add.call_args_list), 1)

    def test_matplotlib_preserves_text_geometry_weight_math_and_data(self):
        with matplotlib.rc_context({'mathtext.fontset': 'cm'}):
            fig, ax = plt.subplots(figsize=(5.2, 3.4))
            line, = ax.plot([1, 2, 3], [5, 2, 8], color='#aabbcc', linewidth=3)
            item = ax.text(.2, .8, '中文 + English 123', transform=ax.transAxes,
                           family=['Microsoft YaHei', 'DejaVu Sans'], fontsize=14,
                           fontweight='bold', style='italic', rotation=12)
            serif = ax.text(.2, .5, 'Design', family='Times New Roman', fontsize=11)
            source_file = font_manager.findfont('DejaVu Sans')
            fixed = ax.text(.2, .3, 'File', fontproperties=font_manager.FontProperties(fname=source_file))
            before = (item.get_text(), item.get_position(), item.get_fontsize(), item.get_weight(),
                      item.get_style(), item.get_rotation(), ax.get_position().bounds,
                      ax.get_xlim(), ax.get_ylim(), tuple(fig.get_size_inches()))
            fl.apply_figure_fonts(fig, 'zh')
            after = (item.get_text(), item.get_position(), item.get_fontsize(), item.get_weight(),
                     item.get_style(), item.get_rotation(), ax.get_position().bounds,
                     ax.get_xlim(), ax.get_ylim(), tuple(fig.get_size_inches()))
            self.assertEqual(before, after)
            self.assertEqual(item.get_fontfamily()[0], fl.font_candidates()[0])
            self.assertEqual(serif.get_fontfamily()[0], 'Times New Roman')
            self.assertEqual(fixed.get_fontproperties().get_file(), source_file)
            self.assertEqual(matplotlib.rcParams['mathtext.fontset'], 'cm')
            np.testing.assert_array_equal(line.get_ydata(), [5, 2, 8])
            self.assertEqual(line.get_color(), '#aabbcc')
            self.assertEqual(line.get_linewidth(), 3)

    def test_explicit_family_argument_preserves_requested_choice(self):
        fig, ax = plt.subplots()
        text = ax.text(0, 0, 'My label')
        fl.apply_figure_fonts(fig, family='DejaVu Serif')
        self.assertEqual(text.get_fontfamily()[0], 'DejaVu Serif')

    def test_mixed_zh_en_render_has_no_missing_glyphs(self):
        names = fl.font_candidates()
        if not any(name in names for name in ('MiSans', 'Microsoft YaHei', 'Noto Sans SC', 'Noto Sans CJK SC')):
            self.skipTest('No local Chinese font available')
        for language in ('zh', 'en'):
            with self.subTest(language=language), warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                fig, ax = plt.subplots()
                item = ax.text(.1, .5, '中文默认字体 English 012345 − ± μm', weight='bold')
                fl.apply_figure_fonts(fig, language)
                fig.canvas.draw()
            self.assertFalse([str(item.message) for item in caught
                              if 'Glyph' in str(item.message) and 'missing' in str(item.message)])
            self.assertEqual(item.get_weight(), 'bold')
            if 'MiSans' in names and names[0] == 'Arial':
                self.assertLess(item.get_fontfamily().index('MiSans'), item.get_fontfamily().index('Microsoft YaHei'))

    def test_save_hook_applies_policy_after_late_rc_override(self):
        with matplotlib.rc_context({'font.family': ['Microsoft YaHei', 'DejaVu Sans']}):
            fig, ax = plt.subplots()
            item = ax.text(0, 0, 'Label 123', fontsize=17, weight='bold')
            observed = []
            with mock.patch.object(pu.os, 'makedirs'), \
                 mock.patch.object(pu, '_warn_if_wasted_margin'), \
                 mock.patch.object(pu, '_warn_if_data_clipped'), \
                 mock.patch.object(pu.vc, 'load_config', return_value={'language': 'en'}), \
                 mock.patch.object(fig, 'savefig', side_effect=lambda *a, **kw: observed.append(item.get_fontfamily())):
                pu._save(fig, 'font-test.png')
            self.assertEqual(observed[0][0], fl.font_candidates('en')[0])
            self.assertEqual(item.get_fontsize(), 17)
            self.assertEqual(item.get_weight(), 'bold')

    def test_plotly_policy_runs_in_both_languages_without_mutating_data(self):
        try:
            import plotly.graph_objects as go
        except ImportError:
            self.skipTest('Plotly is optional')
        for language in ('zh', 'en'):
            with self.subTest(language=language):
                fig = go.Figure(go.Scatter(x=['原始A', '原始B'], y=[2, 9],
                                          customdata=[['中文原始数据'], ['second']],
                                          text=['中文说明', 'English'],
                                          textfont={'family': 'Open Sans, Verdana, Arial', 'size': 16}))
                fig.update_layout(font={'family': 'Microsoft YaHei, DejaVu Sans', 'size': 12},
                                  title={'text': 'Title', 'font': {'family': 'Times New Roman, serif', 'size': 23}},
                                  annotations=[{'text': 'Note', 'x': .2, 'y': .4,
                                                'font': {'family': 'Open Sans', 'size': 11}}])
                before = copy.deepcopy(fig.to_plotly_json())
                report = fl.localize_plotly(fig, language)
                after = fig.to_plotly_json()
                for key in ('x', 'y', 'customdata', 'text'):
                    self.assertEqual(before['data'][0][key], after['data'][0][key])
                preferred = fl.font_candidates(language)[0]
                self.assertTrue(fig.layout.font.family.startswith(preferred))
                self.assertTrue(fig.data[0].textfont.family.startswith(preferred))
                self.assertTrue(fig.layout.annotations[0].font.family.startswith(preferred))
                self.assertTrue(fig.layout.title.font.family.startswith('Times New Roman'))
                self.assertEqual(fig.layout.title.font.size, 23)
                self.assertEqual(fig.data[0].textfont.size, 16)
                self.assertEqual((fig.layout.annotations[0].x, fig.layout.annotations[0].y), (.2, .4))


    def test_current_user_truetype_faces_precede_legacy_system_otf(self):
        with tempfile.TemporaryDirectory(prefix='vivid-user-fonts-') as root:
            user_root = Path(root) / 'Local'
            user_fonts = user_root / 'Microsoft/Windows/Fonts'
            user_fonts.mkdir(parents=True)
            ttf = user_fonts / 'MiSans-Regular.ttf'
            bold = user_fonts / 'MiSans-Bold.ttf'
            ttf.write_bytes(b'local-font-fixture')
            bold.write_bytes(b'local-font-fixture')
            old_otf = Path(root) / 'MiSans-Regular.otf'
            old_otf.write_bytes(b'legacy-font-fixture')
            entries = [font_manager.FontEntry(fname=str(old_otf), name='MiSans', weight=400)]

            def add_font(path):
                name = 'MiSans' if Path(path).name.startswith('MiSans') else 'Noto Sans SC'
                entries.append(font_manager.FontEntry(fname=path, name=name,
                                                       weight=700 if 'Bold' in path else 400))

            with mock.patch.dict('os.environ', {'LOCALAPPDATA': str(user_root), 'WINDIR': root}), \
                 mock.patch.object(fl, '_LOCAL_FONTS_READY', False), \
                 mock.patch.object(font_manager.fontManager, 'ttflist', entries), \
                 mock.patch.object(font_manager.fontManager, 'addfont', side_effect=add_font):
                fl._register_local_fonts()
                faces = [font for font in entries if font.name == 'MiSans']
                self.assertEqual({Path(font.fname) for font in faces[:2]}, {ttf, bold})
                self.assertEqual(Path(faces[-1].fname), old_otf)
                self.assertEqual(font_manager.fontManager.findfont(
                    font_manager.FontProperties(family=['MiSans'], weight='normal')), str(ttf))
                self.assertEqual(font_manager.fontManager.findfont(
                    font_manager.FontProperties(family=['MiSans'], weight='bold')), str(bold))
                self.assertTrue(old_otf.exists())
            font_manager.fontManager._findfont_cached.cache_clear()

    def test_style_configures_searchable_pdf_and_postscript_fonts(self):
        with matplotlib.rc_context():
            pu.setup_style(language='zh')
            self.assertEqual(matplotlib.rcParams['pdf.fonttype'], 42)
            self.assertEqual(matplotlib.rcParams['ps.fonttype'], 42)


if __name__ == '__main__':
    unittest.main()
