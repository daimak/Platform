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

from ai_usage import add_snapshot, dashboard_data, set_include_in_morning_brief
from hunter_store import create_assignment, list_assignments
from security_contour import add_target, dashboard_status, run_check
from task_store import TASK_ID_PATTERN, dashboard_tasks, mark_done

ROOT = Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "eVo" / "dashboard"
AGENT = ROOT / "tools" / "barrymore" / "morning-brief-agent.py"
PORT = 8765
REFRESH_LOCK = threading.Lock()
TASK_LOCK = threading.Lock()
HUNTER_LOCK = threading.Lock()
USAGE_LOCK = threading.Lock()
SECURITY_LOCK = threading.Lock()
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
        hunter_tasks_route = "/api/hunter/tasks"
        security_route = "/api/security/check"
        security_targets_route = "/api/security/targets"
        body_routes = {"/api/ai-usage/snapshots", "/api/ai-usage/settings"}
        bodyless_routes = {
            "/api/refresh-brief",
            "/api/ai-usage/ask-barrymore",
        }
        if request_path not in body_routes | bodyless_routes and not task_done and request_path not in (hunter_tasks_route, security_route, security_targets_route):
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
