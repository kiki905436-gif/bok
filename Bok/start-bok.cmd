@echo off
setlocal
chcp 65001 >nul
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "VAULT_DIR=%%~fI"
set "PYTHONPATH=%SCRIPT_DIR%"
if not defined TEMP set "TEMP=%VAULT_DIR%\.bok\tmp"
set "PYTHONPYCACHEPREFIX=%TEMP%\bok-pycache"
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  py -3 -m bok_core --vault "%VAULT_DIR%" serve
  exit /b
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  python -m bok_core --vault "%VAULT_DIR%" serve
  exit /b
)

echo 找不到 Python 3。请先双击 AI-Second-Brain-UI\open-preview.cmd 按提示安装，或从 python.org 安装 Python 3.12。
exit /b 1
