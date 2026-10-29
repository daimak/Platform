const ENGINE_ISLANDS = {
  "engine-core": {
    icon: "🏰",
    title: "Core Citadel",
    subtitle: "Архитектура, принципы и решения, на которых держится Platform.",
    sections: [
      {
        title: "Назначение",
        text: "Центр инженерной карты: здесь задаются границы модулей, архитектурные правила и направление развития eVo. Для поручений Hunter откройте его личный кабинет кнопкой ниже."
      },
      {
        title: "Первые ориентиры",
        items: [
          "Architecture Decision Records — почему система устроена именно так.",
          "Platform core — принципы, контракты и общий словарь проекта.",
          "Estate Command Center — карта состояния для ежедневной работы."
        ]
      },
    ],
    links: [
      { href: "index.html", icon: "🏰", label: "Открыть Estate Command Center" },
      { island: "hunter", icon: "🎯", label: "Открыть личный кабинет Hunter" },
      { href: "index.html?island=aiSandbox", icon: "🔮", label: "Открыть AI Sandbox на Estate" },
      { href: "maelstorm.html", icon: "🌀", label: "Перейти к исследовательским островам" }
    ]
  },
  hunter: {
    icon: "🎯",
    title: "Hunter — личный кабинет",
    subtitle: "Флигель Core Citadel · поиск работы и быстрых источников дохода для всего архипелага.",
    sections: [
      {
        title: "Главный приоритет",
        text: "Находить реалистичные способы получить доход как можно быстрее. В первую очередь — вакансии с высокой вероятностью быстрого найма; параллельно — заказы и другие оплачиваемые возможности с коротким сроком до первой выплаты."
      },
      {
        title: "Рабочие направления",
        items: [
          "Работа по найму: вакансии, где требования совпадают с опытом, а отбор и выход на работу могут пройти быстро.",
          "Быстрый доход: разовые заказы, подработки и услуги с понятными условиями и сроком оплаты.",
          "Другие источники заработка: отдельная группа для путей с более высокой сложностью или долгим стартом."
        ]
      },
      {
        title: "Как будут устроены находки",
        items: [
          "Для каждой возможности: категория, источник и дата последней проверки.",
          "Скорость: ожидаемый срок найма или срок до первой выплаты.",
          "Условия: сложность входа, необходимые навыки и подтверждённая сумма или диапазон оплаты.",
          "Ранжирование: сначала скорость и реалистичность получения денег, затем соответствие навыкам, сложность и надёжность источника."
        ]
      },
      {
        title: "Граница текущей версии",
        text: "Поручения сохраняются в локальную очередь Hunter. Автономный исполнитель, сбор вакансий из внешних источников и автоматическая актуализация пока не подключены; реальные предложения не подменяются примерами."
      }
    ],
    links: [
      { href: "index.html?island=aiSandbox", icon: "🔮", label: "Перейти к AI Sandbox на Estate" }
    ]
  },
  forge: {
    icon: "⚒️",
    title: "Builder's Forge",
    subtitle: "Рабочие инструменты, автоматизация и превращение идей в работающий код.",
    sections: [
      {
        title: "Назначение",
        text: "Кузница собирает инструменты разработки, локальные сценарии, поддержку агентов и проверяемые операции."
      },
      {
        title: "Первая практика",
        items: [
          "Каждую автоматизацию оформлять как ограниченный, повторяемый инструмент.",
          "Показывать результат выполнения явно; не подменять отсутствие данных успехом.",
          "Сохранять историю изменений и проверок рядом с инженерным контекстом."
        ]
      }
    ],
    links: [
      { href: "index.html", icon: "🧭", label: "Вернуться к карте Estate" }
    ]
  },
  harbor: {
    icon: "⚓",
    title: "Integration Harbor",
    subtitle: "Шлюзы, API и контролируемый обмен данными с внешними сервисами.",
    sections: [
      {
        title: "Назначение",
        text: "Гавань соединяет локальную платформу с внешними сервисами, сохраняя понятные границы доступа и происхождение данных."
      },
      {
        title: "Принцип связи",
        items: [
          "У каждого соединения есть явный владелец, цель и область разрешений.",
          "Секреты остаются в локальном хранилище и не попадают в журнал.",
          "Если сервис не сообщает usage или стоимость, система показывает «нет данных»."
        ]
      }
    ],
    links: [
      { href: "ai-usage.html", icon: "📊", label: "Посмотреть учёт AI-сервисов" }
    ]
  },
  lab: {
    icon: "🧪",
    title: "Test & Quality Reef",
    subtitle: "Проверки, наблюдаемость и спокойная уверенность в изменениях.",
    sections: [
      {
        title: "Назначение",
        text: "Риф качества защищает систему от хрупких изменений: здесь живут синтаксические проверки, тесты сценариев и контроль состояния."
      },
      {
        title: "Путь проверки",
        items: [
          "Сначала самый узкий тест, который проверяет требование.",
          "Затем интеграционная проверка важных границ.",
          "В итогах отдельно сообщать, что проверено и что осталось неизвестным."
        ]
      }
    ],
    links: [
      { href: "index.html", icon: "🧭", label: "Вернуться к карте Estate" }
    ]
  },
  launch: {
    icon: "🚀",
    title: "Release Beacon",
    subtitle: "Версии, заметки к выпуску и прозрачная доставка изменений.",
    sections: [
      {
        title: "Назначение",
        text: "Маяк релизов связывает проверенное состояние кода с понятной версией и коротким рассказом о том, что изменилось."
      },
      {
        title: "Релизный ритуал",
        items: [
          "Проверить branch и рабочее дерево.",
          "Обновить единый маркер версии и release notes.",
          "Зафиксировать только согласованные файлы; публикация — отдельное действие."
        ]
      }
    ],
    links: [
      { href: "index.html", icon: "🏰", label: "Вернуться к карте Estate" }
    ]
  },
  observatory: {
    icon: "🔮",
    title: "AI Observatory",
    subtitle: "Модели, квоты и стоимость AI — только по подтверждённым данным.",
    sections: [
      {
        title: "Назначение",
        text: "Обсерватория наблюдает за AI-сервисами и отделяет подписочные лимиты от тарифицируемых API-вызовов."
      },
      {
        title: "Что уже можно проверить",
        items: [
          "Ручные снимки Copilot, ChatGPT и других кабинетов.",
          "Записанные локальные вызовы, если шлюз вернул счётчики токенов.",
          "Неизвестные значения остаются неизвестными; догадок о расходах нет."
        ]
      }
    ],
    links: [
      { href: "ai-usage.html", icon: "📊", label: "Открыть AI Usage Ledger" },
      { href: "index.html", icon: "🏰", label: "Вернуться к Estate Command Center" }
    ]
  }
};

