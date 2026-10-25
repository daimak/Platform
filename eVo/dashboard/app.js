/**
 * eVo Estate — Interactive World (Level 1) & Island Modals (Level 2)
 */

console.log("eVo Estate World & Command Center initialized.");

// Данные иконок островов
const ISLAND_ICONS = {
  mainEstate: "🏰",
  barrymore: "🤖",
  navigator: "🔭",
  memoryLibrary: "📚",
  harbor: "⚓",
  careerGuild: "⚔️",
  knowledgeArchive: "🏛️",
  aiSandbox: "🔮",
  workshop: "⚙️"
};

// Задачи для острова рычагов (сохраняются в localStorage)
let leverageTasks = JSON.parse(localStorage.getItem("evo_leverage_tasks")) || [
  { id: 1, textRu: "Визуальное состояние системы (Estate Level 2)", textEn: "Visual state & spatial depth (Estate Level 2)", done: true },
  { id: 2, textRu: "Интеграция долговременной памяти (Context / Decisions)", textEn: "Long-term memory integration (Context / Decisions)", done: false },
  { id: 3, textRu: "Пространственная карта Estate и шлюз рабочих кабинетов", textEn: "Estate spatial world map & workspace portal", done: false }
];

let activeIslandKey = null;

// Инициализация при загрузке документа
document.addEventListener("DOMContentLoaded", () => {
  initLanguageControls();
  initIslandHotspots();
  initModalControls();
  updateLanguage();
});

/**
 * Инициализация языкового переключателя
 */
function initLanguageControls() {
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
}

/**
 * Инициализация маяков островов
 */
function initIslandHotspots() {
  const hotspots = document.querySelectorAll(".island-hotspot");

  hotspots.forEach(spot => {
    spot.addEventListener("click", () => {
      const islandKey = spot.getAttribute("data-island");
      if (islandKey) {
        openIslandModal(islandKey);
      }
    });
  });
}

/**
 * Открытие модального окна конкретного острова
 */
function openIslandModal(islandKey) {
  activeIslandKey = islandKey;
  const lang = (typeof LANG !== 'undefined' && LANG[currentLanguage]) ? LANG[currentLanguage] : {};
  const islandData = (lang.islands && lang.islands[islandKey]) ? lang.islands[islandKey] : {};

  const viewport = document.getElementById("estate-viewport");
  const backdrop = document.getElementById("island-modal-backdrop");
  const iconBadge = document.getElementById("modal-island-icon");
  const badgeEl = document.getElementById("modal-island-badge");
  const titleEl = document.getElementById("modal-island-title");
  const subEl = document.getElementById("modal-island-subtitle");
  const bodyEl = document.getElementById("modal-island-content");
  const actionsEl = document.getElementById("modal-island-actions");

  // Иконка и заголовки
  if (iconBadge) iconBadge.textContent = ISLAND_ICONS[islandKey] || "📍";
  if (badgeEl) badgeEl.textContent = islandData.badge || "ESTATE NODE";
  if (titleEl) titleEl.textContent = islandData.title || islandKey.toUpperCase();
  if (subEl) subEl.textContent = islandData.subtitle || "";

  // Генерация специфичного контента для каждого острова
  if (bodyEl) {
    bodyEl.innerHTML = buildIslandContentHTML(islandKey, islandData, lang);
  }

  // Генерация кнопок действий в футере
  if (actionsEl) {
    if (islandKey === "mainEstate" || islandKey === "barrymore") {
      actionsEl.innerHTML = `
        <button class="btn-action-primary" id="btn-modal-open-workspace">
          <span>${lang.toWorkspaceBtn || "🚪 Перейти в рабочий кабинет"}</span>
        </button>
      `;
      const btnWs = document.getElementById("btn-modal-open-workspace");
      if (btnWs) {
        btnWs.addEventListener("click", () => {
          closeIslandModal();
          openWorkspaceModal();
        });
      }
    } else {
      actionsEl.innerHTML = "";
    }
  }

  // Подключение обработчиков интерактивных задач (если открыт остров рычагов)
  if (islandKey === "careerGuild") {
    bindTaskEvents();
  }

  if (viewport) viewport.classList.add("modal-active");
  if (backdrop) backdrop.classList.add("open");
}

