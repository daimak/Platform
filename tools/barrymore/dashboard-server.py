#!/usr/bin/env python3
"""Serve the local Estate dashboard and expose Barrymore brief refresh."""

import json
import logging
import os
import re
import socket
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from ai_usage import add_snapshot, dashboard_data, set_include_in_morning_brief
from hunter_store import create_assignment, list_assignments
from security_contour import add_target, dashboard_status, run_check
from task_store import TASK_ID_PATTERN, add_comment, can_transition, dashboard_tasks, mark_done, set_stage

ROOT = Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "eVo" / "dashboard"
AGENT = ROOT / "tools" / "barrymore" / "morning-brief-agent.py"
PORT = 8765
REFRESH_LOCK = threading.Lock()
TASK_LOCK = threading.Lock()
HUNTER_LOCK = threading.Lock()
USAGE_LOCK = threading.Lock()
SECURITY_LOCK = threading.Lock()
REPORTS_LOCK = threading.Lock()
HOLMES_RUN_LOCK = threading.Lock()
HOLMES_RUN: dict = {
    "running": False,
    "started_at": None,
    "finished_at": None,
    "returncode": None,
    "error": None,
}
HOLMES_AGENT = ROOT / "tools" / "agents" / "run_agent.py"
LOG_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Platform" / "Barrymore"
TASHKENT = timezone(timedelta(hours=5), "Tashkent")

# Инструменты безопасности (прототипы 01.11, вкладка «Инструменты» AI Sandbox).
# Поводок: запуск только кнопкой/рукой; отчёты — в LOCALAPPDATA вне git (правило видимости).
SANDBOX_TOOLS = {
    "radar": {"script": ROOT / "tools" / "security" / "vuln_radar.py", "prefix": "vuln-radar", "timeout": 180, "title": "Радар уязвимостей"},
    "portaudit": {"script": ROOT / "tools" / "security" / "port_audit.py", "prefix": "port-audit", "timeout": 60, "title": "Аудит портов"},
    "secrets": {"script": ROOT / "tools" / "security" / "secret_scan.py", "prefix": "secret-scan", "timeout": 120, "title": "Поиск секретов"},
    "nmap": {"script": ROOT / "tools" / "security" / "nmap_probe.py", "prefix": "nmap-probe", "timeout": 900, "title": "nmap-скан"},
}

# Гвард A-01 (аудит 06.11, CWE-88): инструменту разрешены только санкционированные флаги.
# Значение = сколько аргументов-значений ждёт флаг после себя.
SANDBOX_ARG_ALLOW = {
    "radar": {"--days": 1, "--keywords": 1, "--limit": 1},
    "portaudit": {},
    "secrets": {},
    "nmap": {"--target": 1, "--ports": 1, "--cve": 0, "--allow-external": 0},
}
SANDBOX_PORTS_RE = re.compile(r"[0-9]{1,5}(-[0-9]{1,5})?(,[0-9]{1,5}(-[0-9]{1,5})?)*")
SANDBOX_NUM_RE = re.compile(r"[0-9]{1,4}")
SANDBOX_RUN_LOCK = threading.Lock()
SANDBOX_RUN: dict = {
    "running": False,
    "tool": None,
    "started_at": None,
    "finished_at": None,
    "returncode": None,
    "summary": None,
    "error": None,
}
SANDBOX_REPORT_DIR = (
    Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Platform" / "SecurityReports"
)

# Реестр джобов (Л-3, Docs/DATA-FOUNDATION-PLAN-2026-11-04): API без UI-кнопок.
JOBS_REGISTRY_PATH = ROOT / "tools" / "ops" / "jobs.json"
JOBS_STATE_PATH = ROOT / "Workspace" / "logs" / "jobs_state.json"
JOBS_LOCK = threading.Lock()


class DashboardHTTPServer(ThreadingHTTPServer):
    """Один порт — один владелец: 8765 каноничен (Docs/Barrymore.md).

    stdlib ставит SO_REUSEADDR, и на Windows второй экземпляр молча цепляется
    на тот же порт и отдаёт устаревший код; SO_EXCLUSIVEADDRUSE дополнительно
    запрещает захват порта чужим процессом.
    """

    allow_reuse_address = False

    def server_bind(self):
        if os.name == "nt":
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


class TashkentFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        timestamp = datetime.fromtimestamp(record.created, TASHKENT)
        return timestamp.strftime(datefmt or "%Y-%m-%d %H:%M:%S")


def run_brief(retry_llm_error: bool = False) -> dict:
    command = [sys.executable, str(AGENT)]
    if retry_llm_error:
        command.append("--retry-llm-error")
    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=100,
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
    )
    if result.stdout:
        logging.info("Brief generator: %s", result.stdout.strip())
        if sys.stdout is not None:
            print(result.stdout, end="")
    if result.stderr:
        logging.error("Brief generator stderr: %s", result.stderr.strip())
        if sys.stderr is not None:
            print(result.stderr, end="", file=sys.stderr)
    if result.returncode:
        raise RuntimeError(
            f"Генератор завершился с кодом {result.returncode}. "
            f"Подробности: {LOG_DIR / 'dashboard-server.log'}"
        )

    generated = (DASHBOARD / "brief.js").read_text(encoding="utf-8")
    prefix = "window.EVO_BRIEF = "
    if not generated.startswith(prefix) or not generated.rstrip().endswith(";"):
        raise RuntimeError("Генератор записал brief.js в неожиданном формате.")
    return json.loads(generated[len(prefix):].rstrip()[:-1])


# Находки Холмса со стабильными ID — заголовки задач лиджера.
FINDING_TITLES = {
    "host-noise": "Холмс: шум авто-коммитов агент-хоста в истории",
    "untracked-files": "Холмс: разобрать untracked-файлы (коммит или .gitignore)",
    "uncommitted-edits": "Холмс: незакоммиченные правки в рабочем дереве",
    "journal-stale": "Холмс: журнал LOG.md давно не обновлялся",
    "branch-drift": "Холмс: рабочая ветка разошлась с upstream",
    "main-behind": "Холмс: локальный main позади origin/main",
}


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=f".{path.stem}.", suffix=".tmp", delete=False,
        ) as temporary:
            tmp_path = Path(temporary.name)
            json.dump(payload, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
        os.replace(tmp_path, path)
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink()


def holmes_ensure_task(finding_id: str, severity: str, detail: str) -> str:
    """Create-if-missing задача holmes-<id>: инициатива Холмса, санкционированная
    Sovereign через дашборд. Существующие задачи не изменяет (ADR-003)."""
    base_id = f"holmes-{finding_id}"
    if not TASK_ID_PATTERN.fullmatch(base_id):
        return "invalid-id"
    active_dir = ROOT / "Memory" / "Engineering" / "Tasks" / "Active"
    archive_dir = ROOT / "Memory" / "Engineering" / "Tasks" / "Archive"
    if (active_dir / f"{base_id}.json").exists():
        return "exists"
    task_id = None
    for candidate in [base_id] + [f"{base_id}-{n}" for n in range(2, 10)]:
        if archive_dir.exists() and any(archive_dir.rglob(f"{candidate}.json")):
            continue
        task_id = candidate
        break
    if task_id is None:
        return "no-free-id"
    created = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    note = f"{detail[:180]} — санкция Sovereign через дашборд." if detail else "Санкция Sovereign через дашборд."
    task = {
        "id": task_id,
        "title": FINDING_TITLES.get(finding_id, f"Холмс: находка {finding_id}"),
        "source": "Holmes",
        "priority": "urgent" if severity == "P1" else "regular",
        "status": "active",
        "createdAt": created,
        "history": [{"status": "active", "at": created, "by": "Sovereign", "note": note}],
    }
    _atomic_write_json(active_dir / f"{task_id}.json", task)
    return f"created:{task_id}"


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} завершился с кодом {result.returncode}")
    return result.stdout.strip()


