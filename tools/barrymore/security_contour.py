#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Защищённый контур: изоляция локального сервера и ручные пассивные
проверки внешних ресурсов (ADR-003/ADR-004).

Свойства:
- только stdlib;
- isolation_status() — read-only самопроверка: сервер привязан к loopback,
  внешний IP:порт не отвечает;
- passive_check() — один исходящий GET / на цель из allowlist-файла
  tools/barrymore/security-targets.json: TLS-сертификат, security-заголовки,
  цепочка редиректов (только внутри allowlist), флаги cookies. Без сканирования
  портов и активных проб;
- analyze_with_llm() — заключение по фактам через локальный шлюз FreeLLMAPI
  (ключ читается из Workspace/.env и не выводится), вызов фиксируется в общем
  журнале AI-Usage (purpose="Security contour review");
- audit_event() — журнал запусков в %LOCALAPPDATA%/Platform/Security-Contour.

Каждая проверка запускается только вручную — кнопкой во вкладке
«Защищённый контур» консоли AI Sandbox.
"""

import http.client
import json
import os
import re
import socket
import ssl
import sys
import tempfile
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from ai_usage import record_request

ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT / "Workspace" / ".env"
TARGETS_PATH = ROOT / "tools" / "barrymore" / "security-targets.json"
DATA_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Platform" / "Security-Contour"
AUDIT_PATH = DATA_DIR / "audit.json"

USER_AGENT = "Platform-eVo-Security-Contour/1.0 (passive check)"
HTTP_TIMEOUT_SEC = 10
MAX_REDIRECTS = 5
LLM_TIMEOUT_SEC = 90
MAX_EVENTS = 1000
LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")
HOST_PATTERN = re.compile(
    r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?"
    r"(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+"
    r"(:[0-9]{1,5})?$"
)
SECURITY_HEADERS = (
    "strict-transport-security",
    "content-security-policy",
    "x-content-type-options",
    "x-frame-options",
    "referrer-policy",
    "permissions-policy",
)

SECURITY_SYSTEM_PROMPT = (
    "Ты — аналитик безопасности «Защищённого контура» Platform eVo. Тебе переданы "
    "пассивно собранные факты об одном внешнем ресурсе: TLS-сертификат, "
    "security-заголовки, цепочка редиректов и флаги cookies. Правила: используй "
    "только переданные факты; ничего не выдумывай и не приписывай ресурсу "
    "проверки, которых не проводилось; отделяй «неизвестно» от «отсутствует». "
    "Пиши по-русски, кратко и по делу. Ответ дай СТРОГО в JSON: "
    '{"summary": "краткое заключение о поверхности атаки", '
    '"findings": [{"severity": "high|medium|low|info", "title": "короткое название", '
    '"detail": "что видно в фактах и почему это важно"}], '
    '"nextStep": "конкретный следующий шаг владельца"}'
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_env(path: Path) -> dict:
    env = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = re.match(r'(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"?([^"\r\n]*)"?\s*$', line)
            if match:
                env[match.group(1)] = match.group(2)
    return env


def _validate_entry(entry) -> dict:
    """Валидирует одну цель allowlist и возвращает её нормализованную копию."""
    if not isinstance(entry, dict) or not isinstance(entry.get("host"), str):
        raise ValueError("Каждая цель — объект с полем host.")
    host = entry["host"].strip().lower()
    if not HOST_PATTERN.fullmatch(host):
        raise ValueError(f"Некорректный host: {entry.get('host')!r}. Ожидается домен или IP, можно с портом (example.com:8443).")
    if ":" in host and not 1 <= int(host.rsplit(":", 1)[1]) <= 65535:
        raise ValueError(f"Порт вне диапазона 1–65535: {host}")
    scheme = entry.get("scheme", "https")
    if scheme not in ("http", "https"):
        raise ValueError(f"Неверный scheme для {host}: допускаются http/https.")
    return {"host": host, "scheme": scheme, "note": str(entry.get("note", "")).strip()[:120]}


def _read_targets_file() -> dict:
    if not TARGETS_PATH.exists():
        return {"schema_version": 1, "llm_analysis": True, "targets": []}
    data = json.loads(TARGETS_PATH.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("targets"), list):
        raise ValueError("Неверный формат security-targets.json: ожидался schema_version 1 и список targets.")
    return data


def _write_targets_file(data: dict) -> None:
    TARGETS_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".targets-", suffix=".tmp", dir=TARGETS_PATH.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temp_name, TARGETS_PATH)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def add_target(payload: dict) -> list:
    """Узкая запись: добавляет одну валидированную цель в allowlist (кнопка «Добавить цель»)."""
    entry = _validate_entry(payload)
    data = _read_targets_file()
    for existing in data["targets"]:
        if isinstance(existing, dict) and existing.get("host") == entry["host"] and existing.get("scheme") == entry["scheme"]:
            raise ValueError(f"Цель {entry['host']} ({entry['scheme']}) уже в списке.")
    if len(data["targets"]) >= 100:
        raise ValueError("Достигнут лимит в 100 целей — удалите лишние из security-targets.json.")
    data["targets"].append(entry)
    _write_targets_file(data)
    audit_event("target-added", {"host": entry["host"], "scheme": entry["scheme"]})
    return data["targets"]


def load_config() -> dict:
    """Читает allowlist. Пополняется кнопкой «Добавить цель» или правкой файла; пустой список — ничего не разрешено."""
    data = _read_targets_file()
    llm_analysis = data.get("llm_analysis", True)
    if not isinstance(llm_analysis, bool):
        raise ValueError("llm_analysis должен быть true/false.")
    return {"targets": [_validate_entry(entry) for entry in data["targets"]], "llm_analysis": llm_analysis}


def _find_target(host: str, config: dict):
    normalized = host.strip().lower()
    for entry in config["targets"]:
        if entry["host"] == normalized:
            return entry
    return None


@contextmanager
def _audit_lock():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with (DATA_DIR / ".audit.lock").open("a+b") as lock_file:
        if os.name == "nt":
            import msvcrt

            lock_file.seek(0, os.SEEK_END)
            if lock_file.tell() == 0:
                lock_file.write(b"\0")
                lock_file.flush()
            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UNLCK)


def _read_audit() -> dict:
    if not AUDIT_PATH.exists():
        return {"schema_version": 1, "events": []}
    data = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("events"), list):
        raise ValueError("Unsupported security contour audit format.")
    return data


def _write_audit(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".audit-", suffix=".tmp", dir=DATA_DIR)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temp_name, AUDIT_PATH)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def audit_event(event_type: str, detail: dict) -> dict:
    event = {
        "id": f"sec-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}",
        "recorded_at": _now(),
        "event_type": event_type,
    }
    for key, value in detail.items():
        if isinstance(value, str):
            value = value[:120]
        event[key] = value
    with _audit_lock():
        data = _read_audit()
        data["events"].append(event)
        data["events"] = data["events"][-MAX_EVENTS:]
        _write_audit(data)
    return event


def audit_summary() -> dict:
    with _audit_lock():
        data = _read_audit()
    events = data["events"]
    return {"path": str(AUDIT_PATH), "event_count": len(events), "last": events[-1] if events else None}


def _external_interface_ip() -> str | None:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect(("8.8.8.8", 80))  # только выбор маршрута, пакеты не отправляются
            return sock.getsockname()[0]
        finally:
            sock.close()
    except OSError:
        return None


def isolation_status(server_address, probe_external: bool = True) -> dict:
    """Изоляция контура: привязка сервера к loopback + живая проба внешнего IP."""
    bind_host, bind_port = server_address[0], server_address[1]
    status = {
        "bind_host": bind_host,
        "bind_port": bind_port,
        "loopback_only": bind_host in LOOPBACK_HOSTS,
        "external_probe": None,
        "checked_at": _now(),
    }
    if probe_external:
        address = _external_interface_ip()
        if not address or address in LOOPBACK_HOSTS:
            status["external_probe"] = {
                "result": "unknown",
                "reason": "Внешний сетевой интерфейс не определён.",
            }
        else:
            try:
                probe = socket.create_connection((address, bind_port), timeout=1)
                probe.close()
                status["external_probe"] = {
                    "result": "open",
                    "address": f"{address}:{bind_port}",
                    "reason": "Внешний интерфейс отвечает — проверьте привязку сервера.",
                }
            except OSError:
                status["external_probe"] = {"result": "blocked", "address": f"{address}:{bind_port}"}
    return status


def _normalize_authority(netloc: str, scheme: str) -> str:
    netloc = (netloc or "").strip().lower()
    if "@" in netloc:
        netloc = netloc.rsplit("@", 1)[1]
    default_port = "443" if scheme == "https" else "80"
    host, sep, port = netloc.partition(":")
    if sep and port == default_port:
        return host
    return netloc


def _rdn_attr(rdns, attr: str):
    for rdn in rdns or ():
        for key, value in rdn:
            if key == attr:
                return value
    return None


def _tls_facts(connection) -> dict | None:
    sock = getattr(connection, "sock", None)
    if not isinstance(sock, ssl.SSLSocket):
        return None
    try:
        cert = sock.getpeercert() or {}
    except (OSError, ValueError):
        cert = {}
    cipher = sock.cipher()
    not_after = cert.get("notAfter")
    days_left = None
    if not_after:
        try:
            days_left = round((ssl.cert_time_to_seconds(not_after) - time.time()) / 86400)
        except ValueError:
            days_left = None
    return {
        "version": sock.version(),
        "cipher": cipher[0] if cipher else None,
        "issuer_cn": _rdn_attr(cert.get("issuer"), "commonName"),
        "subject_cn": _rdn_attr(cert.get("subject"), "commonName"),
        "not_after": not_after,
        "days_left": days_left,
    }


def _open_connection(name: str, port: int, scheme: str):
    if scheme == "https":
        context = ssl.create_default_context()
        return http.client.HTTPSConnection(name, port, timeout=HTTP_TIMEOUT_SEC, context=context)
    return http.client.HTTPConnection(name, port, timeout=HTTP_TIMEOUT_SEC)


def _analyze_headers(headers) -> dict:
    lower = {str(name).lower(): str(value) for name, value in headers}
    present = []
    values = {}
    for name in SECURITY_HEADERS:
        value = lower.get(name, "").strip()
        if value:
            present.append(name)
            values[name] = value[:200]
    return {
        "present": present,
        "missing": [name for name in SECURITY_HEADERS if name not in present],
        "values": values,
        "server_banner": lower.get("server") or None,
        "powered_by": lower.get("x-powered-by") or None,
    }


def _analyze_cookies(header_values) -> list:
    """Только имена и флаги; значения cookies не сохраняются."""
    cookies = []
    for raw in header_values:
        parts = str(raw).split(";")
        name = parts[0].split("=", 1)[0].strip()[:80]
        if not name:
            continue
        rest = ";".join(parts[1:]).lower()
        same_site = None
        for mode in ("strict", "lax", "none"):
            if f"samesite={mode}" in rest:
                same_site = mode
                break
        cookies.append(
            {
                "name": name,
                "secure": "secure" in rest,
                "http_only": "httponly" in rest,
                "same_site": same_site,
            }
        )
    return cookies


def passive_check(host: str, scheme: str = "https", allowed_authorities=None) -> dict:
    """Один пассивный GET / к цели; редиректы — только внутри allowlist."""
    result = {
        "host": host,
        "scheme": scheme,
        "started_at": _now(),
        "final_url": None,
        "status": None,
        "redirects": [],
        "headers": None,
        "cookies": [],
        "tls": None,
        "error": None,
    }
    if allowed_authorities is None:
        allowed_authorities = {_normalize_authority(host, scheme), host.lower()}
    current_url = f"{scheme}://{host}/"
    try:
        for hop in range(MAX_REDIRECTS + 1):
            parsed = urlsplit(current_url)
            connection = _open_connection(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80), parsed.scheme)
            try:
                connection.request(
                    "GET",
                    parsed.path or "/",
                    headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
                )
                response = connection.getresponse()
                result["status"] = response.status
                result["headers"] = _analyze_headers(response.getheaders())
                result["cookies"] = _analyze_cookies(response.msg.get_all("Set-Cookie") or [])
                if parsed.scheme == "https":
                    try:
                        result["tls"] = _tls_facts(connection)
                    except (OSError, ValueError):
                        result["tls"] = None
                location = response.getheader("Location")
            finally:
                connection.close()
            if 300 <= result["status"] < 400 and location:
                target = urljoin(current_url, location)
                target_parsed = urlsplit(target)
                entry = {"status": result["status"], "to": target[:300]}
                result["redirects"].append(entry)
                if target_parsed.scheme not in ("http", "https"):
                    entry["note"] = "Редирект на неподдерживаемую схему — переход остановлен."
                    break
                if _normalize_authority(target_parsed.netloc, target_parsed.scheme) not in allowed_authorities:
                    entry["note"] = "Цель редиректа вне allowlist — переход остановлен."
                    break
                if hop >= MAX_REDIRECTS:
                    result["error"] = f"Превышен лимит редиректов ({MAX_REDIRECTS})."
                    break
                current_url = target
                continue
            result["final_url"] = current_url
            break
    except (OSError, http.client.HTTPException, ValueError) as error:
        result["error"] = f"{type(error).__name__}: {error}"
    return result


def _parse_llm_reply(text: str, model: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    match = re.search(r"\{.*\}", cleaned, re.S)
    obj = None
    if match:
        try:
            candidate = json.loads(match.group(0))
            obj = candidate if isinstance(candidate, dict) else None
        except json.JSONDecodeError:
            obj = None
    if obj is None:
        return {"model": model, "summary": cleaned[:800], "findings": [], "next_step": ""}
    raw_findings = obj.get("findings")
    findings = []
    if isinstance(raw_findings, list):
        for item in raw_findings:
            if not isinstance(item, dict):
                continue
            findings.append(
                {
                    "severity": str(item.get("severity", "info")).strip()[:12] or "info",
                    "title": str(item.get("title", "")).strip()[:120],
                    "detail": str(item.get("detail", "")).strip()[:400],
                }
            )
    return {
        "model": model,
        "summary": str(obj.get("summary", "")).strip()[:800] or cleaned[:800],
        "findings": findings,
        "next_step": str(obj.get("nextStep", "")).strip()[:300],
    }


def analyze_with_llm(facts: dict) -> dict:
    """Заключение по фактам через локальный шлюз FreeLLMAPI. Ошибки не роняют проверку."""
    env = load_env(ENV_PATH)
    base = env.get("FREE_LLM_BASE_URL", "http://localhost:31415/v1").rstrip("/")
    key = env.get("FREE_LLM_API_KEY", "")
    model = env.get("FREE_LLM_MODEL", "auto")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SECURITY_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": "Пассивно собранные факты о внешнем ресурсе:\n"
                + json.dumps(facts, ensure_ascii=False, indent=2)
                + "\n\nДай заключение по правилам системы.",
            },
        ],
        "temperature": 0.2,
    }
    request = urllib.request.Request(
        base + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=LLM_TIMEOUT_SEC) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = ""
        try:
            body = error.read().decode("utf-8", "replace")[:200]
        except Exception:
            pass
        return {"error": f"LLM gateway HTTP {error.code} {body}".strip()}
    except (urllib.error.URLError, OSError, ValueError) as error:
        return {"error": f"LLM gateway недоступен: {getattr(error, 'reason', error)}"}

    text = ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    text = text.strip()
    if not text:
        return {"error": "LLM вернул пустой ответ"}
    result = _parse_llm_reply(text, str(data.get("model") or model))

    usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
    cost = data.get("cost") if isinstance(data.get("cost"), dict) else {}
    try:
        record_request("freellmapi", result["model"], usage, cost, "Security contour review", result["summary"][:240])
    except (OSError, ValueError) as error:
        print("[Security-Contour] Не удалось сохранить метаданные usage: %s" % error, file=sys.stderr)
    return result


def run_check(host: str) -> dict:
    """Ручная проверка цели: allowlist → пассивный сбор → LLM → аудит."""
    config = load_config()
    entry = _find_target(host, config)
    if entry is None:
        raise PermissionError(f"Хост {host!r} не входит в allowlist security-targets.json — проверка отклонена.")
    allowed = set()
    for item in config["targets"]:
        allowed.add(_normalize_authority(item["host"], item["scheme"]))
        allowed.add(item["host"])
    facts = passive_check(entry["host"], scheme=entry["scheme"], allowed_authorities=allowed)

    llm = None
    if config["llm_analysis"] and not facts.get("error"):
        llm = analyze_with_llm(facts)

    event = audit_event(
        "external-check",
        {
            "host": entry["host"],
            "status": facts.get("status"),
            "error": facts.get("error"),
            "redirect_count": len(facts.get("redirects") or []),
            "llm_used": bool(llm and not llm.get("error")),
            "llm_model": (llm or {}).get("model"),
            "finding_count": len((llm or {}).get("findings") or []),
        },
    )
    return {"facts": facts, "llm": llm, "audit_event_id": event["id"]}


def dashboard_status(server_address) -> dict:
    config = load_config()
    return {
        "isolation": isolation_status(server_address),
        "targets": config["targets"],
        "llm_analysis": config["llm_analysis"],
        "audit": audit_summary(),
    }
