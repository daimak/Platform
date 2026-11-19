"""Разовая миграция estate-staff.json: rank L0..L5 -> CEO-0..CEO-5 (решение Дмитрия 15.11).

Соломон поднимается на CEO-1 (рядом с Бэрримором), Рокфеллер — CEO-2,
службы CEO-3, капитаны миров CEO-4, специалисты CEO-5.
Запуск: python -I scratch/migrate-staff-ranks.py
"""
import json
from pathlib import Path

path = Path(r"C:/Work/Platform/Memory/Agents/estate-staff.json")
data = json.loads(path.read_text(encoding="utf-8"))

MAP = {"barrymore": "CEO-1", "solomon": "CEO-1", "rockefeller": "CEO-2"}
for m in data.get("members", []):
    rank = m.get("rank")
    if rank == "L1":
        m["rank"] = MAP.get(m.get("id"), "CEO-1")
    elif rank == "L2":
        m["rank"] = MAP.get(m.get("id"), "CEO-2")
    elif rank == "L3":
        m["rank"] = "CEO-3"
    elif rank == "L4":
        m["rank"] = "CEO-4"
    elif rank == "L5":
        m["rank"] = "CEO-5"

comment = str(data.get("comment", ""))
data["comment"] = comment.replace(
    "регалия табеля о рангах L0..L5",
    "регалия табеля о рангах CEO-0..CEO-5 (с 15.11; переезд с L0..L5 по слову Дмитрия, Соломон CEO-1)",
)
data["version"] = 6
data["updated"] = "2026-11-15"

path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("ok")
for m in data.get("members", []):
    if m.get("rank"):
        print(m.get("id"), "->", m["rank"])
