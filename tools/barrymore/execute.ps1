param(
    [string]$Task = "manual"
)

$time = Get-Date -Format "yyyy-MM-dd_HHmmss"

$report = "tools\barrymore\reports\$time-report.md"

""
"# Barrymore Execution Report" | Out-File $report
"" | Out-File $report -Append
"Task: $Task" | Out-File $report -Append
"Date: $(Get-Date)" | Out-File $report -Append

""
"Environment:" | Out-File $report -Append

"PowerShell: $($PSVersionTable.PSVersion)" | Out-File $report -Append

""
"Git status:" | Out-File $report -Append

Write-Host ""
Write-Host "Staging changes..."
git add .

Write-Host ""
Write-Host "Creating commit..."

$commitMessage = "Barrymore: $Task $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
git commit -m $commitMessage

git status | Out-File $report -Append

Write-Host "Barrymore report created:"
Write-Host $report