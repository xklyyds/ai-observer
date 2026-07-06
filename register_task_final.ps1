$taskName = "AI日报任务"
$vbsPath = "C:\Users\28352\Desktop\AI前沿观察者\AIobserve\run_task.vbs"
$workingDir = "C:\Users\28352\Desktop\AI前沿观察者\AIobserve"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AI日报任务注册工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "任务名称: $taskName" -ForegroundColor Yellow
Write-Host "启动脚本: $vbsPath" -ForegroundColor Yellow
Write-Host "工作目录: $workingDir" -ForegroundColor Yellow
Write-Host ""

try {
    $action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$vbsPath`"" -WorkingDirectory $workingDir

    $trigger = New-ScheduledTaskTrigger -Daily -At 20:00

    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -WakeToRun `
        -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
        -MultipleInstances IgnoreNew `
        -Hidden $false

    $principal = New-ScheduledTaskPrincipal `
        -UserId "$env:USERDOMAIN\$env:USERNAME" `
        -LogonType Interactive `
        -RunLevel Highest

    $task = New-ScheduledTask `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings `
        -Description "每天晚上8点自动运行AI前沿观察者智能体，生成日报并发送邮件"

    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

    Register-ScheduledTask -TaskName $taskName -InputObject $task -Force | Out-Null

    Write-Host ""
    Write-Host "任务注册成功！" -ForegroundColor Green
    Write-Host "下次运行时间: 每天晚上 20:00" -ForegroundColor Green
    Write-Host ""
    Write-Host "验证任务..." -ForegroundColor Yellow
    $taskInfo = Get-ScheduledTask -TaskName $taskName
    $taskInfo | Get-ScheduledTaskInfo | Select-Object @{Name="下次运行时间";Expression={$_.NextRunTime}}, @{Name="上次运行结果";Expression={$_.LastTaskResult}} | Format-List
    Write-Host ""
    Write-Host "提示: 如果任务未正常执行，请查看以下日志文件:" -ForegroundColor Cyan
    Write-Host "  - $workingDir\task_runner.log (批处理日志)" -ForegroundColor Cyan
    Write-Host "  - $workingDir\vbs_runner.log (VBS日志)" -ForegroundColor Cyan
    Write-Host "  - $workingDir\ai_daily_report.log (Python日志)" -ForegroundColor Cyan

} catch {
    Write-Host ""
    Write-Host "任务注册失败: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "请确保以管理员身份运行此脚本！" -ForegroundColor Yellow
    Write-Host "右键点击PowerShell，选择'以管理员身份运行'" -ForegroundColor Yellow
    exit 1
}