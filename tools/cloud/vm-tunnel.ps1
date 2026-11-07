# vm-tunnel.ps1 - persistent SSH tunnel to the cloud workshop VM (reallab).
# Reads VM coordinates from Workspace/private/vars/cloud-vm.json (never hardcoded).
# Ports forwarded (all to VM loopback): 18765->8766 dashboard, 8080 wp, 8081 keycloak,
# 5432 pg, 6379 redis, 8788 rl-console.
#
# Usage:
#   powershell -File vm-tunnel.ps1              # run (reconnect loop, for scheduled task)
#   powershell -File vm-tunnel.ps1 -Once        # single ssh session (manual/testing)
#   powershell -File vm-tunnel.ps1 -Install     # register scheduled task + start
#   powershell -File vm-tunnel.ps1 -Uninstall   # remove scheduled task
param(
  [switch]$Install,
  [switch]$Uninstall,
  [switch]$Once
)
$ErrorActionPreference = "Stop"
$taskName = "VM Tunnel reallab"

if ($Uninstall) {
  $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
  if ($task) {
    Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Output "Removed scheduled task: $taskName"
  } else { Write-Output "Scheduled task is not installed: $taskName" }
  exit 0
}

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$varsFile = Join-Path $root "Workspace\private\vars\cloud-vm.json"
if (-not (Test-Path $varsFile)) {
  Write-Error "vars file not found: $varsFile (create it per Docs/TEMPLATING.md)"
  exit 1
}
$vars = Get-Content $varsFile -Raw | ConvertFrom-Json
$ip = $vars.vm_public_ip
$user = $vars.vm_user

$fwd = @(
  "-L", "18765:127.0.0.1:8766",
  "-L", "8080:127.0.0.1:8080",
  "-L", "8081:127.0.0.1:8081",
  "-L", "5432:127.0.0.1:5432",
  "-L", "6379:127.0.0.1:6379",
  "-L", "8788:127.0.0.1:8788"
)
$sshArgs = @("-N", "-o", "BatchMode=yes", "-o", "ExitOnForwardFailure=yes",
             "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=3",
             "-o", "StrictHostKeyChecking=accept-new") + $fwd + @("$user@$ip")

if ($Install) {
  $userId = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
  $action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$PSCommandPath`"" `
    -WorkingDirectory $root
  $trigger = New-ScheduledTaskTrigger -AtLogOn -User $userId
  $principal = New-ScheduledTaskPrincipal `
    -UserId $userId `
    -LogonType Interactive `
    -RunLevel Limited
  $settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RestartCount 5 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit ([TimeSpan]::Zero)
  Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
    -Principal $principal -Settings $settings -Description "Persistent SSH tunnel to the cloud VM (reallab). Auto-reconnects inside the script loop." `
    -Force | Out-Null
  Start-ScheduledTask -TaskName $taskName
  Write-Output "Installed and started: $taskName"
  exit 0
}

# Run mode: reconnect loop (autossh pattern natively)
while ($true) {
  Write-Output "$(Get-Date -Format s) tunnel up: $user@$ip"
  & ssh @sshArgs
  if ($Once) { break }
  Write-Output "$(Get-Date -Format s) tunnel dropped, reconnect in 5s"
  Start-Sleep -Seconds 5
}
