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
  tradingQuarter: "🏺",
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
  if (new URLSearchParams(window.location.search).get("island") === "aiSandbox") {
    openIslandModal("aiSandbox");
  }
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
const STAFF_STATUS_COLORS = {
  "на службе": "#5eead4",
  "испытательный срок": "#fbbf24",
  "кандидат": "#f87171",
  "уволен": "#64748b",
  "приглашённый специалист": "#c4b5fd",
};
const STAFF_STATUS_ORDER = ["на службе", "испытательный срок", "кандидат", "уволен"];

const STAFF_GROUPS = [
  { key: "active", label: "Активные", countLabel: "активных", color: "#5eead4", statuses: ["на службе", "приглашённый специалист"] },
  { key: "inactive", label: "Неактивные", countLabel: "неактивных", color: "#fbbf24", statuses: ["испытательный срок"] },
  { key: "candidate", label: "Потенциальные", countLabel: "потенциальных", color: "#f87171", statuses: ["кандидат"] },
  { key: "dismissed", label: "Списаны", countLabel: "списаны", color: "#64748b", statuses: ["уволен"] },
];
let estateStaffExpanded = false;

function groupEstateStaff(staff) {
  const groups = Object.fromEntries(STAFF_GROUPS.map((g) => [g.key, []]));
  for (const member of [...(staff.members || []), ...(staff.guests || [])]) {
    const group = STAFF_GROUPS.find((g) => g.statuses.includes(member.status));
    groups[group ? group.key : "dismissed"].push(member);
  }
  return groups;
}

function renderStaffCounts(groups) {
  const muted = "color: var(--text-muted);";
  return (
    `<span style="${muted}">(</span>` +
    STAFF_GROUPS.slice(0, 3)
      .map((g) => `<span style="color: ${g.color};">${g.countLabel}: ${groups[g.key].length}</span>`)
      .join(`<span style="${muted}"> · </span>`) +
    `<span style="${muted}">)</span>`
  );
}

function renderStaffBreakdown(groups) {
  return STAFF_GROUPS.filter((g) => groups[g.key].length)
    .map(
      (g) => `
    <div style="display: flex; align-items: baseline; gap: 8px; padding: 6px 10px; background: rgba(0,0,0,0.25); border-radius: 6px;">
      <span style="color: ${g.color}; font-size: 0.65rem;">●</span>
      <span style="color: ${g.color}; font-size: 0.8rem; font-weight: 600; white-space: nowrap;">${g.label}: ${groups[g.key].length}</span>
      <span style="font-size: 0.8rem; color: #cbd5e1;">${groups[g.key].map((m) => m.name).join(", ")}</span>
    </div>`
    )
    .join("");
}

async function initEstateStaff() {
  const listEl = document.getElementById("estate-staff-list");
  const bodyEl = document.getElementById("estate-staff-body");
  const toggleEl = document.getElementById("estate-staff-toggle");
  if (!listEl || !bodyEl || !toggleEl) return;

  const applyState = () => {
    bodyEl.style.gridTemplateRows = estateStaffExpanded ? "1fr" : "0fr";
    toggleEl.setAttribute("aria-expanded", String(estateStaffExpanded));
    const chevron = document.getElementById("estate-staff-chevron");
    if (chevron) chevron.style.transform = estateStaffExpanded ? "rotate(90deg)" : "rotate(0deg)";
  };
  toggleEl.addEventListener("click", () => {
    estateStaffExpanded = !estateStaffExpanded;
    applyState();
  });
  toggleEl.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      toggleEl.click();
    }
  });
  applyState();

  try {
    const response = await fetch("/api/staff", { cache: "no-store" });
    if (!response.ok) throw new Error("HTTP " + response.status);
    const staff = await response.json();
    const groups = groupEstateStaff(staff);
    const countsEl = document.getElementById("estate-staff-counts");
    const breakdownEl = document.getElementById("estate-staff-breakdown");
    if (countsEl) countsEl.innerHTML = renderStaffCounts(groups);
    if (breakdownEl) breakdownEl.innerHTML = renderStaffBreakdown(groups);
    listEl.innerHTML = renderEstateStaff(staff);
    initAgentRunButton("watson", "watson-run-btn", "watson-run-status", "watson-report-box");
    initAgentRunButton("riskscan", "riskscan-run-btn", "riskscan-run-status", "riskscan-report-box");
  } catch (error) {
    listEl.innerHTML = `<span style="font-size: 0.82rem; color: #fca5a5;">Штат недоступен: ${error.message}</span>`;
  }
}

