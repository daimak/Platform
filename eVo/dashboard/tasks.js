// Снимок задач для плашки Бэрримора.
// Пока заполнен вручную (демо-данные на реальных пунктах плана); в будущем
// генератор (аналогично morning-brief) может собирать этот файл из
// Memory/Engineering/PLAN.md и Memory/Context/.
// Формат: { generatedAt, urgent: [{title, source}], regular: [{title, source}] }
window.EVO_TASKS = {
  generatedAt: "2026-10-25T12:00:00",
  urgent: [
    { id: "rotate-langsmith-freellmapi", title: "Ротация ключей LangSmith/FreeLLMAPI", source: "S-1" },
    { id: "keepass-master-password-backup", title: "Мастер-пароль KeePassXC + бэкап хранилища", source: "S-4" }
  ],
  regular: [
    { id: "update-current-context", title: "Актуализация Memory/Context/CURRENT.md", source: "R3" },
    { id: "merge-branches-d002", title: "Слияние веток по D-002", source: "R9" },
    { id: "clean-empty-stubs", title: "Чистка пустых заглушек (locales, Carrier, Timeline)", source: "R7" }
  ]
};
