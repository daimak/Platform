/* ==========================================================================
   COMMAND CENTER — штаб поместья.
   Топливо:  GET /api/tokens/usage (фактура model-io, кэш 60 с на сервере)
   Конвейер: GET /api/agents/live + /api/agents/history («Флот в море»)
   Радар:    GET /api/darkwatch (суточные счётчики и топы, безличные данные)
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
      { date: '09.11', text: 'Рокфеллер нанят (финансовый советник) — паспорт + штат v4 готовы', ask: 'слово на пилот: первый дайджест «положение казны»' },
      { date: '06.11', text: 'Higgsfield живой кадр — аккаунт и ключ готовы, потолок $1', ask: 'слово «запускай» — вернётся оценка пушки $50–200/ролик' },
      { date: '06.11', text: 'Kali-эпик отложен («хвосты прежде мощного эпика»)', ask: 'ждёт «запускай» — замок открыт, SSH готов' },
      { date: '08.11', text: 'Шлюпки-минизадачи в Обсерватории — проба пера', ask: 'понравилось? подключим живой канбан /api/tasks' },
      { date: '08.11', text: 'Расширение мира назревает', ask: 'что за мир — чтобы приготовить место в реестре и меню' },
      { date: '09.11', text: '14 драфт-миров ждут выбор №/комбо/концепт (worlds-draft)', ask: 'обзор http://127.0.0.1:8765/worlds-draft/index.html' },
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

  var BUDGET_FULL_M = 500;  // полный бюджет после пополнения 14.11 (500M); правится полем в панели
  var BALANCE_SEED_M = 500; // оценка остатка до ввода точного баланса (сид − расход за день)
  var balanceInput = document.getElementById('cc-balance-input');
  var balanceSaved = document.getElementById('cc-balance-saved');
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

  function renderTokens(usage, budgetData) {
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

    // Источник остатка: СТОР бюджета (сервер, выживает ротацию фактуры) →
    // localStorage (офлайн-фолбэк) → сид. Фактура отвечает только за темп
    // (инцидент 16.11: ротация съела историю и дашборд стал врать про остаток).
    var budget = budgetData || {};
    var budgetOk = typeof budget.balance_m === 'number' && budget.balance_m > 0;
    var balance = loadBalance();
    var isEstimate = !budgetOk && !(balance && balance.balance > 0);
    var balM = budgetOk ? budget.balance_m : (balance && balance.balance > 0 ? balance.balance : BALANCE_SEED_M);
    var capM = budgetOk && budget.cap_m > 0 ? budget.cap_m : BUDGET_FULL_M;

    // темп сжигания: свои показания (≥2, разнос ≥6 ч) → фактура недели → «—»
    var daysLeft = null;
    var paceM = null;
    var readings = budgetOk && Array.isArray(budget.readings) ? budget.readings : [];
    if (readings.length >= 2) {
      var firstR = readings[0], lastR = readings[readings.length - 1];
      var spanH = (new Date(lastR.at) - new Date(firstR.at)) / 3600000;
      if (spanH >= 6 && lastR.balance_m < firstR.balance_m) {
        paceM = (firstR.balance_m - lastR.balance_m) / (spanH / 24);
      }
    }
    if (paceM === null && week > 0) paceM = week / 7 / 1000000;
    if (paceM !== null && paceM > 0) daysLeft = balM / paceM;
    var burnout = daysLeft === null ? '—'
      : daysLeft >= 2 ? '~' + Math.round(daysLeft) + ' дн'
      : '~' + Math.max(1, Math.round(daysLeft * 24)) + ' ч';
    document.getElementById('cc-burnout').textContent = burnout;

    // бюджет-полоса: против полного бюджета (как на счётчике: 372M из 500M)
    var haveEl = document.getElementById('cc-budget-have');
    var spentEl = document.getElementById('cc-budget-spent');
    var haveNum = document.getElementById('cc-budget-have-num');
    var spentNum = document.getElementById('cc-budget-spent-num');
    var havePct = capM > 0 ? Math.max(0, Math.min(100, balM / capM * 100)) : 100;
    haveEl.style.width = havePct.toFixed(1) + '%';
    spentEl.style.width = (100 - havePct).toFixed(1) + '%';
    haveNum.textContent = (isEstimate ? '≈' : '') + Math.round(balM) + 'M / ' + Math.round(capM) + 'M';
    spentNum.textContent = fmtNum((capM - balM) * 1000000) + ' · с пополнения';

    // кольцо: СЖИГАНИЕ от полного бюджета — дуга = потрачено, пустое = свежий счётчик.
    // Источник — стор бюджета: ротация фактуры не влияет (инцидент 16.11).
    var leftNowM = isEstimate ? Math.max(0, balM - today / 1000000) : balM;
    var spentPct = capM > 0 ? Math.max(0, Math.min(100, (capM - leftNowM) / capM * 100)) : null;
    var gaugeFill = document.getElementById('cc-gauge-fill');
    var gaugeEl = document.getElementById('cc-gauge');
    var C = 2 * Math.PI * 52;
    var ratio = spentPct === null ? 0 : Math.max(0.02, Math.min(1, spentPct / 100));
    gaugeFill.style.strokeDashoffset = String(C * (1 - ratio));
    document.getElementById('cc-gauge-value').textContent =
      spentPct === null ? '—' : (isEstimate ? '≈' : '') + Math.round(spentPct) + '%';
    document.getElementById('cc-gauge-label').textContent = 'сожжено';
    gaugeEl.classList.toggle('storm', spentPct !== null && (spentPct >= 85 || (daysLeft !== null && daysLeft < 3)));
    gaugeEl.classList.toggle('warn', spentPct !== null && spentPct >= 70 && spentPct < 85);

    // огонь бюджета — та же цифра и формат, что в solomon.html («Мир сейчас»),
    // одна формула: последний час / день / остаток / хватит на N ч. При введённом
    // точном балансе считает от него, иначе от сида BALANCE_SEED_M.
    var burnLine = document.getElementById('cc-burn-line');
    if (burnLine) {
      var lastHour = hours.length ? hours[hours.length - 1].tokens : 0;
      var prevHour = hours.length > 1 ? hours[hours.length - 2].tokens : 0;
      var leftT = leftNowM * 1000000;
      var leftPct = leftNowM / capM * 100;
      var hoursLeft = lastHour > 0 ? leftT / lastHour : null;
      var fmtM = function (t) { return (t / 1000000).toFixed(1); };
      burnLine.innerHTML = 'огонь за час: <b>' + fmtM(lastHour) + 'M</b>'
        + (prevHour ? ' (пред. ' + fmtM(prevHour) + 'M)' : '')
        + ' · за день: <b>' + fmtM(today) + 'M</b>'
        + ' · сожжено: <b>' + Math.round(100 - leftPct) + '%</b> · остаток: <b>' + (isEstimate ? '≈' : '') + fmtM(leftT) + 'M (' + Math.round(leftPct) + '% от ' + Math.round(capM) + 'M)</b>'
        + (hoursLeft !== null ? ' ≈ <b>' + (hoursLeft < 48 ? '<span style="color:#f87171">' + Math.round(hoursLeft) + ' ч</span>' : Math.round(hoursLeft / 24) + ' дн') + '</b> при текущей скорости' : '');
    }
    balanceSaved.textContent = budgetOk
      ? 'в сторе · точное, введено ' + fmtDayClock(budget.updated_at)
      : (isEstimate
        ? 'оценка ' + BALANCE_SEED_M + 'M — введи точный остаток (уйдёт в стор на сервере)'
        : 'введено ' + fmtDayClock(balance.saved_at) + ' · только локально, введи ещё раз — уйдёт в стор');
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
    if (record) {
      fetch('/api/tokens/budget', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ balance_m: value, cap_m: 500 })
      }).then(function (r) { return r.ok ? r.json() : null; }).then(function (b) {
        if (b && typeof b.balance_m === 'number') {
          lastBudget = b;
          renderTokens(lastUsage || { per_day: [], per_hour: [] }, b);
        }
      }).catch(function () { /* офлайн — localStorage держит до следующего ввода */ });
    }
    renderTokens(lastUsage || { per_day: [], per_hour: [] }, lastBudget || {});
  });

  /* --- Конвейер + артефакты ------------------------------------------------------ */

  var lastUsage = null;
  var lastBudget = null;

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
          + '<span class="ship-task">' + escapeHtml(s.task || '') + (s.owner ? ' · отв: ' + escapeHtml(s.owner) : '') + '</span>'
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

  /* --- Сторож: кто сейчас работает (6 слоёв /api/steward) ----------------------------- */

  function renderSteward(data) {
    var watchEl = document.getElementById('cc-watch');
    if (!watchEl) return;
    var rows = [];
    function row(cls, name, value) {
      rows.push('<li class="' + cls + '"><span class="w-dot"></span>'
        + '<span class="w-name">' + escapeHtml(name) + '</span>'
        + '<span class="w-val">' + value + '</span></li>');
    }

    if (!data) {
      row('err', 'Сторож', 'сводка недоступна — сервер без эндпоинта /api/steward (нужен рестарт)');
    } else {
      var runtimes = Array.isArray(data.runtimes) ? data.runtimes : [];
      runtimes.forEach(function (r) {
        var code = r.returncode;
        var state = r.running ? '<b>работает</b>'
          : code === null || code === undefined ? 'покой'
          : code === 0 ? 'покой · последний прогон ок'
          : '<span style="color:#f87171">падение (код ' + escapeHtml(code) + ')</span>';
        row(r.running ? 'live' : code === 0 || code === null ? '' : 'err', r.name, state);
      });

      var proc = data.processes;
      if (proc) {
        var nAgents = (proc.agent_processes || []).length;
        var servers = proc.dashboard_servers || 0;
        row(nAgents ? 'live' : '', 'Процессы',
          'агентов в процессах: <b>' + nAgents + '</b>' + (nAgents ? ' · ' + escapeHtml(proc.agent_processes.join(', ')) : '')
          + ' · серверов: ' + servers);
      } else {
        row('err', 'Процессы', 'слой не собрался');
      }

      var sched = data.scheduler;
      if (sched) {
        row(sched.status ? 'live' : '', 'Планировщик',
          sched.found ? escapeHtml(sched.status || 'состояние неизвестно') : 'задача автостарта не найдена');
      } else {
        row('err', 'Планировщик', 'слой не собрался');
      }

      var auto = data.automations;
      if (auto) {
        row(auto.enabled_count ? 'live' : '', 'Кроны ZCode',
          'включено: <b>' + auto.enabled_count + '</b>' + (auto.enabled_count
            ? ' · ' + (auto.enabled || []).map(function (a) { return escapeHtml(a.title || a.id); }).join('; ')
            : ''));
      } else {
        row('err', 'Кроны ZCode', 'слой не собрался (база занята?)');
      }

      var sess = data.sessions;
      if (sess) {
        var fresh = sess.newest_age_min === null ? '—' : sess.newest_age_min + ' мин назад';
        row(sess.alive ? 'live' : sess.idle ? 'warm' : '', 'Сессии ZCode',
          'живых: <b>' + sess.alive + '</b> · остывших: ' + sess.idle + ' · свежайшая: ' + fresh);
      } else {
        row('err', 'Сессии ZCode', 'слой не собрался');
      }

      var journal = data.journal;
      if (journal) {
        var last = (journal.tail || []).length ? journal.tail[journal.tail.length - 1] : '';
        row('warm', 'Журнал сервера', journal.size_kb + ' КБ · ' + escapeHtml(String(last).slice(0, 120) || 'пусто'));
      } else {
        row('err', 'Журнал сервера', 'слой не собрался');
      }
    }
    watchEl.innerHTML = rows.join('');
    document.getElementById('cc-steward-updated').textContent =
      'сверка: ' + fmtClock(data ? data.generated_at : new Date().toISOString());
  }

  /* --- Тёмный радар: суточные счётчики (/api/darkwatch) ----------------------------- */

  function renderDarkwatch(data) {
    var feed = data && data.feed ? data.feed : null;
    var groups = data && data.groups ? data.groups : null;
    var dateEl = document.getElementById('cc-darkwatch-date');
    dateEl.textContent = data && data.date ? 'срез ' + data.date.split('-').reverse().join('.') : 'среза нет';

    var victims = document.getElementById('cc-dw-victims');
    var topEl = document.getElementById('cc-dw-top');
    var dls = document.getElementById('cc-dw-dls');
    var groupsEl = document.getElementById('cc-dw-groups');
    var topGroups = feed && Array.isArray(feed.top_groups) ? feed.top_groups : [];
    victims.textContent = feed ? fmtNum(feed.last24) : '—';
    topEl.textContent = topGroups.length ? topGroups[0][0] : '—';
    dls.textContent = groups ? fmtNum(groups.live_dls) : '—';
    groupsEl.textContent = groups ? fmtNum(groups.total) : '—';

    var listEl = document.getElementById('cc-dw-top-list');
    if (!feed || !topGroups.length) {
      listEl.innerHTML = '<li><span class="cc-muted">срез ещё не собран — цифры появятся после суточного прогона</span></li>';
      return;
    }
    var maxCount = topGroups[0][1] || 1;
    listEl.innerHTML = topGroups.map(function (pair, index) {
      var share = Math.max(4, Math.round((pair[1] / maxCount) * 100));
      return '<li>'
        + '<span class="dw-rank">' + (index + 1) + '</span>'
        + '<span class="dw-name">' + escapeHtml(pair[0]) + '</span>'
        + '<span class="dw-bar"><i style="width:' + share + '%"></i></span>'
        + '<span class="dw-count">' + fmtNum(pair[1]) + '</span></li>';
    }).join('');

    // подробности прямо в панели: страны + старейшая запись в корме
    var extraEl = document.getElementById('cc-dw-extra');
    if (extraEl) {
      var countries = Array.isArray(feed.top_countries) ? feed.top_countries.slice(0, 4) : [];
      var bits = [];
      if (countries.length) {
        bits.push('страны: ' + countries.map(function (pair) {
          return '<b>' + escapeHtml(pair[0]) + '</b> ' + fmtNum(pair[1]);
        }).join(' · '));
      }
      if (feed.oldest_in_feed) {
        bits.push('старейшая запись в корме: ' + escapeHtml(feed.oldest_in_feed));
      }
      extraEl.innerHTML = bits.length ? bits.join('<br>') : '';
    }
  }

  /* --- Обновление ------------------------------------------------------------------------ */

  function showError(message) {
    statusEl.hidden = false;
    statusEl.textContent = message;
  }

  function refresh() {
    document.getElementById('cc-menu-refresh').disabled = true;
    var tokensPromise = Promise.all([
      fetchJson('/api/tokens/usage').catch(function () { return { per_day: [], per_hour: [] }; }),
      fetchJson('/api/tokens/budget').catch(function () { return {}; }),
    ]).then(function (results) {
      lastUsage = results[0];
      lastBudget = results[1];
      renderTokens(results[0], results[1]);
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
    var stewardPromise = fetchJson('/api/steward')
      .then(renderSteward)
      .catch(function () { renderSteward(null); });
    var radarPromise = fetchJson('/api/darkwatch')
      .then(renderDarkwatch)
      .catch(function (error) {
        document.getElementById('cc-darkwatch-date').textContent =
          'панель поднимется после рестарта сервера (' + error.message + ')';
        document.getElementById('cc-dw-top-list').innerHTML =
          '<li><span class="cc-muted">сводка недоступна</span></li>';
      });
    Promise.all([tokensPromise, fleetPromise, stewardPromise, radarPromise]).finally(function () {
      statusEl.hidden = true;
      updatedEl.textContent = 'обновлено в ' + fmtClock(new Date().toISOString());
      document.getElementById('cc-menu-refresh').disabled = false;
      if (isStatic && window.requestAnimationFrame) { /* один кадр уже отрисован */ }
    });
  }

  /* --- Меню 🧭 (навигация/тема/обновление) и темы (localStorage cc_theme_v1) --- */
  var THEME_ORDER = ['dawn', 'orchid', 'alliance', 'bunker'];
  var THEME_TITLE = { dawn: 'Рассвет', orchid: 'Орхидея', alliance: 'Альянс', bunker: 'Бункер' };
  function currentTheme() {
    try {
      var t = localStorage.getItem('cc_theme_v1');
      return THEME_ORDER.indexOf(t) >= 0 ? t : 'dawn';
    } catch (e) { return 'dawn'; }
  }
  function applyTheme(t) {
    document.querySelector('.cc-page').setAttribute('data-theme', t);
    var nameEl = document.getElementById('cc-menu-theme-name');
    if (nameEl) nameEl.textContent = THEME_TITLE[t];
    if (typeof ffReadColor === 'function') ffReadColor();
  }
  applyTheme(currentTheme());

  var navBtn = document.getElementById('cc-nav-btn');
  var navMenu = document.getElementById('cc-nav-menu');
  function closeMenu() { if (navMenu) navMenu.hidden = true; }
  if (navBtn && navMenu) {
    navBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      navMenu.hidden = !navMenu.hidden;
    });
    document.addEventListener('click', function (e) {
      if (!navMenu.hidden && !navMenu.contains(e.target)) closeMenu();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closeMenu();
    });
  }
  document.getElementById('cc-menu-refresh').addEventListener('click', function () {
    closeMenu();
    refresh();
  });
  document.getElementById('cc-menu-theme').addEventListener('click', function () {
    var next = THEME_ORDER[(THEME_ORDER.indexOf(currentTheme()) + 1) % THEME_ORDER.length];
    try { localStorage.setItem('cc_theme_v1', next); } catch (e) {}
    applyTheme(next);
  });

  /* --- Оживление: светлячки/дыхание/блеск/подъём (localStorage cc_anim_v1) --- */
  var ANIM_KEYS = ['fireflies', 'breath', 'shimmer', 'lift'];
  var animState = null;
  try { animState = JSON.parse(localStorage.getItem('cc_anim_v1')); } catch (e) { animState = null; }
  animState = Object.assign({ fireflies: true, breath: true, shimmer: true, lift: true }, animState || {});
  function saveAnims() { try { localStorage.setItem('cc_anim_v1', JSON.stringify(animState)); } catch (e) {} }

  var ffCanvas = null, ffRaf = 0, ffParts = [], ffColor = '#d4b24c';
  function ffReadColor() {
    try {
      var c = getComputedStyle(document.querySelector('.cc-page')).getPropertyValue('--cc-accent').trim();
      if (c) ffColor = c;
    } catch (e) {}
  }
  window.addEventListener('resize', function () {
    if (ffCanvas) { ffCanvas.width = window.innerWidth; ffCanvas.height = window.innerHeight; }
  });
  function startFireflies() {
    if (ffCanvas) return;
    ffCanvas = document.createElement('canvas');
    ffCanvas.id = 'cc-fireflies';
    document.querySelector('.cc-page').appendChild(ffCanvas);
    ffCanvas.width = window.innerWidth;
    ffCanvas.height = window.innerHeight;
    ffReadColor();
    var ctx = ffCanvas.getContext('2d');
    var i;
    for (i = 0; i < 26; i++) ffParts.push({
      x: Math.random() * ffCanvas.width, y: Math.random() * ffCanvas.height,
      vy: -(0.15 + Math.random() * 0.35), sway: Math.random() * Math.PI * 2,
      sr: 0.003 + Math.random() * 0.006, r: 1 + Math.random() * 1.8, a: 0.15 + Math.random() * 0.5
    });
    var hidden = false;
    document.addEventListener('visibilitychange', function () { hidden = document.hidden; });
    function tick(t) {
      ffRaf = requestAnimationFrame(tick);
      if (hidden) return;
      ctx.clearRect(0, 0, ffCanvas.width, ffCanvas.height);
      for (var j = 0; j < ffParts.length; j++) {
        var p = ffParts[j];
        p.y += p.vy; p.sway += p.sr; p.x += Math.sin(p.sway) * 0.3;
        if (p.y < -10) { p.y = ffCanvas.height + 10; p.x = Math.random() * ffCanvas.width; }
        ctx.beginPath();
        ctx.fillStyle = ffColor;
        ctx.globalAlpha = p.a * (0.55 + 0.45 * Math.sin(t / 700 + j));
        ctx.shadowColor = ffColor; ctx.shadowBlur = 8;
        ctx.arc(p.x, p.y, p.r, 0, 6.283);
        ctx.fill();
        ctx.globalAlpha = 1; ctx.shadowBlur = 0;
      }
    }
    ffRaf = requestAnimationFrame(tick);
  }
  function stopFireflies() {
    if (ffRaf) cancelAnimationFrame(ffRaf);
    ffRaf = 0;
    if (ffCanvas) { ffCanvas.remove(); ffCanvas = null; ffParts = []; }
  }
  function applyAnims() {
    var page = document.querySelector('.cc-page');
    ANIM_KEYS.forEach(function (k) { page.classList.toggle('anim-' + k, !!animState[k]); });
    var toggles = document.querySelectorAll('.cc-menu-toggle');
    for (var i = 0; i < toggles.length; i++) {
      var k = toggles[i].getAttribute('data-anim');
      toggles[i].classList.toggle('on', !!animState[k]);
    }
    if (animState.fireflies) startFireflies(); else stopFireflies();
  }
  var toggleBtns = document.querySelectorAll('.cc-menu-toggle');
  for (var ti = 0; ti < toggleBtns.length; ti++) {
    toggleBtns[ti].addEventListener('click', function () {
      var k = this.getAttribute('data-anim');
      animState[k] = !animState[k];
      saveAnims();
      applyAnims();
    });
  }
  applyAnims();

  renderState();
  var stored = loadBalance();
  if (stored && stored.balance) balanceInput.value = stored.balance;
  refresh();
  if (!isStatic) setInterval(refresh, REFRESH_MS);
})();
