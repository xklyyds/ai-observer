@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo [%date% %time%] 任务开始执行 >> "%~dp0task_runner.log"
echo [%date% %time%] 工作目录: %cd% >> "%~dp0task_runner.log"
echo [%date% %time%] Python路径: %~dp0python >> "%~dp0task_runner.log"

python "%~dp0ai_daily_report.py" >> "%~dp0task_runner.log" 2>&1

set exit_code=%errorlevel%
echo [%date% %time%] 脚本执行完毕，退出码: %exit_code% >> "%~dp0task_runner.log"
echo. >> "%~dp0task_runner.log"

exit /b %exit_code%