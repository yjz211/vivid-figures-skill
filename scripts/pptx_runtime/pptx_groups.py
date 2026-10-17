"""Nonduplicating, paint-order-safe semantic groups for native PowerPoint shapes.

Only disjoint paint bounds may exchange order. A semantic component split by an
overlapping foreign object is exported as separately named fragments. This is
intentional: PowerPoint groups cannot interleave children with outside shapes.
"""
from __future__ import annotations

from collections import defaultdict
import math


def _bounds(value):
    if isinstance(value, dict):
        value = [value.get(k) for k in ("x", "y", "width", "height")]
    try:
        x, y, w, h = map(float, value)
        if not all(math.isfinite(v) for v in (x, y, w, h)):
            return None
        return (min(x, x + w), min(y, y + h), abs(w), abs(h))
    except (TypeError, ValueError):
        return None


def _overlap(a, b):
    # Missing bounds cannot establish safe reordering. Touching boundaries are
    # conservatively overlapping, protecting antialiasing and zero-width lines.
    if a is None or b is None:
        return True
    return not (a[0] + a[2] < b[0] or b[0] + b[2] < a[0]
                or a[1] + a[3] < b[1] or b[1] + b[3] < a[1])


def _group_ids(item):
    values = item.get("group_ids", item.get("ancestor_ids", item.get("groups", [])))
    if isinstance(values, str):
        values = [values]
    return [str(v.get("id")) if isinstance(v, dict) else str(v) for v in (values or [])]


def _components(items, structure):
    structure = structure or {}
    raw = structure.get("components", structure.get("parts", []))
    if isinstance(raw, dict):
        raw = [dict(v, id=k) for k, v in raw.items()]
    inferred = defaultdict(set)
    for item in items:
        for gid in _group_ids(item):
            inferred[gid].add(str(item["key"]))
    if not raw:
        raw = [{"id": gid, "name": gid} for gid in inferred]
    result = []
    seen = set()
    for index, component in enumerate(raw):
        cid = str(component.get("id", f"component-{index + 1}"))
        if cid in seen:
            raise ValueError(f"Duplicate semantic component id: {cid}")
        seen.add(cid)
        keys = component.get("element_keys", component.get("keys"))
        members = set(map(str, keys)) if keys is not None else inferred.get(cid, set())
        result.append({"id": cid, "name": str(component.get("name", cid)),
                       "members": members, "index": index})
    return result



def resolve_ownership(items, structure=None):
    """Shared web/PPT object ownership, independent of rendering and paint order."""
    items = list(items)
    by_key = {str(i["key"]): i for i in items}
    if len(by_key) != len(items):
        raise ValueError("Scene keys must be unique")
    components = _components(items, structure)
    candidates = defaultdict(list)
    for component in components:
        for key in component["members"]:
            if key in by_key:
                candidates[key].append(component)
    ownership, shared = {}, []
    for key, options in candidates.items():
        # A subset component has a smaller membership and is the most specific.
        minimum = min(len(c["members"]) for c in options)
        narrowest = [c for c in options if len(c["members"]) == minimum]
        if len(narrowest) == 1:
            ownership[key] = narrowest[0]["id"]
        else:
            shared.append({"key": key, "components": [c["id"] for c in narrowest]})

    return components, ownership, shared

def group_shapes(slide, items, shapes_by_key, structure=None):
    """Group already-emitted native shapes in place; return a JSON-safe report.

    ``items`` are paint-ordered scene dicts with unique ``key`` and global SVG
    ``bbox=[x,y,width,height]`` (prefer painted bounds including stroke). Optional
    ``group_ids`` identifies SVG ancestor groups for code-template assets.
    ``shapes_by_key`` maps each key to a shape or a sequence of shapes. Existing
    slide order is authoritative. Shapes absent from the map remain untouched.
    The operation preserves shape instances, IDs, text, geometry and appearance;
    it does not duplicate native objects or insert any picture.
    """
    items = list(items)
    by_key = {str(item["key"]): item for item in items}
    if len(by_key) != len(items):
        raise ValueError("Scene keys must be unique before semantic grouping")
    components = _components(items, structure)
    components, ownership, shared = resolve_ownership(items, structure)

    original = list(slide.shapes)
    element_to_key = {}
    for key, shapes in shapes_by_key.items():
        if hasattr(shapes, "_element"):
            shapes = [shapes]
        for shape in shapes:
            element = shape._element
            if element in element_to_key:
                raise ValueError(f"Native shape assigned more than once: {shape.name}")
            element_to_key[element] = str(key)
    records = []
    for index, shape in enumerate(original):
        key = element_to_key.get(shape._element)
        item = by_key.get(key, {})
        bounds = _bounds(item.get("paint_bbox", item.get("bbox")))
        records.append({"shape": shape, "key": key, "owner": ownership.get(key),
                        "bbox": bounds, "index": index})

    plans, splits = [], []
    for component in components:
        cid = component["id"]
        owned = [r for r in records if r["owner"] == cid]
        if not owned:
            continue
        fragments, current = [], []
        for record in owned:
            if not current:
                current = [record]
                continue
            # Pull this member back to the first member. Only foreign objects
            # crossed by this member matter; own members retain their order.
            barriers = [r for r in records[current[0]["index"]:record["index"]]
                        if r["owner"] != cid and _overlap(record["bbox"], r["bbox"])]
            if barriers:
                fragments.append(current)
                splits.append({"component": cid, "before_key": record["key"],
                               "barrier_keys": list(dict.fromkeys(r["key"] for r in barriers)),
                               "reason": "preserve overlapping paint order"})
                current = [record]
            else:
                current.append(record)
        if current:
            fragments.append(current)
        for index, fragment in enumerate(fragments, 1):
            suffix = f" [{index}/{len(fragments)}]" if len(fragments) > 1 else ""
            plans.append({"component": cid, "name": component["name"] + suffix,
                          "records": fragment, "fragment": index,
                          "fragment_count": len(fragments)})

    report = {"groups": [], "singletons": [], "splits": splits,
              "shared_keys": shared, "original_shape_count": len(original),
              "unassigned_keys": [k for k in by_key if k not in ownership],
              "missing_component_keys": sorted(set().union(*(c["members"] for c in components))
                                               - set(by_key)) if components else [],
              "policy": "smallest unambiguous component; intersecting paint order preserved"}
    tree = slide.shapes._spTree
    for plan in sorted(plans, key=lambda p: p["records"][0]["index"]):
        members = [r["shape"] for r in plan["records"]]
        detail = {k: plan[k] for k in ("component", "name", "fragment", "fragment_count")}
        detail.update(keys=list(dict.fromkeys(r["key"] for r in plan["records"])),
                      shape_ids=[s.shape_id for s in members])
        if len(members) < 2:
            # Keep meaningful selection-pane names even when z-order requires
            # a fragment containing one native object rather than a fake group.
            members[0].name = f"{plan['name']} | {members[0].name}"
            report["singletons"].append(detail)
            continue
        anchor = min(tree.index(shape._element) for shape in members)
        group = slide.shapes.add_group_shape(members)
        group.name = plan["name"]
        tree.remove(group._element)
        tree.insert(anchor, group._element)
        detail["group_shape_id"] = group.shape_id
        report["groups"].append(detail)
    report["group_count"] = len(report["groups"])
    report["grouped_native_shape_count"] = sum(len(g["shape_ids"]) for g in report["groups"])
    report["top_level_shape_count"] = len(slide.shapes)
    return report
