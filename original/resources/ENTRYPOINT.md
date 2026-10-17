# 绘图入口

Use the pattern: classify upstream, record a machine-readable contract, execute the core render passes, then reconcile and audit. Do not choose a renderer from visual taste alone and do not load every drawing workflow.

## Required decision sequence

1. Read `references/router-contract.md` completely. For a full problem, paper, or complete figure set, create or update the anchored `FIGURE_MANIFEST` before drawing. Validate it with `python scripts/validate_figure_manifest.py --manifest <planning-document> --profile modeling --full-paper`; fix every failure before rendering. For an explicit figure or user-bounded small data-figure batch, apply the same classification rules; a separate manifest is optional.
2. Run `python scripts/bootstrap.py --workspace <active-project-root> --profile modeling-competition --capability all` before the first deterministic figure.
3. Execute only the non-empty renderer classes, in this order:
   - DATA/TABLE -> [data child Skill](../../channels/vivid-figure-skill/SKILL.md), which owns template selection, source adaptation and data-figure review;
   - ARCHITECTURE -> [architecture child Skill](../../channels/vivid-architecture-diagram-skill/SKILL.md), which owns the SVG asset route for model/system/solution architecture; preserve its A/B choice and selected-version delivery;
   - DRAWIO/TIKZ -> `paper-technical-diagram`, the manifest-compatible umbrella for the selected Draw.io and TikZ diagrams, including engineering, physical, geometric, network, scheduling, and process diagrams;
   - ILLUSTRATION -> `paper-illustration` only for qualifying pictorial or 3-D physical/engineering scenes;
   - HTML -> only when the user explicitly selects HTML instead of Draw.io;
   - MERMAID -> only when Mermaid or text-native maintainability is requested.
4. For DATA/TABLE and ARCHITECTURE, read only the corresponding child Skill and the references it requires for this figure. For other non-empty classes, read `workflows/<name>.md`, then its linked `references/<name>.md`; load conditional references only when relevant and preserve its drawing methods and templates. Review scope, timing and repair limits follow the selected channel: SVG architecture uses its own acceptance guidance; other legacy routes follow `../review-policy.md` without adding extra rounds.
5. Reconcile the manifest after every pass. A missing planned output keeps the task open; retry or use only the documented fallback for that class. Never silently reclassify a missing figure.
6. For paper-bound figures, read `references/paper-layout-gate.md`; apply its size guidance with review scope and timing governed by `../review-policy.md`. Inspect individual figures during drawing and compiled pages after paper layout; a figures-only request does not require a compiled paper.

When uncertain whether something is a data curve or a TikZ construction, classify it as DATA. Model/system/solution architecture uses ARCHITECTURE unless the user selects another supported format or the task needs precise TikZ geometry; other non-data diagrams that require exact, reproducible structure use `paper-technical-diagram`. An explicit HTML/Mermaid choice remains in that class, including a roadmap: do not add a duplicate Draw.io roadmap. AI illustration must not replace evidence plots, engineering schematics that can be drawn deterministically, precise topology, or mathematical geometry.

## Completion gate

Finish only when the manifest is reconciled, every selected workflow passes its own checks, `figures/latex_includes.tex` has normalized sizes when LaTeX delivery is in scope, the paper uses those sizes unchanged, and the compiled paper page has been visually checked when a paper source is available.