function renderEstateStaff(staff) {
  const memberRow = (member) => {
    const runtime = RUNTIME_BY_STAFF_ID[member.id];
    const cfg = runtime ? AGENT_RUNTIMES_UI[runtime] : null;
    return `
    <div style="padding: 8px 12px; background: rgba(0,0,0,0.25); border-radius: 6px;">
      <div style="display: flex; justify-content: space-between; gap: 10px; align-items: baseline;">
        <strong style="color: #fff; font-size: 0.9rem;">${escapeHtml(member.name)}</strong>
        <span style="font-size: 0.72rem; color: ${STAFF_STATUS_COLORS[member.status] || "#94a3b8"}; white-space: nowrap;">${escapeHtml(member.status)}</span>
      </div>
      <div style="font-size: 0.8rem; color: #cbd5e1; margin-top: 2px;">${escapeHtml(member.role || "")}</div>
      ${member.metric ? `<div style="font-family: var(--font-mono); font-size: 0.72rem; color: var(--text-muted); margin-top: 4px;">Метрика: ${escapeHtml(member.metric)}</div>` : ""}
      ${member.last_pocket_result ? `<div style="font-size: 0.75rem; color: #a7f3d0; margin-top: 4px;">В кармане: ${escapeHtml(member.last_pocket_result)}</div>` : ""}
      ${member.dismiss_reason ? `<div style="font-size: 0.75rem; color: #fca5a5; margin-top: 4px;">Причина увольнения: ${escapeHtml(member.dismiss_reason)}</div>` : ""}
      ${member.note ? `<div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 4px;">${escapeHtml(member.note)}</div>` : ""}
      ${cfg ? `<div style="display: flex; gap: 10px; align-items: center; margin-top: 8px; flex-wrap: wrap;">
        <button id="${runtime}-run-btn" style="font-size: 0.78rem; padding: 6px 12px; background: rgba(94,234,212,0.12); color: #5eead4; border: 1px solid rgba(94,234,212,0.35); border-radius: 6px; cursor: pointer;"><span>${cfg.btnLabel}</span></button>
        <span id="${runtime}-run-status" style="font-size: 0.75rem; color: #8b96a5;"></span>
      </div>
      <div id="${runtime}-report-box" style="margin-top: 8px;"></div>` : ""}
    </div>`;
  };
  const section = (title, list) => (list && list.length)
    ? `<div style="font-size: 0.72rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; margin: 10px 0 6px;">${title}</div>${list.map(memberRow).join("")}`
    : "";
  const members = [...(staff.members || [])].sort(
    (a, b) => STAFF_STATUS_ORDER.indexOf(a.status) - STAFF_STATUS_ORDER.indexOf(b.status)
  );
  return section("Штат", members) + section("Приглашённые специалисты", staff.guests || []);
}

// --- Прогоны штата на шлюзе (Ватсон, Risk scan) — по образцу кабинета Холмса ---

const AGENT_RUNTIMES_UI = {
  watson: {
    run: "/api/watson/run",
    status: "/api/watson/run-status",
    reports: "/api/watson/reports",
    btnLabel: "📝 Сверка хроники",
    emptyText: "Сверок ещё не было — запусти проверку кнопкой.",
  },
  riskscan: {
    run: "/api/riskscan/run",
    status: "/api/riskscan/run-status",
    reports: "/api/riskscan/reports",
    btnLabel: "🛡 Проверить свежие правки",
    emptyText: "Проверок ещё не было — запусти скан кнопкой.",
  },
};
const RUNTIME_BY_STAFF_ID = { watson: "watson", "risk-scan": "riskscan" };

function initAgentRunButton(runtime, btnId, statusId, reportId) {
  const cfg = AGENT_RUNTIMES_UI[runtime];
  const btn = document.getElementById(btnId);
  const statusEl = document.getElementById(statusId);
  const reportEl = document.getElementById(reportId);
  if (!cfg || !btn || !statusEl || !reportEl) return;
  let pollTimer = null;

  const loadLastReport = () => {
    fetch(cfg.reports, { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error("HTTP " + r.status))))
      .then((data) => {
        const latest = data && data.latest;
        reportEl.innerHTML = latest
          ? `<div style="font-family: var(--font-mono); font-size: 0.72rem; color: #8b96a5; margin-bottom: 6px;">${escapeHtml(latest.file)}</div>` +
            `<pre style="max-height: 260px; overflow: auto; white-space: pre-wrap; font-family: var(--font-mono); font-size: 0.74rem; color: #cbd5e1; background: rgba(0,0,0,0.3); padding: 10px; border-radius: 6px; margin: 0;">${escapeHtml(latest.content)}</pre>`
          : `<span style="font-size: 0.78rem; color: #8b96a5;">${cfg.emptyText}</span>`;
      })
      .catch(() => { reportEl.textContent = "Отчёты недоступны."; });
  };
  const stopPoll = () => { if (pollTimer) { clearInterval(pollTimer); pollTimer = null; } };
  const pollOnce = () => {
    fetch(cfg.status, { cache: "no-store" })
      .then((r) => r.json())
      .then((state) => {
        if (state.running) {
          btn.disabled = true;
          statusEl.textContent = "Прогон идёт…";
          return;
        }
        btn.disabled = false;
        statusEl.textContent = state.returncode === null || state.returncode === undefined
          ? ""
          : (state.returncode === 0 ? "Готово." : "Ошибка: " + (state.error || "код " + state.returncode));
        if (state.finished_at) loadLastReport();
        stopPoll();
      })
      .catch(() => {});
  };
  const startPoll = () => { if (!pollTimer) pollTimer = setInterval(pollOnce, 5000); pollOnce(); };

  btn.addEventListener("click", () => {
    btn.disabled = true;
    statusEl.textContent = "Запуск…";
    fetch(cfg.run, { method: "POST" })
      .then((r) => {
        if (r.status === 409) { statusEl.textContent = "Прогон уже идёт."; return; }
        if (r.status !== 202) throw new Error("HTTP " + r.status);
        statusEl.textContent = "Прогон запущен.";
        startPoll();
      })
      .catch((e) => { statusEl.textContent = "Запуск не удался (" + e.message + ")."; btn.disabled = false; });
  });
  fetch(cfg.status, { cache: "no-store" })
    .then((r) => r.json())
    .then((state) => {
      if (state.running) { btn.disabled = true; statusEl.textContent = "Прогон идёт…"; startPoll(); }
    })
    .catch(() => {});
  loadLastReport();
}

let holmesRunPoll = null;

function initHolmesContext() {
  const branchEl = document.getElementById("holmes-branch");
  const treeEl = document.getElementById("holmes-tree");
  const verdictEl = document.getElementById("holmes-verdict");
  const runBtn = document.getElementById("holmes-run-btn");
  const runStatus = document.getElementById("holmes-run-status");
  if (!branchEl || !treeEl || !verdictEl || !runBtn || !runStatus) return;

  const loadContext = () => {
    fetch("/api/holmes/context", { cache: "no-store" })
      .then((r) => { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then((ctx) => {
        branchEl.innerHTML = `Текущая ветка: <span style="color: #fb7185; font-weight: bold;">${escapeHtml(ctx.branch || "?")}</span>`;
        const changed = Number(ctx.tree_changed) || 0;
        treeEl.textContent = changed ? `● Рабочее дерево: ${changed} незакоммиченных изменений` : "● Рабочее дерево чисто";
        treeEl.style.color = changed ? "#a7f3d0" : "#5eead4";
        verdictEl.textContent = ctx.last_report
          ? `Последний осмотр: ${ctx.last_report.modified} (${ctx.last_report.file}). Данные сыщика актуальны на эту минуту.`
          : "Осмотров ещё не было — сыщик не владеет данными.";
      })
      .catch(() => {
        branchEl.textContent = "Текущая ветка: недоступна";
        treeEl.textContent = "● Рабочее дерево: не читается";
        treeEl.style.color = "#fbbf24";
        verdictEl.textContent = "Контекст недоступен — дашборд-сервер молчит.";
      });
  };
  loadContext();

  const finishRun = (state) => {
    runBtn.disabled = false;
    if (state.returncode === 0) {
      runStatus.style.color = "#5eead4";
      runStatus.textContent = "Дело закрыто — свежий отчёт в списке ниже.";
    } else {
      runStatus.style.color = "#fca5a5";
      runStatus.textContent = "Осмотр не удался: " + (state.error || ("код " + state.returncode));
    }
    if (typeof initHolmesReports === "function") initHolmesReports();
    loadContext();
  };

  const pollRun = () => {
    if (holmesRunPoll) clearInterval(holmesRunPoll);
    holmesRunPoll = setInterval(() => {
      fetch("/api/holmes/run-status", { cache: "no-store" })
        .then((r) => r.json())
        .then((state) => {
          if (state.running) {
            runStatus.textContent = "Расследование идёт" + (state.started_at ? " (с " + String(state.started_at).replace("T", " ") + ")" : "") + " — Холмс осматривает место происшествия…";
            return;
          }
          clearInterval(holmesRunPoll);
          holmesRunPoll = null;
          finishRun(state);
        })
        .catch(() => {});
    }, 5000);
  };

  runBtn.onclick = () => {
    if (runBtn.disabled) return;
    runBtn.disabled = true;
    runStatus.style.color = "#8b96a5";
    runStatus.textContent = "Холмс выходит на место происшествия…";
    fetch("/api/holmes/run", { method: "POST" })
      .then(async (r) => {
        if (!r.ok) {
          const body = await r.json().catch(() => ({}));
          throw new Error(body.error || "HTTP " + r.status);
        }
      })
      .then(pollRun)
      .catch((error) => {
        runBtn.disabled = false;
        runStatus.textContent = "Не удалось начать: " + error.message;
      });
  };

  fetch("/api/holmes/run-status", { cache: "no-store" })
    .then((r) => r.json())
    .then((state) => {
      if (!state.running) return;
      runBtn.disabled = true;
      pollRun();
    })
    .catch(() => {});
}

function initHolmesReports() {
  const select = document.getElementById("holmes-report-select");
  const button = document.getElementById("holmes-report-btn");
  const statusEl = document.getElementById("holmes-report-status");
  const viewEl = document.getElementById("holmes-report-view");
  const fullscreenBtn = document.getElementById("holmes-fullscreen-btn");
  const initiativesEl = document.getElementById("holmes-initiatives");
  const initiativesList = document.getElementById("holmes-initiatives-list");
  const implementBtn = document.getElementById("holmes-implement-btn");
  const implementStatus = document.getElementById("holmes-implement-status");
  if (!select || !button || !statusEl || !viewEl || !fullscreenBtn || !initiativesEl || !initiativesList || !implementBtn || !implementStatus) return;
  const lang = (typeof LANG !== 'undefined' && LANG[currentLanguage]) ? LANG[currentLanguage] : {};
  const islandData = (lang.islands && lang.islands.holmesStudy) ? lang.islands.holmesStudy : {};
  const prefix = islandData.reportForPrefix || "Отчёт за ";
  const failMessage = islandData.reportsError || "Не удалось загрузить отчёты.";
  let currentFile = null;
  let currentInitiatives = [];

  function parseHolmesFindings(content) {
    const blocks = [...content.matchAll(/```json\s*(\{[\s\S]*?\})\s*```/g)];
    if (!blocks.length) return null;
    try {
      const parsed = JSON.parse(blocks[blocks.length - 1][1]);
      return parsed && Array.isArray(parsed.findings) ? parsed.findings : null;
    } catch (error) {
      return null;
    }
  }

  function renderInitiatives(findings) {
    initiativesList.innerHTML = "";
    const actionable = (findings || []).filter(
      (f) => f && f.id && f.status !== "resolved" && (f.severity === "P1" || f.severity === "P2")
    );
    if (!actionable.length) {
      initiativesEl.style.display = "none";
      currentInitiatives = [];
      return;
    }
    currentInitiatives = actionable;
    initiativesEl.style.display = "block";
    implementBtn.disabled = true;
    implementStatus.textContent = islandData.initiativesHint || "";
    for (const finding of actionable) {
      const row = document.createElement("label");
      row.style.cssText = "display: flex; gap: 8px; align-items: flex-start; cursor: pointer; padding: 6px 8px; background: rgba(0,0,0,0.25); border-radius: 6px;";
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.dataset.findingId = finding.id;
      checkbox.addEventListener("change", () => {
        implementBtn.disabled = !initiativesList.querySelector("input:checked");
      });
      const tag = document.createElement("span");
      tag.textContent = finding.severity;
      tag.style.cssText = finding.severity === "P1"
        ? "color: #fb7185; font-family: var(--font-mono); font-size: 0.72rem; font-weight: bold; margin-top: 2px;"
        : "color: #fbbf24; font-family: var(--font-mono); font-size: 0.72rem; font-weight: bold; margin-top: 2px;";
      const text = document.createElement("span");
      text.textContent = finding.detail || finding.id;
      text.style.cssText = "font-size: 0.82rem; color: #cbd5e1; line-height: 1.45;";
      row.appendChild(checkbox);
      row.appendChild(tag);
      row.appendChild(text);
      initiativesList.appendChild(row);
    }
  }

  statusEl.textContent = islandData.reportsLoading || "Загрузка списка отчётов…";
  viewEl.style.display = "none";
  fullscreenBtn.style.display = "none";
  initiativesEl.style.display = "none";
  fetch("/api/holmes/reports")
    .then((r) => r.json())
    .then((data) => {
      const reports = (data && data.reports) || [];
      select.innerHTML = "";
      if (!reports.length) {
        statusEl.textContent = islandData.reportsEmpty || "Отчётов пока нет — запусти Холмса.";
        button.disabled = true;
        return;
      }
      for (const rep of reports) {
        const option = document.createElement("option");
        option.value = rep.file;
        option.textContent = prefix + rep.file.replace("Report-", "").replace("-holmes-audit.md", "");
        select.appendChild(option);
      }
      button.disabled = false;
      statusEl.textContent = "Отчётов: " + reports.length;
    })
    .catch(() => { statusEl.textContent = failMessage; });

  button.onclick = () => {
    const file = select.value;
    if (!file) return;
    statusEl.textContent = "Загрузка " + file + "…";
    fetch("/api/holmes/reports?file=" + encodeURIComponent(file))
      .then((r) => r.json())
      .then((data) => {
        if (data && data.content) {
          currentFile = file;
          viewEl.textContent = data.content;
          viewEl.style.display = "block";
          fullscreenBtn.style.display = "inline-block";
          statusEl.textContent = file;
          renderInitiatives(parseHolmesFindings(data.content));
        } else {
          statusEl.textContent = failMessage;
        }
      })
      .catch(() => { statusEl.textContent = failMessage; });
  };

  fullscreenBtn.onclick = () => {
    if (!currentFile) return;
    window.open("/holmes.html?file=" + encodeURIComponent(currentFile), "_blank");
  };

  implementBtn.onclick = () => {
    const checked = [...initiativesList.querySelectorAll("input:checked")]
      .map((box) => currentInitiatives.find((f) => f.id === box.dataset.findingId))
      .filter(Boolean)
      .map((f) => ({ id: f.id, severity: f.severity, detail: f.detail || "" }));
    if (!checked.length || !currentFile) return;
    implementBtn.disabled = true;
    implementStatus.textContent = "Отправка…";
    fetch("/api/holmes/implement", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file: currentFile, items: checked }),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data && (data.created || data.existing)) {
          const template = islandData.initiativesSent || "Готово: создано задач — {created}; уже было в лиджере — {existing}.";
          implementStatus.textContent = template
            .replace("{created}", (data.created || []).length)
            .replace("{existing}", (data.existing || []).length);
        } else {
          implementStatus.textContent = islandData.initiativesError || "Не удалось отправить инициативы.";
        }
      })
      .catch(() => { implementStatus.textContent = islandData.initiativesError || "Не удалось отправить инициативы."; });
  };
}

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
  if (islandKey === "aiSandbox") {
    initAiSandboxTabs();
    initAiSandboxControls();
    initSecurityContourControls();
    initSecurityTools();
    initSandboxExcursion();
  }
  if (islandKey === "holmesStudy") {
    initHolmesReports();
    initHolmesContext();
  }
  if (islandKey === "memoryLibrary") {
    initAgentRunButton("watson", "watson-run-btn", "watson-run-status", "watson-report-box");
  }
  if (islandKey === "barrymore") {
    initEstateStaff();
  }
  if (islandKey === "tradingQuarter") {
    initTradingQuarterGroups();
    initTradingQuarterTabs();
  }

  // Генерация кнопок действий в футере
  if (actionsEl) {
    if (islandKey === "mainEstate" || islandKey === "barrymore") {
      actionsEl.innerHTML = `
        <button class="btn-action-primary" id="btn-modal-open-workspace">
          <span>${lang.toWorkspaceBtn || "🚪 Перейти в рабочий кабинет"}</span>
        </button>
        <a class="btn-action-kanban" id="btn-modal-open-kanban" href="kanban.html" target="_blank" rel="noopener noreferrer" title="Доска задач: Анализ → Сделать → В работе → Проверка → Готово">📋 Канбан лиджера</a>
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

function initAiSandboxTabs() {
  const tabs = Array.from(document.querySelectorAll('[data-ai-sandbox-tab][role="tab"]'));
  if (!tabs.length) return;

  const selectTab = (selectedTab, focus = false) => {
    tabs.forEach((tab) => {
      const selected = tab === selectedTab;
      tab.setAttribute("aria-selected", String(selected));
      tab.tabIndex = selected ? 0 : -1;
      tab.classList.toggle("is-active", selected);
      const panel = document.getElementById(tab.getAttribute("aria-controls"));
      if (panel) panel.hidden = !selected;
    });
    if (focus) selectedTab.focus();
  };

  tabs.forEach((tab, index) => {
    tab.addEventListener("click", () => selectTab(tab));
    tab.addEventListener("keydown", (event) => {
      let nextIndex;
      if (event.key === "ArrowRight") nextIndex = (index + 1) % tabs.length;
      else if (event.key === "ArrowLeft") nextIndex = (index - 1 + tabs.length) % tabs.length;
      else if (event.key === "Home") nextIndex = 0;
      else if (event.key === "End") nextIndex = tabs.length - 1;
      else return;

      event.preventDefault();
      selectTab(tabs[nextIndex], true);
    });
  });
}

/**
 * Инструменты безопасности (прототипы 01.11): кнопки → POST /api/sandbox/run,
 * статус → GET /api/sandbox/run-status, последний отчёт → GET /api/sandbox/report?tool=.
 * Отчёты рендерятся по-инструментному; secrets/nmap/portaudit — read-only, радар пассивен.
 */
function initSecurityTools() {
  const buttons = Array.from(document.querySelectorAll("[data-sandbox-tool]"));
  if (!buttons.length) return;
  const esc = (value) => escapeHtml(value == null ? "" : String(value));
  const lang = (typeof LANG !== 'undefined' && LANG[currentLanguage]) ? LANG[currentLanguage] : {};
  const labels = (lang.islands && lang.islands.aiSandbox) ? lang.islands.aiSandbox : {};

  buttons.forEach((button) => {
    const tool = button.dataset.sandboxTool;
    button.addEventListener("click", () => runSandboxTool(tool));
  });
  ["radar", "portaudit", "secrets", "nmap"].forEach(loadLatestReport);

  function setStatus(tool, text) {
    const el = document.getElementById(`sandbox-status-${tool}`);
    if (el) el.textContent = text || "";
  }

  async function runSandboxTool(tool) {
    const args = [];
    if (tool === "nmap") {
      const input = document.getElementById("sandbox-nmap-target");
      const target = ((input && input.value) || "127.0.0.1").trim();
      if (!target || /[^0-9A-Za-z.:\-/]/.test(target)) {
        setStatus(tool, `${labels.toolsError || "Ошибка:"} цель должна быть IP/подсетью без лишних символов`);
        return;
      }
      args.push("--target", target);
    }
    setStatus(tool, labels.toolsRunning || "Выполняется…");
    try {
      const response = await fetch("/api/sandbox/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tool, args }),
      });
      const payload = await response.json();
      if (!response.ok) {
        setStatus(tool, `${labels.toolsError || "Ошибка:"} ${payload.error || response.status}`);
        return;
      }
      pollStatus(tool);
    } catch (error) {
      setStatus(tool, `${labels.toolsError || "Ошибка:"} ${error}`);
    }
  }

  function pollStatus(tool) {
    const started = Date.now();
    const timer = setInterval(async () => {
      try {
        const response = await fetch("/api/sandbox/run-status");
        const state = await response.json();
        if (!state.running) {
          clearInterval(timer);
          if (state.returncode === 0) {
            setStatus(tool, `${labels.toolsDone || "Готово."} ${state.finished_at || ""}`);
            loadLatestReport(tool);
          } else {
            setStatus(tool, `${labels.toolsError || "Ошибка:"} ${state.error || state.returncode}`);
          }
          return;
        }
        if (Date.now() - started > 10 * 60 * 1000) {
          clearInterval(timer);
          setStatus(tool, labels.toolsTimeout || "Ожидание превышено — смотри лог сервера.");
          return;
        }
        const seconds = Math.round((Date.now() - started) / 1000);
        setStatus(tool, `${labels.toolsRunning || "Выполняется…"} ${seconds} с`);
      } catch (error) {
        clearInterval(timer);
        setStatus(tool, `${labels.toolsError || "Ошибка:"} ${error}`);
      }
    }, 2000);
  }

  async function loadLatestReport(tool) {
    const box = document.getElementById(`sandbox-result-${tool}`);
    if (!box) return;
    try {
      const response = await fetch(`/api/sandbox/report?tool=${encodeURIComponent(tool)}`);
      if (response.status === 404) {
        box.innerHTML = `<div style="font-size:0.8rem; color:var(--text-muted);">${labels.toolsNoReports || "Отчётов ещё нет — нажми кнопку."}</div>`;
        return;
      }
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || response.status);
      box.innerHTML = renderReport(tool, payload.data, payload.file);
    } catch (error) {
      box.innerHTML = `<div style="font-size:0.8rem; color:#fb7185;">${labels.toolsError || "Ошибка:"} ${esc(error)}</div>`;
    }
  }

  const severityColor = { red: "#fb7185", orange: "#fbbf24", yellow: "#fde68a", info: "#94a3b8" };

  function renderReport(tool, report, file) {
    const head = `<div style="font-family:var(--font-mono); font-size:0.72rem; color:var(--text-muted); margin-bottom:6px;">${esc(file)}</div>`;
    if (tool === "radar") {
      const counts = report.counts || {};
      const rows = (report.items || []).map((item) => {
        const color = severityColor[item.severity] || "#94a3b8";
        const chipText = item.severity === "red" ? "КРАСНЫЙ" : item.severity === "orange" ? "ОРАНЖ" : "ЖЁЛТЫЙ";
        const epss = item.epss != null ? `EPSS ${Math.round(item.epss * 100)}%` : "EPSS —";
        const cvss = item.cvss != null ? `CVSS ${item.cvss}` : "CVSS —";
        const flags = [item.kev ? "KEV" : "", item.ransomware ? "ransomware" : ""].filter(Boolean).join("+");
        return `<div style="display:flex; gap:8px; align-items:baseline; padding:4px 6px; background:rgba(0,0,0,0.25); border-radius:6px; margin-bottom:4px;">
          <span style="font-family:var(--font-mono); font-size:0.7rem; font-weight:bold; color:${color};">${chipText}</span>
          <span style="font-family:var(--font-mono); font-size:0.74rem; color:#e2e8f0;">${esc(item.cve || "")}</span>
          <span style="font-family:var(--font-mono); font-size:0.72rem; color:#94a3b8; white-space:nowrap;">${esc(epss)} · ${esc(cvss)}${flags ? " · " + esc(flags) : ""}</span>
          <span style="font-size:0.76rem; color:#cbd5e1; flex:1;">${esc(item.title || "")}</span>
        </div>`;
      });
      const totals = `<div style="font-size:0.78rem; color:var(--text-secondary); margin-bottom:6px;">всего ${counts.total || 0}: красных ${counts.red || 0}, оранжевых ${counts.orange || 0}, жёлтых ${counts.yellow || 0}</div>`;
      return head + totals + (rows.length ? rows.join("") : `<div style="font-size:0.8rem; color:#a7f3d0;">Совпадений нет.</div>`);
    }
    if (tool === "portaudit") {
      const counts = report.counts || {};
      const rows = (report.listeners || [])
        .filter((l) => l.severity === "red" || l.severity === "orange")
        .map((l) => `<div style="padding:4px 6px; background:rgba(0,0,0,0.25); border-radius:6px; margin-bottom:4px; font-family:var(--font-mono); font-size:0.74rem; color:${severityColor[l.severity]};">${esc(l.proto)} ${esc(l.addr)}:${esc(l.port)} — ${esc(l.process)} — ${esc(l.note)}</div>`);
      const totals = `<div style="font-size:0.78rem; color:var(--text-secondary); margin-bottom:6px;">слушателей ${report.total_listeners || 0}: красных ${counts.red || 0}, оранжевых ${counts.orange || 0}, системных ${counts.info || 0}, loopback ${counts.ok || 0}</div>`;
      return head + totals + (rows.length ? rows.join("") : `<div style="font-size:0.8rem; color:#a7f3d0;">Опасных и незнакомых wildcard-слушателей нет — чисто.</div>`);
    }
    if (tool === "secrets") {
      const counts = report.counts || {};
      const rows = (report.findings || []).slice(0, 15).map((f) => `<div style="padding:4px 6px; background:rgba(0,0,0,0.25); border-radius:6px; margin-bottom:4px; font-family:var(--font-mono); font-size:0.74rem; color:${severityColor[f.severity] || "#94a3b8"};">${esc(f.file)}:${esc(f.line)} — ${esc(f.label)} ${esc(f.excerpt)}</div>`);
      const totals = `<div style="font-size:0.78rem; color:var(--text-secondary); margin-bottom:6px;">файлов просканировано ${report.files_scanned || 0}, находок ${report.findings_count || 0} (красных ${counts.red || 0}, оранжевых ${counts.orange || 0})</div>`;
      return head + totals + (rows.length ? rows.join("") : `<div style="font-size:0.8rem; color:#a7f3d0;">Секретов известных форматов не найдено.</div>`);
    }
    if (tool === "nmap") {
      const rows = (report.open_ports || []).map((p) => `<div style="padding:4px 6px; background:rgba(0,0,0,0.25); border-radius:6px; margin-bottom:4px; font-family:var(--font-mono); font-size:0.74rem; color:#cbd5e1;">${esc(p.port)} ${esc(p.service)}${p.cves && p.cves.length ? " — CVE: " + esc(p.cves.map((c) => c.id + (c.cvss ? ` (${c.cvss})` : "")).slice(0, 6).join(", ")) : ""}</div>`);
      const totals = `<div style="font-size:0.78rem; color:var(--text-secondary); margin-bottom:6px;">цель ${esc(report.target || "")}, vulners: ${report.cve_script ? "да" : "нет"}, открытых TCP ${ (report.open_ports || []).length }</div>`;
      return head + totals + (rows.length ? rows.join("") : `<div style="font-size:0.8rem; color:#a7f3d0;">Открытых портов не найдено.</div>`);
    }
    return head;
  }

  /**
   * Целевой стенд (04.11, задание Sovereign): список целей в localStorage,
   * галочки проверок → args для nmap_probe через /api/sandbox/run.
   * Гварды на месте: nmap_probe сам отклоняет цели вне loopback/приватных
   * без --allow-external; галочка внешних целей требует подтверждения.
   */
  function initTargetBoard() {
    const chipsBox = document.getElementById("sandbox-targets-chips");
    if (!chipsBox) return;
    const input = document.getElementById("sandbox-targets-input");
    const statusEl = document.getElementById("sandbox-status-targets");
    const resultBox = document.getElementById("sandbox-result-targets");
    const STORE_KEY = "sandbox-targets-v1";
    let targets = [];
    let selected = "";
    try {
      const stored = JSON.parse(localStorage.getItem(STORE_KEY) || "[]");
      if (Array.isArray(stored)) targets = stored.filter((t) => typeof t === "string");
    } catch (error) { targets = []; }
    if (!targets.length) targets = ["127.0.0.1", "192.168.238.128"];

    const validTarget = (value) => value.length <= 64 && !/[^0-9A-Za-z.:\-/]/.test(value);
    const setStatus = (text) => { if (statusEl) statusEl.textContent = text || ""; };

    function save() {
      try { localStorage.setItem(STORE_KEY, JSON.stringify(targets)); } catch (error) { /* приватный режим — ок */ }
    }

    function render() {
      chipsBox.innerHTML = targets.map((t) => `
        <span data-target="${esc(t)}" title="${esc(labels.targetsSelectHint || "Клик — выбрать цель, × — убрать")}"
          style="display:inline-flex; align-items:center; gap:6px; padding:3px 8px; border-radius:14px; cursor:pointer;
          font-family:var(--font-mono); font-size:0.76rem; color:#e2e8f0;
          border:1px solid ${t === selected ? "var(--accent-amber, #f59e0b)" : "rgba(255,255,255,0.18)"};
          background:${t === selected ? "rgba(245,158,11,0.15)" : "rgba(0,0,0,0.3)"};">
          ▶ ${esc(t)} <span data-remove="${esc(t)}" style="cursor:pointer; color:#fb7185; font-weight:bold;">×</span>
        </span>`).join("")
        || `<span style="font-size:0.78rem; color:var(--text-muted);">${esc(labels.targetsEmpty || "Список пуст — добавь цель.")}</span>`;
    }

    async function runScan() {
      if (!selected) { setStatus(labels.targetsSelectFirst || "Сначала выбери цель — клик по чипу."); return; }
      const args = ["--target", selected];
      const fast = document.getElementById("sandbox-check-fast");
      const full = document.getElementById("sandbox-check-full");
      const cve = document.getElementById("sandbox-check-cve");
      const external = document.getElementById("sandbox-check-external");
      if (fast && fast.checked && full && !full.checked) args.push("--ports", "1-1000");
      if (full && full.checked) args.push("--ports", "1-65535");
      if (cve && cve.checked) args.push("--cve");
      if (external && external.checked) args.push("--allow-external");
      setStatus(labels.toolsRunning || "Выполняется…");
      if (resultBox) resultBox.innerHTML = "";
      try {
        const response = await fetch("/api/sandbox/run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ tool: "nmap", args }),
        });
        const payload = await response.json();
        if (!response.ok) {
          setStatus(`${labels.toolsError || "Ошибка:"} ${payload.error || response.status}`);
          return;
        }
        pollTargets();
      } catch (error) {
        setStatus(`${labels.toolsError || "Ошибка:"} ${esc(error)}`);
      }
    }

    function pollTargets() {
      const started = Date.now();
      const timer = setInterval(async () => {
        try {
          const state = await (await fetch("/api/sandbox/run-status")).json();
          if (!state.running) {
            clearInterval(timer);
            if (state.returncode === 0) {
              setStatus(`${labels.toolsDone || "Готово."} ${state.finished_at || ""}`);
              const reportResponse = await fetch("/api/sandbox/report?tool=nmap");
              if (reportResponse.ok) {
                const reportPayload = await reportResponse.json();
                if (resultBox) resultBox.innerHTML = renderReport("nmap", reportPayload.data, reportPayload.file);
              }
            } else {
              setStatus(`${labels.toolsError || "Ошибка:"} ${state.error || state.returncode}`);
            }
            return;
          }
          if (Date.now() - started > 10 * 60 * 1000) {
            clearInterval(timer);
            setStatus(labels.toolsTimeout || "Ожидание превышено — смотри лог сервера.");
            return;
          }
          setStatus(`${labels.toolsRunning || "Выполняется…"} ${Math.round((Date.now() - started) / 1000)} с`);
        } catch (error) {
          clearInterval(timer);
          setStatus(`${labels.toolsError || "Ошибка:"} ${esc(error)}`);
        }
      }, 2000);
    }

    const addButton = document.getElementById("sandbox-targets-add");
    if (addButton) {
      addButton.addEventListener("click", () => {
        const value = ((input && input.value) || "").trim();
        if (!value || !validTarget(value)) { setStatus(labels.targetsBad || "Цель должна быть IP/подсетью/хостом без лишних символов."); return; }
        if (!targets.includes(value)) targets.push(value);
        if (targets.length > 20) targets = targets.slice(-20);
        selected = value;
        if (input) input.value = "";
        save();
        render();
        setStatus("");
      });
    }
    if (input) {
      input.addEventListener("keydown", (event) => {
        if (event.key === "Enter") { event.preventDefault(); if (addButton) addButton.click(); }
      });
    }
    chipsBox.addEventListener("click", (event) => {
      const remove = event.target.closest("[data-remove]");
      if (remove) {
        const target = remove.getAttribute("data-remove");
        targets = targets.filter((t) => t !== target);
        if (selected === target) selected = targets[0] || "";
        save();
        render();
        return;
      }
      const chip = event.target.closest("[data-target]");
      if (chip) {
        selected = chip.getAttribute("data-target") || "";
        render();
      }
    });
    const fastCheck = document.getElementById("sandbox-check-fast");
    const fullCheck = document.getElementById("sandbox-check-full");
    if (fastCheck) fastCheck.addEventListener("change", (event) => { if (event.target.checked && fullCheck) fullCheck.checked = false; });
    if (fullCheck) fullCheck.addEventListener("change", (event) => { if (event.target.checked && fastCheck) fastCheck.checked = false; });
    const externalCheck = document.getElementById("sandbox-check-external");
    if (externalCheck) {
      externalCheck.addEventListener("change", (event) => {
        if (event.target.checked && !window.confirm(labels.targetsConfirmExternal || "Разрешить сканирование целей вне loopback/приватных сетей? Это осознанное решение Sovereign.")) {
          event.target.checked = false;
        }
      });
    }
    const runButton = document.getElementById("sandbox-targets-run");
    if (runButton) runButton.addEventListener("click", runScan);
    render();
  }
  initTargetBoard();
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

