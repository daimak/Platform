#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agent Runtime — запуск агента по паспорту с инструментами из реестра.

Этап 1-2 дорожной карты агентов (Docs/AGENTS-LANDSCAPE-2026-10-29-ZCode.md):
паспорт из Memory/Agents/<Имя>.md подставляется как системный промпт, данные
собирают только инструменты из tools/agents/registry.json (ADR-004/005).

Свойства:
- только stdlib; ключ шлюза читается из Workspace/.env и не выводится;
- LLM получает только текст источников, доступа к ОС у модели нет (ADR-004);
- «мозги»: черновик отчёта LLM проходит независимый проход верификации против
  данных инструментов; неверные и опасные утверждения помечаются явно;
- «власть в меру»: единственная запись — отчёт аудита в
  Memory/Engineering/Reports/ (инструмент report.write из реестра);
- при --no-llm или недоступном шлюзе собирает детерминированный отчёт по
  правилам проверки — выхлоп есть всегда.

Запуск:
  python tools/agents/run_agent.py --agent Holmes
  python tools/agents/run_agent.py --agent Holmes --no-llm
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = Path(__file__).resolve().parent / "registry.json"
ENV_PATH = ROOT / "Workspace" / ".env"
TASHKENT = timezone(timedelta(hours=5), "Tashkent")

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


# --- Инструменты (реестр: git.inspect, journal.read, tree.inspect) ----------

def parse_branch_tracking() -> list:
    """Каждая локальная ветка и её позиция относительно СВОЕГО upstream."""
    out = []
    for line in git("branch", "-vv").splitlines():
        m = re.match(r"^[*+]?\s*(\S+)\s+([0-9a-f]{7,})\s+(.*)$", line)
        if not m:
            continue
        name, _sha, rest = m.groups()
        tracking, ahead, behind = None, 0, 0
        tm = re.search(r"\[(origin/\S+?)(?::\s*([^\]]+))?\]", rest)
        if tm:
            tracking = tm.group(1)
            rel = tm.group(2) or ""
            am = re.search(r"ahead (\d+)", rel)
            bm = re.search(r"behind (\d+)", rel)
            ahead = int(am.group(1)) if am else 0
            behind = int(bm.group(1)) if bm else 0
        out.append({"branch": name, "tracking": tracking, "ahead": ahead, "behind": behind})
    return out


def tool_git_inspect(days: int = 7) -> dict:
    week = f"{days} days ago"
    commits = git("log", "--all", f"--since={week}", "--pretty=format:%s")
    commit_list = commits.splitlines() if commits else []
    noise = [c for c in commit_list if c.startswith("Agent host session")]
    status_sb = git("status", "-sb").splitlines()
    branch_line = status_sb[0] if status_sb else ""
    m = re.search(r"(?:ahead (\d+))?(?:, )?(?:behind (\d+))?$", branch_line)
    current = git("branch", "--show-current")
    untracked = [l[3:] for l in git("status", "--porcelain", "--untracked-files=all").splitlines() if l.startswith("??")]
    modified = [l[3:] for l in git("status", "--porcelain").splitlines() if l.startswith(" M")]
    tracking = parse_branch_tracking()
    current_sync = next((b for b in tracking if b["branch"] == current), {"branch": current, "tracking": None, "ahead": 0, "behind": 0})
    main_row = next((b for b in tracking if b["branch"] == "main"), None)
    return {
        "branch": current,
        "branchSync": current_sync,
        "branchTrackingNote": "branchSync — позиция ТЕКУЩЕЙ ветки относительно её upstream; branchTracking — каждая ветка относительно СВОЕГО upstream. Не приписывайте одной ветке отставание другой.",
        "branchTracking": tracking,
        "localMainVsItsUpstream": main_row,
        "commitsLastNDays": {"days": days, "total": len(commit_list), "agentHostNoise": len(noise)},
        "modifiedTracked": modified,
        "untracked": untracked[:30],
        "untrackedCount": len(untracked),
    }


