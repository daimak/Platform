#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agent Runtime — запуск агента по паспорту с инструментами из реестра.

Замкнутый цикл аудита (Холмс, Ватсон, Risk scan — Этап 2 дорожной карты,
Docs/AGENTS-LANDSCAPE-2026-10-29-ZCode.md): каждый прогон вычисляет находки
со стабильными ID (набор правил задаётся полем findings_kind агента в реестре),
сравнивает их с машиночитаемым блоком прошлого отчёта (new / persisting /
resolved) и пишет отчёт с новым блоком состояния. Инициативы (P1/P2) Sovereign
отмечает галочками в модалке Холмса на дашборде и отправляет на реализацию —
задачи в лиджере создаёт dashboard-server (/api/holmes/implement), только по санкции.

Свойства:
- только stdlib; ключ шлюза читается из Workspace/.env и не выводится;
- LLM получает только текст источников, доступа к ОС у модели нет (ADR-004);
- «мозги»: черновик отчёта проходит независимую верификацию против данных;
- «власть в меру»: единственная запись — отчёт в Memory/Engineering/Reports/;
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


# --- Инструменты (реестр: git.inspect, journal.read, tree.inspect, reports.inspect, git.diff)

SENSITIVE_PATH_NAMES = {
    "dashboard-server.py", "security-targets.json", "security_contour.py",
    "main.py", ".env", ".env.example", "registry.json", "run_agent.py", "task_store.py",
}

# Секретоподобное = префикс + РЕАЛЬНОЕ значение (упоминания вида «FreeLLMAPI ключи» не матчатся).
SECRET_PATTERN = re.compile(
    r"(lsv2_pt_[A-Za-z0-9_\-]{10,}|sk-ant-[A-Za-z0-9_\-]{10,}|freellmapi-[a-z0-9]{10,}|"
    r"ghp_[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{12,}|AIza[A-Za-z0-9_\-]{20,}|"
    r"api_?key\s*[=:]\s*[\"'][A-Za-z0-9_\-]{16,}|password\s*[=:]\s*[\"'][^\"']{6,})",
    re.I,
)
# Файлы-сканеры сами содержат образцы паттернов — из проверки секретов исключены.
SECRET_SCAN_EXEMPT = {"tools/agents/run_agent.py", "tools/security/secret_scan.py"}


def _mask_secretish(line: str) -> str:
    return re.sub(r"(lsv2_pt_|sk-ant-|freellmapi-|ghp_|AKIA[0-9A-Z]{4}|AIza)[A-Za-z0-9_\-]{6,}",
                  lambda m: m.group(1) + "***", line)


