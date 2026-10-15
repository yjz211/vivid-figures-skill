"""Data integrity and hierarchy checks for grouped radial bars."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'catalog/sources/advanced.grouped_radial_bar/original.py'
spec = importlib.util.spec_from_file_location('grouped_radial_bar', SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class GroupedRadialBarTests(unittest.TestCase):
    def tearDown(self):
        plt.close('all')

    def test_preserves_actual_bar_heights_and_series_order(self):
        values = np.array([[0, 3, 9], [2, 8, 4], [7, 1, 6]])
        fig = module.plot_chart(['甲', '乙', '丙'], ['模型丙', '模型甲', '模型乙'], values,
                                major_groups=['一类', '一类', '二类'], highlight_index=1,
                                scale_mode='shared', scale_max=300)
        ax = fig.axes[0]
        self.assertEqual(ax.name, 'polar')
        np.testing.assert_array_equal([bar.get_height() for bar in ax.patches], values.ravel())
        self.assertEqual([t.get_text() for t in fig.legends[0].get_texts()], ['模型丙', '模型甲', '模型乙'])
        self.assertEqual(len({bar.get_y() for bar in ax.patches}), 1)
        self.assertEqual(len(ax.lines), 2)

    def test_rejects_missing_negative_nonfinite_and_wrong_shape(self):
        for values in ([[1, -1], [2, 3]], [[1, np.nan], [2, 3]],
                       [[1, np.inf], [2, 3]], [[1, 2, 3], [4, 5, 6]]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                module.plot_chart(['甲', '乙'], ['A', 'B'], values)

    def test_rejects_noncontiguous_hierarchy_and_undersized_scale(self):
        with self.assertRaisesRegex(ValueError, 'contiguous'):
            module.plot_chart(list('ABC'), list('XY'), np.ones((3, 2)), ['甲', '乙', '甲'])
        with self.assertRaisesRegex(ValueError, 'scale_max'):
            module.plot_chart(list('AB'), list('XY'), [[1, 9], [2, 3]], scale_max=5, scale_mode='shared')

    def test_zero_data_and_visibility_toggles_do_not_remove_tasks(self):
        fig = module.plot_chart(['甲任务', '乙任务'], ['A', 'B'], np.zeros((2, 2)),
                                show_values=False, show_legend=False)
        self.assertEqual(len(fig.axes[0].patches), 4)
        text = [item.get_text() for item in fig.axes[0].texts]
        self.assertIn('甲任务', text)
        self.assertIn('乙任务', text)
        self.assertEqual(fig.legends, [])

    def test_limits_and_maximum_supported_shape(self):
        fig = module.plot_chart([str(i) for i in range(12)], [str(i) for i in range(8)], np.ones((12, 8)))
        self.assertEqual(len(fig.axes[0].patches), 96)
        with self.assertRaisesRegex(ValueError, '96'):
            module.plot_chart([str(i) for i in range(16)], [str(i) for i in range(8)], np.ones((16, 8)))

    def test_reference_has_55_original_values_and_explicit_task_scaling(self):
        data = module.demo_data()
        self.assertEqual(data['values'].shape, (11, 5))
        fig = module.plot_chart(**data)
        ax = fig.axes[0]
        lengths = np.array([bar.get_height() for bar in ax.patches]).reshape(11, 5)
        np.testing.assert_allclose(lengths.min(axis=1), 100)
        np.testing.assert_allclose(lengths.max(axis=1), 300)
        self.assertEqual(len(ax.lines), 3)
        actual_labels = [t.get_text() for t in ax.texts[:55]]
        self.assertEqual(actual_labels, [f'{v:.2f}' for v in data['values'].ravel()])
        self.assertEqual(data['model_names'][1], 'Top 1 baseline')
        self.assertIn('Within', module.plot_chart.__doc__.title())

    def test_csv_metadata_joins_by_name_without_sorting(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / 'scores.csv').write_text('任务,模型乙,模型甲\n乙,2,8\n甲,9,3\n', encoding='utf-8')
            (path / 'labels.csv').write_text('任务,大类,说明\n甲,组二,描述甲\n乙,组一,\n', encoding='utf-8')
            tasks, models, values = module.read_wide_csv(path / 'scores.csv')
            groups, details = module.read_metadata_csv(path / 'labels.csv', tasks)
            self.assertEqual(tasks, ['乙', '甲'])
            self.assertEqual(models, ['模型乙', '模型甲'])
            self.assertEqual(groups, ['组一', '组二'])
            self.assertEqual(details, ['', '描述甲'])
            np.testing.assert_array_equal(values, [[2, 8], [9, 3]])


if __name__ == '__main__':
    unittest.main()
