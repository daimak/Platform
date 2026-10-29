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
  knowledgeArchive: "🏛️",
  aiSandbox: "🔮",
  workshop: "⚙️",
  holmesStudy: "🔍",
  leonardoStudy: "🎨",
  sinbadMarket: "🏺",
  maelstormAtlas: "🧭",
  lifeTreeSanctuary: "🌳",
  maelstromObservatory: "🌀"
};

let activeIslandKey = null;

// Инициализация при загрузке документа
document.addEventListener("DOMContentLoaded", () => {
  initLanguageControls();
  initIslandHotspots();
  initBarrymorePlaque();
  initModalControls();
  initSidebarsToggle();
  updateLanguage();
  if (window.location.protocol !== "file:") {
    loadBarrymoreTasks().finally(() => refreshBarrymoreBrief({ automatic: true }));
    window.setInterval(async () => {
      if (await loadBarrymoreTasks()) {
        await refreshBarrymoreBrief({ automatic: true });
      }
    }, 60_000);
  }
});

function initSidebarsToggle() {
  const btn = document.getElementById("btn-toggle-sidebars");
  const leftSidebar = document.getElementById("left-sidebar");
  if (btn && leftSidebar) {
    btn.addEventListener("click", () => {
      leftSidebar.classList.toggle("sidebar-hidden");
    });
  }
}

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
 * Плашка Баррримора (нарисована на арте) — кликабельная зона вместо маячка.
 * Живой контент: приветствие по времени суток + строка данных из Morning Brief
 * (brief.js). Ссылка «Morning Brief» под плашкой появляется при новом
 * (непрочитанном) докладе и исчезает после его открытия (localStorage:
 * evo_brief_seen). Точка расширения: вместо брифа ссылка может нести краткое
 * имя другого события (1–2 слова) — когда появятся другие типы событий.
 */
function initBarrymorePlaque() {
  const plaque = document.getElementById("barrymore-plaque");
  if (plaque) {
    plaque.addEventListener("click", () => openIslandModal("barrymore"));
    plaque.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") openIslandModal("barrymore");
    });
  }
  renderPlaqueContent();
  setInterval(renderPlaqueContent, 60000); // приветствие следует за временем суток
  updateBriefLink();
}

/**
 * Живой текст на плашке: приветствие по часам + счётчик задач из EVO_TASKS
 * (tasks.js). Если задач нет — самая полезная строка из EVO_BRIEF
 * (дайджест агента → следующий шаг → git).
 */
function renderPlaqueContent() {
  const greetingEl = document.getElementById("plaque-greeting");
  const infoEl = document.getElementById("plaque-info");
  const brief = (typeof EVO_BRIEF !== "undefined") ? EVO_BRIEF : null;
  const tasks = (typeof EVO_TASKS !== "undefined") ? EVO_TASKS : null;

  if (greetingEl) {
    const h = new Date().getHours();
    const word = h < 5 ? "Доброй ночи" : h < 12 ? "Доброе утро" : h < 18 ? "Добрый день" : "Добрый вечер";
    greetingEl.textContent = word + ", Дмитрий";
  }

  if (infoEl) {
    const urgent = (tasks && tasks.urgent) ? tasks.urgent.length : 0;
    const regular = (tasks && tasks.regular) ? tasks.regular.length : 0;
    const analytical = 1; // Заглушка
    const other = 6;     // Заглушка

    infoEl.innerHTML = `
      <div style="display: block;">Срочные задачи: ${urgent}</div>
      <div style="display: block;">Активные задачи: ${regular}</div>
      <div style="display: block;">Задачи в аналитике: ${analytical}</div>
      <div style="display: block;">Прочая информация: ${other}</div>
    `;

    let tip = "";
    if (urgent > 0) tip += "Срочные:\n" + tasks.urgent.map(t => "• " + t.title + " (" + t.source + ")").join("\n") + "\n\n";
    if (regular > 0) tip += "Постоянные:\n" + tasks.regular.map(t => "• " + t.title + " (" + t.source + ")").join("\n");
    infoEl.title = tip.trim();
  }
}

