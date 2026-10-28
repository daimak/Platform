// Снимок задач для плашки Бэрримора.
// Пока заполнен вручную (демо-данные на реальных пунктах плана); в будущем
// генератор (аналогично morning-brief) может собирать этот файл из
// Memory/Engineering/PLAN.md и Memory/Context/.
// Формат: { generatedAt, urgent: [{title, source}], regular: [{title, source}] }
window.EVO_TASKS = {
  generatedAt: "2026-10-25T12:00:00",
  urgent: [
    { title: "Ротация ключей LangSmith/FreeLLMAPI", source: "S-1" },
    { title: "Мастер-пароль KeePassXC + бэкап хранилища", source: "S-4" }
  ],
  regular: [
    { title: "Актуализация Memory/Context/CURRENT.md", source: "R3" },
    { title: "Слияние веток по D-002", source: "R9" },
    { title: "Чистка пустых заглушек (locales, Carrier, Timeline)", source: "R7" }
  ]
};
