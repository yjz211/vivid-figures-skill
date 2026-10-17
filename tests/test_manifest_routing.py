"""Manifest renderer routes and full-paper roadmap roles stay explicit."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "original/resources/scripts/validate_figure_manifest.py"
SPEC = importlib.util.spec_from_file_location("validate_figure_manifest", SCRIPT)
manifest = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manifest)


def entry(name="fig_method_overview", purpose="roadmap", formats="svg,pdf", renderer=None):
    fields = (f"claim=Method overview | source=METHOD.md | section=Methods | "
              f"language=en | format={formats} | layout=single")
    if purpose is not None:
        fields += f" | purpose={purpose}"
    if renderer is not None:
        fields += f" | renderer={renderer}"
    return f"- {name} | {fields}"


class ManifestRoutingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="vivid-manifest-")
        self.path = Path(self.temp.name) / "PLAN.md"

    def tearDown(self):
        self.temp.cleanup()

    def parse(self, block):
        self.path.write_text(f"{manifest.BEGIN}\n{block}\n{manifest.END}\n", encoding="utf-8")
        return manifest.parse_manifest(self.path)

    def test_architecture_headings_have_their_own_route(self):
        for heading in ("ARCHITECTURE", "SVG架构", "SVG 架构", "architecture-assets"):
            with self.subTest(heading=heading):
                entries = self.parse(f"**{heading}：**\n{entry()}")
                self.assertEqual(entries[0]["category"], "ARCHITECTURE")
                self.assertEqual(manifest.validate(entries, "modeling", True), ([], []))
                plan = manifest.execution_plan(entries)
                self.assertEqual(plan[0]["items"], [])
                self.assertEqual(plan[1], {"workflow": "architecture-assets",
                                          "classes": ["ARCHITECTURE"],
                                          "items": ["fig_method_overview"]})

    def test_svg_data_output_is_not_an_architecture_route(self):
        entries = self.parse(f"**数据图（matplotlib；paper-figure）：**\n"
                             f"{entry('fig_comparison', 'result', 'svg,pdf')}")
        self.assertEqual(entries[0]["category"], "DATA")
        plan = manifest.execution_plan(entries)
        self.assertEqual(plan[0]["items"], ["fig_comparison"])
        self.assertEqual(plan[1]["items"], [])

    def test_semantic_names_and_explicit_roadmap_role(self):
        for heading, name, formats in (("DRAWIO", "fig_method_overview", "drawio,pdf"),
                                       ("TIKZ", "tikz_method_overview", "tex,pdf")):
            with self.subTest(heading=heading):
                entries = self.parse(f"**{heading}：**\n{entry(name, formats=formats)}")
                self.assertEqual(manifest.validate(entries, "modeling", True), ([], []))

    def test_explicit_html_and_mermaid_satisfy_roadmap_role(self):
        for formats in ("html,pdf", "mermaid,svg", "mmd,pdf", ".html", "HTML / PDF"):
            with self.subTest(formats=formats):
                entries = self.parse(f"**显式可选格式（HTML / Mermaid）：**\n"
                                     f"{entry(formats=formats)}")
                self.assertEqual(manifest.validate(entries, "modeling", True), ([], []))
                self.assertEqual(manifest.execution_plan(entries)[-1]["items"],
                                 ["fig_method_overview"])

    def test_optional_roadmap_requires_explicit_supported_format(self):
        for formats in ("svg,pdf", "htmlish", "notmermaid"):
            with self.subTest(formats=formats):
                entries = self.parse(f"**OPTIONAL：**\n{entry(formats=formats)}")
                errors, warnings = manifest.validate(entries, "modeling", True)
                self.assertTrue(any("purpose=roadmap" in error for error in errors))
                self.assertTrue(any("HTML or Mermaid" in warning for warning in warnings))

    def test_explicit_optional_renderer_allows_requested_pdf_only_exports(self):
        for renderer in ("HTML", "MERMAID", "html", "Mermaid"):
            with self.subTest(renderer=renderer):
                entries = self.parse(f"**OPTIONAL：**\n{entry(formats='pdf', renderer=renderer)}")
                self.assertEqual(manifest.validate(entries, "modeling", True), ([], []))
                self.assertEqual(entries[0]["fields"]["format"], "pdf")
                self.assertEqual(manifest.execution_plan(entries)[-1]["items"], ["fig_method_overview"])

    def test_optional_renderer_requires_exact_html_or_mermaid_name(self):
        for renderer in ("HTMLish", "MMD", "notmermaid", "HTML + MERMAID", "SVG"):
            with self.subTest(renderer=renderer):
                entries = self.parse(f"**OPTIONAL：**\n{entry(formats='pdf', renderer=renderer)}")
                errors, warnings = manifest.validate(entries, "modeling", True)
                self.assertTrue(any("purpose=roadmap" in error for error in errors))
                self.assertTrue(any("HTML or Mermaid" in warning for warning in warnings))

    def test_new_roadmap_names_require_purpose(self):
        for heading, name, formats in (("ARCHITECTURE", "fig_method_overview", "svg,pdf"),
                                       ("DRAWIO", "fig_method_overview", "drawio,pdf"),
                                       ("TIKZ", "tikz_method_overview", "tex,pdf"),
                                       ("OPTIONAL", "fig_method_overview", "html,pdf")):
            with self.subTest(heading=heading):
                entries = self.parse(f"**{heading}：**\n{entry(name, None, formats)}")
                errors, _ = manifest.validate(entries, "modeling", True)
                self.assertTrue(any("purpose=roadmap" in error for error in errors))

    def test_nondeterministic_or_data_entries_cannot_satisfy_roadmap_role(self):
        for heading in ("DATA", "ILLUSTRATION"):
            with self.subTest(heading=heading):
                entries = self.parse(f"**{heading}：**\n{entry()}")
                errors, _ = manifest.validate(entries, "modeling", True)
                self.assertTrue(any("purpose=roadmap" in error for error in errors))

    def test_legacy_drawio_name_is_accepted_with_migration_warning(self):
        entries = self.parse(f"**DRAWIO：**\n{entry('fig_roadmap', None, 'drawio,pdf')}")
        errors, warnings = manifest.validate(entries, "modeling", True)
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("add purpose=roadmap", warnings[0])
        entries[0]["fields"]["purpose"] = "roadmap"
        self.assertEqual(manifest.validate(entries, "modeling", True), ([], []))

    def test_legacy_name_does_not_override_an_explicit_different_role(self):
        entries = self.parse(f"**DRAWIO：**\n{entry('fig_roadmap', 'result', 'drawio,pdf')}")
        errors, warnings = manifest.validate(entries, "modeling", True)
        self.assertTrue(errors)
        self.assertEqual(warnings, [])

    def test_unknown_renderer_does_not_inherit_previous_category(self):
        entries = self.parse(f"**DATA：**\n{entry('fig_result', 'result')}\n"
                             f"**Unknown renderer：**\n{entry()}\n"
                             f"**ARCHITECTURE：**\n{entry('fig_architecture')}")
        self.assertEqual([item["category"] for item in entries], ["DATA", None, "ARCHITECTURE"])
        errors, _ = manifest.validate(entries, "modeling", True)
        self.assertEqual(errors, ["fig_method_overview: entry is outside a recognized renderer section"])
        self.assertNotIn("fig_method_overview", manifest.execution_plan(entries)[0]["items"])

    def test_plain_svg_heading_is_not_mistaken_for_architecture(self):
        entries = self.parse(f"**DATA：**\n{entry('fig_result', 'result')}\n"
                             f"**SVG：**\n{entry()}")
        self.assertIsNone(entries[-1]["category"])

    def test_totals_are_not_renderer_headings(self):
        for heading in ("**总数：** DATA=1, DRAWIO=1, ARCHITECTURE=1, ALL=3",
                        "**Total: DATA=1, DRAWIO=1, ARCHITECTURE=1, ALL=3**"):
            with self.subTest(heading=heading):
                self.assertIsNone(manifest.heading_category(heading))
                entries = self.parse(f"**ARCHITECTURE：**\n{entry()}\n{heading}")
                self.assertEqual(len(entries), 1)
                self.assertEqual(manifest.validate(entries, "modeling", True), ([], []))

    def test_execution_order_and_cli_output_preserve_all_routes(self):
        specs = (("DATA", "fig_result", "result", "pdf,png"),
                 ("ARCHITECTURE", "fig_method_overview", "roadmap", "svg,pdf"),
                 ("DRAWIO", "fig_apparatus", "schematic", "drawio,pdf"),
                 ("TIKZ", "tikz_geometry", "geometry", "tex,pdf"),
                 ("ILLUSTRATION", "fig_scene", "scene", "png"),
                 ("OPTIONAL", "fig_pipeline", "pipeline", "mermaid,svg"))
        entries = self.parse("\n".join(f"**{heading}：**\n{entry(name, purpose, formats)}"
                                       for heading, name, purpose, formats in specs))
        plan = manifest.execution_plan(entries)
        self.assertEqual([step["workflow"] for step in plan],
                         ["paper-figure", "architecture-assets", "paper-technical-diagram",
                          "paper-illustration", "explicit-html-or-mermaid"])
        self.assertEqual(plan[2]["items"], ["fig_apparatus", "tikz_geometry"])
        output = Path(self.temp.name) / "audit.json"
        result = subprocess.run([sys.executable, str(SCRIPT), "--manifest", str(self.path),
                                 "--profile", "modeling", "--full-paper", "--json", str(output)],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(payload["errors"], [])
        self.assertEqual(payload["plan"], plan)

    def test_roadmap_requirement_only_applies_to_complete_modeling_papers(self):
        entries = self.parse(f"**DATA：**\n{entry('fig_result', 'result')}")
        for profile, full_paper in (("research", True), ("modeling", False)):
            self.assertEqual(manifest.validate(entries, profile, full_paper), ([], []))


if __name__ == "__main__":
    unittest.main()