const engineBackdrop = document.getElementById("engine-console-backdrop");
const engineTitle = document.getElementById("engine-console-title");
const engineSubtitle = document.getElementById("engine-console-subtitle");
const engineKicker = document.getElementById("engine-console-kicker");
const engineBody = document.getElementById("engine-console-body");
const closeEngineConsole = document.getElementById("engine-console-close");
const backEngineConsole = document.getElementById("engine-console-back");
let previousFocus = null;

function openEngineIsland(islandId) {
  const island = ENGINE_ISLANDS[islandId];
  if (!island) return;

  if (!engineBody.contains(document.activeElement)) {
    previousFocus = document.activeElement;
  }
  engineKicker.textContent = `${island.icon}  ENGINE CORE ATOLL`;
  engineTitle.textContent = island.title;
  engineSubtitle.textContent = island.subtitle;
  engineBody.replaceChildren();

  for (const section of island.sections) {
    const card = document.createElement("section");
    card.className = "engine-console-card";

    const heading = document.createElement("h2");
    heading.textContent = section.title;
    card.append(heading);

    if (section.text) {
      const paragraph = document.createElement("p");
      paragraph.textContent = section.text;
      card.append(paragraph);
    }

    if (section.items) {
      const list = document.createElement("ul");
      for (const item of section.items) {
        const listItem = document.createElement("li");
        listItem.textContent = item;
        list.append(listItem);
      }
      card.append(list);
    }
    engineBody.append(card);
  }

  if (islandId === "hunter") {
    engineBody.append(buildHunterAssignmentsCard());
  }

  const linkCard = document.createElement("nav");
  linkCard.className = "engine-console-links";
  linkCard.setAttribute("aria-label", "Переходы по архипелагу");
  for (const item of island.links) {
    const link = item.island
      ? document.createElement("button")
      : document.createElement("a");
    if (item.island) {
      link.type = "button";
      link.addEventListener("click", () => openEngineIsland(item.island));
    } else {
      link.href = item.href;
    }
    link.className = "engine-console-link";
    if (item.island === "hunter") link.classList.add("engine-console-link--hunter");
    link.textContent = `${item.icon} ${item.label}`;
    linkCard.append(link);
  }
  engineBody.append(linkCard);

  engineBackdrop.hidden = false;
  closeEngineConsole.focus();
}

