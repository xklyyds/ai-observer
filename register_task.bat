@echo off
cd /d "%~dp0"
schtasks /create /tn "AI日报任务" /tr "python ""%cd%\ai_daily_report.py""" /sc daily /st 20:00 /rl highest /f
echo 任务注册完成
pause