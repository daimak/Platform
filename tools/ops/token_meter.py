#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""token_meter.py — счётчик расхода токенов z.ai по локальной фактуре.

Сканирует ~/.zcode/cli/rollout/model-io-*.jsonl, считает input+output+cacheRead
по каждой сессии, пишет замер в Workspace/analytics/token-spend/ledger.jsonl
и обновляет state.json для дельт между замерами.

Запуск: python tools/ops/token_meter.py [--reading 287] [--quiet]
  --reading N  — свежее показание счётчика Дмитрия в миллионах (остаток).
                 Сохраняется и используется для сверки: дельта счётчика vs дельта фактуры.
На поводке: запускается вручную (рука Дмитрия или живая сессия), не по крону.
"""
import argparse
import glob
import json
import os
import sys
from datetime import datetime

HOME = os.path.expanduser("~")
ROLLOUT = os.path.join(HOME, ".zcode", "cli", "rollout")
SPEND_DIR = os.path.join("Workspace", "analytics", "token-spend")
LEDGER = os.path.join(SPEND_DIR, "ledger.jsonl")
STATE = os.path.join(SPEND_DIR, "state.json")

SHORT_ID = 10  # символов sessionId в отчёте


def usage_of(entry):
    u = (entry.get("response") or {}).get("usage") or {}
    return (u.get("inputTokens") or 0, u.get("outputTokens") or 0, u.get("cacheReadTokens") or 0)


def scan_sessions():
    """Возвращает {short_sid: {...}} по всем model-io файлам."""
    sessions = {}
    for path in glob.glob(os.path.join(ROLLOUT, "model-io-*.jsonl")):
        mtime = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M")
        inp = out = cr = 0
        n = 0
        first = last = None
        sid = None
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    try:
                        j = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    n += 1
                    i, o, c = usage_of(j)
                    inp += i; out += o; cr += c
                    if j.get("sessionId") and sid is None:
                        sid = j["sessionId"]
                    if j.get("startedAt"):
                        first = first or j["startedAt"]; last = j["startedAt"]
        except OSError as e:
            print(f"ERR чтение {path}: {e}", file=sys.stderr)
            continue
        if not n or (inp + out + cr) == 0:
            continue
        short = (sid or os.path.basename(path)[9:-6])[-SHORT_ID:]
        s = sessions.setdefault(short, {"requests": 0, "input": 0, "output": 0, "cache_read": 0,
                                        "total": 0, "first": None, "last": None})
        s["requests"] += n
        s["input"] += inp; s["output"] += out; s["cache_read"] += cr
        s["total"] += inp + out + cr
        s["first"] = min(filter(None, [s["first"], first])) if (s["first"] or first) else first
        s["last"] = max(filter(None, [s["last"], last])) if (s["last"] or last) else last
        s["mtime"] = mtime
    return sessions


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reading", type=float, help="показание счётчика Дмитрия, миллионов остатка")
    ap.add_argument("--quiet", action="store_true", help="без диагностических строк")
    args = ap.parse_args()

    os.makedirs(SPEND_DIR, exist_ok=True)
    # Хранилище не должно попадать в git (интерьер платформы): локальный .gitignore
    gi = os.path.join(SPEND_DIR, ".gitignore")
    if not os.path.exists(gi):
        with open(gi, "w", encoding="utf-8") as fh:
            fh.write("*\n!.gitignore\n")

    prev = {}
    manual_last = None
    if os.path.exists(STATE):
        try:
            with open(STATE, encoding="utf-8") as fh:
                st = json.load(fh)
            prev = st.get("sessions", {})
            manual_last = st.get("manual")
        except (json.JSONDecodeError, OSError):
            pass

    now = datetime.now().astimezone().isoformat(timespec="seconds")
    sessions = scan_sessions()

    rows = []
    grand = 0
    grand_delta = 0
    for sid, s in sorted(sessions.items(), key=lambda kv: -kv[1]["total"]):
        d = s["total"] - prev.get(sid, 0)
        grand += s["total"]
        grand_delta += d
        rows.append({"id": sid, "total": s["total"], "delta": d, "requests": s["requests"],
                     "input": s["input"], "output": s["output"], "cache_read": s["cache_read"],
                     "first": s["first"], "last": s["last"]})

    reading = None
    if args.reading is not None:
        reading = {"ts": now, "million": args.reading}
        if manual_last and manual_last.get("million") is not None:
            counter_delta = (manual_last["million"] - args.reading) * 1e6
            reading["prev_million"] = manual_last["million"]
            reading["counter_delta"] = counter_delta
            reading["ledger_delta"] = grand_delta
            reading["gap"] = counter_delta - grand_delta  # >0: счётчик сожрал больше фактуры (лаг/доначисление)

    record = {"ts": now, "grand_total": grand, "grand_delta": grand_delta, "sessions": rows}
    if reading:
        record["manual"] = reading
    with open(LEDGER, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    new_state = {"last_ts": now, "sessions": {sid: s["total"] for sid, s in sessions.items()},
                 "manual": reading or manual_last}
    with open(STATE, "w", encoding="utf-8") as fh:
        json.dump(new_state, fh, ensure_ascii=False, indent=1)

    # Компактный вывод (времена — в локальную зону, у Дмитрия Тшк)
    def loc(ts):
        if not ts:
            return "?"
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().strftime("%H:%M:%S")
        except ValueError:
            return ts[-8:]
    print(f"[{now}] факт всего: {grand/1e6:.2f}M (дельта с прошлого замера: {grand_delta/1e6:+.2f}M)")
    print(f"{'сессия':<12}{'всего':>9}{'дельта':>9}{'запр.':>7}  окно")
    for r in rows[:8]:
        print(f"{r['id']:<12}{r['total']/1e6:>8.2f}M{r['delta']/1e6:>+8.2f}M{r['requests']:>7}  {loc(r['first'])}→{loc(r['last'])}")
    if len(rows) > 8:
        print(f"  ...и ещё {len(rows)-8} сессий")
    if reading and "gap" in reading:
        print(f"счётчик: {reading['prev_million']:.1f}M → {reading['million']:.1f}M "
              f"(−{(reading['counter_delta'])/1e6:.2f}M) vs фактура −{grand_delta/1e6:.2f}M; "
              f"расхождение {reading['gap']/1e6:+.2f}M (лаг/доначисление)")
    if not args.quiet:
        print(f"ledger: {os.path.abspath(LEDGER)}")


if __name__ == "__main__":
    main()
