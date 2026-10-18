/**
 * Platform Evo (eVo) — Command Center Logic (v0.2.0)
 * Manages language switching, Steward Barrymore interactions,
 * Level 2 ↔ Level 3 (Workspace) spatial transitions, and interactive tasks.
 */

console.log("eVo Command Center v0.2 initialized — Estate Level 2 Active");

// Функция обновления языковых строк во всем интерфейсе
function updateLanguage() {
  if (typeof LANG === 'undefined') return;

  const lang = LANG[currentLanguage] || LANG.ru;

  const setText = (id, text) => {
    const el = document.getElementById(id);
    if (el && text !== undefined) {
      el.textContent = text;
    }
  };

  // Верхняя панель
  setText("command-center-title", lang.commandCenter);
  setText("system-subtitle", lang.systemSubtitle);
  setText("platform-alive-text", lang.platformAlive);
  setText("heartbeat-text", lang.heartbeat);

  // Стюард Бэрримор
  setText("barrymore-name-text", lang.barrymoreTitle);
  setText("barrymore-status-text", lang.barrymoreStatus);
  setText("barrymore-briefing-quote", lang.barrymoreBriefing);

  // Hero & Переход в Workspace
  setText("current-state-label", lang.currentStateLabel);
  setText("current-title", lang.currentTitle);
  setText("current-text", lang.currentText);
  setText("to-workspace-text", lang.toWorkspaceBtn);

  // Узел 1: Git
  setText("git-state-label", lang.gitStateLabel);
  setText("branch-title", lang.branchTitle);
  setText("git-status-line", lang.gitClean);
  setText("latest-commit-label", lang.latestCommitLabel);
  setText("commit-hash", lang.commitHash);

  // Узел 2: Точка внимания & Агенты
  setText("attention-label", lang.attentionLabel);
  setText("attention-title", lang.attentionTitle);
  setText("attention-status-line", lang.statusBuilding);
  setText("attention-desc", lang.attentionDesc);
  setText("agent-barrymore-text", lang.agentBarrymore);
  setText("agent-context-text", lang.agentContext);
  setText("agent-memory-text", lang.agentMemory);

  // Узел 3: Рычаги & Задачи
  setText("leverage-label", lang.leverageLabel);
  setText("leverage-title", lang.leverageTitle);
  setText("task-text-1", lang.taskVisualState);
  setText("task-text-2", lang.taskMemory);
  setText("task-text-3", lang.taskSystemMap);
  setText("btn-add-task", lang.addTaskBtn);
  const inputTask = document.getElementById("input-new-task");
  if (inputTask) inputTask.placeholder = lang.addTaskPlaceholder;

  // Узел 4: Эволюция & Уровни Estate
  setText("evolution-label", lang.evolutionLabel);
  setText("evolution-title", lang.evolutionTitle);
  setText("evolution-flow", lang.evolutionFlow);
  setText("estate-level-1-text", lang.estateLevel1);
  setText("estate-level-2-text", lang.estateLevel2);
  setText("estate-level-3-text", lang.estateLevel3);

  // Модальный рабочий кабинет (Уровень 3)
  setText("workspace-title-text", lang.workspaceTitle);
  setText("workspace-sub-text", lang.workspaceSubtitle);
  setText("btn-close-workspace", lang.backToCommandCenter);
  setText("active-task-section-label", lang.activeTaskSection);
  setText("active-task-name", lang.taskName);
  setText("active-task-desc", lang.taskDesc);
  setText("checklist-title-label", lang.checklistTitle);
  setText("check-1-text", lang.check1);
  setText("check-2-text", lang.check2);
  setText("check-3-text", lang.check3);
  setText("status-select-label", lang.statusSelectorLabel);
  setText("opt-building", lang.statusBuildingOpt);
  setText("opt-operational", lang.statusOperationalOpt);
  setText("btn-save-workspace", lang.saveTaskBtn);

  // Обновление подсветки кнопок языка
  const btnRu = document.getElementById("lang-ru");
  const btnEn = document.getElementById("lang-en");
  if (btnRu && btnEn) {
    btnRu.classList.toggle("active", currentLanguage === "ru");
    btnEn.classList.toggle("active", currentLanguage === "en");
  }
}

// Инициализация обработчиков событий
document.addEventListener("DOMContentLoaded", () => {
  // Кнопки переключения языка
  const btnRu = document.getElementById("lang-ru");
  const btnEn = document.getElementById("lang-en");

  if (btnRu) {
    btnRu.addEventListener("click", () => {
      currentLanguage = "ru";
      localStorage.setItem("evo_language", "ru");
      updateLanguage();
    });
  }

  if (btnEn) {
    btnEn.addEventListener("click", () => {
      currentLanguage = "en";
      localStorage.setItem("evo_language", "en");
      updateLanguage();
    });
  }

  // Интерактивный шлюз Стюарда Бэрримора
  const barrymoreNexus = document.getElementById("barrymore-nexus");
  if (barrymoreNexus) {
    barrymoreNexus.addEventListener("click", (e) => {
      // Клик по Бэрримору активирует шлюз перехода в кабинет
      openWorkspace();
    });
  }

  // Переход в Рабочий кабинет (Level 3 Workspace)
  const btnOpenWorkspace = document.getElementById("btn-open-workspace");
  const btnCloseWorkspace = document.getElementById("btn-close-workspace");
  const workspaceModal = document.getElementById("workspace-modal");
  const btnSaveWorkspace = document.getElementById("btn-save-workspace");

  function openWorkspace() {
    if (workspaceModal) workspaceModal.classList.add("open");
  }

  function closeWorkspace() {
    if (workspaceModal) workspaceModal.classList.remove("open");
  }

  if (btnOpenWorkspace) btnOpenWorkspace.addEventListener("click", openWorkspace);
  if (btnCloseWorkspace) btnCloseWorkspace.addEventListener("click", closeWorkspace);
  if (btnSaveWorkspace) {
    btnSaveWorkspace.addEventListener("click", () => {
      closeWorkspace();
    });
  }

  // Закрытие по клику вне контента или Escape
  if (workspaceModal) {
    workspaceModal.addEventListener("click", (e) => {
      if (e.target === workspaceModal) closeWorkspace();
    });
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && workspaceModal && workspaceModal.classList.contains("open")) {
      closeWorkspace();
    }
  });

  // Интерактивные задачи (Next Leverage)
  const taskList = document.getElementById("task-list");
  if (taskList) {
    taskList.addEventListener("click", (e) => {
      const taskItem = e.target.closest(".task-item");
      if (!taskItem) return;

      taskItem.classList.toggle("completed");
      const checkbox = taskItem.querySelector(".task-checkbox");
      if (checkbox) {
        checkbox.textContent = taskItem.classList.contains("completed") ? "✓" : "";
      }
    });
  }

  // Добавление новой задачи
  const btnAddTask = document.getElementById("btn-add-task");
  const inputNewTask = document.getElementById("input-new-task");

  const addNewTask = () => {
    if (!inputNewTask) return;
    const text = inputNewTask.value.trim();
    if (!text) return;

    const li = document.createElement("li");
    li.className = "task-item";
    li.innerHTML = `
      <div class="task-checkbox"></div>
      <span class="task-text">${escapeHtml(text)}</span>
    `;

    taskList.appendChild(li);
    inputNewTask.value = "";
  };

  if (btnAddTask && inputNewTask) {
    btnAddTask.addEventListener("click", addNewTask);
    inputNewTask.addEventListener("keydown", (e) => {
      if (e.key === "Enter") addNewTask();
    });
  }

  // Запуск локализации
  updateLanguage();
});

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}