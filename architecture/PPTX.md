# 可编辑 PowerPoint 导出

在 [A/B 双候选流程](WORKFLOW.md)中，用户选定候选后默认直接执行本节，交付所选版本的 **原生可编辑 PPTX + SVG + PDF**，不再询问格式或导出确认。用户明确另有格式要求时按其要求。单独请求 PowerPoint 导出也使用本节；候选尚未选定时先展示预览并等待选择，不预先批量转换候选或整个资源库。

转换来源必须是**用户所选图的当前 SVG**。在新的交付目录复制该版 SVG、对应 PDF 与结构信息，并记录来源；若生成器调整了图件，应先重新渲染同版 PDF。PPTX 是独立的人工编辑副本，不自动回写 SVG。

```text
python "<SKILL>/scripts/export_architecture_pptx.py" figures/control/fig.svg --out figures/control/fig.pptx --structure figures/control/structure.json
```

准备工作副本时已复制该命令和运行模块，也可在副本中运行 `python export_architecture_pptx.py fig.svg --out fig.pptx`。同目录 `structure.json` 存在时自动使用；`--structure` 可明确选择。Windows 有 PowerPoint 时追加 `--office-verify` 做实际 Office 验证。默认宽度720pt，可用 `--width-pt` 改变，长宽比不变。已有 PPTX 默认不覆盖；明确需要重新导出时使用新文件名，或在确认不会丢失手改内容后使用 `--force`。

核对成功退出和完整 `.pptx-report.json`，将其中 `svg_sha256` 与交付 SVG 对照，并在交付记录保存结构文件的版本。Office 验证失败前可能已写出 PPTX，因此仅文件存在不算成功。组报告中的 `splits` 可能用于维持画序；缺失成员或意外未归属对象则应核对修复。

## 能编辑什么

- 几何输出为 PowerPoint 原生自由形状和路径，文字输出为原生文本框，无整图位图或整图 SVG 包装。保留字体、字重、颜色、透明度、曲线、普通箭头和裁切后的可见几何。
- 按 `structure.json` 的部件组织具名组；代码图可从 SVG 的具名祖先组推导。点击模块可整体移动，再进入组内改文字或单个形状，也可取消组合。
- 重叠部件采用明确的单一归属；共享对象可能独立。画序冲突时一个语义部件会拆成多个带编号的组，报告会列出。不会为追求一个组而复制对象或改变遮挡。
- **移动模块不会自动重接箭头**。线条仍需手动调整；公式字母和上下标保持可编辑文本，不声称恢复为 PowerPoint 公式编辑器对象。
- PDF 提取底稿有时省略空格、仅保留字间坐标。转换器会按局部字距恢复词间空格并记录数量；复杂排版可能分成多个文本框，不能保证整段只有一个框。

## 字体与验证

输出附带同名 `.fonts/` 目录，含 SVG 实际内嵌的字体、说明和安装入口。Windows 可运行 `python fig.fonts/install_fonts.py`，或导出时加 `--install-fonts`，只安装到当前用户；macOS 使用字体册。SVG 没有内嵌的系统字体需在目标机器另行具备。

`--office-verify` 需要 Windows 的 Microsoft PowerPoint：保存嵌入字体、重新打开，生成 `.powerpoint.png`、`.powerpoint.pdf`。保留字体包：某些 Office 渲染路径和第三方编辑器会忽略嵌入字体。本机已观察到未安装字体时 PNG 导出替换、但同一 PPTX 的 Office PDF 导出字体正确，因此不能单凭有字体二进制或一次 PNG 断言跨机正常。

导出后检查 PPT 内确有原生文本和矢量形状、具名组及对应来源版本；在独立检查副本试改一个标签、移动一个模块并保存重开，不把试改后的样例当最终交付。环境有 PowerPoint 时查看实际 PowerPoint/PDF 效果，检查文字基线、上下标、箭头、遮挡与边界。缺少 Office 时仍可生成原生 PPTX 并做结构/读写核验，但明确未做 Office 视觉验证；不能把源码预览称为 PowerPoint 渲染。`.pptx-report.json` 记录对象、分组、字体和限制，计数通过不能替代视觉检查。首批已验证分层、多区域复杂和数学符号样例；这不代表196套或任意 SVG 已全部通过。

最终直接提供 PPTX、SVG、PDF 三个链接，附字体包及必要的使用说明。源码和诊断报告保留在交付目录，用户要求时提供；无需用内部检查清单打断下载流程。

## 环境与边界

Python 依赖登记在 Skill 根目录的 `requirements-architecture.txt`，准备工作副本时也会携带：`python-pptx>=1.0.2`、`lxml`、`playwright`（Chromium）、`shapely>=2`、`fonttools`；Office 检查额外需要 `pywin32`。可只安装该清单；根 `requirements.txt` 也已引用。安装依赖后首次运行 `python -m playwright install chromium`。不依赖 FigGenie 的脚本或资源。

当前支持基本路径/矩形/圆/椭圆/折线、多层变换、纯色和透明度、实线/虚线、真实矢量裁切及 Vivid 普通线段箭头。复杂裁剪与非等比描边会以约0.02pt容差转为可编辑矢量轮廓。位图、渐变、滤镜、混合效果、复杂 marker、倾斜/非等比文字、真实裁掉部分字形等尚不支持时明确报错，不静默栅格化；在工作 SVG 中改成已支持的表达后再导出。

导出代码所需 MIT 声明随 `scripts/pptx_runtime/NOTICE-pptx.txt` 分发；字体许可随字体包保留。

## 从工作台导出

完整本地工作台的[模块编辑器](EDITOR.md)可以直接导出当前保存版本的 PPTX，或包含字体、SVG、结构与报告的 ZIP。网页编辑与 PPT 使用相同模块归属，复杂模块在 PPT 中仍可能为保持画序拆成多个组。网页不会自动安装字体，也不会调用 Office 检查；跨电脑使用优先带上字体包并按上文检查。
