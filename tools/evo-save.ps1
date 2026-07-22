Write-Host "=== eVo Save ==="

Write-Host ""
Write-Host "Текущее состояние:"
git status

Write-Host ""
$confirm = Read-Host "Продолжить сохранение? (y/n)"

if ($confirm -ne "y") {
    Write-Host "Сохранение отменено."
    exit
}

git add .

$comment = Read-Host "Описание изменения"

git commit -m $comment

git push

Write-Host ""
Write-Host "Финальное состояние:"
git status
