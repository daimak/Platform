# -*- coding: utf-8 -*-
"""Сборка снапшота «Хроника» — как менялся проект (git-история).

Паттерн brief.js/excursion-data.js: детерминированный генератор пишет
eVo/dashboard/chronicle-data.js, страница только читает (работает и с file://,
и через сервер 8765). stdlib-only, git — read-only.

Прогон: python tools/barrymore/build-chronicle.py
"""

import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "eVo" / "dashboard" / "chronicle-data.js"

# Потоки проекта: ключи (subject, пути) → категория. Порядок = приоритет.
CATS = [
    ("security", "🛡", "#f87171", [
        "security", "vuln", "secret", "pentest", "kali", "darkwatch", "feeds",
        "radar", "sandbox", "hook", "key", "leak", "cve", "threat", "защит",
        "безопасн", "юjuice", "полигон"]),
    ("agents", "🕵", "#38bdf8", [
        "agent", "holmes", "watson", "riskscan", "steward", "staff", "hunter",
        "barrymore", "rockefeller", "штат", "паспорт", "бриф", "диспетчер",
        "флот", "вахта", "лейн"]),
    ("worlds", "🌀", "#f472b6", [
        "world", "maelstorm", "observatory", "planet", "map", "мир", "миров",
        "остров", "архипелаг", "worlds"]),
    ("money", "💰", "#fbbf24", [
        "money", "order", "sale", "resume", "job", "kwork", "higgsfield",
        "income", "деньг", "заработ", "продаж", "касса", "заказ", "отклик"]),
    ("infra", "☁", "#a78bfa", [
        "cloud", "vm", "tunnel", "docker", "deploy", "systemd", "install",
        "restart", "gitignore", "ветк", "release", "merge", "репозитор",
        "пуш", "commit"]),
    ("ui", "🏰", "#34d399", [
        "dashboard", "kanban", "css", "панель", "меню", "кнопк", "виджет",
        "дашборд", "интерфейс", "отчёт", "доклад"]),
    ("docs", "📚", "#94a3b8", [
        "memory", "journal", "changelog", "readme", "docs", "principle",
        "decision", "protocol", "журнал", "документ", "протокол", "принцип",
        "аудит", "задач"]),
]


def classify(subject, paths):
    text = subject.lower() + " " + " ".join(paths).lower()
    best, best_score = "docs", 0
    for cat_id, _icon, _color, keys in CATS:
        score = sum(2 for key in keys if key in text)
        if score > best_score:
            best, best_score = cat_id, score
    return best


def main():
    proc = subprocess.run(
        ["git", "log", "--all", "--pretty=format:%x01%h|%ad|%s",
         "--date=format:%Y-%m-%d|%H:%M", "--numstat"],
        cwd=ROOT, capture_output=True, check=True)
    blocks = proc.stdout.decode("utf-8", errors="replace").split("\x01")

    commits, days = [], []
    total_add = total_del = 0
    for block in blocks:
        if not block.strip():
            continue
        lines = block.strip().splitlines()
        head = lines[0]
        if head.count("|") < 3:
            continue
        chash, date, htime, subject = head.split("|", 3)
        files, add, dele = 0, 0, 0
        paths = []
        for line in lines[1:]:
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            a, d, path = parts[0], parts[1], parts[2]
            files += 1
            paths.append(path.rsplit("/", 1)[-1])
            if a != "-" and d != "-":
                add += int(a)
                dele += int(d)
        cat = classify(subject, paths)
        total_add += add
        total_del += dele
        commits.append({"h": chash, "d": date, "t": htime, "s": subject[:120],
                        "f": files, "a": add, "x": dele, "c": cat})

    by_day = defaultdict(lambda: {"n": 0, "a": 0, "x": 0, "cats": defaultdict(int)})
    for c in commits:
        day = by_day[c["d"]]
        day["n"] += 1
        day["a"] += c["a"]
        day["x"] += c["x"]
        day["cats"][c["c"]] += 1
    for date in sorted(by_day):
        d = by_day[date]
        top = max(d["cats"].items(), key=lambda kv: kv[1])[0]
        days.append({"date": date, "n": d["n"], "a": d["a"], "x": d["x"],
                     "top": top, "cats": dict(d["cats"])})

    data = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_commits": len(commits),
        "total_add": total_add,
        "total_del": total_del,
        "days": days,
        "commits": list(reversed(commits)),  # свежие сверху
        "cats_meta": {cid: {"icon": icon, "color": color}
                      for cid, icon, color, _keys in CATS},
    }

    OUT.write_text(
        "/* ХРОНИКА — снапшот git-истории (генератор tools/barrymore/build-chronicle.py).\n"
        "   Регенерируется прогоном генератора; страница chronicle.html только читает. */\n"
        "window.CHRONICLE = " + _dump(data) + ";\n",
        encoding="utf-8")
    print("chronicle-data.js: %d commits, %d days, %d bytes" % (
        len(commits), len(days), OUT.stat().st_size))
    return 0


def _dump(obj):
    import json
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    sys.exit(main())
