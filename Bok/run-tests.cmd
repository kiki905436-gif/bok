@echo off
setlocal
chcp 65001 >nul
set "SCRIPT_DIR=%~dp0"
set "PYTHONPATH=%SCRIPT_DIR%"
if not defined TEMP set "TEMP=%SCRIPT_DIR%tmp"
set "PYTHONPYCACHEPREFIX=%TEMP%\bok-pycache"
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  py -3 -m unittest discover -s "%SCRIPT_DIR%tests" -v
  exit /b
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  python -m unittest discover -s "%SCRIPT_DIR%tests" -v
  exit /b
)

echo 找不到 Python 3，无法运行 Bok 测试。
exit /b 1