function buildHunterAssignmentsCard() {
  const card = document.createElement("section");
  card.className = "engine-console-card";

  const heading = document.createElement("h2");
  heading.textContent = "Поставить поручение Hunter";
  card.append(heading);

  const form = document.createElement("form");
  form.className = "hunter-assignment-form";

  const categoryLabel = document.createElement("label");
  categoryLabel.textContent = "Направление";
  const category = document.createElement("select");
  category.name = "category";
  category.required = true;
  for (const [value, label] of [
    ["employment", "Работа по найму"],
    ["quick-income", "Быстрый заработок"],
    ["organize", "Систематизация и актуализация"],
    ["other", "Другое"]
  ]) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    category.append(option);
  }
  categoryLabel.append(category);
  form.append(categoryLabel);

  const titleLabel = document.createElement("label");
  titleLabel.textContent = "Коротко: что найти или сделать";
  const title = document.createElement("input");
  title.name = "title";
  title.maxLength = 120;
  title.required = true;
  title.placeholder = "Например: вакансии с быстрым выходом";
  titleLabel.append(title);
  form.append(titleLabel);

  const detailsLabel = document.createElement("label");
  detailsLabel.textContent = "Уточнения и ограничения";
  const details = document.createElement("textarea");
  details.name = "details";
  details.maxLength = 3000;
  details.placeholder = "Навыки, условия, география, желаемый срок и другие критерии";
  detailsLabel.append(details);
  form.append(detailsLabel);

  const status = document.createElement("p");
  status.className = "hunter-assignment-status";
  status.setAttribute("role", "status");

  const submit = document.createElement("button");
  submit.className = "btn-action-primary";
  submit.type = "submit";
  submit.textContent = "Сохранить поручение";
  form.append(submit, status);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    status.textContent = "";
    status.classList.remove("is-error");
    submit.disabled = true;
    try {
      const response = await fetch("/api/hunter/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          category: category.value,
          title: title.value,
          details: details.value
        })
      });
      const payload = await readHunterResponse(response);
      title.value = "";
      details.value = "";
      status.textContent = "Поручение сохранено в локальной очереди. Исполнитель пока не подключён.";
      renderHunterQueue(queueList, payload.tasks);
    } catch (error) {
      status.classList.add("is-error");
      status.textContent = error.message || "Не удалось связаться с локальным сервером.";
    } finally {
      submit.disabled = false;
    }
  });

  card.append(form);
  const queueHeading = document.createElement("h2");
  queueHeading.textContent = "Открытые поручения";
  card.append(queueHeading);
  const queueList = document.createElement("ul");
  queueList.className = "hunter-task-list";
  card.append(queueList);
  loadHunterQueue(status, queueList);
  return card;
}

async function loadHunterQueue(status, list) {
  try {
    const response = await fetch("/api/hunter/tasks", { cache: "no-store" });
    const payload = await readHunterResponse(response);
    renderHunterQueue(list, payload.tasks);
  } catch (error) {
    const message = error.message || "Не удалось загрузить очередь Hunter.";
    if (status) {
      status.classList.add("is-error");
      status.textContent = message;
    } else {
      renderHunterQueueError(list, message);
    }
  }
}

async function readHunterResponse(response) {
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const message = response.status === 403
      ? "Сервер отклонил запрос. Откройте дашборд через локальный HTTP-сервер, а не напрямую из файла."
      : payload?.error || `Локальный сервер Hunter ответил с ошибкой (${response.status}).`;
    throw new Error(message);
  }
  if (!payload || !Array.isArray(payload.tasks)) {
    throw new Error("Сервер Hunter вернул ответ неожиданного формата.");
  }
  return payload;
}

function renderHunterQueue(list, tasks) {
  list.replaceChildren();
  if (!tasks.length) {
    const empty = document.createElement("li");
    empty.className = "hunter-empty-state";
    empty.textContent = "Очередь пуста. Источники вакансий и автоматический поиск пока не подключены.";
    list.append(empty);
    return;
  }

  for (const task of tasks) {
    const item = document.createElement("li");
    item.className = "hunter-task-item";
    const meta = document.createElement("div");
    meta.className = "hunter-task-meta";
    meta.textContent = `${task.category_label} · принято ${new Date(task.created_at).toLocaleString()}`;
    const title = document.createElement("h3");
    title.textContent = task.title;
    item.append(meta, title);
    if (task.details) {
      const details = document.createElement("p");
      details.textContent = task.details;
      item.append(details);
    }
    list.append(item);
  }
}

function renderHunterQueueError(list, message) {
  list.replaceChildren();
  const error = document.createElement("li");
  error.className = "hunter-empty-state";
  error.textContent = `Очередь Hunter недоступна: ${message}`;
  list.append(error);
}

function hideEngineConsole() {
  engineBackdrop.hidden = true;
  if (previousFocus instanceof HTMLElement) previousFocus.focus();
}

for (const hotspot of document.querySelectorAll(".engine-island")) {
  hotspot.addEventListener("click", () => openEngineIsland(hotspot.dataset.island));
}

closeEngineConsole.addEventListener("click", hideEngineConsole);
backEngineConsole.addEventListener("click", hideEngineConsole);
engineBackdrop.addEventListener("click", (event) => {
  if (event.target === engineBackdrop) hideEngineConsole();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !engineBackdrop.hidden) hideEngineConsole();
});
