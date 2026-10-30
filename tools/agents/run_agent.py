#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agent Runtime — запуск агента по паспорту с инструментами из реестра.

Замкнутый цикл Холмса (Этап 2 дорожной карты, Docs/AGENTS-LANDSCAPE-2026-10-29-ZCode.md):
каждый прогон вычисляет находки со стабильными ID, сравнивает их с
машиночитаемым блоком прошлого отчёта (new / persisting / resolved), создаёт
задачи в лиджере Memory/Engineering/Tasks/Active (create-if-missing, формат
Tasks/README.md) и пишет отчёт с новым блоком состояния — так следующий прогон
видит последствия предыдущего.

Свойства:
- только stdlib; ключ шлюза читается из Workspace/.env и не выводится;
- LLM получает только текст источников, доступа к ОС у модели нет (ADR-004);
- «мозги»: черновик отчёта проходит независимую верификацию против данных;
- «власть в меру»: ровно две записи — отчёт в Memory/Engineering/Reports/ и
  задачи holmes-* в лиджере (existing tasks не трогаются, Mark Done — за
  Sovereign через дашборд);
- при --no-llm или недоступном шлюзе цикл всё равно работает детерминированно.

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
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = Path(__file__).resolve().parent / "registry.json"
ENV_PATH = ROOT / "Workspace" / ".env"
TASHKENT = timezone(timedelta(hours=5), "Tashkent")

sys.path.insert(0, str(ROOT / "tools" / "barrymore"))
try:
    import task_store  # формат и каталоги лиджера Tasks/README.md
except Exception:
    task_store = None

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Находки со стабильными ID: сравнение прогонов и задачи в лиджере.
FINDING_TITLES = {
    "host-noise": "Холмс: шум авто-коммитов агент-хоста в истории",
    "untracked-files": "Холмс: разобрать untracked-файлы (коммит или .gitignore)",
    "uncommitted-edits": "Холмс: незакоммиченные правки в рабочем дереве",
    "journal-stale": "Холмс: журнал LOG.md давно не обновлялся",
    "branch-drift": "Холмс: рабочая ветка разошлась с upstream",
    "main-behind": "Холмс: локальный main позади origin/main",
}
TASKABLE_SEVERITIES = {"P1", "P2"}
# Файлы, создаваемые самими агентами Platform (не считаются «незакоммиченной
# правкой», иначе Холмс триггерит сам себя):
GENERATED_PATHS = ("eVo/dashboard/brief.js",)
GENERATED_PREFIXES = ("Memory/Engineering/Reports/",)


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


# --- Инструменты (реестр: git.inspect, journal.read, tree.inspect, reports.inspect)

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


def tool_reports_inspect() -> dict:
    """Прошлый отчёт Холмса и его машиночитаемый блок находок."""
    data = {"previousReportPath": None, "previousFindings": None}
    reports_dir = ROOT / "Memory" / "Engineering" / "Reports"
    if not reports_dir.exists():
        return data
    reports = sorted(reports_dir.glob("Report-*-holmes-audit.md"))
    if not reports:
        return data
    latest = reports[-1]
    data["previousReportPath"] = str(latest.relative_to(ROOT))
    text = latest.read_text(encoding="utf-8-sig", errors="replace")
    blocks = re.findall(r"```json\s*(\{.*?\})\s*```", text, re.S)
    if blocks:
        try:
            parsed = json.loads(blocks[-1])
            if isinstance(parsed, dict):
                data["previousFindings"] = parsed
        except json.JSONDecodeError:
            pass
    return data


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


# --- Цикл: находки → сравнение → лиджер -------------------------------------

def compute_findings(git_data: dict, journal: dict) -> list:
    """Детерминированные находки со стабильными ID (сравнимы между прогонами)."""
    findings = []
    total = git_data.get("commitsLastNDays", {}).get("total", 0)
    noise = git_data.get("commitsLastNDays", {}).get("agentHostNoise", 0)
    if total and noise and 100 * noise // max(total, 1) >= 30:
        findings.append({
            "id": "host-noise", "severity": "P1",
            "detail": f"Шум истории: {noise} авто-коммитов агент-хоста из {total} за 7 дней "
                      f"({100 * noise // total}%).",
        })
    untracked = git_data.get("untracked") or []
    if untracked:
        findings.append({
            "id": "untracked-files", "severity": "P2",
            "detail": f"Untracked-файлов: {git_data['untrackedCount']}: {', '.join(untracked[:5])}"
                      + ("…" if git_data["untrackedCount"] > 5 else ""),
        })
    own_writes = [p for p in git_data.get("modifiedTracked") or []
                  if p not in GENERATED_PATHS and not p.startswith(GENERATED_PREFIXES)]
    if own_writes:
        findings.append({
            "id": "uncommitted-edits", "severity": "P2",
            "detail": "Незакоммиченные правки: " + ", ".join(own_writes[:5]),
        })
    sync = git_data.get("branchSync") or {}
    if sync.get("ahead") or sync.get("behind"):
        findings.append({
            "id": "branch-drift", "severity": "P3",
            "detail": f"Ветка {sync['branch']} относительно {sync.get('tracking')}: "
                      f"ahead {sync.get('ahead')}, behind {sync.get('behind')}.",
        })
    main_row = git_data.get("localMainVsItsUpstream")
    if main_row and main_row.get("behind"):
        findings.append({
            "id": "main-behind", "severity": "P3",
            "detail": f"Локальный main позади {main_row.get('tracking')} на {main_row['behind']} коммитов "
                      "(позиция main, не рабочей ветки).",
        })
    if journal.get("logModified"):
        try:
            last = datetime.strptime(journal["logModified"][:16], "%Y-%m-%d %H:%M")
            age = (datetime.now() - last).days
            if age >= 3:
                findings.append({
                    "id": "journal-stale", "severity": "P3",
                    "detail": f"Журнал LOG.md не обновлялся {age} дней (последнее касание {journal['logModified']}).",
                })
        except ValueError:
            pass
    return findings


