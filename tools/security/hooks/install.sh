#!/bin/sh
# Установка pre-commit гейта секретов (V-09): копирует pre-commit в .git/hooks/.
# Идемпотентно: повторный запуск обновляет наш хук; чужой (не наш) — не затирает.
set -eu

here=$(cd "$(dirname "$0")" && pwd)
hook_src="$here/pre-commit"

git_dir=$(git rev-parse --git-common-dir 2>/dev/null) || git_dir=$(git rev-parse --git-dir)
hooks_dir="${git_dir%/}/hooks"
dst="$hooks_dir/pre-commit"

[ -f "$hook_src" ] || { echo "ОШИБКА: не найден исходник хука: $hook_src"; exit 1; }
mkdir -p "$hooks_dir"

if [ -f "$dst" ] && ! grep -q "secret_scan" "$dst"; then
    echo "ОШИБКА: $dst уже занят другим хуком — не перезаписываю."
    echo "Разберись вручную (сохрани чужой хук, объедини логику) и запусти снова."
    exit 1
fi

cp "$hook_src" "$dst"
chmod +x "$dst"

echo "OK: pre-commit установлен: $dst"
[ -x "$dst" ] && echo "OK: права на исполнение есть."
echo "Проверка: добавь файл с тестовым секретом и попробуй git commit (должен отклонить RED)."
echo "Обход гейта: git commit --no-verify"