def holmes_context() -> dict:
    """Живой контекст кабинета Холмса: ветка, дерево, последний коммит и осмотр."""
    branch = _git("branch", "--show-current")
    status_out = _git("status", "--porcelain")
    changed = len([line for line in status_out.splitlines() if line.strip()])
    log_raw = _git("log", "-1", "--date=format-local:%Y-%m-%d %H:%M", "--format=%h|%ad|%s")
    hash_, commit_date, subject = (log_raw.split("|", 2) + ["", "", ""])[:3] if log_raw else ("", "", "")
    files = sorted((ROOT / "Memory" / "Engineering" / "Reports").glob("Report-*-holmes-audit.md"), reverse=True)
    last_report = None
    if files:
        stat = files[0].stat()
        last_report = {
            "file": files[0].name,
            "modified": datetime.fromtimestamp(stat.st_mtime, TASHKENT).strftime("%Y-%m-%d %H:%M"),
        }
    return {
        "branch": branch or "(detached HEAD)",
        "tree_changed": changed,
        "last_commit": {"hash": hash_, "date": commit_date, "subject": subject},
        "last_report": last_report,
    }


def _holmes_run_worker() -> None:
    """Единичный цикл аудита Холмса (run_agent.py --agent Holmes) в фоне."""
    command = [sys.executable, str(HOLMES_AGENT), "--agent", "Holmes"]
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=1800,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
        )
        with HOLMES_RUN_LOCK:
            HOLMES_RUN.update({
                "running": False,
                "finished_at": datetime.now(TASHKENT).isoformat(timespec="seconds"),
                "returncode": result.returncode,
                "error": None if result.returncode == 0
                else (result.stderr.strip() or result.stdout.strip() or f"код {result.returncode}")[-800:],
            })
        logging.info("Holmes run finished with code %s", result.returncode)
    except subprocess.TimeoutExpired:
        with HOLMES_RUN_LOCK:
            HOLMES_RUN.update({
                "running": False,
                "finished_at": datetime.now(TASHKENT).isoformat(timespec="seconds"),
                "returncode": -1,
                "error": "Осмотр не уложился в 30 минут.",
            })
        logging.error("Holmes run timed out after 1800s")
    except Exception as error:  # поток не должен умирать молча
        with HOLMES_RUN_LOCK:
            HOLMES_RUN.update({
                "running": False,
                "finished_at": datetime.now(TASHKENT).isoformat(timespec="seconds"),
                "returncode": -1,
                "error": str(error)[:800],
            })
        logging.exception("Holmes run failed")


def holmes_reports(file: str | None = None) -> dict:
    """Read-only отчёты аудита Холмса для острова holmes.html."""
    reports_dir = ROOT / "Memory" / "Engineering" / "Reports"
    if file is not None:
        if not re.fullmatch(r"Report-\d{4}-\d{2}-\d{2}-holmes-audit\.md", file):
            raise ValueError("Недопустимое имя отчёта.")
        path = reports_dir / file
        if not path.is_file():
            raise FileNotFoundError(f"Отчёт не найден: {file}")
        return {"file": file, "content": path.read_text(encoding="utf-8-sig", errors="replace")[:200_000]}
    files = sorted(reports_dir.glob("Report-*-holmes-audit.md"), reverse=True)
    reports = []
    for path in files:
        stat = path.stat()
        reports.append({
            "file": path.name,
            "modified": datetime.fromtimestamp(stat.st_mtime, TASHKENT).strftime("%Y-%m-%d %H:%M"),
            "size": stat.st_size,
        })
    latest = None
    if files:
        latest = {
            "file": files[0].name,
            "content": files[0].read_text(encoding="utf-8-sig", errors="replace")[:200_000],
        }
    return {"reports": reports, "latest": latest}


# --- Обобщённые прогоны штата (Ватсон, Risk scan) по образцу квартета Холмса ---

AGENT_RUNTIMES = {
    "watson": {"registry_name": "Watson", "report_tag": "watson-audit", "label": "Ватсон"},
    "riskscan": {"registry_name": "RiskScan", "report_tag": "riskscan-audit", "label": "Risk scan"},
}
AGENT_RUN_STATE = {
    runtime: {
        "lock": threading.Lock(),
        "state": {"running": False, "started_at": None, "finished_at": None, "returncode": None, "error": None},
    }
    for runtime in AGENT_RUNTIMES
}


def _agent_run_worker(runtime: str) -> None:
    """Единичный прогон агента штата (run_agent.py --agent <name>) в фоне."""
    spec = AGENT_RUNTIMES[runtime]
    entry = AGENT_RUN_STATE[runtime]
    lock, state = entry["lock"], entry["state"]
    command = [sys.executable, str(HOLMES_AGENT), "--agent", spec["registry_name"]]
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=1800,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
        )
        with lock:
            state.update({
                "running": False,
                "finished_at": datetime.now(TASHKENT).isoformat(timespec="seconds"),
                "returncode": result.returncode,
                "error": None if result.returncode == 0
                else (result.stderr.strip() or result.stdout.strip() or f"код {result.returncode}")[-800:],
            })
        logging.info("%s run finished with code %s", spec["label"], result.returncode)
    except subprocess.TimeoutExpired:
        with lock:
            state.update({
                "running": False,
                "finished_at": datetime.now(TASHKENT).isoformat(timespec="seconds"),
                "returncode": -1,
                "error": "Прогон не уложился в 30 минут.",
            })
        logging.error("%s run timed out after 1800s", spec["label"])
    except Exception as error:  # поток не должен умирать молча
        with lock:
            state.update({
                "running": False,
                "finished_at": datetime.now(TASHKENT).isoformat(timespec="seconds"),
                "returncode": -1,
                "error": str(error)[:800],
            })
        logging.exception("%s run failed", spec["label"])