/**
 * Закрытие модального окна острова
 */
function closeIslandModal() {
  activeIslandKey = null;
  const viewport = document.getElementById("estate-viewport");
  const backdrop = document.getElementById("island-modal-backdrop");

  if (viewport) viewport.classList.remove("modal-active");
  if (backdrop) backdrop.classList.remove("open");
}

/**
 * Инициализация кнопок закрытия модальных окон
 */
function initModalControls() {
  const btnClose = document.getElementById("btn-close-island-modal");
  const btnBack = document.getElementById("btn-back-to-map");
  const backdrop = document.getElementById("island-modal-backdrop");

  if (btnClose) btnClose.addEventListener("click", closeIslandModal);
  if (btnBack) btnBack.addEventListener("click", closeIslandModal);

  if (backdrop) {
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) closeIslandModal();
    });
  }

  // Рабочий кабинет (Уровень 3)
  const wsBackdrop = document.getElementById("workspace-modal-backdrop");
  const btnCloseWs = document.getElementById("btn-close-workspace");
  const btnSaveWs = document.getElementById("btn-save-workspace");

  if (btnCloseWs) btnCloseWs.addEventListener("click", closeWorkspaceModal);
  if (btnSaveWs) btnSaveWs.addEventListener("click", closeWorkspaceModal);
  if (wsBackdrop) {
    wsBackdrop.addEventListener("click", (e) => {
      if (e.target === wsBackdrop) closeWorkspaceModal();
    });
  }

  // Закрытие по Escape
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeIslandModal();
      closeWorkspaceModal();
    }
  });
}

function openWorkspaceModal() {
  const wsBackdrop = document.getElementById("workspace-modal-backdrop");
  const viewport = document.getElementById("estate-viewport");
  if (viewport) viewport.classList.add("modal-active");
  if (wsBackdrop) wsBackdrop.classList.add("open");
}

function closeWorkspaceModal() {
  const wsBackdrop = document.getElementById("workspace-modal-backdrop");
  const viewport = document.getElementById("estate-viewport");
  if (viewport) viewport.classList.remove("modal-active");
  if (wsBackdrop) wsBackdrop.classList.remove("open");
}

/**
 * Генерация HTML-разметки для полупрозрачного окна конкретного острова
 */
