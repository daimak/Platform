Write-Host ""
Write-Host "================================"
Write-Host "        eVo RELEASE GATE"
Write-Host "================================"
Write-Host ""

Write-Host "Project: eVo"

$branch = git branch --show-current

Write-Host "Branch: $branch"

$status = git status --porcelain

if ($status) {
    Write-Host "Git: CHANGES DETECTED"
}
else {
    Write-Host "Git: CLEAN"
}

$commit = git log -1 --pretty=format:"%h %s"

Write-Host ""
Write-Host "Latest commit:"
Write-Host $commit

Write-Host ""

$remote = git status -sb

Write-Host "Remote:"
Write-Host $remote

Write-Host ""
Write-Host "================================"

if (!$status) {
    Write-Host "STATUS: READY FOR NEXT EVOLUTION"
}
else {
    Write-Host "STATUS: WORK IN PROGRESS"
}

Write-Host "================================"