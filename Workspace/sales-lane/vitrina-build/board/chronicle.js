/* ==========================================================================
   ХРОНИКА — интерактивная лента git-истории.
   Данные: window.CHRONICLE (chronicle-data.js, снапшот build-chronicle.py).
   Выбор дня — клик по колонке ленты; фильтр потока — клик по чипу.
   Выходные (последние пт–вс с активностью) подсвечены золотым.
   ========================================================================== */
(function () {
  'use strict';

  var data = window.CHRONICLE;
  var CAT_NAMES = {
    security: 'Безопасность', agents: 'Агенты', worlds: 'Миры',
    money: 'Деньги', infra: 'Инфраструктура', ui: 'Интерфейс', docs: 'Документация',
  };
  var selectedDay = null;
  var catFilter = null;

  function el(id) { return document.getElementById(id); }

  function fmtNum(n) {
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return Math.round(n / 1000) + 'K';
    return String(n);
  }

  function isMerge(c) { return /^Merge /.test(c.s); }

  function escapeHtml(v) {
    return String(v === null || v === undefined ? '' : v)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  /* --- Шапка: счётчики --------------------------------------------------- */

  function renderHeader() {
    el('ch-c-commits').textContent = fmtNum(data.total_commits);
    el('ch-c-days').textContent = String(data.days.length);
    var weekend = data.days.filter(function (d) { return d.date >= '2026-11-07'; });
    el('ch-c-weekend').textContent = String(weekend.reduce(function (s, d) { return s + d.n; }, 0));
    el('ch-c-lines').textContent = '+' + fmtNum(data.total_add) + ' / −' + fmtNum(data.total_del);
    el('ch-generated').textContent = 'собрано ' + data.generated_at.slice(0, 10);
  }

  /* --- Чипы потоков -------------------------------------------------------- */

  function renderCats() {
    var counts = {};
    data.commits.forEach(function (c) { counts[c.c] = (counts[c.c] || 0) + 1; });
    var order = Object.keys(CAT_NAMES).filter(function (k) { return counts[k]; });
    var chips = ['<span class="ch-cat' + (catFilter === null ? ' on' : '')
      + '" data-cat="" role="tab"><b>все</b> ' + data.total_commits + '</span>'];
    order.forEach(function (cat) {
      var meta = data.cats_meta[cat] || {};
      chips.push('<span class="ch-cat' + (catFilter === cat ? ' on' : '')
        + '" data-cat="' + cat + '" role="tab">'
        + '<span class="dot" style="background:' + (meta.color || '#888') + '"></span>'
        + (meta.icon || '') + ' ' + CAT_NAMES[cat] + ' <b>' + counts[cat] + '</b></span>');
    });
    var box = el('ch-cats');
    box.innerHTML = chips.join('');
    box.querySelectorAll('.ch-cat').forEach(function (chip) {
      chip.addEventListener('click', function () {
        var cat = chip.getAttribute('data-cat') || null;
        catFilter = (catFilter === cat || (cat === null && catFilter === null)) ? null : cat;
        renderCats();
        renderDayList();
      });
    });
  }

  /* --- Лента дней ----------------------------------------------------------- */

  function renderRail() {
    var maxN = Math.max.apply(null, data.days.map(function (d) { return d.n; }));
    var rail = el('ch-days-rail');
    rail.innerHTML = data.days.map(function (d) {
      var meta = data.cats_meta[d.top] || { color: '#475569' };
      var h = Math.round(8 + (d.n / maxN) * 120);
      return '<div class="day-col' + (d.date >= '2026-11-07' ? ' weekend' : '')
        + '" data-date="' + d.date + '" title="' + d.date + ': ' + d.n + ' коммит., +'
        + fmtNum(d.a) + ' / −' + fmtNum(d.x) + '">'
        + '<span class="day-count">' + d.n + '</span>'
        + '<span class="day-bar" style="height:' + h + 'px;background:linear-gradient(180deg,'
        + meta.color + ' 0%, rgba(8,20,34,0.9) 130%)"></span>'
        + '<span class="day-label">' + d.date.slice(5).replace('-', '.') + '</span>'
        + '</div>';
    }).join('');
    rail.querySelectorAll('.day-col').forEach(function (col) {
      col.addEventListener('click', function () { selectDay(col.getAttribute('data-date')); });
    });
    rail.scrollLeft = rail.scrollWidth; // свежие дни справа — открыть на них
  }

  function selectDay(date) {
    selectedDay = date;
    var rail = el('ch-days-rail');
    rail.querySelectorAll('.day-col').forEach(function (col) {
      col.classList.toggle('sel', col.getAttribute('data-date') === date);
    });
    renderDayHead();
    renderDayList();
  }

  /* --- Выбранный день ------------------------------------------------------------ */

  function dayCommits(date) {
    return data.commits.filter(function (c) { return c.d === date; });
  }

  function renderDayHead() {
    var commits = dayCommits(selectedDay);
    var day = data.days.find(function (d) { return d.date === selectedDay; }) || { n: commits.length, a: 0, x: 0, top: 'docs' };
    var wd = ['вс', 'пн', 'вт', 'ср', 'чт', 'пт', 'сб'][new Date(selectedDay + 'T12:00:00').getDay()];
    var meta = data.cats_meta[day.top] || {};
    el('ch-day-label').textContent = 'ДЕНЬ · ' + selectedDay.split('-').reverse().join('.') + ' · ' + wd
      + (selectedDay >= '2026-11-07' ? ' · ВЫХОДНЫЕ' : '');
    el('ch-day-title').textContent = (meta.icon || '') + ' ' + commits.length + ' коммитов — доминирует '
      + (CAT_NAMES[day.top] || day.top);
    var merges = commits.filter(isMerge).length;
    el('ch-day-summary').textContent = '+' + fmtNum(day.a) + ' / −' + fmtNum(day.x) + ' строк'
      + (merges ? ' · merge: ' + merges : '');
  }

  function renderDayList() {
    var list = el('ch-commits');
    var commits = dayCommits(selectedDay).filter(function (c) {
      if (!catFilter) return true;
      return isMerge(c) ? true : c.c === catFilter; // merge показываем всегда
    });
    if (!commits.length) {
      list.innerHTML = '<li class="ch-empty">в этот день по выбранному фильтру коммитов нет</li>';
      return;
    }
    list.innerHTML = commits.map(function (c) {
      var meta = data.cats_meta[c.c] || { icon: '', color: '#888' };
      var name = CAT_NAMES[c.c] || c.c;
      return '<li>'
        + '<time>' + c.t + '</time>'
        + '<span class="commit-chip" style="color:' + meta.color + ';border-color:' + meta.color + '55" title="' + name + '">' + (meta.icon || '') + '</span>'
        + '<span class="commit-subject">' + escapeHtml(c.s) + '</span>'
        + '<span class="commit-stats"><b>+' + c.a + '</b> / <i>−' + c.x + '</i> · ' + c.f + ' ф.</span>'
        + '</li>';
    }).join('');
  }

  /* --- Старт ------------------------------------------------------------------------ */

  if (!data || !data.commits) {
    el('ch-commits').innerHTML = '<li class="ch-empty">снапшот не собран — прогони '
      + 'python tools/barrymore/build-chronicle.py и обнови страницу</li>';
    return;
  }
  renderHeader();
  renderCats();
  renderRail();
  selectDay(data.days[data.days.length - 1].date);
})();
