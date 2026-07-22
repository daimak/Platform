Write-Host "================================="
Write-Host " Barrymore Estate Status"
Write-Host "================================="
Write-Host ""

Write-Host "Estate status:"
Write-Host "Estate is alive"

Write-Host ""
Write-Host "Last change:"
git log -1 --pretty=format:"%s"

Write-Host ""
Write-Host ""
Write-Host "Git status:"
git status --short

Write-Host ""
Write-Host "================================="