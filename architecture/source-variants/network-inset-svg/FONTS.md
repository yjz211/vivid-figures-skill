# Typography is part of the asset

`font_profile.json` records font roles and the reference's size hierarchy at 468 pt width. Serif labels use Times New Roman; machine/event labels use Consolas. The reference specimen ranges from 7.83 pt auxiliary labels to 11.44 pt primary labels. Those values describe this figure and do not establish universal paper standards.

Two **explicit** profiles are available in `example.json`:

- `"font_profile": "reference-system"` preserves the reference families using installed Times New Roman and Consolas. Required faces and actual glyphs are checked before generation. Missing fonts produce an actionable error rather than silent substitution. The exported PDF embeds the fonts; the editable SVG requires those local families.
- `"font_profile": "portable"` uses bundled Tinos (serif) and Inconsolata (monospace). These are visibly different fonts, not an exact replacement. Full unmodified OFL font files, regular/bold and serif italic/bold-italic faces, licence text, source URLs/commits and hashes accompany the working copy. The SVG embeds the used font faces and keeps text editable. No OS font installation is needed. Geometry and final labels must be rechecked after switching profiles.

`font_assets.py` applies the selected profile after SVG object edits; retain the `apply_font_profile()` call when adapting `make_figure.py`. Font files are available in the prepared working directory's `fonts/`; this SVG asset includes the same portable pack in its own `fonts/`. Font hashes are verified against its manifest. The original paper SVG's embedded subset is not a full-font resource and is not used as a general font pack.

The renderer writes `fig.fonts.json`: selected faces and hashes, checked characters, actual PDF font names and embedding status. A PDF with unexpected fallback fonts or missing font-program embedding is reported as an error. The checks do not replace visual inspection of glyph shape, letter spacing, italics, line breaks or the final paper width.

The thin wrapper refreshes font metadata after SVG edits. With the original profile, specify `font_family` as `Times New Roman` or `Consolas` according to `labels.json` when replacing a label through `labels`, so the generic PDF-subset fallback does not alter the intended role. For another language's font profile, use a matching role alias as described below. Unsupported characters fail generation. Font sizes and object geometry remain editable in SVG.

## Chinese and other characters outside the original fonts

Keep the requested language, including the Skill's default Chinese. The original reference families and the bundled Tinos/Inconsolata portable pack do not cover Chinese; changing only `font_profile` to `portable` does not solve missing glyphs. Adapt the prepared working copy's `font_profile.json`, keeping the serif and monospace roles distinct:

1. For each affected role, set `reference_family` to an available full font family that covers the actual labels and retains that role. Verify the required real regular, bold and italic faces where used. The current validator opens single-font TTF/OTF files; TTC/OTC collections are not supported by this path. Choose compatible font files that Matplotlib can resolve, rather than assuming any installed family will work.
2. Keep the original `source_aliases` and add the selected family name. Aliases identify a text object's role; `reference_family` selects its output family. For `labels` replacements, explicitly use either an original alias or the new alias in `font_family`, matching the label's role. Omitting it can trigger the generic runtime's unrelated fallback.
3. Use `"font_profile": "reference-system"` and retain the final `apply_font_profile()` call. It resolves the configured families and rejects missing glyphs. Recheck actual face selection, text width, wrapping and final-size layout after replacement; glyph validation alone does not establish visual fidelity.

This changes only the working copy's font choices. It does not add Chinese fonts to the bundled portable pack, and `reference-system` does not embed font files into SVG. Record the selected fonts and provide permitted font files or acquisition instructions for the target machine. Do not remove validation or relabel Chinese text in English to bypass a missing-font error.

Preparing a standalone SVG asset must copy `font_assets.py`, `font_profile.json`, this file, and the asset-local `fonts/` pack (Tinos, Inconsolata, OFL licences, provenance and manifest). System reference fonts are not redistributed. Generic source-asset replacement fonts may also be present; they do not replace the explicit font roles.