def agent_reports(runtime: str, file: str | None = None) -> dict:
    """Read-only отчёты агента штата для дашборда (по report_tag из реестра)."""
    spec = AGENT_RUNTIMES[runtime]
    tag = spec["report_tag"]
    reports_dir = ROOT / "Memory" / "Engineering" / "Reports"
    if file is not None:
        if not re.fullmatch(rf"Report-\d{{4}}-\d{{2}}-\d{{2}}-{re.escape(tag)}\.md", file):
            raise ValueError("Недопустимое имя отчёта.")
        path = reports_dir / file
        if not path.is_file():
            raise FileNotFoundError(f"Отчёт не найден: {file}")
        return {"file": file, "content": path.read_text(encoding="utf-8-sig", errors="replace")[:200_000]}
    files = sorted(reports_dir.glob(f"Report-*-{tag}.md"), reverse=True)
    reports = []
    for path in files:
        stat = path.stat()
        reports.append({
            "file": path.name,
            "modified": datetime.fromtimestamp(stat.st_mtime, TASHKENT).strftime("%Y-%m-%d %H:%M"),
            "size": stat.st_size,
        })
    latest = None
    if files:
        latest = {
            "file": files[0].name,
            "content": files[0].read_text(encoding="utf-8-sig", errors="replace")[:200_000],
        }
    return {"reports": reports, "latest": latest}


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DASHBOARD), **kwargs)

    def guess_type(self, path: str) -> str:
        content_type = super().guess_type(path)
        if content_type.startswith("text/") and "charset=" not in content_type:
            return f"{content_type}; charset=utf-8"
        return content_type

    def _is_local_host(self) -> bool:
        try:
            host = urlsplit("//" + self.headers.get("Host", ""))
            return (
                host.username is None
                and host.password is None
                and host.hostname in ("127.0.0.1", "localhost")
                and host.port == self.server.server_port
            )
        except ValueError:
            return False

    def translate_path(self, path: str) -> str:
        candidate = Path(super().translate_path(path)).resolve()
        try:
            candidate.relative_to(DASHBOARD.resolve())
        except ValueError:
            return str(DASHBOARD / "__not_found__")
        return str(candidate)

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        logging.info("%s - %s", self.address_string(), format % args)

    def do_GET(self) -> None:
        if not self._is_local_host():
            self._send_json(403, {"error": "Доступ разрешён только с локального компьютера."})
            return
        request_path = urlsplit(self.path).path
        if request_path == "/AI-SANDBOX-HISTORY.md":
            self.send_response(302)
            self.send_header("Location", "/ai-sandbox-history.html")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return
        if request_path == "/api/tasks":
            try:
                with TASK_LOCK:
                    tasks = dashboard_tasks()
                self._send_json(200, {"tasks": tasks})
            except (OSError, ValueError, json.JSONDecodeError) as error:
                logging.exception("Task list failed")
                self._send_json(500, {"error": f"Не удалось прочитать список задач: {error}"})
            return
        if request_path == "/api/staff":
            staff_path = ROOT / "Memory" / "Agents" / "estate-staff.json"
            try:
                self._send_json(200, json.loads(staff_path.read_text(encoding="utf-8")))
            except FileNotFoundError:
                self._send_json(404, {"error": "Файл штата не найден: Memory/Agents/estate-staff.json"})
            except (OSError, json.JSONDecodeError) as error:
                logging.exception("Staff read failed")
                self._send_json(500, {"error": f"Не удалось прочитать штат поместья: {error}"})
            return
        if request_path == "/api/hunter/tasks":
            try:
                with HUNTER_LOCK:
                    tasks = list_assignments()
                self._send_json(200, {"tasks": tasks})
            except (OSError, ValueError, json.JSONDecodeError) as error:
                logging.exception("Hunter task list failed")
                self._send_json(500, {"error": f"Не удалось прочитать очередь Hunter: {error}"})
            return
        if request_path == "/api/ai-usage":
            try:
                with USAGE_LOCK:
                    self._send_json(200, dashboard_data())
            except (OSError, ValueError, json.JSONDecodeError) as error:
                logging.exception("AI usage read failed")
                self._send_json(500, {"error": f"Не удалось прочитать AI-статистику: {error}"})
            return
        if request_path == "/api/security/status":
            try:
                with SECURITY_LOCK:
                    self._send_json(200, dashboard_status(self.server.server_address))
            except (OSError, ValueError, json.JSONDecodeError) as error:
                logging.exception("Security contour status failed")
                self._send_json(500, {"error": f"Не удалось получить состояние контура: {error}"})
            return
        agent_report_route = re.fullmatch(r"/api/(watson|riskscan)/reports", request_path)
        if agent_report_route:
            try:
                query = urlsplit(self.path).query
                requested = re.fullmatch(r"file=([^&]+)", query)
                payload = agent_reports(agent_report_route.group(1), requested.group(1) if requested else None)
                self._send_json(200, payload)
            except (OSError, ValueError) as error:
                logging.exception("Agent reports read failed")
                self._send_json(404, {"error": f"Не удалось прочитать отчёты: {error}"})
            return
        agent_status_route = re.fullmatch(r"/api/(watson|riskscan)/run-status", request_path)
        if agent_status_route:
            entry = AGENT_RUN_STATE[agent_status_route.group(1)]
            with entry["lock"]:
                self._send_json(200, dict(entry["state"]))
            return
        if request_path == "/api/holmes/reports":
            try:
                query = urlsplit(self.path).query
                requested = re.fullmatch(r"file=([^&]+)", query)
                with REPORTS_LOCK:
                    payload = holmes_reports(requested.group(1) if requested else None)
                self._send_json(200, payload)
            except (OSError, ValueError) as error:
                logging.exception("Holmes reports read failed")
                self._send_json(404, {"error": f"Не удалось прочитать отчёты Холмса: {error}"})
            return
        if request_path == "/api/holmes/context":
            try:
                self._send_json(200, holmes_context())
            except (OSError, RuntimeError) as error:
                logging.exception("Holmes context failed")
                self._send_json(500, {"error": f"Не удалось собрать контекст кабинета: {error}"})
            return
        if request_path == "/api/holmes/run-status":
            with HOLMES_RUN_LOCK:
                self._send_json(200, dict(HOLMES_RUN))
            return
        if request_path == "/api/sandbox/run-status":
            with SANDBOX_RUN_LOCK:
                self._send_json(200, dict(SANDBOX_RUN))
            return
        if request_path == "/api/sandbox/report":
            query = urlsplit(self.path).query
            match = re.fullmatch(r"tool=([^&]+)", query)
            spec = SANDBOX_TOOLS.get(match.group(1) if match else "")
            if spec is None:
                self._send_json(400, {"error": "Укажи инструмент: radar, portaudit, secrets или nmap."})
                return
            report_file = sandbox_latest_report(spec["prefix"])
            if report_file is None:
                self._send_json(404, {"error": "Отчётов ещё нет — запусти инструмент кнопкой."})
                return
            try:
                data = json.loads(report_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                logging.exception("Sandbox report read failed")
                self._send_json(500, {"error": f"Не удалось прочитать отчёт: {error}"})
                return
            self._send_json(200, {"file": report_file.name, "data": data})
            return
        if request_path == "/api/jobs":
            # Л-3: реестр джобов (enabled по умолчанию, ?all=1 — все) + статус последнего запуска.
            try:
                include_all = re.fullmatch(r"all=1", urlsplit(self.path).query) is not None
                with JOBS_LOCK:
                    self._send_json(200, jobs_snapshot(include_all))
            except (OSError, ValueError, json.JSONDecodeError) as error:
                logging.exception("Jobs registry read failed")
                self._send_json(500, {"error": f"Не удалось прочитать реестр джобов: {error}"})
            return
        if request_path == "/api/agents/live":
            # ТЗ «Флот в море» (Docs/AGENT-FLEET-PLAN-2026-11-05-ZCode.md): активные
            # рейсы; единственный источник — Workspace/logs/events.jsonl, панель только читает.
            try:
                self._send_json(200, agents_live_snapshot())
            except (OSError, ValueError, json.JSONDecodeError) as error:
                logging.exception("Agents live read failed")
                self._send_json(500, {"error": f"Не удалось собрать флот: {error}"})
            return
        if request_path == "/api/agents/history":
            # ТЗ «Флот в море»: завершённые рейсы с итогами; ?limit=20 по умолчанию (1..100).
            try:
                raw_limit = re.fullmatch(r"limit=(\d{1,3})", urlsplit(self.path).query)
                limit = int(raw_limit.group(1)) if raw_limit else 20
                self._send_json(200, agents_history_snapshot(limit=limit))
            except (OSError, ValueError, json.JSONDecodeError) as error:
                logging.exception("Agents history read failed")
                self._send_json(500, {"error": f"Не удалось собрать причалы: {error}"})
            return
        super().do_GET()

    def _read_json_body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("Некорректная длина запроса.") from error
        if length < 1 or length > 8192:
            raise ValueError("Размер JSON-запроса должен быть от 1 до 8192 байт.")
        if self.headers.get_content_type() != "application/json":
            raise ValueError("Ожидался Content-Type: application/json.")
        try:
            value = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("Некорректный JSON.") from error
        if not isinstance(value, dict):
            raise ValueError("JSON должен быть объектом.")
        return value

    def _run_ai_usage_review(self) -> dict:
        result = subprocess.run(
            [sys.executable, str(AGENT), "--ai-usage-review"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=100,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
        )
        if result.returncode:
            logging.error("Barrymore AI usage review failed: %s", result.stderr.strip())
            raise RuntimeError(result.stderr.strip() or "Бэрримор не смог подготовить обзор.")
        try:
            response = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise RuntimeError("Бэрримор вернул некорректный ответ.") from error
        if not isinstance(response, dict) or not isinstance(response.get("summary"), str):
            raise RuntimeError("Бэрримор вернул ответ неожиданного формата.")
        return response

    def do_POST(self) -> None:
        if not self._is_local_host():
            self._send_json(403, {"error": "Доступ разрешён только с локального компьютера."})
            return
        request_path = urlsplit(self.path).path
        task_done = re.fullmatch(r"/api/tasks/[a-z0-9][a-z0-9-]{0,63}/done", request_path)
        task_stage = re.fullmatch(
            r"/api/tasks/([a-z0-9][a-z0-9-]{0,63})/stage/(analysis|todo|in-progress|test|done)",
            request_path,
        )
        task_comment = re.fullmatch(r"/api/tasks/([a-z0-9][a-z0-9-]{0,63})/comments", request_path)
        # Л-3: запуск джоба из реестра tools/ops/jobs.json.
        jobs_run = re.fullmatch(r"/api/jobs/([a-z0-9][a-z0-9-]{0,63})/run", request_path)
        hunter_tasks_route = "/api/hunter/tasks"
        security_route = "/api/security/check"
        security_targets_route = "/api/security/targets"
        holmes_implement_route = "/api/holmes/implement"
        body_routes = {"/api/ai-usage/snapshots", "/api/ai-usage/settings"}
        sandbox_run_route = "/api/sandbox/run"
        bodyless_routes = {
            "/api/refresh-brief",
            "/api/ai-usage/ask-barrymore",
            "/api/holmes/run",
            "/api/watson/run",
            "/api/riskscan/run",
        }
        if request_path not in body_routes | bodyless_routes and not task_done and not task_stage and not task_comment and not jobs_run and request_path not in (hunter_tasks_route, security_route, security_targets_route, holmes_implement_route, sandbox_run_route):
            self._send_json(404, {"error": "Неизвестный локальный endpoint."})
            return

        origin = self.headers.get("Origin")
        if not origin:
            self._send_json(403, {"error": "Запрос должен исходить из локального дашборда."})
            return
        try:
            parsed_origin = urlsplit(origin)
        except ValueError:
            self._send_json(403, {"error": "Некорректный источник запроса."})
            return
        if (
            parsed_origin.scheme != "http"
            or parsed_origin.netloc.casefold() != self.headers.get("Host", "").casefold()
        ):
            self._send_json(403, {"error": "Обновление разрешено только из локального дашборда."})
            return

        if request_path in bodyless_routes and self.headers.get("Content-Length", "0") != "0":
            self._send_json(400, {"error": "Endpoint не принимает тело запроса."})
            return

        if request_path in body_routes:
            try:
                payload = self._read_json_body()
                with USAGE_LOCK:
                    if request_path == "/api/ai-usage/snapshots":
                        snapshot = add_snapshot(payload)
                        self._send_json(201, {"snapshot": snapshot})
                    else:
                        enabled = payload.get("include_in_morning_brief")
                        settings = set_include_in_morning_brief(enabled)
                        self._send_json(200, {"settings": settings})
            except (OSError, ValueError, json.JSONDecodeError) as error:
                self._send_json(400 if isinstance(error, ValueError) else 500, {"error": str(error)})
            return

        if request_path == holmes_implement_route:
            try:
                payload = self._read_json_body()
            except ValueError as error:
                self._send_json(400, {"error": str(error)})
                return
            file_name = payload.get("file")
            items = payload.get("items")
            if not isinstance(file_name, str) or not re.fullmatch(
                r"Report-\d{4}-\d{2}-\d{2}-holmes-audit\.md", file_name
            ):
                self._send_json(400, {"error": "Некорректное имя отчёта."})
                return
            if not isinstance(items, list) or not items or len(items) > 20:
                self._send_json(400, {"error": "Список инициатив пуст или слишком велик."})
                return
            results = {"created": [], "existing": [], "errors": []}
            try:
                with TASK_LOCK:
                    for item in items[:20]:
                        if not isinstance(item, dict):
                            results["errors"].append("bad-item")
                            continue
                        fid = str(item.get("id", ""))
                        severity = str(item.get("severity", "P2"))
                        detail = str(item.get("detail", ""))[:300]
                        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,55}", fid):
                            results["errors"].append(fid or "bad-id")
                            continue
                        outcome = holmes_ensure_task(fid, severity, detail)
                        if outcome.startswith("created:"):
                            results["created"].append(outcome.split(":", 1)[1])
                        elif outcome == "exists":
                            results["existing"].append(f"holmes-{fid}")
                        else:
                            results["errors"].append(f"{fid}:{outcome}")
                self._send_json(200, results)
            except OSError as error:
                logging.exception("Holmes implement failed")
                self._send_json(500, {"error": f"Не удалось создать задачи: {error}"})
            return

        agent_run_route = re.fullmatch(r"/api/(watson|riskscan)/run", request_path)
        if agent_run_route:
            runtime = agent_run_route.group(1)
            entry = AGENT_RUN_STATE[runtime]
            if not entry["lock"].acquire(blocking=False):
                self._send_json(409, {"error": "Состояние запуска уже изменяется."})
                return
            try:
                if entry["state"]["running"]:
                    self._send_json(409, {"error": f"Прогон {AGENT_RUNTIMES[runtime]['label']} уже идёт — дождитесь завершения."})
                    return
                started_at = datetime.now(TASHKENT).isoformat(timespec="seconds")
                entry["state"].update({
                    "running": True,
                    "started_at": started_at,
                    "finished_at": None,
                    "returncode": None,
                    "error": None,
                })
                threading.Thread(target=_agent_run_worker, args=(runtime,), name=f"{runtime}-run", daemon=True).start()
                logging.info("%s run started from dashboard", AGENT_RUNTIMES[runtime]["label"])
                self._send_json(202, {"started": True, "started_at": started_at})
            finally:
                entry["lock"].release()
            return

        if request_path == "/api/holmes/run":
            if not HOLMES_RUN_LOCK.acquire(blocking=False):
                self._send_json(409, {"error": "Состояние запуска уже изменяется."})
                return
            try:
                if HOLMES_RUN["running"]:
                    self._send_json(409, {"error": "Расследование уже идёт — дождитесь завершения."})
                    return
                started_at = datetime.now(TASHKENT).isoformat(timespec="seconds")
                HOLMES_RUN.update({
                    "running": True,
                    "started_at": started_at,
                    "finished_at": None,
                    "returncode": None,
                    "error": None,
                })
                threading.Thread(target=_holmes_run_worker, name="holmes-run", daemon=True).start()
                logging.info("Holmes run started from dashboard")
                self._send_json(202, {"started": True, "started_at": started_at})
            finally:
                HOLMES_RUN_LOCK.release()
            return

        if request_path == "/api/sandbox/run":
            try:
                payload = self._read_json_body()
            except ValueError as error:
                self._send_json(400, {"error": str(error)})
                return
            tool = payload.get("tool")
            if tool not in SANDBOX_TOOLS:
                self._send_json(400, {"error": "Неизвестный инструмент: radar, portaudit, secrets или nmap."})
                return
            args = payload.get("args") or []
            if (
                not isinstance(args, list)
                or len(args) > 20
                or not all(isinstance(a, str) and len(a) <= 300 for a in args)
            ):
                self._send_json(400, {"error": "Некорректные аргументы запуска."})
                return
            # Гвард A-01: только флаги из белого списка инструмента, со строгими значениями.
            sandbox_allowed = SANDBOX_ARG_ALLOW.get(tool, {})
            index = 0
            while index < len(args):
                flag = args[index]
                if flag not in sandbox_allowed:
                    self._send_json(400, {"error": f"Аргумент «{flag}» не разрешён для «{tool}»."})
                    return
                value_count = sandbox_allowed[flag]
                index += 1
                for _ in range(value_count):
                    if index >= len(args):
                        self._send_json(400, {"error": f"«{flag}» ожидает значение."})
                        return
                    value = args[index]
                    if flag == "--ports" and not SANDBOX_PORTS_RE.fullmatch(value):
                        self._send_json(400, {"error": "Некорректный формат --ports."})
                        return
                    if flag in ("--days", "--limit") and not SANDBOX_NUM_RE.fullmatch(value):
                        self._send_json(400, {"error": f"Некорректный формат {flag}."})
                        return
                    index += 1
            if not SANDBOX_RUN_LOCK.acquire(blocking=False):
                self._send_json(409, {"error": "Инструмент песочницы уже запускается."})
                return
            try:
                if SANDBOX_RUN["running"]:
                    self._send_json(
                        409,
                        {"error": f"«{SANDBOX_RUN.get('tool')}» ещё выполняется — дождись завершения."},
                    )
                    return
                started_at = datetime.now(TASHKENT).isoformat(timespec="seconds")
                SANDBOX_RUN.update({
                    "running": True,
                    "tool": tool,
                    "started_at": started_at,
                    "finished_at": None,
                    "returncode": None,
                    "summary": None,
                    "error": None,
                })
                threading.Thread(
                    target=_sandbox_run_worker, args=(tool, args), name=f"sandbox-{tool}", daemon=True
                ).start()
                logging.info("Sandbox tool %s started from dashboard", tool)
                self._send_json(202, {"started": True, "tool": tool, "started_at": started_at})
            finally:
                SANDBOX_RUN_LOCK.release()
            return

        if request_path == hunter_tasks_route:
            try:
                payload = self._read_json_body()
            except ValueError as error:
                self._send_json(400, {"error": str(error)})
                return
            if not HUNTER_LOCK.acquire(blocking=False):
                self._send_json(409, {"error": "Очередь Hunter уже обновляется — повторите попытку."})
                return
            try:
                task = create_assignment(payload)
                self._send_json(201, {"task": task, "tasks": list_assignments()})
            except ValueError as error:
                self._send_json(400, {"error": str(error)})
            except (OSError, json.JSONDecodeError) as error:
                logging.exception("Hunter task save failed")
                self._send_json(500, {"error": f"Не удалось сохранить поручение Hunter: {error}"})
            finally:
                HUNTER_LOCK.release()
            return

        if request_path == security_route:
            try:
                payload = self._read_json_body()
            except ValueError as error:
                self._send_json(400, {"error": str(error)})
                return
            host = payload.get("host")
            if not isinstance(host, str) or not host.strip():
                self._send_json(400, {"error": "Укажите host цели проверки."})
                return
            if not SECURITY_LOCK.acquire(blocking=False):
                self._send_json(409, {"error": "Проверка уже выполняется — дождитесь завершения."})
                return
            try:
                self._send_json(200, run_check(host.strip()))
            except PermissionError as error:
                self._send_json(403, {"error": str(error)})
            except ValueError as error:
                self._send_json(400, {"error": str(error)})
            except OSError as error:
                logging.exception("Security contour check failed")
                self._send_json(500, {"error": f"Проверка не удалась: {error}"})
            finally:
                SECURITY_LOCK.release()
            return

        if request_path == security_targets_route:
            try:
                payload = self._read_json_body()
            except ValueError as error:
                self._send_json(400, {"error": str(error)})
                return
            if not SECURITY_LOCK.acquire(blocking=False):
                self._send_json(409, {"error": "Список целей уже изменяется — повторите попытку."})
                return
            try:
                targets = add_target(payload)
                self._send_json(201, {"targets": targets})
            except ValueError as error:
                self._send_json(400, {"error": str(error)})
            except OSError as error:
                logging.exception("Security target add failed")
                self._send_json(500, {"error": f"Не удалось сохранить цель: {error}"})
            finally:
                SECURITY_LOCK.release()
            return

        if request_path == "/api/ai-usage/ask-barrymore":
            if not REFRESH_LOCK.acquire(blocking=False):
                self._send_json(409, {"error": "Бэрримор уже выполняет другой запрос."})
                return
            try:
                self._send_json(200, self._run_ai_usage_review())
            except subprocess.TimeoutExpired:
                self._send_json(504, {"error": "Обзор не завершился за 100 секунд. Проверьте шлюз FreeLLMAPI."})
            except (OSError, RuntimeError) as error:
                logging.exception("Barrymore AI usage review failed")
                self._send_json(500, {"error": str(error)})
            finally:
                REFRESH_LOCK.release()
            return

        if task_done:
            task_id = request_path.split("/")[3]
            if not TASK_ID_PATTERN.fullmatch(task_id):
                self._send_json(400, {"error": "Некорректный идентификатор задачи."})
                return
            # Врата/подпись как у stage: by из тела, дефолт Sovereign (P1 ревизора:
            # /done раньше обходил врата и писал "unknown").
            by = "Sovereign"
            if self.headers.get("Content-Length", "0") not in ("", "0"):
                try:
                    done_payload = self._read_json_body()
                    declared = done_payload.get("by")
                    if isinstance(declared, str) and declared.strip():
                        by = declared.strip()[:100]
                except ValueError as error:
                    self._send_json(400, {"error": str(error)})
                    return
            if not can_transition(task_id, by, "done"):
                self._send_json(403, {
                    "error": (f"Автор «{by}» не может закрыть «{task_id}»: "
                              "врата стоят только на владельца работы (source/owner).")})
                return
            if not TASK_LOCK.acquire(blocking=False):
                self._send_json(409, {"error": "Список задач уже обновляется."})
                return
            try:
                task = mark_done(task_id, by=by)
                self._send_json(200, {"task": task, "tasks": dashboard_tasks()})
            except FileNotFoundError as error:
                self._send_json(404, {"error": str(error)})
            except (OSError, ValueError, json.JSONDecodeError) as error:
                logging.exception("Task update failed")
                self._send_json(500, {"error": f"Не удалось обновить задачу: {error}"})
            finally:
                TASK_LOCK.release()
            return

        if task_stage:
            task_id, stage = task_stage.group(1), task_stage.group(2)
            # Л-5: автор перехода декларируется в JSON-теле ("by"), дефолт "Sovereign"
            # (loopback, один хозяин, без логинов). Пустое тело = дефолт.
            by = "Sovereign"
            declared_by = None
            if self.headers.get("Content-Length", "0") not in ("", "0"):
                try:
                    stage_payload = self._read_json_body()
                except ValueError as error:
                    self._send_json(400, {"error": str(error)})
                    return
                declared = stage_payload.get("by")
                if isinstance(declared, str) and declared.strip():
                    by = declared.strip()[:100]
                    declared_by = by
            # Врата требуют ЯВНО объявленного автора (P2 ревизора: дефолт Sovereign
            # = ключ от врат — обходится omit-ом поля). Рабочие колонки — дефолт ок.
            if stage in ("test", "done") and declared_by is None:
                self._send_json(400, {"error": "Для перевода в «Проверку/Готово» объяви автора: поле by в JSON-теле."})
                return
            # Врата Sovereign (2026-11-06): заявлять готовность (test/done) может
            # только владелец работы (source/owner/ZCode/Sovereign).
            if not can_transition(task_id, by, stage):
                self._send_json(403, {
                    "error": (f"Автор «{by}» не может переводить «{task_id}» в «{stage}»: "
                              "врата стоят только на владельца работы (source/owner).")})
                return
            if not TASK_LOCK.acquire(blocking=False):
                self._send_json(409, {"error": "Список задач уже обновляется."})
                return
            try:
                task = set_stage(task_id, stage, by=by)
                self._send_json(200, {"task": task, "tasks": dashboard_tasks()})
            except FileNotFoundError as error:
                self._send_json(404, {"error": str(error)})
            except (OSError, ValueError, json.JSONDecodeError) as error:
                logging.exception("Task stage update failed")
                self._send_json(500, {"error": f"Не удалось обновить задачу: {error}"})
            finally:
                TASK_LOCK.release()
            return

        if task_comment:
            # Комментарий к карточке (Sovereign 2026-11-06). by из тела, дефолт Sovereign.
            try:
                payload = self._read_json_body()
            except ValueError as error:
                self._send_json(400, {"error": str(error)})
                return
            by = payload.get("by")
            if not isinstance(by, str) or not by.strip():
                by = "Sovereign"
            by = by.strip()[:100]
            text = payload.get("text")
            if not isinstance(text, str):
                self._send_json(400, {"error": "Ожидалось поле text (строка)."})
                return
            if not TASK_LOCK.acquire(blocking=False):
                self._send_json(409, {"error": "Список задач уже обновляется."})
                return
            try:
                task = add_comment(task_comment.group(1), by, text)
                self._send_json(200, {"task": task, "tasks": dashboard_tasks()})
            except FileNotFoundError as error:
                self._send_json(404, {"error": str(error)})
            except (OSError, ValueError, json.JSONDecodeError) as error:
                self._send_json(400, {"error": str(error)})
            finally:
                TASK_LOCK.release()
            return

        if jobs_run:
            # Л-3: немедленный ответ {"started": true}, процесс ведёт поток-наблюдатель.
            status_code, response = start_job(jobs_run.group(1))
            self._send_json(status_code, response)
            return

        manual_refresh = self.headers.get("X-Barrymore-Manual")
        if manual_refresh not in (None, "true"):
            self._send_json(400, {"error": "Некорректный режим проверки доклада."})
            return

        if not REFRESH_LOCK.acquire(blocking=False):
            self._send_json(409, {"error": "Доклад уже обновляется."})
            return

        try:
            previous = (DASHBOARD / "brief.js").read_bytes() if (DASHBOARD / "brief.js").exists() else None
            brief = run_brief(retry_llm_error=manual_refresh == "true")
            current = (DASHBOARD / "brief.js").read_bytes()
            self._send_json(200, {"brief": brief, "changed": current != previous})
        except subprocess.TimeoutExpired:
            self._send_json(504, {"error": "Генератор не завершился за 100 секунд. Проверьте шлюз FreeLLMAPI."})
        except (OSError, RuntimeError, json.JSONDecodeError) as error:
            logging.exception("Brief refresh failed")
            self._send_json(500, {"error": str(error)})
        finally:
            REFRESH_LOCK.release()


def sandbox_latest_report(prefix: str):
    if not SANDBOX_REPORT_DIR.exists():
        return None
    files = sorted(SANDBOX_REPORT_DIR.glob(f"{prefix}-*.json"), reverse=True)
    return files[0] if files else None


def _sandbox_run_worker(tool: str, args: list) -> None:
    """Прогон инструмента песочницы в фоне (stdino-стайл Холмса: статус в SANDBOX_RUN)."""
    spec = SANDBOX_TOOLS[tool]
    command = [sys.executable, str(spec["script"]), *args]
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=spec["timeout"],
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
        )
        with SANDBOX_RUN_LOCK:
            SANDBOX_RUN.update({
                "running": False,
                "finished_at": datetime.now(TASHKENT).isoformat(timespec="seconds"),
                "returncode": result.returncode,
                "summary": (result.stdout or "")[-4000:] or None,
                "error": None if result.returncode == 0
                else (result.stderr.strip() or f"код {result.returncode}")[-800:],
            })
        logging.info("Sandbox tool %s finished with code %s", tool, result.returncode)
    except subprocess.TimeoutExpired:
        with SANDBOX_RUN_LOCK:
            SANDBOX_RUN.update({
                "running": False,
                "finished_at": datetime.now(TASHKENT).isoformat(timespec="seconds"),
                "returncode": None,
                "summary": None,
                "error": f"Инструмент не завершился за {spec['timeout']} с.",
            })
    except Exception as error:
        with SANDBOX_RUN_LOCK:
            SANDBOX_RUN.update({
                "running": False,
                "finished_at": datetime.now(TASHKENT).isoformat(timespec="seconds"),
                "returncode": None,
                "summary": None,
                "error": str(error)[:800],
            })
        logging.exception("Sandbox tool %s failed", tool)


