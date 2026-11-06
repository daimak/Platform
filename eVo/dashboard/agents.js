/* ==========================================================================
   «Флот в море» — панель запущенных агентов.
   ТЗ: Docs/AGENT-FLEET-PLAN-2026-11-05-ZCode.md (карточка agents-fleet).
   Данные: GET /api/agents/live + GET /api/agents/history (dashboard-server.py,
   единственный источник — Workspace/logs/events.jsonl; панель — читатель).
   Автообновление каждые 15 с, кнопка «Обновить сейчас».
   Чужие скрипты дашборда (app.js, brief.js, languages.js, ...) не трогаются.
   ========================================================================== */
(function () {
  'use strict';

  const REFRESH_MS = 15000;
  const HISTORY_LIMIT = 20;

  const KIND_LABELS = {
    'agent.started': 'старт',
    'agent.lane': 'лейн',
    'agent.pulse': 'маячок',
    'agent.storm': 'шторм',
    'agent.finished': 'финиш',
  };

  const PULSE_CLASSES = {
    'идёт': 'fleet-badge-pulse-go',
    'тихо': 'fleet-badge-pulse-calm',
    'шторм': 'fleet-badge-pulse-storm',
  };

  const seaEl = document.getElementById('fleet-sea');
  const harborEl = document.getElementById('fleet-harbor');
  const statusEl = document.getElementById('fleet-status');
  const updatedEl = document.getElementById('fleet-updated');
  const refreshBtn = document.getElementById('fleet-refresh');
  const countSeaEl = document.getElementById('fleet-count-sea');
  const countStormEl = document.getElementById('fleet-count-storm');
  const countHarborEl = document.getElementById('fleet-count-harbor');

  function escapeHtml(value) {
    return String(value === null || value === undefined ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function kindSlug(kind) {
    return String(kind || '').replace(/\./g, '-');
  }

  function fmtMinutes(min) {
    if (min === null || min === undefined || Number.isNaN(Number(min))) return '—';
    const value = Math.max(0, Math.round(Number(min)));
    if (value < 60) return value + ' мин';
    return Math.floor(value / 60) + ' ч ' + (value % 60) + ' мин';
  }

  function fmtClock(ts) {
    if (!ts) return '—';
    const date = new Date(ts);
    if (Number.isNaN(date.getTime())) return escapeHtml(ts);
    return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  function fmtDayClock(ts) {
    if (!ts) return '—';
    const date = new Date(ts);
    if (Number.isNaN(date.getTime())) return escapeHtml(ts);
    return date.toLocaleString('ru-RU', {
      day: '2-digit', month: '2-digit',
      hour: '2-digit', minute: '2-digit',
    });
  }

  async function fetchJson(url) {
    const response = await fetch(url, { cache: 'no-store' });
    if (!response.ok) {
      throw new Error('HTTP ' + response.status);
    }
    return response.json();
  }

  /* --- Корабли в море ----------------------------------------------------- */

  function shipBadge(ship) {
    if (ship.status === 'шторм') {
      return '<span class="fleet-badge fleet-badge-storm" '
        + 'title="Шторм: storm-событие без finished либо тишина &gt;30 мин">⛈ ШТОРМ</span>';
    }
    return '<span class="fleet-badge fleet-badge-sea" title="Корабль в море">⛵ МОРЕ</span>';
  }

  function lanesBlock(ship) {
    const lanes = ship.lanes || {};
    const done = Number(lanes.done) || 0;
    const total = lanes.total === null || lanes.total === undefined ? null : Number(lanes.total);
    let width = 0;
    let caption;
    let unknown = false;
    if (total !== null && total > 0) {
      width = Math.max(0, Math.min(100, Math.round((done / total) * 100)));
      caption = 'лейны: ' + done + '/' + total;
    } else if (total === 0) {
      caption = 'лейны: 0/0';
    } else {
      unknown = true;
      width = done > 0 ? 100 : 0;
      caption = 'лейны закрыты: ' + done + ' (итог не заявлен)';
    }
    return '<div class="fleet-lanes' + (unknown ? ' fleet-lanes-unknown' : '') + '">'
      + '<div class="fleet-lanes-scale"><div class="fleet-lanes-fill" style="width:' + width + '%"></div></div>'
      + '<span class="fleet-lanes-caption">' + escapeHtml(caption) + '</span>'
      + '</div>';
  }

  function tapeItem(event) {
    const kind = event.kind || '';
    const label = KIND_LABELS[kind] || kind || '?';
    const time = fmtClock(event.ts);
    return '<li>'
      + '<span class="fleet-tape-kind ' + kindSlug(kind) + '">' + escapeHtml(label) + '</span>'
      + '<span class="fleet-tape-text" title="' + escapeHtml(event.text || '') + '">' + escapeHtml(event.text || '') + '</span>'
      + '<time>' + time + '</time>'
      + '</li>';
  }

  function shipCard(ship) {
    const storms = Number(ship.storms) || 0;
    const pulseClass = PULSE_CLASSES[ship.pulse_status] || '';
    const eta = ship.eta_min === null || ship.eta_min === undefined
      ? '—'
      : '~' + fmtMinutes(ship.eta_min);
    const recent = Array.isArray(ship.events_recent) ? ship.events_recent : [];
    return '<article class="fleet-ship' + (ship.status === 'шторм' ? ' storm' : '') + '">'
      + '<header class="fleet-ship-head">'
      + '<span class="fleet-ship-icon">⛵</span>'
      + '<div class="fleet-ship-name">'
      + '<strong>' + escapeHtml(ship.by) + '</strong>'
      + '<span class="fleet-ship-task">' + escapeHtml(ship.task || 'задача не объявлена') + '</span>'
      + '</div>'
      + '<div class="fleet-ship-badges">'
      + shipBadge(ship)
      + (ship.pulse_status
        ? '<span class="fleet-badge ' + pulseClass + '">пульс: ' + escapeHtml(ship.pulse_status) + '</span>'
        : '')
      + '</div>'
      + '</header>'
      + '<div class="fleet-ship-metrics">'
      + '<div class="fleet-metric"><span class="fleet-metric-label">в море</span>'
      + '<strong>' + fmtMinutes(ship.elapsed_min) + '</strong></div>'
      + '<div class="fleet-metric"><span class="fleet-metric-label">посл. событие</span>'
      + '<strong>' + (ship.pulse_min === null || ship.pulse_min === undefined ? '—' : fmtMinutes(ship.pulse_min) + ' назад') + '</strong></div>'
      + '<div class="fleet-metric' + (storms > 0 ? ' storm-metric' : '') + '">'
      + '<span class="fleet-metric-label">штормы</span>'
      + '<strong>' + (storms > 0 ? '⛈ ' : '') + storms + '</strong></div>'
      + '<div class="fleet-metric"><span class="fleet-metric-label">ETA (оценка)</span>'
      + '<strong>' + eta + '</strong></div>'
      + '</div>'
      + lanesBlock(ship)
      + '<ul class="fleet-tape">' + (recent.map(tapeItem).join('') || '<li><span class="fleet-tape-text">событий пока нет</span></li>') + '</ul>'
      + '</article>';
  }

  function renderLive(payload) {
    const ships = Array.isArray(payload && payload.ships) ? payload.ships : [];
    countSeaEl.textContent = String(ships.length);
    const storming = ships.filter(function (ship) { return ship.status === 'шторм'; }).length;
    countStormEl.textContent = String(storming);
    if (!ships.length) {
      seaEl.innerHTML = '<p class="fleet-empty">Море пусто: ни один корабль не пишет события '
        + 'agent.* в журнал. Кто не пишет события — для панели не существует (ТЗ).</p>';
      return;
    }
    seaEl.innerHTML = ships.map(shipCard).join('');
  }

  /* --- Причалы ------------------------------------------------------------ */

  function verdictBadge(verdict) {
    if (!verdict) return '';
    const normalized = String(verdict).toLowerCase();
    const cls = normalized.indexOf('принято') >= 0
      ? 'fleet-badge-verdict-accepted'
      : normalized.indexOf('доработ') >= 0 ? 'fleet-badge-verdict-rework' : '';
    return '<span class="fleet-badge ' + cls + '">' + escapeHtml(verdict) + '</span>';
  }

  function chainStep(step, index, array) {
    const kind = step.kind || '';
    const label = KIND_LABELS[kind] || kind || '?';
    const cls = ['fleet-chain-step'];
    if (step.role === 'initial') cls.push('fleet-chain-initial');
    if (step.role === 'final') cls.push('fleet-chain-final');
    if (kind === 'agent.storm') cls.push('storm-step');
    const tip = (step.ts ? step.ts + ' · ' : '') + (step.text || '');
    const arrow = index < array.length - 1 ? '<span class="fleet-chain-arrow">→</span>' : '';
    return '<span class="' + cls.join(' ') + '" title="' + escapeHtml(tip) + '">'
      + escapeHtml(label) + (step.text ? ': ' + escapeHtml(String(step.text).slice(0, 60)) : '')
      + '</span>' + arrow;
  }

  function dockedCard(voyage) {
    const lanes = voyage.lanes || {};
    const lanesCaption = lanes.total !== null && lanes.total !== undefined
      ? lanes.done + '/' + lanes.total
      : String(lanes.done || 0) + ' (итог не заявлен)';
    const files = Array.isArray(voyage.files) && voyage.files.length
      ? voyage.files.length + ' шт.'
      : null;
    const tests = voyage.tests === null || voyage.tests === undefined
      ? null
      : (Array.isArray(voyage.tests) ? voyage.tests.join(', ') : String(voyage.tests)).slice(0, 80);
    const facts = [];
    facts.push('старт: <b>' + fmtDayClock(voyage.started_at) + '</b>');
    facts.push('финиш: <b>' + fmtDayClock(voyage.finished_at) + '</b>');
    if (voyage.minutes !== null && voyage.minutes !== undefined) {
      facts.push('в море: <b>' + fmtMinutes(voyage.minutes) + '</b>');
    }
    facts.push('лейны: <b>' + escapeHtml(lanesCaption) + '</b>');
    facts.push('штормы: <b>' + (Number(voyage.storms) || 0) + '</b>');
    if (voyage.tokens !== null && voyage.tokens !== undefined) {
      facts.push('токены: <b>' + escapeHtml(String(voyage.tokens)) + '</b>');
    }
    if (files) facts.push('файлы: <b>' + files + '</b>');
    if (tests) facts.push('тесты: <b>' + escapeHtml(tests) + '</b>');
    const chain = Array.isArray(voyage.chain) ? voyage.chain : [];
    return '<article class="fleet-docked">'
      + '<header class="fleet-docked-head">'
      + '<span class="fleet-ship-icon">⚓</span>'
      + '<strong>' + escapeHtml(voyage.by) + '</strong>'
      + '<span class="fleet-docked-task" title="' + escapeHtml(voyage.task || '') + '">'
      + escapeHtml(voyage.task || 'задача не объявлена') + '</span>'
      + verdictBadge(voyage.verdict)
      + '</header>'
      + '<div class="fleet-docked-facts">' + facts.join(' ') + '</div>'
      + '<p class="fleet-chain">'
      + (chain.map(chainStep).join('') || '<span class="fleet-chain-step">цепочка пуста</span>')
      + '</p>'
      + '</article>';
  }

  function renderHistory(payload) {
    const voyages = Array.isArray(payload && payload.voyages) ? payload.voyages : [];
    countHarborEl.textContent = String(voyages.length);
    if (!voyages.length) {
      harborEl.innerHTML = '<p class="fleet-empty">Причалы пусты: ни одного завершённого рейса '
        + '(событие agent.finished) в журнале ещё нет.</p>';
      return;
    }
    harborEl.innerHTML = voyages.map(dockedCard).join('');
  }

  /* --- Обновление --------------------------------------------------------- */

  function showError(message) {
    statusEl.hidden = false;
    statusEl.textContent = message;
  }

  async function refresh() {
    refreshBtn.disabled = true;
    try {
      const live = await fetchJson('/api/agents/live');
      const history = await fetchJson('/api/agents/history?limit=' + HISTORY_LIMIT);
      renderLive(live);
      renderHistory(history);
      statusEl.hidden = true;
      updatedEl.textContent = 'обновлено в ' + new Date().toLocaleTimeString('ru-RU', {
        hour: '2-digit', minute: '2-digit', second: '2-digit',
      });
    } catch (error) {
      showError('Не удалось получить флот (' + error.message + '). '
        + 'Живой сервер 127.0.0.1:8765 отвечает? Повтор через 15 с или кнопкой «Обновить сейчас».');
    } finally {
      refreshBtn.disabled = false;
    }
  }

  refreshBtn.addEventListener('click', refresh);
  refresh();
  setInterval(refresh, REFRESH_MS);
})();
