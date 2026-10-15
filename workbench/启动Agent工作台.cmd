@echo off
chcp 65001 >nul
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -X utf8 scripts\manage.py agent --open
) else (
  python -X utf8 scripts\manage.py agent --open
)
if errorlevel 1 (
  echo 请按 docs\AGENT-WORKBENCH.md 安装 Agent 依赖，或检查 8766 端口是否已占用。
  pause
)
