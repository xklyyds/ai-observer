@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   AI日报任务注册工具
echo ========================================
echo.

powershell -ExecutionPolicy Bypass -Command "Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File ""%cd%\register_task_final.ps1""' -Verb RunAs"

echo.
echo 如果没有弹出管理员授权窗口，请手动以管理员身份运行PowerShell，
echo 然后执行以下命令:
echo cd "%cd%"
echo powershell -ExecutionPolicy Bypass -File register_task_final.ps1
echo.
pause