function initAiSandboxControls() {
  const askButton = document.getElementById("btn-ask-ai-usage");
  const optIn = document.getElementById("include-ai-usage-in-brief");
  const status = document.getElementById("ai-usage-action-status");
  if (!askButton || !optIn || !status) return;

  fetch("/api/ai-usage", { cache: "no-store" })
    .then((response) => response.json().then((data) => {
      if (!response.ok) throw new Error(data.error || `Ошибка сервера (${response.status}).`);
      optIn.checked = data.settings.include_in_morning_brief;
    }))
    .catch((error) => {
      status.textContent = `Не удалось загрузить настройки AI-статистики: ${error.message}`;
    });

  askButton.addEventListener("click", async () => {
    askButton.disabled = true;
    status.textContent = "Бэрримор проверяет сохранённые данные…";
    try {
      const response = await fetch("/api/ai-usage/ask-barrymore", {
        method: "POST",
        headers: { "X-Estate-Action": "ai-usage" }
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `Ошибка сервера (${response.status}).`);
      status.textContent = [data.summary, data.nextStep].filter(Boolean).join("\n\n");
    } catch (error) {
      status.textContent = `Не удалось получить обзор: ${error.message}`;
    } finally {
      askButton.disabled = false;
    }
  });

  optIn.addEventListener("change", async () => {
    optIn.disabled = true;
    try {
      const response = await fetch("/api/ai-usage/settings", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Estate-Action": "ai-usage"
        },
        body: JSON.stringify({ include_in_morning_brief: optIn.checked })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `Ошибка сервера (${response.status}).`);
      optIn.checked = data.settings.include_in_morning_brief;
      status.textContent = optIn.checked
        ? "AI-сводка будет добавляться к докладу по включённой настройке."
        : "AI-сводка отключена для Morning Brief.";
    } catch (error) {
      optIn.checked = !optIn.checked;
      status.textContent = `Не удалось сохранить настройку: ${error.message}`;
    } finally {
      optIn.disabled = false;
    }
  });
}

