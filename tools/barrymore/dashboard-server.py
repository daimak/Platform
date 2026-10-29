#!/usr/bin/env python3
"""Serve the local Estate dashboard and expose Barrymore brief refresh."""

import json
import logging
import os
import re
import subprocess
import sys
import threading
from datetime import datetime, timedelta, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from task_store import TASK_ID_PATTERN, dashboard_tasks, mark_done

ROOT = Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "eVo" / "dashboard"
AGENT = ROOT / "tools" / "barrymore" / "morning-brief-agent.py"
PORT = 8765
REFRESH_LOCK = threading.Lock()
TASK_LOCK = threading.Lock()
LOG_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Platform" / "Barrymore"
TASHKENT = timezone(timedelta(hours=5), "Tashkent")


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


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DASHBOARD), **kwargs)

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
        if self.path == "/api/tasks":
            try:
                with TASK_LOCK:
                    tasks = dashboard_tasks()
                self._send_json(200, {"tasks": tasks})
            except (OSError, ValueError, json.JSONDecodeError) as error:
                logging.exception("Task list failed")
                self._send_json(500, {"error": f"Не удалось прочитать список задач: {error}"})
            return
        super().do_GET()

    def do_POST(self) -> None:
        if not self._is_local_host():
            self._send_json(403, {"error": "Доступ разрешён только с локального компьютера."})
            return
        request_path = urlsplit(self.path).path
        if request_path != "/api/refresh-brief" and not re.fullmatch(
            r"/api/tasks/[a-z0-9][a-z0-9-]{0,63}/done",
            request_path,
        ):
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

        if self.headers.get("Content-Length", "0") != "0":
            self._send_json(400, {"error": "Endpoint не принимает тело запроса."})
            return

        if request_path != "/api/refresh-brief":
            task_id = request_path.split("/")[3]
            if not TASK_ID_PATTERN.fullmatch(task_id):
                self._send_json(400, {"error": "Некорректный идентификатор задачи."})
                return
            if not TASK_LOCK.acquire(blocking=False):
                self._send_json(409, {"error": "Список задач уже обновляется."})
                return
            try:
                task = mark_done(task_id)
                self._send_json(200, {"task": task, "tasks": dashboard_tasks()})
            except FileNotFoundError as error:
                self._send_json(404, {"error": str(error)})
            except (OSError, ValueError, json.JSONDecodeError) as error:
                logging.exception("Task update failed")
                self._send_json(500, {"error": f"Не удалось обновить задачу: {error}"})
            finally:
                TASK_LOCK.release()
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


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(LOG_DIR / "dashboard-server.log", encoding="utf-8")
    handler.setFormatter(TashkentFormatter("%(asctime)s UZT %(levelname)s %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[handler])
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), DashboardHandler)
    except OSError:
        logging.exception("Could not bind dashboard server to 127.0.0.1:%s", PORT)
        raise
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
