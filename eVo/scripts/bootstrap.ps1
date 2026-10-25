$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "====================================="
Write-Host "      eVo Bootstrap v0.1"
Write-Host "====================================="
Write-Host ""

$folders = @(
    "agents",
    "agents\barrymore",
    "agents\barrymore\config",
    "agents\barrymore\memory",
    "agents\barrymore\prompts",

    "runtime",
    "runtime\tools",
    "runtime\providers",
    "runtime\permissions",
    "runtime\schemas",

    "memory",
    "memory\decisions",
    "memory\daily",
    "memory\sessions",
    "memory\knowledge",

    "docs",
    "docs\architecture",
    "docs\agents",
    "docs\runtime",
    "docs\security",
    "docs\vision"
)

foreach ($folder in $folders)
{
    if (!(Test-Path $folder))
    {
        New-Item -ItemType Directory $folder | Out-Null
        Write-Host "[CREATE] $folder"
    }
    else
    {
        Write-Host "[ OK ]    $folder"
    }
}

$files = @{
    "agents\barrymore\README.md" = "# Barrymore`n`nSystem agent of eVo."
    "docs\vision\README.md" = "# Vision"
    "docs\architecture\README.md" = "# Architecture"
    "docs\security\README.md" = "# Security"
    "docs\runtime\README.md" = "# Runtime"
}

# ADR с 2026-10-25 bootstrap'ом не создаются: единый каталог решений — Core\Architecture\ADR\ (INDEX.md).

foreach($file in $files.Keys)
{
    if (!(Test-Path $file))
    {
        $files[$file] | Set-Content $file -Encoding UTF8
        Write-Host "[CREATE] $file"
    }
    else
    {
        Write-Host "[ OK ]    $file"
    }
}

Write-Host ""
Write-Host "Git status"
git status

Write-Host ""
Write-Host "Done."