function markBriefSeen() {
  if (typeof EVO_BRIEF !== "undefined" && EVO_BRIEF && EVO_BRIEF.generatedAt) {
    localStorage.setItem("evo_brief_seen", EVO_BRIEF.generatedAt);
  }
}

function updateBriefLink() {
  const link = document.getElementById("barrymore-brief-link");
  if (!link) return;
  const brief = (typeof EVO_BRIEF !== "undefined") ? EVO_BRIEF : null;
  const fresh = !!(brief && brief.generatedAt &&
    localStorage.getItem("evo_brief_seen") !== brief.generatedAt);
  link.hidden = !fresh;
}

/**
 * Открытие модального окна конкретного острова
 */
function openIslandModal(islandKey) {
  activeIslandKey = islandKey;
  const refreshButton = document.getElementById("btn-refresh-barrymore");
  const refreshStatus = document.getElementById("barrymore-refresh-status");
  if (refreshButton) refreshButton.hidden = islandKey !== "barrymore";
  if (refreshStatus) {
    refreshStatus.hidden = islandKey !== "barrymore";
    if (islandKey === "barrymore") {
      refreshStatus.textContent = "";
      refreshStatus.classList.remove("is-error");
    }
  }

  if (islandKey === "barrymore") {
    markBriefSeen();
    updateBriefLink();
  }
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

    // Подключение обработчиков
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
  const btnRefreshBarrymore = document.getElementById("btn-refresh-barrymore");
  const btnBack = document.getElementById("btn-back-to-map");
  const backdrop = document.getElementById("island-modal-backdrop");

  if (btnClose) btnClose.addEventListener("click", closeIslandModal);
  if (btnRefreshBarrymore) btnRefreshBarrymore.addEventListener("click", refreshBarrymoreBrief);
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

async function refreshBarrymoreBrief(options = {}) {
  const automatic = options.automatic === true;
  const button = document.getElementById("btn-refresh-barrymore");
  const status = document.getElementById("barrymore-refresh-status");
  if (!button || !status || button.disabled) return;

  button.disabled = true;
  button.classList.add("is-refreshing");
  status.hidden = activeIslandKey !== "barrymore";
  status.classList.remove("is-error");
  if (activeIslandKey === "barrymore") status.textContent = "Проверяю изменения…";

  try {
    const headers = automatic ? {} : { "X-Barrymore-Manual": "true" };
    const response = await fetch("/api/refresh-brief", { method: "POST", headers });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || `Ошибка сервера (${response.status}).`);
    }
    if (!result.brief || typeof result.brief !== "object") {
      throw new Error("Сервер вернул некорректный доклад.");
    }

    window.EVO_BRIEF = result.brief;
    updateBriefLink();
    if (!result.changed) {
      if (activeIslandKey === "barrymore") {
        status.hidden = false;
        status.textContent = "Изменений нет — доклад актуален.";
      }
      return;
    }
    if (activeIslandKey !== "barrymore") return;

    openIslandModal("barrymore");
    const refreshedStatus = document.getElementById("barrymore-refresh-status");
    if (refreshedStatus) {
      refreshedStatus.hidden = false;
      refreshedStatus.textContent = result.brief.agent && result.brief.agent.error
        ? "Данные обновлены без LLM."
        : `Обновлено: ${result.brief.generatedAt || "сейчас"}`;
    }
  } catch (error) {
    if (automatic && activeIslandKey !== "barrymore") {
      console.error("Barrymore brief check failed:", error);
      return;
    }
    const message = error instanceof TypeError && window.location.protocol === "file:"
      ? "Дашборд открыт как файл. Откройте его по адресу http://127.0.0.1:8765."
      : error instanceof TypeError
        ? "Не удалось связаться с сервером. Проверьте задание Barrymore Dashboard Server в планировщике Windows."
        : error.message;
    if (activeIslandKey === "barrymore") {
      status.hidden = false;
      status.classList.add("is-error");
      status.textContent = message;
    } else {
      console.error("Barrymore brief refresh failed:", error);
    }
  } finally {
    button.disabled = false;
    button.classList.remove("is-refreshing");
  }
}

