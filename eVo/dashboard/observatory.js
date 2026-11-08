/* ==========================================================================
   MAELSTORM OBSERVATORY — живая картина работы агентов.
   Слой данных: GET /api/agents/live + GET /api/agents/history
   (dashboard-server.py; единственный источник — Workspace/logs/events.jsonl,
   панель только читает — так же, как agents.html «Флот в море»).
   Слой картины: canvas (океан, воронка, корабли, сигналы) + HTML-подписи
   поверх (текст выделяется — правило поместья). Служебных легенд нет:
   только живые цифры и события журнала.
   ?static=1 — один кадр без анимации (для скриншотов и проверок).
   ========================================================================== */
(function () {
  'use strict';

  var REFRESH_MS = 15000;
  var TRAIL_MAX = 46;
  var RIPPLE_TTL = 2.4; // сек

  /* --- ПРОБА ПЕРА 08.11 (слово Дмитрия: «парочку задач, маленьких совсем») ---
     Шлюпки в бухте: мини-задачи, ждущие корабля. Не из канбана — заготовленные
     мини-хвосты поместья. Понравится — подключим /api/tasks по-настоящему;
     не понравится — OBS_DEMO_TASKS=false, и бухта пустеет. */
  var OBS_DEMO_TASKS = true;
  // углы закреплены за сторонами (Дмитрий 09.11: «сверху, слева, справа»);
  // экранные углы: ось Y вниз → 90°=низ, 270°=верх; 188°/352° = бока чуть выше центра
  var DEMO_TASKS = [
    {
      name: 'Снести assets/review по списку',
      note: 'старые референсы карты мира лежат с 04.11 — нужен явный список от Sovereign',
      angle: 188,
    },
    {
      name: 'Русифицировать промпт Risk scan',
      note: 'автоматизация 17:30 отвечает английским — артефакт настройки',
      angle: 270,
    },
    {
      name: 'Бейдж Staff со слэшем',
      note: 'хвост правки бейджей канбана: старые source со слэшем не тронуты',
      angle: 352,
    },
  ];

  var isStatic = /[?&]static=1/.test(location.search)
    || (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

  var canvas = document.getElementById('obs-canvas');
  var ctx = canvas.getContext('2d');
  var labelsEl = document.getElementById('obs-ship-labels');
  var taskEl = document.getElementById('obs-task-labels');
  var dockEl = document.getElementById('obs-dock-labels');
  var cardEl = document.getElementById('obs-card');
  var tapeEl = document.getElementById('obs-tape');
  var tapeListEl = document.getElementById('obs-tape-list');
  var statusEl = document.getElementById('obs-status');
  var updatedEl = document.getElementById('obs-updated');

  /* --- Состояние ----------------------------------------------------------- */

  var state = {
    ships: [],
    voyages: [],
    tasks: [],
    w: 0,
    h: 0,
    cx: 0,
    cy: 0,
    rMax: 0,
    lastFetch: null,
    lastEventTs: {},      // корабль -> ts последнего известного события (для сигналов)
    lastFinishedTs: null, // для сигналов «корабль причалил»
  };

  var particles = [];   // спиральные частицы водоворота
  var trails = {};      // корабль -> [{x, y}]
  var ripples = [];     // сигналы: {x, y, t0, color}
  var foam = [];        // пена за кормой: {x, y, t0}

  /* --- Утилиты -------------------------------------------------------------- */

  function fmtMinutes(min) {
    if (min === null || min === undefined || Number.isNaN(Number(min))) return '—';
    var value = Math.max(0, Math.round(Number(min)));
    if (value < 60) return value + ' мин';
    return Math.floor(value / 60) + ' ч ' + (value % 60) + ' мин';
  }

  function fmtClock(ts) {
    if (!ts) return '—';
    var date = new Date(ts);
    if (Number.isNaN(date.getTime())) return String(ts);
    return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  function fmtDayClock(ts) {
    if (!ts) return '—';
    var date = new Date(ts);
    if (Number.isNaN(date.getTime())) return String(ts);
    return date.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
  }

  function escapeHtml(value) {
    return String(value === null || value === undefined ? '' : value)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function agoMinutes(ts) {
    if (!ts) return null;
    var date = new Date(ts);
    if (Number.isNaN(date.getTime())) return null;
    return Math.max(0, (Date.now() - date.getTime()) / 60000);
  }

  function shipKey(ship, index) {
    return (ship.by || 'корабль') + '#' + index;
  }

  /* --- Геометрия сцены ------------------------------------------------------ */

  function resize() {
    var dpr = window.devicePixelRatio || 1;
    state.w = canvas.clientWidth || window.innerWidth;
    state.h = canvas.clientHeight || window.innerHeight;
    canvas.width = Math.round(state.w * dpr);
    canvas.height = Math.round(state.h * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    state.cx = state.w / 2;
    state.cy = state.h * 0.44;
    state.rMax = Math.max(150, Math.min(state.w * 0.36, state.h * 0.34));
  }

  function seedParticles() {
    particles = [];
    var count = 300;
    for (var i = 0; i < count; i++) {
      var r = 26 + Math.pow(Math.random(), 0.8) * (state.rMax * 1.25 - 26);
      particles.push({
        r: r,
        angle: Math.random() * Math.PI * 2,
        size: 0.6 + Math.random() * 1.6,
        speed: (28 + Math.random() * 26) / Math.max(0.25, r / state.rMax),
        flicker: Math.random() * Math.PI * 2,
      });
    }
  }

  /* Корабли: слоты радиусов + золотой угол между соседями */
  var SLOT_R = [0.88, 0.66, 0.77];
  var GOLDEN_ANGLE = 2.39996;

  function shipBasePose(index) {
    return {
      r: state.rMax * SLOT_R[index % SLOT_R.length],
      angle: index * GOLDEN_ANGLE,
      speed: (0.055 + 0.011 * (index % 3)) * (index % 2 === 0 ? 1 : -1),
    };
  }

  function shipPose(ship, index, tSeconds) {
    var base = shipBasePose(index);
    var calm = ship.pulse_status === 'тихо';
    var storm = ship.pulse_status === 'шторм' || ship.status === 'шторм';
    var omega = base.speed * (storm ? 2.4 : calm ? 0.35 : 1);
    var angle = base.angle + omega * tSeconds;
    var r = base.r;
    if (storm) {
      // штормящий затягивается к воронке и кренится
      r = base.r * (0.58 + 0.09 * Math.sin(tSeconds * 2.2 + index));
    }
    var x = state.cx + Math.cos(angle) * r;
    var y = state.cy + Math.sin(angle) * r * 0.62; // эллипс — перспектива «вид сверху»
    return { x: x, y: y, angle: angle, r: r, storm: storm, calm: calm };
  }

  function dockPose(index, total) {
    // гавань: два ряда под воронкой, равномерный шаг — подписи не слипаются
    var row = index % 2;
    var perRow = Math.ceil(total / 2);
    var posInRow = Math.floor(index / 2);
    var stepX = Math.min(300, (state.w * 0.52) / Math.max(1, perRow));
    var x = state.cx + (posInRow - (perRow - 1) / 2) * stepX;
    var y = state.cy + state.rMax * 0.74 + row * 34;
    return { x: x, y: y };
  }

  function taskPose(task, index, tSeconds) {
    // шлюпка стоит на своей стороне света и качается на волне;
    // дрейф по кругу убран (09.11: шлюпки съезжались вниз к гавани) —
    // вместо него лёгкое «якорное» покачивание угла ±3°
    var base = (task.angle * Math.PI) / 180;
    var angle = base + Math.sin(tSeconds * 0.1 + index * 1.9) * 0.05;
    var r = state.rMax * 1.04;
    var bob = Math.sin(tSeconds * 1.3 + index * 1.9) * 3;
    return {
      x: state.cx + Math.cos(angle) * r,
      y: state.cy + Math.sin(angle) * r * 0.62 + bob,
      angle: angle,
    };
  }

  /* --- Canvas: отрисовка ---------------------------------------------------- */

  function drawBackdrop() {
    ctx.clearRect(0, 0, state.w, state.h);
    var vignette = ctx.createRadialGradient(state.cx, state.cy, state.rMax * 0.05, state.cx, state.cy, state.rMax * 1.6);
    vignette.addColorStop(0, 'rgba(9, 44, 68, 0.55)');
    vignette.addColorStop(0.55, 'rgba(6, 21, 37, 0.12)');
    vignette.addColorStop(1, 'rgba(2, 9, 15, 0)');
    ctx.fillStyle = vignette;
    ctx.fillRect(0, 0, state.w, state.h);
  }

  function drawParticles(t) {
    for (var i = 0; i < particles.length; i++) {
      var p = particles[i];
      var omega = p.speed / state.rMax;
      p.angle += omega * 0.016; // шаг интегрирования кадра
      var x = state.cx + Math.cos(p.angle) * p.r;
      var y = state.cy + Math.sin(p.angle) * p.r * 0.62;
      var depth = 1 - p.r / (state.rMax * 1.3);
      var alpha = (0.16 + 0.5 * depth) * (0.75 + 0.25 * Math.sin(t * 1.7 + p.flicker));
      ctx.beginPath();
      ctx.fillStyle = 'rgba(126, 200, 230, ' + alpha.toFixed(3) + ')';
      ctx.arc(x, y, p.size, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  function drawWhirl(t) {
    // спиральные дуги воронки: 3.5 витка от глаза к кромке
    var arms = 5;
    for (var k = 0; k < arms; k++) {
      ctx.beginPath();
      var offset = t * 0.5 + (k * Math.PI * 2) / arms;
      for (var s = 0; s <= 70; s++) {
        var theta = s / 70 * Math.PI * 3.5;
        var r = 12 + theta * (state.rMax * 0.072);
        var angle = theta + offset;
        var x = state.cx + Math.cos(angle) * r;
        var y = state.cy + Math.sin(angle) * r * 0.62;
        if (s === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      ctx.strokeStyle = 'rgba(56, 189, 248, ' + (0.12 + 0.06 * (k % 2)) + ')';
      ctx.lineWidth = 1.1;
      ctx.stroke();
    }
    // глаз воронки
    var eye = ctx.createRadialGradient(state.cx, state.cy, 2, state.cx, state.cy, 34);
    eye.addColorStop(0, 'rgba(1, 6, 10, 0.95)');
    eye.addColorStop(0.7, 'rgba(3, 12, 20, 0.8)');
    eye.addColorStop(1, 'rgba(56, 189, 248, 0)');
    ctx.beginPath();
    ctx.fillStyle = eye;
    ctx.arc(state.cx, state.cy, 34, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.strokeStyle = 'rgba(125, 211, 252, 0.5)';
    ctx.lineWidth = 1.4;
    ctx.arc(state.cx, state.cy, 12 + Math.sin(t * 1.4) * 2.5, 0, Math.PI * 2);
    ctx.stroke();
  }

  function drawShipGlyph(x, y, angle, storm, calm, alpha) {
    var color = storm ? '248, 113, 113' : calm ? '148, 163, 184' : '56, 189, 248';
    var tilt = storm ? Math.sin(Date.now() / 180) * 0.16 : 0;
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(angle + Math.PI / 2 + tilt);

    // свечение под кораблём
    var glow = ctx.createRadialGradient(0, 0, 2, 0, 0, 26);
    glow.addColorStop(0, 'rgba(' + color + ', ' + (0.34 * alpha).toFixed(3) + ')');
    glow.addColorStop(1, 'rgba(' + color + ', 0)');
    ctx.fillStyle = glow;
    ctx.fillRect(-26, -26, 52, 52);

    // корпус
    ctx.beginPath();
    ctx.moveTo(13, 0);
    ctx.quadraticCurveTo(3, 7, -11, 4.5);
    ctx.quadraticCurveTo(-15, 0, -11, -4.5);
    ctx.quadraticCurveTo(3, -7, 13, 0);
    ctx.closePath();
    ctx.fillStyle = 'rgba(' + color + ', ' + (0.92 * alpha).toFixed(3) + ')';
    ctx.fill();

    // парус
    ctx.beginPath();
    ctx.moveTo(0, -1);
    ctx.lineTo(0, -14);
    ctx.lineTo(8, -2);
    ctx.closePath();
    ctx.fillStyle = 'rgba(226, 232, 240, ' + (0.85 * alpha).toFixed(3) + ')';
    ctx.fill();

    // мачта
    ctx.strokeStyle = 'rgba(' + color + ', ' + (0.8 * alpha).toFixed(3) + ')';
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.moveTo(0, 1);
    ctx.lineTo(0, -14);
    ctx.stroke();
    ctx.restore();
  }

  function pushTrail(key, x, y) {
    var list = trails[key] || (trails[key] = []);
    list.push({ x: x, y: y });
    if (list.length > TRAIL_MAX) list.shift();
  }

  function drawTrail(key, storm, calm, alpha) {
    var list = trails[key];
    if (!list || list.length < 2) return;
    var color = storm ? '248, 113, 113' : calm ? '148, 163, 184' : '56, 189, 248';
    for (var i = 1; i < list.length; i++) {
      var a = (i / list.length) * 0.34 * alpha;
      ctx.beginPath();
      ctx.strokeStyle = 'rgba(' + color + ', ' + a.toFixed(3) + ')';
      ctx.lineWidth = 1 + (i / list.length) * 1.6;
      ctx.moveTo(list[i - 1].x, list[i - 1].y);
      ctx.lineTo(list[i].x, list[i].y);
      ctx.stroke();
    }
  }

  function spawnFoam(x, y) {
    foam.push({ x: x + (Math.random() - 0.5) * 8, y: y + (Math.random() - 0.5) * 8, t0: performance.now() / 1000 });
    if (foam.length > 120) foam.shift();
  }

  function drawFoam(nowSec) {
    for (var i = foam.length - 1; i >= 0; i--) {
      var f = foam[i];
      var age = nowSec - f.t0;
      if (age > 1.6) { foam.splice(i, 1); continue; }
      var alpha = 0.4 * (1 - age / 1.6);
      ctx.beginPath();
      ctx.fillStyle = 'rgba(186, 230, 253, ' + alpha.toFixed(3) + ')';
      ctx.arc(f.x, f.y + age * 2.4, 1.3 + age * 1.6, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  function drawRipples(nowSec) {
    for (var i = ripples.length - 1; i >= 0; i--) {
      var r = ripples[i];
      var age = nowSec - r.t0;
      if (age > RIPPLE_TTL) { ripples.splice(i, 1); continue; }
      var progress = age / RIPPLE_TTL;
      ctx.beginPath();
      ctx.strokeStyle = 'rgba(' + (r.color || '125, 211, 252') + ', ' + (0.6 * (1 - progress)).toFixed(3) + ')';
      ctx.lineWidth = 1.6;
      ctx.arc(r.x, r.y, 6 + progress * 44, 0, Math.PI * 2);
      ctx.stroke();
    }
  }

  function drawDocks() {
    var voyages = state.voyages;
    for (var i = 0; i < voyages.length; i++) {
      var pose = dockPose(i, voyages.length);
      var verdict = String(voyages[i].verdict || '');
      var accepted = verdict.toLowerCase().indexOf('принято') >= 0;
      var rework = verdict.toLowerCase().indexOf('доработ') >= 0;
      var color = accepted ? '52, 211, 153' : rework ? '251, 191, 36' : '148, 163, 184';
      // огонёк причала
      var glow = ctx.createRadialGradient(pose.x, pose.y, 1, pose.x, pose.y, 16);
      glow.addColorStop(0, 'rgba(' + color + ', 0.4)');
      glow.addColorStop(1, 'rgba(' + color + ', 0)');
      ctx.fillStyle = glow;
      ctx.fillRect(pose.x - 16, pose.y - 16, 32, 32);
      ctx.beginPath();
      ctx.fillStyle = 'rgba(' + color + ', 0.9)';
      ctx.arc(pose.x, pose.y, 3.2, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  function drawTaskGlyph(x, y, alpha) {
    // шлюпка: маленький корпус с бортиком, без паруса — ждёт корабля
    var color = '251, 191, 36';
    var glow = ctx.createRadialGradient(x, y, 1, x, y, 18);
    glow.addColorStop(0, 'rgba(' + color + ', ' + (0.28 * alpha).toFixed(3) + ')');
    glow.addColorStop(1, 'rgba(' + color + ', 0)');
    ctx.fillStyle = glow;
    ctx.fillRect(x - 18, y - 18, 36, 36);
    ctx.beginPath();
    ctx.moveTo(9, -1);
    ctx.quadraticCurveTo(4, 5.5, -8, 4);
    ctx.quadraticCurveTo(-11, 0, -8, -3.5);
    ctx.quadraticCurveTo(4, -5.5, 9, -1);
    ctx.closePath();
    ctx.fillStyle = 'rgba(' + color + ', ' + (0.9 * alpha).toFixed(3) + ')';
    ctx.fill();
    // борт
    ctx.beginPath();
    ctx.moveTo(9, -1);
    ctx.quadraticCurveTo(4, -5.5, -8, -3.5);
    ctx.strokeStyle = 'rgba(253, 230, 138, ' + (0.9 * alpha).toFixed(3) + ')';
    ctx.lineWidth = 1.4;
    ctx.stroke();
  }

  /* --- HTML-слои: подписи ---------------------------------------------------- */

  function syncShipLabels() {
    var ships = state.ships;
    var existing = {};
    var wanted = [];
    for (var i = 0; i < ships.length; i++) {
      var key = shipKey(ships[i], i);
      existing[key] = true;
      wanted.push({ key: key, ship: ships[i], index: i });
    }
    // убрать подписи исчезнувших кораблей
    Array.prototype.forEach.call(labelsEl.children, function (node) {
      if (!existing[node.dataset.key]) node.remove();
    });
    for (var j = 0; j < wanted.length; j++) {
      var item = wanted[j];
      var node = labelsEl.querySelector('[data-key="' + CSS.escape(item.key) + '"]');
      if (!node) {
        node = document.createElement('div');
        node.dataset.key = item.key;
        node.className = 'obs-ship-label';
        node.innerHTML =
          '<span class="obs-ship-name"></span>'
          + '<span class="obs-ship-task"></span>'
          + '<span class="obs-ship-lanes"><span class="obs-lanes-scale"><span class="obs-lanes-fill"></span></span>'
          + '<span class="obs-lanes-text"></span></span>';
        node.addEventListener('click', function (event) {
          event.stopPropagation();
          openShipCard(this.dataset.key);
        });
        labelsEl.appendChild(node);
      }
      var ship = item.ship;
      var pulseClass = ship.pulse_status === 'шторм' || ship.status === 'шторм' ? 'pulse-storm'
        : ship.pulse_status === 'тихо' ? 'pulse-calm' : '';
      node.classList.remove('pulse-calm', 'pulse-storm');
      if (pulseClass) node.classList.add(pulseClass);
      node.querySelector('.obs-ship-name').textContent = ship.by || 'корабль';
      node.querySelector('.obs-ship-task').textContent = ship.task || '';
      node.querySelector('.obs-ship-task').hidden = !(ship.task && ship.task !== 'задача не объявлена');
      var lanes = ship.lanes || {};
      var done = Number(lanes.done) || 0;
      var total = lanes.total === null || lanes.total === undefined ? null : Number(lanes.total);
      var width = total ? Math.max(0, Math.min(100, Math.round((done / total) * 100))) : (done > 0 ? 100 : 0);
      node.querySelector('.obs-lanes-fill').style.width = width + '%';
      node.querySelector('.obs-lanes-text').textContent = total !== null ? done + '/' + total : String(done);
      node._index = item.index;
    }
    positionShipLabels();
  }

  function positionShipLabels() {
    var t = staticClock;
    Array.prototype.forEach.call(labelsEl.children, function (node) {
      var index = node._index;
      var ship = state.ships[index];
      if (!ship) return;
      var pose = shipPose(ship, index, t);
      node.style.left = pose.x + 'px';
      node.style.top = (pose.y + 30) + 'px';
    });
  }

  function dockKey(voyage) {
    return (voyage.by || 'корабль') + '|' + (voyage.finished_at || '');
  }

  function syncDockLabels() {
    // переиспользуем узлы по ключу рейса (имя+финиш): DOM не пересоздаётся под курсором
    var voyages = state.voyages;
    var seen = {};
    for (var i = 0; i < voyages.length; i++) seen[dockKey(voyages[i])] = true;
    Array.prototype.forEach.call(dockEl.children, function (node) {
      if (!seen[node.dataset.key]) node.remove();
    });
    for (var j = 0; j < voyages.length; j++) {
      var voyage = voyages[j];
      var key = dockKey(voyage);
      var pose = dockPose(j, voyages.length);
      var node = dockEl.querySelector('[data-key="' + CSS.escape(key) + '"]');
      if (!node) {
        node = document.createElement('div');
        node.className = 'obs-dock-label';
        node.innerHTML =
          '<span class="obs-dock-name"></span>'
          + '<span class="obs-dock-verdict"></span>';
        node.addEventListener('click', function (event) {
          event.stopPropagation();
          openVoyageCard(this._voyageIndex);
        });
        dockEl.appendChild(node);
      }
      node.dataset.key = key;
      node._voyageIndex = j;
      var verdict = String(voyage.verdict || '');
      node.classList.remove('verdict-accepted', 'verdict-rework');
      if (verdict.toLowerCase().indexOf('принято') >= 0) node.classList.add('verdict-accepted');
      else if (verdict.toLowerCase().indexOf('доработ') >= 0) node.classList.add('verdict-rework');
      node.querySelector('.obs-dock-name').textContent = '⚓ ' + (voyage.by || '');
      node.querySelector('.obs-dock-verdict').textContent = verdict || fmtDayClock(voyage.finished_at);
      node.style.left = pose.x + 'px';
      node.style.top = (pose.y + 14) + 'px';
    }
  }

  /* --- Шлюпки: подписи мини-задач -------------------------------------------- */

  function syncTaskLabels() {
    if (!OBS_DEMO_TASKS) {
      taskEl.innerHTML = '';
      state.tasks = [];
      return;
    }
    state.tasks = DEMO_TASKS;
    taskEl.innerHTML = '';
    for (var i = 0; i < state.tasks.length; i++) {
      var task = state.tasks[i];
      var node = document.createElement('div');
      node.className = 'obs-task-label';
      node.textContent = task.name;
      node._taskIndex = i;
      node.addEventListener('click', function (event) {
        event.stopPropagation();
        openTaskCard(this._taskIndex);
      });
      taskEl.appendChild(node);
    }
    positionTaskLabels();
  }

  function positionTaskLabels() {
    var nodes = document.querySelectorAll('.obs-task-label');
    for (var i = 0; i < nodes.length; i++) {
      var task = state.tasks[i];
      if (!task) continue;
      var pose = taskPose(task, i, staticClock);
      nodes[i].style.left = pose.x + 'px';
      nodes[i].style.top = (pose.y + 20) + 'px';
    }
  }

  /* --- Карточка корабля / рейса ---------------------------------------------- */

  function cardTapeRow(kind, ts, text, storm) {
    var li = document.createElement('li');
    if (storm) li.className = 'storm-row';
    var time = document.createElement('time');
    time.textContent = fmtClock(ts);
    var spanKind = document.createElement('span');
    spanKind.className = 'tape-kind';
    var kindStr = String(kind || '');
    var kindShort = kindStr.replace('agent.', '') || '?';
    spanKind.textContent = kindShort;
    li.appendChild(time); li.appendChild(spanKind);
    var textStr = String(text || '');
    // «pulse · agent.pulse» не читаем: текст, совпадающий с типом, не показываем
    if (textStr && textStr !== kindStr && textStr !== kindShort) {
      var spanText = document.createElement('span');
      spanText.textContent = textStr;
      li.appendChild(spanText);
    }
    return li;
  }

  function openShipCard(key) {
    var index = null;
    Array.prototype.forEach.call(labelsEl.children, function (node) {
      if (node.dataset.key === key) index = node._index;
    });
    if (index === null) return;
    var ship = state.ships[index];
    if (!ship) return;
    var storms = Number(ship.storms) || 0;
    document.getElementById('obs-card-badge').textContent =
      (ship.pulse_status === 'шторм' || ship.status === 'шторм') ? 'КОРАБЛЬ В ШТОРМЕ' : 'КОРАБЛЬ В МОРЕ';
    document.getElementById('obs-card-title').textContent = ship.by || 'корабль';
    document.getElementById('obs-card-task').textContent = ship.task || 'задача не объявлена';
    var metrics = document.getElementById('obs-card-metrics');
    metrics.innerHTML = '';
    function metric(text, stormClass) {
      var span = document.createElement('span');
      if (stormClass) span.className = stormClass;
      span.textContent = text;
      metrics.appendChild(span);
    }
    metric('в море: ' + fmtMinutes(ship.elapsed_min));
    metric('посл. событие: ' + (ship.pulse_min === null || ship.pulse_min === undefined
      ? '—' : fmtMinutes(ship.pulse_min) + ' назад'));
    metric('ETA: ' + (ship.eta_min === null || ship.eta_min === undefined ? '—' : '~' + fmtMinutes(ship.eta_min)));
    if (storms > 0) metric('штормы: ⛈ ' + storms, 'storm');
    metric('старт: ' + fmtDayClock(ship.started_at));

    var lanes = ship.lanes || {};
    var done = Number(lanes.done) || 0;
    var total = lanes.total === null || lanes.total === undefined ? null : Number(lanes.total);
    var width = total ? Math.max(0, Math.min(100, Math.round((done / total) * 100))) : (done > 0 ? 100 : 0);
    var lanesEl = document.getElementById('obs-card-lanes');
    lanesEl.innerHTML =
      '<div class="obs-lanes-scale"><div class="obs-lanes-fill" style="width:' + width + '%"></div></div>'
      + '<span class="obs-lanes-text"></span>';
    lanesEl.querySelector('.obs-lanes-text').textContent = total !== null
      ? 'лейны: ' + done + '/' + total
      : 'лейны закрыты: ' + done;

    var tape = document.getElementById('obs-card-tape');
    tape.innerHTML = '';
    var list = document.createElement('ul');
    var recent = Array.isArray(ship.events_recent) ? ship.events_recent : [];
    if (recent.length) {
      for (var i = recent.length - 1; i >= 0 && i >= recent.length - 8; i--) {
        list.appendChild(cardTapeRow(recent[i].kind, recent[i].ts, recent[i].text, recent[i].kind === 'agent.storm'));
      }
    } else {
      var empty = document.createElement('li');
      empty.textContent = 'событий пока нет';
      list.appendChild(empty);
    }
    tape.appendChild(list);
    cardEl.hidden = false;
  }

  function openVoyageCard(index) {
    var voyage = state.voyages[index];
    if (!voyage) return;
    var storms = Number(voyage.storms) || 0;
    document.getElementById('obs-card-badge').textContent = 'ПРИЧАЛ · РЕЙС ЗАВЕРШЁН';
    document.getElementById('obs-card-title').textContent = voyage.by || 'корабль';
    document.getElementById('obs-card-task').textContent = voyage.task || 'задача не объявлена';
    var metrics = document.getElementById('obs-card-metrics');
    metrics.innerHTML = '';
    function metric(text, stormClass) {
      var span = document.createElement('span');
      if (stormClass) span.className = stormClass;
      span.textContent = text;
      metrics.appendChild(span);
    }
    metric('старт: ' + fmtDayClock(voyage.started_at));
    metric('финиш: ' + fmtDayClock(voyage.finished_at));
    if (voyage.minutes !== null && voyage.minutes !== undefined) metric('в море: ' + fmtMinutes(voyage.minutes));
    if (voyage.tokens !== null && voyage.tokens !== undefined) metric('токены: ' + voyage.tokens);
    if (Array.isArray(voyage.files) && voyage.files.length) metric('файлы: ' + voyage.files.length);
    if (voyage.tests !== null && voyage.tests !== undefined) metric('тесты: ' + String(voyage.tests).slice(0, 40));
    if (storms > 0) metric('штормы: ⛈ ' + storms, 'storm');
    if (voyage.verdict) metric('вердикт: ' + voyage.verdict);

    var lanes = voyage.lanes || {};
    var done = Number(lanes.done) || 0;
    var total = lanes.total === null || lanes.total === undefined ? null : Number(lanes.total);
    var width = total ? Math.max(0, Math.min(100, Math.round((done / total) * 100))) : (done > 0 ? 100 : 0);
    var lanesEl = document.getElementById('obs-card-lanes');
    lanesEl.innerHTML =
      '<div class="obs-lanes-scale"><div class="obs-lanes-fill" style="width:' + width + '%"></div></div>'
      + '<span class="obs-lanes-text"></span>';
    lanesEl.querySelector('.obs-lanes-text').textContent = total !== null
      ? 'лейны: ' + done + '/' + total
      : 'лейны закрыты: ' + done;

    var tape = document.getElementById('obs-card-tape');
    tape.innerHTML = '';
    var list = document.createElement('ul');
    var chain = Array.isArray(voyage.chain) ? voyage.chain : [];
    if (chain.length) {
      for (var i = chain.length - 1; i >= 0 && i >= chain.length - 10; i--) {
        list.appendChild(cardTapeRow(chain[i].kind, chain[i].ts, chain[i].text, chain[i].kind === 'agent.storm'));
      }
    } else {
      var empty = document.createElement('li');
      empty.textContent = 'цепочка пуста';
      list.appendChild(empty);
    }
    tape.appendChild(list);
    cardEl.hidden = false;
  }

  document.getElementById('obs-card-close').addEventListener('click', function () {
    cardEl.hidden = true;
  });
  canvas.addEventListener('click', function () {
    cardEl.hidden = true;
  });
  document.addEventListener('click', function (event) {
    // клик мимо карточки и мимо подписей (те останавливают событие) закрывает карточку
    if (!cardEl.hidden && !cardEl.contains(event.target)) cardEl.hidden = true;
  });
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') cardEl.hidden = true;
  });

  function openTaskCard(index) {
    var task = state.tasks[index];
    if (!task) return;
    document.getElementById('obs-card-badge').textContent = 'ШАЛУПА · ЗАДАЧА ЖДЁТ КОРАБЛЯ';
    document.getElementById('obs-card-title').textContent = task.name;
    document.getElementById('obs-card-task').textContent = task.note;
    var metrics = document.getElementById('obs-card-metrics');
    metrics.innerHTML = '';
    function metric(text, stormClass) {
      var span = document.createElement('span');
      if (stormClass) span.className = stormClass;
      span.textContent = text;
      metrics.appendChild(span);
    }
    metric('размер: маленькая');
    metric('статус: в бухте, ждёт корабля');
    metric('источник: проба пера (не из канбана)');
    document.getElementById('obs-card-lanes').innerHTML = '';
    document.getElementById('obs-card-tape').innerHTML = '';
    cardEl.hidden = false;
  }

  /* --- Лента сигналов ---------------------------------------------------------- */

  function syncTape() {
    var rows = [];
    for (var i = 0; i < state.ships.length; i++) {
      var ship = state.ships[i];
      var recent = Array.isArray(ship.events_recent) ? ship.events_recent : [];
      for (var j = 0; j < recent.length; j++) {
        rows.push({ ts: recent[j].ts, ship: ship.by, kind: recent[j].kind, text: recent[j].text });
      }
    }
    rows.sort(function (a, b) { return String(b.ts || '').localeCompare(String(a.ts || '')); });
    if (!rows.length) {
      for (var v = 0; v < state.voyages.length && rows.length < 8; v++) {
        var chain = state.voyages[v].chain || [];
        for (var c = chain.length - 1; c >= 0 && rows.length < 8; c--) {
          rows.push({ ts: chain[c].ts, ship: state.voyages[v].by, kind: chain[c].kind, text: chain[c].text });
        }
      }
    }
    if (!rows.length) { tapeEl.hidden = true; return; }
    tapeEl.hidden = false;
    tapeListEl.innerHTML = '';
    for (var r = 0; r < Math.min(rows.length, 8); r++) {
      var row = rows[r];
      var li = document.createElement('li');
      if (row.kind === 'agent.storm') li.className = 'storm-row';
      var time = document.createElement('time');
      time.textContent = fmtClock(row.ts);
      var shipSpan = document.createElement('span');
      shipSpan.className = 'tape-ship';
      shipSpan.textContent = row.ship || '';
      var kindStr = String(row.kind || '');
      var kindShort = kindStr.replace('agent.', '') || '?';
      var textStr = String(row.text || '');
      var textSpan = document.createElement('span');
      textSpan.textContent = textStr && textStr !== kindStr && textStr !== kindShort
        ? kindShort + ' · ' + textStr
        : kindShort;
      li.appendChild(time); li.appendChild(shipSpan); li.appendChild(textSpan);
      tapeListEl.appendChild(li);
    }
  }

  /* --- Сигналы (ripple) при новых событиях -------------------------------------- */

  function detectSignals() {
    var now = new Date().toISOString();
    for (var i = 0; i < state.ships.length; i++) {
      var ship = state.ships[i];
      var key = shipKey(ship, i);
      var recent = Array.isArray(ship.events_recent) ? ship.events_recent : [];
      var lastTs = state.lastEventTs[key];
      for (var j = 0; j < recent.length; j++) {
        var ts = recent[j].ts;
        if (!ts) continue;
        if (lastTs && String(ts) <= String(lastTs)) continue;
        var pose = shipPose(ship, i, staticClock);
        var color = recent[j].kind === 'agent.storm' ? '248, 113, 113' : '125, 211, 252';
        ripples.push({ x: pose.x, y: pose.y, t0: performance.now() / 1000, color: color });
        if (!isStatic) spawnFoam(pose.x, pose.y);
      }
      if (recent.length) state.lastEventTs[key] = recent[recent.length - 1].ts;
    }
    if (state.lastEventTs.__cleared !== true && !state.ships.length) {
      // море опустело — причаливший корабль даёт сигнал на своём причале
      if (state.lastFinishedTs && state.voyages.length) {
        var pose = dockPose(0, state.voyages.length);
        ripples.push({ x: pose.x, y: pose.y, t0: performance.now() / 1000, color: '52, 211, 153' });
      }
      state.lastEventTs.__cleared = true;
    } else if (state.ships.length) {
      state.lastEventTs.__cleared = false;
      state.lastFinishedTs = new Date();
    }
  }

  /* --- Данные -------------------------------------------------------------------- */

  function fetchJson(url) {
    return fetch(url, { cache: 'no-store' }).then(function (response) {
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return response.json();
    });
  }

  function showError(message) {
    statusEl.hidden = false;
    statusEl.textContent = message;
  }

  function refresh() {
    document.getElementById('obs-refresh').disabled = true;
    return Promise.all([
      fetchJson('/api/agents/live'),
      fetchJson('/api/agents/history?limit=24'),
    ]).then(function (results) {
      state.ships = Array.isArray(results[0].ships) ? results[0].ships : [];
      state.voyages = Array.isArray(results[1].voyages) ? results[1].voyages : [];
      state.lastFetch = new Date();
      statusEl.hidden = true;
      document.getElementById('obs-count-sea').textContent = String(state.ships.length);
      var storming = state.ships.filter(function (ship) {
        return ship.status === 'шторм' || ship.pulse_status === 'шторм';
      }).length;
      document.getElementById('obs-count-storm').textContent = String(storming);
      document.getElementById('obs-count-dock').textContent = String(state.voyages.length);
      updatedEl.textContent = 'обновлено в ' + fmtClock(state.lastFetch.toISOString());
      detectSignals();
      syncShipLabels();
      syncDockLabels();
      syncTaskLabels();
      document.getElementById('obs-count-tasks').textContent = String(state.tasks.length);
      syncTape();
      if (isStatic) renderFrame(performance.now());
    }).catch(function (error) {
      showError('Живой сервер 127.0.0.1:8765 не отвечает (' + error.message + '). Повтор через 15 с.');
    }).finally(function () {
      document.getElementById('obs-refresh').disabled = false;
    });
  }

  document.getElementById('obs-refresh').addEventListener('click', refresh);

  /* --- Кадр ------------------------------------------------------------------------ */

  var staticClock = 2.0; // сек: единое «время сцены» (в static-режиме фиксировано)

  function renderFrame(nowMs) {
    var t = isStatic ? staticClock : nowMs / 1000;
    if (!isStatic) staticClock = t;
    drawBackdrop();
    drawParticles(t);
    drawWhirl(t);
    drawDocks();
    for (var tk = 0; tk < state.tasks.length; tk++) {
      var tpose = taskPose(state.tasks[tk], tk, t);
      drawTaskGlyph(tpose.x, tpose.y, 0.85);
    }
    for (var i = 0; i < state.ships.length; i++) {
      var ship = state.ships[i];
      var key = shipKey(ship, i);
      var storm = ship.pulse_status === 'шторм' || ship.status === 'шторм';
      var calm = ship.pulse_status === 'тихо';
      var alpha = storm ? 1 : calm ? 0.55 : 0.95;
      var pose = shipPose(ship, i, t);
      drawTrail(key, storm, calm, alpha);
      drawShipGlyph(pose.x, pose.y, Math.atan2(Math.cos(pose.angle) * 0.62, -Math.sin(pose.angle)) , storm, calm, alpha);
      if (!isStatic) {
        pushTrail(key, pose.x, pose.y);
        if (!calm && Math.random() < 0.25) spawnFoam(pose.x, pose.y);
      }
    }
    drawFoam(nowMs / 1000);
    drawRipples(nowMs / 1000);
    positionShipLabels();
    positionTaskLabels();
  }

  function loop(nowMs) {
    renderFrame(nowMs);
    requestAnimationFrame(loop);
  }

  /* --- Запуск ------------------------------------------------------------------------ */

  window.addEventListener('resize', function () {
    resize();
    seedParticles();
    if (isStatic) renderFrame(performance.now());
  });

  resize();
  seedParticles();
  refresh();
  setInterval(refresh, REFRESH_MS);
  if (isStatic) {
    renderFrame(performance.now());
  } else {
    requestAnimationFrame(loop);
  }
})();
