# -*- coding: utf-8 -*-
"""Busy-лок задач Platform Evo (решение Sovereign 2026-11-06: «busy_123» доведён до ума).

Координация между агентами, работающими по одной карточке: кто взял задачу —
атомарно захватывает файл-пульс Busy/<task_id>.json и пишет туда, что делает.
Приходящий второй лейн:
  - пульс свежий (<= TTL) -> не приступает, кладёт отклик Claims/<task_id>.<кто>.json;
  - пульс протух (владелец умер) -> перехватывает лок с пометкой stolen_from.

Гарантии:
- захват атомарен (os.O_CREAT | os.O_EXCL) — гонка «глянул-занял» исключена;
- вечный лок невозможен: протухший пульс перехватывается;
- владелец виден на доске (/api/tasks прикрепляет busy через task_store).

Файлы НЕ в Active/*.json, чтобы не попадать в glob карточек. События
task.busy.* дублируются в events.jsonl (падение журнала лок не ломает).
stdlib-only (ADR-003/004).
"""
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASKS_DIR = ROOT / "Memory" / "Engineering" / "Tasks"
DEFAULT_BUSY_DIR = TASKS_DIR / "Busy"
DEFAULT_CLAIMS_DIR = DEFAULT_BUSY_DIR / "Claims"

DEFAULT_TTL_S = 600  # пульс старше 10 минут = владелец считается умершим

_SLUG_RE = re.compile(r"[^a-z0-9-]+")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _slug(name: str) -> str:
    slug = _SLUG_RE.sub("-", str(name).lower()).strip("-")[:32] or "unknown"
    return slug


def _journal(kind: str, source: str, payload: dict) -> None:
    """Дубликат события в events.jsonl; любая ошибка глушится (лок важнее журнала)."""
    try:
        if str(ROOT) not in __import__("sys").path:
            __import__("sys").path.insert(0, str(ROOT))
        from tools.lib.log_event import append_event

        append_event(kind, source, payload)
    except Exception:
        pass


