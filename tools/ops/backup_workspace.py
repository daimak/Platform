#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Резервная копия незакоммиченного состояния репозитория Platform Evo.

Копирует изменённые (M) и неотслеживаемые (??) файлы из git status в
%LOCALAPPDATA%/Platform/Backups/<метка времени>/ с сохранением относительных
путей. Ничего не изменяет и не удаляет в репозитории, коммитов не создаёт.

Зачем: в рабочем дереве лежат незакоммиченные результаты (правленный вручную
brief.js, автосервисный парсер, TOKEN_USAGE_LOG.md) — при сбое или перезаписи
генератором восстановить их будет неоткуда. Скрипт — «спасательный круг» из
crash-recovery протокола (verify-then-continue): сначала копия, потом действия.

- graphify-out/ пропускается по умолчанию (генерируемый кэш Graphify);
- для удалённых файлов (D) копировать нечего — их содержимое остаётся в
  истории git (в т.ч. на origin, если коммит запушен).

Запуск: python tools/ops/backup_workspace.py [--dest ПУТЬ] [--all]
  --all   включить graphify-out/ (медленно, обычно не нужно)
"""

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASHKENT = timezone(timedelta(hours=5), "Tashkent")
SKIP_PREFIXES = ("graphify-out/",)


def git(*args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} завершился с ошибкой: {proc.stderr.strip()}")
    return proc.stdout


def collect_entries(include_generated: bool) -> tuple[list[tuple[str, str]], list[str]]:
    """Разбирает git status --porcelain -z в список (статус, путь).

    Возвращает (файлы_для_копирования, удалённые_пути). Переименованные
    (R) файлы копируются по новому пути; старый остаётся в индексе git.
    """
    raw = git("status", "--porcelain=v1", "-z")
    entries = raw.split("\0")
    to_copy: list[tuple[str, str]] = []
    deleted: list[str] = []
    i = 0
    while i < len(entries):
        entry = entries[i]
        i += 1
        if not entry or len(entry) < 4:
            continue
        status, path = entry[:2], entry[3:]
        if status[0] in ("R", "C"):
            i += 1  # старый путь идёт следующим NUL-полем, пропускаем
        if status == "??":
            to_copy.append((status, path))
        elif status.strip() == "D":
            deleted.append(path)
        elif status.strip() in ("M", "A") or (status[0] in ("R", "C")):
            to_copy.append((status.strip(), path))
    if not include_generated:
        to_copy = [(s, p) for s, p in to_copy if not any(p.startswith(prefix) for prefix in SKIP_PREFIXES)]
        deleted = [p for p in deleted if not any(p.startswith(prefix) for prefix in SKIP_PREFIXES)]
    return to_copy, deleted


def copy_entry(dest: Path, status: str, rel_path: str) -> tuple[int, int]:
    """Копирует один файл или каталог (для ?? с завершающим '/'). Возвращает (файлов, байт)."""
    source = ROOT / rel_path
    target = dest / rel_path
    if rel_path.endswith("/"):
        copied_files = 0
        copied_bytes = 0
        for dirpath, _dirnames, filenames in os.walk(source):
            for name in filenames:
                src_file = Path(dirpath) / name
                rel_file = src_file.relative_to(ROOT)
                dst_file = dest / rel_file
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dst_file)
                copied_files += 1
                copied_bytes += src_file.stat().st_size
        return copied_files, copied_bytes
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return 1, source.stat().st_size


def main() -> int:
    parser = argparse.ArgumentParser(description="Backup незакоммиченных файлов Platform Evo")
    parser.add_argument("--dest", help="каталог назначения (по умолчанию %LOCALAPPDATA%/Platform/Backups/<ts>)")
    parser.add_argument("--all", action="store_true", help="включить graphify-out/")
    args = parser.parse_args()

    include_generated = args.all
    stamp = datetime.now(TASHKENT).strftime("%Y%m%d-%H%M%S")
    default_root = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Platform" / "Backups"
    dest = Path(args.dest) if args.dest else default_root / stamp

    try:
        to_copy, deleted = collect_entries(include_generated)
    except RuntimeError as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        return 1

    if not to_copy and not deleted:
        print("Рабочее дерево чистое — копировать нечего.")
        return 0

    dest.mkdir(parents=True, exist_ok=True)
    total_files = 0
    total_bytes = 0
    for status, rel_path in sorted(to_copy, key=lambda item: item[1]):
        try:
            files_count, bytes_count = copy_entry(dest, status, rel_path)
        except OSError as error:
            print(f"[FAIL] {rel_path}: {error}", file=sys.stderr)
            continue
        total_files += files_count
        total_bytes += bytes_count
        kind = "каталог" if rel_path.endswith("/") else "файл"
        print(f"[{status:>2}] {kind}: {rel_path}")

    for rel_path in deleted:
        print(f"[ D] удалён, копии нет — содержимое в истории git: {rel_path}")

    print("-" * 60)
    print(f"Скопировано {total_files} файлов ({total_bytes} байт) в:")
    print(f"  {dest}")
    print("Восстановление: вручную перепишите файлы из каталога копии в репозиторий.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
