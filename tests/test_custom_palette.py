"""Short custom palettes remain usable by the unchanged recipe sources."""
import ast
import base64
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / 'original/resources/assets/shared-scripts'
sys.path.insert(0, str(SHARED))

from get_recipe import Recipes
import plot_utils as pu
import vivid_config as vc


class CustomPaletteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='vivid-short-palette-')
        self.previous_workspace = os.environ.get('VIVID_WORKSPACE')
        os.environ['VIVID_WORKSPACE'] = self.temp.name
        self.colors = ['#112233', '#AABBCC']
        vc.write_config(self.temp.name, palette='custom', colors=self.colors)
        pu.setup_style()

    def tearDown(self):
        if self.previous_workspace is None:
            os.environ.pop('VIVID_WORKSPACE', None)
        else:
            os.environ['VIVID_WORKSPACE'] = self.previous_workspace
        self.temp.cleanup()

    def test_unchanged_recipes_can_read_all_fixed_color_roles(self):
        recipes = Recipes(SHARED)
        checked = set()
        for recipe in recipes.entries:
            code, _ = recipes.script(recipe)
            for node in ast.walk(ast.parse(code)):
                if (isinstance(node, ast.Subscript)
                        and isinstance(node.value, ast.Name)
                        and node.value.id in ('PALETTE', 'PALETTE_LIGHT')
                        and isinstance(node.slice, ast.Constant)
                        and type(node.slice.value) is int
                        and node.slice.value >= 0):
                    with self.subTest(recipe=recipe, expression=ast.unparse(node)):
                        result = eval(compile(ast.Expression(node), recipe, 'eval'),
                                      {'PALETTE': pu.PALETTE, 'PALETTE_LIGHT': pu.PALETTE_LIGHT})
                        expected = (self.colors if node.value.id == 'PALETTE' else
                                    [pu._lighten(c, 0.4) for c in self.colors])
                        self.assertEqual(result, expected[node.slice.value % len(expected)])
                        checked.add(recipe)
        self.assertIn('advanced.dumbbell', checked)
        self.assertIn('advanced.kaplan_meier', checked)

    def test_custom_sequence_and_continuous_colors_are_not_expanded(self):
        import matplotlib
        self.assertEqual(vc.load_config(self.temp.name)['colors'], self.colors)
        self.assertEqual(vc.palette_colors(), self.colors)
        self.assertEqual(vc.categorical_colors(), self.colors)
        self.assertEqual(list(pu.PALETTE), self.colors)
        self.assertEqual(len(pu.PALETTE), 2)
        self.assertEqual(pu.PALETTE[:5], self.colors)
        self.assertEqual(pu.PALETTE[-1], self.colors[-1])
        self.assertEqual(pu.PALETTE[np.int64(3)], self.colors[1])
        self.assertEqual(matplotlib.rcParams['axes.prop_cycle'].by_key()['color'], self.colors)
        with self.assertRaises(IndexError):
            _ = pu.PALETTE[-3]

    def test_imported_palette_aliases_follow_later_style_changes(self):
        palette, light = pu.PALETTE, pu.PALETTE_LIGHT
        second = ['#102030', '#405060', '#708090']
        pu.setup_style(second)
        self.assertIs(palette, pu.PALETTE)
        self.assertIs(light, pu.PALETTE_LIGHT)
        self.assertEqual(list(palette), second)
        self.assertEqual(palette[4], second[1])
        self.assertEqual(light[4], pu._lighten(second[1], 0.4))
        pu.setup_style('olive-apricot')
        self.assertEqual(list(palette), vc.categorical_colors({'palette': 'olive-apricot'}))


class PaletteDistributionTests(unittest.TestCase):
    def test_downloads_use_current_helper_and_match_manifest(self):
        web = ROOT / 'workbench'
        canonical = (SHARED / 'plot_utils.py').read_bytes()
        self.assertEqual((web / 'editor_backend/_utils/plot_utils.py').read_bytes(), canonical)
        manifest = json.loads((web / 'docs/template-manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['shared_files']['editor_backend/_utils/plot_utils.py'],
                         hashlib.sha256(canonical).hexdigest())
        listed = set()
        for source in manifest['sources']:
            for bundle in source['bundle']:
                path = web / bundle['path']
                with self.subTest(bundle=bundle['path']):
                    payload = path.read_bytes()
                    self.assertEqual(hashlib.sha256(payload).hexdigest(), bundle['sha256'])
                    with zipfile.ZipFile(path) as archive:
                        self.assertEqual(archive.read('_utils/plot_utils.py'), canonical)
                    prefix = ('window.VIVID_ZIPS=window.VIVID_ZIPS||{};window.VIVID_ZIPS['
                              + json.dumps(path.stem) + ']=')
                    javascript = path.with_suffix('.js').read_text(encoding='utf-8')
                    self.assertTrue(javascript.startswith(prefix))
                    encoded = json.loads(javascript[len(prefix):].strip().removesuffix(';'))
                    self.assertEqual(base64.b64decode(encoded, validate=True), payload)
                    listed.add(path.resolve())
        self.assertEqual(listed, {p.resolve() for p in (web / 'assets/downloads').glob('*.zip')})


if __name__ == '__main__':
    unittest.main()
