# Barrymore Morning Brief — генератор утреннего доклада (read-only, ADR-003).
# Читает источники истины (Memory/Context/CURRENT.md, Memory/Engineering/STATE.md,
# CHANGELOG.md, git) и пишет снимок в eVo/dashboard/brief.js для дашборда.
# INITIATIVE-0001 / DECISION-0003 / рекомендация R4 (Report-2026-10-25-audit.md).
# Секреты не читает и не выводит.
param(
    [string]$Root = (Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSCommandPath)))
)

$ErrorActionPreference = "Stop"

function Read-Utf8Text([string]$Path) {
    if (Test-Path $Path) { return [IO.File]::ReadAllText($Path) } else { return $null }
}

# --- Источник 1: CURRENT.md (дата и Next Action) ---
$current = Read-Utf8Text (Join-Path $Root "Memory\Context\CURRENT.md")
$currentDate = $null
$nextAction = $null
if ($current) {
    if ($current -match '(?m)^\s*Date:\s*(.+?)\s*$') { $currentDate = $Matches[1] }
    if ($current -match '(?s)##\s*Next Action\s*(.*?)(\r?\n##\s|\z)') { $nextAction = $Matches[1].Trim() }
}

# --- Источник 2: Engineering/STATE.md (следующий шаг работ) ---
$state = Read-Utf8Text (Join-Path $Root "Memory\Engineering\STATE.md")
$stateNext = $null
if ($state -match '(?s)##\s*Следующий шаг\s*(.*?)(\r?\n##\s|\z)') { $stateNext = $Matches[1].Trim() }

# --- Источник 3: CHANGELOG.md (последние датированные записи) ---
$changes = @()
$changelogPath = Join-Path $Root "CHANGELOG.md"
if (Test-Path $changelogPath) {
    $changes = @([IO.File]::ReadAllLines($changelogPath) | Where-Object { $_ -match '^\d{4}-\d{2}-\d{2}' } | Select-Object -Last 5)
}

# --- Источник 4: git ---
$branch     = git -C $Root branch --show-current
$lastCommit = git -C $Root log -1 --pretty=format:"%h %s"
$dirtyFiles = @(git -C $Root status --porcelain).Count

$brief = [ordered]@{
    generatedAt = (Get-Date -Format "yyyy-MM-dd HH:mm")
    sources     = @("Memory/Context/CURRENT.md", "Memory/Engineering/STATE.md", "CHANGELOG.md", "git")
    current     = @{ date = $currentDate; nextAction = $nextAction }
    state       = @{ nextStep = $stateNext }
    changes     = $changes
    git         = @{ branch = $branch; lastCommit = $lastCommit; dirtyFiles = $dirtyFiles }
}

$json = $brief | ConvertTo-Json -Depth 4
if (-not $json) { $json = "{}" }

$outPath = Join-Path $Root "eVo\dashboard\brief.js"
[IO.File]::WriteAllText($outPath, "window.EVO_BRIEF = $json;", (New-Object System.Text.UTF8Encoding($false)))
Write-Host "Morning Brief written: $outPath"
Write-Host "Generated at: $($brief.generatedAt); branch: $branch; CURRENT date: $currentDate; changes: $($changes.Count)"
