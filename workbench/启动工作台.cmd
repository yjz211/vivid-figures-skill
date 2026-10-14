@echo off
chcp 65001 >nul
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -X utf8 scripts\manage.py serve --open
  goto done
)
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -X utf8 scripts\manage.py serve --open
  goto done
)
where python >nul 2>nul
if not errorlevel 1 (
  python -X utf8 scripts\manage.py serve --open
  goto done
)
echo 请先安装 Python 3.11 或更新版本，并按 README 安装依赖。
pause
exit /b 1
:done
if errorlevel 1 (
  echo 启动失败，请检查 Python 版本、依赖和 8766 端口占用。
  pause
)
