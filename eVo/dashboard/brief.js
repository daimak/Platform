window.EVO_BRIEF = {
  "generatedAt": "2026-10-27 13:59",
  "sources": [
    "Memory/Context/CURRENT.md",
    "Memory/Engineering/STATE.md",
    "CHANGELOG.md",
    "git"
  ],
  "current": {
    "date": "2026-08-05",
    "nextAction": "Создать Morning Brief:\nкнопка Barrymore →\nутренний доклад:\n- состояние поместья\n- деньги\n- задачи\n- риски\n- возможности"
  },
  "state": {
    "nextStep": "По указанию пользователя: слияние веток по D-002 (после проверки) либо продуктовые шаги (R4 — Morning Brief read-only MVP)."
  },
  "changes": [
    "2026-10-25 | Barrymore Morning Brief: deterministic generator + autonomous LLM agent (local FreeLLMAPI gateway, stdlib-only, ADR-003/004 compliant) | give Barrymore its own brains | —",
    "2026-10-25 | Barrymore UX: map beacon removed, painted plaque is now the clickable entry; unread \"Morning Brief\" link under the plaque; user guide Docs/Barrymore.md | user request | —",
    "2026-10-25 | Barrymore plaque becomes pure HTML over clean art: background swapped to Clear_main (painted text gone), portrait barrymore.png as separate layer, live greeting + task counter (tasks.js), \"Review\" link, geometry on CSS variables | user request | —",
    "2026-10-26 | map layout: full-width frame with atmospheric blurred backdrop (no black bars, nothing cropped, plaque stays on-screen on 16:10); agent passports introduced in Memory/Agents (Barrymore partial-active, Solomon & Holmes drafts aligned with ADR-003/004) | user request + co-worked with second AI | —",
    "2026-10-26 | new island \"Holmes Study\" on the map (beacon + modal + RU/EN), sidebars toggle; all 10 modals verified clickable | co-worked with second AI | —"
  ],
  "git": {
    "branch": "feature_1.8.2",
    "lastCommit": "fa06f26 Move accidental ~/the-agency folder into tools/the-agency",
    "dirtyFiles": 6
  },
  "agent": {
    "model": "auto",
    "summary": "Доброе утро, Дмитрий. Позвольте представить утренний доклад. Обращаю ваше внимание, что системные данные датированы 5 августа 2026 года, что может указывать на их устаревание относительно даты генерации снимка (27 октября 2026 года). В репозитории активна ветка feature_1.8.2, зафиксировано 6 измененных файлов. Из недавних изменений: обновлен мой интерфейс, добавлен остров «Кабинет Холмса» и настроен автономный агент для генерации докладов. Сведения о состоянии поместья, финансах и рисках в предоставленных источниках отсутствуют. Нам необходимо определиться с дальнейшими шагами.",
    "nextStep": "Проверить изменения в ветке feature_1.8.2 для принятия решения о слиянии по задаче D-002 или переходе к шагам R4 (Morning Brief MVP)."
  }
};