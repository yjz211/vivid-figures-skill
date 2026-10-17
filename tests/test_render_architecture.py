"""Small local-SVG regressions for physical text size and viewBox coordinates.

Run with ``python tests/test_render_architecture.py``. The integration test uses
the architecture runtime's local Chromium and writes only to a temporary folder.
"""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from render_architecture import parse_viewbox, render


class ViewBoxTests(unittest.TestCase):
    def test_comma_whitespace_and_scientific_notation(self):
        self.assertEqual(parse_viewbox('-2e1, -10 2e2,160'), [-20, -10, 200, 160])

    def test_invalid_viewbox_has_an_actionable_error(self):
        for value in (None, '', '0 0 100', '0 0 0 10', '0 0 10 -1',
                      '0 0 nan 10', '0 0 10 inf', '0 0 10 10 1'):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, 'Invalid SVG viewBox'):
                    parse_viewbox(value)


class RenderTypographyTests(unittest.TestCase):
    def test_transformed_and_mixed_runs_match_physical_pdf_sizes(self):
        import fitz

        source = '''<svg xmlns="http://www.w3.org/2000/svg"
          width="200pt" viewBox="-20, -10, 200, 160" font-family="sans-serif">
          <g transform="translate(0 20) scale(.5)">
            <text x="0" y="0" font-size="12">Scaled down</text>
          </g>
          <text transform="translate(0 50) rotate(10) scale(2)"
            x="0" y="0" font-size="6">Scaled up</text>
          <g transform="translate(0 80) scale(.5)">
            <text x="0" y="0" font-size="30"><tspan font-size="10">Tspan size</tspan></text>
          </g>
          <text x="0" y="120" font-size="12"><tspan>Large</tspan><tspan font-size="6">small</tspan></text>
          <g data-vivid-part="box" id="box" data-bounds="0 0 20 10"
             transform="translate(100 10) scale(2)">
            <rect x="0" y="0" width="20" height="10"/>
          </g>
        </svg>'''
        with tempfile.TemporaryDirectory(prefix='vivid-render-test-') as folder:
            path = Path(folder) / 'fig.svg'
            path.write_text(source, encoding='utf-8')
            with redirect_stdout(StringIO()):
                status = render(path, scale=1)
            self.assertEqual(status, 0)
            checks = json.loads(path.with_suffix('.checks.json').read_text(encoding='utf-8'))
            geometry = json.loads(path.with_suffix('.geometry.json').read_text(encoding='utf-8'))
            self.assertEqual(checks['errors'], [])
            warnings = {item['text']: item['pt'] for item in checks['warnings']}
            self.assertEqual(warnings, {'Scaled down': 6.0, 'Tspan size': 5.0, 'Largesmall': 6.0})
            texts = {item['text']: item for item in geometry['texts']}
            self.assertAlmostEqual(texts['Scaled up']['print_font_pt'], 12.0, places=4)
            self.assertEqual([run['print_font_pt'] for run in texts['Largesmall']['font_runs']], [12.0, 6.0])
            self.assertEqual(geometry['coordinate_space'], 'svg-viewbox')
            # The negative origin changes viewport placement, not the declared
            # object coordinates or its containment inside the transformed part.
            for actual, expected in zip(geometry['groups'][0]['box'], [100, 10, 140, 30]):
                self.assertAlmostEqual(actual, expected, places=6)
            with fitz.open(path.with_suffix('.pdf')) as pdf:
                self.assertAlmostEqual(pdf[0].rect.width, 200, delta=1)
                spans = [span for block in pdf[0].get_text('dict')['blocks']
                         for line in block.get('lines', []) for span in line['spans']]
                for label, expected in [('Scaled down', 6), ('Scaled up', 12), ('Tspan size', 5)]:
                    sizes = [span['size'] for span in spans if label in span['text']]
                    self.assertTrue(sizes, f'Missing actual PDF text: {label}')
                    self.assertAlmostEqual(sizes[0], expected, delta=.05)


if __name__ == '__main__':
    unittest.main()
