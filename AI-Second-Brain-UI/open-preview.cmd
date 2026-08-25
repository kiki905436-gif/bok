@echo off
setlocal
chcp 65001 >nul
set "BUNDLED_PYTHONW=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\pythonw.exe"
set "LOCAL_PYTHONW=%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"

if exist "%BUNDLED_PYTHONW%" (
  start "" "%BUNDLED_PYTHONW%" "%~dp0web_preview.pyw"
  exit /b 0
)

if exist "%LOCAL_PYTHONW%" (
  start "" "%LOCAL_PYTHONW%" "%~dp0web_preview.pyw"
  exit /b 0
)

where pythonw.exe >nul 2>nul
if not errorlevel 1 (
  start "" pythonw.exe "%~dp0web_preview.pyw"
  exit /b 0
)

where pyw.exe >nul 2>nul
if not errorlevel 1 (
  start "" pyw.exe -3 "%~dp0web_preview.pyw"
  exit /b 0
)

where winget.exe >nul 2>nul
if errorlevel 1 goto compatibility

echo Boujoy知识库需要 Python 3 才能使用搜索、编辑、记忆和备份功能。
choice /C YN /N /M "是否现在通过 Windows 官方 winget 安装 Python 3.12？[Y/N] "
if errorlevel 2 goto compatibility

winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements
if errorlevel 1 goto winget_failed

if exist "%LOCAL_PYTHONW%" (
  start "" "%LOCAL_PYTHONW%" "%~dp0web_preview.pyw"
  exit /b 0
)

where pyw.exe >nul 2>nul
if not errorlevel 1 (
  start "" pyw.exe -3 "%~dp0web_preview.pyw"
  exit /b 0
)

:install_failed
echo Python 安装完成但当前窗口还没有识别到它，请关闭后重新双击本文件。
pause
exit /b 1

:winget_failed
echo Python 安装没有完成，未改动知识库。请检查网络后重试，或从 python.org 安装 Python 3.12。
pause
exit /b 1

:compatibility
echo 未找到 Python，将打开仅浏览兼容模式；搜索、编辑、记忆和备份暂不可用。
call "%~dp0open-app-mode.cmd"