def _iter_diff_files(diff_text: str):
    """Разбить diff на секции по файлам → [(path, [changed lines])]."""
    current, bucket = None, []
    for line in diff_text.splitlines():
        m = re.match(r"^diff --git a/(.+?) b/(.+?)$", line)
        if m:
            if current is not None:
                yield current, bucket
            current, bucket = m.group(2), []
        elif current is not None and line[:1] in ("+", "-") and not line.startswith(("+++", "---")):
            bucket.append(line)
    if current is not None:
        yield current, bucket

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
    agents_dir = ROOT / "Memory" / "Agents"
    data = {"logEntries": [], "logHeadings": [], "logModified": None,
            "activeTasks": [], "estateStaff": [], "passportsOnDisk": []}
    log_path = eng / "LOG.md"
    if log_path.exists():
        data["logModified"] = datetime.fromtimestamp(log_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        text = log_path.read_text(encoding="utf-8-sig", errors="replace")
        ids = sorted(set(re.findall(r"\bE-\d{3}\b", text)))
        data["logEntries"] = ids
        for m in re.finditer(r"^## (E-\d{3})\s*\|\s*([^\n|]+)", text, re.M):
            data["logHeadings"].append({"id": m.group(1), "time": m.group(2).strip()})
    tasks_dir = eng / "Tasks" / "Active"
    if tasks_dir.exists():
        data["activeTasks"] = [
            {"id": p.stem, "modified": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")}
            for p in sorted(tasks_dir.glob("*.json"))
        ]
    staff_path = agents_dir / "estate-staff.json"
    if staff_path.exists():
        try:
            staff = json.loads(staff_path.read_text(encoding="utf-8-sig", errors="replace"))
            members = staff.get("members", staff if isinstance(staff, list) else [])
            data["estateStaff"] = [
                {"id": m.get("id"), "name": m.get("name"), "passport": m.get("passport"),
                 "status": m.get("status")}
                for m in members if isinstance(m, dict)
            ]
        except json.JSONDecodeError:
            pass
    if agents_dir.exists():
        data["passportsOnDisk"] = sorted(p.name for p in agents_dir.glob("*.md"))
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


def tool_git_diff(window_days: int = 2, max_chars: int = 60000) -> dict:
    """Свежие правки (read-only): незакоммиченные изменения + окно последних коммитов."""
    working = git("diff", "HEAD")
    rng = f"@{{{window_days} days ago}}"
    recent = git("diff", rng, "HEAD")
    if not recent:
        rng = "HEAD~3"
        recent = git("diff", rng, "HEAD")
    stat_lines = git("diff", "--stat", rng, "HEAD").splitlines()
    stat_tail = stat_lines[-1] if stat_lines else ""
    deleted = [l for l in git("diff", "--diff-filter=D", "--name-only", rng, "HEAD").splitlines() if l.strip()]
    changed = [l[3:] if l.startswith(" M") else l for l in
               (git("diff", "--name-only", rng, "HEAD").splitlines()
                + git("diff", "--name-only", "HEAD").splitlines()) if l.strip()]
    sensitive = sorted({p for p in changed if Path(p).name in SENSITIVE_PATH_NAMES})
    secretish = []
    for diff_text in (recent, working):
        for path, lines in _iter_diff_files(diff_text):
            if path in SECRET_SCAN_EXEMPT:
                continue
            for line in lines:
                if line.startswith("+") and SECRET_PATTERN.search(line):
                    secretish.append(_mask_secretish(line[:120]).lstrip("+").strip())
    budget = max_chars * 3 // 5
    text = (recent or "")[:budget]
    if working:
        text += ("\n\n# --- uncommitted ---\n" + working[:max_chars - len(text)])
    return {
        "window": f"{rng}..HEAD + uncommitted",
        "statTail": stat_tail,
        "deletedFiles": deleted[:30],
        "sensitiveTouched": sensitive[:20],
        "secretishAddedLines": secretish[:20],
        "diffText": text,
        "truncated": (len(recent) + len(working)) > max_chars,
    }


def tool_reports_inspect(tag: str = "holmes-audit") -> dict:
    """Прошлый отчёт агента (по report_tag из реестра) и его машиночитаемый блок находок."""
    data = {"previousReportPath": None, "previousFindings": None}
    reports_dir = ROOT / "Memory" / "Engineering" / "Reports"
    if not reports_dir.exists():
        return data
    reports = sorted(reports_dir.glob(f"Report-*-{tag}.md"))
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


def compute_watson_findings(git_data: dict, journal: dict) -> list:
    """Хроника Memory/Engineering против фактов git и штата (стабильные ID)."""
    findings = []
    entries = set(journal.get("logEntries") or [])
    nums = sorted(int(e[2:]) for e in entries if re.fullmatch(r"E-\d{3}", e))
    if nums:
        gaps = [f"E-{i:03d}" for i in range(nums[0], nums[-1] + 1) if f"E-{i:03d}" not in entries]
        if gaps:
            findings.append({
                "id": "journal-enum-gap", "severity": "P3",
                "detail": f"Пропуски нумерации журнала: {', '.join(gaps[:10])}.",
            })
    bad_time = [h.get("id") for h in journal.get("logHeadings") or []
                if not re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", h.get("time", ""))]
    if bad_time:
        findings.append({
            "id": "journal-no-timestamp", "severity": "P3",
            "detail": f"Записи журнала без корректного времени (ГГГГ-ММ-ДД ЧЧ:ММ): {', '.join(bad_time[:10])}.",
        })
    mem_paths = [p for p in (git_data.get("modifiedTracked") or []) if p.startswith("Memory/")]
    mem_paths += [p for p in (git_data.get("untracked") or []) if p.startswith("Memory/")]
    if mem_paths:
        findings.append({
            "id": "memory-uncommitted", "severity": "P2",
            "detail": "Память не записана в git: " + ", ".join(mem_paths[:5])
                      + ("…" if len(mem_paths) > 5 else "") + ".",
        })
    active_status = ("на службе", "испытательный срок", "active")
    for s in journal.get("estateStaff") or []:
        if not s.get("id"):
            continue
        pid = s.get("passport")
        status = str(s.get("status") or "").lower()
        if pid is None and status in active_status:
            findings.append({
                "id": "staff-no-passport", "severity": "P3",
                "detail": f"Сотрудник «{s['id']}» ({s.get('status')}) в штате без паспорта.",
            })
        elif pid and not (ROOT / str(pid)).exists():
            findings.append({
                "id": "staff-passport-missing", "severity": "P2",
                "detail": f"Паспорт сотрудника «{s['id']}» не найден на диске: {pid}.",
            })
    stale = []
    for t in journal.get("activeTasks") or []:
        try:
            if (datetime.now() - datetime.strptime(t["modified"], "%Y-%m-%d %H:%M")).days >= 14:
                stale.append(t["id"])
        except ValueError:
            continue
    if stale:
        findings.append({
            "id": "tasks-stale", "severity": "P3",
            "detail": f"Задачи в Active без движения ≥14 дней: {', '.join(stale[:8])}.",
        })
    return findings


def compute_riskscan_findings(diff_data: dict) -> list:
    """Высокие риски свежих правок — только то, что видно в диффе (без спекуляций)."""
    findings = []
    if not diff_data:
        return findings
    secretish = diff_data.get("secretishAddedLines") or []
    if secretish:
        findings.append({
            "id": "secret-in-diff", "severity": "P1",
            "detail": f"В свежих правках {len(secretish)} строк с секретоподобными значениями (маскированы): "
                      + " | ".join(secretish[:3]),
        })
    deleted = diff_data.get("deletedFiles") or []
    if deleted:
        findings.append({
            "id": "deleted-files", "severity": "P2",
            "detail": f"Удалены файлы за окно прогона ({len(deleted)}): " + ", ".join(deleted[:6])
                      + ("…" if len(deleted) > 6 else "") + ".",
        })
    sensitive = diff_data.get("sensitiveTouched") or []
    if sensitive:
        findings.append({
            "id": "sensitive-edited", "severity": "P2",
            "detail": "Правки чувствительных файлов: " + ", ".join(sensitive[:6])
                      + ("…" if len(sensitive) > 6 else "") + ".",
        })
    m = re.search(r"(\d+) deletions?", diff_data.get("statTail") or "")
    if m and int(m.group(1)) >= 500:
        findings.append({
            "id": "mass-deletion", "severity": "P2",
            "detail": f"За окно прогона удалено {m.group(1)} строк ({diff_data.get('statTail', '')}).",
        })
    return findings


def compare_findings(findings: list, prev_block: dict) -> tuple:
    prev_by_id = {f["id"]: f for f in (prev_block or {}).get("findings", [])
                  if isinstance(f, dict) and "id" in f}
    cur_ids = {f["id"] for f in findings}
    statuses = {f["id"]: ("persisting" if f["id"] in prev_by_id else "new") for f in findings}
    resolved = [fid for fid in prev_by_id if fid not in cur_ids]
    return prev_by_id, statuses, resolved


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
                         has_prev: bool, agent_name: str = "Holmes") -> str:
    now_str = datetime.now(TASHKENT).strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# Отчёт {agent_name} (детерминированный, без LLM)",
        f"Сгенерирован: {now_str} (Tashkent)",
        "",
        "**Вывод:** автоматическая проверка по правилам агента; LLM-вердикт недоступен, выводы основаны только на правилах.",
        "**Ключевые факты:**",
    ]
    if findings:
        lines += [f"- [{f['severity']}][{statuses[f['id']]}] {f['detail']}" for f in findings]
    else:
        lines.append("- Аномалий по правилам проверки не обнаружено.")
    lines += followup_lines(findings, statuses, resolved, prev_by_id, has_prev)
    lines += [
        "**Варианты:** устранить находки по списку или повторить с LLM для аналитического вердикта.",
        "**Риски:** без регулярного аудита шум и дрейф контекста накапливаются незаметно.",
        "**Рекомендация:** повторить запуск с LLM; инициативы отмечать в дашборде (кнопка «Отправить на реализацию»).",
        "**Что нужно от Sovereign:** санкция на решение находок из списка.",
    ]
    return "\n".join(lines)


PEER_NOTE_RE = re.compile(r"ЗАМЕТКА СОСЕДУ:\s*([^:\n]{2,40}):\s*([^\n]{5,160})")
PEER_NOTES_PATH = ROOT / "Workspace" / "agents" / "peer-notes.jsonl"


def extract_peer_note(text: str) -> tuple[str, str] | None:
    """Заметка соседу — постскриптум в конце отчёта агента (идея «Заметка
    соседу», слово Sovereign 07.11). Не более одной: берём первое вхождение,
    переносы строк в тексте схлопываем."""
    m = PEER_NOTE_RE.search(text)
    if not m:
        return None
    to = " ".join(m.group(1).split()).strip()
    note = " ".join(m.group(2).split()).strip()
    if not to or not note:
        return None
    return to, note


def save_peer_note(from_agent: str, to: str, note: str) -> Path | None:
    try:
        PEER_NOTES_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "from": from_agent,
            "to": to,
            "text": note,
        }
        with PEER_NOTES_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return PEER_NOTES_PATH
    except OSError as e:
        print(f"[agents] Заметка соседу не сохранена ({e})", file=sys.stderr)
        return None


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
    report_tag = agent.get("report_tag", args.agent.lower() + "-audit")
    findings_kind = agent.get("findings_kind", "holmes")
    data = {
        "git": tool_git_inspect() if "git.inspect" in tools_used else None,
        "journal": tool_journal_read() if "journal.read" in tools_used else None,
        "tree": tool_tree_inspect() if "tree.inspect" in tools_used else None,
        "diff": tool_git_diff() if "git.diff" in tools_used else None,
        "previousReport": tool_reports_inspect(report_tag) if "reports.inspect" in tools_used else {"previousReportPath": None, "previousFindings": None},
    }
    print(f"[agents] Инструменты ({args.agent}): {', '.join(tools_used)}")

    # Цикл последствий: находки → сравнение прогонов. Создание задач из
    # инициатив — через дашборд (/api/holmes/implement) по санкции Sovereign.
    if findings_kind == "watson":
        findings = compute_watson_findings(data["git"] or {}, data["journal"] or {})
    elif findings_kind == "riskscan":
        findings = compute_riskscan_findings(data["diff"] or {})
    else:
        findings = compute_findings(data["git"] or {}, data["journal"] or {})
    prev_block = data["previousReport"].get("previousFindings")
    has_prev = prev_block is not None
    prev_by_id, statuses, resolved = compare_findings(findings, prev_block)
    print(f"[agents] Цикл: new={sum(1 for s in statuses.values() if s == 'new')} "
          f"persisting={sum(1 for s in statuses.values() if s == 'persisting')} "
          f"resolved={len(resolved)}")

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
            "(данные в блоке followup; если previousFindings пуст — «первый прогон, сравнивать не с чем»). "
            "В самом конце можешь добавить ровно одну строку "
            "«ЗАМЕТКА СОСЕДУ: <имя агента-получателя>: <суть, до 160 знаков>» — короткая реплика "
            "другому агенту поместья (соседи: Бэрримор, Холмс, Ватсон, Risk scan, Хантер; Sovereign "
            "соседом не является). Если сообщать соседу нечего — строку не добавляй."
        )
        followup_ctx = {
            "previousReport": data["previousReport"].get("previousReportPath"),
            "previousFindings": (prev_block or {}).get("findings"),
            "currentStatuses": [{"id": f["id"], "severity": f["severity"], "status": statuses[f["id"]]} for f in findings],
            "resolved": resolved,
        }
        user_prompt = (
            f"Данные инструментов (read-only, снимок {datetime.now(TASHKENT).strftime('%Y-%m-%d %H:%M')}):\n"
            + json.dumps(data, ensure_ascii=False, indent=2)
            + "\n\nfollowup (сравнение с прошлым аудитом, посчитано рантаймом):\n"
            + json.dumps(followup_ctx, ensure_ascii=False, indent=2)
            + "\n\n" + agent.get("task_line",
                                 "Проведи плановый аудит чистоты репозитория и журнала по своему мандату.")
        )
        env = load_env(ENV_PATH)
        try:
            result = gateway_chat(registry, env, system_prompt, user_prompt)
            report = result["text"]
            peer = extract_peer_note(report)
            if peer:
                saved = save_peer_note(args.agent, peer[0], peer[1])
                if saved:
                    print(f"[agents] Заметка соседу ({args.agent} → {peer[0]}): {saved.relative_to(ROOT)}")
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
        report = deterministic_report(findings, statuses, resolved, prev_by_id, has_prev,
                                      agent_name=args.agent)

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
    }
    report += "\n\n---\n\n```json\n" + json.dumps(state, ensure_ascii=False, indent=2) + "\n```"

    if "report.write" in agent["tools"]:
        reports_dir = ROOT / "Memory" / "Engineering" / "Reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        out_path = reports_dir / f"Report-{datetime.now(TASHKENT).strftime('%Y-%m-%d')}-{report_tag}.md"
        out_path.write_text(report + "\n", encoding="utf-8")
        print(f"[agents] Отчёт сохранён (report.write): {out_path.relative_to(ROOT)}")

    print()
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
