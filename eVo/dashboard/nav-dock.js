/* ==========================================================================
   nav-dock.js v5 — ЯДРО В ШАПКЕ: лого Эво слева сверху = шлюз дверей.
   (Слово Дмитрия 16.11: «старый логотип бесполезный — туда мою картинку,
   функционал шлюза — в неё; док справа снизу удалить».)
   Заменяет .hud-logo на кроп ядра (assets/logo-core.png, из референса
   Workspace/style-refs/logo-platform-evo_3.png), при наведении/клике —
   стеклянная панель дверей с нитью-рамкой. Нет шапки — нет шлюза.
   Подключение: <script src="nav-dock.js?v=5"></script> перед </body>.
   ========================================================================== */
(function () {
  'use strict';

  var DOORS = [
    ['🏰', 'Estate — карта островов', 'index.html'],
    ['🎛', 'Штаб — Бэрримор', 'command-center.html'],
    ['🏛', 'Правление — совет управляющих', 'council.html'],
    ['🗺', 'Карта денег — путь к аренде', 'money-map.html'],
    ['🌀', 'Обсерватория — канбан приёмки', 'maelstorm-observatory.html'],
    ['🧙', 'Соломон — советник по ценности', 'solomon.html'],
    ['⛵', 'Флот в море', 'agents.html'],
    ['📋', 'Канбан задач', 'kanban.html'],
    ['📜', 'Хроника', 'chronicle.html?v=1'],
    ['🌋', 'Маэльшторм', 'maelstorm.html'],
    ['⚙', 'Engine Core', 'engine-core.html'],
  ];

  var here = location.pathname.split('/').pop().split('?')[0];

  var logo = document.querySelector('.hud-logo');
  if (!logo) return; // нет шапки — нет шлюза

  var style = document.createElement('style');
  style.textContent =
    /* обёртка лого-ядра */
    '.nav-core{position:relative;display:flex;align-items:center}' +
    '.nav-core .hud-logo{cursor:pointer;transition:transform .2s ease,filter .2s ease;' +
    'filter:drop-shadow(0 4px 14px rgba(63,224,255,.35))}' +
    '.nav-core .hud-logo:hover{transform:scale(1.07);filter:drop-shadow(0 4px 20px rgba(63,224,255,.6))}' +
    /* стеклянная панель дверей — по диагонали вправо-вниз, чтобы не накрывать
       плашку Бэрримора (top:12%, left:2% — слово Дмитрия 16.11: «он важный персонаж») */
    '.nav-dock{position:absolute;left:calc(100% + 16px);top:calc(100% - 4px);width:300px;opacity:0;visibility:hidden;pointer-events:none;' +
    'transition:opacity .22s ease,transform .22s ease,visibility .22s;transform:translateY(10px);z-index:110}' +
    '.nav-core.open .nav-dock,.nav-core:hover .nav-dock{opacity:1;visibility:visible;pointer-events:auto;transform:translateY(0)}' +
    '.nav-stem{width:2px;height:20px;margin-left:44px;margin-top:-2px;' +
    'transform:rotate(45deg);transform-origin:top center;' +
    'background:linear-gradient(180deg,rgba(63,224,255,.7),rgba(160,107,255,.35))}' +
    '.nav-list{background:rgba(6,14,22,.76);backdrop-filter:blur(12px);' +
    'border:1px solid transparent;border-image:linear-gradient(180deg,rgba(63,224,255,.55),rgba(160,107,255,.45),rgba(86,217,201,.45)) 1;' +
    'border-radius:16px;padding:8px 6px;box-shadow:0 24px 54px rgba(0,6,14,.6),inset 0 0 24px rgba(63,224,255,.06);' +
    'overflow-y:auto;max-height:62vh}' +
    '.nav-head{display:flex;align-items:center;gap:8px;padding:4px 12px 8px;font:600 10px "JetBrains Mono",Consolas,monospace;' +
    'letter-spacing:2.5px;color:#5f7a8c;text-transform:uppercase}' +
    '.nav-head::before{content:"";width:7px;height:7px;border-radius:50%;background:#3fe0ff;' +
    'box-shadow:0 0 8px rgba(63,224,255,.8)}' +
    '.nav-list a{display:flex;align-items:center;gap:10px;padding:7px 10px;border-radius:10px;text-decoration:none;' +
    'color:#8fa2b0;font:500 12.5px "JetBrains Mono",Consolas,monospace;letter-spacing:.4px;' +
    'transition:background .13s ease,color .13s ease,transform .13s ease}' +
    '.nav-list a:hover{background:rgba(63,224,255,.08);color:#eaf6ff;transform:translateX(3px)}' +
    '.nav-list a.here{color:#eaf6ff;background:rgba(160,107,255,.1);box-shadow:inset 2px 0 0 rgba(196,76,255,.7)}' +
    '.nav-list .dnum{font-size:10px;color:rgba(127,150,170,.65);width:18px;flex:none;text-align:right}' +
    '.nav-list .dico{font-size:16px;flex:none;width:22px;text-align:center;filter:saturate(.9)}' +
    '.nav-list a.here .dnum{color:rgba(196,76,255,.95)}' +
    '@media(max-width:700px){.nav-dock{width:min(86vw,300px)}}';
  document.head.appendChild(style);

  /* обёртка вокруг лого */
  var wrap = document.createElement('div');
  wrap.className = 'nav-core';
  logo.parentNode.insertBefore(wrap, logo);
  wrap.appendChild(logo);

  /* картинка Дмитрия вместо старого логотипа */
  logo.src = 'assets/logo-core.png';
  logo.title = 'Ядро Estate — все приборы';

  /* стеклянная панель дверей */
  var dock = document.createElement('div');
  dock.className = 'nav-dock';
  var stem = document.createElement('div');
  stem.className = 'nav-stem';
  dock.appendChild(stem);
  var list = document.createElement('div');
  list.className = 'nav-list';
  var head = document.createElement('div');
  head.className = 'nav-head';
  head.textContent = 'Estate Core · шлюз';
  list.appendChild(head);
  DOORS.forEach(function (d, i) {
    var a = document.createElement('a');
    a.href = d[2];
    a.title = d[1];
    var num = document.createElement('span');
    num.className = 'dnum';
    num.textContent = '0' + (i + 1);
    var ico = document.createElement('span');
    ico.className = 'dico';
    ico.textContent = d[0];
    var name = document.createElement('span');
    name.textContent = d[1];
    a.appendChild(num);
    a.appendChild(ico);
    a.appendChild(name);
    if (d[2].split('?')[0] === here) a.className = 'here';
    list.appendChild(a);
  });
  dock.appendChild(list);
  wrap.appendChild(dock);

  logo.addEventListener('click', function (e) {
    e.stopPropagation();
    wrap.classList.toggle('open');
  });
  document.addEventListener('click', function (e) {
    if (!wrap.contains(e.target)) wrap.classList.remove('open');
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') wrap.classList.remove('open');
  });
})();
