#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Barrymore Morning Brief Agent — автономный утренний доклад (ADR-003, read-only).

Читает те же источники истины, что и morning-brief.ps1 (CURRENT.md, Engineering/STATE.md,
CHANGELOG.md, git), добавляет к ним «мозги»: запрос к локальному LLM-шлюзу FreeLLMAPI
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

import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT / "Workspace" / ".env"
OUT_PATH = ROOT / "eVo" / "dashboard" / "brief.js"
LLM_TIMEOUT_SEC = 90

SYSTEM_PROMPT = (
    "Ты — Баррримор, стюард персональной операционной системы Platform eVo. "
    "Владелец — Дмитрий. Ты готовишь утренний доклад (Morning Brief) строго по "
    "предоставленным источникам истины. Правила: используй только факты из "
    "источников; ничего не выдумывай; если данные устарели — прямо отметь это; "
    "пиши по-русски, спокойно и по делу, 5–9 строк; завершай конкретным "
    "следующим шагом. Ответ дай СТРОГО в JSON: "
    '{"summary": "текст доклада", "nextStep": "конкретный следующий шаг"}'
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
        )
        return r.stdout.strip()
    except Exception:
        return ""


def collect_sources() -> dict:
    current = read("Memory/Context/CURRENT.md")
    state = read("Memory/Engineering/STATE.md")
    changes = [l for l in read("CHANGELOG.md").splitlines() if re.match(r"^\d{4}-\d{2}-\d{2}", l)]
    dm = re.search(r"(?m)^\s*Date:\s*(.+?)\s*$", current)
    return {
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
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
        "git": {
            "branch": git("branch", "--show-current"),
            "lastCommit": git("log", "-1", "--pretty=format:%h %s"),
            "dirtyFiles": len([l for l in git("status", "--porcelain").splitlines() if l.strip()]),
        },
    }


def ask_brain(brief: dict, env: dict) -> dict:
    base = env.get("FREE_LLM_BASE_URL", "http://localhost:31415/v1").rstrip("/")
    key = env.get("FREE_LLM_API_KEY", "")
    model = env.get("FREE_LLM_MODEL", "auto")

    user_prompt = (
        "Источники истины Platform eVo (снимок):\n"
        + json.dumps(brief, ensure_ascii=False, indent=2)
        + "\n\nСоставь Morning Brief по правилам системы."
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
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
    if m:
        try:
            obj = json.loads(m.group(0))
            return {
                "model": model,
                "summary": str(obj.get("summary", "")).strip() or cleaned,
                "nextStep": str(obj.get("nextStep", "")).strip(),
            }
        except Exception:
            pass
    return {"model": model, "summary": cleaned, "nextStep": ""}


def main() -> int:
    brief = collect_sources()
    env = load_env(ENV_PATH)
    try:
        brief["agent"] = ask_brain(brief, env)
        print("[Barrymore] LLM доклад получен (model=%s)" % brief["agent"]["model"])
        print("[Barrymore] " + brief["agent"]["summary"][:300].replace("\n", " / "))
    except Exception as e:
        brief["agent"] = {"error": str(e)}
        print("[Barrymore] LLM недоступен (%s); записан детерминированный снимок" % e)

    OUT_PATH.write_text(
        "window.EVO_BRIEF = " + json.dumps(brief, ensure_ascii=False, indent=2) + ";",
        encoding="utf-8",
    )
    print("[Barrymore] Morning Brief written: %s (%s)" % (OUT_PATH, brief["generatedAt"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