/**
 * «Защищённый контур» (ADR-003/004): статус изоляции, allowlist-цели и
 * ручной запуск пассивных проверок с LLM-заключением. Наружу уходит ровно
 * один GET / к выбранной цели; всё остальное — локально.
 */
function initSecurityContourControls() {
  const isolationEl = document.getElementById("security-isolation");
  const targetsEl = document.getElementById("security-targets");
  const resultsPanel = document.getElementById("security-results-panel");
  const resultsEl = document.getElementById("security-results");
  if (!isolationEl || !targetsEl || !resultsPanel || !resultsEl) return;

  const langData = typeof LANG !== "undefined" && LANG[currentLanguage] && LANG[currentLanguage].islands
    ? LANG[currentLanguage].islands.aiSandbox || {}
    : {};
  const t = (key, fallback) => langData[key] || fallback;
  const esc = (value) => String(value == null ? "" : value).replace(/[&<>"']/g, (ch) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]
  ));
  const fmt = (value) => (value == null ? "?" : String(value));

  const renderStatus = (payload) => {
    const iso = payload.isolation || {};
    const rows = [];
    rows.push(iso.loopback_only
      ? `<div class="security-fact is-ok">✓ ${esc(t("securityBindOk", "Сервер привязан к 127.0.0.1 — доступ только с этого компьютера"))}</div>`
      : `<div class="security-fact is-bad">✗ ${esc(t("securityBindFail", "ВНИМАНИЕ: сервер отвечает не только на loopback — проверьте привязку"))}</div>`);
    const probe = iso.external_probe;
    if (probe && probe.result === "blocked") {
      rows.push(`<div class="security-fact is-ok">✓ ${esc(t("securityProbeOk", "Внешний интерфейс"))} <span class="security-mono">${esc(probe.address || "")}</span> — ${esc(t("securityProbeBlocked", "не отвечает — снаружи внутрь не пройти"))}</div>`);
    } else if (probe && probe.result === "open") {
      rows.push(`<div class="security-fact is-bad">✗ ${esc(t("securityProbeOpen", "Внешний интерфейс ОТВЕЧАЕТ — контур открыт наружу!"))} <span class="security-mono">${esc(probe.address || "")}</span></div>`);
    } else {
      rows.push(`<div class="security-fact is-warn">● ${esc(t("securityProbeUnknown", "Внешний интерфейс не определён — статус неизвестен"))}</div>`);
    }
    rows.push(`<div class="security-fact">● ${esc(t("securityRouteGuard", "Изменяющие маршруты принимают запросы только из локального дашборда (Origin/Host)"))}</div>`);
    rows.push(payload.llm_analysis
      ? `<div class="security-fact">● ${esc(t("securityLLMEnabled", "LLM-анализ включён: заключение готовит локальный шлюз FreeLLMAPI"))}</div>`
      : `<div class="security-fact is-warn">● ${esc(t("securityLLMDisabled", "LLM-анализ отключён в security-targets.json"))}</div>`);
    if (payload.audit && payload.audit.event_count) {
      const last = payload.audit.last || {};
      const lastTime = last.recorded_at ? new Date(last.recorded_at).toLocaleString() : "";
      rows.push(`<div class="security-fact">● ${esc(t("securityAuditCount", "Запусков в журнале аудита:"))} ${payload.audit.event_count}${lastTime ? ` · ${esc(lastTime)}` : ""}</div>`);
    }
    isolationEl.innerHTML = rows.join("");
    renderTargets(payload.targets || []);
  };

  const state = { targets: [], running: false };

  const selectedHosts = () => Array.from(targetsEl.querySelectorAll(".security-target-check:checked"))
    .map((box) => box.getAttribute("data-security-host"));

  const updateRunButton = () => {
    const runBtn = document.getElementById("security-run-btn");
    if (!runBtn || state.running) return;
    const count = selectedHosts().length;
    runBtn.disabled = count === 0;
    runBtn.textContent = `${t("securityRunCheck", "Проверить выбранные")}${count ? ` (${count})` : ""}`;
  };

  const renderTargets = (targets) => {
    state.targets = Array.isArray(targets) ? targets : [];
    const rows = state.targets.map((target) => `
      <div class="security-target">
        <label class="security-target-pick">
          <input type="checkbox" class="security-target-check" data-security-host="${esc(target.host)}">
          <span class="security-target-host">${esc(target.scheme || "https")}://${esc(target.host)}</span>
        </label>
        ${target.note ? `<span class="security-target-note">${esc(target.note)}</span>` : ""}
      </div>`).join("");
    const listHtml = state.targets.length
      ? rows
      : `<div style="color: var(--text-muted); font-size: 0.88rem; line-height: 1.5;">${esc(t("securityTargetsEmpty", "Разрешённых целей нет. Добавьте первую ниже."))}</div>`;
    targetsEl.innerHTML = `
      <div class="security-target-head">
        <label class="security-target-pick"><input type="checkbox" id="security-check-all"> <span>${esc(t("securitySelectAll", "Выбрать все"))}</span></label>
      </div>
      ${listHtml}
      <div class="security-run-row">
        <button class="btn-action-primary" id="security-run-btn" type="button" disabled>${esc(t("securityRunCheck", "Проверить выбранные"))}</button>
        <span id="security-progress" style="color: var(--text-muted); font-size: 0.82rem;"></span>
      </div>
      <div class="security-add-form">
        <input id="security-add-host" type="text" placeholder="${esc(t("securityAddHostPlaceholder", "host или IP:порт, например 192.168.1.10:8080"))}">
        <select id="security-add-scheme" aria-label="scheme"><option value="https">https</option><option value="http">http</option></select>
        <input id="security-add-note" type="text" placeholder="${esc(t("securityAddNotePlaceholder", "пометка (необязательно)"))}">
        <button class="btn-action-primary" id="security-add-btn" type="button">${esc(t("securityAddBtn", "Добавить цель"))}</button>
      </div>
      <p id="security-add-status" role="status" aria-live="polite" style="margin-top: 8px; color: var(--text-muted); font-size: 0.8rem;"></p>`;
    targetsEl.querySelectorAll(".security-target-check").forEach((box) => {
      box.addEventListener("change", updateRunButton);
    });
    const checkAll = document.getElementById("security-check-all");
    if (checkAll) {
      checkAll.addEventListener("change", () => {
        targetsEl.querySelectorAll(".security-target-check").forEach((box) => { box.checked = checkAll.checked; });
        updateRunButton();
      });
    }
    document.getElementById("security-run-btn").addEventListener("click", () => runChecks(selectedHosts()));
    document.getElementById("security-add-btn").addEventListener("click", addTarget);
    updateRunButton();
  };

  const renderResultsInto = (container, host, payload) => {
    const facts = payload.facts || {};
    const llm = payload.llm;
    const rows = [];
    rows.push(`<div class="security-result-host">${esc(host)} — HTTP ${fmt(facts.status)}${facts.final_url ? ` <span class="security-mono">${esc(facts.final_url)}</span>` : ""}</div>`);
    if (facts.error) rows.push(`<div class="security-fact is-bad">✗ ${esc(facts.error)}</div>`);

    if (facts.tls) {
      rows.push(`<div class="security-sub">${esc(t("securityTlsTitle", "TLS-сертификат"))}</div>`);
      rows.push(`<div class="security-fact">${esc(fmt(facts.tls.version))} · ${esc(fmt(facts.tls.issuer_cn))} · ${esc(t("securityTlsExpires", "истекает:"))} ${esc(fmt(facts.tls.not_after))} (${fmt(facts.tls.days_left)} ${esc(t("securityDays", "дн."))})</div>`);
    } else if (facts.scheme === "https" && !facts.error) {
      rows.push(`<div class="security-fact is-bad">✗ ${esc(t("securityTlsTitle", "TLS-сертификат"))}: ${esc(t("securityTlsUnavailable", "не получен"))}</div>`);
    }

    const headers = facts.headers || {};
    rows.push(`<div class="security-sub">${esc(t("securityHeadersTitle", "Security-заголовки"))}</div>`);
    (headers.present || []).forEach((name) => rows.push(`<div class="security-fact is-ok">✓ ${esc(name)}</div>`));
    (headers.missing || []).forEach((name) => rows.push(`<div class="security-fact is-bad">✗ ${esc(name)}</div>`));
    if (headers.server_banner) rows.push(`<div class="security-fact">● ${esc(t("securityServerBanner", "Баннер сервера:"))} ${esc(headers.server_banner)}</div>`);

    if ((facts.redirects || []).length) {
      rows.push(`<div class="security-sub">${esc(t("securityRedirectsTitle", "Цепочка редиректов"))}</div>`);
      facts.redirects.forEach((redirect) => rows.push(`<div class="security-fact">${fmt(redirect.status)} → ${esc(redirect.to || "")}${redirect.note ? ` — ${esc(redirect.note)}` : ""}</div>`));
    }

    if ((facts.cookies || []).length) {
      rows.push(`<div class="security-sub">Cookies</div>`);
      facts.cookies.forEach((cookie) => rows.push(`<div class="security-fact ${cookie.secure && cookie.http_only ? "is-ok" : "is-warn"}">${esc(cookie.name)}: Secure ${cookie.secure ? "✓" : "✗"} · HttpOnly ${cookie.http_only ? "✓" : "✗"} · SameSite ${esc(fmt(cookie.same_site))}</div>`));
    }

    if (llm && !llm.error) {
      rows.push(`<div class="security-sub">${esc(t("securityLLMTitle", "Заключение ИИ"))} (${esc(llm.model || "?")})</div>`);
      if (llm.summary) rows.push(`<div class="security-llm-summary">${esc(llm.summary)}</div>`);
      (llm.findings || []).forEach((finding) => rows.push(`<div class="security-fact severity-${esc(String(finding.severity || "info").toLowerCase())}">[${esc(finding.severity || "info")}] ${esc(finding.title)}${finding.detail ? ` — ${esc(finding.detail)}` : ""}</div>`));
      if (llm.next_step) rows.push(`<div class="security-fact">→ ${esc(t("securityNextStep", "Следующий шаг:"))} ${esc(llm.next_step)}</div>`);
    } else if (llm && llm.error) {
      rows.push(`<div class="security-fact is-warn">● ${esc(t("securityLLMTitle", "Заключение ИИ"))}: ${esc(llm.error)}</div>`);
    } else {
      rows.push(`<div class="security-fact is-warn">● ${esc(t("securityLLMSkipped", "LLM-анализ отключён — показаны только факты."))}</div>`);
    }

    rows.push(`<div class="security-audit-note">${esc(t("securityAuditNote", "Запуск зафиксирован в журнале аудита:"))} <span class="security-mono">${esc(payload.audit_event_id || "")}</span></div>`);
    container.innerHTML = rows.join("");
  };

  const runChecks = async (hosts) => {
    if (state.running || !hosts.length) return;
    const runBtn = document.getElementById("security-run-btn");
    const progress = document.getElementById("security-progress");
    state.running = true;
    if (runBtn) runBtn.disabled = true;
    resultsPanel.hidden = false;
    resultsEl.innerHTML = "";
    let done = 0;
    for (const host of hosts) {
      done += 1;
      if (progress) progress.textContent = `${t("securityChecking", "Идёт проверка:")} ${done}/${hosts.length} — ${host}`;
      const block = document.createElement("div");
      block.className = "security-result-block";
      resultsEl.appendChild(block);
      try {
        const response = await fetch("/api/security/check", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ host })
        });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || `Ошибка сервера (${response.status}).`);
        renderResultsInto(block, host, payload);
      } catch (error) {
        block.innerHTML = `<div class="security-result-host">${esc(host)}</div><div class="security-fact is-bad">✗ ${esc(t("securityCheckError", "Проверка не удалась:"))} ${esc(error.message)}</div>`;
      }
    }
    if (progress) progress.textContent = `${t("securityDone", "Готово:")} ${hosts.length}`;
    state.running = false;
    updateRunButton();
  };

  const addTarget = async () => {
    const hostInput = document.getElementById("security-add-host");
    const schemeSel = document.getElementById("security-add-scheme");
    const noteInput = document.getElementById("security-add-note");
    const addStatus = document.getElementById("security-add-status");
    const addBtn = document.getElementById("security-add-btn");
    if (!hostInput || !addBtn || !addStatus) return;
    const host = hostInput.value.trim();
    if (!host) {
      addStatus.textContent = t("securityAddEmpty", "Введите host или IP:порт.");
      return;
    }
    addBtn.disabled = true;
    addStatus.textContent = "";
    try {
      const response = await fetch("/api/security/targets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          host,
          scheme: schemeSel ? schemeSel.value : "https",
          note: noteInput ? noteInput.value.trim() : ""
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `Ошибка сервера (${response.status}).`);
      renderTargets(data.targets || []);
      addStatus.textContent = `${t("securityAdded", "Цель добавлена:")} ${host}`;
    } catch (error) {
      addStatus.textContent = `${t("securityAddError", "Не удалось добавить цель:")} ${error.message}`;
    } finally {
      addBtn.disabled = false;
    }
  };

  fetch("/api/security/status", { cache: "no-store" })
    .then((response) => response.json().then((payload) => {
      if (!response.ok) throw new Error(payload.error || `Ошибка сервера (${response.status}).`);
      renderStatus(payload);
    }))
    .catch((error) => {
      isolationEl.innerHTML = `<div class="security-fact is-bad">✗ ${esc(t("securityStatusError", "Не удалось получить состояние изоляции:"))} ${esc(error.message)}</div>`;
    });
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
 * Свёрнутость групп источников ленты вакансий (persist в localStorage,
 * по образцу evo_brief_seen). По умолчанию все группы свёрнуты.
 */
