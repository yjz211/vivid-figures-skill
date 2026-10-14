"""Behavior checks for the radar-ridgeline fusion recipe."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'catalog/sources/advanced.radar_ridgeline/original.py'
spec = importlib.util.spec_from_file_location('radar_ridgeline', SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RadarRidgelineTests(unittest.TestCase):
    def test_two_and_four_layers_render_on_one_polar_axis(self):
        categories = ['A', 'B', 'C', 'D', 'E', 'F']
        for layer_count in (2, 4):
            with self.subTest(layer_count=layer_count):
                values = np.arange(layer_count * len(categories), dtype=float).reshape(layer_count, -1)
                fig = module.plot_chart(categories, [f'L{i}' for i in range(layer_count)], values,
                                        value_suffix='', value_format='.0f')
                self.assertEqual(len(fig.axes), 1)
                self.assertEqual(fig.axes[0].name, 'polar')
                self.assertEqual(len(fig.axes[0].collections), layer_count)
                self.assertEqual([text.get_text() for text in fig.axes[0].get_legend().get_texts()],
                                 [f'L{i}' for i in range(layer_count)])
                plt.close(fig)

    def test_rejects_unreadable_layer_or_category_counts(self):
        with self.assertRaises(ValueError):
            module.plot_chart(['A', 'B', 'C', 'D'], ['L1', 'L2'], np.ones((2, 4)))
        with self.assertRaises(ValueError):
            module.plot_chart(list('ABCDEF'), list('12345'), np.ones((5, 6)))

    def test_wide_csv_preserves_labels_and_orientation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'values.csv'
            path.write_text('category,甲,乙\n精度,1,2\n效率,3,4\n稳定,5,6\n响应,7,8\n成本,9,10\n', encoding='utf-8')
            categories, layers, values = module.read_wide_csv(path)
            self.assertEqual(categories, ['精度', '效率', '稳定', '响应', '成本'])
            self.assertEqual(layers, ['甲', '乙'])
            np.testing.assert_array_equal(values, [[1, 3, 5, 7, 9], [2, 4, 6, 8, 10]])


if __name__ == '__main__':
    unittest.main()
