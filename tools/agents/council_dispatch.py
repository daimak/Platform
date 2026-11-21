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
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN_AGENT_PATH = ROOT / "tools" / "agents" / "run_agent.py"
COUNCIL_DIR = ROOT / "Memory" / "Council"
PASSPORT_MAX = 8000  # знаков паспорта в системном промпте (21.11: паспорт режется — роль теряется)

REGULATION = (
    "Ты — участник Правления Estate (совет управляющих при CEO-0). Правила собрания: "
    "отвечай по-русски, кратко и по делу, без канцелярита и без ИИ-штампов; "
    "выступай от лица своей роли, опирайся на паспорт.\n"
    "ЖЕЛЕЗНО: цифры, файлы и URL брать ТОЛЬКО из раздела ФАКТУРА; чего там нет — "
    "пиши «нет данных», ничего не изобретай. Одно и то же предложение НЕ повторять — "
    "повторы это брак и такой доклад отбраковывается.\n"
    "Формат доклада: **Вывод** (1–2 строки) / **Цифры** (только из ФАКТУРЫ) / "
    "**Риски** / **Что нужно от CEO-0** — всего до 120 слов."
)

# Фактура платформы: реальные источники для докладов (21.11, после брака Холмса/
# Ватсона — агенту без данных нечего есть, кроме заголовка повестки, и он врёт).
FACT_MAX_PER_SOURCE = 900
FACT_SOURCES = [
    ("Токен-бюджет", ROOT / "Workspace" / "analytics" / "token-spend" / "token-budget.json"),
    ("FL-радар заказов, свежий дайджест", "glob:Workspace/analytics/research/fl-orders-radar/digest-*.md"),
    ("Outreach-волны", "glob:Workspace/sales-lane/outreach/wave*.md"),
]


def _fact_pack() -> str:
    """Срез живых данных платформы: только существующие файлы, кап на источник."""
    parts = []
    for label, src in FACT_SOURCES:
        if isinstance(src, Path):
            paths = [src] if src.is_file() else []
        else:  # "glob:путь"
            found = sorted(ROOT.glob(src[5:]), key=lambda p: p.stat().st_mtime, reverse=True)
            paths = found[:2]
        for p in paths:
            try:
                chunk = p.read_text(encoding="utf-8", errors="ignore").strip()[:FACT_MAX_PER_SOURCE]
            except OSError:
                continue
            if chunk:
                parts.append(f"— {label} ({p.name}):\n{chunk}")
    return "\n".join(parts) if parts else "(срезы недоступны — докладывай без цифр, честно помечая «нет данных»)"


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


def _validate(text: str) -> tuple[bool, str]:
    """Детектор брака генерации: петли повторов, словесный салат, выдуманные адреса."""
    t = text.strip()
    if len(t) < 40:
        return False, "слишком короткий ответ"
    lines = [ln.strip() for ln in t.splitlines() if ln.strip()]
    if len(lines) >= 6:
        top = max(set(lines), key=lambda s: lines.count(s))
        if lines.count(top) >= 4 and lines.count(top) / len(lines) >= 0.5:
            return False, "петля: одно предложение повторяется"
    words = t.split()
    n = 8
    if len(words) >= 2 * n:
        grams: dict[str, int] = {}
        for i in range(len(words) - n + 1):
            key = " ".join(words[i:i + n])
            grams[key] = grams.get(key, 0) + 1
        top_gram, cnt = max(grams.items(), key=lambda kv: kv[1])
        if cnt >= 4:
            return False, f"петля n-грамм x{cnt}"
    for url in re.findall(r"https?://[^\s)\]»\"]+", t):
        host = url.split("//", 1)[-1].split("/", 1)[0].lower()
        if re.match(r"^(www\.)?example\.(com|net|org)$", host) or host in {"test.com", "site.ru"}:
            return False, f"выдуманный адрес {host}"
    return True, ""


# Проверка фактов (21.11, после брака Хантера: выдуманный снапшот 2024-11-23 и
# «12 заказов» при пустой доске прошли бы петлевой валидатор — он видит только
# повторы и фейковые URL). Два жёстких правила:
#   1) упомянутый путь репозитория обязан существовать на диске;
#   2) «N <заказов/строк/...> в файле X» сверяется с реальной длиной JSON.
_KNOWN_TOPS = ("Workspace", "tools", "Memory", "Docs", "eVo", "Worlds", "logs", "agents")
_PATH_RE = re.compile(
    r"\b(?:" + "|".join(_KNOWN_TOPS) + r")(?:[\\/][\w.\u0400-\u04FF\u2010-\u2015*-]+)+[\\/]?",
)
_RESOLVE_PREFIXES = (ROOT, ROOT / "eVo", ROOT / "eVo" / "dashboard")
_COUNT_RE = re.compile(
    r"([\w./\\-]+\.(?:json|csv|md|log))"
    r"[^.\n]{0,100}?"
    r"(\d+(?:[.,]\d+)?)(?:\s+[\wа-яёА-ЯЁ-]+){0,2}\s*"
    r"(?:шт\.?|штук|запис\w*|строк\w*|заказ\w*|ваканс\w*|отклик\w*|адресат\w*|"
    r"групп\w*|фидов|обменник\w*|агент\w*|позиц\w*|файлов|объект\w*)"
)
_PLAN_RE = re.compile(
    r"планир|созда|предлага|добави|завед[её]|новый файл|запуст[иим]|провест[иь]|"
    r"провед[её]м|свест[иь]|свед[её]м|сгенерир|подготовить|подготовим|написать|"
    r"напишем|сделать|сделаем|нужен|нужна|прогнать|пройти|собрать|соберём",
    re.IGNORECASE,
)