const VAC_EXPANDED_KEY = "evo_vacancies_expanded";

function getVacExpandedSources() {
  try {
    const v = JSON.parse(localStorage.getItem(VAC_EXPANDED_KEY));
    return Array.isArray(v) ? v : [];
  } catch (e) {
    return [];
  }
}

function setVacSourceExpanded(source, expanded) {
  const cur = getVacExpandedSources().filter((s) => s !== source);
  if (expanded) cur.push(source);
  try {
    localStorage.setItem(VAC_EXPANDED_KEY, JSON.stringify(cur));
  } catch (e) { /* нет доступа к localStorage — просто не персистим */ }
}

function initTradingQuarterGroups() {
  document.querySelectorAll("#modal-island-content .vac-group-toggle").forEach((btn) => {
    btn.addEventListener("click", () => {
      const group = btn.closest(".vac-group");
      const items = group ? group.querySelector(".vac-group-items") : null;
      const expanded = btn.getAttribute("aria-expanded") === "true";
      btn.setAttribute("aria-expanded", String(!expanded));
      const chevron = btn.querySelector(".vac-group-chevron");
      if (chevron) chevron.textContent = expanded ? "▸" : "▾";
      if (items) items.hidden = expanded;
      const src = btn.getAttribute("data-source");
      if (src) setVacSourceExpanded(src, !expanded);
    });
  });
}

/**
 * Вкладка «Вакансии» Trading Quarter.
 * Данные приходят из vacancies.js (EVO_VACANCIES), который генерирует
 * tools/job_search.py --js. Пустая лента — подсказка, как её обновить.
 */
function buildTQVacanciesHTML(data) {
  const vac = (typeof EVO_VACANCIES !== "undefined") ? EVO_VACANCIES : null;
  const header = `
    <div class="glass-panel" style="border-left: 4px solid var(--accent-amber);">
      <div class="panel-label">${data.badge || "TRADE DISTRICT"}</div>
      <h4 style="color: var(--accent-amber); font-family: var(--font-display);">${data.title || "TRADING QUARTER"}</h4>
      <p style="color: #cbd5e1; font-size: 0.95rem; line-height: 1.6; margin: 12px 0;">
        ${data.shortDesc || ""}
      </p>
      <div class="status-badge-row" style="color: var(--text-muted);">
        <span>${data.status || ""}</span>
      </div>
    </div>
  `;
  if (!vac || !Array.isArray(vac.jobs) || vac.jobs.length === 0) {
    return header + `
      <div class="glass-panel">
        <p style="color: var(--text-muted); font-size: 0.86rem; line-height: 1.5;">
          ${data.nextStep || "Лента пуста."}
        </p>
      </div>
    `;
  }

  const groups = {};
  vac.jobs.forEach((job) => {
    const src = job.source || "unknown";
    (groups[src] = groups[src] || []).push(job);
  });

  const isEn = currentLanguage === "en";
  const updatedLine = `
    <div style="font-family: var(--font-mono); font-size: 0.72rem; color: var(--text-muted); margin: 2px 0 10px;">
      ${data.vacUpdated || "Лента обновлена:"} ${escapeHtml(vac.generatedAt || "")}
    </div>
  `;
  let body = "";
  const vacExpandedSources = getVacExpandedSources();
  for (const [src, jobs] of Object.entries(groups)) {
    const items = jobs.map((job) => {
      const meta = [job.company, job.location, job.salary]
        .filter(Boolean).map(escapeHtml).join(" · ");
      const date = job.date ? escapeHtml(String(job.date).slice(0, 16).replace("T", " ")) : "";
      const snippet = job.snippet ? escapeHtml(String(job.snippet).slice(0, 200)) : "";
      return `
        <div class="brief-task-item" style="cursor: default;">
          <a href="${safeUrl(job.url)}" target="_blank" rel="noopener noreferrer"
             style="color: #5eead4; text-decoration: none;">
            <div class="brief-task-title">${escapeHtml(job.title || "")}</div>
          </a>
          <div style="font-family: var(--font-mono); font-size: 0.72rem; color: var(--text-muted); margin-top: 2px;">
            ${meta}${date ? " · " + date : ""}
          </div>
          ${snippet ? `<div style="color: var(--text-secondary); font-size: 0.82rem; line-height: 1.45; margin-top: 4px;">${snippet}</div>` : ""}
        </div>
      `;
    }).join("");
    const isGroupExpanded = vacExpandedSources.indexOf(src) !== -1;
    body += `
      <div class="glass-panel vac-group">
        <button type="button" class="vac-group-toggle" data-source="${escapeHtml(src)}"
                aria-expanded="${isGroupExpanded}" title="${escapeHtml(src)}"
                style="display: flex; align-items: center; gap: 8px; width: 100%; padding: 0; background: none; border: none; cursor: pointer; text-align: left; color: inherit; font: inherit;">
          <span class="vac-group-chevron" aria-hidden="true" style="font-family: var(--font-mono); color: var(--accent-amber); flex-shrink: 0;">${isGroupExpanded ? "▾" : "▸"}</span>
          <span class="panel-label">${escapeHtml(src)} · ${jobs.length} ${data.vacPositions || (isEn ? "positions" : "позиций")}</span>
        </button>
        <div class="vac-group-items" ${isGroupExpanded ? "" : "hidden"}>
          ${items}
        </div>
      </div>
    `;
  }
  return header + updatedLine + body;
}

/**
 * Рынок вакансий и заказов (Trading Quarter): три вкладки.
 * «Вакансии» - лента (buildTQVacanciesHTML), «Заказы» - справочник фриланс-бирж:
 * что продавать, тактика, живые заказы (FL.ru - скрап ленты, Kwork - репосты TG),
 * «Радар» - триаж заказов по перспективности (orders_triage.py → orders-triage.js).
 */
function buildTradingQuarterHTML(data) {
  const isEn = currentLanguage === "en";
  const vacanciesTab = data.vacanciesTab || (isEn ? "Vacancies" : "Вакансии");
  const ordersTab = data.ordersTab || (isEn ? "Gig platforms" : "Заказы");
  const radarTab = data.radarTab || (isEn ? "Radar" : "Радар");
  return `
    <div class="ai-sandbox-tabs" role="tablist" aria-label="${isEn ? "Trading Quarter sections" : "Разделы рынка"}">
      <button class="ai-sandbox-tab is-active" id="tq-vacancies-tab" type="button" role="tab"
              aria-selected="true" aria-controls="tq-panel-vacancies" data-tq-tab>
        ${vacanciesTab}
      </button>
      <button class="ai-sandbox-tab" id="tq-orders-tab" type="button" role="tab"
              aria-selected="false" aria-controls="tq-panel-orders" data-tq-tab tabindex="-1">
        ${ordersTab}
      </button>
      <button class="ai-sandbox-tab" id="tq-radar-tab" type="button" role="tab"
              aria-selected="false" aria-controls="tq-panel-radar" data-tq-tab tabindex="-1">
        ${radarTab}
      </button>
    </div>
    <section class="ai-sandbox-tab-panel" id="tq-panel-vacancies" role="tabpanel" aria-labelledby="tq-vacancies-tab">
      ${buildTQVacanciesHTML(data)}
    </section>
    <section class="ai-sandbox-tab-panel" id="tq-panel-orders" role="tabpanel" aria-labelledby="tq-orders-tab" hidden>
      ${buildTQMarketplacesHTML()}
    </section>
    <section class="ai-sandbox-tab-panel" id="tq-panel-radar" role="tabpanel" aria-labelledby="tq-radar-tab" hidden>
      ${buildTQRadarHTML()}
    </section>
  `;
}

const TQ_MARKETPLACES = [
  { key: "kwork", name: "Kwork", url: "https://kwork.ru/", badge: "RU-БИРЖА",
    sell: "4–6 пакетов: «Kubernetes под ключ», «CI/CD с нуля», «Мониторинг Prometheus+Grafana». Первые 2–3 недели цены ниже рынка ради отзывов.",
    tactic: "Создать кворки-пакеты, отвечать на входящие заказы в течение часа.",
    live: "tg:@kwork_orders" },
  { key: "flru", name: "FL.ru", url: "https://www.fl.ru/projects/", badge: "RU-БИРЖА",
    sell: "Проекты крупнее кворка; для нормальных откликов нужен платный PRO.",
    tactic: "Ежедневные отклики, первые заказы — ради рейтинга.",
    live: "freelance:flru" },
  { key: "workzilla", name: "Workzilla", url: "https://work-zilla.com/", badge: "RU-МИКРО",
    sell: "Мелкие задачи для быстрого набора рейтинга.",
    tactic: "Заходить на свежие задания (уходят за минуты); для постоянного потока — не место." },
  { key: "weblancer", name: "Weblancer", url: "https://www.weblancer.net/freelance/", badge: "RU-БИРЖА",
    sell: "Профиль «пусть висит»; поток средний.",
    tactic: "Регистрация + подписка на категории IT/DevOps." },
  { key: "upwork", name: "Upwork", url: "https://www.upwork.com/", badge: "GLOBAL · ГЛАВНЫЙ",
    sell: "3 кейса из энтерпрайза (PB-хранилище, EE→контейнеры, enterprise CI/CD), английский B2+.",
    tactic: "Первые 2–4 недели тишина — норма. Откликаться на свежие jobs (<24ч), первые заказы дёшево ради отзывов. Вывод из UZ: Payoneer." },
  { key: "toptal", name: "Toptal", url: "https://www.toptal.com/", badge: "SCREENING",
    sell: "$60–120+/час после скрининга, enterprise-клиенты.",
    tactic: "Скрининг жёсткий (язык + тесты + live-интервью), готовиться 1–2 недели. Заявку подать сразу — процесс небыстрый." },
  { key: "proxify", name: "Proxify", url: "https://proxify.io/", badge: "SCREENING",
    sell: "$40–80/час, европейские клиенты.",
    tactic: "Скрининг мягче Toptal; поток клиентов не мгновенный — профиль пусть живёт." },
  { key: "lemonio", name: "Lemon.io", url: "https://lemon.io/", badge: "POOL",
    sell: "Стартапы US/EU, DevOps берут регулярно.",
    tactic: "Заявка + интервью, дальше пул подбирает проекты." },
  { key: "arc", name: "Arc.dev", url: "https://arc.dev/", badge: "POOL",
    sell: "Remote-пул сеньоров.",
    tactic: "Заполнить профиль на английском полностью — без этого не зовут." },
  { key: "gunio", name: "Gun.io", url: "https://www.gun.io/", badge: "POOL",
    sell: "US-фриланс для разработчиков и DevOps.",
    tactic: "Заявка + короткое интервью." },
  { key: "braintrust", name: "Braintrust", url: "https://www.usebraintrust.com/", badge: "GLOBAL",
    sell: "Комиссию платит клиент, много enterprise-проектов.",
    tactic: "Профиль + отклик на проекты раз в пару дней." },
  { key: "catalant", name: "Catalant", url: "https://gocatalant.com/", badge: "CONSULTING",
    sell: "Консалтинговая биржа для людей с 12+ годами в больших корпорациях — твой калибр.",
    tactic: "CV на английском с акцентом на enterprise-масштаб (Сбер/Роснефть/X5/ВТБ, PB-хранилища)." },
  { key: "malt", name: "Malt", url: "https://www.malt.com/", badge: "EU",
    sell: "Европейский фриланс-рынок.",
    tactic: "Понадобится EU-подключение/резидентство — держать в уме на будущее." },
  { key: "habrfreelance", name: "Habr Freelance", url: "", badge: "ЗАКРЫЛСЯ",
    sell: "Сервис закрылся навсегда (проверено 30.10.2026, отдаёт 410).",
    tactic: "Не тратить время. Вместо него — Habr Career для вакансий.", closed: true }
];

function buildTQOrderItem(job) {
  const meta = [job.salary, job.date ? String(job.date).slice(0, 16).replace("T", " ") : ""]
    .filter(Boolean).map(escapeHtml).join(" · ");
  return `
    <div class="brief-task-item" style="cursor: default;">
      <a href="${escapeHtml(job.url || "#")}" target="_blank" rel="noopener noreferrer"
         style="color: #5eead4; text-decoration: none;">
        <div class="brief-task-title">${escapeHtml(job.title || "")}</div>
      </a>
      ${meta ? `<div style="font-family: var(--font-mono); font-size: 0.72rem; color: var(--text-muted); margin-top: 2px;">${meta}</div>` : ""}
    </div>
  `;
}

