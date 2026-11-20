"""Диспетчер диспута Правления — рука Бэрримова (решил Дмитрий 16.11:
«щёлкаю по нему — у него активна возможность собрать собрание»).

Берёт свежее собрание правления (фаза «созвано»/«доклады») и последовательно
гоняет через LLM-шлюз :31415 (тот же, что у Холмса/Ватсона — план-токены
CEO не тратит):
  раунд 1 — доклад каждого участника по каждому пункту;
  раунд 2 — возражения (каждый читал доклады коллег; CEO-1 может оценивать
            «правильно / слабо / доработай»);
  сводка модератора — совместные выводы, спорное — на решение CEO-0.
Фазы двигает сам. Протокол — через локальный бэк /api/council/* (тот же
контракт, что у кнопок CEO-0 в зале council.html).

Запуск: python -I tools/agents/council_dispatch.py --id <meeting-id>
Прогресс — в stdout (бэк пишет в LOG_DIR/council-dispatch.log).

Только stdlib; ключ шлюза читается из Workspace/.env и не выводится.
"""
import argparse
import importlib.util
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN_AGENT_PATH = ROOT / "tools" / "agents" / "run_agent.py"
COUNCIL_DIR = ROOT / "Memory" / "Council"
PASSPORT_MAX = 2600  # знаков паспорта в системном промпте

REGULATION = (
    "Ты — участник Правления Estate (совет управляющих при CEO-0). Правила собрания: "
    "отвечай по-русски, кратко и по делу, без канцелярита и без ИИ-штампов; "
    "НЕ выдумывай цифры и факты — если данных нет, прямо скажи, что нужно проверить; "
    "выступай от лица своей роли, опирайся на паспорт."
)


