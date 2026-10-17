# 架构图语义配色

七套配色和自定义色与数据图共用 `original/resources/assets/shared-scripts/palettes.json` 及 `.vivid/config.json`。准备工作副本时复制该色板和读取器，不另维护颜色表。配色改变对象颜色，不改变布局、字体、透明度或连接；正文、底色、警告和状态色可按语义保留。资源没有预装通用角色映射，不能仅凭原色猜测所有对象身份。

## 196套 SVG 资产

在实际查看候选图和 `geometry.json` 后，于 `example.json` 添加当前图专用映射：

```json
{
  "palette": "project",
  "color_roles": {
    "compute": {
      "slot": 0,
      "tone": 0.8,
      "selectors": [{"keys": ["e0012"], "attributes": ["fill"]}]
    },
    "data-path": {
      "slot": 1,
      "selectors": [{"colors": ["#336699"], "attributes": ["stroke"]}]
    },
    "warning": {
      "preserve": true,
      "selectors": [{"keys": ["e0017"], "attributes": ["fill", "stroke"]}]
    }
  }
}
```

示例键和原色仅说明语法，必须替换成本图实际对象与颜色。`palette` 可为 `project`、七套预设 ID/名称、`custom` 或 `original`。`project` 使用当前运行目录向上查找的 `.vivid/config.json`，也可用 `palette_workspace` 或 `VIVID_WORKSPACE` 指定任务目录；不会从资产安装目录猜测项目。找不到项目配置时，已有角色映射使用默认橄榄杏棕。自定义遵循同一配置格式：`palette: "custom"` 加至少两个 `#RRGGBB` 的 `colors`。

`slot` 是分类顺序中的零起始索引，七套预设按 canonical `category_order`，自定义保持指定顺序。索引越界报错，不循环复用。`tone` 范围 -1 到 1，0 使用原色，正值向白色混合，负值向黑色混合；例如同一身份的浅容器 `0.8`、边框 `0` 可以共用一个 slot。调色后仍需检查实际文字对比度，工具不自动改文字颜色或宣称符合可读性标准。

选择器的 `keys` 匹配 `data-asset-key`，`ids` 匹配 SVG `id`，`colors` 匹配原始 RGB；同时提供时是交集，各数组内部是并集。`colors` 支持 HEX 与 RGB/RGBA，可匹配不同 alpha 的同一 RGB；原 alpha 保留。`attributes` 支持 `fill`、`stroke`、`stop-color`，建议逐项明确。只有颜色的选择器匹配显式颜色声明；指定对象可以覆盖继承颜色。文字 `tspan`、独立箭头头部、图例及跨区域同对象须纳入映射；不自动沿对象关系传播颜色。

渐变应给具体 `<stop id="...">` 添加 `ids` 选择器，并使用 `stop-color`。`url(#gradient)`、渐变位置、透明度及 `stop-opacity` 不受替换。共享渐变会影响所有引用该渐变的对象，若语义不同先在工作副本拆成独立渐变。CSS 样式表类选择器和 `currentColor` 不做计算推断；先改成明确的局部颜色声明再映射。代码生成的图使用独立 helper 时也遵守此限制。

`preserve: true` 角色优先保护选中颜色。其余互相冲突的角色、未知键、无匹配颜色、无效色板/slot 均报错，不静默忽略。不配置角色、未请求配色且任务没有显式配色配置时，历史默认输出不变；请求了配色或项目已指定配色但没有映射时明确提示补映射。需要忠实查看原色可设置 `palette: "original"`，它会跳过配色。角色在文字/部件编辑及 `customize()` 后统一应用，整图和部件采用同一结果，元数据记录角色与色板。

## 历史 Python 生成器兼容

VA-001–004 的当前目录均指向 SVG 资产，使用上面的 `color_roles` 接口。`architecture/templates/` 下的旧 Python 生成器只为已有项目保留。继续维护旧项目时，可将生成的 SVG 根元素交给 `apply_palette(root, config)`，或在构图函数中显式使用色板的分类颜色。接入前先检查旧生成器已支持的颜色参数，不能假定它们与 SVG 资产 JSON 接口一致。

```python
from semantic_palette import apply_palette
changes = apply_palette(root, config)
```

改造后照常输出 SVG、PNG、PDF 和部件，并检查同身份颜色一致、原语义区分、警告色、黑白印刷和实际论文缩放下的可读性。语义角色数多于当前色板可区分颜色时，应结合容器、线型、形状、纹理等编码，而不是无声重复颜色。