def tool_journal_read() -> dict:
    eng = ROOT / "Memory" / "Engineering"
    data = {"logEntries": [], "logModified": None, "activeTasks": []}
    log_path = eng / "LOG.md"
    if log_path.exists():
        data["logModified"] = datetime.fromtimestamp(log_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        ids = sorted(set(re.findall(r"\bE-\d{3}\b", log_path.read_text(encoding="utf-8-sig", errors="replace"))))
        data["logEntries"] = ids
    tasks_dir = eng / "Tasks" / "Active"
    if tasks_dir.exists():
        data["activeTasks"] = sorted(p.stem for p in tasks_dir.glob("*.json"))
    return data


def tool_tree_inspect() -> dict:
    heavy = []
    for p in ROOT.rglob("*"):
        if ".git" in p.parts or "node_modules" in p.parts:
            continue
        if p.is_file() and p.suffix.lower() in {".png", ".jpg"} and p.stat().st_size > 1_000_000:
            heavy.append(str(p.relative_to(ROOT)))
        if len(heavy) > 15:
            break
    return {"heavyAssetsMB": heavy}


# --- Шлюз -------------------------------------------------------------------

def gateway_chat(registry: dict, env: dict, system_prompt: str, user_prompt: str) -> dict:
    gw = registry["gateway"]
    base = env.get(gw["base_url_env"], gw["default_base_url"]).rstrip("/")
    key = env.get(gw["key_env"], "")
    model = env.get(gw["model_env"], gw["default_model"])
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }
    req = urllib.request.Request(
        base + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=gw["timeout_sec"]) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
    return {"model": str(data.get("model") or model), "text": (text or "").strip(),
            "usage": data.get("usage") or {}}


# --- «Мозги»: независимый верификатор ---------------------------------------

VERIFIER_SYSTEM = (
    "Ты — независимый верификатор аудиторских отчётов Platform eVo. Тебе даны "
    "ИСТИНА (данные инструментов) и ЧЕРНОВИК отчёта агента. Проверь каждое "
    "фактическое утверждение черновика против истины и помечай: wrong — "
    "противоречит данным; unverified — не подтверждено данными; dangerous — "
    "рекомендация, которая может уничтожить или перезаписать чужую работу "
    "(удаление файлов, git clean/reset/force, перезапись чужих изменений). "
    "Свои факты не выдумывай. Ответ дай СТРОГО в JSON: "
    '{"verdict": "pass" или "issues", '
    '"issues": [{"claim": "утверждение", "status": "wrong|unverified|dangerous", "note": "что по данным"}], '
    '"summary": "1-2 предложения итога"}'
)


def verify_draft(registry: dict, env: dict, data: dict, draft: str) -> str:
    user_prompt = (
        "Данные инструментов (истина):\n"
        + json.dumps(data, ensure_ascii=False, indent=2)
        + "\n\nЧерновик отчёта:\n"
        + draft
    )
    res = gateway_chat(registry, env, VERIFIER_SYSTEM, user_prompt)
    cleaned = re.sub(r"^```(?:json)?|```$", "", res["text"], flags=re.M).strip()
    m = re.search(r"\{.*\}", cleaned, re.S)
    try:
        obj = json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        return res["text"]
    lines = [f"**Вердикт верификатора:** {obj.get('verdict', 'unknown')}. {obj.get('summary', '')}".strip()]
    for issue in obj.get("issues", []):
        lines.append(f"- [{issue.get('status', '?')}] {issue.get('claim', '')} — {issue.get('note', '')}")
    return "\n".join(lines)


# --- Детерминированный отчёт (без LLM) --------------------------------------

