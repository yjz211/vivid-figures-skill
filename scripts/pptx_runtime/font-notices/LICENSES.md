# Vivid 架构资源字体与许可

All files here are free fonts that may be embedded in SVG output and redistributed with the skill.
These full font files support the explicit font mappings embedded in Vivid diagram.svg assets. They are replacement families, not a promise of identical glyph shapes or spacing.

| family | files | substitutes | license |
|---|---|---|---|
| Arimo | Arimo-*.ttf | Arial, Liberation Sans | SIL Open Font License 1.1 (Google / Monotype, ChromeOS core fonts) |
| Tinos | Tinos-*.ttf | Times New Roman, Liberation Serif | SIL Open Font License 1.1 |
| Carlito | Carlito-*.ttf | Calibri | SIL Open Font License 1.1 (tyPoland Lukasz Dziedzic) |
| TeX Gyre Heros | texgyreheros-*.otf | Helvetica, Helvetica Neue, Nimbus Sans | GUST Font License (LPPL-compatible) |
| TeX Gyre Termes | texgyretermes-*.otf | Times, Nimbus Roman | GUST Font License |
| Latin Modern Roman / Sans | lmroman10-*.otf, lmsans10-*.otf | Computer Modern | GUST Font License |
| DejaVu Sans | DejaVuSans*.ttf | Verdana, matplotlib default | Bitstream Vera / DejaVu license |
| Inter | Inter-*.otf | modern UI sans | SIL Open Font License 1.1 |
| Roboto | Roboto-*.otf | Roboto | Apache License 2.0 |
| Source Sans Pro | SourceSansPro-*.otf | Source Sans | SIL Open Font License 1.1 |

Sources: the files were copied from a TeX Live 2025 installation (`texmf-dist/fonts/{truetype,opentype}`),
which redistributes them under the licenses above. Full license texts are available in TeX Live
(`texmf-dist/doc/fonts/<name>/`) and from the upstream projects.

Vivid 的 diagram.svg 包含本图字体映射及已用字体的嵌入样式；source_asset.py 在文字适配时补充所需完整字体。准备工具复制本目录。不要依赖其他 Skill 的字体脚本。Inconsolata 的许可见 Inconsolata-OFL.txt；各字体文件自身的版权、许可及来源信息另见 font-notices.json。


STIX Two Math (`STIXTwoMath-Regular.ttf`) 用于完整数学字母和运算符覆盖，遵守附带的 [SIL Open Font License](STIXTwoMath-OFL.txt)。来源、版本和 SHA-256 见 [STIXTwoMath-provenance.json](STIXTwoMath-provenance.json)。仅数学或相应符号片段使用该族，正文沿用各自字体角色。