def compare_findings(findings: list, prev_block: dict) -> tuple:
    prev_by_id = {f["id"]: f for f in (prev_block or {}).get("findings", [])
                  if isinstance(f, dict) and "id" in f}
    cur_ids = {f["id"] for f in findings}
    statuses = {f["id"]: ("persisting" if f["id"] in prev_by_id else "new") for f in findings}
    resolved = [fid for fid in prev_by_id if fid not in cur_ids]
    return prev_by_id, statuses, resolved


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=f".{path.stem}.", suffix=".tmp", delete=False,
        ) as fh:
            tmp = Path(fh.name)
            json.dump(payload, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        os.replace(tmp, path)
    finally:
        if tmp and tmp.exists():
            tmp.unlink()


def ledger_ensure_task(finding: dict) -> str:
    """Create-if-missing задача holmes-<id> в Tasks/Active; существующие не трогает."""
    if task_store is None:
        return "unavailable"
    base_id = f"holmes-{finding['id']}"
    if not task_store.TASK_ID_PATTERN.fullmatch(base_id):
        return "invalid-id"
    if (task_store.ACTIVE_DIR / f"{base_id}.json").exists():
        return "exists"
    task_id = None
    for candidate in [base_id] + [f"{base_id}-{n}" for n in range(2, 10)]:
        if any(task_store.ARCHIVE_DIR.rglob(f"{candidate}.json")):
            continue
        task_id = candidate
        break
    if task_id is None:
        return "no-free-id"
    path = task_store.ACTIVE_DIR / f"{task_id}.json"
    if path.exists():
        return "exists"
    created = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    task = {
        "id": task_id,
        "title": FINDING_TITLES.get(finding["id"], f"Холмс: находка {finding['id']}"),
        "source": "Holmes",
        "priority": "urgent" if finding["severity"] == "P1" else "regular",
        "status": "active",
        "createdAt": created,
        "history": [{
            "status": "active",
            "at": created,
            "by": "Holmes",
            "note": finding["detail"][:200],
        }],
    }
    _atomic_write_json(path, task)
    return f"created:{task_id}"


def run_ledger_cycle(findings: list, statuses: dict) -> list:
    """По находкам P1/P2 (new/persisting) обеспечить задачи в лиджере."""
    actions = []
    for f in findings:
        if f["severity"] in TASKABLE_SEVERITIES and statuses.get(f["id"]) in ("new", "persisting"):
            outcome = ledger_ensure_task(f)
            actions.append({"finding": f["id"], "outcome": outcome})
    return actions


def followup_lines(findings: list, statuses: dict, resolved: list, prev_by_id: dict, has_prev: bool) -> list:
    lines = ["**Последствия предыдущего аудита:**"]
    if not has_prev:
        lines.append("- Первый прогон с механизмом последствий — сравнивать не с чем.")
        return lines
    fixed = [f"- исправлено: {fid} — {prev_by_id[fid].get('detail', '')}" for fid in resolved]
    persisting = [f"- остаётся: {f['id']} [{f['severity']}] — {f['detail']}" for f in findings if statuses[f["id"]] == "persisting"]
    new = [f"- новое: {f['id']} [{f['severity']}] — {f['detail']}" for f in findings if statuses[f["id"]] == "new"]
    lines += fixed + persisting + new
    if not (fixed or persisting or new):
        lines.append("- Изменений с прошлого прогона не зафиксировано.")
    return lines


def deterministic_report(findings: list, statuses: dict, resolved: list, prev_by_id: dict,
                         has_prev: bool, ledger_actions: list) -> str:
    now_str = datetime.now(TASHKENT).strftime("%Y-%m-%d %H:%M")
    lines = [
        "# Отчёт Холмса (детерминированный, без LLM)",
        f"Сгенерирован: {now_str} (Tashkent)",
        "",
        "**Вывод:** автоматическая проверка гигиены репозитория; LLM-вердикт недоступен, выводы основаны только на правилах.",
        "**Ключевые факты:**",
    ]
    if findings:
        lines += [f"- [{f['severity']}][{statuses[f['id']]}] {f['detail']}" for f in findings]
    else:
        lines.append("- Аномалий по правилам проверки не обнаружено.")
    lines += followup_lines(findings, statuses, resolved, prev_by_id, has_prev)
    if ledger_actions:
        lines.append("**Лиджер:** " + "; ".join(f"{a['finding']} → {a['outcome']}" for a in ledger_actions))
    lines += [
        "**Варианты:** устранить находки по списку или повторить с LLM для аналитического вердикта.",
        "**Риски:** без регулярного аудита шум и дрейф контекста накапливаются незаметно.",
        "**Рекомендация:** повторить запуск с LLM; закрывать задачи в дашборде по факту исправления.",
        "**Что нужно от Sovereign:** санкция на решение находок из списка.",
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

    tools_used = [t for t in agent["tools"] if t not in ("gateway.chat", "report.write", "ledger.write")]
    data = {
        "git": tool_git_inspect() if "git.inspect" in tools_used else None,
        "journal": tool_journal_read() if "journal.read" in tools_used else None,
        "tree": tool_tree_inspect() if "tree.inspect" in tools_used else None,
        "previousReport": tool_reports_inspect() if "reports.inspect" in tools_used else {"previousReportPath": None, "previousFindings": None},
    }
    print(f"[agents] Инструменты ({args.agent}): {', '.join(tools_used)}")

    # Цикл последствий: находки → сравнение → лиджер.
    findings = compute_findings(data["git"] or {}, data["journal"] or {})
    prev_block = data["previousReport"].get("previousFindings")
    has_prev = prev_block is not None
    prev_by_id, statuses, resolved = compare_findings(findings, prev_block)
    ledger_actions = run_ledger_cycle(findings, statuses) if "ledger.write" in agent["tools"] else []
    created = [a["outcome"].split(":", 1)[1] for a in ledger_actions if a["outcome"].startswith("created:")]
    print(f"[agents] Цикл: new={sum(1 for s in statuses.values() if s == 'new')} "
          f"persisting={sum(1 for s in statuses.values() if s == 'persisting')} "
          f"resolved={len(resolved)}; задач создано: {len(created)}"
          + (f" ({', '.join(created)})" if created else ""))

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
            "**Вывод:** / **Ключевые факты:** / **Варианты:** / **Риски:** / **Рекомендация:** / "
            "**Что нужно от Sovereign:** — и обязательно добавь раздел "
            "**Последствия предыдущего аудита:** о том, что исправлено/остаётся/новое с прошлого прогона "
            "(данные в блоке followup; если previousFindings пуст — «первый прогон, сравнивать не с чем»)."
        )
        followup_ctx = {
            "previousReport": data["previousReport"].get("previousReportPath"),
            "previousFindings": (prev_block or {}).get("findings"),
            "currentStatuses": [{"id": f["id"], "severity": f["severity"], "status": statuses[f["id"]]} for f in findings],
            "resolved": resolved,
            "ledgerActions": ledger_actions,
        }
        user_prompt = (
            f"Данные инструментов (read-only, снимок {datetime.now(TASHKENT).strftime('%Y-%m-%d %H:%M')}):\n"
            + json.dumps(data, ensure_ascii=False, indent=2)
            + "\n\nfollowup (сравнение с прошлым аудитом, посчитано рантаймом):\n"
            + json.dumps(followup_ctx, ensure_ascii=False, indent=2)
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
        report = deterministic_report(findings, statuses, resolved, prev_by_id, has_prev, ledger_actions)

    if verification:
        report += "\n\n---\n\n## Верификация (авто, против данных инструментов)\n\n" + verification

    # Машиночитаемый блок состояния — источник сравнения для следующего прогона.
    state_findings = [{**f, "status": statuses[f["id"]]} for f in findings]
    state_findings += [{
        "id": fid, "severity": prev_by_id[fid].get("severity", "P3"),
        "detail": prev_by_id[fid].get("detail", ""), "status": "resolved",
    } for fid in resolved]
    state = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "findings": state_findings,
        "ledger": ledger_actions,
    }
    report += "\n\n---\n\n```json\n" + json.dumps(state, ensure_ascii=False, indent=2) + "\n```"

    if "report.write" in agent["tools"]:
        reports_dir = ROOT / "Memory" / "Engineering" / "Reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        out_path = reports_dir / f"Report-{datetime.now(TASHKENT).strftime('%Y-%m-%d')}-{args.agent.lower()}-audit.md"
        out_path.write_text(report + "\n", encoding="utf-8")
        print(f"[agents] Отчёт сохранён (report.write): {out_path.relative_to(ROOT)}")

    print()
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