function buildIslandContentHTML(islandKey, data, lang) {
  switch (islandKey) {
    case "mainEstate":
      return `
        <div class="glass-panel">
          <div class="panel-label">${data.stateTitle || "СОСТОЯНИЕ СИСТЕМЫ"}</div>
          <h4 style="font-size: 1.4rem; color: #5eead4;">${data.stateHeading || "Foundation → Interface"}</h4>
          <p style="color: #cbd5e1; font-size: 1rem; line-height: 1.6; margin-bottom: 14px;">
            ${data.stateDesc || ""}
          </p>
          <div style="font-family: var(--font-mono); font-size: 0.84rem; color: var(--accent-gold); padding: 8px 12px; background: rgba(0,0,0,0.3); border-radius: 6px;">
            ${data.activeProject || ""}
          </div>
        </div>
        <div class="glass-panel">
          <div class="panel-label">АРХИТЕКТУРНЫЙ СТАТУС</div>
          <p style="color: #cbd5e1; font-size: 0.92rem;">
            Управление всей системой eVo, координация агентов и переходы в рабочие кабинеты.
          </p>
        </div>
      `;

    case "barrymore":
      if (typeof EVO_BRIEF !== "undefined" && EVO_BRIEF && EVO_BRIEF.current) {
        return buildMorningBriefHTML(EVO_BRIEF, lang);
      }
      return `
        <div class="glass-panel" style="border-left: 4px solid var(--accent-amber);">
          <div class="panel-label">ЛИЧНЫЙ СТЮАРД ПЛАТФОРМЫ (ADR-003)</div>
          <h4 style="font-size: 1.25rem; color: #fef08a;">${lang.barrymoreGreeting || "Доброе утро, Дмитрий."}</h4>
          <p style="font-style: italic; color: #fed7aa; font-size: 1.05rem; line-height: 1.6; margin: 12px 0;">
            ${lang.barrymoreFullBrief || ""}
          </p>
          <div style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-muted); border-top: 1px solid rgba(255,255,255,0.08); padding-top: 8px;">
            ${lang.barrymoreSubtext || ""}
          </div>
        </div>
      `;

    case "workshop":
      return `
        <div class="glass-panel">
          <div class="panel-label">ИНФРАСТРУКТУРА КОДА & РЕПОЗИТОРИЙ</div>
          <h4 style="color: #fff;">${data.branchTitle || "Ветка: experiment"}</h4>
          <div class="status-badge-row" style="color: var(--accent-emerald);">
            <span>${data.gitStatus || "● Рабочее дерево чисто"}</span>
          </div>
          <div style="font-family: var(--font-mono); font-size: 0.85rem; margin-top: 12px; color: #94a3b8; background: rgba(0,0,0,0.3); padding: 10px 14px; border-radius: 8px;">
            <span>${data.commitLabel || "Последний коммит:"}</span>
            <span style="color: #5eead4; font-weight: bold;">${data.commitHash || ""}</span>
          </div>
          <div style="font-family: var(--font-mono); font-size: 0.8rem; color: #94a3b8; margin-top: 10px;">
            ${data.toolsLabel || ""}
          </div>
        </div>
      `;

    case "aiSandbox":
      return `
        <div class="glass-panel">
          <div class="panel-label">ТОЧКА ВНИМАНИЯ (ATTENTION)</div>
          <h4 style="color: #fff;">${data.attentionHeading || ""}</h4>
          <div class="status-badge-row" style="color: var(--accent-amber);">
            <span>${data.attentionStatus || "● В процессе разработки"}</span>
          </div>
          <p style="color: #cbd5e1; font-size: 0.95rem; margin: 10px 0;">
            ${data.attentionDesc || ""}
          </p>
        </div>
        <div class="glass-panel">
          <div class="panel-label">ПОДСИСТЕМЫ И АВТОНОМНЫЕ АГЕНТЫ</div>
          <div style="display: flex; flex-direction: column; gap: 8px; margin-top: 8px;">
            <div style="padding: 8px 12px; background: rgba(0,0,0,0.25); border-radius: 6px; font-size: 0.85rem; color: #fed7aa;">
              ${data.agentBarrymore || ""}
            </div>
            <div style="padding: 8px 12px; background: rgba(0,0,0,0.25); border-radius: 6px; font-size: 0.85rem; color: #a7f3d0;">
              ${data.agentContext || ""}
            </div>
            <div style="padding: 8px 12px; background: rgba(0,0,0,0.25); border-radius: 6px; font-size: 0.85rem; color: #bae6fd;">
              ${data.agentMemory || ""}
            </div>
          </div>
          <div style="font-family: var(--font-mono); font-size: 0.78rem; color: var(--text-muted); margin-top: 12px;">
            ${data.securityRule || ""}
          </div>
        </div>
      `;

    case "careerGuild":
      return `
        <div class="glass-panel">
          <div class="panel-label">ПРИОРИТЕТНЫЕ РЫЧАГИ (NEXT LEVERAGE)</div>
          <h4 style="color: #fff;">${data.tasksHeading || ""}</h4>
          <div id="island-tasks-list" style="margin-top: 12px;">
            ${renderLeverageTasksHTML()}
          </div>
          <div style="display: flex; gap: 8px; margin-top: 14px;">
            <input type="text" id="island-new-task-input" placeholder="${data.addTaskPlaceholder || "Новая задача..."}" style="flex: 1; background: rgba(0,0,0,0.4); border: 1px solid var(--border-glass); border-radius: 6px; padding: 8px 12px; color: #fff; font-size: 0.85rem; outline: none;">
            <button id="island-add-task-btn" style="background: var(--accent-teal); border: none; color: #04121a; font-weight: bold; padding: 8px 14px; border-radius: 6px; cursor: pointer;">${data.addTaskBtn || "+ Добавить"}</button>
          </div>
        </div>
      `;

    case "memoryLibrary":
      return `
        <div class="glass-panel">
          <div class="panel-label">ХРОНИКА ЭВОЛЮЦИИ</div>
          <h4 style="color: #fff;">${data.evolutionHeading || ""}</h4>
          <div style="font-family: var(--font-mono); font-size: 0.95rem; color: #5eead4; margin: 10px 0;">
            ${data.evolutionPath || ""}
          </div>
          <div style="display: flex; flex-direction: column; gap: 6px; margin-top: 10px;">
            <div style="padding: 6px 10px; background: rgba(0,0,0,0.2); border-radius: 4px; font-size: 0.85rem; color: #cbd5e1;">${data.estateL1 || ""}</div>
            <div style="padding: 6px 10px; background: rgba(245,158,11,0.1); border-left: 3px solid var(--accent-amber); border-radius: 4px; font-size: 0.85rem; color: #fef3c7; font-weight: bold;">${data.estateL2 || ""}</div>
            <div style="padding: 6px 10px; background: rgba(0,0,0,0.2); border-radius: 4px; font-size: 0.85rem; color: #cbd5e1;">${data.estateL3 || ""}</div>
          </div>
          <div style="font-family: var(--font-mono); font-size: 0.78rem; color: var(--text-muted); margin-top: 12px;">
            ${data.archiveFiles || ""}
          </div>
        </div>
      `;

    case "navigator":
      return `
        <div class="glass-panel">
          <div class="panel-label">ДОРОЖНАЯ КАРТА ЭВОЛЮЦИИ (ROADMAP)</div>
          <h4 style="color: #5eead4;">${data.task1Title || ""}</h4>
          <p style="color: #cbd5e1; font-size: 0.9rem; margin-bottom: 12px;">${data.task1Desc || ""}</p>
          <h4 style="color: #fef08a;">${data.task2Title || ""}</h4>
          <p style="color: #cbd5e1; font-size: 0.9rem; margin-bottom: 12px;">${data.task2Desc || ""}</p>
          <div style="font-style: italic; font-size: 0.85rem; color: #fed7aa; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 10px;">
            ${data.principle || ""}
          </div>
        </div>
      `;

    case "harbor":
      return `
        <div class="glass-panel">
          <div class="panel-label">ШЛЮЗЫ И ВНЕШНИЕ СВЯЗИ</div>
          <p style="color: #cbd5e1; font-size: 0.95rem; line-height: 1.6; margin-bottom: 12px;">
            ${data.harborInfo || ""}
          </p>
          <div style="font-family: var(--font-mono); font-size: 0.85rem; color: var(--accent-emerald);">
            ${data.status || ""}
          </div>
        </div>
      `;

    case "knowledgeArchive":
      return `
        <div class="glass-panel">
          <div class="panel-label">КОНЦЕПТУАЛЬНАЯ БАЗА ЗНАНИЙ</div>
          <p style="color: #cbd5e1; font-size: 0.9rem; margin-bottom: 10px;">${data.docsInfo || ""}</p>
          <blockquote style="border-left: 3px solid var(--accent-gold); padding-left: 12px; font-style: italic; color: #fed7aa; font-size: 0.95rem; line-height: 1.5;">
            ${data.quote || ""}
          </blockquote>
        </div>
      `;

    default:
      return `<p style="color: #cbd5e1;">${data.shortDesc || ""}</p>`;
  }
}