def _resolve_path(candidate: str):
    """Путь кандидата → существующий Path или None. Globs (с *) — по родителю."""
    clean = candidate.replace("\\", "/").rstrip(".,;:)]»\"'").rstrip("/")
    if "*" in clean:
        parent = clean.split("*")[0].rsplit("/", 1)[0]
        return next((base / parent for base in _RESOLVE_PREFIXES
                     if (base / parent).exists()), None)
    return next((base / clean for base in _RESOLVE_PREFIXES
                 if (base / clean).exists()), None)


def _check_facts(text: str, known: str) -> tuple[bool, str]:
    """Галлюцинация фактов: несуществующие пути и противоречащие счётчики.

    known — фактура + повестка: путь, дословно упомянутый там, реален, не проверяем.
    """
    bad = []
    for match in _PATH_RE.finditer(text):
        path = match.group(0)
        if path.replace("\\", "/").rstrip(".,;:)]»\"'") in known:
            continue  # путь назван в фактуре/повестке — он настоящий
        # планы («создать Docs/plan.md», «запустить tools/x.py») — не галлюцинация
        before = text[max(0, match.start() - 80):match.start()]
        if _PLAN_RE.search(before):
            continue
        if _resolve_path(path) is None:
            bad.append(path)
    if bad:
        return False, "несуществующие пути: " + ", ".join(sorted(set(bad))[:5])
    for file_tok, claimed in _COUNT_RE.findall(text):
        path = _resolve_path(file_tok)
        if path is None or path.suffix != ".json":
            continue  # несуществующий файл поймает проверка путей; csv/md не парсим
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        except (OSError, ValueError):
            continue
        lens = ([len(data)] if isinstance(data, list)
                else [len(v) for v in data.values() if isinstance(v, list)]) if isinstance(data, (list, dict)) else []
        if lens and int(claimed.replace(" ", "")) not in lens:
            return False, f"в {file_tok} фактически {min(lens)}, заявлено {claimed}"
    return True, ""


def _chat_checked(ra, registry: dict, env: dict, system: str, user: str, who: str, facts: str | None = None) -> str | None:
    """Вызов шлюза с валидацией: брак → 1 ретрай → честная метка в протоколе."""
    prompt = user
    if facts:
        prompt = user + "\n\nФАКТУРА платформы (проверенные данные, цифры только отсюда):\n" + facts
    text = _chat(ra, registry, env, system, prompt, who)
    if not text:
        return None
    ok, reason = _validate(text)
    if ok:
        ok, reason = _check_facts(text, (facts or "") + "\n" + prompt)
    if ok:
        return text
    print(f"[council] брак у {who}: {reason} — ретрай", file=sys.stderr)
    retry = _chat(ra, registry, env, system,
                  prompt + f"\n\nВНИМАНИЕ: твой предыдущий ответ забракован ({reason}). "
                  "Ответь заново: коротко, без повторов предложений, только факты из ФАКТУРЫ. "
                  "Не выдумывай файлы и цифры — чего нет в ФАКТУРЕ, тому место «нет данных».",
                  who)
    ok2, reason2 = (False, "пустой ответ")
    if retry:
        ok2, reason2 = _validate(retry)
        if ok2:
            ok2, reason2 = _check_facts(retry, (facts or "") + "\n" + prompt)
    if ok2:
        return retry
    print(f"[council] {who}: брак после ретрая ({reason2}) — в протокол идёт метка", file=sys.stderr)
    return f"⚠ БРАК генерации ({reason2}) — доклад не состоялся."


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
    facts = _fact_pack()

    print(f"[council] диспут {meeting_id}: {len(agenda)} пунктов, докладчики {len(speakers)}, фактура {len(facts)} зн.")
    _post(base, "/api/council/status", {"id": meeting_id, "phase": "доклады"})

    # Раунд 1 — доклады
    for idx, point in enumerate(agenda, start=1):
        for mid in speakers:
            member = members[mid]
            text = _chat_checked(ra, registry, env, _system_prompt(member),
                                 f"Пункт повестки №{idx}: {point['title']}\n\nТвой доклад по этому пункту.",
                                 member["name"], facts)
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
            text = _chat_checked(ra, registry, env, _system_prompt(member), user, member["name"], facts)
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
        text = _chat_checked(ra, registry, env, _system_prompt(member), user, member["name"], None)
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
