param(
  [switch]$Uninstall
)

$ErrorActionPreference = "Stop"
$taskName = "Barrymore Dashboard Server"

if ($Uninstall) {
  $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
  if ($task) {
    Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Output "Removed scheduled task: $taskName"
  } else {
    Write-Output "Scheduled task is not installed: $taskName"
  }
  exit 0
}

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$serverScript = Join-Path $PSScriptRoot "dashboard-server.py"
$python = (Get-Command python.exe -ErrorAction Stop).Source
$pythonw = Join-Path (Split-Path $python) "pythonw.exe"
if (-not (Test-Path $pythonw)) {
  $pythonw = $python
}

$userId = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$action = New-ScheduledTaskAction `
  -Execute $pythonw `
  -Argument "`"$serverScript`"" `
  -WorkingDirectory $projectRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $userId
$principal = New-ScheduledTaskPrincipal `
  -UserId $userId `
  -LogonType Interactive `
  -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet `
  -StartWhenAvailable `
  -RestartCount 3 `
  -RestartInterval (New-TimeSpan -Minutes 1) `
  -MultipleInstances IgnoreNew `
  -ExecutionTimeLimit ([TimeSpan]::Zero)

Register-ScheduledTask `
  -TaskName $taskName `
  -Action $action `
  -Trigger $trigger `
  -Principal $principal `
  -Settings $settings `
  -Description "Starts Barrymore's loopback-only dashboard server when this user signs in." `
  -Force | Out-Null

Start-ScheduledTask -TaskName $taskName
Write-Output "Installed and started: $taskName"
Write-Output "Dashboard URL: http://127.0.0.1:8765"
