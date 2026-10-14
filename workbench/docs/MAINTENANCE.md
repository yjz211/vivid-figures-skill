# 工作台维护

## 运行与检查

在 `workbench/` 中使用 Python 3.11+。运行依赖见 `requirements.txt`；测试依赖见 `requirements-dev.txt`，静态检查另需 Node.js。当前浏览器回归使用 Windows 标准安装路径下的 Chrome；其他系统需调整测试中的 Chrome 路径。

```sh
python -X utf8 scripts/manage.py serve --open
python -X utf8 scripts/manage.py check
python -X utf8 scripts/manage.py check --skill-root ..
python -m pip install -r requirements-dev.txt
python -X utf8 scripts/manage.py test
```

`test` 校验当前服务确属这个工作台；服务未运行时临时启动，结束后关闭。测试覆盖图库、全部预览资源、新旧前端地址兼容、数据整理、多表导入、文字点选与拖动，以及新图导出和独立复现。测试明确记录的临时项目移到 `verification/test-projects/`。

8766 端口已被其他服务或另一份工作台使用时，先停止对应服务再启动本副本。不要同时启动仓库副本和桌面的安装副本。

## 代码位置

| 修改内容 | 位置 |
| --- | --- |
| 图库、搜索 | `frontend/app.js`、`frontend/style.css` |
| 表格、字段、编辑状态 | `frontend/editor.js`、`frontend/grid.js` |
| 布局、数据整理 | `frontend/studio.*`、`frontend/data-transform.js` |
| 对象选择、文字拖动 | `frontend/direct-edit.js`、`frontend/interactions.*`、`editor_backend/object_editor.py` |
| 数据契约、模板适配 | `editor_backend/schema.py`、`catalog_data.py`、`engine.py` |
| 本地服务、项目保存 | `editor_backend/server.py`、`library.py` |

HTML 保留根目录入口，JS/CSS 位于 `frontend/`。服务兼容整理前的根目录 JS/CSS 地址，并要求页面与前端资源重新校验缓存。

## 模板来源

`assets/sources/<编号>/original.py` 是原始源码，`preview.py` 是图库运行版本。`docs/template-manifest.json` 记录原始来源、预览、下载包及共享文件的 SHA-256。工作台运行时使用自带资源；不会自动读取已安装的 Codex Skill。

新增或更新模板时，同时核对数据契约、卡片、预览、下载包与来源记录；完成对应图形和独立复现验证后更新快照。不要为消除检查错误而直接重算所有哈希。

维护当前源码和静态资源即可；过去的一次性构建脚本没有作为发布入口包含在仓库中。

## 本地文件

`workspace/library/` 保存项目和样式，`workspace/jobs/` 保存绘图任务，`verification/` 保存测试输出。以上目录由运行过程创建，全部忽略，不随 GitHub 发布；备份时优先保留用户库。

如果本机另有历史任务，可手动维护 `workspace/archive-jobs.json`，使用 `{"version":1,"roots":["../归档/日期/工作台/workspace/jobs"]}` 登记路径。服务只接受工作台上一级「归档」目录内的路径。普通下载使用无需此文件，也不需要历史归档。

工作台目录不包含嵌套 `.git`，跟随仓库统一提交。`.gitattributes` 保留模板资源和共享运行文件的原字节，避免源码哈希因换行转换失效。