function buildTQMarketplacesHTML() {
  const vac = (typeof EVO_VACANCIES !== "undefined") ? EVO_VACANCIES : null;
  const isEn = currentLanguage === "en";
  let html = `
    <p style="color: var(--text-muted); font-size: 0.84rem; margin: 0 0 14px 2px;">
      ${isEn ? "Expand a platform: what to sell there, entry tactics and live gigs where the feed is available." : "Раскрой биржу: что на ней продавать, тактика входа и живые заказы, если биржа отдаёт ленту."}
    </p>
  `;
  for (const mk of TQ_MARKETPLACES) {
    let live = [];
    let liveLabel = "";
    if (!mk.closed && mk.live) {
      if (mk.live.startsWith("freelance:")) {
        const key = mk.live.slice("freelance:".length);
        live = (vac && vac.freelance && Array.isArray(vac.freelance[key])) ? vac.freelance[key].slice(0, 8) : [];
        liveLabel = isEn ? "LIVE GIGS FROM THE PLATFORM" : "ЖИВЫЕ ЗАКАЗЫ С БИРЖИ";
      } else if (mk.live.startsWith("tg:@")) {
        const channel = mk.live.slice("tg:@".length).toLowerCase();
        live = ((vac && Array.isArray(vac.jobs)) ? vac.jobs : [])
          .filter((job) => (job.source || "").toLowerCase().includes("@" + channel))
          .slice(0, 8);
        liveLabel = isEn ? "ORDER REPOSTS (TELEGRAM)" : "РЕПОСТЫ ЗАКАЗОВ (TELEGRAM)";
      }
    }
    const countText = mk.closed ? "" : (live.length ? live.length + (isEn ? " gigs" : " заказов") : "");
    const openAttr = (mk.key === "flru" || mk.key === "upwork") ? " open" : "";
    html += `
      <details class="tq-acc"${openAttr}>
        <summary>
          <span class="tq-name">${escapeHtml(mk.name)}</span>
          <span class="tq-badge"${mk.closed ? ' style="color: var(--accent-rose); border-color: var(--accent-rose);"' : ""}>${escapeHtml(mk.badge)}</span>
          ${countText ? `<span class="tq-count">${escapeHtml(countText)}</span>` : ""}
        </summary>
        <div class="tq-body">
          <div class="tq-line"><b>${isEn ? "What to sell:" : "Что продавать:"}</b> ${escapeHtml(mk.sell)}</div>
          <div class="tq-line"><b>${isEn ? "Tactics:" : "Тактика:"}</b> ${escapeHtml(mk.tactic)}</div>
          ${mk.url ? `<div class="tq-line" style="margin-top: 8px;"><a href="${escapeHtml(mk.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(mk.url.replace(/^https:\/\//, ""))} ↗</a></div>` : ""}
          ${(!mk.closed && mk.live && live.length)
            ? `<div class="tq-live-head">${liveLabel} · ${live.length}</div>` + live.map(buildTQOrderItem).join("")
            : ""}
          ${(!mk.closed && mk.live && live.length === 0)
            ? `<div class="tq-live-head">${isEn ? "No live feed - check the platform manually or refresh vacancies.js" : "Ленты нет — проверь биржу вручную или обнови vacancies.js"}</div>`
            : ""}
        </div>
      </details>
    `;
  }
  return html;
}

/**
 * Радар заказов (orders_triage.py → orders-triage.js): триаж записей снапшота
 * на перспективные (по категориям), основной блок и отсев. Ручные статусы
 * правятся в Workspace/analytics/orders_board.json и при перегенерации сохраняются.
 */
function buildTQRadarHTML() {
  const board = (typeof EVO_ORDERS_TRIAGE !== "undefined") ? EVO_ORDERS_TRIAGE : null;
  const isEn = currentLanguage === "en";
  if (!board || !Array.isArray(board.categories)) {
    return `<p style="color: var(--text-muted); font-size: 0.84rem; margin: 4px 0 0 2px;">${
      isEn ? "No radar data yet. Run: python tools/orders_triage.py" : "Данных радара ещё нет — прогони: python tools/orders_triage.py"
    }</p>`;
  }
  const asRow = (item) => buildTQOrderItem({
    title: item.title,
    url: item.url,
    salary: item.has_salary === "yes" ? (isEn ? "salary ✓" : "ЗП ✓") : (isEn ? "ask for range" : "спросить вилку"),
    date: item.date,
  });
  const accordion = (name, count, rows, moreCount) => `
    <details class="tq-acc">
      <summary>
        <span class="tq-name">${escapeHtml(name)}</span>
        <span class="tq-count">${count}${isEn ? " items" : " шт."}</span>
      </summary>
      <div class="tq-body">
        ${rows}
        ${moreCount > 0 ? `<div class="tq-line" style="color: var(--text-muted);">… ${isEn ? "and" : "и ещё"} ${moreCount} — ${isEn ? "in orders_board.json" : "в orders_board.json"}</div>` : ""}
      </div>
    </details>
  `;
  let html = `
    <p style="color: var(--text-muted); font-size: 0.84rem; margin: 0 0 14px 2px;">
      ${isEn
        ? `Triage of the ${board.snapshot} snapshot: promising orders by category first, then the study pile. Manual sorting lives in orders_board.json and survives regeneration.`
        : `Триаж снапшота ${board.snapshot}: перспективные заказы по категориям, ниже основной блок. Ручная сортировка живёт в orders_board.json и переживает перегенерацию.`}
    </p>
  `;
  for (const cat of board.categories) {
    const items = Array.isArray(cat.items) ? cat.items : [];
    if (!items.length) continue;
    html += accordion(cat.label, cat.count, items.map(asRow).join(""), Math.max(cat.count - items.length, 0));
  }
  if (board.main && board.main.count) {
    html += accordion(isEn ? "Study pile (main)" : "Основной блок (изучать)", board.main.count,
      (board.main.items || []).map(asRow).join(""), Math.max(board.main.count - (board.main.items || []).length, 0));
  }
  if (board.outset && board.outset.count) {
    html += accordion(isEn ? "Discarded (outset)" : "Отсев", board.outset.count,
      (board.outset.items || []).map(asRow).join(""), Math.max(board.outset.count - (board.outset.items || []).length, 0));
  }
  return html;
}

/**
 * Переключение вкладок Trading Quarter (та же механика, что в aiSandbox).
 */
function initTradingQuarterTabs() {
  const tabs = Array.from(document.querySelectorAll('[data-tq-tab][role="tab"]'));
  if (!tabs.length) return;

  const selectTab = (selectedTab, focus = false) => {
    tabs.forEach((tab) => {
      const selected = tab === selectedTab;
      tab.setAttribute("aria-selected", String(selected));
      tab.tabIndex = selected ? 0 : -1;
      tab.classList.toggle("is-active", selected);
      const panel = document.getElementById(tab.getAttribute("aria-controls"));
      if (panel) panel.hidden = !selected;
    });
    if (focus) selectedTab.focus();
  };

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => selectTab(tab));
  });
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

    case "barrymore": {
      const briefHTML = (typeof EVO_BRIEF !== "undefined" && EVO_BRIEF && EVO_BRIEF.current)
        ? buildMorningBriefHTML(EVO_BRIEF, lang)
        : `
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
      return `
        ${briefHTML}
        <div class="glass-panel" id="estate-staff-panel">
          <div id="estate-staff-toggle" role="button" tabindex="0" aria-expanded="false" title="Развернуть/свернуть штат"
               style="display: flex; align-items: baseline; gap: 8px; cursor: pointer;">
            <span id="estate-staff-chevron" style="display: inline-block; transition: transform 0.3s ease; color: var(--text-muted); font-size: 0.65rem;">▶</span>
            <span class="panel-label">ШТАТ ПОМЕСТЬЯ (ESTATE STAFF)</span>
            <span id="estate-staff-counts" style="font-family: var(--font-mono); font-size: 0.78rem; white-space: nowrap;"></span>
          </div>
          <div id="estate-staff-body" style="display: grid; grid-template-rows: 0fr; transition: grid-template-rows 0.3s ease;">
            <div style="overflow: hidden; min-height: 0;">
              <p style="font-size: 0.82rem; color: var(--text-muted); margin: 8px 0 10px;">
                Кто числится в доме. Режим «поводка»: без расписаний — запуск кнопкой «Прогон» или рукой Sovereign.
              </p>
              <div id="estate-staff-breakdown" style="display: flex; flex-direction: column; gap: 6px; margin-bottom: 10px;"></div>
              <div id="estate-staff-list" style="display: flex; flex-direction: column; gap: 8px;">
                <span style="font-size: 0.82rem; color: var(--text-muted);">Читаю штат…</span>
              </div>
            </div>
          </div>
        </div>
      `;
    }

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
        <div class="ai-sandbox-tabs" role="tablist" aria-label="${currentLanguage === "en" ? "AI Sandbox sections" : "Разделы песочницы ИИ"}">
          <button class="ai-sandbox-tab is-active" id="ai-sandbox-overview-tab" type="button" role="tab" aria-selected="true" aria-controls="ai-sandbox-overview" data-ai-sandbox-tab>
            ${data.overviewTab || "Обзор"}
          </button>
          <button class="ai-sandbox-tab" id="ai-sandbox-security-tab" type="button" role="tab" aria-selected="false" aria-controls="ai-sandbox-security" data-ai-sandbox-tab tabindex="-1">
            ${data.securityTab || "Защищённый контур"}
          </button>
          <button class="ai-sandbox-tab" id="ai-sandbox-tools-tab" type="button" role="tab" aria-selected="false" aria-controls="ai-sandbox-tools" data-ai-sandbox-tab tabindex="-1">
            ${data.toolsTab || "Инструменты"}
          </button>
          <button class="ai-sandbox-tab" id="ai-sandbox-excursion-tab" type="button" role="tab" aria-selected="false" aria-controls="ai-sandbox-excursion" data-ai-sandbox-tab tabindex="-1">
            ${data.excursionTab || "Экскурсия"}
          </button>
        </div>
        <section class="ai-sandbox-tab-panel" id="ai-sandbox-overview" role="tabpanel" aria-labelledby="ai-sandbox-overview-tab">
        <div class="glass-panel">
          <div class="panel-label">${data.attentionLabel || "ТОЧКА ВНИМАНИЯ"}</div>
          <h4 style="color: #fff;">${data.attentionHeading || ""}</h4>
          <div class="status-badge-row" style="color: var(--accent-amber);">
            <span>${data.attentionStatus || "● В процессе разработки"}</span>
          </div>
          <p style="color: #cbd5e1; font-size: 0.95rem; margin: 10px 0;">
            ${data.attentionDesc || ""}
          </p>
        </div>
        <div class="glass-panel">
          <div class="panel-label">${data.subsystemsTitle || "ПОДСИСТЕМЫ И АВТОНОМНЫЕ АГЕНТЫ"}</div>
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
        <div class="glass-panel">
          <div class="panel-label">${data.usageTitle || "AI USAGE"}</div>
          <p style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.5; margin: 8px 0 12px;">
            ${data.usageDesc || ""}
          </p>
          <div style="display:flex; flex-wrap:wrap; gap:10px;">
            <a class="btn-action-primary" href="ai-usage.html">${data.usageOpen || "Открыть статистику AI"}</a>
            <button class="btn-action-primary" id="btn-ask-ai-usage" type="button">${data.usageAsk || "Попросить Бэрримора проверить"}</button>
          </div>
          <label style="display:flex; gap:9px; align-items:flex-start; margin-top:14px; color:var(--text-secondary); font-size:0.85rem;">
            <input id="include-ai-usage-in-brief" type="checkbox" style="margin-top:3px;">
            <span>${data.usageOptIn || "Включать AI-статистику в Morning Brief"}</span>
          </label>
          <p id="ai-usage-action-status" role="status" aria-live="polite" style="margin-top:10px; color:var(--text-muted); white-space:pre-wrap;"></p>
        </div>
        <div class="glass-panel">
          <div class="panel-label">${data.historyTitle || "AI PROJECT HISTORY"}</div>
          <p style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.5; margin: 8px 0 12px;">
            ${data.historyDesc || ""}
          </p>
          <a class="btn-action-primary" href="ai-sandbox-history.html">${data.historyOpen || "Открыть историю ИИ"}</a>
        </div>
        </section>
        <section class="ai-sandbox-tab-panel" id="ai-sandbox-security" role="tabpanel" aria-labelledby="ai-sandbox-security-tab" tabindex="0" hidden>
          <div class="glass-panel ai-sandbox-security-placeholder">
            <div class="panel-label">${data.securityTab || "Защищённый контур"}</div>
            <h4 style="color: #fff;">${data.securityTitle || "Изоляция и внешние проверки"}</h4>
            <p style="color: var(--text-secondary); line-height: 1.6;">${data.securityDesc || ""}</p>
            <div id="security-isolation" class="security-fact-list" role="status" aria-live="polite">
              <div style="color: var(--text-muted); font-size: 0.85rem;">${data.securityStatusLoading || "Проверяю изоляцию…"}</div>
            </div>
          </div>
          <div class="glass-panel">
            <div class="panel-label">${data.securityTargetsTitle || "РАЗРЕШЁННЫЕ ЦЕЛИ (ALLOWLIST)"}</div>
            <div id="security-targets" class="security-target-list"></div>
            <p style="font-family: var(--font-mono); font-size: 0.74rem; color: var(--text-muted); margin-top: 10px; line-height: 1.5;">${data.securityTargetsHint || ""}</p>
          </div>
          <div class="glass-panel" id="security-results-panel" hidden>
            <div class="panel-label">${data.securityResultTitle || "РЕЗУЛЬТАТ ПРОВЕРКИ"}</div>
            <div id="security-results"></div>
          </div>
        </section>
        <section class="ai-sandbox-tab-panel" id="ai-sandbox-tools" role="tabpanel" aria-labelledby="ai-sandbox-tools-tab" tabindex="0" hidden>
          <div class="glass-panel">
            <div class="panel-label">${data.toolsHeading || "ИНСТРУМЕНТЫ БЕЗОПАСНОСТИ (ПРОТОТИПЫ)"}</div>
            <p style="color: var(--text-secondary); font-size: 0.86rem; line-height: 1.5; margin: 8px 0 0;">
              ${data.toolsDesc || "Запуск только по кнопке (режим «поводок»). Отчёты пишутся вне git — %LOCALAPPDATA%\\Platform\\SecurityReports."}
            </p>
          </div>
          <div class="glass-panel">
            <div class="panel-label">${data.radarTitle || "🛰 Радар уязвимостей"}</div>
            <p style="color: var(--text-secondary); font-size: 0.84rem; line-height: 1.5;">${data.radarDesc || "CISA KEV + EPSS + NVD: воронка «эксплуатируется → вероятно → тяжёлое»."}</p>
            <div style="display:flex; gap:10px; align-items:center;">
              <button class="btn-action-primary" type="button" data-sandbox-tool="radar">${data.radarBtn || "Собрать радар"}</button>
              <span id="sandbox-status-radar" style="font-size:0.78rem; color:var(--text-muted);"></span>
            </div>
            <div id="sandbox-result-radar" style="margin-top:10px;"></div>
          </div>
          <div class="glass-panel">
            <div class="panel-label">${data.portTitle || "🔌 Аудит портов"}</div>
            <p style="color: var(--text-secondary); font-size: 0.84rem; line-height: 1.5;">${data.portDesc || "Что слушает Windows и на каких адресах. Опасные порты на 0.0.0.0 — красным."}</p>
            <div style="display:flex; gap:10px; align-items:center;">
              <button class="btn-action-primary" type="button" data-sandbox-tool="portaudit">${data.portBtn || "Проверить порты"}</button>
              <span id="sandbox-status-portaudit" style="font-size:0.78rem; color:var(--text-muted);"></span>
            </div>
            <div id="sandbox-result-portaudit" style="margin-top:10px;"></div>
          </div>
          <div class="glass-panel">
            <div class="panel-label">${data.secretsTitle || "🔑 Поиск секретов"}</div>
            <p style="color: var(--text-secondary); font-size: 0.84rem; line-height: 1.5;">${data.secretsDesc || "Ключи известных форматов в дереве репозитория; найденное маскируется."}</p>
            <div style="display:flex; gap:10px; align-items:center;">
              <button class="btn-action-primary" type="button" data-sandbox-tool="secrets">${data.secretsBtn || "Проверить секреты"}</button>
              <span id="sandbox-status-secrets" style="font-size:0.78rem; color:var(--text-muted);"></span>
            </div>
            <div id="sandbox-result-secrets" style="margin-top:10px;"></div>
          </div>
          <div class="glass-panel">
            <div class="panel-label">${data.nmapTitle || "🎯 nmap-скан своих хостов"}</div>
            <p style="color: var(--text-secondary); font-size: 0.84rem; line-height: 1.5;">${data.nmapDesc || "Версии сервисов и CVE (vulners). По умолчанию 127.0.0.1; внешние цели — осознанное решение."}</p>
            <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
              <label style="font-size:0.8rem; color:var(--text-secondary);">${data.nmapTargetLabel || "Цель:"}
                <input id="sandbox-nmap-target" value="127.0.0.1" spellcheck="false"
                  style="background:rgba(0,0,0,0.35); border:1px solid rgba(255,255,255,0.15); border-radius:6px; color:#e2e8f0; padding:4px 8px; font-family:var(--font-mono); font-size:0.8rem; width:180px;">
              </label>
              <button class="btn-action-primary" type="button" data-sandbox-tool="nmap">${data.nmapBtn || "Сканировать"}</button>
              <span id="sandbox-status-nmap" style="font-size:0.78rem; color:var(--text-muted);"></span>
            </div>
            <div id="sandbox-result-nmap" style="margin-top:10px;"></div>
          </div>
          <div class="glass-panel">
            <div class="panel-label">${data.targetsTitle || "🧭 Целевой стенд"}</div>
            <p style="color: var(--text-secondary); font-size: 0.84rem; line-height: 1.5;">${data.targetsDesc || "Свои цели: вбей IP/подсеть, щёлкни галочки проверок, запускай. По умолчанию разрешены только loopback и приватные сети; внешние — отдельная галочка Sovereign."}</p>
            <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
              <input id="sandbox-targets-input" placeholder="192.168.238.128 / 127.0.0.1" spellcheck="false"
                style="background:rgba(0,0,0,0.35); border:1px solid rgba(255,255,255,0.15); border-radius:6px; color:#e2e8f0; padding:4px 8px; font-family:var(--font-mono); font-size:0.8rem; width:200px;">
              <button type="button" id="sandbox-targets-add"
                style="background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.18); border-radius:6px; color:#e2e8f0; padding:4px 10px; font-size:0.78rem; cursor:pointer;">${data.targetsAdd || "＋ добавить"}</button>
            </div>
            <div id="sandbox-targets-chips" style="display:flex; gap:6px; flex-wrap:wrap; margin-top:8px;"></div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:4px 14px; margin-top:10px; font-size:0.78rem; color:var(--text-secondary);">
              <label><input type="checkbox" id="sandbox-check-fast"> ${data.targetsFast || "Быстрый скан (порты 1–1000)"}</label>
              <label><input type="checkbox" id="sandbox-check-full"> ${data.targetsFull || "Все порты 1–65535 (медленно)"}</label>
              <label><input type="checkbox" id="sandbox-check-cve"> ${data.targetsCve || "Поиск CVE (vulners)"}</label>
              <label style="color:#fb7185;"><input type="checkbox" id="sandbox-check-external"> ${data.targetsExternal || "Внешние цели (Sovereign)"}</label>
            </div>
            <div style="display:flex; gap:10px; align-items:center; margin-top:10px;">
              <button class="btn-action-primary" type="button" id="sandbox-targets-run">${data.targetsRun || "Сканировать выбранную"}</button>
              <span id="sandbox-status-targets" style="font-size:0.78rem; color:var(--text-muted);"></span>
            </div>
            <div id="sandbox-result-targets" style="margin-top:10px;"></div>
          </div>
        </section>
        <section class="ai-sandbox-tab-panel" id="ai-sandbox-excursion" role="tabpanel" aria-labelledby="ai-sandbox-excursion-tab" tabindex="0" hidden>
          <div id="sandbox-excursion-root"></div>
        </section>
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
        <div class="glass-panel" style="border-left: 4px solid #93c5fd; margin-top: 14px;">
          <div class="panel-label">ВАТСОН — СВЕРКА ХРОНИКИ</div>
          <p style="color: #cbd5e1; font-size: 0.9rem; margin: 10px 0;">
            Холмс расследует — Ватсон ведёт протокол: сверка журнала, штата и задач с фактами git.
          </p>
          <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
            <button id="watson-run-btn" style="font-size: 0.82rem; padding: 7px 14px; background: rgba(147,197,253,0.14); color: #93c5fd; border: 1px solid rgba(147,197,253,0.4); border-radius: 6px; cursor: pointer;"><span>📝 Сверить хронику</span></button>
            <span id="watson-run-status" style="font-size: 0.8rem; color: #8b96a5;"></span>
          </div>
          <div id="watson-report-box" style="margin-top: 10px;"></div>
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
        ${buildHunterObservatoryHTML()}
      `;

    case "holmesStudy":
      return `
        <div class="glass-panel" style="border-left: 4px solid var(--accent-rose);">
          <div class="panel-label">${data.investigationHeading || "Активное расследование"}</div>
          <h4 style="color: #fb7185;" id="holmes-branch"><span style="color: #94a3b8;">Выясняю, где сыщик ведёт наблюдение…</span></h4>
          <div style="font-family: var(--font-mono); font-size: 0.85rem; color: #a7f3d0; margin-top: 10px;" id="holmes-tree"></div>
          <p style="color: #cbd5e1; font-size: 0.95rem; margin: 12px 0;">
            ${data.agentHolmes || ""}
          </p>
          <div style="font-family: var(--font-mono); font-size: 0.85rem; color: #fef08a; background: rgba(0,0,0,0.3); padding: 10px; border-radius: 6px; margin-top: 10px;" id="holmes-verdict"></div>
          <div style="display: flex; gap: 10px; align-items: center; margin-top: 12px; flex-wrap: wrap;">
            <button class="btn-action-primary" id="holmes-run-btn"><span>🔎 ${data.runBtn || "Собрать улики"}</span></button>
            <span id="holmes-run-status" style="font-size: 0.8rem; color: #8b96a5;"></span>
          </div>
        </div>
        <div class="glass-panel" style="border-left: 4px solid var(--accent-rose); margin-top: 14px;">
          <div class="panel-label">${data.reportsHeading || "Отчёты аудита"}</div>
          <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-top: 10px;">
            <select id="holmes-report-select" style="background: rgba(0,0,0,0.35); color: #cbd5e1; border: 1px solid rgba(255,255,255,0.15); border-radius: 6px; padding: 8px 10px; font-family: var(--font-mono); font-size: 0.85rem;">
              <option value="">…</option>
            </select>
            <button class="btn-action-primary" id="holmes-report-btn" disabled>
              <span>${data.viewReportBtn || "Посмотреть отчёт"}</span>
            </button>
          </div>
          <div style="display: flex; align-items: center; gap: 8px; margin-top: 8px;">
            <div id="holmes-report-status" style="font-size: 0.8rem; color: #8b96a5;"></div>
            <button id="holmes-fullscreen-btn" style="display: none; margin-left: auto; background: rgba(0,0,0,0.35); color: #8b96a5; border: 1px solid rgba(255,255,255,0.15); border-radius: 6px; padding: 3px 9px; font-size: 0.72rem; cursor: pointer;">${data.fullscreenBtn || "⤢ Во весь экран"}</button>
          </div>
          <pre id="holmes-report-view" style="display: none; max-height: 340px; overflow: auto; white-space: pre-wrap; word-break: break-word; font-family: var(--font-mono); font-size: 0.78rem; line-height: 1.55; color: #cfd7e1; background: rgba(0,0,0,0.35); padding: 12px; border-radius: 6px; margin-top: 10px;"></pre>
          <div id="holmes-initiatives" style="display: none; margin-top: 14px; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 10px;">
            <div class="panel-label" style="font-size: 0.7rem;">${data.initiativesHeading || "Инициативы Холмса"}</div>
            <div id="holmes-initiatives-hint" style="font-size: 0.75rem; color: #8b96a5; margin-top: 4px;">${data.initiativesHint || ""}</div>
            <div id="holmes-initiatives-list" style="margin-top: 8px; display: flex; flex-direction: column; gap: 6px;"></div>
            <div style="display: flex; gap: 10px; align-items: center; margin-top: 10px; flex-wrap: wrap;">
              <button class="btn-action-primary" id="holmes-implement-btn" disabled>
                <span>${data.initiativeSendBtn || "🚀 Отправить на реализацию"}</span>
              </button>
              <span id="holmes-implement-status" style="font-size: 0.8rem; color: #8b96a5;"></span>
            </div>
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

    case "tradingQuarter":
      return buildTradingQuarterHTML(data);

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
function buildHunterObservatoryHTML() {
  const esc = (s) => escapeHtml(s || "");
  const r = (typeof EVO_HUNTER_REPORT !== "undefined") ? EVO_HUNTER_REPORT : null;
  if (!r || !r.generatedAt) {
    return `
      <div class="glass-panel" style="border-left: 4px solid var(--accent-amber); margin-top: 14px;">
        <div class="panel-label">🔭 ДОКЛАД ХАНТЕРА — ВНЕШНИЙ МИР</div>
        <p style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.5;">
          Доклад не сформирован. Генератор: <code>python tools/hunter/report.py</code> (запуск из корня Platform).
        </p>
      </div>
    `;
  }
  const c = r.counts || {};
  const chip = (label, value) => `
    <span style="display:inline-block; padding:3px 9px; margin:0 6px 6px 0; background:rgba(0,0,0,0.25); border:1px solid rgba(255,255,255,0.08); border-radius:5px; font-family:var(--font-mono); font-size:0.74rem; color:#cbd5e1;">${esc(label)}: <b style="color:#5eead4;">${esc(String(value ?? 0))}</b></span>`;
  const subHead = (text, extra) => `
    <div class="panel-label" style="font-size:0.68rem; margin-top:10px;${extra || ""}">${text}</div>`;
  const linkRow = (item, meta) => `
    <div style="padding:4px 0; font-size:0.83rem; line-height:1.45; border-top:1px solid rgba(255,255,255,0.05);">
      <a href="${esc(item.url)}" target="_blank" rel="noopener" style="color:#93c5fd;">${esc(item.title)}</a>
      <span style="color:var(--text-muted); font-size:0.75rem;"> — ${esc(meta)}</span>
    </div>`;
  const o = r.observatory || {};
  const salaries = (o.salaries || []).map((i) => linkRow(i, [i.source, i.salary].filter(Boolean).join(", "))).join("");
  const persp = (o.perspective || []).map((i) => linkRow(i, [i.category, i.source, i.date].filter(Boolean).join(", "))).join("");
  const olx = (o.olx || []).map((i) => linkRow(i, [i.price, i.city].filter(Boolean).join(", "))).join("");
  const queue = (o.queue || []).map((i) => `
    <div style="padding:4px 0; font-size:0.83rem; line-height:1.45; border-top:1px solid rgba(255,255,255,0.05); color:#cbd5e1;">· ${esc(i.title)} <span style="color:var(--text-muted); font-size:0.75rem;"> — ${esc(i.category)}</span></div>`).join("");
  return `
    <div class="glass-panel" style="border-left: 4px solid var(--accent-amber); margin-top: 14px;">
      <div class="panel-label">🔭 ДОКЛАД ХАНТЕРА — ВНЕШНИЙ МИР</div>
      <p style="color:#cbd5e1; font-size:0.9rem; line-height:1.5; margin:8px 0 10px;">${esc(r.headline)}</p>
      <div>
        ${chip("перспективные", c.perspective || 0)}
        ${chip("основные", c.main || 0)}
        ${chip("с вилкой", c.jobsWithSalary || 0)}
        ${chip("OLX", c.olxItems || 0)}
        ${chip("поручения", c.queue || 0)}
      </div>
      ${salaries ? subHead("С ВИЛКОЙ — БЫСТРЕЕ К ДЕНЬГАМ") + salaries : ""}
      ${persp ? subHead("ПЕРСПЕКТИВНЫЕ") + persp : ""}
      ${olx ? subHead("OLX — ПОДРАБОТКИ") + olx : ""}
      ${queue ? subHead("ОЧЕРЕДЬ ПОРУЧЕНИЙ") + queue : ""}
      <p style="font-family:var(--font-mono); font-size:0.72rem; color:var(--text-muted); margin-top:12px;">
        Доклад: ${esc(r.generatedAt)} • снимок ${esc(r.snapshot || "—")} • полная часть: Workspace/analytics/hunter/digest.json
      </p>
    </div>
  `;
}

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
      ${buildAgentBlock(brief.agent)}
      ${brief.aiUsage ? buildAiUsageSummaryHTML(brief.aiUsage) : ""}

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

      <!-- Раздел ВНЕШНИЙ МИР (выжимка Хантера, масса — на Observatory) -->
      ${brief.hunter ? `
      <div class="brief-section" id="section-hunter">
        <div class="brief-section-header" onclick="toggleBriefSection('section-hunter')">
          <span>🔭 ВНЕШНИЙ МИР (ХАНТЕР)</span>
          <span class="arrow">▶</span>
        </div>
        <div class="brief-section-content">
          <p style="color: var(--text-secondary); font-size: 0.85rem; line-height: 1.5;">
            ${escMulti(brief.hunter.headline)}
          </p>
          ${(brief.hunter.top || []).map((i) => `
            <div class="brief-task-item">
              <div class="brief-task-title">
                <a href="${safeUrl(i.url)}" target="_blank" rel="noopener" style="color:#93c5fd;">${esc(i.title)}</a>
              </div>
              <div class="brief-task-details" style="display:block; border:none; margin:0; padding:0;">
                ${esc([i.salary, i.category, i.source].filter(Boolean).join(" • "))}
              </div>
            </div>`).join("")}
          <p style="font-family:var(--font-mono); font-size:0.72rem; color:var(--text-muted); margin-top:8px;">
            Полная часть: Observatory → Доклад Хантера • ${esc(brief.hunter.generatedAt)}
          </p>
        </div>
      </div>` : ""}

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

function buildAiUsageSummaryHTML(usage) {
  const esc = (value) => escapeHtml(value === null || value === undefined ? "нет данных" : String(value));
  const costs = (usage.costs || []).length
    ? usage.costs.map((cost) => `${esc(cost.amount)} ${esc(cost.currency)}`).join(", ")
    : "нет подтверждённых сумм";
  const tokens = usage.total_tokens === null || usage.total_tokens === undefined
    ? "нет данных от провайдеров"
    : new Intl.NumberFormat(currentLanguage === "en" ? "en-US" : "ru-RU").format(usage.total_tokens);
  return `
    <div class="glass-panel" style="border-left:4px solid var(--accent-cyan); margin:0 0 14px;">
      <div class="panel-label">${currentLanguage === "en" ? "AI USAGE · RECORDED DATA" : "УЧЁТ ИИ · ЗАПИСАННЫЕ ДАННЫЕ"}</div>
      <p style="color:var(--text-secondary); line-height:1.55;">
        ${currentLanguage === "en" ? "Recorded requests:" : "Записано запросов:"} ${esc(usage.request_count)} ·
        ${currentLanguage === "en" ? "known token total:" : "известно токенов:"} ${tokens} ·
        ${currentLanguage === "en" ? "confirmed API cost:" : "подтверждённая стоимость API:"} ${costs}
      </p>
      <p style="color:var(--text-muted); font-size:0.8rem; margin-top:6px;">
        ${currentLanguage === "en" ? "Missing values are unknown, not zero." : "Недостающие значения неизвестны, это не ноль."}
      </p>
    </div>`;
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

// A-02 (аудит 06.11, CWE-79): URL из внешних фидов в href — только http(s), иначе "#".
function safeUrl(value) {
  const raw = String(value == null ? "" : value).trim();
  return /^(https?:)?\/\//i.test(raw) ? escapeHtml(raw) : "#";
}
/** Экскурсия по рейсам агентов (запрос Sovereign 07.11): визуальный граф
 * «откуда всё шло → как реализовывалось» внутри AI Sandbox. Данные —
 * window.EVO_EXCURSION из excursion-data.js (генератор
 * tools/barrymore/build-excursion.py, источник — events.jsonl + карточки). */
function initSandboxExcursion() {
  const root = document.getElementById("sandbox-excursion-root");
  if (!root || root.dataset.ready) return;
  const data = window.EVO_EXCURSION;
  if (!data || !Array.isArray(data.flights) || !data.flights.length) {
    root.innerHTML = '<div style="color:var(--text-muted); font-size:0.86rem;">Нет снимка. Перегенерируй: python tools/barrymore/build-excursion.py</div>';
    return;
  }
  root.dataset.ready = "1";
  const flightsHtml = data.flights.map(excursionFlightHtml).join("");
  root.innerHTML = `
    <style>
      .exc-flight { margin-bottom: 22px; }
      .exc-head { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; margin-bottom: 4px; }
      .exc-title { color: #fff; font-size: 0.95rem; font-weight: 600; }
      .exc-verdict { font-size: 0.68rem; padding: 2px 9px; border-radius: 20px; border: 1px solid rgba(52,211,153,0.5); color: #34d399; }
      .exc-sub { color: var(--text-muted, #7d8aa0); font-size: 0.74rem; margin-bottom: 10px; }
      .exc-flow { display: flex; align-items: stretch; flex-wrap: wrap; gap: 6px; }
      .exc-node { background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.12); border-radius: 9px; padding: 7px 10px; cursor: pointer; min-width: 86px; transition: border-color 0.12s ease; }
      .exc-node:hover { border-color: rgba(94,234,212,0.55); }
      .exc-node.is-open { border-color: rgba(94,234,212,0.9); }
      .exc-node-time { font-family: var(--font-mono); font-size: 0.62rem; color: var(--text-muted, #7d8aa0); }
      .exc-node-label { color: #eef2f7; font-size: 0.78rem; margin-top: 2px; }
      .exc-arrow { align-self: center; color: #475569; font-size: 0.85rem; padding: 0 2px; }
      .exc-node.exc-kind-idea { border-left: 3px solid #67e8f9; }
      .exc-node.exc-kind-spec { border-left: 3px solid #c4b5fd; }
      .exc-node.exc-kind-agent { border-left: 3px solid #fbbf24; }
      .exc-node.exc-kind-lane { border-left: 3px solid #7dd3fc; min-width: 200px; flex: 1; }
      .exc-node.exc-kind-storm { border-left: 3px solid #fb7185; }
      .exc-node.exc-kind-storm .exc-node-label { color: #fb7185; }
      .exc-node.exc-kind-artifact { border-left: 3px solid #a7f3d0; }
      .exc-node.exc-kind-finish { border-left: 3px solid #34d399; }
      .exc-node.exc-kind-accept { border-left: 3px solid #5eead4; }
      .exc-chips { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 6px; }
      .exc-chip { font-size: 0.68rem; color: #bae6fd; background: rgba(56,189,248,0.1); border: 1px solid rgba(56,189,248,0.3); border-radius: 7px; padding: 2px 7px; cursor: pointer; }
      .exc-chip:hover { border-color: rgba(56,189,248,0.7); }
      .exc-chip.is-open { background: rgba(56,189,248,0.25); }
      .exc-detail { margin-top: 10px; background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.08); border-radius: 9px; padding: 10px 12px; color: #cbd5e1; font-size: 0.8rem; line-height: 1.55; }
      .exc-detail:empty { display: none; }
      .exc-detail b { color: #fff; }
      .exc-detail .exc-refs { margin-top: 6px; display: flex; flex-direction: column; gap: 2px; }
      .exc-detail .exc-refs code { font-family: var(--font-mono); font-size: 0.7rem; color: #94a3b8; }
    </style>
    ${flightsHtml}`;
  wireExcursionClicks(root);
}

function excursionFlightHtml(flight) {
  const nodes = flight.nodes.map((node, i) => {
    const arrow = i > 0 ? '<div class="exc-arrow">→</div>' : "";
    if (node.kind === "lane" && Array.isArray(node.chips)) {
      const chips = node.chips.map((chip, ci) =>
        `<span class="exc-chip" role="button" tabindex="0" data-flight="${escapeHtml(flight.id)}" data-node="${i}" data-chip="${ci}">${escapeHtml(chip.name)}</span>`
      ).join("");
      return `${arrow}<div class="exc-node exc-kind-lane" data-flight="${escapeHtml(flight.id)}" data-node="${i}">
        <div class="exc-node-time">${escapeHtml(node.time || "")}</div>
        <div class="exc-node-label">${escapeHtml(node.label)}</div>
        <div class="exc-chips">${chips}</div>
      </div>`;
    }
    return `${arrow}<div class="exc-node exc-kind-${escapeHtml(node.kind)}" role="button" tabindex="0" data-flight="${escapeHtml(flight.id)}" data-node="${i}">
      <div class="exc-node-time">${escapeHtml(node.time || "")}</div>
      <div class="exc-node-label">${escapeHtml(node.label)}</div>
    </div>`;
  }).join("");
  return `
    <div class="exc-flight" data-flight-id="${escapeHtml(flight.id)}">
      <div class="exc-head"><span class="exc-title">${escapeHtml(flight.title)}</span><span class="exc-verdict">${escapeHtml(flight.verdict)}</span></div>
      <div class="exc-sub">${escapeHtml(flight.subtitle || "")}</div>
      <div class="exc-flow">${nodes}</div>
      <div class="exc-detail" data-detail-for="${escapeHtml(flight.id)}"></div>
    </div>`;
}

function wireExcursionClicks(root) {
  const data = window.EVO_EXCURSION;
  const showDetail = (flightId, nodeIdx, chipIdx) => {
    const flight = (data.flights || []).find((f) => f.id === flightId);
    if (!flight) return;
    const node = flight.nodes[nodeIdx];
    if (!node) return;
    let title = node.label, time = node.time || "", detail = node.detail || "", refs = node.refs || [];
    if (typeof chipIdx === "number" && Array.isArray(node.chips) && node.chips[chipIdx]) {
      const chip = node.chips[chipIdx];
      title = chip.name; detail = chip.detail || ""; refs = chip.refs || node.refs || [];
    }
    if (Array.isArray(node.files) && node.files.length && !detail) {
      detail = node.files.map((f) =>
        `${f.path}${f.private ? " — приватная зона (путь без содержимого)" : f.size != null ? ` — ${f.size} байт` : f.exists ? "" : " — нет на диске"}`
      ).join("; ");
    }
    const drawer = root.querySelector(`[data-detail-for="${flightId}"]`);
    if (!drawer) return;
    drawer.innerHTML = `<b>${escapeHtml(title)}</b>${time ? ` <span style="color:var(--text-muted); font-size:0.72rem;">· ${escapeHtml(time)}</span>` : ""}<div style="margin-top:4px;">${escapeHtml(detail || "деталей нет")}</div>` +
      (refs.length ? `<div class="exc-refs">${refs.map((r) => `<code>${escapeHtml(r)}</code>`).join("")}</div>` : "");
  };
  root.querySelectorAll(".exc-node, .exc-chip").forEach((el) => {
    el.addEventListener("click", (e) => {
      e.stopPropagation();
      root.querySelectorAll(".is-open").forEach((x) => x.classList.remove("is-open"));
      el.classList.add("is-open");
      showDetail(el.dataset.flight, Number(el.dataset.node),
        el.dataset.chip != null ? Number(el.dataset.chip) : undefined);
    });
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); el.click(); }
    });
  });
}
