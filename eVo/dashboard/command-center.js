/* ==========================================================================
   COMMAND CENTER — штаб поместья.
   Топливо:  GET /api/tokens/usage (фактура model-io, кэш 60 с на сервере)
   Конвейер: GET /api/agents/live + /api/agents/history («Флот в море»)
   Решения и блокеры: живой список CC_STATE ниже — обновляет ZCode при каждом
   новом развороте (панель только читает, как весь дашборд).
   Остаток счётчика вводится вручную (Sovereign), хранится в localStorage.
   ?static=1 — без автообновления (для скриншотов).
   ========================================================================== */
(function () {
  'use strict';

  var REFRESH_MS = 15000;
  var isStatic = /[?&]static=1/.test(location.search);

  /* --- Живой список развилок и блокеров (обновляет ZCode, дата обязательна) --- */
  var CC_STATE = {
    decisions: [
      { date: '06.11', text: 'Allowlist-фикс events.jsonl (test/done только ZCode)', ask: 'вердикт: да/нет — один рестарт 8765 вместе со Штабом' },
      { date: '06.11', text: 'Higgsfield живой кадр — аккаунт и ключ готовы, потолок $1', ask: 'слово «запускай» — вернётся оценка пушки $50–200/ролик' },
      { date: '06.11', text: 'Kali-эпик отложен («хвосты прежде мощного эпика»)', ask: 'ждёт «запускай» — замок открыт, SSH готов' },
      { date: '08.11', text: 'Шлюпки-минизадачи в Обсерватории — проба пера', ask: 'понравилось? подключим живой канбан /api/tasks' },
      { date: '08.11', text: 'Расширение мира назревает', ask: 'что за мир — чтобы приготовить место в реестре и меню' },
      { date: '08.11', text: 'Некоммиченный пакет: Обсерватория + окно Флота + Штаб', ask: 'осмотреть diff и сказать «коммить»' },
    ],
    blockers: [
      { done: true, text: 'ПИНФЛ оформлен', note: 'самозанятость' },
      { done: true, text: 'SIM-карта', note: '' },
      { done: true, text: 'KYC-рельс изучен', note: '4 урока, Trust Wallet → BestChange' },
      { done: true, text: 'OFFER-KIT собран', note: 'OFFER-KIT-2026-11-08.md' },
      { done: true, text: 'Фабрика продаж', note: '21 артефакт, 10 откликов' },
      { done: false, text: 'Затравочный USDT', note: 'вход в рельс обмена' },
      { done: false, text: 'Тест-сделка', note: 'первый заказ → первый отзыв' },
      { done: false, text: 'Посты-загоны', note: '3 канала, тексты готовы' },
    ],
  };

  var balanceInput = document.getElementById('cc-balance-input');
  var balanceSaved = document.getElementById('cc-balance-saved');
  var sparkline = document.getElementById('cc-sparkline');
  var statusEl = document.getElementById('cc-status');
  var updatedEl = document.getElementById('cc-updated');

  function fmtNum(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
    var n = Number(value);
    if (n >= 1000000) return (n / 1000000).toFixed(n >= 10000000 ? 0 : 1) + 'M';
    if (n >= 1000) return Math.round(n / 1000) + 'K';
    return String(Math.round(n));
  }

  function fmtMinutes(min) {
    if (min === null || min === undefined || Number.isNaN(Number(min))) return '—';
    var v = Math.max(0, Math.round(Number(min)));
    if (v < 60) return v + ' мин';
    return Math.floor(v / 60) + ' ч ' + (v % 60) + ' мин';
  }

  function fmtClock(ts) {
    if (!ts) return '—';
    var d = new Date(ts);
    if (Number.isNaN(d.getTime())) return String(ts);
    return d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  function fmtDayClock(ts) {
    if (!ts) return '—';
    var d = new Date(ts);
    if (Number.isNaN(d.getTime())) return String(ts);
    return d.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
  }

  function escapeHtml(value) {
    return String(value === null || value === undefined ? '' : value)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function fetchJson(url) {
    return fetch(url, { cache: 'no-store' }).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
  }

  /* --- Топливо ------------------------------------------------------------------ */

  function loadBalance() {
    try { return JSON.parse(localStorage.getItem('cc_counter_v1') || 'null'); } catch (e) { return null; }
  }

  function renderTokens(usage) {
    var dayBucket = new Date().toISOString().slice(0, 13).slice(0, 10);
    var today = 0, week = 0, peak = 0, i;
    var days = usage.per_day || [];
    var hours = usage.per_hour || [];
    var todayBucket = new Date().toISOString().slice(0, 10);
    for (i = 0; i < days.length; i++) {
      if (days[i].bucket === todayBucket) today = days[i].tokens;
      week += days[i].tokens;
    }
    for (i = 0; i < hours.length; i++) {
      if (hours[i].tokens > peak) peak = hours[i].tokens;
    }
    document.getElementById('cc-tokens-total').textContent = fmtNum(usage.total_observed);
    document.getElementById('cc-tokens-generated').textContent = 'фактура: ' + fmtClock(usage.generated_at);
    document.getElementById('cc-today').textContent = fmtNum(today);
    document.getElementById('cc-week').textContent = fmtNum(week);
    document.getElementById('cc-peak').textContent = fmtNum(peak);
    document.getElementById('cc-sessions').textContent = String((usage.sessions || []).length);

    // запас хода: остаток (в млн) / средний расход в день (фактура в токенах → млн)
    var balance = loadBalance();
    var activeDays = days.length;
    var burnout = '—';
    var daysLeft = null;
    if (balance && balance.balance > 0 && activeDays > 0 && week > 0) {
      var perDayM = week / activeDays / 1000000; // млн токенов в день
      daysLeft = balance.balance / perDayM;
      burnout = daysLeft >= 2 ? '~' + Math.round(daysLeft) + ' дн' : '~' + Math.max(1, Math.round(daysLeft * 24)) + ' ч';
    }
    document.getElementById('cc-burnout').textContent = burnout;

    // кольцо: запас хода, полное = 30 дней
    var fill = document.getElementById('cc-gauge-fill');
    var gaugeValue = document.getElementById('cc-gauge-value');
    var C = 2 * Math.PI * 52;
    if (balance && balance.balance > 0) {
      gaugeValue.textContent = fmtNum(balance.balance);
      var ratio = daysLeft === null ? 0 : Math.max(0, Math.min(1, daysLeft / 30));
      fill.style.strokeDashoffset = String(C * (1 - ratio));
      if (daysLeft !== null && daysLeft < 3) fill.style.stroke = '#f87171';
      else if (daysLeft !== null && daysLeft < 7) fill.style.stroke = '#fbbf24';
      else fill.style.stroke = '#38bdf8';
      balanceSaved.textContent = balance.saved_at
        ? 'введено ' + fmtDayClock(balance.saved_at)
        : '';
    } else {
      gaugeValue.textContent = '—';
      fill.style.strokeDashoffset = String(C);
      balanceSaved.textContent = 'введи остаток — посчитаю запас хода';
    }

    drawSparkline(hours.slice(-48));
  }

  function drawSparkline(hours) {
    if (!sparkline || !sparkline.getContext) return;
    var dpr = window.devicePixelRatio || 1;
    var w = sparkline.clientWidth || sparkline.offsetWidth || 600;
    var h = 72;
    sparkline.width = Math.round(w * dpr);
    sparkline.height = Math.round(h * dpr);
    var ctx = sparkline.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    if (!hours.length) {
      ctx.fillStyle = 'rgba(148, 163, 184, 0.5)';
      ctx.font = '11px "JetBrains Mono", monospace';
      ctx.fillText('фактуры пока нет', 6, h / 2);
      return;
    }
    var max = 1;
    var i;
    for (i = 0; i < hours.length; i++) if (hours[i].tokens > max) max = hours[i].tokens;
    var gap = 2;
    var barW = Math.max(2, w / hours.length - gap);
    var grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, 'rgba(56, 189, 248, 0.95)');
    grad.addColorStop(1, 'rgba(56, 189, 248, 0.12)');
    for (i = 0; i < hours.length; i++) {
      var barH = Math.max(2, (hours[i].tokens / max) * (h - 14));
      var x = i * (w / hours.length);
      ctx.fillStyle = grad;
      ctx.fillRect(x, h - barH, barW, barH);
      if (hours[i].tokens === max) {
        ctx.fillStyle = 'rgba(125, 211, 252, 0.9)';
        ctx.font = '10px "JetBrains Mono", monospace';
        ctx.fillText(fmtNum(max), Math.min(x, w - 46), h - barH - 3);
      }
    }
  }

  balanceInput.addEventListener('change', function () {
    var value = Number(balanceInput.value);
    var record = Number.isFinite(value) && value > 0
      ? { balance: value, saved_at: new Date().toISOString() }
      : null;
    try {
      if (record) localStorage.setItem('cc_counter_v1', JSON.stringify(record));
      else localStorage.removeItem('cc_counter_v1');
    } catch (e) { /* приватный режим — просто не запоминаем */ }
    renderTokens(lastUsage || { per_day: [], per_hour: [] });
  });

  /* --- Конвейер + артефакты ------------------------------------------------------ */

  var lastUsage = null;

  function pulseClass(ship) {
    if (ship.pulse_status === 'шторм' || ship.status === 'шторм') return 'storm';
    if (ship.pulse_status === 'тихо') return 'calm';
    return 'go';
  }

  function renderFleet(live, history) {
    var ships = Array.isArray(live.ships) ? live.ships : [];
    var voyages = Array.isArray(history.voyages) ? history.voyages : [];
    document.getElementById('cc-count-sea').textContent = String(ships.length);
    var storming = ships.filter(function (s) { return s.status === 'шторм' || s.pulse_status === 'шторм'; }).length;
    document.getElementById('cc-count-storm').textContent = String(storming);
    document.getElementById('cc-count-dock').textContent = String(voyages.length);

    var lanesDone = 0;
    ships.forEach(function (s) { lanesDone += Number((s.lanes || {}).done) || 0; });
    voyages.forEach(function (v) { lanesDone += Number((v.lanes || {}).done) || 0; });
    document.getElementById('cc-lanes-done').textContent = String(lanesDone);

    var shipsEl = document.getElementById('cc-ships');
    if (!ships.length) {
      shipsEl.innerHTML = '<li class="cc-ships-empty">море пусто: ни один агент не пишет agent.* — как выйдут в море, появятся здесь</li>';
    } else {
      shipsEl.innerHTML = ships.slice(0, 6).map(function (s) {
        return '<li><span class="ship-pulse ' + pulseClass(s) + '"></span>'
          + '<span class="ship-name">' + escapeHtml(s.by || 'корабль') + '</span>'
          + '<span class="ship-task">' + escapeHtml(s.task || '') + '</span>'
          + '<span class="cc-muted">' + fmtMinutes(s.elapsed_min) + '</span></li>';
      }).join('');
    }

    var artEl = document.getElementById('cc-artifacts');
    if (!voyages.length) {
      artEl.innerHTML = '<li><span class="cc-muted">причалы пусты: ни одного завершённого рейса в журнале</span></li>';
    } else {
      artEl.innerHTML = voyages.slice(0, 6).map(function (v) {
        var verdict = String(v.verdict || '');
        var low = verdict.toLowerCase();
        var cls = low.indexOf('принято') >= 0 ? '' : low.indexOf('доработ') >= 0 ? 'rework' : '';
        var facts = [];
        if (v.minutes !== null && v.minutes !== undefined) facts.push('в море <b>' + fmtMinutes(v.minutes) + '</b>');
        if (Array.isArray(v.files) && v.files.length) facts.push('файлов <b>' + v.files.length + '</b>');
        if (v.tokens !== null && v.tokens !== undefined) facts.push('токены <b>' + v.tokens + '</b>');
        var lanes = v.lanes || {};
        if (lanes.total !== null && lanes.total !== undefined) facts.push('лейны <b>' + (lanes.done || 0) + '/' + lanes.total + '</b>');
        return '<li><div class="art-head">'
          + '<span class="art-name">⚓ ' + escapeHtml(v.by || '') + '</span>'
          + '<span class="art-verdict ' + cls + '">' + escapeHtml(verdict || fmtDayClock(v.finished_at)) + '</span>'
          + '</div><div class="art-facts">' + facts.join(' ') + '</div></li>';
      }).join('');
    }
  }

  /* --- Решения и блокеры ----------------------------------------------------------- */

  function renderState() {
    document.getElementById('cc-decisions-count').textContent = 'открыто: ' + CC_STATE.decisions.length;
    document.getElementById('cc-decisions').innerHTML = CC_STATE.decisions.map(function (d) {
      return '<li><span class="dec-date">' + escapeHtml(d.date) + '</span> '
        + '<span class="dec-text">' + escapeHtml(d.text) + '</span>'
        + '<span class="dec-ask">↳ ' + escapeHtml(d.ask || '') + '</span></li>';
    }).join('');
    document.getElementById('cc-blockers').innerHTML = CC_STATE.blockers.map(function (b) {
      return '<li class="' + (b.done ? 'bk-done' : 'bk-todo') + '">'
        + '<span class="bk-mark">' + (b.done ? '✓' : '✕') + '</span>'
        + '<span>' + escapeHtml(b.text) + '</span>'
        + (b.note ? '<span class="bk-note">' + escapeHtml(b.note) + '</span>' : '')
        + '</li>';
    }).join('');
  }

  /* --- Сигналы ------------------------------------------------------------------------ */

  function renderTape(live, history) {
    var rows = [];
    var ships = Array.isArray(live.ships) ? live.ships : [];
    ships.forEach(function (s) {
      (s.events_recent || []).forEach(function (e) {
        rows.push({ ts: e.ts, ship: s.by, kind: e.kind, text: e.text, storm: e.kind === 'agent.storm' });
      });
    });
    if (rows.length < 18) {
      (history.voyages || []).some(function (v) {
        var chain = v.chain || [];
        for (var c = chain.length - 1; c >= 0 && rows.length < 18; c--) {
          rows.push({ ts: chain[c].ts, ship: v.by, kind: chain[c].kind, text: chain[c].text, storm: chain[c].kind === 'agent.storm' });
        }
        return rows.length >= 18;
      });
    }
    rows.sort(function (a, b) { return String(b.ts || '').localeCompare(String(a.ts || '')); });
    var tapeEl = document.getElementById('cc-tape');
    if (!rows.length) {
      tapeEl.innerHTML = '<li><span class="cc-muted">журнал молчит — событий пока нет</span></li>';
      return;
    }
    tapeEl.innerHTML = rows.slice(0, 18).map(function (r) {
      var kind = String(r.kind || '').replace('agent.', '') || '?';
      var text = r.text && r.text !== r.kind && r.text !== kind ? kind + ' · ' + r.text : kind;
      return '<li' + (r.storm ? ' class="storm-row"' : '') + '>'
        + '<time>' + fmtClock(r.ts) + '</time>'
        + '<span class="tape-kind">' + escapeHtml(r.ship || '') + '</span>'
        + '<span>' + escapeHtml(text) + '</span></li>';
    }).join('');
  }

  /* --- Обновление ------------------------------------------------------------------------ */

  function showError(message) {
    statusEl.hidden = false;
    statusEl.textContent = message;
  }

  function refresh() {
    document.getElementById('cc-refresh').disabled = true;
    var tokensPromise = fetchJson('/api/tokens/usage').then(function (u) {
      lastUsage = u;
      renderTokens(u);
    }).catch(function (error) {
      document.getElementById('cc-tokens-generated').textContent =
        'панель топлива поднимется после рестарта сервера (' + error.message + ')';
    });
    var fleetPromise = Promise.all([
      fetchJson('/api/agents/live'),
      fetchJson('/api/agents/history?limit=12'),
    ]).then(function (results) {
      renderFleet(results[0], results[1]);
      renderTape(results[0], results[1]);
    }).catch(function (error) {
      showError('Живой сервер 127.0.0.1:8765 не отвечает (' + error.message + ').');
    });
    Promise.all([tokensPromise, fleetPromise]).finally(function () {
      statusEl.hidden = true;
      updatedEl.textContent = 'обновлено в ' + fmtClock(new Date().toISOString());
      document.getElementById('cc-refresh').disabled = false;
      if (isStatic && window.requestAnimationFrame) { /* один кадр уже отрисован */ }
    });
  }

  document.getElementById('cc-refresh').addEventListener('click', refresh);
  window.addEventListener('resize', function () {
    if (lastUsage) drawSparkline((lastUsage.per_hour || []).slice(-48));
  });

  renderState();
  var stored = loadBalance();
  if (stored && stored.balance) balanceInput.value = stored.balance;
  refresh();
  if (!isStatic) setInterval(refresh, REFRESH_MS);
})();