function openWorkspaceModal() {
  const wsBackdrop = document.getElementById("workspace-modal-backdrop");
  const viewport = document.getElementById("estate-viewport");
  if (wsBackdrop) {
    if (viewport) viewport.classList.add("modal-active");
    wsBackdrop.classList.add("open");
  } else {
    console.warn("Workspace modal backdrop not found on this page.");
  }
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

    case "holmesStudy":
      return `
        <div class="glass-panel" style="border-left: 4px solid var(--accent-rose);">
          <div class="panel-label">${data.investigationHeading || "Активное расследование"}</div>
          <h4 style="color: #fb7185;">${data.activeBranch || "Ветка: feature/1.8.2"}</h4>
          <div style="font-family: var(--font-mono); font-size: 0.85rem; color: #a7f3d0; margin-top: 10px;">
            ${data.treeStatus || "● Проверка завершена"}
          </div>
          <p style="color: #cbd5e1; font-size: 0.95rem; margin: 12px 0;">
            ${data.agentHolmes || ""}
          </p>
          <div style="font-family: var(--font-mono); font-size: 0.85rem; color: #fef08a; background: rgba(0,0,0,0.3); padding: 10px; border-radius: 6px; margin-top: 10px;">
            ${data.securityVerdict || ""}
          </div>
        </div>
      `;

    case "leonardoStudy":
      return `
        <div class="glass-panel" style="border-left: 4px solid var(--accent-cyan); background: radial-gradient(circle at center, rgba(56, 189, 248, 0.05) 0%, rgba(0,0,0,0) 100%);">
          <div class="panel-label">${data.conceptHeading || "Витрувианский человек"}</div>
          <h4 style="color: #38bdf8; font-family: var(--font-display);">${data.activeExperiment || "Исследование закономерностей"}</h4>
          <div style="margin: 20px 0; text-align: center; opacity: 0.8;">
             <span style="font-size: 4rem;">🧍</span>
          </div>
          <p style="color: #cbd5e1; font-size: 1rem; line-height: 1.6;">
            ${data.agentLeonardo || ""}
          </p>
          <div style="font-style: italic; color: #fed7aa; font-size: 0.9rem; margin-top: 16px; padding: 12px; border-top: 1px solid rgba(255,255,255,0.08);">
            ${data.quote || ""}
          </div>
        </div>
      `;

    case "sinbadMarket":
      return `
        <div class="glass-panel" style="border-left: 4px solid var(--accent-amber);">
          <div class="panel-label">${data.badge || "MARITIME MARKET"}</div>
          <h4 style="color: #f59e0b; font-family: var(--font-display);">${data.title || "SINBAD MARKET"}</h4>
          <p style="color: #cbd5e1; font-size: 1rem; line-height: 1.6; margin: 12px 0;">
            ${data.marketInfo || ""}
          </p>
          <div class="status-badge-row" style="color: var(--accent-emerald);">
            <span>${data.status || "● Пути открыты"}</span>
          </div>
        </div>
      `;

    case "leonardoStudy":
      return `
        <div class="glass-panel" style="border-left: 4px solid var(--accent-cyan); background: radial-gradient(circle at center, rgba(56, 189, 248, 0.05) 0%, rgba(0,0,0,0) 100%);">
          <div class="panel-label">${data.conceptHeading || "Витрувианский человек"}</div>
          <h4 style="color: #38bdf8; font-family: var(--font-display);">${data.activeExperiment || "Исследование закономерностей"}</h4>
          <div style="margin: 20px 0; text-align: center; opacity: 0.8;">
             <span style="font-size: 4rem;">🧍</span>
          </div>
          <p style="color: #cbd5e1; font-size: 1rem; line-height: 1.6;">
            ${data.agentLeonardo || ""}
          </p>
          <div style="font-style: italic; color: #fed7aa; font-size: 0.9rem; margin-top: 16px; padding: 12px; border-top: 1px solid rgba(255,255,255,0.08);">
            ${data.quote || ""}
          </div>
        </div>
      `;

    case "sinbadMarket":
      return `
        <div class="glass-panel" style="border-left: 4px solid var(--accent-amber);">
          <div class="panel-label">${data.badge || "MARITIME MARKET"}</div>
          <h4 style="color: #f59e0b; font-family: var(--font-display);">${data.title || "SINBAD MARKET"}</h4>
          <p style="color: #cbd5e1; font-size: 1rem; line-height: 1.6; margin: 12px 0;">
            ${data.marketInfo || ""}
          </p>
          <div class="status-badge-row" style="color: var(--accent-emerald);">
            <span>${data.status || "● Пути открыты"}</span>
          </div>
        </div>
      `;

    case "maelstormAtlas":
    case "lifeTreeSanctuary":
    case "maelstromObservatory":
      return `
        <div class="glass-panel" style="border-left: 4px solid var(--accent-cyan);">
          <div class="panel-label">${data.badge || "RESEARCH FRONTIER"}</div>
          <h4 style="color: var(--accent-cyan); font-family: var(--font-display);">${data.title || ""}</h4>
          <p style="color: #cbd5e1; font-size: 0.95rem; line-height: 1.6; margin: 12px 0;">
            ${data.shortDesc || ""}
          </p>
          <div class="status-badge-row" style="color: var(--text-muted);">
            <span>${data.status || ""}</span>
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
 * Снимок генерируется из реальных данных проекта.
 */
function buildMorningBriefHTML(brief, lang) {
  const esc = (s) => escapeHtml(s || "");
  const escMulti = (s) => escapeHtml(s || "").replace(/\r?\n/g, "<br>");

  // Получаем реальные задачи из EVO_TASKS (или пустые массивы)
  const tasks = (typeof EVO_TASKS !== "undefined") ? EVO_TASKS : { urgent: [], regular: [] };

  // Дата формирования (с учетом локализации)
  const generatedAt = brief.generatedAt || "Unknown";

  return `
    <div class="glass-panel" style="border-left: 4px solid var(--accent-amber);">
      <div class="panel-label">BARRYMORE MORNING BRIEF</div>
      <h4 style="font-size: 1.25rem; color: #fef08a; margin-bottom: 4px;">${lang.barrymoreGreeting || "Доброе утро, Дмитрий."}</h4>
      <p style="font-family: var(--font-mono); font-size: 0.7rem; color: var(--text-muted); margin-bottom: 16px;">
        Сформировано: ${esc(generatedAt)} UZT (Ташкент)
      </p>

      <!-- Раздел ЗАДАЧИ -->
      <div class="brief-section open" id="section-tasks">
        <div class="brief-section-header" onclick="toggleBriefSection('section-tasks')">
          <span>ЗАДАЧИ</span>
          <span class="arrow">▶</span>
        </div>
        <div class="brief-section-content">
          ${renderTasksSection(tasks)}
        </div>
      </div>

      <!-- Раздел СОСТОЯНИЕ -->
      <div class="brief-section" id="section-state">
        <div class="brief-section-header" onclick="toggleBriefSection('section-state')">
          <span>СОСТОЯНИЕ</span>
          <span class="arrow">▶</span>
        </div>
        <div class="brief-section-content">
          <div class="brief-task-item">
            <div class="brief-task-title">
              <span style="color: var(--accent-emerald);">🟢</span> Инфраструктура
            </div>
            <div class="brief-task-details" style="display:block; border:none; margin:0; padding:0;">
              Проблем не обнаружено. Платформа активна.
            </div>
          </div>
          <div class="brief-task-item">
            <div class="brief-task-title">
              <span style="color: var(--accent-gold);">⚠️</span> Требуют внимания
            </div>
            <div class="brief-task-details" style="display:block; border:none; margin:0; padding:0;">
              ${brief.git && brief.git.dirtyFiles > 0 ? `Файлов с изменениями: ${brief.git.dirtyFiles}` : "Рабочее дерево чистое"}
            </div>
          </div>
        </div>
      </div>

      <!-- Раздел ВОЗМОЖНОСТИ -->
      <div class="brief-section" id="section-opps">
        <div class="brief-section-header" onclick="toggleBriefSection('section-opps')">
          <span>ВОЗМОЖНОСТИ</span>
          <span class="arrow">▶</span>
        </div>
        <div class="brief-section-content">
          <p style="color: var(--text-secondary); font-size: 0.85rem; line-height: 1.5;">
            ${escMulti(brief.current && brief.current.nextAction) || "Предложений на данный момент нет."}
          </p>
        </div>
      </div>

      <!-- Раздел ТЕХНИЧЕСКОЕ СОСТОЯНИЕ (Свернут по умолчанию) -->
      <div class="brief-section" id="section-tech">
        <div class="brief-section-header" onclick="toggleBriefSection('section-tech')">
          <span>ТЕХНИЧЕСКОЕ СОСТОЯНИЕ</span>
          <span class="arrow">▶</span>
        </div>
        <div class="brief-section-content" style="font-family: var(--font-mono); font-size: 0.75rem;">
          <div style="margin-bottom: 8px; color: var(--accent-cyan);">
            Branch: ${esc(brief.git && brief.git.branch)}
          </div>
          <div style="color: var(--text-muted); font-size: 0.7rem; line-height: 1.4;">
            Last Commit: ${esc(brief.git && brief.git.lastCommit)}
          </div>
          <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.05); color: var(--text-muted);">
            Источники: ${esc((brief.sources || []).join(", "))}
          </div>
        </div>
      </div>

    </div>
  `;
}

/**
 * Рендеринг вложенных задач в секции
 */
function renderTasksSection(tasks) {
  let html = "";

  if (tasks.urgent && tasks.urgent.length > 0) {
    html += `<div style="color: var(--accent-rose); font-size: 0.75rem; font-weight: bold; margin: 8px 0 4px 4px; letter-spacing: 0.5px;">🔴 СРОЧНЫЕ — ${tasks.urgent.length}</div>`;
    tasks.urgent.forEach((task) => { html += renderTaskItem(task, "urgent", true); });
  }

  if (tasks.regular && tasks.regular.length > 0) {
    html += `<div style="color: var(--accent-cyan); font-size: 0.75rem; font-weight: bold; margin: 12px 0 4px 4px; letter-spacing: 0.5px;">🔵 АКТИВНЫЕ — ${tasks.regular.length}</div>`;
    tasks.regular.forEach((task) => { html += renderTaskItem(task, "regular", true); });
  }

  if (tasks.done && tasks.done.length > 0) {
    html += `<div style="color: var(--accent-emerald); font-size: 0.75rem; font-weight: bold; margin: 12px 0 4px 4px; letter-spacing: 0.5px;">✅ DONE — ${tasks.done.length}</div>`;
    tasks.done.forEach((task) => { html += renderTaskItem(task, "done", false); });
  }

  if (!html) html = `<p style="color: var(--text-muted); font-size: 0.85rem;">Задач не обнаружено.</p>`;

  return html;
}

function renderTaskItem(task, group, canComplete) {
  const taskId = escapeHtml(task.id || `${group}-task`);
  const taskTitle = escapeHtml(task.title);
  const source = escapeHtml(task.source || "System");
  const detailId = `task-details-${taskId}`;
  const isEnglish = currentLanguage === "en";
  const status = group === "done"
    ? (isEnglish ? "Done" : "Готово")
    : group === "urgent"
      ? (isEnglish ? "Waiting" : "Ожидает")
      : (isEnglish ? "In progress" : "В работе");
  const priority = group === "urgent"
    ? (isEnglish ? "High" : "Высокий")
    : (isEnglish ? "Normal" : "Обычный");
  const completed = task.completedAt
    ? `<span>${isEnglish ? "Completed:" : "Завершена:"}</span> <span>${escapeHtml(formatTashkentTime(task.completedAt, isEnglish))} UZT</span>`
    : "";
  const completeButton = canComplete && task.id && window.location.protocol !== "file:"
    ? `<button class="task-done-btn" type="button" onclick="completeBarrymoreTask('${taskId}', event)">${isEnglish ? "Mark Done" : "Отметить Done"}</button>`
    : "";

  return `
    <div class="brief-task-item" onclick="toggleTaskDetails('${detailId}', event)">
      <div class="brief-task-title">${group === "done" ? "✅ " : ""}${taskTitle}</div>
      <div class="brief-task-details" id="${detailId}">
        <div class="brief-task-meta">
          <span>${isEnglish ? "Source:" : "Источник:"}</span> <span>${source}</span>
          <span>${isEnglish ? "Priority:" : "Приоритет:"}</span> <span>${priority}</span>
          <span>${isEnglish ? "Status:" : "Статус:"}</span> <span>${status}</span>
          ${completed}
        </div>
        ${completeButton}
      </div>
    </div>
  `;
}

function formatTashkentTime(value, isEnglish) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(isEnglish ? "en-GB" : "ru-RU", {
    timeZone: "Asia/Tashkent",
    dateStyle: "short",
    timeStyle: "short"
  }).format(date);
}

async function loadBarrymoreTasks() {
  try {
    const previous = JSON.stringify(window.EVO_TASKS || null);
    const response = await fetch("/api/tasks");
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || `Ошибка сервера (${response.status}).`);
    window.EVO_TASKS = result.tasks;
    renderPlaqueContent();
    if (activeIslandKey === "barrymore") openIslandModal("barrymore");
    return previous !== JSON.stringify(result.tasks);
  } catch (error) {
    console.error("Barrymore task list could not be loaded:", error);
    return false;
  }
}

window.completeBarrymoreTask = async function(taskId, event) {
  event.stopPropagation();
  try {
    const response = await fetch(`/api/tasks/${encodeURIComponent(taskId)}/done`, { method: "POST" });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || `Ошибка сервера (${response.status}).`);
    window.EVO_TASKS = result.tasks;
    renderPlaqueContent();
    if (activeIslandKey === "barrymore") openIslandModal("barrymore");
    await refreshBarrymoreBrief({ automatic: true });
  } catch (error) {
    const status = document.getElementById("barrymore-refresh-status");
    if (status && activeIslandKey === "barrymore") {
      status.hidden = false;
      status.classList.add("is-error");
      status.textContent = error.message || "Не удалось обновить статус задачи.";
    } else {
      console.error("Barrymore task update failed:", error);
    }
  }
};

/**
 * Переключение разделов брифа
 */
window.toggleBriefSection = function(id) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle("open");
};

/**
 * Переключение деталей задачи
 */
window.toggleTaskDetails = function(id, event) {
  event.stopPropagation();
  const el = document.getElementById(id);
  if (!el) return;
  const parent = el.closest(".brief-task-item");
  if (parent) parent.classList.toggle("open");
};

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
  const refreshBriefButton = document.getElementById("btn-refresh-barrymore");
  if (refreshBriefButton && lang.refreshBriefBtn) {
    refreshBriefButton.setAttribute("aria-label", lang.refreshBriefBtn);
    refreshBriefButton.title = lang.refreshBriefBtn;
  }
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