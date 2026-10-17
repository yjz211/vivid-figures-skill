"""Focused, browser-free regression tests for connection diagnostics.

Run with ``python scripts/test_check_architecture_connections.py``.
The fixtures describe CSS-pixel geometry and never modify SVG input files.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


MODULE_PATH = Path(__file__).with_name("check_architecture_connections.py")
SPEC = importlib.util.spec_from_file_location("check_architecture_connections", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)


def geometry(*, d="M 0 5 L 20 5", box=(5, 0, 15, 10), owner="unrelated",
             role="component", rects=None, matrix=None, path_order=10):
    return {
        "paths": [{
            "id": "edge-1", "from": "source-a", "to": "target-b", "d": d,
            "matrix": matrix or [1, 0, 0, 1, 0, 0], "order": path_order,
            "visible": True, "unsupported": [], "stroke_width": 1,
        }],
        "texts": [{
            "text": "A label", "box": list(box), "order": 20,
            "owners": [{"id": owner, "role": role}],
            "unsupported": [], "visible": True,
        }],
        "rects": rects or [],
        "skipped_texts": [],
    }


def rectangle(*, fill="white", order=15, box=(4, -1, 16, 11), **changes):
    value = {
        "order": order, "box": list(box), "fill": fill,
        "effective_opacity": 1, "fill_opacity": 1, "simple": True,
    }
    value.update(changes)
    return value


class PathParsingTests(unittest.TestCase):
    def test_absolute_line_commands(self):
        self.assertEqual(
            checker.parse_polyline_path("M 10 20 L 30 40 H 50 V 60 L 70 80"),
            [((10, 20), (30, 40)), ((30, 40), (50, 40)),
             ((50, 40), (50, 60)), ((50, 60), (70, 80))],
        )

    def test_relative_commands_accumulate_coordinates(self):
        self.assertEqual(
            checker.parse_polyline_path("m 10 20 l 5 -2 h 7 v 10 l -2 4"),
            [((10, 20), (15, 18)), ((15, 18), (22, 18)),
             ((22, 18), (22, 28)), ((22, 28), (20, 32))],
        )

    def test_implicit_lines_and_repeated_axis_values(self):
        self.assertEqual(
            checker.parse_polyline_path("M0,0 10,0 10,10 h5 5 v-5 -5"),
            [((0, 0), (10, 0)), ((10, 0), (10, 10)),
             ((10, 10), (15, 10)), ((15, 10), (20, 10)),
             ((20, 10), (20, 5)), ((20, 5), (20, 0))],
        )

    def test_move_starts_another_subpath_without_joining_it(self):
        self.assertEqual(
            checker.parse_polyline_path("M0 0 L1 1 M10 10 l2 0"),
            [((0, 0), (1, 1)), ((10, 10), (12, 10))],
        )

    def test_curves_and_unknown_commands_are_not_partially_accepted(self):
        for suffix in ("C 2 2 3 3 4 4", "Q 2 2 4 4", "A 3 3 0 0 1 4 4", "R 2 2"):
            with self.subTest(suffix=suffix):
                with self.assertRaises(ValueError):
                    checker.parse_polyline_path("M0 0 L1 1 " + suffix)

    def test_incomplete_coordinate_pair_is_rejected(self):
        with self.assertRaises(ValueError):
            checker.parse_polyline_path("M0 0 L1")


class SegmentIntersectionTests(unittest.TestCase):
    def assert_clipped(self, actual, expected):
        self.assertIsNotNone(actual)
        for actual_point, expected_point in zip(actual, expected):
            for actual_value, expected_value in zip(actual_point, expected_point):
                # The checker clips to the interior with a sub-pixel epsilon.
                self.assertAlmostEqual(actual_value, expected_value, delta=1e-6)

    def test_horizontal_vertical_and_diagonal_clipping(self):
        box = [4, 4, 6, 6]
        cases = [
            ((0, 5), (10, 5), ((4, 5), (6, 5))),
            ((5, 0), (5, 10), ((5, 4), (5, 6))),
            ((0, 0), (10, 10), ((4, 4), (6, 6))),
            ((10, 5), (0, 5), ((6, 5), (4, 5))),
        ]
        for start, end, expected in cases:
            with self.subTest(start=start, end=end):
                self.assert_clipped(checker.segment_box_intersection(start, end, box), expected)

    def test_l_shaped_route_does_not_hit_rectangle_inside_its_overall_bbox(self):
        box = [4, 4, 6, 6]
        route = checker.parse_polyline_path("M0 0 V10 H10")
        self.assertTrue(all(checker.segment_box_intersection(a, b, box) is None for a, b in route))
        report = checker.analyze_geometry(geometry(d="M0 0 V10 H10", box=box))
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["coverage"]["supported_edges"], 1)


class OpacityTests(unittest.TestCase):
    def test_only_fully_opaque_colors_occlude(self):
        for fill in ("white", "#fff", "#ffffff", "rgb(255, 255, 255)", "rgba(255,255,255,1)"):
            with self.subTest(fill=fill):
                self.assertTrue(checker.opaque_color(fill))
        for fill in ("none", "transparent", "rgba(255,255,255,0)", "rgba(255,255,255,0.5)"):
            with self.subTest(fill=fill):
                self.assertFalse(checker.opaque_color(fill))

    def test_rect_opacity_and_geometry_must_all_be_supported(self):
        self.assertTrue(checker.rect_is_opaque(rectangle()))
        for changes in ({"effective_opacity": 0.5}, {"fill_opacity": 0.5},
                        {"simple": False}, {"fill": "rgba(255,255,255,0)"}):
            with self.subTest(changes=changes):
                self.assertFalse(checker.rect_is_opaque(rectangle(**changes)))


class DiagnosticTests(unittest.TestCase):
    def assert_category(self, report, category):
        self.assertEqual([item["category"] for item in report["findings"]], [category])
        self.assertEqual(report["counts"].get(category, 0), 1)

    def test_unrelated_text_is_reported_even_in_an_endpoint_ancestor_region(self):
        g = geometry(owner="hospital", role="region")
        self.assert_category(checker.analyze_geometry(g), "visible-text-intrusion")

    def test_shallow_endpoint_contact_and_deep_endpoint_intrusion_differ(self):
        cases = [
            ("M0 5 L5.4 5", "target-b", "minor-endpoint-contact"),
            ("M14.6 5 L20 5", "source-a", "minor-endpoint-contact"),
            ("M0 5 L8 5", "target-b", "visible-text-intrusion"),
            ("M12 5 L20 5", "source-a", "visible-text-intrusion"),
        ]
        for path, owner, category in cases:
            with self.subTest(path=path, owner=owner):
                self.assert_category(checker.analyze_geometry(geometry(d=path, owner=owner)), category)

    def test_shallow_contact_with_unrelated_text_still_requires_review(self):
        self.assert_category(
            checker.analyze_geometry(geometry(d="M0 5 L5.4 5")), "minor-text-contact",
        )

    def test_matrix_is_applied_before_intersection(self):
        self.assert_category(
            checker.analyze_geometry(geometry(matrix=[1, 0, 0, 1, 100, 0], box=(105, 0, 115, 10))),
            "visible-text-intrusion",
        )

    def test_later_opaque_backplate_distinguishes_intentional_label_gap(self):
        self.assert_category(
            checker.analyze_geometry(geometry(rects=[rectangle()])), "occluded-intersection",
        )

    def test_earlier_or_transparent_background_does_not_hide_a_collision(self):
        for rect in (rectangle(order=5), rectangle(fill="rgba(255,255,255,0)"),
                     rectangle(fill="rgba(255,255,255,0.5)"), rectangle(effective_opacity=0.5),
                     rectangle(fill_opacity=0.5)):
            with self.subTest(rect=rect):
                self.assert_category(
                    checker.analyze_geometry(geometry(rects=[rect])), "visible-text-intrusion",
                )

    def test_partial_backplate_does_not_hide_the_whole_collision(self):
        self.assert_category(
            checker.analyze_geometry(geometry(rects=[rectangle(box=(4, -1, 9, 11))])),
            "visible-text-intrusion",
        )

    def test_unsupported_curve_reports_missing_coverage(self):
        report = checker.analyze_geometry(geometry(d="M0 5 C5 5 10 5 20 5"))
        self.assertEqual(report["status"], "not-checked")
        self.assertEqual(report["coverage"]["semantic_edges"], 1)
        self.assertEqual(report["coverage"]["supported_edges"], 0)
        self.assertEqual(report["coverage"]["skipped_edges"], 1)
        self.assertEqual(report["findings"], [])

    def test_empty_semantic_edge_set_cannot_claim_pass(self):
        g = geometry()
        g["paths"] = []
        report = checker.analyze_geometry(g)
        self.assertEqual(report["status"], "not-applicable")
        self.assertEqual(report["coverage"]["semantic_edges"], 0)
        self.assertEqual(report["coverage"]["supported_edges"], 0)
        self.assertEqual(report["findings"], [])


class BrowserMeasurementTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec("playwright"), "Playwright is not installed")
    def test_visible_text_filtering_and_input_is_not_rewritten(self):
        svg = b'''<svg xmlns="http://www.w3.org/2000/svg" width="200" height="180"
            style="font-family:Arial;font-size:12px">
          <g id="source" data-role="component"/>
          <g id="target" data-role="component"/>
          <path id="visible-edge" data-from="source" data-to="target" d="M0 15 L150 15" stroke="black"/>
          <rect x="20" y="0" width="150" height="25" fill="rgba(255,255,255,0.25)"/>
          <text x="30" y="20">Visible label</text>
          <path id="transparent-text-edge" data-from="source" data-to="target" d="M0 45 L150 45" stroke="black"/>
          <text x="30" y="50" fill="rgba(0,0,0,0)">Transparent label</text>
          <path id="unpainted-text-edge" data-from="source" data-to="target" d="M0 75 L150 75" stroke="black"/>
          <text x="30" y="80" fill="none">Unpainted label</text>
          <path id="transparent-edge" data-from="source" data-to="target" d="M0 105 L150 105" stroke="rgba(0,0,0,0)"/>
          <text x="30" y="110">No visible edge</text>
          <path id="rotated-text-edge" data-from="source" data-to="target" d="M0 135 L150 135" stroke="black"/>
          <text x="30" y="140" transform="rotate(10,30,140)">Rotated label</text>
          <path id="curve-edge" data-from="source" data-to="target" d="M0 165 C40 165 100 165 150 165" stroke="black"/>
          <text x="30" y="170">Unsupported curve</text>
        </svg>'''
        with tempfile.TemporaryDirectory(prefix="vivid-connections-test-") as directory:
            source = Path(directory) / "input.svg"
            source.write_bytes(svg)
            try:
                report = checker.inspect_svg(source)
            except Exception as exc:
                if "Executable doesn't exist" in str(exc):
                    self.skipTest("Playwright Chromium is not installed")
                raise
            self.assertEqual(source.read_bytes(), svg)
            self.assertEqual(sorted(p.name for p in Path(directory).iterdir()), ["input.svg"])
        self.assertEqual({item["edge"] for item in report["findings"]}, {"visible-edge"})
        self.assertEqual(report["counts"]["visible-text-intrusion"], 1)
        self.assertEqual(report["coverage"]["semantic_edges"], 6)
        self.assertEqual(report["coverage"]["supported_edges"], 4)
        self.assertEqual(report["coverage"]["skipped_edges"], 2)
        self.assertGreaterEqual(report["coverage"]["skipped_text_runs"], 3)


if __name__ == "__main__":
    unittest.main()
