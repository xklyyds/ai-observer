$taskName = "AI日报任务"
$pythonPath = (Get-Command python).Source
$taskPath = "C:\Users\28352\Desktop\AI前沿观察者\AIobserve\ai_daily_report.py"
$workingDir = "C:\Users\28352\Desktop\AI前沿观察者\AIobserve"

Write-Host "Python路径: $pythonPath"
Write-Host "任务路径: $taskPath"
Write-Host "工作目录: $workingDir"

$action = New-ScheduledTaskAction -Execute $pythonPath -Argument "`"$taskPath`"" -WorkingDirectory $workingDir

$trigger = New-ScheduledTaskTrigger -Daily -At 20:00

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U -RunLevel Highest

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -WakeToRun -ExecutionTimeLimit (New-TimeSpan -Hours 1) -Hidden $false

$task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Settings $settings

try {
    Register-ScheduledTask -TaskName $taskName -InputObject $task -Force
    Write-Host "任务 '$taskName' 已成功注册，每天晚上8点自动执行" -ForegroundColor Green
    Write-Host "下次运行时间: 明天晚上8点" -ForegroundColor Cyan
} catch {
    Write-Host "任务注册失败: $_" -ForegroundColor Red
    Write-Host "请确保以管理员身份运行此脚本" -ForegroundColor Yellow
}