def deterministic_report(git_data: dict, journal: dict) -> str:
    findings = []
    sync = git_data.get("branchSync") or {}
    if git_data["agentHostNoise"] and git_data["commitsLastNDays"]["total"]:
        share = 100 * git_data["agentHostNoise"] // max(git_data["commitsLastNDays"]["total"], 1)
        findings.append(("P1", f"Шум истории: {git_data['agentHostNoise']} авто-коммитов агент-хоста из "
                               f"{git_data['commitsLastNDays']['total']} за {git_data['commitsLastNDays']['days']} дней ({share}%)."))
    if git_data["untrackedCount"]:
        findings.append(("P2", f"Untracked-файлов: {git_data['untrackedCount']} — по protocol-first они «не существуют»; "
                               f"кандидаты в .gitignore или коммит: {', '.join(git_data['untracked'][:5])}…"))
    if git_data["modifiedTracked"]:
        findings.append(("P2", "Незакоммиченные правки: " + ", ".join(git_data["modifiedTracked"][:5])))
    if sync.get("ahead") or sync.get("behind"):
        findings.append(("P3", f"Ветка {sync['branch']} относительно своего upstream ({sync.get('tracking')}): "
                               f"ahead {sync.get('ahead')}, behind {sync.get('behind')}."))
    main_row = git_data.get("localMainVsItsUpstream")
    if main_row and main_row.get("behind"):
        findings.append(("P3", f"Локальный main позади {main_row.get('tracking')} на {main_row['behind']} коммитов "
                               "(это позиция main, а не рабочей ветки)."))
    if journal["logModified"]:
        age = (datetime.now() - datetime.strptime(journal["logModified"][:16], "%Y-%m-%d %H:%M")).days
        if age >= 3:
            findings.append(("P3", f"Журнал LOG.md не обновлялся {age} дней (последнее касание {journal['logModified']}); "
                                   f"записи: {', '.join(journal['logEntries'][-3:])}."))
    if journal["activeTasks"]:
        findings.append(("P3", f"Открытых задач в лиджере: {len(journal['activeTasks'])}: {', '.join(journal['activeTasks'])}"))

    lines = [
        "# Отчёт Холмса (детерминированный, без LLM)",
        f"Сгенерирован: {datetime.now(TASHKENT).strftime('%Y-%m-%d %H:%M')} (Tashkent)",
        "",
        "**Вывод:** автоматическая проверка гигиены репозитория; LLM-вердикт недоступен, выводы основаны только на правилах.",
        "**Ключевые факты:**",
    ]
    if findings:
        for sev, text in findings:
            lines.append(f"- [{sev}] {text}")
    else:
        lines.append("- Аномалий по правилам проверки не обнаружено.")
    lines += [
        "**Варианты:** устранить находки по списку выше или передать LLM для аналитического вердикта (повторить без --no-llm).",
        "**Риски:** без регулярного аудита шум и дрейф контекста накапливаются незаметно.",
        "**Рекомендация:** повторить запуск с LLM; закрепить еженедельный триггер.",
        "**Что нужно от Sovereign:** санкция на фиксацию режима коммитов агент-хоста и чистку untracked.",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", default="Holmes")
    parser.add_argument("--no-llm", action="store_true")
    args = parser.parse_args()

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    agent = registry["agents"].get(args.agent)
    if not agent:
        print(f"[agents] Агент «{args.agent}» не в реестре. Доступны: {', '.join(registry['agents'])}", file=sys.stderr)
        return 1
    passport_path = ROOT / agent["passport"]
    if not passport_path.exists():
        print(f"[agents] Паспорт не найден: {agent['passport']}", file=sys.stderr)
        return 1
    passport = passport_path.read_text(encoding="utf-8-sig", errors="replace")

    tools_used = [t for t in agent["tools"] if t not in ("gateway.chat", "report.write")]
    data = {
        "git": tool_git_inspect() if "git.inspect" in tools_used else None,
        "journal": tool_journal_read() if "journal.read" in tools_used else None,
        "tree": tool_tree_inspect() if "tree.inspect" in tools_used else None,
    }
    print(f"[agents] Инструменты ({args.agent}): {', '.join(tools_used)}")

    report = None
    verification = None
    if not args.no_llm:
        system_prompt = (
            passport
            + "\n\nПравила: используй только факты из переданных данных; ничего не выдумывай; "
              "если данных недостаточно — прямо напиши «данных недостаточно» вместо догадки; "
              "не рекомендуй необратимых операций (удаление, git clean/reset/force) — только "
              "выноси их на санкцию Sovereign; пиши по-русски, сухо, как протокол инспекции.\n"
            "Ответ дай строго в каноническом формате раздела 4 паспорта: "
            "**Вывод:** / **Ключевые факты:** / **Варианты:** / **Риски:** / **Рекомендация:** / **Что нужно от Sovereign:**"
        )
        user_prompt = (
            f"Данные инструментов (read-only, снимок {datetime.now(TASHKENT).strftime('%Y-%m-%d %H:%M')}):\n"
            + json.dumps(data, ensure_ascii=False, indent=2)
            + "\n\nПроведи плановый аудит чистоты репозитория и журнала по своему мандату."
        )
        env = load_env(ENV_PATH)
        try:
            result = gateway_chat(registry, env, system_prompt, user_prompt)
            report = result["text"]
            usage = result["usage"]
            print(f"[agents] Черновик получен (model={result['model']}, tokens={usage.get('total_tokens', 'unknown')})")
            try:
                verification = verify_draft(registry, env, data, report)
                print("[agents] Верификация против данных выполнена")
            except Exception as e:
                print(f"[agents] Верификация не удалась ({e}); отчёт помечен как непроверенный", file=sys.stderr)
                verification = "**Вердикт верификатора:** недоступен (" + str(e) + ")"
        except Exception as e:
            print(f"[agents] Шлюз недоступен ({e}); детерминированный отчёт", file=sys.stderr)

    if report is None:
        report = deterministic_report(data["git"] or {}, data["journal"] or {})

    final = report
    if verification:
        final += "\n\n---\n\n## Верификация (авто, против данных инструментов)\n\n" + verification

    if "report.write" in agent["tools"]:
        reports_dir = ROOT / "Memory" / "Engineering" / "Reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        out_path = reports_dir / f"Report-{datetime.now(TASHKENT).strftime('%Y-%m-%d')}-{args.agent.lower()}-audit.md"
        out_path.write_text(final + "\n", encoding="utf-8")
        print(f"[agents] Отчёт сохранён (report.write): {out_path.relative_to(ROOT)}")

    print()
    print(final)
    return 0


if __name__ == "__main__":
    sys.exit(main())
