# 配色选择

本 Skill 使用一套绘图指导，配色只决定颜色搭配。七套配色及颜色顺序唯一维护于 [palettes.json](original/resources/assets/shared-scripts/palettes.json)，文档和示例不另存一份颜色表。

架构资产也可使用同一项目色板，按 [架构图语义配色](architecture/PALETTE.md) 为实际对象填写角色映射，保留同身份颜色一致、浅底与深描边层次及必要状态色。此路线不套用普通框图的统一单主色规则，也不盲目按原色出现顺序替换；当前没有为全部资产预标注颜色角色。

可选：**橄榄杏棕（默认）**、珊瑚青绿、蓝粉浅彩、蓝天绿地、柔绿森林、粉彩少女、海洋清风，以及自定义颜色。「橄榄行踪」按现有橄榄杏棕识别。

分类图的 `pu.PALETTE`、`pu.COLORS` 和默认颜色循环使用色板的固定 `category_order`（从 0 开始的索引），优先取差异明显的颜色；色值仍只保存一份。连续色阶使用 `palette_colors()` 的原顺序或下述热图接口，不套用分类顺序。自定义颜色保留用户指定的顺序，无需新增绘图步骤。

已有选择时沿用，补图或修图不重复询问。用户未指定配色时使用默认；明确要求由助手决定时可选择并简短告知。用户自己的颜色优先，不按目录名抽选主题。

在初始化工作区后，用所选 Python 执行：

```bash
python _utils/vivid_config.py palettes
python _utils/vivid_config.py set palette olive-apricot
```

命令可加 `--workspace <任务目录>`，也可在其子目录运行。配置保存在 `.vivid/config.json`。预设只保存 ID，读取时从色板文件取得颜色；自定义使用 `palette: "custom"` 与至少两个 HEX 字符串构成的 `colors` 数组。一次写入自定义设置：

```python
from _utils.vivid_config import write_config
write_config(workspace, palette="custom", colors=user_colors)
```

生成代码在 `setup_style()` 后读取 `pu.PALETTE` / `pu.COLORS`。换色不改变已选模板、用户已有版式、字体尺寸、渐变、透明度或审图要求。分类色与热图色阶均随项目选择。热图使用 `_utils.palette_maps.palette_cmap` / `palette_stops`；连续量保留连续插值，正负量保留中性中心。用户明确指定固定科学色图时才保留该色图。流程/框图统一主色，工程图保留原配色，批注白底，具体执行见 [绘图指导](original/drawing-guide.md)。

热图接口每次读取当前配置，支持七套预设和自定义配色。`sequential` 从浅色到主题首色；`diverging` 使用首色和色板中与之差异最大的颜色，避免两个相近色作为两端。`palette_stops` 可保留原模板的中性色和色阶节点数；文字用 `contrast_text` 根据实际底色和透明度选择黑白对比色。
