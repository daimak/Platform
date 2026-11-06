#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Higgsfield pilot для Platform Evo.

Назначение:
  (a) auth-check — проверка аутентификации и чтение профиля/статуса аккаунта;
  (b) submit-скелет кадра Soul 2 — собирает реальный payload, но исполнение
      генерации возможно ТОЛЬКО при:
        1. установленной переменной окружения HIGGSFIELD_API_KEY, и
        2. явном флаге --live (санкция на платный вызов).

Без ключа скрипт работает в dry-run: документирует ТОЧНОЕ поведение
(локальные ошибки SDK/HTTP-кода ответа) и ничего не платит.

Ключ НИКОГДА не выводится и не логируется. Читается из окружения;
в Workspace/.env не заходим (загрузку .env делает вызывающий, не этот скрипт).

Запуск:
  python pilot.py              # dry-run: auth-check без ключа + скелет payload
  python pilot.py --live       # ПОСЛЕ санкции: реальные вызовы (ключ должен быть в env)

Требования: pip install higgsfield-client  (venv: .venv/Scripts/python.exe)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone

BASE_URL = "https://api.higgsfield.ai"

# Имя приложения (путь в API) для Soul 2 standard.
# Источник: docs.higgsfield.ai (страница SOUL V2) и openapi.json docs.
SOUL_V2_STANDARD_APP = "higgsfield-ai/soul/v2/standard"
# В supplementary openapi.json также есть старый стандарт:
SOUL_STANDARD_APP = "higgsfield-ai/soul/standard"

# SDK-имена переменных окружения (higgsfield_client.auth.get_credential_key):
#   HF_KEY                = "<api_key_id>:<api_key_secret>"
#   HF_API_KEY + HF_API_SECRET = пара отдельно
# Платформенное имя Platform Evo: HIGGSFIELD_API_KEY = "<id>:<secret>" (одно значение).

REAL_PAYMENT_SANCTIONED = False  # Меняется ТОЛЬКО явной санкцией Sovereign, не кодом.


def log(msg: str) -> None:
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {msg}", file=sys.stderr)


def redact(value: str) -> str:
    """Показать форму ключа, не раскрывая значения."""
    if not value:
        return "(пусто)"
    if ":" in value:
        left, right = value.split(":", 1)
        return f"{left[:3]}***:{right[:3]}*** (id:secret, {len(left)}+{len(right)} символов)"
    return f"{value[:3]}*** ({len(value)} символов)"


def check_env() -> dict:
    """Что видно в окружении (только наличие/форма, никогда значения)."""
    return {
        "HIGGSFIELD_API_KEY": redact(os.getenv("HIGGSFIELD_API_KEY", "")),
        "HF_KEY": redact(os.getenv("HF_KEY", "")),
        "HF_API_KEY_set": bool(os.getenv("HF_API_KEY")),
        "HF_API_SECRET_set": bool(os.getenv("HF_API_SECRET")),
    }


def build_soul2_payload() -> dict:
    """Скелет реального payload одного кадра Soul 2 (standard).

    Схема сверена с живыми доками 2026-11-06 (models/soul-2/generate.md):
    prompt (required); batch_size 1|4 (НЕ num_images); resolution 720p|1080p
    (2K/4K остались у старого Soul v1 /higgsfield-ai/soul/standard);
    aspect_ratio default 1:1, enum 9:16,16:9,4:3,3:4,1:1,2:3,3:2;
    опционально: enhance_prompt, custom_reference_id(+strength), style_id,
    style_strength (сейчас не влияет), seed 1..1000000.
    """
    return {
        "prompt": (
            "Editorial fashion photo, a mid-30s woman in a charcoal wool coat, "
            "standing on a rain-wet Tokyo street at dusk, neon reflections, "
            "shallow depth of field, 85mm lens, cinematic color grade"
        ),
        "batch_size": 1,
        "resolution": "1080p",
        "aspect_ratio": "3:4",
        "enhance_prompt": False,
    }


def auth_check_sdk() -> dict:
    """Auth-check через официальный SDK. Без ключа SDK падает ЛОКАЛЬНО."""
    try:
        import higgsfield_client
        import higgsfield_client.auth as hf_auth
    except ImportError as e:
        return {"ok": False, "stage": "import", "error": f"{type(e).__name__}: {e}"}

    # 1) Локальная проверка наличия креденшелов в переменных SDK.
    try:
        hf_auth.get_credential_key()
        creds = "SDK-переменные найдены (HF_KEY или HF_API_KEY+HF_API_SECRET)"
        creds_ok = True
    except Exception as e:
        creds = f"{type(e).__name__}: {e}"
        creds_ok = False

    return {
        "ok": creds_ok,
        "stage": "credentials-local-check",
        "sdk_version": getattr(higgsfield_client, "__version__", "0.2.0 (не экспортируется)"),
        "credentials": creds,
    }


