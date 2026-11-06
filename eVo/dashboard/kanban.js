/* Канбан лиджера — доска статусов задач из Memory/Engineering/Tasks/Active.
 * Данные: GET /api/tasks (task_store.dashboard_tasks, поле "all").
 * Движение: POST /api/tasks/<id>/stage/<колонка> (task_store.set_stage).
 * Колонки: analysis → todo → in-progress → test → done (поле stage карточки,
 * терминальность в status active/done; Done↔рабочая колонка = reopen).
 * Drag: pointer-events (мышь и тач), клик без движения = модалка карточки. */
"use strict";

const COLUMNS = [
  { key: "analysis",    label: "Анализ",   dot: "#a78bfa" },
  { key: "todo",        label: "Сделать",  dot: "#38bdf8" },
  { key: "in-progress", label: "В работе", dot: "#fbbf24" },
  { key: "test",        label: "Проверка", dot: "#f472b6" },
  { key: "done",        label: "Готово",   dot: "#34d399" },
];

/* Типы сущностей (Sovereign 2026-11-06, ITIL-минимум): task | change | epic */
const TYPE_LABELS = { task: "Таска", change: "ЗНИ", epic: "Эпик" };
const TYPE_ORDER = ["task", "change", "epic"];

let TASKS = [];
let modalId = null;
let typeFilter = localStorage.getItem("kb-type") || "all";

function typeOf(task) {
  return TYPE_LABELS[task.type] ? task.type : "task";
}

function typeBadgeHtml(task) {
  return typeOf(task) !== "task"
    ? `<span class="kb-badge kb-type-${typeOf(task)}">${TYPE_LABELS[typeOf(task)]}</span>`
    : "";
}

function stageOf(task) {
  if (task.status === "done") return "done";
  return COLUMNS.some((c) => c.key === task.stage) ? task.stage : "todo";
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (ch) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]
  ));
}

function fmtDate(iso) {
  if (!iso) return "—";
  try { return new Date(iso).toLocaleString("ru-RU", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" }); }
  catch (_) { return iso; }
}

function fmtAgo(iso) {
  if (!iso) return "";
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86400000);
  if (days <= 0) return "сегодня";
  const last = days % 10;
  if (days >= 11 && days <= 14) return `${days} дней в работе`;
  if (last === 1) return `${days} день в работе`;
  if (last >= 2 && last <= 4) return `${days} дня в работе`;
  return `${days} дней в работе`;
}

function linkify(s) {
  const str = String(s ?? "");
  if (/^https?:\/\//i.test(str)) {
    return `<a href="${esc(str)}" target="_blank" rel="noopener noreferrer" style="color:#38bdf8;">${esc(str)}</a>`;
  }
  return `<code style="font-size:0.66rem;color:#94a3b8;">${esc(str)}</code>`;
}

/* ---------- доска ---------- */

function cardHtml(task) {
  const pr = task.priority === "urgent" ? "urgent" : "regular";
  const badge = task.status === "done"
    ? '<span class="kb-badge done-badge">DONE</span>'
    : `<span class="kb-badge ${pr}">${pr === "urgent" ? "URGENT" : "REGULAR"}</span>`;
  const source = task.source ? `<span class="kb-badge">${esc(task.source)}</span>` : "";
  return `
    <div class="kb-card ${pr}" data-id="${esc(task.id)}">
      <div class="kb-card-title">${esc(task.title)}</div>
      <div class="kb-card-foot">${badge}${source}${typeBadgeHtml(task)}<span class="kb-card-id">${esc(task.id)}</span></div>
    </div>`;
}

function renderFilters() {
  const box = document.getElementById("kb-filters");
  if (!box) return;
  const buttons = [
    { key: "all", label: "Все", n: TASKS.length },
    ...TYPE_ORDER.map((ty) => ({
      key: ty,
      label: TYPE_LABELS[ty],
      n: TASKS.filter((t) => typeOf(t) === ty).length,
    })),
  ];
  box.innerHTML = buttons.map((b) =>
    `<button class="kb-filter ${b.key === typeFilter ? "current" : ""}" data-type="${b.key}">${b.label} · ${b.n}</button>`
  ).join("");
  box.querySelectorAll(".kb-filter").forEach((btn) => {
    btn.addEventListener("click", () => {
      typeFilter = btn.dataset.type;
      localStorage.setItem("kb-type", typeFilter);
      render();
    });
  });
}

function render() {
  const board = document.getElementById("kb-board");
  const byStage = Object.fromEntries(COLUMNS.map((c) => [c.key, []]));
  const visible = typeFilter === "all" ? TASKS : TASKS.filter((t) => typeOf(t) === typeFilter);
  visible.forEach((t) => byStage[stageOf(t)].push(t));
  renderFilters();

  board.innerHTML = COLUMNS.map((col) => {
    const list = byStage[col.key];
    const cards = list.length
      ? list.map(cardHtml).join("")
      : '<div class="kb-empty">пусто — перетащи сюда</div>';
    return `
      <div class="kb-col" data-stage="${col.key}">
        <div class="kb-col-head">
          <span class="kb-col-dot" style="background:${col.dot}"></span>
          <span>${col.label}</span>
          <span class="kb-col-count">${list.length}</span>
        </div>
        <div class="kb-cards">${cards}</div>
      </div>`;
  }).join("");
  wireDrag();
  if (modalId) openModal(modalId, { keepScroll: true });
}

function toast(text, isErr) {
  const el = document.getElementById("kb-toast");
  el.textContent = text;
  el.classList.toggle("err", Boolean(isErr));
  el.classList.add("show");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => el.classList.remove("show"), 2200);
}

