#!/usr/bin/env python
"""Validate a manifest-compatible FIGURE_MANIFEST and print its execution plan."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BEGIN = "<!-- BEGIN FIGURE_MANIFEST -->"
END = "<!-- END FIGURE_MANIFEST -->"
ENTRY_RE = re.compile(r"^\s*-\s+([A-Za-z][A-Za-z0-9_]*)\s*(?:\|(.*))?$")
HEADING_RE = re.compile(r"^\s*\*\*(.+?)\*\*")
CATEGORIES = (
    ("DATA", ("data figure", "数据图", "matplotlib", "paper-figure")),
    ("ARCHITECTURE", ("svg架构", "svg 架构", "architecture-assets")),
    ("DRAWIO", ("drawio", "draw.io")),
    ("TIKZ", ("tikz",)),
    ("ILLUSTRATION", ("illustration", "ai 场景", "ai插图", "paper-illustration")),
    ("OPTIONAL", ("optional", "可选格式", "html / mermaid", "html/mermaid")),
)
REQUIRED_FIELDS = {"claim", "source", "section", "language", "format", "layout"}
DETERMINISTIC_CLASSES = {"ARCHITECTURE", "DRAWIO", "TIKZ", "OPTIONAL"}


def heading_category(line: str) -> str | None:
    match = HEADING_RE.match(line)
    if not match:
        return None
    low = match.group(1).strip().lower()
    if re.match(r"^(?:总数|totals?)(?:\s|[:：]|$)", low):
        return None
    # Class identifiers take precedence over workflow aliases in descriptions.
    for category, _ in CATEGORIES:
        if re.search(rf"(?<![a-z0-9_]){category.lower()}(?![a-z0-9_])", low):
            return category
    for category, terms in CATEGORIES:
        if any(term in low for term in terms):
            return category
    return None


def has_explicit_optional_format(fields: dict[str, str]) -> bool:
    # The renderer is separate from the requested exports, which may be PDF-only.
    if fields.get("renderer", "").strip().upper() in {"HTML", "MERMAID"}:
        return True
    return bool(re.search(r"(?<![a-z0-9_])(?:html|mmd|mermaid)(?![a-z0-9_])",
                          fields.get("format", "").lower()))


def is_legacy_roadmap(item: dict) -> bool:
    return (item["category"] == "DRAWIO" and item["name"] == "fig_roadmap"
            and not item["fields"].get("purpose", "").strip())


def is_roadmap(item: dict) -> bool:
    category, fields = item["category"], item["fields"]
    if category not in DETERMINISTIC_CLASSES:
        return False
    if category == "OPTIONAL" and not has_explicit_optional_format(fields):
        return False
    return fields.get("purpose", "").strip().lower() == "roadmap" or is_legacy_roadmap(item)


def parse_fields(raw: str | None) -> dict[str, str]:
    result = {}
    for part in (raw or "").split("|"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        result[key.strip().lower()] = value.strip()
    return result


def parse_manifest(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    start, end = text.find(BEGIN), text.find(END)
    if start < 0 or end < 0 or end <= start:
        raise ValueError("missing or invalid FIGURE_MANIFEST anchors")
    block = text[start + len(BEGIN):end]
    entries = []
    category = None
    for number, line in enumerate(block.splitlines(), 1):
        if HEADING_RE.match(line):
            # Unknown headings must not inherit the preceding renderer section.
            category = heading_category(line)
            continue
        match = ENTRY_RE.match(line)
        if not match or match.group(1).lower() == "none":
            continue
        entries.append(
            {
                "line": number,
                "name": match.group(1),
                "category": category,
                "fields": parse_fields(match.group(2)),
            }
        )
    return entries


def validate(entries: list[dict], profile: str, full_paper: bool):
    errors, warnings = [], []
    seen = {}
    for item in entries:
        name, category, fields = item["name"], item["category"], item["fields"]
        if category is None:
            errors.append(f"{name}: entry is outside a recognized renderer section")
            continue
        if name in seen:
            errors.append(f"{name}: duplicated in {seen[name]} and {category}")
        seen[name] = category
        missing = sorted(REQUIRED_FIELDS - set(fields))
        if missing:
            errors.append(f"{name}: missing fields {', '.join(missing)}")
        if category == "TIKZ" and not name.startswith("tikz_"):
            errors.append(f"{name}: TikZ basename must start with tikz_")
        elif category != "TIKZ" and not (name.startswith("fig_") or name.startswith("TABLE_")):
            errors.append(f"{name}: basename must start with fig_ or TABLE_")
        if category == "OPTIONAL" and not has_explicit_optional_format(fields):
            warnings.append(f"{name}: optional entry should identify HTML or Mermaid via renderer or format")
        if is_legacy_roadmap(item):
            warnings.append(f"{name}: legacy DRAWIO roadmap name accepted; add purpose=roadmap")
    if full_paper and profile == "modeling":
        if not any(is_roadmap(item) for item in entries):
            errors.append("full modeling paper requires a purpose=roadmap entry in ARCHITECTURE, "
                          "DRAWIO, TIKZ, or OPTIONAL with explicit HTML/Mermaid renderer or format")
    if not entries:
        errors.append("manifest contains no figure entries")
    return errors, warnings


def execution_plan(entries: list[dict]):
    grouped = {key: [] for key, _ in CATEGORIES}
    for item in entries:
        if item["category"] in grouped:
            grouped[item["category"]].append(item["name"])
    return [
        {"workflow": "paper-figure", "classes": ["DATA"], "items": grouped["DATA"]},
        {"workflow": "architecture-assets", "classes": ["ARCHITECTURE"], "items": grouped["ARCHITECTURE"]},
        {
            "workflow": "paper-technical-diagram",
            "classes": ["DRAWIO", "TIKZ"],
            "items": grouped["DRAWIO"] + grouped["TIKZ"],
        },
        {
            "workflow": "paper-illustration",
            "classes": ["ILLUSTRATION"],
            "items": grouped["ILLUSTRATION"],
        },
        {"workflow": "explicit-html-or-mermaid", "classes": ["OPTIONAL"], "items": grouped["OPTIONAL"]},
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--profile", choices=["research", "modeling"], default="modeling")
    parser.add_argument("--full-paper", action="store_true")
    parser.add_argument("--json", dest="json_path", type=Path)
    args = parser.parse_args()
    try:
        entries = parse_manifest(args.manifest)
        errors, warnings = validate(entries, args.profile, args.full_paper)
    except Exception as exc:
        print(f"FAIL: {exc}")
        return 1
    plan = execution_plan(entries)
    payload = {"manifest": str(args.manifest), "entries": entries, "plan": plan, "errors": errors, "warnings": warnings}
    print("=== FIGURE_MANIFEST routing audit ===")
    for step in plan:
        if step["items"]:
            print(f"{step['workflow']}: {', '.join(step['items'])}")
    for warning in warnings:
        print(f"WARN: {warning}")
    for error in errors:
        print(f"FAIL: {error}")
    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