def auth_check_http_raw() -> dict:
    """Auth-check сырым HTTP.

    Два случая:
      * ключа нет -> отправляем запрос БЕЗ Authorization и фиксируем точный
        ответ сервера (ожидаем 401). Такой вызов не может запустить генерацию
        и не стоит денег.
      * ключ есть (и --live) -> GET /requests/{несуществующий uuid}/status с
        заголовком Authorization: Key ... : корректная аутентификация даёт 404
        (request не существует), неверная — 401. Это БЕСПЛАТНЫЙ вызов чтения.
    """
    import urllib.error
    import urllib.request

    key = os.getenv("HIGGSFIELD_API_KEY", "").strip()
    probe_url = f"{BASE_URL}/requests/{uuid.uuid4()}/status"

    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if key:
        headers["Authorization"] = f"Key {key}"

    req = urllib.request.Request(probe_url, headers=headers, method="GET")
    result = {"probe_url": probe_url, "auth_header": "present" if key else "absent"}
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", "replace")
            result.update({"http_status": resp.status, "body": body[:500]})
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        result.update({"http_status": e.code, "reason": e.reason, "body": body[:500]})
    except Exception as e:
        result.update({"http_status": None, "error": f"{type(e).__name__}: {e}"})
    return result


def submit_soul2_live() -> dict:
    """LIVE: один платный submit Soul 2. Вызывается только при --live и ключе."""
    import higgsfield_client

    payload = build_soul2_payload()
    log(f"LIVE submit -> POST {BASE_URL}/{SOUL_V2_STANDARD_APP} payload={json.dumps(payload, ensure_ascii=False)}")
    controller = higgsfield_client.submit(SOUL_V2_STANDARD_APP, arguments=payload)
    log(f"request_id={controller.request_id}; опрашиваю статус раз в 2с (таймаут 300с)...")
    import time
    deadline = time.monotonic() + 300
    last = None
    while time.monotonic() < deadline:
        st = controller.status()
        if type(st).__name__ != last:
            log(f"статус: {type(st).__name__}")
            last = type(st).__name__
        if isinstance(st, higgsfield_client.DONE_STATUSES):
            break
        time.sleep(2)
    result = controller.get()
    return {"request_id": controller.request_id, "result": result}


def main() -> int:
    ap = argparse.ArgumentParser(description="Higgsfield pilot (Platform Evo)")
    ap.add_argument("--live", action="store_true",
                    help="разрешить реальный платный вызов (только по санкции Sovereign)")
    args = ap.parse_args()

    report = {"run_mode": "LIVE" if args.live else "DRY-RUN",
              "utc": datetime.now(timezone.utc).isoformat()}

    print("=" * 72)
    print("HIGGSFIELD PILOT — Platform Evo — режим:", report["run_mode"])
    print("=" * 72)

    print("\n--- 0. Окружение (значения секретов не выводятся) ---")
    env = check_env()
    print(json.dumps(env, ensure_ascii=False, indent=2))
    report["env"] = env

    has_platform_key = bool(os.getenv("HIGGSFIELD_API_KEY", "").strip())
    has_sdk_creds = bool(os.getenv("HF_KEY") or
                         (os.getenv("HF_API_KEY") and os.getenv("HF_API_SECRET")))

    print("\n--- 1. Auth-check через SDK (локальная проверка кредов) ---")
    sdk_check = auth_check_sdk()
    print(json.dumps(sdk_check, ensure_ascii=False, indent=2))
    report["sdk_check"] = sdk_check

    print("\n--- 2. Auth-check сырым HTTP (точное поведение сервера) ---")
    if not has_platform_key and not has_sdk_creds:
        print("Ключа нет -> проба БЕЗ Authorization (не может запустить генерацию, бесплатна).")
    raw = auth_check_http_raw()
    print(json.dumps(raw, ensure_ascii=False, indent=2))
    report["raw_auth_check"] = raw

    print("\n--- 3. Скелет submit Soul 2 (payload собран, НЕ отправлен) ---")
    payload = build_soul2_payload()
    print(f"POST {BASE_URL}/{SOUL_V2_STANDARD_APP}")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("Смета: 1 кадр x $0.0032 (Soul 2, стартовый тариф, подтверждено блогом API) = $0.0032"
          " (~0,26 руб по курсу ~81); точную цену конфига 1080p даст POST /estimate/higgsfield-ai/soul/v2/standard.")
    report["payload"] = payload

    live_allowed = args.live and (has_platform_key or has_sdk_creds)
    if args.live and not (has_platform_key or has_sdk_creds):
        print("\nLIVE запрошен, но ключа нет -> генерация НЕ выполняется (dry-run).")
    if live_allowed:
        if not REAL_PAYMENT_SANCTIONED:
            print("\nПлатная генерация заблокирована в коде (REAL_PAYMENT_SANCTIONED=False). "
                  "Нужна явная санкция Sovereign: правка константы ИЛИ отдельный флаг санкции.")
        else:
            print("\n--- 4. LIVE: один платный submit Soul 2 ---")
            try:
                live = submit_soul2_live()
                print(json.dumps(live, ensure_ascii=False, indent=2)[:3000])
                report["live"] = live
            except Exception as e:
                print(f"LIVE ошибка: {type(e).__name__}: {e}")
                report["live_error"] = f"{type(e).__name__}: {e}"
    else:
        print("\n--- 4. LIVE-генерация: не выполнялась (нет ключа/не запрошена) ---")

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "pilot-report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("\nОтчёт сохранён: pilot-report.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
