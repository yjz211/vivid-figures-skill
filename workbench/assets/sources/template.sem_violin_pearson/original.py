#!/usr/bin/env python
"""Create residual violin and Pearson pair-grid figures for SEM survey data."""

from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


DEFAULT_ORDER = ["USE", "ATT", "PBC", "BI", "EVA", "AWA", "SN", "ETH"]
PREFIX_GROUPS = {
    "AWA": ("10\u3001", "@10\u3001"),
    "USE": ("11\u3001", "@11\u3001"),
    "EVA": ("12\u3001", "@12\u3001"),
    "ETH": ("13\u3001", "@13\u3001"),
    "SN": ("14\u3001", "@14\u3001"),
    "PBC": ("15\u3001", "@15\u3001"),
    "ATT": ("16\u3001", "@16\u3001"),
    "BI": ("17\u3001", "@17\u3001"),
}


def load_data(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    if suffix == ".sav":
        try:
            import pyreadstat
        except ImportError as exc:
            raise SystemExit("Reading .sav requires pyreadstat. Install it or use an XLSX source.") from exc
        df, _meta = pyreadstat.read_sav(str(path), apply_value_formats=False)
        return df
    if suffix == ".csv":
        return pd.read_csv(path)
    raise SystemExit(f"Unsupported data format: {path.suffix}")


def parse_json_arg(value: str | None, default):
    if not value:
        return default
    candidate = Path(value)
    try:
        if candidate.exists():
            return json.loads(candidate.read_text(encoding="utf-8"))
    except OSError:
        pass
    return json.loads(value)


def auto_construct_map(columns: list[str], exclude: dict[str, list[int]]) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for construct, prefixes in PREFIX_GROUPS.items():
        selected = [c for c in columns if str(c).startswith(prefixes)]
        if selected:
            removed = set(exclude.get(construct, []))
            keep = [i for i in range(len(selected)) if i not in removed]
            mapping[construct] = [selected[i] for i in keep]
    return mapping


def build_scores(df: pd.DataFrame, mapping: dict[str, list[str]], order: list[str]) -> pd.DataFrame:
    missing = [c for cols in mapping.values() for c in cols if c not in df.columns]
    if missing:
        raise SystemExit(f"Construct map references missing columns: {missing[:8]}")
    scored = pd.DataFrame(index=df.index)
    for construct in order:
        cols = mapping.get(construct)
        if not cols:
            raise SystemExit(f"No item mapping found for construct: {construct}")
        scored[construct] = df[cols].apply(pd.to_numeric, errors="coerce").mean(axis=1)
    return scored


def standardize(df: pd.DataFrame) -> pd.DataFrame:
    return (df - df.mean()) / df.std(ddof=0)


def residualize_each_variable(scored: pd.DataFrame, order: list[str]) -> pd.DataFrame:
    residuals = pd.DataFrame(index=scored.index)
    for y in order:
        x_cols = [c for c in order if c != y]
        x = scored[x_cols].to_numpy(float)
        yv = scored[y].to_numpy(float)
        mask = np.isfinite(yv) & np.isfinite(x).all(axis=1)
        X = np.column_stack([np.ones(mask.sum()), x[mask]])
        beta, *_ = np.linalg.lstsq(X, yv[mask], rcond=None)
        residuals.loc[mask, y] = yv[mask] - (X @ beta)
    return standardize(residuals[order])


def p_values(scored: pd.DataFrame, order: list[str]) -> pd.DataFrame:
    pmat = pd.DataFrame(index=order, columns=order, dtype=float)
    for a in order:
        for b in order:
            if a == b:
                pmat.loc[a, b] = 0.0
                continue
            pair = scored[[a, b]].dropna()
            _r, p = stats.pearsonr(pair[a], pair[b])
            pmat.loc[a, b] = p
    return pmat


def star(p: float) -> str:
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return ""


def available_times_font() -> str | None:
    candidates = [
        Path(r"C:\Windows\Fonts\times.ttf"),
        Path(r"C:\Windows\Fonts\timesbd.ttf"),
        Path(r"C:\Windows\Fonts\Times New Roman.ttf"),
    ]
    return next((str(p) for p in candidates if p.exists()), None)


def paper_comparison(corr: pd.DataFrame, paper: dict | None, order: list[str]) -> pd.DataFrame:
    if not paper:
        return pd.DataFrame()
    rows = []
    for a, b in combinations(order, 2):
        target = None
        if isinstance(paper.get(a), dict) and b in paper[a]:
            target = paper[a][b]
        elif isinstance(paper.get(b), dict) and a in paper[b]:
            target = paper[b][a]
        elif f"{a},{b}" in paper:
            target = paper[f"{a},{b}"]
        elif f"{b},{a}" in paper:
            target = paper[f"{b},{a}"]
        if target is None:
            continue
        rows.append({
            "var1": a,
            "var2": b,
            "computed": float(corr.loc[a, b]),
            "paper": float(target),
            "abs_diff": abs(float(corr.loc[a, b]) - float(target)),
        })
    return pd.DataFrame(rows).sort_values("abs_diff", ascending=False)


def draw_plots(
    scored: pd.DataFrame,
    residuals: pd.DataFrame,
    corr: pd.DataFrame,
    pmat: pd.DataFrame,
    order: list[str],
    out_dir: Path,
    prefix: str,
) -> dict[str, str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.cm import ScalarMappable
    from matplotlib.colors import LinearSegmentedColormap, Normalize
    from matplotlib.ticker import FuncFormatter
    import seaborn as sns
    from PIL import Image

    font_path = available_times_font()
    if font_path:
        font_manager.fontManager.addfont(font_path)
    plt.rcParams.update({
        "font.family": "Times New Roman",
        "font.size": 24,
        "axes.labelsize": 30,
        "xtick.labelsize": 24,
        "ytick.labelsize": 24,
        "axes.unicode_minus": False,
        "figure.dpi": 180,
        "savefig.dpi": 300,
    })
    sns.set_theme(style="whitegrid", rc={
        "font.family": "Times New Roman",
        "axes.edgecolor": "#AEB7C4",
        "grid.color": "#E5EAF0",
        "axes.facecolor": "#FFFFFF",
        "figure.facecolor": "#FFFFFF",
    })

    fill = "#87DED7"
    line = "#3049A1"
    dot = "#2D84AD"
    cmap = LinearSegmentedColormap.from_list(
        "paper_teal_blue",
        ["#25258F", "#5A69A8", "#F6FAFA", "#BEEAD6", "#53CDC9", "#4A98B9", "#25258F"],
        N=256,
    )

    long = residuals.melt(var_name="Variable", value_name="Residual")
    long["Variable"] = pd.Categorical(long["Variable"], categories=order, ordered=True)
    fig, ax = plt.subplots(figsize=(6.4, 11.0))
    sns.violinplot(
        data=long,
        y="Variable",
        x="Residual",
        order=order,
        orient="h",
        inner=None,
        color=fill,
        linewidth=1.8,
        cut=0,
        ax=ax,
    )
    for collection in ax.collections:
        collection.set_edgecolor(line)
        collection.set_alpha(0.75)
    rng = np.random.default_rng(20260626)
    for yi, var in enumerate(order):
        vals = long.loc[long["Variable"] == var, "Residual"].dropna().to_numpy()
        ax.scatter(vals, rng.normal(yi, 0.055, len(vals)), s=11, color=dot, alpha=0.28, edgecolors="none", zorder=3)
    ax.axvline(0, color="#6E7785", linestyle=":", linewidth=1.4)
    ax.set_xlim(-2.8, 2.8)
    ax.set_xlabel("Residual", fontsize=30)
    ax.set_ylabel("")
    ax.tick_params(axis="y", labelsize=30)
    ax.tick_params(axis="x", labelsize=26)
    ax.grid(axis="x", color="#E5EAF0", linewidth=1)
    ax.grid(axis="y", visible=False)
    sns.despine(ax=ax, top=False, right=False)
    ax.text(-0.02, 1.02, "(a)", transform=ax.transAxes, fontsize=34, fontweight="bold", ha="left", va="bottom")
    fig.tight_layout(pad=1.2)
    violin_png = out_dir / f"{prefix}_residual_violin.png"
    violin_svg = out_dir / f"{prefix}_residual_violin.svg"
    fig.savefig(violin_png, bbox_inches="tight")
    fig.savefig(violin_svg, bbox_inches="tight")
    plt.close(fig)

    n = len(order)
    fig = plt.figure(figsize=(16.8, 14.4))
    gs = fig.add_gridspec(n, n, wspace=0.03, hspace=0.03)
    norm = Normalize(vmin=-1, vmax=1)
    for i, row in enumerate(order):
        for j, col in enumerate(order):
            ax = fig.add_subplot(gs[i, j])
            for spine in ax.spines.values():
                spine.set_color("#AEB7C4")
                spine.set_linewidth(1.0)
            ax.tick_params(length=0, pad=3)
            if i == j:
                vals = scored[row].dropna()
                ax.hist(vals, bins=np.arange(1, 8.5, 0.5), color="#CBEFC9", edgecolor="#6FAB74", linewidth=1.0)
                try:
                    sns.kdeplot(x=vals, ax=ax, color=line, linewidth=1.6, bw_adjust=0.9)
                except Exception:
                    pass
                ax.set_xlim(0.8, 7.2)
                ax.set_yticks([])
                ax.set_xlabel("")
                ax.set_ylabel("")
            elif i > j:
                ax.scatter(scored[col], scored[row], s=10, color="#2BB8C6", alpha=0.34, edgecolors="none")
                ax.set_xlim(0.8, 7.2)
                ax.set_ylim(0.8, 7.2)
            else:
                value = corr.loc[row, col]
                ax.set_facecolor(cmap(norm(value)))
                ax.text(0.5, 0.57, f"{value:.3f}", transform=ax.transAxes, ha="center", va="center", fontsize=24, color="#202633")
                ax.text(
                    0.5,
                    0.38,
                    star(float(pmat.loc[row, col])),
                    transform=ax.transAxes,
                    ha="center",
                    va="center",
                    fontsize=24,
                    fontweight="bold",
                    color="#202633",
                )
                ax.set_xticks([])
                ax.set_yticks([])
            if i < n - 1:
                ax.set_xticklabels([])
            else:
                ax.set_xlabel(col, labelpad=10, fontsize=30)
            if j > 0:
                ax.set_yticklabels([])
            else:
                ax.set_ylabel(row, rotation=90, labelpad=20, fontsize=30)
            ax.grid(False)
    fig.text(0.03, 0.965, "(b)", fontsize=34, fontweight="bold", ha="left", va="top")
    cax = fig.add_axes([0.92, 0.13, 0.025, 0.75])
    cb = fig.colorbar(ScalarMappable(norm=norm, cmap=cmap), cax=cax)
    cb.set_ticks([-1, -0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75, 1])
    cb.ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _pos: "0.00" if abs(x) < 0.0005 else f"{x:.2f}"))
    cb.ax.tick_params(labelsize=24)
    cb.outline.set_edgecolor("#AEB7C4")
    fig.subplots_adjust(left=0.08, right=0.89, top=0.93, bottom=0.08)
    pearson_png = out_dir / f"{prefix}_pearson_pairgrid.png"
    pearson_svg = out_dir / f"{prefix}_pearson_pairgrid.svg"
    fig.savefig(pearson_png, bbox_inches="tight")
    fig.savefig(pearson_svg, bbox_inches="tight")
    plt.close(fig)

    img_a = Image.open(violin_png).convert("RGB")
    img_b = Image.open(pearson_png).convert("RGB")
    h = max(img_a.height, img_b.height)
    resample = getattr(Image, "Resampling", Image).LANCZOS
    img_a = img_a.resize((round(img_a.width * h / img_a.height), h), resample)
    img_b = img_b.resize((round(img_b.width * h / img_b.height), h), resample)
    combined = Image.new("RGB", (img_a.width + img_b.width + 40, h), "white")
    combined.paste(img_a, (0, 0))
    combined.paste(img_b, (img_a.width + 40, 0))
    combined_png = out_dir / f"{prefix}_violin_pearson_combined.png"
    combined.save(combined_png, quality=95)
    return {
        "violin_png": str(violin_png),
        "violin_svg": str(violin_svg),
        "pearson_png": str(pearson_png),
        "pearson_svg": str(pearson_svg),
        "combined_png": str(combined_png),
    }