# --- Реестр джобов: GET /api/jobs + POST /api/jobs/<id>/run (Л-3, Docs/DATA-FOUNDATION-PLAN-2026-11-04) ---

_JOBS_REQUIRED_FIELDS = ("id", "title", "owner", "cmd", "timeout_s", "enabled")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _load_jobs_registry() -> list:
    """Прочитать tools/ops/jobs.json; битый реестр — ValueError с внятной ошибкой."""
    raw = json.loads(JOBS_REGISTRY_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("jobs.json должен быть массивом записей.")
    for index, job in enumerate(raw):
        if not isinstance(job, dict):
            raise ValueError(f"jobs.json[{index}]: запись должна быть объектом.")
        for field in _JOBS_REQUIRED_FIELDS:
            if field not in job:
                raise ValueError(f"jobs.json[{index}]: нет обязательного поля {field}.")
        if not isinstance(job["cmd"], list) or not all(isinstance(arg, str) for arg in job["cmd"]):
            raise ValueError(f"jobs.json[{index}]: cmd должен быть списком строк.")
    return raw


def _load_jobs_state() -> dict:
    """Прочитать Workspace/logs/jobs_state.json (конверт evo.ops.job_state); нет файла или битый — {}."""
    try:
        raw = json.loads(JOBS_STATE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {}
    if (
        isinstance(raw, dict)
        and raw.get("schema_id") == "evo.ops.job_state"
        and isinstance(raw.get("payload"), dict)
    ):
        return raw["payload"]
    return raw if isinstance(raw, dict) else {}


def _save_jobs_state(payload: dict) -> None:
    """Перезаписать jobs_state.json одним конвертом schema_id="evo.ops.job_state"."""
    envelope = {
        "schema_id": "evo.ops.job_state",
        "schema_version": 1,
        "produced_by": "dashboard-server",
        "produced_at": _utc_now_iso(),
        "payload": payload,
        "refs": {},
    }
    _atomic_write_json(JOBS_STATE_PATH, envelope)


def _job_is_running(state_entry) -> bool:
    """Маркер «джоб уже запущен»: started_at есть, finished_at ещё нет (по ТЗ Л-3 → 409)."""
    return (
        isinstance(state_entry, dict)
        and bool(state_entry.get("started_at"))
        and not state_entry.get("finished_at")
    )


def jobs_snapshot(include_all: bool = False) -> dict:
    """Собрать payload GET /api/jobs: реестр (enabled по умолчанию) + статус последнего запуска."""
    state = _load_jobs_state()
    jobs = []
    for job in _load_jobs_registry():
        if not include_all and not job.get("enabled"):
            continue
        entry = dict(job)
        last_run = state.get(str(job.get("id")))
        entry["last_run"] = dict(last_run) if isinstance(last_run, dict) else None
        entry["running"] = _job_is_running(last_run)
        jobs.append(entry)
    return {"jobs": jobs}


def _job_cwd(job: dict) -> Path:
    raw = Path(str(job.get("cwd") or "."))
    return raw if raw.is_absolute() else ROOT / raw


def _jobs_run_worker(job_id: str, cmd: list, cwd: Path, timeout_s: int, started_at: str) -> None:
    """Поток-наблюдатель: ждёт процесс с таймаутом (kill при превышении) и пишет финальный state."""
    exit_code = -1
    started_monotonic = time.monotonic()
    try:
        process = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
        )
        try:
            exit_code = process.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            process.kill()
            exit_code = process.wait()
    except Exception:
        logging.exception("Job %s failed to start", job_id)
        exit_code = -1
    finished_at = _utc_now_iso()
    duration_s = round(time.monotonic() - started_monotonic, 1)
    with JOBS_LOCK:
        state = _load_jobs_state()
        state[job_id] = {
            "started_at": started_at,
            "finished_at": finished_at,
            "exit_code": exit_code,
            "duration_s": duration_s,
        }
        _save_jobs_state(state)
    logging.info("Job %s finished with code %s", job_id, exit_code)


def start_job(job_id: str) -> tuple:
    """Запустить джоб из реестра; возвращает (http_status, response) для обработчика.

    Повторный запуск уже идущего джоба (started_at без finished_at) — 409.
    """
    try:
        registry = _load_jobs_registry()
    except (OSError, json.JSONDecodeError, ValueError) as error:
        return 500, {"error": f"Реестр джобов не читается: {error}"}
    job = next((entry for entry in registry if str(entry.get("id")) == job_id), None)
    if job is None:
        return 404, {"error": f"Джоб не найден в реестре: {job_id}"}
    if not job.get("enabled"):
        return 403, {"error": f"Джоб выключен (enabled=false): {job_id}"}
    with JOBS_LOCK:
        state = _load_jobs_state()
        if _job_is_running(state.get(job_id)):
            return 409, {"error": f"Джоб уже выполняется — дождитесь завершения: {job_id}"}
        started_at = _utc_now_iso()
        state[job_id] = {"started_at": started_at, "finished_at": None, "exit_code": None, "duration_s": None}
        try:
            _save_jobs_state(state)
        except OSError as error:
            return 500, {"error": f"Не удалось записать jobs_state.json: {error}"}
        threading.Thread(
            target=_jobs_run_worker,
            args=(job_id, list(job["cmd"]), _job_cwd(job), int(job.get("timeout_s") or 600), started_at),
            name=f"job-{job_id}",
            daemon=True,
        ).start()
    return 202, {"started": True, "id": job_id, "started_at": started_at}


# --- Флот агентов: GET /api/agents/live + GET /api/agents/history ---
# (ТЗ Docs/AGENT-FLEET-PLAN-2026-11-05-ZCode.md, фаза 1)

# Единственный источник — журнал Л-2 (конверт Л-1); панель ничего не собирает сама.
AGENTS_LOG_PATH = ROOT / "Workspace" / "logs" / "events.jsonl"
AGENTS_KINDS = ("agent.started", "agent.lane", "agent.pulse", "agent.storm", "agent.finished")
AGENTS_SILENCE_STORM_MIN = 30  # тишина дольше 30 минут = шторм (метрики пульса ТЗ)
AGENTS_TAIL_LINES = 5000  # читаем только хвост журнала, чтобы не душить IO на больших файлах
AGENTS_RECENT_LIMIT = 5  # events_recent в карточке корабля


def _parse_agent_ts(value) -> datetime | None:
    """ISO-время журнала (…Z) → aware datetime UTC; мусор → None."""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _read_agent_events(log_path=None) -> list:
    """Хвост events.jsonl → конверты с payload.kind из AGENTS_KINDS.

    Битые и чужие строки пропускаются тихо: панель — читатель, падать на мусоре
    не имеет права. Файл не пишется и не переформатируется.
    """
    path = Path(log_path) if log_path is not None else AGENTS_LOG_PATH
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            lines = handle.readlines()
    except OSError:
        return []
    events = []
    for raw_line in lines[-AGENTS_TAIL_LINES:]:
        line = raw_line.strip()
        if not line:
            continue  # пустые строки формата записи (см. tools/lib/log_event.py)
        try:
            envelope = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(envelope, dict):
            continue
        payload = envelope.get("payload")
        if isinstance(payload, dict) and payload.get("kind") in AGENTS_KINDS:
            events.append(envelope)
    return events


def _agent_ship(envelope: dict) -> str:
    """Имя корабля: payload.by (схема evo.agent.event по ТЗ), иначе produced_by (фаза 1)."""
    payload = envelope.get("payload") or {}
    by = payload.get("by")
    if isinstance(by, str) and by.strip():
        return by.strip()
    produced = envelope.get("produced_by")
    if isinstance(produced, str) and produced.strip():
        return produced.strip()
    return "(без имени)"


def _agent_sort_key(envelope: dict) -> datetime:
    return _parse_agent_ts(envelope.get("ts") or envelope.get("produced_at")) or datetime.min.replace(tzinfo=timezone.utc)


def _agent_text(envelope: dict, limit: int = 140) -> str:
    """Короткая человекочитаемая строка события для ленты/цепочки."""
    payload = envelope.get("payload") or {}
    kind = payload.get("kind")
    candidates = {
        "agent.started": ("task", "title", "goal", "spec"),
        "agent.lane": ("lane", "lane_id", "step", "title", "note"),
        "agent.storm": ("reason", "error", "note", "step"),
        "agent.pulse": ("step", "note", "message", "status"),
        "agent.finished": ("verdict", "task", "title", "note"),
    }
    for field in candidates.get(kind, ()):
        value = payload.get(field)
        if isinstance(value, (str, int, float, bool)) and str(value).strip():
            return str(value).strip()[:limit]
    return kind if isinstance(kind, str) else "событие"


def _agent_voyages(events: list) -> list:
    """События корабля → список рейсов: каждый agent.started открывает новый рейс."""
    voyages = []
    current = []
    for envelope in events:
        if (envelope.get("payload") or {}).get("kind") == "agent.started" and current:
            voyages.append(current)
            current = []
        current.append(envelope)
    if current:
        voyages.append(current)
    return voyages


def _agent_started_at(voyage: list) -> str | None:
    """ts начала рейса: первый agent.started, иначе первое событие (корабли без started-писателя)."""
    for envelope in voyage:
        if (envelope.get("payload") or {}).get("kind") == "agent.started":
            ts = envelope.get("ts") or envelope.get("produced_at")
            return ts if isinstance(ts, str) else None
    if not voyage:
        return None
    ts = voyage[0].get("ts") or voyage[0].get("produced_at")
    return ts if isinstance(ts, str) else None


def _agent_lanes(voyage: list) -> dict:
    """Лейны рейса: done = закрытые agent.lane; total = заявленный в started (или None)."""
    done = sum(1 for envelope in voyage if (envelope.get("payload") or {}).get("kind") == "agent.lane")
    total = None
    for envelope in voyage:
        if (envelope.get("payload") or {}).get("kind") != "agent.started":
            continue
        payload = envelope.get("payload") or {}
        raw = payload.get("lanes_total", payload.get("lanes"))
        if isinstance(raw, bool):
            continue
        if isinstance(raw, int) and raw >= 0:
            total = raw
        elif isinstance(raw, list):
            total = len(raw)
    return {"done": done, "total": total}


def _agent_voyage_task(voyage: list) -> str:
    """Задача рейса: из последнего agent.started, иначе «задача не объявлена»."""
    for envelope in reversed(voyage):
        if (envelope.get("payload") or {}).get("kind") != "agent.started":
            continue
        payload = envelope.get("payload") or {}
        for field in ("task", "title", "goal"):
            value = payload.get(field)
            if isinstance(value, str) and value.strip():
                return value.strip()[:200]
    return "задача не объявлена"


def _agent_live_entry(ship: str, voyage: list, moment: datetime) -> dict:
    """Карточка корабля для /api/agents/live (метрики ТЗ: лейны, пульс, штормы, ETA-оценка)."""
    started_ts = _agent_started_at(voyage)
    started_dt = _parse_agent_ts(started_ts)
    last_ts = None
    if voyage:
        last_ts = _parse_agent_ts(voyage[-1].get("ts") or voyage[-1].get("produced_at"))
    pulse_min = None
    if last_ts is not None:
        pulse_min = round(max(0.0, (moment - last_ts).total_seconds() / 60.0), 1)
    storms = sum(1 for envelope in voyage if (envelope.get("payload") or {}).get("kind") == "agent.storm")
    # Правило ТЗ: шторм = storm-событие без finished (рейс ещё не завершён)
    # либо тишина > 30 минут.
    has_storm = storms > 0
    silence_storm = pulse_min is not None and pulse_min > AGENTS_SILENCE_STORM_MIN
    if pulse_min is None:
        pulse_status = "неизвестно"
    elif has_storm or silence_storm:
        pulse_status = "шторм"
    elif pulse_min < 10:
        pulse_status = "идёт"
    else:
        pulse_status = "тихо"
    lanes = _agent_lanes(voyage)
    elapsed_min = None
    if started_dt is not None:
        elapsed_min = max(0.0, (moment - started_dt).total_seconds() / 60.0)
    eta_min = None
    if lanes["total"] is not None and 0 < lanes["done"] < lanes["total"] and started_dt is not None:
        # ETA-оценка по фактической скорости лейнов (ТЗ, помечается «~»): от старта
        # до последнего закрытого лейна; без лейнов — fallback на время с старта.
        lane_span = None
        for envelope in voyage:
            if (envelope.get("payload") or {}).get("kind") == "agent.lane":
                lane_dt = _parse_agent_ts(envelope.get("ts") or envelope.get("produced_at"))
                if lane_dt is not None and lane_dt > started_dt:
                    lane_span = max(0.0, (lane_dt - started_dt).total_seconds() / 60.0)
        if lane_span is None:
            lane_span = elapsed_min
        if lane_span and lane_span > 0:
            eta_min = round((lanes["total"] - lanes["done"]) * (lane_span / lanes["done"]), 1)
    recent = [
        {
            "kind": (envelope.get("payload") or {}).get("kind"),
            "ts": envelope.get("ts") or envelope.get("produced_at"),
            "text": _agent_text(envelope),
        }
        for envelope in voyage[-AGENTS_RECENT_LIMIT:]
    ]
    return {
        "by": ship,
        "task": _agent_voyage_task(voyage),
        "status": "шторм" if (has_storm or silence_storm) else "море",
        "pulse_status": pulse_status,
        "lanes": lanes,
        "pulse_min": pulse_min,
        "storms": storms,
        "started_at": started_ts,
        "eta_min": eta_min,
        "elapsed_min": round(elapsed_min, 1) if elapsed_min is not None else None,
        "events_recent": recent,
    }


def agents_live_snapshot(log_path=None, now=None) -> dict:
    """Агрегат GET /api/agents/live: активные рейсы по кораблям из events.jsonl.

    Корабль = payload.by либо produced_by (фаза 1: писателей agent.started может
    не быть — тогда рейс собирается из любых agent.*-событий корабля). Корабль с
    завершённым последним рейсом уходит в history, в live не попадает.
    """
    moment = now if now is not None else datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    ships = {}
    for envelope in _read_agent_events(log_path):
        ships.setdefault(_agent_ship(envelope), []).append(envelope)
    live = []
    for ship, events in ships.items():
        events.sort(key=_agent_sort_key)
        voyages = _agent_voyages(events)
        if not voyages:
            continue
        current = voyages[-1]
        if (current[-1].get("payload") or {}).get("kind") == "agent.finished":
            continue  # корабль у причала: GET /api/agents/history
        live.append(_agent_live_entry(ship, current, moment))
    live.sort(key=lambda entry: (entry["started_at"] or "", entry["by"]))
    return {"ships": live, "generated_at": _utc_now_iso()}


def agents_history_snapshot(limit: int = 20, log_path=None) -> dict:
    """Агрегат GET /api/agents/history: завершённые рейсы, новые сверху.

    Итоги — из payload финального agent.finished (вердикт, файлы, тесты, факты
    токенов/времени); chain — цепочка «начальные → промежуточные → итоговые».
    """
    limit = max(1, min(int(limit), 100))
    ships = {}
    for envelope in _read_agent_events(log_path):
        ships.setdefault(_agent_ship(envelope), []).append(envelope)
    finished_voyages = []
    for ship, events in ships.items():
        events.sort(key=_agent_sort_key)
        for voyage in _agent_voyages(events):
            if voyage and (voyage[-1].get("payload") or {}).get("kind") == "agent.finished":
                finished_voyages.append((ship, voyage))
    finished_voyages.sort(key=lambda pair: _agent_sort_key(pair[1][-1]), reverse=True)
    history = []
    for ship, voyage in finished_voyages[:limit]:
        final = voyage[-1]
        final_payload = final.get("payload") or {}
        started_ts = _agent_started_at(voyage)
        started_dt = _parse_agent_ts(started_ts)
        finished_dt = _parse_agent_ts(final.get("ts") or final.get("produced_at"))
        minutes = final_payload.get("minutes")
        if isinstance(minutes, bool) or not isinstance(minutes, (int, float)):
            minutes = None
            if started_dt is not None and finished_dt is not None:
                minutes = round(max(0.0, (finished_dt - started_dt).total_seconds() / 60.0), 1)
        tokens = final_payload.get("tokens")
        if isinstance(tokens, bool) or not isinstance(tokens, (int, float)):
            tokens = None
        files = final_payload.get("files") if isinstance(final_payload.get("files"), list) else None
        tests = final_payload.get("tests") if isinstance(final_payload.get("tests"), (str, list)) else None
        chain = []
        for envelope in voyage:
            kind = (envelope.get("payload") or {}).get("kind")
            if kind == "agent.started":
                role = "initial"
            elif kind == "agent.finished":
                role = "final"
            else:
                role = "intermediate"
            chain.append({
                "role": role,
                "kind": kind,
                "ts": envelope.get("ts") or envelope.get("produced_at"),
                "text": _agent_text(envelope),
            })
        history.append({
            "by": ship,
            "task": _agent_voyage_task(voyage),
            "started_at": started_ts,
            "finished_at": final.get("ts") or final.get("produced_at"),
            "verdict": final_payload.get("verdict") if isinstance(final_payload.get("verdict"), str) else None,
            "files": files,
            "tests": tests,
            "tokens": tokens,
            "minutes": minutes,
            "lanes": _agent_lanes(voyage),
            "storms": sum(1 for envelope in voyage if (envelope.get("payload") or {}).get("kind") == "agent.storm"),
            "chain": chain,
        })
    return {"voyages": history, "generated_at": _utc_now_iso()}


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(LOG_DIR / "dashboard-server.log", encoding="utf-8")
    handler.setFormatter(TashkentFormatter("%(asctime)s UZT %(levelname)s %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[handler])
    server = None
    for attempt in range(5):
        try:
            server = DashboardHTTPServer(("127.0.0.1", PORT), DashboardHandler)
            break
        except OSError:
            if attempt == 4:
                logging.exception("Could not bind dashboard server to 127.0.0.1:%s", PORT)
                if sys.stdout is not None:
                    print(
                        f"Порт 127.0.0.1:{PORT} занят — второй экземпляр дашборда не запускаю.",
                        file=sys.stderr,
                    )
                    print(
                        f"Канонический адрес один: http://127.0.0.1:{PORT} — сервер, вероятно, уже работает.",
                        file=sys.stderr,
                    )
                    print(f"Найти владельца порта: netstat -ano | findstr :{PORT}", file=sys.stderr)
                raise SystemExit(1)
            logging.warning("Port %s busy, retry %d/5 in 2s", PORT, attempt + 1)
            time.sleep(2)
    logging.info("Barrymore dashboard server started at http://127.0.0.1:%s", PORT)
    if sys.stdout is not None:
        print(f"Estate dashboard: http://127.0.0.1:{PORT}")
        print(f"Server log: {LOG_DIR / 'dashboard-server.log'}")
        print("Press Ctrl+C to stop the local dashboard server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        if sys.stdout is not None:
            print("\nStopping Estate dashboard server.")
    finally:
        server.server_close()
        logging.info("Barrymore dashboard server stopped")


if __name__ == "__main__":
    main()
