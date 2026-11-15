# Fix VitrinaPing action: hidden wscript launcher (no cmd window flash)
$action = New-ScheduledTaskAction -Execute 'wscript.exe' -Argument '//B //Nologo "C:\Work\Platform\Workspace\sales-lane\ping-vitrina-hidden.vbs"'
Set-ScheduledTask -TaskName VitrinaPing -Action $action | Out-Null
(Get-ScheduledTask -TaskName VitrinaPing).Actions | ForEach-Object { '{0} {1}' -f $_.Execute, $_.Arguments }