def write_audit(
    out_dir: Path,
    prefix: str,
    mapping: dict[str, list[str]],
    scored: pd.DataFrame,
    residuals: pd.DataFrame,
    corr: pd.DataFrame,
    comparison: pd.DataFrame,
) -> Path:
    out = out_dir / f"{prefix}_plot_audit.xlsx"
    rows = [{"construct": k, "items_used": " | ".join(map(str, mapping[k]))} for k in mapping]
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        pd.DataFrame(rows).to_excel(writer, sheet_name="item_mapping", index=False)
        scored.to_excel(writer, sheet_name="construct_scores", index=False)
        residuals.to_excel(writer, sheet_name="residuals_z", index=False)
        corr.round(6).to_excel(writer, sheet_name="computed_corr")
        if not comparison.empty:
            comparison.round(6).to_excel(writer, sheet_name="paper_comparison", index=False)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--order", default=",".join(DEFAULT_ORDER))
    parser.add_argument("--exclude-json", default=None, help='JSON such as {"AWA":[0,2]} using zero-based item positions after auto-detection.')
    parser.add_argument("--construct-map-json", default=None, help="JSON string or file path mapping constructs to exact column names.")
    parser.add_argument("--paper-corr-json", default=None, help="Optional JSON string or file path with paper correlations for comparison.")
    parser.add_argument("--prefix", default="sem")
    args = parser.parse_args()

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    order = [x.strip() for x in args.order.split(",") if x.strip()]
    exclude = parse_json_arg(args.exclude_json, {})
    data = load_data(args.data)
    mapping = parse_json_arg(args.construct_map_json, None) or auto_construct_map(list(data.columns), exclude)
    scored = build_scores(data, mapping, order)
    corr = scored[order].corr()
    pmat = p_values(scored, order)
    residuals = residualize_each_variable(scored, order)
    paper = parse_json_arg(args.paper_corr_json, None)
    comparison = paper_comparison(corr, paper, order)
    figures = draw_plots(scored, residuals, corr, pmat, order, out_dir, args.prefix)
    audit = write_audit(out_dir, args.prefix, mapping, scored[order], residuals[order], corr, comparison)
    summary = {
        "source_data": str(args.data),
        "n_rows": int(data.shape[0]),
        "n_complete_construct_rows": int(scored[order].dropna().shape[0]),
        "order": order,
        "mapping": mapping,
        "figures": figures,
        "audit_workbook": str(audit),
    }
    if not comparison.empty:
        summary["mean_abs_diff_vs_paper_corr"] = float(comparison["abs_diff"].mean())
        summary["max_abs_diff_vs_paper_corr"] = float(comparison["abs_diff"].max())
    summary_path = out_dir / f"{args.prefix}_plot_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=True, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
