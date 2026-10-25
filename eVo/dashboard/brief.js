window.EVO_BRIEF = {
  "generatedAt": "2026-10-25 19:15",
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
    "2026-10-25 | engineering journal Memory/Engineering/ (protocol E-000, full audit E-001–E-008, secrets fix S-3) | durable cross-session engineering context | —",
    "2026-10-25 | contour restructure: claude-chief-of-staff/ and Backup/ moved out of repo; graphify-out untracked; Interface/ removed; byte-identical duplicates dropped; Workspace/CURRENT.md renamed to notes-memory-design.md | one repository = one system | RFC-001",
    "2026-10-25 | ADR consolidated into Core/Architecture/ADR (ADR-001..005 + INDEX); dangling ADR refs fixed | single ADR numbering space | RFC-001",
    "2026-10-25 | RFC/ process created (README + RFC-001); D-002 branch model (develop / feature_X.Y.Z / release_X.Y.Z) | agreed change and release process | RFC-001",
    "2026-10-25 | audit report archived: Memory/Archive/Reports/Report-2026-10-25-audit.md | record E-008 deliverable | —"
  ],
  "git": {
    "branch": "feature_1.8.2",
    "lastCommit": "0e454e1 Barrymore Morning Brief MVP (R4 / INITIATIVE-0001, ADR-003 read-only): generator reads CURRENT/STATE/CHANGELOG/git into eVo/dashboard/brief.js; dashboard renders live brief with static fallback; journal E-010",
    "dirtyFiles": 3
  },
  "agent": {
    "model": "auto",
    "summary": "Дата отчёта: 2026‑08‑05.\nТекущая ветка репозитория: feature_1.8.2.\nПоследний коммит: 0e454e1 – \"Barrymore Morning Brief MVP (R4 / INITIATIVE‑0001, ADR‑003 read‑only)\".\nВ репозитории 3 грязных файла.\nИнформация о состоянии поместья, деньгах, задачах, рисках и возможностях в предоставленных источниках отсутствует.",
    "nextStep": "Запросить у пользователя недостающие данные о состоянии поместья, деньгах, задачах, рисках и возможностях для составления полноценного Morning Brief."
  }
};