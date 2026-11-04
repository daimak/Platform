#!/usr/bin/env python3
"""Обёртка nmap для своих хостов: версии сервисов + CVE (NSE-скрипт vulners).

По умолчанию цель — 127.0.0.1. Цели вне loopback и приватных диапазонов требуют
--allow-external (осознанное решение Sovereign). Сырой вывод nmap сохраняется рядом
с JSON-отчётом в %LOCALAPPDATA%/Platform/SecurityReports/.
"""

import argparse
import ipaddress
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import REPORTS_DIR, now_iso, print_summary, save_report  # noqa: E402

NMAP_CANDIDATES = [
    shutil.which("nmap"),
    r"C:\Program Files (x86)\Nmap\nmap.exe",
    r"C:\Program Files\Nmap\nmap.exe",
    "/usr/bin/nmap",
]
PORT_ROW = re.compile(r"^(\d+)/(tcp|udp)\s+(open|open\|filtered)\s+(.*)$")
CVE_RE = re.compile(r"\bCVE-\d{4}-\d{4,7}\b")
CVSS_RE = re.compile(r"(?:cvss=|CVSSv3(?:\.1)? Score:\s*|\b)(\d{1,2}\.\d)")


def find_nmap() -> str:
    for candidate in NMAP_CANDIDATES:
        if candidate and Path(candidate).exists():
            return candidate
    raise FileNotFoundError("nmap не найден ни в PATH, ни в стандартных каталогах установки.")


def check_target(target: str, allow_external: bool) -> str:
    host = target.split("/")[0].strip()
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        # доменное имя: разрешаем только с явным флагом
        if allow_external:
            return host
        raise ValueError(f"Цель «{host}» — не IP; для внешних целей нужен --allow-external.")
    if ip.is_loopback or ip.is_private:
        return host
    if allow_external:
        return host
    raise ValueError(f"Цель {host} вне loopback/приватных сетей — нужен --allow-external (Sovereign решает сам).")


def parse_output(raw: str) -> list:
    ports = []
    current = None
    for line in raw.splitlines():
        row = PORT_ROW.match(line.strip())
        if row:
            current = {"port": f"{row.group(1)}/{row.group(2)}", "service": row.group(4).strip(), "cves": []}
            ports.append(current)
            continue
        if current is not None:
            for cve in CVE_RE.findall(line):
                if cve not in [c["id"] for c in current["cves"]]:
                    score_match = CVSS_RE.search(line)
                    current["cves"].append({"id": cve, "cvss": float(score_match.group(1)) if score_match else None})
    return ports


def main() -> int:
    parser = argparse.ArgumentParser(description="nmap-скан своих хостов")
    parser.add_argument("--target", default="127.0.0.1")
    parser.add_argument("--ports", default="", help="например 1-1000 или 80,443,8086 (пусто = топ-порты nmap)")
    parser.add_argument("--cve", action="store_true", help="добавить NSE-скрипт vulners (запрос к vulners.com)")
    parser.add_argument("--allow-external", action="store_true", help="разрешить цели вне loopback/приватных сетей")
    args = parser.parse_args()

    target = check_target(args.target, args.allow_external)
    nmap = find_nmap()
    command = [nmap, "-Pn", "-sV", "--version-light"]
    if args.ports:
        command += ["-p", args.ports]
    if args.cve:
        command += ["--script", "vulners"]
    command.append(target)

    result = subprocess.run(
        command, capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=900, check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if __import__("os").name == "nt" else 0,
    )
    raw = result.stdout or ""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = now_iso().replace(":", "").replace("-", "")[0:15]
    raw_path = REPORTS_DIR / f"nmap-probe-raw-{stamp}.txt"
    raw_path.write_text(raw, encoding="utf-8")

    ports = parse_output(raw)
    open_ports = [p for p in ports if p["port"].endswith("/tcp")]
    report = {
        "tool": "nmap-probe",
        "generated": now_iso(),
        "target": target,
        "cve_script": bool(args.cve),
        "returncode": result.returncode,
        "open_ports": open_ports,
        "raw_file": raw_path.name,
    }
    out_path = save_report("nmap-probe", report)

    lines = [
        f"nmap {target} (vulners={'да' if args.cve else 'нет'}): открытых TCP-портов {len(open_ports)}",
    ]
    for p in open_ports[:12]:
        cve_note = f" — CVE: {', '.join(c['id'] for c in p['cves'][:5])}" if p["cves"] else ""
        lines.append(f"  {p['port']:10} {p['service']}{cve_note}")
    if not open_ports:
        lines.append("Открытых портов не найдено.")
    lines.append(f"Отчёт: {out_path.name}; сырой вывод: {raw_path.name} ({REPORTS_DIR})")
    print_summary(lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
