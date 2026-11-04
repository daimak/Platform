#!/usr/bin/env python3
"""Поиск секретов в дереве репозитория (gitleaks-lite, read-only, stdlib-only).

Известные форматы ключей — красным, общие присваивания — оранжевым (проверить руками).
Найденное МАСКИРУЕТСЯ в отчёте: печатаются первые 6 символов, не больше.
Отчёт — в %LOCALAPPDATA%/Platform/SecurityReports/ (вне git, правило видимости).
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import now_iso, print_summary, save_report  # noqa: E402

SKIP_DIRS = {".git", "node_modules", "graphify-out", ".obsidian", "__pycache__", ".zcode", ".vscode"}
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2", ".ttf", ".eot",
            ".zip", ".gz", ".7z", ".exe", ".dll", ".pyc", ".pdf", ".mp4", ".webm", ".sqlite"}
MAX_FILE_BYTES = 1_500_000

# (rule, severity, regex, метка)
PATTERNS = [
    ("aws-access-key", "red", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS Access Key ID"),
    ("github-token", "red", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"), "GitHub token"),
    ("google-api-key", "red", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b"), "Google API key"),
    ("openai-key", "red", re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}\b"), "OpenAI-стиль ключ"),
    ("slack-token", "red", re.compile(r"\bxox[bpars]-[A-Za-z0-9\-]{10,}\b"), "Slack token"),
    ("huggingface-token", "red", re.compile(r"\bhf_[A-Za-z0-9]{30,}\b"), "HuggingFace token"),
    ("private-key-block", "red", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP |DSA )?PRIVATE KEY"), "Приватный ключ в файле"),
    ("generic-assignment", "orange", re.compile(
        r"(?i)(?:api[_-]?key|apikey|secret|token|passwd|password)\s*[:=]\s*[\"'][A-Za-z0-9+/_\-\.]{20,}[\"']"
    ), "Похоже на присваивание секрета — проверить руками"),
]
PLACEHOLDER_HINTS = ("example", "placeholder", "xxx", "your_", "your-", "insert_", "changeme", "test", "sample", "xxxxx")


def iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        if path.suffix.lower() in SKIP_EXT:
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        yield path, relative


def mask(match_text: str) -> str:
    return match_text[:6] + "…(masked)"


def main() -> int:
    parser = argparse.ArgumentParser(description="Поиск секретов в репо (read-only)")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    args = parser.parse_args()
    root = Path(args.root).resolve()

    findings = []
    files_scanned = 0
    for path, relative in iter_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "\x00" in text[:4096]:
            continue
        files_scanned += 1
        for lineno, line in enumerate(text.splitlines(), start=1):
            if any(hint in line.lower() for hint in PLACEHOLDER_HINTS):
                continue
            for rule, severity, regex, label in PATTERNS:
                match = regex.search(line)
                if match:
                    findings.append({
                        "file": str(relative),
                        "line": lineno,
                        "rule": rule,
                        "severity": severity,
                        "label": label,
                        "excerpt": mask(match.group(0)),
                    })

    counts = {}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    report = {
        "tool": "secret-scan",
        "generated": now_iso(),
        "root": str(root),
        "files_scanned": files_scanned,
        "findings_count": len(findings),
        "counts": counts,
        "findings": findings[:200],
    }
    out_path = save_report("secret-scan", report)

    lines = [
        f"Поиск секретов: просканировано {files_scanned} файлов, находок {len(findings)} "
        f"(красных {counts.get('red', 0)}, оранжевых {counts.get('orange', 0)})",
    ]
    for f in findings[:15]:
        lines.append(f"[{f['severity'].upper():6}] {f['file']}:{f['line']}  {f['label']}  {f['excerpt']}")
    if not findings:
        lines.append("Известных форматов секретов не найдено — чисто.")
    lines.append(f"Отчёт: {out_path.name} ({out_path.parent}) — содержимое маскировано")
    print_summary(lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
