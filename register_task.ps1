$taskName = "AI前沿观察者日报任务"
$taskPath = "C:\Users\28352\Desktop\AI前沿观察者\AIobserve\ai_daily_report.py"
$workingDir = "C:\Users\28352\Desktop\AI前沿观察者\AIobserve"

$action = New-ScheduledTaskAction -Execute "python" -Argument "`"$taskPath`"" -WorkingDirectory $workingDir

$trigger = New-ScheduledTaskTrigger -Daily -At 20:00

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -WakeToRun -ExecutionTimeLimit (New-TimeSpan -Hours 1)

$task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Settings $settings

Register-ScheduledTask -TaskName $taskName -InputObject $task -Force

Write-Host "任务 '$taskName' 已成功注册，每天晚上8点自动执行"
Write-Host "任务路径: $taskPath"
Write-Host "工作目录: $workingDir"