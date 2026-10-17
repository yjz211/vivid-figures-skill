# Figure Routing Contract — Mathematical Modeling

Reproduce the pattern: the analysis stage classifies every planned figure, records the decision in `FIGURE_MANIFEST`, then the drawing stages execute and reconcile that contract.

## Decision order

1. Determine what the figure must prove: numerical result, model logic, exact mathematical construction, or physical scene.
2. Classify measured, simulated, optimized, or statistical evidence as DATA.
3. Route model/system/solution architecture to `ARCHITECTURE` and the SVG asset workflow at `../../../architecture/WORKFLOW.md`, unless the user specifies another supported format or exact mathematical construction needs TikZ. Route other non-data diagrams that need reproducible structure into `paper-technical-diagram`: Draw.io for editable engineering/physical schematics; TikZ for exact 2-D geometry, formulas, force/optical constructions, or coordinate-based diagrams.
4. Classify only genuinely pictorial or complex 3-D physical/engineering scenes that deterministic Draw.io/TikZ cannot communicate well as ILLUSTRATION.
5. HTML and Mermaid are opt-in formats. They do not replace the default Draw.io pass unless the user explicitly selects them.

## Renderer classes

| Class | Use it for | Primary workflow | Hard boundary |
|---|---|---|---|
| DATA/TABLE | trends, comparisons, distributions, uncertainty, sensitivity, convergence, validation, optimization results, heatmaps, data maps | `paper-figure` | never invent values or use AI illustration as evidence |
| ARCHITECTURE | model, system, solution architecture adapted from an SVG asset | `architecture-assets` → `../../../architecture/WORKFLOW.md` | follow A/B → actual user selection → selected PPTX/SVG/PDF; explicit format and existing-version requests take precedence |
| DRAWIO | editable engineering schematic, physical-relation diagram, apparatus or spatial layout, required roadmap, workflow, pipeline, hierarchy, decision tree, Gantt, compact network, conceptual framework | Draw.io path in `paper-technical-diagram` | not for statistical curves or formula-dense exact geometry |
| TIKZ | exact 2-D engineering/physical construction, feasible region, phase plane, force/optical diagram, true geometric derivation, formula-bearing algorithm, mathematically exact architecture/topology | TikZ path in `paper-technical-diagram` | ordinary function/data curves remain DATA |
| ILLUSTRATION | genuinely pictorial or complex 3-D object/scene that deterministic drawing cannot communicate adequately | `paper-illustration` | maximum 1–2 scene figures; never replace DATA or a feasible Draw.io/TikZ engineering diagram |
| HTML | explicit HTML/CSS structure-diagram request | `paper-figure-html` | not the competition default |
| MERMAID | explicit Mermaid or text-native maintenance request | `mermaid-diagram` | not the default final-paper renderer |

`paper-technical-diagram` is the Draw.io/TikZ umbrella, not a flowchart-only tool; it does not reinitialize a selected ARCHITECTURE asset workflow. If DATA versus TIKZ is uncertain, choose DATA. If deterministic diagram versus ILLUSTRATION is uncertain, choose the appropriate deterministic route.

## Modeling triggers

For a complete competition paper, include one overall technical roadmap with `purpose=roadmap` in the selected deterministic class (ARCHITECTURE, DRAWIO, TIKZ, HTML, or MERMAID). The basename is semantic, not fixed to `fig_roadmap`. Honor explicit user format choices and do not add a duplicate Draw.io roadmap. Add further figures only when the problem demands them:

