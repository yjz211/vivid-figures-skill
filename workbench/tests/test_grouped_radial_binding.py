"""Grouped radial bars preserve task joins, series order and original source rendering."""
from pathlib import Path
import copy
import runpy
import sys
import unittest

import numpy as np

WEB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WEB / 'editor_backend'))
from schema import Invalid, SPECS, prepare, sample
from agent.tools import bind_template
from engine import adapt, radial_reference_caption

TID = 'advanced.grouped_radial_bar'


def project():
    result = sample(TID)
    result['tables'] = {
        'scores': {'headers': ['任务', '重点模型', '模型乙', '模型甲'],
                   'rows': [['识别', 71, 63, 66], ['版面', 84, 72, 77],
                            ['定位', 55, 61, 58], ['指代', 79, 74, 76]]},
        # Metadata order deliberately differs from score order.
        'labels': {'headers': ['任务', '大类', '说明'],
                   'rows': [['指代', '空间', None], ['版面', '文字', '文档集'],
                            ['识别', '文字', ''], ['定位', '空间', '场景集']]},
    }
    result['active_table'] = 'scores'
    result['table'] = result['tables']['scores']
    return result


class GroupedRadialBinding(unittest.TestCase):
    def test_default_contract_is_registered_and_uses_gallery_palette(self):
        p = sample(TID)
        values, _ = prepare(p)
        self.assertEqual(SPECS[TID]['family'], 'catalog')
        self.assertEqual(p['settings']['palette'], 'pastel-girl')
        self.assertEqual(p['settings']['title'], '')
        self.assertEqual(values['values'].shape, (11, 5))
        self.assertEqual(values['model_names'][0], 'GroundingPI')

    def test_metadata_is_joined_by_task_without_sorting_models_or_scores(self):
        p = project()
        before = copy.deepcopy(p)
        values, _ = prepare(p)
        self.assertEqual(p, before)
        self.assertEqual(values['task_names'], ['识别', '版面', '定位', '指代'])
        self.assertEqual(values['model_names'], ['重点模型', '模型乙', '模型甲'])
        self.assertEqual(values['major_groups'], ['文字', '文字', '空间', '空间'])
        self.assertEqual(values['task_details'], ['', '文档集', '场景集', ''])
        np.testing.assert_array_equal(values['values'], [[71, 63, 66], [84, 72, 77], [55, 61, 58], [79, 74, 76]])

    def test_sample_matches_complete_source_and_adaptation_keeps_function_body(self):
        path = WEB.parent / 'catalog/sources' / TID / 'original.py'
        namespace = runpy.run_path(str(path), run_name='radial_contract_check')
        reference = namespace['demo_data']()
        values, _ = prepare(sample(TID))
        for key in ['task_names', 'model_names', 'major_groups', 'task_details']:
            self.assertEqual(values[key], reference[key])
        np.testing.assert_array_equal(values['values'], reference['values'])
        self.assertEqual(radial_reference_caption(values, reference), reference['baseline_label'])
        source = path.read_text(encoding='utf8')
        self.assertTrue(adapt(TID, source).startswith(source))

    def test_active_sheet_and_label_column_mapping(self):
        p = project()
        p['active_table'] = 'labels'
        p['table'] = {'headers': ['备注', '组别', '任务名称'],
                      'rows': [[r[2], r[1], r[0]] for r in p['tables']['labels']['rows']]}
        p['column_mappings'] = {'labels': [2, 1, 0]}
        values, _ = prepare(p)
        self.assertEqual(values['task_details'], ['', '文档集', '场景集', ''])
        self.assertEqual(values['major_groups'], ['文字', '文字', '空间', '空间'])

    def test_agent_binding_projects_matrix_columns_in_selected_order(self):
        p = project()
        table = {'headers': ['忽略', '模型甲', '任务', '重点模型', '模型乙'],
                 'rows': [['备注', r[3], r[0], r[1], r[2]] for r in p['table']['rows']]}
        datasets = [{'id': 'scores-id', 'table': table}, {'id': 'labels-id', 'table': p['tables']['labels']}]
        bound = bind_template(TID, datasets,
                              [{'table_key': 'scores', 'dataset_id': 'scores-id', 'columns': [2, 3, 4, 1]},
                               {'table_key': 'labels', 'dataset_id': 'labels-id', 'columns': [0, 1, 2]}])
        values, _ = prepare(bound)
        self.assertEqual(values['model_names'], ['重点模型', '模型乙', '模型甲'])
        np.testing.assert_array_equal(values['values'], prepare(p)[0]['values'])
        self.assertEqual(datasets[0]['table'], table)

    def test_duplicate_missing_and_extra_tasks_are_rejected(self):
        for change in ['duplicate-score', 'duplicate-label', 'missing-label', 'extra-label']:
            with self.subTest(change=change):
                p = project()
                if change == 'duplicate-score':
                    p['table']['rows'][1][0] = p['table']['rows'][0][0]
                elif change == 'duplicate-label':
                    p['tables']['labels']['rows'][1][0] = p['tables']['labels']['rows'][0][0]
                elif change == 'missing-label':
                    p['tables']['labels']['rows'].pop()
                else:
                    p['tables']['labels']['rows'].append(['额外任务', '空间', ''])
                with self.assertRaises(Invalid):
                    prepare(p)

    def test_noncontiguous_or_empty_major_groups_are_rejected(self):
        for group in ['文字', '']:
            p = project()
            p['tables']['labels']['rows'][0][1] = group
            with self.assertRaises(Invalid):
                prepare(p)

    def test_values_are_nonnegative_finite_and_not_imputed(self):
        for bad in [-0.01, None, '', True, float('inf'), float('nan')]:
            with self.subTest(value=bad):
                p = project()
                p['table']['rows'][0][1] = bad
                with self.assertRaises(Invalid):
                    prepare(p)
        p = project()
        p['table']['rows'][0][1] = 0
        self.assertEqual(prepare(p)[0]['values'][0, 0], 0)

    def test_chart_limits_and_highlight_are_checked(self):
        for tasks, models in [(1, 3), (17, 3), (4, 1), (4, 9), (16, 7)]:
            with self.subTest(tasks=tasks, models=models):
                p = project()
                p['table']['headers'] = ['任务'] + [f'模型{i}' for i in range(models)]
                p['table']['rows'] = [[f'任务{i}'] + [1] * models for i in range(tasks)]
                p['tables']['labels']['rows'] = [[f'任务{i}', '同一类', ''] for i in range(tasks)]
                with self.assertRaises(Invalid):
                    prepare(p)
        for bad in [-1, 3, '0', True]:
            p = project()
            p['settings']['highlight'] = bad
            with self.assertRaises(Invalid):
                prepare(p)


    def test_reference_baseline_claim_is_removed_after_real_data_changes(self):
        values, _ = prepare(project())
        reference = copy.deepcopy(values)
        reference['baseline_label'] = 'Best Four models\nAcross 45 Baselines\nIncluding GPT-6 Astra'
        self.assertEqual(radial_reference_caption(values, reference), reference['baseline_label'])
        changed = copy.deepcopy(values)
        changed['settings']['title'] = '更换标题仍是同一份参考数据'
        changed['settings']['palette'] = 'blue-sky'
        self.assertEqual(radial_reference_caption(changed, reference), reference['baseline_label'])
        changed['values'][0, 0] += .01
        self.assertIsNone(radial_reference_caption(changed, reference))
        changed = copy.deepcopy(values)
        changed['highlight_index'] = 1
        self.assertIsNone(radial_reference_caption(changed, reference))
        for key in ['task_names', 'model_names', 'major_groups', 'task_details']:
            changed = copy.deepcopy(values)
            changed[key][0] = '新的内容'
            self.assertIsNone(radial_reference_caption(changed, reference), key)


if __name__ == '__main__':
    unittest.main()