def _load_run_agent():
    """run_agent.py — дефис в имени, обычный import не проходит."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))  # run_agent:36 импортирует tools.lib.token_logger — корень нужен в sys.path (python -I его убирает)
    spec = importlib.util.spec_from_file_location("run_agent_mod", RUN_AGENT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _get(base: str, path: str) -> dict:
    with urllib.request.urlopen(base + path, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post(base: str, path: str, payload: dict) -> dict:
    req = urllib.request.Request(
        base + path,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "Origin": base},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _system_prompt(member: dict) -> str:
    passport_line = "(паспорта нет — отвечай по роли)"
    passport = ROOT / member["passport"] if member.get("passport") else None
    if passport and passport.is_file():
        passport_line = passport.read_text(encoding="utf-8")[:PASSPORT_MAX]
    critic = (
        "У тебя право рассуждения: можешь оценивать чужие доклады — «правильно / слабо / доработай»."
        if member.get("critic")
        else "Права рассуждения нет (оценки «слабо/доработай» — только CEO-1): докладывай и возражай по существу."
    )
    return (
        f"{REGULATION}\n\nТы: {member['name']} — CEO-{member['ceo']}, {member['role']}.\n"
        f"{critic}\n\nТвой паспорт (контекст):\n{passport_line}"
    )


def _chat(ra, registry: dict, env: dict, system: str, user: str, who: str) -> str | None:
    try:
        result = ra.gateway_chat(registry, env, system, user)
    except Exception as error:  # noqa: BLE001 — диспут не должен падать из-за одного вызова
        print(f"[council] шлюз не ответил для {who}: {error}", file=sys.stderr)
        return None
    text = str(result.get("text") or "").strip()
    if not text:
        print(f"[council] пустой ответ шлюза для {who}", file=sys.stderr)
        return None
    return text[:4000]


def _attendees_for(meeting: dict, members: dict) -> list:
    return [mid for mid in meeting.get("attendees", []) if mid in members and mid != "dmitry"]


def dispatch(meeting_id: str, base: str, ra, registry: dict, env: dict) -> int:
    meeting = _get(base, f"/api/council/{meeting_id}")
    if meeting.get("phase") not in ("созвано", "доклады"):
        print(f"[council] фаза «{meeting.get('phase')}» — диспут уже шёл, перезапуск не поддержан")
        return 2
    board = json.loads((COUNCIL_DIR / "board.json").read_text(encoding="utf-8"))
    members = {m["id"]: m for m in board.get("members", [])}
    speakers = _attendees_for(meeting, members)
    if not speakers:
        print("[council] некому докладывать — состав пуст")
        return 2
    agenda = meeting.get("agenda", [])

    print(f"[council] диспут {meeting_id}: {len(agenda)} пунктов, докладчики {len(speakers)}")
    _post(base, "/api/council/status", {"id": meeting_id, "phase": "доклады"})

    # Раунд 1 — доклады
    for idx, point in enumerate(agenda, start=1):
        for mid in speakers:
            member = members[mid]
            text = _chat(ra, registry, env, _system_prompt(member),
                         f"Пункт повестки №{idx}: {point['title']}\n\nТвой доклад по этому пункту.",
                         member["name"])
            if not text:
                continue
            _post(base, "/api/council/report", {"id": meeting_id, "agent": mid, "point": idx - 1, "round": 1, "text": text})
            print(f"[council] доклад: {member['name']} → пункт {idx}")

    # Раунд 2 — возражения (каждый читал всех)
    _post(base, "/api/council/status", {"id": meeting_id, "phase": "возражения"})
    meeting = _get(base, f"/api/council/{meeting_id}")
    for idx, point in enumerate(meeting.get("agenda", []), start=1):
        reports = "\n".join(
            f"— {members.get(r.get('agent'), {}).get('name', r.get('agent'))}: {r.get('text', '')}"
            for r in point.get("reports", [])
        )
        if not reports:
            continue
        for mid in speakers:
            member = members[mid]
            if any(o.get("agent") == mid for o in point.get("objections", [])):
                continue  # уже возражал (повторный прогон)
            user = (
                f"Пункт повестки №{idx}: {point['title']}\n\nДоклады коллег:\n{reports}\n\n"
                "Твоё возражение или поддержка (до 100 слов). Если согласен со всеми — скажи это прямо."
            )
            text = _chat(ra, registry, env, _system_prompt(member), user, member["name"])
            if not text:
                continue
            _post(base, "/api/council/report", {"id": meeting_id, "agent": mid, "point": idx - 1, "round": 2, "text": text})
            print(f"[council] возражение: {member['name']} → пункт {idx}")

    # Сводка модератора
    moderator = meeting.get("moderator") or "solomon"
    if moderator in members:
        _post(base, "/api/council/status", {"id": meeting_id, "phase": "сводка"})
        meeting = _get(base, f"/api/council/{meeting_id}")
        parts = []
        for idx, point in enumerate(meeting.get("agenda", []), start=1):
            rounds = "\n".join(f"  доклад {members.get(r.get('agent'), {}).get('name', '')}: {r.get('text', '')}"
                               for r in point.get("reports", []))
            rounds += "\n" + "\n".join(f"  возражение {members.get(o.get('agent'), {}).get('name', '')}: {o.get('text', '')}"
                                       for o in point.get("objections", []))
            parts.append(f"Пункт №{idx}: {point['title']}\n{rounds}")
        member = members[moderator]
        user = (
            "Ты модератор собрания. Вот протокол диспута по всем пунктам:\n\n" + "\n\n".join(parts) +
            "\n\nСведи совместные выводы правления по каждому пункту и отдельно отметь спорное — "
            "его решает CEO-0. До 220 слов."
        )
        text = _chat(ra, registry, env, _system_prompt(member), user, member["name"])
        if text:
            _post(base, "/api/council/summary", {"id": meeting_id, "agent": moderator, "text": text})
            print(f"[council] сводка модератора: {member['name']}")

    _post(base, "/api/council/status", {"id": meeting_id, "phase": "вердикты"})
    print("[council] диспут завершён — ждём вердикты CEO-0")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Диспут Правления (рука Бэрримова)")
    parser.add_argument("--id", dest="meeting_id", default=None, help="id собрания (2026-11-15-1)")
    parser.add_argument("--base", default="http://127.0.0.1:8765", help="локальный бэк Estate")
    args = parser.parse_args()

    if not args.meeting_id:
        board = _get(args.base, "/api/council")
        fresh = [m for m in board.get("meetings", []) if m.get("phase") in ("созвано", "доклады")]
        if not fresh:
            print("[council] свежих собраний нет — сначала «🔔 Собрать собрание» в зале")
            return 2
        args.meeting_id = fresh[0]["id"]

    ra = _load_run_agent()
    registry = json.loads((ROOT / "tools" / "agents" / "registry.json").read_text(encoding="utf-8"))
    env = ra.load_env(ra.ENV_PATH)
    key = env.get(registry["gateway"].get("key_env", ""), "")
    if not key:
        print("[council] в Workspace/.env нет ключа шлюза — диспут невозможен", file=sys.stderr)
        return 3
    return dispatch(args.meeting_id, args.base, ra, registry, env)


if __name__ == "__main__":
    sys.exit(main())
