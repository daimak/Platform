#!/usr/bin/env python3
"""Daily analytics snapshot builder.

Reads the live data sources (job search results, OLX autoservices listings,
token usage log) and writes a dated snapshot under Workspace/analytics/YYYY-MM-DD/
with raw copies, clean CSVs, LLM-ready chunks and a stats summary.

stdlib-only (ADR-003/004). Run: python tools/analytics_snapshot.py [YYYY-MM-DD]
"""
import csv
import json
import re
import shutil
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYTICS = ROOT / "Workspace" / "analytics"

JOBS_CHUNK_SIZE = 30
OLX_CHUNK_SIZE = 11

TOKEN_LOG = ROOT / "TOKEN_USAGE_LOG.md"


def snapshot_dir(day: str) -> Path:
    d = ANALYTICS / day
    (d / "raw").mkdir(parents=True, exist_ok=True)
    (d / "chunks").mkdir(parents=True, exist_ok=True)
    return d


def copy_raw(d: Path) -> dict:
    raw = {}
    for src in ["tools/job_search_results.json", "tools/olx_autoservices_data.json",
                "tools/autoservices_data.json"]:
        p = ROOT / src
        if p.exists():
            shutil.copy2(p, d / "raw" / p.name)
            raw[p.name] = p.stat().st_size
    if TOKEN_LOG.exists():
        shutil.copy2(TOKEN_LOG, d / "raw" / TOKEN_LOG.name)
        raw[TOKEN_LOG.name] = TOKEN_LOG.stat().st_size
    return raw


