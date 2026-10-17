# Typography is part of the asset

`font_profile.json` records font roles and the reference's size hierarchy at 468 pt width. Serif labels use Times New Roman; machine/event labels use Consolas. The reference specimen ranges from 7.83 pt auxiliary labels to 11.44 pt primary labels. Those values describe this figure and do not establish universal paper standards.

Two **explicit** profiles are available in `example.json`:

- `"font_profile": "reference-system"` preserves the reference families using installed Times New Roman and Consolas. Required faces and actual glyphs are checked before generation. Missing fonts produce an actionable error rather than silent substitution. The exported PDF embeds the fonts; the editable SVG requires those local families.
- `"font_profile": "portable"` uses bundled Tinos (serif) and Inconsolata (monospace). These are visibly different fonts, not an exact replacement. Full unmodified OFL font files, regular/bold and serif italic/bold-italic faces, licence text, source URLs/commits and hashes accompany the working copy. The SVG embeds the used font faces and keeps text editable. No OS font installation is needed. Geometry and final labels must be rechecked after switching profiles.

`font_assets.py` applies the selected profile in the generator; retain the `apply_font_profile()` call when adapting `make_figure.py`. Font files are available in the prepared working directory's `fonts/`; the installed asset uses Vivid `architecture/fonts/`. Font hashes are verified against its manifest. The original paper SVG's embedded subset is not a full-font resource and is not used as a general font pack.

The renderer writes `fig.fonts.json`: selected faces and hashes, checked characters, actual PDF font names and embedding status. A PDF with unexpected fallback fonts or missing font-program embedding is reported as an error. The checks do not replace visual inspection of glyph shape, letter spacing, italics, line breaks or the final paper width.

Preview all six supported faces with `python font_specimen.py --profile portable --out font-specimen`, then `python render_architecture.py font-specimen/fig.svg`. Switch the profile to `reference-system` for a comparison. Unsupported characters fail generation; this English architecture pack is not a Chinese or full mathematical-typesetting font pack. Add an appropriate licensed family and explicit role mapping when the content needs one.

Scaled source backgrounds keep their outline thin via `piece(..., keep_stroke=True)`; labels are laid out separately. Do not enlarge a complete group of source text to fit a new layout, or reduce all labels to keep the old canvas. Body, IDs and event labels should retain a deliberate hierarchy.

This profile only governs this architecture asset. Vivid's existing data-figure defaults, Chinese-font resources and the user's explicit font choices elsewhere are unchanged.
