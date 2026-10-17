"""Regressions for edited SVG canvases, object keys and customized part registries.

Run with ``python tests/test_source_asset_runtime.py``.
"""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'architecture/lib'))
import source_asset


class SourceAssetRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.recipe = Path(self.tmp.name) / 'recipe'
        self.recipe.mkdir()
        (self.recipe / 'diagram.svg').write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50">'
            '<metadata id="legacy-metadata">Existing source metadata</metadata>'
            '<defs><marker id="arrow"><path d="M0 0 L2 1 L0 2Z"/></marker></defs>'
            '<rect id="original-box" x="10" y="10" width="60" height="20"/>'
            '<text id="original-label" x="20" y="25" font-family="Arial" '
            'font-size="12">Original label</text></svg>', encoding='utf-8')
        source_asset.write(self.recipe / 'asset.json', {
            'id': 'test.canvas', 'name': 'Canvas fixture',
            'parts': [{'id': 'main', 'name': 'Main', 'box': [0, 0, 1, 1]}],
        })
        source_asset.write(self.recipe / 'geometry.json', {
            'viewBox': [0, 0, 100, 50],
            'elements': [
                {'key': 'e0001', 'tag': 'rect', 'visible': True,
                 'bounds': [10, 10, 60, 20]},
                {'key': 'e0002', 'tag': 'text', 'visible': True,
                 'bounds': [20, 13, 45, 12]},
            ],
        })
        self.config = {'palette': 'original', 'print_width': 400}
        source_asset.write(self.recipe / 'example.json', self.config)

    def test_final_viewbox_sets_physical_aspect_without_geometry_sync(self):
        def customize(root, context):
            root.set('viewBox', '-10, -20, 200, 300')
            root.set('width', '1pt')
            root.set('height', '2pt')
            # Deliberately leave the source geometry at its old 100 x 50 size.
            self.assertEqual(context['geometry']['viewBox'], [0, 0, 100, 50])

        root, _, geometry, _, _ = source_asset.build(
            self.recipe, self.config, customize)
        self.assertEqual(root.get('width'), '400pt')
        self.assertEqual(root.get('height'), '600pt')
        self.assertEqual(geometry['viewBox'], [0, 0, 100, 50])

    def test_geometry_changes_cannot_override_actual_final_canvas(self):
        def customize(root, context):
            context['geometry']['viewBox'] = [0, 0, 900, 100]

        root, *_ = source_asset.build(self.recipe, self.config, customize)
        self.assertEqual(root.get('width'), '400pt')
        self.assertEqual(root.get('height'), '200pt')

    def test_invalid_final_viewboxes_fail_before_svg_is_written(self):
        for value in (None, '', '0 0 100', '0 0 100 50 20', 'bad',
                      '0 0 0 50', '0 0 100 -1', '0 0 nan 50',
                      '0 0 100 inf', 'inf 0 100 50'):
            with self.subTest(viewbox=value):
                def customize(root, context):
                    if value is None:
                        root.attrib.pop('viewBox')
                    else:
                        root.set('viewBox', value)

                out = Path(self.tmp.name) / 'invalid'
                with patch.object(sys, 'argv', ['make_figure.py', '--out', str(out)]):
                    with self.assertRaisesRegex(ValueError, 'Invalid final SVG viewBox'):
                        source_asset.run(self.recipe / 'make_figure.py', customize)
                self.assertFalse((out / 'fig.svg').exists())

    def test_duplicate_existing_key_identifies_both_objects(self):
        def customize(root, context):
            ET.SubElement(root, source_asset.tag('path'), {
                'id': 'new-edge', 'data-asset-key': 'e0001', 'd': 'M0 0 L1 1',
            })

        with self.assertRaises(ValueError) as error:
            source_asset.build(self.recipe, self.config, customize)
        message = str(error.exception)
        for detail in ('Duplicate data-asset-key', 'e0001', 'original-box', 'new-edge'):
            self.assertIn(detail, message)

    def test_duplicate_new_keys_do_not_write_outputs_or_parts(self):
        def customize(root, context):
            for ident in ('new-a', 'new-b'):
                ET.SubElement(root, source_asset.tag('rect'), {
                    'id': ident, 'data-asset-key': 'new-127',
                    'x': '0', 'y': '0', 'width': '10', 'height': '10',
                })

        out = Path(self.tmp.name) / 'duplicate'
        with patch.object(sys, 'argv', ['make_figure.py', '--out', str(out), '--parts']):
            with self.assertRaisesRegex(ValueError, "Duplicate data-asset-key 'new-127'"):
                source_asset.run(self.recipe / 'make_figure.py', customize)
        self.assertEqual(list(out.iterdir()), [])

    def test_run_preserves_legacy_nodes_and_allows_unassigned_new_objects(self):
        def customize(root, context):
            root.set('viewBox', '0 0 1e2 1.5e2')
            ET.SubElement(root, source_asset.tag('circle'), {
                'data-asset-key': 'new-circle', 'cx': '90', 'cy': '90', 'r': '5',
            })
            ET.SubElement(root, source_asset.tag('text')).text = 'Unkeyed addition'

        out = Path(self.tmp.name) / 'valid'
        with patch.object(sys, 'argv', ['make_figure.py', '--out', str(out)]):
            with redirect_stdout(StringIO()):
                source_asset.run(self.recipe / 'make_figure.py', customize)
        root = ET.parse(out / 'fig.svg').getroot()
        self.assertEqual((root.get('width'), root.get('height')), ('400pt', '600pt'))
        self.assertEqual(root.find(".//*[@id='legacy-metadata']").text,
                         'Existing source metadata')
        self.assertIsNotNone(root.find(".//*[@id='arrow']"))
        label = root.find(".//*[@id='original-label']")
        self.assertEqual((label.get('font-family'), label.get('font-size')), ('Arial', '12'))
        self.assertIn('new-circle', source_asset.element_map(root))
        structure = json.loads((out / 'structure.json').read_text(encoding='utf-8'))
        self.assertNotIn('new-circle', structure['components'][0]['element_keys'])

    def test_clear_and_replace_parts_updates_structure_and_actual_part_svg(self):
        def customize(root, context):
            label = ET.SubElement(root, source_asset.tag('text'), {
                'data-asset-key': 'clinical-label', 'x': '10', 'y': '45',
                'font-size': '10', 'font-family': 'Arial',
            })
            label.text = 'Clinical review'
            context['parts'].clear()
            # Visible elements are measured for export; explicit bounds are optional.
            context['parts']['clinical'] = {
                'id': 'clinical', 'element_keys': ['clinical-label'],
            }

        out = Path(self.tmp.name) / 'replaced'
        with patch.object(sys, 'argv', ['make_figure.py', '--out', str(out), '--parts']):
            with redirect_stdout(StringIO()):
                source_asset.run(self.recipe / 'make_figure.py', customize)
        structure = source_asset.read(out / 'structure.json')
        self.assertEqual([p['id'] for p in structure['components']], ['clinical'])
        index = source_asset.read(out / 'parts/index.json')
        self.assertEqual(index[0]['visible_element_keys'], ['clinical-label'])
        self.assertFalse(index[0]['empty'])
        self.assertFalse((out / 'parts/main.svg').exists())
        part = ET.parse(out / 'parts/clinical.svg').getroot()
        self.assertEqual(set(source_asset.element_map(part)), {'clinical-label'})
        self.assertEqual(source_asset.element_map(part)['clinical-label'].text, 'Clinical review')

    def test_added_deleted_and_mutated_existing_parts_all_take_effect(self):
        asset = source_asset.read(self.recipe / 'asset.json')
        asset['parts'].append({'id': 'obsolete', 'name': 'Old', 'box': [0, 0, 1, 1]})
        source_asset.write(self.recipe / 'asset.json', asset)

        def customize(root, context):
            del context['parts']['obsolete']
            context['parts']['main']['element_keys'] = ['e0001']
            context['parts']['label'] = {'id': 'label', 'element_keys': ['e0002']}

        root, _, geometry, parts, _ = source_asset.build(self.recipe, self.config, customize)
        self.assertEqual([p['id'] for p in parts], ['main', 'label'])
        out = Path(self.tmp.name) / 'added'
        out.mkdir()
        source_asset.export_parts(root, parts, geometry, out)
        main = ET.parse(out / 'parts/main.svg').getroot()
        label = ET.parse(out / 'parts/label.svg').getroot()
        self.assertEqual(set(source_asset.element_map(main)), {'e0001'})
        self.assertEqual(set(source_asset.element_map(label)), {'e0002'})
        self.assertFalse((out / 'parts/obsolete.svg').exists())

    def test_replacing_registry_with_empty_mapping_removes_all_parts(self):
        def customize(root, context):
            context['parts'] = {}

        _, _, _, parts, _ = source_asset.build(self.recipe, self.config, customize)
        self.assertEqual(parts, [])

    def test_missing_part_id_has_diagnostic_before_output_write(self):
        def customize(root, context):
            context['parts'].clear()
            context['parts']['clinical'] = {'element_keys': ['e0002'], 'label': 'Clinical'}

        out = Path(self.tmp.name) / 'invalid-parts'
        with patch.object(sys, 'argv', ['make_figure.py', '--out', str(out), '--parts']):
            with self.assertRaisesRegex(ValueError, "Invalid customized part 'clinical': id"):
                source_asset.run(self.recipe / 'make_figure.py', customize)
        self.assertEqual(list(out.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