/**
 * Morning Brief из источников истины (ADR-003, read-only).
 * Снимок генерируется tools/barrymore/morning-brief.ps1 в brief.js.
 */
function buildMorningBriefHTML(brief, lang) {
  const escMulti = (s) => escapeHtml(s || "").replace(/\r?\n/g, "<br>");
  const changes = (brief.changes || []).map(c => `
      <div style="padding: 5px 10px; background: rgba(0,0,0,0.25); border-radius: 4px; font-size: 0.8rem; color: #cbd5e1;">${escapeHtml(c)}</div>
    `).join("");

  const currentDate = (brief.current && brief.current.date) ? ` (${escapeHtml(brief.current.date)})` : "";
  const stateNext = (brief.state && brief.state.nextStep) ? brief.state.nextStep : "";
  const dirtyInfo = brief.git && brief.git.dirtyFiles > 0
    ? `изменений в дереве: ${brief.git.dirtyFiles}`
    : "рабочее дерево чистое";

  return `
    <div class="glass-panel" style="border-left: 4px solid var(--accent-amber);">
      <div class="panel-label">MORNING BRIEF — ИЗ ИСТОЧНИКОВ ИСТИНЫ (ADR-003, READ-ONLY)</div>
      <h4 style="font-size: 1.25rem; color: #fef08a;">${lang.barrymoreGreeting || "Доброе утро, Дмитрий."}</h4>
      <p style="font-family: var(--font-mono); font-size: 0.78rem; color: var(--text-muted); margin: 4px 0 14px;">Сформировано: ${escapeHtml(brief.generatedAt || "")}</p>

      ${buildAgentBlock(brief.agent)}

      <div class="panel-label">ТЕКУЩИЙ ФОКУС — CURRENT.md${currentDate}</div>
      <p style="color: #cbd5e1; font-size: 0.95rem; line-height: 1.6; margin: 8px 0 14px;">${escMulti(brief.current && brief.current.nextAction) || "—"}</p>

      <div class="panel-label">СЛЕДУЮЩИЙ ШАГ РАБОТ — Engineering/STATE.md</div>
      <p style="color: #cbd5e1; font-size: 0.95rem; line-height: 1.6; margin: 8px 0 14px;">${escMulti(stateNext) || "—"}</p>

      <div class="panel-label">ПОСЛЕДНИЕ ИЗМЕНЕНИЯ — CHANGELOG.md</div>
      <div style="display: flex; flex-direction: column; gap: 6px; margin: 8px 0 14px;">${changes || "—"}</div>

      <div class="panel-label">GIT</div>
      <div style="font-family: var(--font-mono); font-size: 0.85rem; color: #5eead4; margin: 8px 0 14px;">
        ${escapeHtml((brief.git && brief.git.branch) || "")} · ${escapeHtml((brief.git && brief.git.lastCommit) || "")} · ${dirtyInfo}
      </div>

      <div style="font-family: var(--font-mono); font-size: 0.72rem; color: var(--text-muted); border-top: 1px solid rgba(255,255,255,0.08); padding-top: 8px;">
        Источники: ${escapeHtml((brief.sources || []).join(", "))}. Обновить: tools/barrymore/morning-brief-agent.py (данные + доклад LLM) или morning-brief.ps1 (только данные)
      </div>
    </div>
  `;
}

