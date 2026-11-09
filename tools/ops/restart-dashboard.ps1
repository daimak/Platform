# Перезапуск дашборда Estate (127.0.0.1:8765) — единственная команда, которую
# надо помнить:  powershell -NoProfile -ExecutionPolicy Bypass -File tools\ops\restart-dashboard.ps1
# Убивает старый процесс на 8765, поднимает сервер заново (скрытое окно),
# ждёт и проверяет /api/peer-notes. Создан 07.11 (E-054) по просьбе Sovereign —
# «не помню команду рестарта».

$root = "C:\Work\Platform"
# Прямой путь к реальному python: лаунчер py/python3.exe держит ребёнка в job-объекте
# с kill-on-close — убийство лаунчера валит и сервер (инцидент 09.11).
$py = "C:\Users\temp\AppData\Local\Programs\Python\Python313\python.exe"
if (-not (Test-Path $py)) { $py = "C:\Users\temp\AppData\Local\Python\pythoncore-3.15-64\python.exe" }
if (-not (Test-Path $py)) { $py = "py" }

# 1. Убить слушателей 8765 (по PID из соединения, не по имени — точнее).
$killed = 0
Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction Stop
        $killed++
    } catch { }
}
if ($killed -gt 0) { Write-Host "Старый сервер остановлен (процессов: $killed)." }
else { Write-Host "Слушателей 8765 не найдено — просто запускаю." }

Start-Sleep -Seconds 1

# 2. Поднять заново в отдельном скрытом окне (живёт без нашей сессии).
Start-Process -FilePath $py -ArgumentList "tools\barrymore\dashboard-server.py" -WorkingDirectory $root -WindowStyle Hidden

# 3. Дождаться и проверить живой endpoint переписки агентов.
$ok = $false
foreach ($i in 1..10) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:8765/api/peer-notes" -UseBasicParsing -TimeoutSec 3
        if ($r.StatusCode -eq 200) { $ok = $true; break }
    } catch { }
}

if ($ok) {
    Write-Host "OK: дашборд перезапущен, http://127.0.0.1:8765 отвечает, /api/peer-notes жив."
} else {
    Write-Host "НЕ УДАЛОСЬ: 8765 не отвечает за 10 секунд. Диагностика: netstat -ano | findstr :8765"
}
