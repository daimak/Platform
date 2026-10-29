#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Barrymore Morning Brief Agent — автономный утренний доклад (ADR-003, read-only).

Читает CURRENT.md, Engineering/STATE.md, CHANGELOG.md, Git и журнал задач Barrymore,
добавляет к ним «мозги»: запрос к локальному LLM-шлюзу FreeLLMAPI
(http://localhost:31415/v1) в роли стюарда Баррримора. Результат — тот же
eVo/dashboard/brief.js с дополнительным полем agent.

Свойства:
- только stdlib (никаких pip-зависимостей);
- ключ FREE_LLM_API_KEY читается из Workspace/.env (в терминал не выводится);
- ADR-004: LLM получает только текст источников, никакого доступа к ОС;
- ADR-003: скрипт только читает источники и пишет ровно один файл (brief.js);
- при недоступности шлюза пишет детерминированный снимок с agent.error (дашборд
  продолжит работать).

Запуск: python tools/barrymore/morning-brief-agent.py
"""

import argparse
import json
import hashlib
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ai_usage import data_for_barrymore, record_request, settings as ai_usage_settings
from task_store import dashboard_tasks

ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT / "Workspace" / ".env"
OUT_PATH = ROOT / "eVo" / "dashboard" / "brief.js"
LLM_TIMEOUT_SEC = 90
BRIEF_PREFIX = "window.EVO_BRIEF = "
TASHKENT = timezone(timedelta(hours=5), "Tashkent")

SYSTEM_PROMPT = (
    "Ты — Баррримор, стюард персональной операционной системы Platform eVo. "
    "Владелец — Дмитрий. Ты готовишь утренний доклад (Morning Brief) строго по "
    "предоставленным источникам истины. Правила: используй только факты из "
    "источников; ничего не выдумывай; если данные устарели — прямо отметь это; "
    "пиши по-русски, спокойно и по делу, 5–9 строк; завершай конкретным "
    "следующим шагом. Ответ дай СТРОГО в JSON: "
    '{"summary": "текст доклада", "nextStep": "конкретный следующий шаг"}. '
    "Если передана секция aiUsage, сообщи только измеренные значения и явно "
    "отделяй неизвестное от нуля; не делай выводов о расходах без подтверждённых сумм."
)

AI_USAGE_SYSTEM_PROMPT = (
    "Ты — Баррримор, аналитик учёта AI Platform eVo. Суммируй только переданные "
    "снимки и агрегаты. Не подменяй unknown нулём, не выводи стоимость по токенам "
    "без тарифа. Различай подписочные кредиты и API-токены. Пиши кратко по-русски "
    "и укажи, какие сведения отсутствуют. Ответ дай строго в JSON: "
    '{"summary": "краткий обзор", "nextStep": "полезное действие или пустая строка"}'
)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def load_env(path: Path) -> dict:
    env = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = re.match(r'(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"?([^"\r\n]*)"?\s*$', line)
            if m:
                env[m.group(1)] = m.group(2)
    return env


def read(rel: str) -> str:
    p = ROOT / rel
    return p.read_text(encoding="utf-8-sig", errors="replace") if p.exists() else ""


def section(text: str, header: str):
    m = re.search(r"##\s*" + re.escape(header) + r"\s*\r?\n(.*?)(?=\r?\n##\s|\Z)", text, re.S)
    return m.group(1).strip() if m else None


def git(*args: str) -> str:
    try:
        r = subprocess.run(
            ["git", "-C", str(ROOT)] + list(args),
            capture_output=True, text=True, timeout=15,
            encoding="utf-8", errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
        )
        return r.stdout.strip()
    except Exception:
        return ""


def collect_sources() -> dict:
    current = read("Memory/Context/CURRENT.md")
    state = read("Memory/Engineering/STATE.md")
    changes = [l for l in read("CHANGELOG.md").splitlines() if re.match(r"^\d{4}-\d{2}-\d{2}", l)]
    dm = re.search(r"(?m)^\s*Date:\s*(.+?)\s*$", current)
    status_lines = git("status", "--porcelain", "--untracked-files=all").splitlines()
    runtime_paths = {
        "eVo/dashboard/brief.js",
    }
    dirty_files = 0
    for line in status_lines:
        path = line[3:].replace("\\", "/").strip()
        if path.startswith("Memory/Engineering/Tasks/") or path in runtime_paths:
            continue
        dirty_files += 1

    brief = {
        "generatedAt": datetime.now(TASHKENT).strftime("%Y-%m-%d %H:%M"),
        "sources": [
            "Memory/Context/CURRENT.md",
            "Memory/Engineering/STATE.md",
            "CHANGELOG.md",
            "git",
        ],
        "current": {
            "date": dm.group(1) if dm else None,
            "nextAction": section(current, "Next Action"),
        },
        "state": {"nextStep": section(state, "Следующий шаг")},
        "changes": changes[-5:],
        "tasks": dashboard_tasks(archive_expired=False),
        "git": {
            "branch": git("branch", "--show-current"),
            "lastCommit": git("log", "-1", "--pretty=format:%h %s"),
            "dirtyFiles": dirty_files,
        },
    }
    if ai_usage_settings()["include_in_morning_brief"]:
        brief["aiUsage"] = data_for_barrymore()
    return brief


def source_fingerprint(brief: dict) -> str:
    source_data = {key: value for key, value in brief.items() if key != "generatedAt"}
    serialized = json.dumps(source_data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def read_cached_brief() -> dict | None:
    if not OUT_PATH.exists():
        return None
    content = OUT_PATH.read_text(encoding="utf-8")
    if not content.startswith(BRIEF_PREFIX) or not content.rstrip().endswith(";"):
        return None
    try:
        cached = json.loads(content[len(BRIEF_PREFIX):].rstrip()[:-1])
    except json.JSONDecodeError:
        return None
    return cached if isinstance(cached, dict) else None


def ask_brain(
    brief: dict,
    env: dict,
    system_prompt: str = SYSTEM_PROMPT,
    purpose: str = "Morning Brief",
) -> dict:
    base = env.get("FREE_LLM_BASE_URL", "http://localhost:31415/v1").rstrip("/")
    key = env.get("FREE_LLM_API_KEY", "")
    model = env.get("FREE_LLM_MODEL", "auto")

    instruction = (
        "Составь Morning Brief по правилам системы."
        if purpose == "Morning Brief"
        else "Подготовь обзор AI-использования по правилам системы."
    )
    user_prompt = (
        "Источники истины Platform eVo (снимок):\n"
        + json.dumps(brief, ensure_ascii=False, indent=2)
        + "\n\n"
        + instruction
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
    }
    req = urllib.request.Request(
        base + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=LLM_TIMEOUT_SEC) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "replace")[:200]
        except Exception:
            pass
        raise RuntimeError("LLM gateway HTTP %s %s" % (e.code, body))
    except urllib.error.URLError as e:
        raise RuntimeError("LLM gateway unreachable: %s" % e.reason)

    text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
    text = (text or "").strip()
    if not text:
        raise RuntimeError("LLM вернул пустой ответ")

    cleaned = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    m = re.search(r"\{.*\}", cleaned, re.S)
    agent_result = None
    if m:
        try:
            obj = json.loads(m.group(0))
            agent_result = {
                "model": str(data.get("model") or model),
                "summary": str(obj.get("summary", "")).strip() or cleaned,
                "nextStep": str(obj.get("nextStep", "")).strip(),
            }
        except Exception:
            pass
    if agent_result is None:
        agent_result = {"model": str(data.get("model") or model), "summary": cleaned, "nextStep": ""}

    usage = data.get("usage")
    usage = usage if isinstance(usage, dict) else {}
    reported_cost = data.get("cost")
    if not isinstance(reported_cost, dict):
        reported_cost = usage.get("cost")
    cost = reported_cost if isinstance(reported_cost, dict) else {}
    if isinstance(reported_cost, (int, float)) and not isinstance(reported_cost, bool):
        cost = {
            "amount": reported_cost,
            "currency": data.get("currency") or usage.get("currency"),
            "source": "provider_response",
        }
    elif isinstance(cost, dict) and cost.get("amount") is not None:
        cost = {**cost, "source": cost.get("source", "provider_response")}
    try:
        record_request(
            "freellmapi",
            agent_result["model"],
            usage,
            cost,
            purpose,
            "Доклад сформирован" if purpose == "Morning Brief" else agent_result["summary"],
        )
    except (OSError, ValueError) as error:
        print("[Barrymore] Не удалось сохранить метаданные usage: %s" % error, file=sys.stderr)
    return agent_result


def review_ai_usage() -> dict:
    report = data_for_barrymore()
    result = ask_brain(
        {"aiUsage": report},
        load_env(ENV_PATH),
        system_prompt=AI_USAGE_SYSTEM_PROMPT,
        purpose="AI usage review",
    )
    return {"summary": result["summary"], "nextStep": result["nextStep"]}


def main(retry_llm_error: bool = False) -> int:
    brief = collect_sources()
    fingerprint = source_fingerprint(brief)
    cached = read_cached_brief()
    if cached and cached.get("_sourceFingerprint") == fingerprint:
        previous_agent = cached.get("agent") or {}
        if not (retry_llm_error and previous_agent.get("error")):
            print("[Barrymore] Источники не изменились; существующий доклад актуален.")
            return 0

    env = load_env(ENV_PATH)
    try:
        brief["agent"] = ask_brain(brief, env)
        print("[Barrymore] LLM доклад получен (model=%s)" % brief["agent"]["model"])
        print("[Barrymore] " + brief["agent"]["summary"][:300].replace("\n", " / "))
    except Exception as e:
        brief["agent"] = {"error": str(e)}
        print("[Barrymore] LLM недоступен (%s); записан детерминированный снимок" % e)

    brief["_sourceFingerprint"] = fingerprint
    OUT_PATH.write_text(
        BRIEF_PREFIX + json.dumps(brief, ensure_ascii=False, indent=2) + ";",
        encoding="utf-8",
    )
    print("[Barrymore] Morning Brief written: %s (%s)" % (OUT_PATH, brief["generatedAt"]))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--retry-llm-error", action="store_true")
    parser.add_argument("--ai-usage-review", action="store_true")
    args = parser.parse_args()
    if args.ai_usage_review:
        print(json.dumps(review_ai_usage(), ensure_ascii=False))
        sys.exit(0)
    sys.exit(main(retry_llm_error=args.retry_llm_error))