/**
 * Блок доклада Баррримора от локального LLM (morning-brief-agent.py).
 * agent = { model, summary, nextStep } | { error } | null.
 */
function buildAgentBlock(agent) {
  if (!agent) return "";

  if (agent.error) {
    return `
      <div class="glass-panel" style="border-left: 4px solid var(--accent-amber); margin: 0 0 14px 0;">
        <div class="panel-label">ДОКЛАД БАРРИМОРА (LLM)</div>
        <p style="color: #fca5a5; font-size: 0.9rem; margin: 8px 0;">Мозги недоступны: ${escapeHtml(agent.error)}</p>
        <p style="color: var(--text-muted); font-size: 0.8rem; margin: 0;">Ниже — детерминированный снимок без LLM (morning-brief.ps1 совместим).</p>
      </div>
    `;
  }

  return `
    <div class="glass-panel" style="border-left: 4px solid var(--accent-amber); margin: 0 0 14px 0;">
      <div class="panel-label">ДОКЛАД БАРРИМОРА — ЛОКАЛЬНЫЙ LLM (${escapeHtml(agent.model || "")})</div>
      <p style="font-style: italic; color: #fed7aa; font-size: 1.0rem; line-height: 1.65; margin: 10px 0;">
        ${escapeHtml(agent.summary || "").replace(/\r?\n/g, "<br>")}
      </p>
      ${agent.nextStep ? `
        <div class="panel-label">ПРЕДЛОЖЕНИЕ СЛЕДУЮЩЕГО ШАГА</div>
        <p style="color: #5eead4; font-size: 0.95rem; line-height: 1.6; margin: 8px 0 0 0;">${escapeHtml(agent.nextStep).replace(/\r?\n/g, "<br>")}</p>
      ` : ""}
    </div>
  `;
}

