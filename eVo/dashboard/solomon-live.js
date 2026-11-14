// СОЛОМОН — живые трубы («Мир сейчас»). Опрос 45 с, панель только читает.
// Источники: /api/agents/live (флот), /api/agents/ops (шлюпки под ковром),
// /api/agents/history (причалы), /api/tokens/usage (огонь бюджета).
(function () {
  'use strict';

  const BUDGET_SEED = 440e6;       // сид счётчика (вечер 14.11, из памяти Sovereign)
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const el = (id) => document.getElementById(id);

  const ago = (min) => {
    if (min == null) return '';
    if (min < 1) return 'только что';
    if (min < 60) return Math.round(min) + ' мин назад';
    return Math.floor(min / 60) + ' ч ' + Math.round(min % 60) + ' мин назад';
  };

  const stateDot = (state) => '<span class="sl-dot sl-dot-' + esc(state) + '"></span>';

  function renderSea(ships) {
    const box = el('sl-world-sea');
    if (!ships.length) { box.innerHTML = '<li class="sl-live-empty">море пусто</li>'; return; }
    box.innerHTML = ships.slice(0, 5).map(function (s) {
      const pulse = s.pulse_status || '';
      const owner = s.owner ? ' · отв: ' + esc(s.owner) : '';
      return '<li>' + stateDot(pulse === 'идёт' ? 'writing' : 'idle')
        + '<div><strong>' + esc(s.by) + '</strong>'
        + '<span class="sl-live-sub">' + esc(s.task || '') + owner + '</span>'
        + '<span class="sl-live-sub">' + esc(pulse) + (s.pulse_min != null ? ' · ' + ago(s.pulse_min) : '') + '</span></div></li>';
    }).join('');
  }

  function renderOps(flights) {
    const box = el('sl-world-ops');
    if (!flights.length) { box.innerHTML = '<li class="sl-live-empty">шлюпок не заведено</li>'; return; }
    box.innerHTML = flights.slice(0, 5).map(function (f) {
      return '<li>' + stateDot(f.state)
        + '<div><strong>' + esc(f.task) + '</strong>'
        + '<span class="sl-live-sub">' + esc(f.state === 'writing' ? 'пишет' : 'молчит') + ' · ' + ago(f.age_min) + ' · ' + Math.round(f.bytes / 1024) + ' КБ</span></div></li>';
    }).join('');
  }

  function renderHarbor(voyages) {
    const box = el('sl-world-harbor');
    if (!voyages.length) { box.innerHTML = '<li class="sl-live-empty">причалы пусты</li>'; return; }
    box.innerHTML = voyages.slice(0, 5).map(function (v) {
      const facts = [];
      if (v.minutes != null) facts.push(Math.round(v.minutes) + ' мин');
      if (v.tokens != null) facts.push(v.tokens + 'M');
      return '<li>' + stateDot('harbor')
        + '<div><strong>' + esc(v.by) + '</strong>'
        + '<span class="sl-live-sub">' + esc(v.verdict || v.task || '') + '</span>'
        + (facts.length ? '<span class="sl-live-sub">' + esc(facts.join(' · ')) + '</span>' : '')
        + '</div></li>';
    }).join('');
  }

  function renderBurn(usage) {
    const burnEl = el('sl-live-burn');
    const metaEl = el('sl-world-meta');
    const hours = usage.per_hour || [];
    const last = hours.length ? hours[hours.length - 1] : null;
    const prev = hours.length > 1 ? hours[hours.length - 2] : null;
    const speed = last ? last.tokens : 0;
    const prevSpeed = prev ? prev.tokens : 0;
    const day = (usage.per_day || []).reduce(function (a, d) { return a + (d.tokens || 0); }, 0);
    const left = Math.max(0, BUDGET_SEED - day);
    const hoursLeft = speed > 0 ? (left / speed) : null;
    const fmt = (t) => (t / 1e6).toFixed(1);
    if (burnEl) {
      let msg = 'огонь за час: <b>' + fmt(speed) + 'M</b>'
        + (prevSpeed ? ' (пред. час ' + fmt(prevSpeed) + 'M)' : '')
        + ' · за день: <b>' + fmt(day) + 'M</b>'
        + ' · запас от сида 440M: <b>' + fmt(left) + 'M</b>';
      if (hoursLeft != null) msg += ' ≈ <b>' + (hoursLeft < 48 ? '<span class="sl-burn-warn">' + Math.round(hoursLeft) + ' ч</span>' : Math.round(hoursLeft / 24) + ' дн') + '</b> при текущей скорости';
      burnEl.innerHTML = msg;
    }
    if (metaEl) metaEl.textContent = 'обновлено ' + new Date(usage.generated_at).toLocaleTimeString('ru-RU');
  }

  function getJSON(url) {
    return fetch(url, { cache: 'no-store' }).then(function (r) { return r.json(); });
  }

  function tick() {
    getJSON('/api/tokens/usage').then(renderBurn).catch(function () {
      if (el('sl-world-meta')) el('sl-world-meta').textContent = 'труба топлива недоступна';
    });
    getJSON('/api/agents/live').then(function (d) { renderSea(d.ships || []); }).catch(function () {
      el('sl-world-sea').innerHTML = '<li class="sl-live-empty">труба флота недоступна</li>';
    });
    getJSON('/api/agents/ops').then(function (d) { renderOps(d.flights || []); }).catch(function () {
      el('sl-world-ops').innerHTML = '<li class="sl-live-empty">труба шлюпок недоступна</li>';
    });
    getJSON('/api/agents/history?limit=6').then(function (d) { renderHarbor(d.voyages || []); }).catch(function () {
      el('sl-world-harbor').innerHTML = '<li class="sl-live-empty">труба причалов недоступна</li>';
    });
  }

  tick();
  setInterval(tick, 45000);
})();
