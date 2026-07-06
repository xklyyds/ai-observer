Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
batchFile = scriptDir & "\run_task.bat"
logFile = scriptDir & "\vbs_runner.log"

logText = "[" & Now & "] 启动任务..." & vbCrLf
logText = logText & "[" & Now & "] 批处理文件: " & batchFile & vbCrLf

WshShell.CurrentDirectory = scriptDir

exitCode = WshShell.Run("""" & batchFile & """", 0, True)

logText = logText & "[" & Now & "] 执行完毕，退出码: " & exitCode & vbCrLf & vbCrLf

Set logStream = fso.OpenTextFile(logFile, 8, True)
logStream.Write logText
logStream.Close

WScript.Quit exitCode