- evaluation/ranking/AHP/TOPSIS/fuzzy assessment -> indicator hierarchy;
- scheduling/resource allocation -> Gantt or schedule diagram;
- graph/logistics/network optimization -> network topology or route map;
- deep or ensemble model -> exact model architecture;
- causal/path/SEM model -> variable-relation diagram;
- custom iterative optimization -> formula-bearing algorithm flow;
- multi-stage cleaning/feature engineering/modeling -> data pipeline;
- spatial data -> spatial evidence plot;
- reasoning-dense geometry -> true derivation construction plus necessary result/validation plots;
- engineering apparatus, physical relationship, force/ray construction, or 2-D spatial mechanism -> `paper-technical-diagram`, choosing Draw.io or TikZ internally;
- genuinely pictorial or complex 3-D physical/engineering scene that the deterministic paths cannot express clearly -> at most 1–2 ILLUSTRATION figures.

Do not create one near-identical flowchart per subproblem unless the user explicitly requests it. Do not force unrelated evidence into a multi-panel figure merely to reduce page count.

## Manifest contract

Create or update a planning document containing the anchored block below. Preserve existing entries and revise them rather than creating competing manifests.

```markdown
<!-- BEGIN FIGURE_MANIFEST -->
## 图表清单（FIGURE_MANIFEST）

**数据图（matplotlib；paper-figure）：**
- fig_q1_result | claim=... | source=figures/q1_results.json | section=问题一结果 | language=zh | format=pdf,png | layout=single-landscape

**DrawIO 确定性技术图（paper-technical-diagram）：**
- fig_roadmap | purpose=roadmap | claim=... | source=PROBLEM_ANALYSIS.md | section=问题重述 | language=zh | format=drawio,pdf,png | layout=single-landscape

**ARCHITECTURE SVG架构资产（architecture-assets）：**
- fig_model_architecture | claim=... | source=MODELING_REPORT.md | section=模型构建 | language=zh | format=pptx,svg,pdf | layout=single-landscape

**TikZ 精确图（paper-technical-diagram）：**
- tikz_q2_geometry | claim=... | source=MODELING_REPORT.md | section=问题二模型 | language=zh | format=tex,pdf | layout=single

**AI 场景图（paper-illustration）：**
- fig_scene | claim=... | source=题面物理场景 | section=问题重述 | language=zh | format=png | layout=single-landscape

**显式可选格式（HTML / Mermaid）：**
- none

**总数：** DATA=1, ARCHITECTURE=1, DRAWIO=1, TIKZ=1, ILLUSTRATION=1, OPTIONAL=0, ALL=5
<!-- END FIGURE_MANIFEST -->
```

Each entry must identify a semantic basename, claim, factual source, destination section, paper language, output formats, and intended page layout. Preserve `purpose=roadmap` or `purpose=derivation` from the JSON plan when present. Use `fig_` for ordinary figures, `tikz_` for TikZ, and `TABLE_` for tables. A figure belongs to one primary class only. The example demonstrates sections, not a mandatory five-figure set; remove empty entries and do not duplicate a roadmap across formats. Legacy DRAWIO `fig_roadmap` without purpose is accepted with a migration warning.

HTML and MERMAID plans share the OPTIONAL section. Preserve the JSON class as `renderer=HTML` or `renderer=MERMAID`, independently of actual delivery formats: for example, `purpose=roadmap | renderer=MERMAID | format=pdf,png` is valid when the user only requests those exports. Native `html`, `mmd`, or `mermaid` in `format` also identifies the route for existing manifests. Do not add unrequested native outputs merely to satisfy classification.

## Fixed execution and recovery

Run non-empty classes in this order:

1. `paper-figure` for DATA/TABLE.
2. `architecture-assets` for ARCHITECTURE; follow `../../../architecture/WORKFLOW.md`, including actual selection before final PPTX export. Candidate pairs count as one planned figure.
3. `paper-technical-diagram` for DRAWIO/TIKZ.
4. `paper-illustration` only for qualifying ILLUSTRATION entries.
5. Explicit optional formats, if any.

After every pass, reconcile each planned basename against actual artifacts. A missing item keeps the task open. Do not silently drop, rename, or reclassify it. Existing valid outputs must be preserved on resume; regenerate only missing or failed items.
