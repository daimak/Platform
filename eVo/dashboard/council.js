/* ==========================================================================
   ПРАВЛЕНИЕ (council.html): зал совета управляющих Estate.
   Читает /api/council (состав + сводка собраний) и /api/council/<id>
   (протокол). Действия CEO-0: созвать собрание, правка к пункту,
   вердикт по пункту, смена фазы. Доклады/возражения/сводку пишет
   диспетчер диспута теми же POST-роутами. Темы — cc_theme_v1 со штабом.
   ========================================================================== */
(function () {
  'use strict';

  var FALLBACK_PHASES = ['созвано', 'доклады', 'возражения', 'сводка', 'вердикты', 'закрыто'];
  var REVISIONS = [['a', 'Обсидиан'], ['b', 'Чертёж'], ['c', 'Ателье']];
  var state = { board: null, meetings: [], meeting: null, activeId: null, members: {}, dispatch: {} };

  function esc(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function setStatus(message) {
    var el = document.getElementById('cw-status');
    if (!el) return;
    if (!message) { el.hidden = true; el.textContent = ''; return; }
    el.hidden = false; el.textContent = message;
  }

  function apiGet(url) {
    return fetch(url, { cache: 'no-store' }).then(function (res) {
      return res.json().then(function (data) {
        if (!res.ok) throw new Error(data && data.error ? data.error : 'HTTP ' + res.status);
        return data;
      });
    });
  }

  function apiPost(url, payload) {
    return fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }).then(function (res) {
      return res.json().then(function (data) {
        if (!res.ok) throw new Error(data && data.error ? data.error : 'HTTP ' + res.status);
        return data;
      });
    });
  }

  /* --- Ревизия дизайна (свой localStorage, не темы штаба) --- */
  function applyRev(code) {
    var body = document.querySelector('.cw-body');
    if (body) body.setAttribute('data-rev', code);
    try { localStorage.setItem('council_rev_v1', code); } catch (e) {}
    var rev = REVISIONS.filter(function (r) { return r[0] === code; })[0] || REVISIONS[0];
    var btn = document.getElementById('cw-rev');
    if (btn) btn.textContent = '◆ ' + rev[1];
  }
  function initRev() {
    var saved = null;
    try { saved = localStorage.getItem('council_rev_v1'); } catch (e) {}
    applyRev(REVISIONS.some(function (r) { return r[0] === saved; }) ? saved : 'a');
  }

  /* --- Табель: этажи CEO --- */
  function renderFloors() {
    var box = document.getElementById('cw-floors');
    var members = (state.board && state.board.members) || [];
    var levels = (state.board && state.board.levels) || {};
    var attendees = state.meeting ? (state.meeting.attendees || []) : [];
    var byLevel = {};
    members.forEach(function (m) { (byLevel[m.ceo] = byLevel[m.ceo] || []).push(m); });
    var html = '';
    Object.keys(byLevel).sort(function (a, b) { return a - b; }).forEach(function (lvl) {
      var label = levels['CEO-' + lvl] ? 'CEO-' + lvl + ' · ' + levels['CEO-' + lvl] : 'CEO-' + lvl;
      html += '<div class="cw-floor"><p class="cw-floor-label">' + esc(label) + '</p>';
      byLevel[lvl].forEach(function (m) {
        var inMeeting = attendees.indexOf(m.id) >= 0;
        var dispatching = m.id === 'barrymore' && state.dispatch && state.dispatch.running;
        html += '<div class="cw-seat' + (inMeeting ? ' cw-in-meeting' : '') + (dispatching ? ' cw-dispatching' : '') + '" data-agent="' + esc(m.id) + '" title="CEO-' + m.ceo + (m.critic ? ' · право рассуждения' : '') + (m.id === 'barrymore' ? ' · щелкни — соберёт диспут' : '') + '">'
          + '<span class="cw-pulse"></span>'
          + '<span><strong>' + esc(m.name) + '</strong><em>' + esc(m.role) + '</em></span>'
          + '<span class="cw-ceo-badge">CEO-' + m.ceo + '</span>'
          + '</div>';
      });
      html += '</div>';
    });
    box.innerHTML = html;
  }

  /* --- Собрание --- */
  function phaseIndex(meeting) {
    var phases = meeting.phases || FALLBACK_PHASES;
    return Math.max(0, phases.indexOf(meeting.phase || 'созвано'));
  }

  function renderMeeting() {
    var box = document.getElementById('cw-meeting');
    var meeting = state.meeting;
    if (!meeting) { box.innerHTML = '<p class="cw-meta">Собраний пока нет — созывай кнопкой справа.</p>'; return; }
    var phases = meeting.phases || FALLBACK_PHASES;
    var nowIdx = phaseIndex(meeting);
    var nameOf = function (id) {
      var m = state.members[id];
      return m ? m.name : id;
    };

    var html = '<h3 class="cw-topic">' + esc(meeting.topic) + '</h3>';
    html += '<p class="cw-meta">Созвано ' + esc((meeting.created || '').replace('T', ' ').slice(0, 16))
      + ' · состав: ' + (meeting.attendees || []).map(function (id) { return esc(nameOf(id)); }).join(', ')
      + (meeting.moderator ? ' · модератор: ' + esc(nameOf(meeting.moderator)) : '')
      + (meeting.secretary ? ' · протокол: ' + esc(nameOf(meeting.secretary)) : '') + '</p>';

    html += '<div class="cw-phase-bar">';
    phases.forEach(function (p, i) {
      html += '<span class="cw-phase' + (i === nowIdx ? ' cw-now' : (i < nowIdx ? ' cw-done' : '')) + '">' + esc(p) + '</span>';
    });
    html += '</div>';

    (meeting.agenda || []).forEach(function (point, idx) {
      html += '<div class="cw-point" data-point="' + idx + '">'
        + '<h4><span class="cw-num">' + (idx + 1) + '</span>' + esc(point.title) + '</h4>';
      (point.reports || []).forEach(function (r) {
        html += '<div class="cw-speech"><div class="cw-who">' + esc(nameOf(r.agent)) + ' · доклад</div><p>' + esc(r.text) + '</p></div>';
      });
      if (point.ceo_edit) {
        html += '<div class="cw-edit-plate"><div class="cw-who">Правка CEO-0</div><p>' + esc(point.ceo_edit.text) + '</p></div>';
      }
      (point.objections || []).forEach(function (o) {
        html += '<div class="cw-speech cw-obj"><div class="cw-who">' + esc(nameOf(o.agent)) + ' · возражение</div><p>' + esc(o.text) + '</p></div>';
      });
      if (point.verdict) {
        html += '<span class="cw-verdict-chip" data-v="' + esc(point.verdict.verdict) + '">' + esc(point.verdict.verdict) + '</span>';
        if (point.verdict.note) html += '<p class="cw-verdict-note">' + esc(point.verdict.note) + '</p>';
      } else {
        html += '<div class="cw-actions">'
          + '<button class="cw-btn" type="button" data-act="verdict-toggle">⚖ Вердикт</button>'
          + '<button class="cw-btn" type="button" data-act="edit-toggle">✍ Правка</button>'
          + '</div>'
          + '<div class="cw-verdict-form">'
          + '<input class="cw-note" type="text" maxlength="1000" placeholder="Примечание к вердикту (необязательно)">'
          + '<div>'
          + '<button class="cw-btn" type="button" data-act="verdict" data-v="принято">✅ Принято</button>'
          + '<button class="cw-btn" type="button" data-act="verdict" data-v="доработка">🔧 Доработка</button>'
          + '<button class="cw-btn" type="button" data-act="verdict" data-v="отклонено">❌ Отклонено</button>'
          + '<button class="cw-btn" type="button" data-act="verdict" data-v="на моё решение">👑 На моё решение</button>'
          + '</div></div>'
          + '<div class="cw-edit-form"><textarea class="cw-ta" maxlength="4000" placeholder="Правка CEO-0 к пункту"></textarea>'
          + '<div class="cw-actions"><button class="cw-btn cw-primary" type="button" data-act="edit">Внести правку</button></div></div>';
      }
      html += '</div>';
    });

    (meeting.summary || []).forEach(function (s) {
      html += '<div class="cw-summary-block"><div class="cw-who">' + esc(nameOf(s.agent)) + ' · сводка модератора</div><p>' + esc(s.text) + '</p></div>';
    });

    var nextPhase = nowIdx < phases.length - 1 ? phases[nowIdx + 1] : null;
    if (nextPhase) {
      html += '<div class="cw-actions"><button class="cw-btn" type="button" data-act="phase">⏭ Фаза → ' + esc(nextPhase) + '</button></div>';
    }

    var log = (meeting.log || []).slice(-5);
    if (log.length) {
      html += '<div class="cw-log">' + log.map(function (row) {
        return esc((row.ts || '').replace('T', ' ').slice(0, 16)) + ' · ' + esc(row.event);
      }).join('<br>') + '</div>';
    }

    box.innerHTML = html;
  }

  function renderMeetingPicks() {
    var box = document.getElementById('cw-meeting-picks');
    box.innerHTML = state.meetings.map(function (m) {
      return '<button class="cw-meeting-pick' + (m.id === state.activeId ? ' cw-active' : '') + '" type="button" data-id="' + esc(m.id) + '">'
        + esc(m.id) + ' · ' + esc(m.topic) + ' · ' + esc(m.phase) + '</button>';
    }).join('');
  }

  /* --- Форма созыва --- */
  function renderAttendeeBoxes() {
    var box = document.getElementById('cw-attendees');
    var members = ((state.board && state.board.members) || []).filter(function (m) { return m.callable; });
    var html = members.map(function (m) {
      var pre = m.id === 'solomon' || m.id === 'barrymore';
      return '<label class="cw-attendee' + (pre ? ' cw-locked' : '') + '">'
        + '<input type="checkbox" value="' + esc(m.id) + '"' + (pre ? ' checked' : '') + '> '
        + esc(m.name) + '<span class="cw-ceo-badge">CEO-' + m.ceo + '</span></label>';
    }).join('');
    box.innerHTML = '<p class="cw-meta" style="margin:10px 0 4px;">Состав (модератор и протоколист предзазваны):</p>' + html;
  }

  /* --- Данные --- */
  function load() {
    return apiGet('/api/council').then(function (data) {
      state.board = data.board || {};
      state.meetings = data.meetings || [];
      state.dispatch = data.dispatch || {};
      state.members = {};
      (state.board.members || []).forEach(function (m) { state.members[m.id] = m; });
      var current = state.meetings.filter(function (m) { return m.phase !== 'закрыто'; });
      state.activeId = state.activeId && state.meetings.some(function (m) { return m.id === state.activeId; })
        ? state.activeId
        : (current.length ? current[0].id : (state.meetings.length ? state.meetings[0].id : null));
      renderFloors();
      renderMeetingPicks();
      renderAttendeeBoxes();
      return state.activeId ? apiGet('/api/council/' + state.activeId) : null;
    }).then(function (meeting) {
      state.meeting = meeting;
      renderMeeting();
      renderDispatch();
      var el = document.getElementById('cw-updated');
      if (el) el.textContent = 'обновлено ' + new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
    }).catch(function (error) {
      setStatus('Правление недоступно: ' + error.message);
    });
  }

  /* --- Рука Бэрримова: диспут через шлюз :31415 --- */
  function renderDispatch() {
    var btn = document.getElementById('cw-dispatch');
    var running = state.dispatch && state.dispatch.running;
    if (btn) {
      btn.disabled = !!running;
      btn.textContent = running ? '⏳ Бэрримов ведёт диспут…' : '🫖 Диспут Бэрримова';
    }
    if (running) {
      var phase = state.meeting && state.meeting.phase ? state.meeting.phase : '';
      setStatus('Бэрримов ведёт диспут: ' + phase + '…');
    }
  }

  function dispatchRun() {
    if (state.dispatch && state.dispatch.running) return;
    if (!state.activeId) { setStatus('Сначала собери собрание.'); return; }
    var phase = state.meeting && state.meeting.phase;
    if (phase && phase !== 'созвано' && phase !== 'доклады') {
      setStatus('Диспут уже шёл — собери новое собрание.');
      return;
    }
    setStatus('Зову Бэрримова…');
    apiPost('/api/council/run', { id: state.activeId }).then(function () {
      return load();
    }).catch(function (error) { setStatus(error.message); });
  }

  function reloadAll() {
    return load();
  }

  /* --- События --- */
  function bind() {
    document.getElementById('cw-refresh').addEventListener('click', reloadAll);

    document.getElementById('cw-dispatch').addEventListener('click', dispatchRun);
    document.getElementById('cw-floors').addEventListener('click', function (event) {
      var seat = event.target.closest('.cw-seat[data-agent="barrymore"]');
      if (seat) dispatchRun();
    });

    document.getElementById('cw-rev').addEventListener('click', function () {
      var cur = document.querySelector('.cw-body').getAttribute('data-rev') || 'a';
      var idx = REVISIONS.findIndex(function (r) { return r[0] === cur; });
      applyRev(REVISIONS[(idx + 1) % REVISIONS.length][0]);
    });

    document.getElementById('cw-convene-toggle').addEventListener('click', function () {
      document.getElementById('cw-convene').classList.toggle('cw-open');
    });
    document.getElementById('cw-convene-cancel').addEventListener('click', function () {
      document.getElementById('cw-convene').classList.remove('cw-open');
    });

    document.getElementById('cw-convene').addEventListener('submit', function (event) {
      event.preventDefault();
      var topic = document.getElementById('cw-topic').value.trim();
      var agenda = document.getElementById('cw-agenda').value.split('\n').map(function (s) { return s.trim(); }).filter(Boolean);
      var attendees = Array.prototype.slice.call(document.querySelectorAll('#cw-attendees input:checked')).map(function (el) { return el.value; });
      if (!topic || !agenda.length) { setStatus('Нужны тема и хотя бы один пункт повестки.'); return; }
      setStatus('Созываю собрание…');
      apiPost('/api/council/convene', { topic: topic, agenda: agenda, attendees: attendees }).then(function (data) {
        state.activeId = data.id;
        setStatus('');
        return reloadAll();
      }).then(function () {
        setStatus('Собрание созвано. Диспут запускается словом «го собрание» в чате ZCode.');
      }).catch(function (error) {
        setStatus('Созыв не прошёл: ' + error.message);
      });
    });

    document.getElementById('cw-meeting-picks').addEventListener('click', function (event) {
      var btn = event.target.closest('.cw-meeting-pick');
      if (!btn) return;
      state.activeId = btn.getAttribute('data-id');
      renderMeetingPicks();
      apiGet('/api/council/' + state.activeId).then(function (meeting) {
        state.meeting = meeting;
        renderMeeting();
        renderFloors();
      }).catch(function (error) { setStatus(error.message); });
    });

    document.getElementById('cw-meeting').addEventListener('click', function (event) {
      var btn = event.target.closest('[data-act]');
      if (!btn) return;
      var pointEl = btn.closest('.cw-point');
      var point = pointEl ? parseInt(pointEl.getAttribute('data-point'), 10) : null;
      var act = btn.getAttribute('data-act');
      var id = state.activeId;

      if (act === 'verdict-toggle') {
        var form = pointEl.querySelector('.cw-verdict-form');
        if (form) form.classList.toggle('cw-open');
      } else if (act === 'edit-toggle') {
        var editForm = pointEl.querySelector('.cw-edit-form');
        if (editForm) editForm.classList.toggle('cw-open');
      } else if (act === 'verdict') {
        var note = pointEl.querySelector('.cw-note');
        setStatus('Ставлю вердикт…');
        apiPost('/api/council/verdict', {
          id: id, point: point, verdict: btn.getAttribute('data-v'), note: note ? note.value.trim() : ''
        }).then(reloadAll).then(function () { setStatus(''); }).catch(function (error) { setStatus(error.message); });
      } else if (act === 'edit') {
        var ta = pointEl.querySelector('.cw-edit-form textarea');
        if (!ta || !ta.value.trim()) { setStatus('Правка пуста.'); return; }
        setStatus('Вношу правку…');
        apiPost('/api/council/edit', { id: id, point: point, text: ta.value.trim() })
          .then(reloadAll).then(function () { setStatus(''); }).catch(function (error) { setStatus(error.message); });
      } else if (act === 'phase') {
        setStatus('Смена фазы…');
        apiPost('/api/council/status', { id: id, phase: (state.meeting.phases || FALLBACK_PHASES)[phaseIndex(state.meeting) + 1] })
          .then(reloadAll).then(function () { setStatus(''); }).catch(function (error) { setStatus(error.message); });
      }
    });
  }

  initRev();
  bind();
  load();
  (function poll() {
    var running = state.dispatch && state.dispatch.running;
    setTimeout(function () {
      if (!document.hidden && !(state.meeting && state.meeting.phase === 'закрыто')) load();
      poll();
    }, running ? 10000 : 25000);
  })();
})();
