#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Healthcheck Platform Evo по находкам аудита 2026-10-29 (изменения v1.8.4).

Только чтение: ничего не пишет ни в репозиторий, ни в %LOCALAPPDATA%.

Проверки (номера — находки аудита, см. tools/ops/README.md):
- F1: целостность eVo/dashboard/brief.js — формат "window.EVO_BRIEF = {...};",
  валидный JSON, наличие ключей generatedAt/_sourceFingerprint/agent;
- F2: каждая запись Memory/Engineering/Tasks/Active/*.json валидна — одна
  невалидная запись валит весь /api/tasks и генерацию Morning Brief;
- F4: читаемость журнала AI-Usage (%LOCALAPPDATA%/Platform/AI-Usage/usage.json);
- инфраструктура: дашборд-сервер на 127.0.0.1:8765 (TCP, при живом сервере —
  GET /api/tasks), валидность allowlist security-targets.json, очередь Hunter,
  наличие Workspace/.env и ключа FREE_LLM_API_KEY (только факт наличия,
  значение ключа не читается и не выводится);
- git: ветка, опережение origin, число незакоммиченных/неотслеживаемых файлов.

Коды выхода: 0 — всё чисто; 1 — есть FAIL; 2 — только WARN.
Запуск: python tools/ops/healthcheck.py
"""

import json
import socket
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BARRYMORE = ROOT / "tools" / "barrymore"
sys.path.insert(0, str(BARRYMORE))

import ai_usage  # noqa: E402
import hunter_store  # noqa: E402
import security_contour  # noqa: E402
import task_store  # noqa: E402

BRIEF_PATH = ROOT / "eVo" / "dashboard" / "brief.js"
BRIEF_PREFIX = "window.EVO_BRIEF = "
PORT = 8765

results = []


def ok(message: str) -> None:
    results.append(("OK  ", message))


def warn(message: str) -> None:
    results.append(("WARN", message))


def fail(message: str) -> None:
    results.append(("FAIL", message))


def git(*args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15,
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def check_brief() -> None:
    # F1: усечённый/битый brief.js ломает Morning Brief в дашборде до успешного refresh.
    if not BRIEF_PATH.exists():
        fail(f"brief.js отсутствует: {BRIEF_PATH}")
        return
    try:
        content = BRIEF_PATH.read_text(encoding="utf-8")
    except OSError as error:
        fail(f"brief.js не читается: {error}")
        return
    if not content.startswith(BRIEF_PREFIX) or not content.rstrip().endswith(";"):
        fail("brief.js: неожиданный формат (нет префикса 'window.EVO_BRIEF = ' или ';' в конце)")
        return
    try:
        brief = json.loads(content[len(BRIEF_PREFIX):].rstrip()[:-1])
    except json.JSONDecodeError as error:
        fail(f"brief.js: JSON невалиден — {error}")
        return
    missing = [k for k in ("generatedAt", "_sourceFingerprint", "agent") if k not in brief]
    if missing:
        warn(f"brief.js: JSON валиден, но нет ключей {', '.join(missing)} (файл писался не генератором — "
             "при следующем refresh будет перезаписан, один лишний LLM-запрос)")
    ok(f"brief.js: формат и JSON валидны, generatedAt={brief.get('generatedAt')!r}")


def check_tasks() -> None:
    # F2: одна невалидная задача валит весь список — ищем её заранее.
    if not task_store.ACTIVE_DIR.exists():
        ok("задачи: каталог Active/ отсутствует (пусто — это нормально)")
        return
    broken = []
    total = 0
    for path in sorted(task_store.ACTIVE_DIR.glob("*.json")):
        total += 1
        try:
            task_store._read_task(path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            broken.append(f"{path.name}: {error}")
    if broken:
        for item in broken:
            fail(f"задачи (F2): невалидная запись — {item}")
        warn("невалидные записи ломают /api/tasks и Morning Brief целиком; "
             "исправьте или уберите файл(ы) из Active/")
    else:
        ok(f"задачи: {total} записей в Active/ валидны")


def check_hunter() -> None:
    try:
        assignments = hunter_store.list_assignments()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        fail(f"очередь Hunter: {error}")
        return
    ok(f"очередь Hunter: {len(assignments)} поручений, файл валиден")


def check_ai_usage() -> None:
    # F4: читаемость журнала под параллельной записью (transient 500 на /api/ai-usage).
    try:
        data = ai_usage._read_ledger()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        fail(f"AI-Usage журнал: {error}")
        return
    ok(f"AI-Usage: {len(data['requests'])} запросов, {len(data['snapshots'])} снимков, "
       f"include_in_morning_brief={data['settings']['include_in_morning_brief']}")


def check_server() -> None:
    try:
        with socket.create_connection(("127.0.0.1", PORT), timeout=1):
            pass
    except OSError:
        ok(f"дашборд-сервер: не запущен (порт {PORT} свободен — это не ошибка)")
        return
    ok(f"дашборд-сервер: слушает 127.0.0.1:{PORT}")
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/tasks", timeout=5) as response:
            body = json.loads(response.read().decode("utf-8"))
            tasks = body.get("tasks", {})
            ok(f"GET /api/tasks: 200, urgent={len(tasks.get('urgent', []))}, "
               f"regular={len(tasks.get('regular', []))}, done={len(tasks.get('done', []))}")
    except Exception as error:  # noqa: BLE001 — диагностика, не боевой путь
        warn(f"GET /api/tasks не удался: {type(error).__name__}: {error}")


def check_security_targets() -> None:
    try:
        config = security_contour.load_config()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        fail(f"allowlist security-targets.json: {error}")
        return
    hosts = ", ".join(t["host"] for t in config["targets"]) or "пусто"
    ok(f"allowlist: {len(config['targets'])} целей ({hosts}), llm_analysis={config['llm_analysis']}")


def check_env() -> None:
    env_path = ROOT / "Workspace" / ".env"
    if not env_path.exists():
        fail(f"{env_path} отсутствует — LLM-шлюз не сможет авторизоваться")
        return
    env = security_contour.load_env(env_path)
    if env.get("FREE_LLM_API_KEY"):
        ok("Workspace/.env: FREE_LLM_API_KEY установлен (значение не выводится)")
    else:
        fail("Workspace/.env: FREE_LLM_API_KEY не найден")
    if not env.get("FREE_LLM_BASE_URL"):
        warn("Workspace/.env: FREE_LLM_BASE_URL не задан — будет использован http://localhost:31415/v1")


def check_git() -> None:
    branch = git("branch", "--show-current")
    if not branch:
        fail("git: не удалось определить ветку (detached HEAD или git недоступен?)")
        return
    ahead = git("rev-list", "--count", f"origin/{branch}..HEAD")
    status = git("status", "--porcelain=v1")
    modified = len([l for l in status.splitlines() if l and not l.startswith("??")])
    untracked = len([l for l in status.splitlines() if l.startswith("??")])
    note = ""
    if ahead and ahead != "0":
        note = f" — ВНИМАНИЕ: {ahead} локальных коммитов не запушено"
        warn(f"git: ветка {branch}, {ahead} коммитов впереди origin{note}")
    else:
        ok(f"git: ветка {branch}, синхронизирована с origin")
    if modified or untracked:
        warn(f"git: {modified} изменённых и {untracked} неотслеживаемых файлов — "
             "см. tools/ops/backup_workspace.py")
    else:
        ok("git: рабочее дерево чистое")


def main() -> int:
    check_brief()
    check_tasks()
    check_hunter()
    check_ai_usage()
    check_server()
    check_security_targets()
    check_env()
    check_git()

    width = max(len(m) for _, m in results)
    for level, message in results:
        print(f"[{level}] {message}")
    fails = sum(1 for l, _ in results if l == "FAIL")
    warns = sum(1 for l, _ in results if l == "WARN")
    print("-" * max(width + 8, 40))
    print(f"Итого: FAIL={fails}, WARN={warns}. "
          "FAIL — требуется действие; WARN — известно, см. tools/ops/README.md.")
    return 1 if fails else (2 if warns else 0)


if __name__ == "__main__":
    sys.exit(main())
