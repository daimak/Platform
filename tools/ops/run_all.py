#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Единый тест-раннер Platform Evo (карточка ops-test-runner-unify, 06.11).

Все сьюты одной командой: python tools/ops/run_all.py
Сводка по каждому сьюту, общий exit code: 0 — всё зелёное, 1 — были падения.
Новые сьюты добавляй в SUITES (discover-путь + флаги).
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SUITES = [
    ("tools/tests", ["discover", "-s", "tools/tests"]),
    ("tools/barrymore", ["discover", "-s", "tools/barrymore", "-p", "test_*.py"]),
]


def main() -> int:
    failed = []
    for label, args in SUITES:
        print(f"=== {label} ===", flush=True)
        result = subprocess.run(
            [sys.executable, "-m", "unittest", *args],
            cwd=ROOT,
        )
        if result.returncode != 0:
            failed.append(label)
    print()
    if failed:
        print(f"ПАДАЛИ: {', '.join(failed)}")
        return 1
    print("Все сьюты зелёные.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