def build_jobs(d: Path) -> dict:
    src = d / "raw" / "job_search_results.json"
    if not src.exists():
        return {}
    rows = json.loads(src.read_text(encoding="utf-8"))
    fields = ["idx", "source", "title", "company", "location", "salary", "date", "url", "snippet"]
    with open(d / "jobs.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(fields)
        for i, r in enumerate(rows, 1):
            w.writerow([i] + [r.get(k, "") or "" for k in fields[1:]])
    # LLM-ready chunks
    chunk_files = []
    for start in range(0, len(rows), JOBS_CHUNK_SIZE):
        part = rows[start:start + JOBS_CHUNK_SIZE]
        n = start // JOBS_CHUNK_SIZE + 1
        out = d / "chunks" / f"jobs-{n:02d}.md"
        lines = [f"# Jobs chunk {n:02d} (records {start + 1}-{start + len(part)} of {len(rows)})\n"]
        for i, r in enumerate(part, start + 1):
            lines.append(f"## #{i:03d} | {r.get('title', '')} | {r.get('company', '') or '—'}")
            lines.append(f"- source: {r.get('source', '')}")
            if r.get("location"):
                lines.append(f"- location: {r['location']}")
            if r.get("salary"):
                lines.append(f"- salary: {r['salary']}")
            if r.get("date"):
                lines.append(f"- date: {r['date']}")
            lines.append(f"- url: {r.get('url', '')}")
            if r.get("snippet"):
                lines.append(f"- snippet: {r['snippet']}")
            lines.append("")
        out.write_text("\n".join(lines), encoding="utf-8")
        chunk_files.append(out.name)
    return {"count": len(rows), "chunks": chunk_files,
            "unique_urls": len({r.get("url", "") for r in rows})}


def build_olx_chunks(d: Path) -> dict:
    src = d / "raw" / "olx_autoservices_data.json"
    if not src.exists():
        return {}
    rows = json.loads(src.read_text(encoding="utf-8"))
    chunk_files = []
    for start in range(0, len(rows), OLX_CHUNK_SIZE):
        part = rows[start:start + OLX_CHUNK_SIZE]
        n = start // OLX_CHUNK_SIZE + 1
        out = d / "chunks" / f"olx-autoservices-{n:02d}.md"
        lines = [f"# OLX autoservices chunk {n:02d} (records {start + 1}-{start + len(part)} of {len(rows)})\n"]
        for i, r in enumerate(part, start + 1):
            lines.append(f"## #{i:03d} | {r.get('title', '')}")
            lines.append(f"- url: {r.get('url', '')}")
            lines.append(f"- description: {r.get('description', '')}")
            lines.append("")
        out.write_text("\n".join(lines), encoding="utf-8")
        chunk_files.append(out.name)
    return {"count": len(rows), "chunks": chunk_files}


def parse_k(v: str) -> str:
    m = re.search(r"([\d.,]+)\s*K", v)
    if m:
        return str(int(float(m.group(1).replace(",", ".")) * 1000))
    m = re.search(r"\d[\d\s]*", v)
    return m.group(0).replace(" ", "") if m else ""


def build_tokens(d: Path) -> dict:
    if not TOKEN_LOG.exists():
        return {}
    text = TOKEN_LOG.read_text(encoding="utf-8-sig")
    rows = []
    for m in re.finditer(r"### Ответ (\d+)\n- \*\*Дата и время\*\*: (.+?)\n- \*\*Расход токенов\*\*: (\d+)\n- \*\*Контекст\*\*: (.+)", text):
        rows.append(["codex-tui", f"ответ {m.group(1)}", m.group(2), "", "", m.group(3), "", m.group(4)])
    for m in re.finditer(r"#### Запрос: (.+?)\n- \*\*Модель\*\*: (.+?)\n- \*\*Входной контекст \(Prompt\)\*\*: (.+?)\n- \*\*Выходные токены \(Completion\)\*\*: (.+?)\n- \*\*Время ответа\*\*: (\d+)", text):
        rows.append(["freellm-api", "", m.group(1), m.group(2), parse_k(m.group(3)),
                     re.search(r"\d+", m.group(4)).group(0), m.group(5) + " мс", ""])
    with open(d / "token_usage.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["kind", "item", "time", "model", "prompt_tokens", "completion_tokens", "latency_ms", "context"])
        for r in rows:
            w.writerow(r)
    return {"codex_answers": sum(1 for r in rows if r[0] == "codex-tui"),
            "freellm_calls": sum(1 for r in rows if r[0] == "freellm-api")}


def build_stats(d: Path, raw: dict, jobs: dict, olx: dict, tokens: dict) -> None:
    lines = [f"# Snapshot stats — {d.name}\n"]
    lines.append(f"Raw files: {', '.join(f'{k} ({v} B)' for k, v in raw.items())}\n")
    if jobs:
        lines.append(f"- Jobs: {jobs['count']} records, {jobs['unique_urls']} unique urls, chunks: {', '.join(jobs['chunks'])}")
        rows = json.loads((d / "raw" / "job_search_results.json").read_text(encoding="utf-8"))
        for s, c in Counter(r.get("source", "") for r in rows).most_common():
            lines.append(f"  - {s}: {c}")
        lines.append(f"  - без salary: {sum(1 for r in rows if not r.get('salary'))}, "
                     f"без location: {sum(1 for r in rows if not r.get('location'))}, "
                     f"без date: {sum(1 for r in rows if not r.get('date'))}")
    if olx:
        lines.append(f"- OLX autoservices: {olx['count']} records, chunks: {', '.join(olx['chunks'])}")
    if tokens:
        lines.append(f"- Token log: {tokens['codex_answers']} codex answers, {tokens['freellm_calls']} FreeLLMAPI calls")
    lines.append("")
    (d / "stats.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    day = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    d = snapshot_dir(day)
    raw = copy_raw(d)
    jobs = build_jobs(d)
    olx = build_olx_chunks(d)
    tokens = build_tokens(d)
    build_stats(d, raw, jobs, olx, tokens)
    manifest = {"date": day, "raw": raw, "jobs": jobs, "olx": olx, "tokens": tokens,
                "generator": "tools/analytics_snapshot.py (stdlib-only)"}
    (d / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