/**
 * Рендеринг интерактивного списка задач
 */
function renderLeverageTasksHTML() {
  const isEn = (currentLanguage === "en");
  return leverageTasks.map(t => {
    const text = isEn ? t.textEn : t.textRu;
    const doneClass = t.done ? "done" : "";
    const mark = t.done ? "✓" : "";
    return `
      <div class="task-item-row ${doneClass}" data-task-id="${t.id}">
        <div class="task-check-box">${mark}</div>
        <span class="task-title-text">${escapeHtml(text)}</span>
      </div>
    `;
  }).join("");
}

/**
 * Навешивание обработчиков событий для задач
 */
function bindTaskEvents() {
  const listEl = document.getElementById("island-tasks-list");
  const inputEl = document.getElementById("island-new-task-input");
  const btnEl = document.getElementById("island-add-task-btn");

  if (listEl) {
    listEl.addEventListener("click", (e) => {
      const row = e.target.closest(".task-item-row");
      if (!row) return;

      const id = parseInt(row.getAttribute("data-task-id"), 10);
      const task = leverageTasks.find(t => t.id === id);
      if (task) {
        task.done = !task.done;
        localStorage.setItem("evo_leverage_tasks", JSON.stringify(leverageTasks));
        listEl.innerHTML = renderLeverageTasksHTML();
      }
    });
  }

  const addNewTask = () => {
    if (!inputEl) return;
    const val = inputEl.value.trim();
    if (!val) return;

    const newTask = {
      id: Date.now(),
      textRu: val,
      textEn: val,
      done: false
    };
    leverageTasks.push(newTask);
    localStorage.setItem("evo_leverage_tasks", JSON.stringify(leverageTasks));
    if (listEl) listEl.innerHTML = renderLeverageTasksHTML();
    inputEl.value = "";
  };

  if (btnEl) btnEl.addEventListener("click", addNewTask);
  if (inputEl) {
    inputEl.addEventListener("keydown", (e) => {
      if (e.key === "Enter") addNewTask();
    });
  }
}

/**
 * Обновление текстов интерфейса при смене языка
 */
function updateLanguage() {
  if (typeof LANG === "undefined") return;
  const lang = LANG[currentLanguage] || LANG.ru;

  const setText = (id, text) => {
    const el = document.getElementById(id);
    if (el && text !== undefined) el.textContent = text;
  };

  // HUD
  setText("hud-brand-title", lang.estateTitle);
  setText("hud-brand-subtitle", lang.systemSubtitle);
  setText("hud-platform-alive", lang.platformAlive);
  setText("hud-heartbeat", lang.heartbeat);
  setText("hud-status-quiet", lang.estateStatusQuiet);
  setText("hud-active-processes", lang.activeProcessesLabel);
  setText("hud-attention-count", lang.attentionQueueLabel);
  setText("btn-close-island-modal", lang.closeBtnText);
  setText("btn-back-to-map", lang.backToMapBtn);

  // Кнопки языка
  const btnRu = document.getElementById("lang-ru");
  const btnEn = document.getElementById("lang-en");
  if (btnRu && btnEn) {
    btnRu.classList.toggle("active", currentLanguage === "ru");
    btnEn.classList.toggle("active", currentLanguage === "en");
  }

  // Обновление всплывающих подсказок на карте
  document.querySelectorAll(".island-hotspot").forEach(spot => {
    const key = spot.getAttribute("data-island");
    if (!key || !lang.islands || !lang.islands[key]) return;

    const data = lang.islands[key];
    const badgeEl = spot.querySelector(".hover-badge");
    const titleEl = spot.querySelector(".hover-title");
    const subEl = spot.querySelector(".hover-subtitle");
    const hintEl = spot.querySelector(".hover-action-hint");

    if (badgeEl) badgeEl.textContent = data.badge;
    if (titleEl) titleEl.textContent = data.title;
    if (subEl) subEl.textContent = data.subtitle;
    if (hintEl) hintEl.textContent = "👆 " + lang.clickToOpenConsole;
  });

  // Если окно какого-то острова сейчас открыто, обновляем и его содержимое
  if (activeIslandKey) {
    openIslandModal(activeIslandKey);
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}