async function loadTasks() {
  const res = await fetch("/api/tasks", { headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  TASKS = data.tasks.all || [];
  const urgent = TASKS.filter((t) => t.status !== "done" && t.priority === "urgent").length;
  document.getElementById("kb-meta").innerHTML =
    `карточек: <b>${TASKS.length}</b> · срочных: <b>${urgent}</b>`;
}

async function moveTask(id, stage) {
  /* Л-5: подпись автора перехода. Без логинов и ролей: loopback, один хозяин —
   * автор декларирует сам; сервер пишет её в history и в журнал событий. */
  const res = await fetch(`/api/tasks/${encodeURIComponent(id)}/stage/${stage}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ by: "Sovereign" }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
  TASKS = data.tasks.all || [];
  render();
  const labels = Object.fromEntries(COLUMNS.map((c) => [c.key, c.label]));
  toast(`${id} → ${labels[stage] || stage}`);
}

/* ---------- drag: pointer-механика (мышь и тач), клик без движения = модалка ---------- */

function wireDrag() {
  document.querySelectorAll(".kb-card").forEach((card) => {
    card.addEventListener("pointerdown", (e) => onDragStart(e, card));
  });
}

function onDragStart(e, card) {
  if (e.button !== undefined && e.button !== 0) return;
  const startX = e.clientX, startY = e.clientY;
  const id = card.dataset.id;
  let ghost = null, hoverCol = null, dragging = false;

  const onMove = (ev) => {
    if (!dragging) {
      if (Math.hypot(ev.clientX - startX, ev.clientY - startY) < 5) return;
      // правило «текст выделяется ВЕЗДЕ»: пока есть живое выделение, drag не стартует;
      // перетаскивание карточки — от пустого места карточки
      let selLen = 0;
      try { selLen = String(getSelection()).length; } catch (err) {}
      if (selLen > 0) return;
      dragging = true;
      const r = card.getBoundingClientRect();
      ghost = card.cloneNode(true);
      ghost.className = card.className + " kb-ghost";
      ghost.style.width = r.width + "px";
      document.body.appendChild(ghost);
      card.classList.add("dragging");
    }
    ev.preventDefault();
    ghost.style.left = (ev.clientX - ghost.offsetWidth / 2) + "px";
    ghost.style.top = (ev.clientY - 14) + "px";
    const under = document.elementFromPoint(ev.clientX, ev.clientY);
    const col = under && under.closest ? under.closest(".kb-col") : null;
    if (hoverCol && hoverCol !== col) hoverCol.classList.remove("dragover");
    if (col && col.dataset.stage && stageOf(TASKS.find((t) => t.id === id)) !== col.dataset.stage) {
      col.classList.add("dragover");
    }
    hoverCol = col;
  };

  const onUp = (ev) => {
    window.removeEventListener("pointermove", onMove);
    window.removeEventListener("pointerup", onUp);
    if (ghost) ghost.remove();
    card.classList.remove("dragging");
    if (hoverCol) hoverCol.classList.remove("dragover");
    if (dragging && hoverCol && hoverCol.dataset.stage) {
      const stage = hoverCol.dataset.stage;
      if (stageOf(TASKS.find((t) => t.id === id)) !== stage) {
        moveTask(id, stage).catch((err) => toast(`Ошибка: ${err.message}`, true));
      }
    } else if (!dragging) {
      openModal(id);
    }
  };

  window.addEventListener("pointermove", onMove);
  window.addEventListener("pointerup", onUp);
}

/* ---------- модалка карточки ---------- */

function openModal(id, opts = {}) {
  const task = TASKS.find((t) => t.id === id);
  modalId = id;
  const root = document.getElementById("kb-modal");
  if (!task) { root.classList.remove("open"); modalId = null; return; }
  const cur = stageOf(task);
  const pr = task.priority === "urgent" ? "urgent" : "regular";

  const metaRow = (label, value) => `
    <div class="kbm-meta-item">
      <div class="kbm-meta-label">${label}</div>
      <div class="kbm-meta-value">${value}</div>
    </div>`;

  const html = `
    <div class="kbm-head">
      <div>
        <div class="kbm-title">${esc(task.title)}</div>
        <div class="kbm-badges">
          ${task.status === "done" ? '<span class="kb-badge done-badge">DONE</span>' : `<span class="kb-badge ${pr}">${pr === "urgent" ? "URGENT" : "REGULAR"}</span>`}
          ${task.source ? `<span class="kb-badge">${esc(task.source)}</span>` : ""}
          ${typeBadgeHtml(task)}
          <span class="kb-badge">${esc(task.id)}</span>
        </div>
      </div>
      <button class="kbm-close" id="kbm-close" aria-label="Закрыть">✕</button>
    </div>

    <div class="kbm-statusbar">
      ${COLUMNS.map((c) => `
        <button class="kbm-stage-btn ${c.key === cur ? "current" : ""}" data-stage="${c.key}" ${c.key === cur ? "disabled" : ""}>
          <span class="kb-col-dot" style="background:${c.dot}"></span>${c.label}
        </button>`).join("")}
    </div>

    <div class="kbm-statusbar">
      ${TYPE_ORDER.map((ty) => `
        <button class="kbm-stage-btn kb-type-btn ${ty === typeOf(task) ? "current" : ""}" data-type="${ty}" ${ty === typeOf(task) ? "disabled" : ""}>${TYPE_LABELS[ty]}</button>`).join("")}
    </div>

    <div class="kbm-meta">
      ${metaRow("Создал", esc(task.source || "—"))}
      ${metaRow("Создана", `${fmtDate(task.createdAt)}<br><span style="color:#7d8aa0;font-size:0.64rem;">${fmtAgo(task.createdAt)}</span>`)}
      ${metaRow("Статус", `${COLUMNS.find((c) => c.key === cur)?.label || cur}${task.status === "done" ? " · закрыта" : ""}`)}
      ${metaRow("Срок исполнения", esc(task.due ? fmtDate(task.due) : "—"))}
      ${metaRow("Ответственный", esc(task.owner || "—"))}
      ${metaRow("Тип", TYPE_LABELS[typeOf(task)] || esc(task.type || "task"))}
      ${metaRow("Закрыта", task.status === "done" ? fmtDate(task.completedAt) : "—")}
    </div>

    ${task.description ? `
      <div class="kbm-section">
        <div class="kbm-sec-title">Для чего</div>
        <div class="kbm-text">${esc(task.description)}</div>
      </div>` : ""}

    ${Array.isArray(task.steps) && task.steps.length ? `
      <div class="kbm-section">
        <div class="kbm-sec-title">Шаги</div>
        ${task.steps.map((s) => `
          <div class="kbm-step">
            <div class="kbm-step-do"><b>${esc(s.n)}.</b> ${esc(s.do)}</div>
            ${s.dod ? `<div class="kbm-step-dod">Готово, когда: ${esc(s.dod)}</div>` : ""}
          </div>`).join("")}
      </div>` : ""}

    ${Array.isArray(task.constraints) && task.constraints.length ? `
      <div class="kbm-section">
        <div class="kbm-sec-title">Красные линии</div>
        ${task.constraints.map((c) => `<div class="kbm-redline">⛔ ${esc(c)}</div>`).join("")}
      </div>` : ""}

    ${Array.isArray(task.links) && task.links.length ? `
      <div class="kbm-section">
        <div class="kbm-sec-title">Связанное</div>
        ${task.links.map((l) => `<div class="kbm-link">${linkify(l)}</div>`).join("")}
      </div>` : ""}

    ${Array.isArray(task.history) && task.history.length ? `
      <div class="kbm-section">
        <div class="kbm-sec-title">История (кто и когда двигал)</div>
        ${[...task.history].reverse().map((h) => `
          <div class="kbm-hist">
            <span class="kbm-hist-when">${fmtDate(h.at)}</span>
            ${h.status === "done" ? '<span class="kb-badge done-badge">DONE</span>'
              : h.status === "reopened" ? `<span class="kb-badge">REOPEN → ${esc(COLUMNS.find((c) => c.key === h.stage)?.label || h.stage || "")}</span>`
              : h.status === "archived" ? '<span class="kb-badge">ARCHIVED</span>'
              : h.type ? `<span class="kb-badge kb-type-${esc(h.type)}">ТИП → ${esc(TYPE_LABELS[h.type] || h.type)}</span>`
              : h.stage ? `<span class="kb-badge">→ ${esc(COLUMNS.find((c) => c.key === h.stage)?.label || h.stage)}</span>`
              : `<span class="kb-badge">${esc(h.status || "")}</span>`}
          </div>`).join("")}
      </div>` : ""}

    ${Array.isArray(task.comments) && task.comments.length ? `
      <div class="kbm-section">
        <div class="kbm-sec-title">Комментарии (${task.comments.length})</div>
        ${[...task.comments].reverse().map((c) => `
          <div class="kbm-comment">
            <div class="kbm-comment-head">
              <b>${esc(c.by || "—")}</b>
              <span class="kbm-hist-when">${fmtDate(c.at)}</span>
            </div>
            <div class="kbm-comment-text">${esc(c.text)}</div>
          </div>`).join("")}
      </div>` : ""}

    <div class="kbm-section">
      <div class="kbm-sec-title">Добавить комментарий</div>
      <textarea class="kbm-comment-input" id="kbm-comment-input" maxlength="2000" rows="3"
        placeholder="Текст комментария…"></textarea>
      <button class="kbm-comment-send" id="kbm-comment-send" type="button">Добавить</button>
    </div>
  `;

  document.getElementById("kbm-body").innerHTML = html;
  root.classList.add("open");
  document.getElementById("kbm-close").addEventListener("click", closeModal);
  const commentSend = document.getElementById("kbm-comment-send");
  if (commentSend) {
    commentSend.addEventListener("click", async () => {
      const input = document.getElementById("kbm-comment-input");
      const text = ((input && input.value) || "").trim();
      if (!text) { toast("Комментарий пуст", true); return; }
      commentSend.disabled = true;
      try {
        const res = await fetch(`/api/tasks/${encodeURIComponent(task.id)}/comments`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ by: "Sovereign", text }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
        TASKS = data.tasks.all || [];
        render();
        toast("Комментарий добавлен");
        openModal(task.id, { keepScroll: true });
      } catch (err) {
        toast(`Ошибка: ${err.message}`, true);
        commentSend.disabled = false;
      }
    });
  }
  root.querySelectorAll(".kbm-stage-btn:not(.current)").forEach((btn) => {
    btn.addEventListener("click", () => {
      moveTask(task.id, btn.dataset.stage)
        .then(() => openModal(task.id, { keepScroll: true }))
        .catch((err) => toast(`Ошибка: ${err.message}`, true));
    });
  });
  root.querySelectorAll(".kb-type-btn:not(.current)").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        const res = await fetch(`/api/tasks/${encodeURIComponent(task.id)}/type`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ by: "Sovereign", type: btn.dataset.type }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
        TASKS = data.tasks.all || [];
        render();
        toast(`Тип: ${TYPE_LABELS[btn.dataset.type] || btn.dataset.type}`);
        openModal(task.id, { keepScroll: true });
      } catch (err) {
        toast(`Ошибка: ${err.message}`, true);
      }
    });
  });
  if (!opts.keepScroll) document.getElementById("kbm-body").scrollTop = 0;
}

function closeModal() {
  modalId = null;
  document.getElementById("kb-modal").classList.remove("open");
}

document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeModal(); });

loadTasks().then(render).catch((err) => {
  document.getElementById("kb-meta").textContent = `Не удалось загрузить задачи: ${err.message}`;
});
