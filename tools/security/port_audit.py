#!/usr/bin/env python3
"""Аудит слушающих портов Windows: кто слушает, на каких адресах, опасно ли.

Read-only (ADR-003/004): netstat + tasklist, никаких изменений. Классификация:
красный — опасный сервис на 0.0.0.0/::; предупреждение — незнакомое на wildcard;
инфо — норма Windows; ожидаемые loopback-службы — из port_allowlist.json.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import now_iso, print_summary, save_report  # noqa: E402

ALLOWLIST_PATH = Path(__file__).resolve().parent / "port_allowlist.json"

# Порты, чья открытость на wildcard-интерфейсе = класс «открытый 8086».
DANGEROUS = {
    2375: "Docker API без TLS (= root хоста)",
    2376: "Docker API TLS",
    3389: "RDP (брутфорс круглосуточно)",
    5900: "VNC",
    6379: "Redis (без пароля = запись файлов/RCE)",
    8086: "InfluxDB",
    9200: "Elasticsearch",
    27017: "MongoDB",
    3306: "MySQL",
    5432: "PostgreSQL",
    3000: "Grafana",
    9000: "Portainer / PHP-FPM",
    8500: "Consul",
    15672: "RabbitMQ Management",
}
# Системные слушатели Windows — норма, не шумим.
WINDOWS_NORMAL = {135, 139, 445, 5040, 5355, 5357, 5353, 7680, 3702, 5985, 5986}

NETSTAT_ROW = re.compile(r"^\s*(TCP|UDP)\s+(\S+)\s+(\S+)(?:\s+(\S+))?\s+(\d+)\s*$")


def run_command(command: list, timeout: int = 30) -> str:
    result = subprocess.run(
        command, capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=timeout, check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if __import__("os").name == "nt" else 0,
    )
    return result.stdout or ""


def process_map() -> dict:
    names = {}
    output = run_command(["tasklist", "/FO", "CSV", "/NH"])
    for row in csv_rows(output):
        if len(row) >= 2 and row[1].strip().isdigit():
            names[int(row[1])] = row[0].strip('"')
    return names


def csv_rows(text: str):
    import csv as csv_module
    import io

    reader = csv_module.reader(io.StringIO(text))
    for row in reader:
        if row:
            yield row


def parse_netstat(output: str) -> list:
    listeners = []
    for line in output.splitlines():
        match = NETSTAT_ROW.match(line)
        if not match:
            continue
        proto, local, _foreign, state, pid = match.groups()
        addr, _, port = local.rpartition(":")
        if proto == "TCP" and state != "LISTENING":
            continue
        listeners.append({"proto": proto, "addr": addr, "port": int(port), "state": state or "—", "pid": int(pid)})
    return listeners


def classify(listener: dict, process: str, allowlist: dict) -> dict:
    addr, port = listener["addr"], listener["port"]
    if addr in ("127.0.0.1", "::1"):
        bind, severity = "loopback", "ok"
        expected = any(e.get("port") == port for e in allowlist.get("loopback", []))
        note = "ожидаемая служба" if expected else "только локально (не из allowlist)"
    elif addr in ("0.0.0.0", "::", "*"):
        bind = "wildcard"
        if port in DANGEROUS:
            severity, note = "red", f"ОПАСНО: {DANGEROUS[port]} открыт на всех интерфейсах"
        elif port in WINDOWS_NORMAL:
            severity, note = "info", "норма для Windows (проверить фаервол при сомнении)"
        else:
            severity, note = "orange", "незнакомый сервис на всех интерфейсах — опознать!"
    else:
        bind, severity, note = "частный адрес", "info", "привязан к конкретному интерфейсу"
    listener.update({"process": process, "bind": bind, "severity": severity, "note": note})
    return listener


def main() -> int:
    parser = argparse.ArgumentParser(description="Аудит слушающих портов (read-only)")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]), help="корень репо (для allowlist)")
    args = parser.parse_args()

    allowlist_path = Path(args.root) / "tools" / "security" / "port_allowlist.json"
    allowlist = {}
    try:
        allowlist = json.loads(allowlist_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        allowlist = {}

    netstat = run_command(["netstat", "-ano"])
    listeners = parse_netstat(netstat)
    processes = process_map()
    records = [classify(dict(l), processes.get(l["pid"], "?"), allowlist) for l in listeners]
    records.sort(key=lambda r: ({"red": 0, "orange": 1, "info": 2, "ok": 3}[r["severity"]], r["port"]))

    counts = {}
    for r in records:
        counts[r["severity"]] = counts.get(r["severity"], 0) + 1
    report = {
        "tool": "port-audit",
        "generated": now_iso(),
        "total_listeners": len(records),
        "counts": counts,
        "listeners": records,
        "allowlist_note": str(allowlist_path.name),
    }
    path = save_report("port-audit", report)

    lines = [
        f"Аудит портов: слушателей {len(records)} — красных {counts.get('red', 0)}, "
        f"оранжевых {counts.get('orange', 0)}, системных {counts.get('info', 0)}, loopback {counts.get('ok', 0)}",
    ]
    for r in records:
        if r["severity"] in ("red", "orange"):
            lines.append(f"[{r['severity'].upper():6}] {r['proto']} {r['addr']}:{r['port']}  {r['process']}  — {r['note']}")
    if counts.get("red", 0) == 0 and counts.get("orange", 0) == 0:
        lines.append("Опасных и незнакомых wildcard-слушателей нет — чисто.")
    lines.append(f"Отчёт: {path.name} ({path.parent})")
    print_summary(lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
