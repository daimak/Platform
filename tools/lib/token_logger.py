import json
import os
import time
import uuid
import sys
from datetime import datetime, timezone
from pathlib import Path

# Константы
LOG_DIR = Path("Workspace/analytics/token-spend")
LEDGER = LOG_DIR / "ledger.jsonl"
LOCK_FILE = LOG_DIR / "ledger.jsonl.lock"
LOCK_TTL = 30  # секунд

def _get_utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def _acquire_lock():
    """Атомарный захват блокировки с защитой от 'зависания'."""
    my_info = json.dumps({"pid": os.getpid(), "ts": time.time()})
    
    for _ in range(50):  # 5 секунд суммарно
        try:
            # Пытаемся создать файл атомарно
            fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, 'w') as f:
                f.write(my_info)
            return True
        except FileExistsError:
            # Проверяем на протухание
            try:
                with open(LOCK_FILE, 'r') as f:
                    data = json.load(f)
                    if time.time() - data.get("ts", 0) > LOCK_TTL:
                        # Замок протух. Пытаемся удалить его.
                        # На Windows файл может быть занят, поэтому игнорируем ошибки.
                        try:
                            os.remove(LOCK_FILE)
                        except OSError:
                            pass
            except (json.JSONDecodeError, OSError, ValueError):
                # Если файл битый или недоступен - тоже пробуем снести
                try:
                    os.remove(LOCK_FILE)
                except OSError:
                    pass
        time.sleep(0.1)
    return False

def _release_lock():
    try:
        if LOCK_FILE.exists():
            # Простая очистка. В MVP считаем, что удаление своего замка безопасно.
            os.remove(LOCK_FILE)
    except OSError:
        pass

def log_usage(agent_id, session_id, task_id, provider, requested_model, actual_model, attempt, usage_data, source="PlatformAgent"):
    """Логирует факт запроса в ledger.jsonl."""
    try:
        raw = usage_data if usage_data else {}
        
        # Нормализация данных (не дублируем cache_read в total)
        # В форматах Anthropic/OpenAI input_tokens уже включает в себя все входящие.
        it = raw.get("input_tokens")
        ot = raw.get("output_tokens")
        cr = raw.get("cache_read_input_tokens")
        
        # Если API не вернуло конкретные поля, total_tokens вычисляем только при наличии базы
        total = None
        if it is not None and ot is not None:
            total = it + ot

        entry = {
            "request_id": str(uuid.uuid4()),
            "timestamp": _get_utc_now(),
            "source": source,
            "agent_id": agent_id,
            "task_id": task_id,
            "session_id": session_id,
            "provider": provider,
            "requested_model": requested_model,
            "actual_model": actual_model,
            "attempt": attempt,
            "usage_status": "success" if usage_data else "no_usage",
            "input_tokens": it,
            "output_tokens": ot,
            "cache_read_tokens": cr,
            "total_tokens": total,
            "raw_usage": raw
        }

        if not LOG_DIR.exists():
            LOG_DIR.mkdir(parents=True, exist_ok=True)

        if _acquire_lock():
            try:
                with open(LEDGER, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                return True
            finally:
                _release_lock()
        else:
            print(f"[token_logger] WARNING: Lock timeout for {agent_id}. Record lost.", file=sys.stderr)
            return False
    except Exception as e:
        # Fail-safe: не роняем агента при ошибке логирования
        print(f"[token_logger] ERROR: {str(e)}", file=sys.stderr)
        return False