def _read_busy(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _write_busy(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data["heartbeat"] = _utc_now_iso()
    # O_CREAT|O_EXCL: создастся только если файла нет — атомарный захват.
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
    except Exception:
        path.unlink(missing_ok=True)
        raise


def _age_s(busy: dict, now: float) -> float:
    try:
        parsed = datetime.fromisoformat(busy["heartbeat"].replace("Z", "+00:00"))
        return max(0.0, now - parsed.timestamp())
    except (KeyError, ValueError, TypeError):
        return float("inf")


def acquire(task_id: str, agent: str, doing: str = "", base=None, ttl_s: int = DEFAULT_TTL_S,
            claim_wanted: str | None = None) -> dict:
    """Атомарно захватить задачу. Успех: {"ok": True, "lock": {...}}.
    Занято живым владельцем: {"ok": False, "busy": {...}, "claimed": True|False}
    — отклик-файл кладётся автоматически (claim_wanted — что собирались делать).
    Протухший лок перехватывается: {"ok": True, "lock": {..., "stolen_from": ...}}.
    """
    busy_dir = Path(base) if base is not None else DEFAULT_BUSY_DIR
    claims_dir = busy_dir / "Claims"
    path = busy_dir / f"{task_id}.json"
    now = time.time()
    last_seen: dict | None = None

    for _attempt in range(3):
        try:
            lock = {
                "task_id": task_id,
                "agent": agent,
                "doing": doing,
                "started_at": _utc_now_iso(),
                "pid": os.getpid(),
            }
            if last_seen is not None:
                lock["stolen_from"] = last_seen.get("agent", "unknown")
                lock["stolen_at"] = _utc_now_iso()
            _write_busy(path, lock)
            _journal("task.busy.acquired", agent, {"id": task_id, "doing": doing,
                                                   "stolen_from": lock.get("stolen_from")})
            return {"ok": True, "lock": lock}
        except FileExistsError:
            existing = _read_busy(path)
            if existing is None:
                # битый/исчезающий файл — попробуем ещё раз
                continue
            if _age_s(existing, now) <= ttl_s:
                # живой владелец: не приступаем, кладём отклик
                claimed = claim(task_id, agent, claim_wanted or doing, base=busy_dir)
                _journal("task.busy.denied", agent, {"id": task_id,
                                                     "owner": existing.get("agent")})
                return {"ok": False, "busy": existing, "claimed": bool(claimed.get("ok"))}
            last_seen = existing
            try:
                path.unlink()  # протух — снимаем мёртвый лок, следующая попытка захватит
            except OSError:
                # Windows: файл читается другим процессом (WinError 32) — ретрай,
                # следующая итерация честно переиграет гонку (P1 ревизора)
                continue
        except OSError:
            return {"ok": False, "error": "busy-лок недоступен"}
    return {"ok": False, "error": "не удалось захватить лок за 3 попытки"}


def heartbeat(task_id: str, agent: str, doing: str | None = None, base=None) -> dict:
    """Владелец продлевает пульс (запись переписывается целиком, atomically)."""
    busy_dir = Path(base) if base is not None else DEFAULT_BUSY_DIR
    path = busy_dir / f"{task_id}.json"
    data = _read_busy(path)
    if data is None:
        return {"ok": False, "error": "лок не найден"}
    if data.get("agent") != agent:
        return {"ok": False, "error": f"лок держит {data.get('agent')}"}
    if doing is not None:
        data["doing"] = doing
    data["heartbeat"] = _utc_now_iso()  # до записи: пульс на диске обязан обновиться (P1 ревизора)
    tmp = path.with_suffix(".hb.tmp")
    try:
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, path)  # replace перезапишет существующий файл
        return {"ok": True, "lock": data}
    except OSError as error:
        return {"ok": False, "error": str(error)}


def release(task_id: str, agent: str, base=None) -> dict:
    """Владелец освобождает задачу."""
    busy_dir = Path(base) if base is not None else DEFAULT_BUSY_DIR
    path = busy_dir / f"{task_id}.json"
    data = _read_busy(path)
    if data is None:
        return {"ok": False, "error": "лок не найден"}
    if data.get("agent") != agent:
        return {"ok": False, "error": f"лок держит {data.get('agent')}"}
    try:
        path.unlink()
    except FileNotFoundError:
        return {"ok": False, "error": "лок не найден"}
    _journal("task.busy.released", agent, {"id": task_id})
    return {"ok": True}


def claim(task_id: str, agent: str, wanted: str, base=None) -> dict:
    """Отклик проигравшего гонку: кто, когда и что хотел делать с задачей."""
    claims_dir = (Path(base) if base is not None else DEFAULT_BUSY_DIR) / "Claims"
    path = claims_dir / f"{task_id}.{_slug(agent)}.json"
    record = {"task_id": task_id, "agent": agent, "wanted": wanted, "at": _utc_now_iso()}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        _journal("task.busy.claim", agent, {"id": task_id, "wanted": wanted})
        return {"ok": True, "claim": record}
    except OSError as error:
        return {"ok": False, "error": str(error)}


def claims(task_id: str, base=None) -> list:
    """Отклики по задаче (для исполнителя: «тут ещё хотели поработать»)."""
    claims_dir = (Path(base) if base is not None else DEFAULT_BUSY_DIR) / "Claims"
    if not claims_dir.is_dir():
        return []
    out = []
    for path in sorted(claims_dir.glob(f"{task_id}.*.json")):
        try:
            out.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return out


def status(task_id: str, base=None, ttl_s: int = DEFAULT_TTL_S) -> dict | None:
    """Текущий лок задачи (или None). Протухший помечается "stale": True."""
    busy_dir = Path(base) if base is not None else DEFAULT_BUSY_DIR
    data = _read_busy(busy_dir / f"{task_id}.json")
    if data is None:
        return None
    if _age_s(data, time.time()) > ttl_s:
        data = dict(data, stale=True)
    return data


def status_all(base=None) -> dict:
    """{task_id: busy} по всем захватам — для прикрепления к /api/tasks."""
    busy_dir = Path(base) if base is not None else DEFAULT_BUSY_DIR
    if not busy_dir.is_dir():
        return {}
    out = {}
    for path in busy_dir.glob("*.json"):
        data = _read_busy(path)
        if data and data.get("task_id"):
            out[data["task_id"]] = data
    return out
