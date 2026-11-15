/**
 * Кораблик-вестник Harbor: раз в 5 минут приплывает к причалу по морю,
 * рассказывает свежие вести (данные - из EVO_VACANCIES, которые собирает
 * tools/job_search.py --js), слушает клики и уплывает.
 *
 * Спрайт - вырезанный из игрового референса Дмитрия галеон
 * (Vision/Good_references/R_SS_MultiAge_SummerBonus18f.png), отзеркален вправо.
 * Фарватер проложен A*-роутером по hand-traced контурам островов карты и
 * проверен попиксельно: каждое колено - 100% вода.
 */
(function () {
  "use strict";

  const SPRITE_VER = "v10"; // bumps при каждом обновлении спрайта/маршрута (анти-кэш)
  const SHIP_SPRITE = `<img class="ship-img" src="assets/harbor-ship-sprite.png?${SPRITE_VER}" alt="" draggable="false">`;

  const VISIT_INTERVAL = 5 * 60 * 1000;  // раз в 5 минут
  const DOCK_MS = 5000;                  // стоянка у причала с речами (5 секунд)
  const FIRST_DELAY = 7000;              // первый заход почти сразу после загрузки

  // ===== ФАРВАТЕР — ПРАВЬ ЗДЕСЬ ================================================
  // Точки в ПИКСЕЛЯХ дизайн-кадра 1280x720: [от левого края, от нижнего края].
  // Навигационная карта с сеткой: assets/route-grid.png (масштаб совпадает с картой).
  // Скорость хода постоянная (~55 px/с), тайминги считаются сами.
  const DESIGN_W = 1280, DESIGN_H = 720;
  const SPEED = 55; // px/с

  const ROUTE_PX = {
    enter: [[-77, 23], [470, 30], [560, 70]],                      // лагуна юга -> стоп у пирса
    exit:  [[560, 70], [650, 30], [1150, 15], [1280, 300]],        // отход вниз, вдоль юга, уход за правый край
  };
  // ==============================================================================

  function pxToLeg(p) { return [p[0] / DESIGN_W * 100, 100 - p[1] / DESIGN_H * 100]; }
  function buildLegs(list) {
    const legs = [];
    for (let i = 0; i < list.length; i++) {
      const from = i > 0 ? list[i - 1] : list[0];
      const ms = i === 0 ? 0 : Math.max(800, Math.round(
        Math.hypot(list[i][0] - from[0], list[i][1] - from[1]) / SPEED * 1000));
      legs.push([...pxToLeg(list[i]), ms]);
    }
    return legs;
  }
  const ENTER_LEGS = buildLegs(ROUTE_PX.enter);
  const EXIT_LEGS = buildLegs(ROUTE_PX.exit);

  let ship, turnEl, bankEl, bubble, busy = false, lastMessage = -1, lastAttempt = 0;

  function pluralize(n, one, few, many) {
    const mod10 = n % 10, mod100 = n % 100;
    if (mod10 === 1 && mod100 !== 11) return one;
    if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few;
    return many;
  }

  function buildMessages() {
    const vac = (typeof EVO_VACANCIES !== "undefined") ? EVO_VACANCIES : null;
    const total = (vac && typeof vac.total === "number") ? vac.total : null;
    const flru = (vac && vac.freelance && Array.isArray(vac.freelance.flru)) ? vac.freelance.flru.length : null;
    const updated = (vac && vac.generatedAt) ? vac.generatedAt : null;
    return [
      (total !== null)
        ? `Весточка с внешних архипелагов, капитан! В трюме ${total} ${pluralize(total, "позиция", "позиции", "позиций")} по твоему профилю.`
        : "Весточка с внешних архипелагов, капитан! Море спокойно, течения попутные.",
      (flru !== null && flru > 0)
        ? `На FL.ru поймал сети ${flru} ${pluralize(flru, "заказ", "заказа", "заказов")} — успевай, пока течение не снесло!`
        : "Сети пустые, но я вернусь с уловом, клянусь компасом!",
      (updated)
        ? `Пресная вода в трюме: лента обновлена ${updated}. Загляни в Trading Quarter!`
        : "Загляни в Trading Quarter — рынок вакансий ждать не любит!",
      "Порядок на палубе, капитан. Маяки горят, компас не врёт, очаг не потух.",
      "Слухи по архипелагу: нужны порты, CI/CD и крепкие нервы. Это всё к нам!"
    ];
  }

  function pickMessage() {
    const pool = buildMessages();
    let i;
    do { i = Math.floor(Math.random() * pool.length); } while (pool.length > 1 && i === lastMessage);
    lastMessage = i;
    return pool[i];
  }

  function shipPoint() {
    // Координаты из процентных style.left/top: rect зависит от отрисованных кадров
    // и может быть заморожен, а проценты всегда актуальны. -42px поднимает пузырь над мачтами.
    const parent = ship.parentElement.getBoundingClientRect();
    return {
      x: (parseFloat(ship.style.left) || 0) / 100 * parent.width,
      y: (parseFloat(ship.style.top) || 0) / 100 * parent.height - 42
    };
  }

  function showBubble(text, ms) {
    const p = shipPoint();
    bubble.textContent = text;
    bubble.style.left = p.x + "px";
    bubble.style.top = p.y + "px";
    bubble.classList.add("visible");
    clearTimeout(showBubble._t);
    showBubble._t = setTimeout(() => bubble.classList.remove("visible"), ms);
  }

  function sleep(ms) { return new Promise((res) => setTimeout(res, ms)); }

  // курс в градусах (спрайт смотрит вправо); круче 35° корпус не заваливаем
  function headingDeg(fromPct, toPct) {
    const dx = (toPct[0] - fromPct[0]) * 16;
    const dy = (toPct[1] - fromPct[1]) * 9;
    if (dx === 0 && dy === 0) return 0;
    const a = Math.atan2(dy, dx) * 180 / Math.PI;
    return Math.max(-35, Math.min(35, a));
  }

  async function sail(legs) {
    ship.classList.add("sailing");
    for (let i = 0; i < legs.length; i++) {
      const [x, y, ms] = legs[i];
      if (i > 0) {
        const newHeading = headingDeg(legs[i - 1], legs[i]);
        const prevHeading = parseFloat((turnEl.style.transform.match(/-?[\d.]+/) || [0])[0]) || 0;
        turnEl.style.transform = `rotateZ(${newHeading}deg)`;
        // крен в повороте: корпус валится на борт, затем выравнивается в лёгкую качку
        const bank = Math.max(-40, Math.min(40, (newHeading - prevHeading) * 1.7));
        bankEl.style.transform = `rotateY(${bank}deg) rotateX(9deg)`;
        setTimeout(() => { bankEl.style.transform = "rotateY(-7deg) rotateX(9deg)"; }, ms * 0.55);
      }
      if (ms > 0) {
        ship.style.transition = `left ${ms}ms cubic-bezier(.45,.05,.55,.95), top ${ms}ms cubic-bezier(.45,.05,.55,.95)`;
        ship.style.left = x + "%";
        ship.style.top = y + "%";
        await sleep(ms + 80);
      } else {
        ship.style.transition = "none";
        ship.style.left = x + "%";
        ship.style.top = y + "%";
        void ship.offsetWidth; // применить мгновенно до включения переходов
      }
    }
    ship.classList.remove("sailing");
  }

  async function visit() {
    // В скрытой вкладке браузер не рисует кадры: переходы замрут. Не выходим зря.
    if (busy || document.hidden) return;
    busy = true;
    lastAttempt = Date.now();
    try {
      await sail(ENTER_LEGS);
      showBubble(pickMessage(), DOCK_MS);
      await sleep(DOCK_MS);
      await sail(EXIT_LEGS);
      ship.classList.remove("visible");
    } finally {
      busy = false;
    }
  }

  const reducedMotion = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function init() {
    const viewport = document.querySelector(".estate-viewport");
    if (!viewport || document.getElementById("harbor-ship")) return;

    ship = document.createElement("div");
    ship.id = "harbor-ship";
    ship.innerHTML =
      `<div class="ship-shadow"></div>` +
      `<div class="ship-bob" title="Кораблик-вестник: клик — внеочередная весточка">` +
        `<div class="ship-turn"><div class="ship-bank">${SHIP_SPRITE}</div></div>` +
        `<div class="ship-wake"></div>` +
      `</div>`;
    viewport.appendChild(ship);
    turnEl = ship.querySelector(".ship-turn");
    bankEl = ship.querySelector(".ship-bank");

    bubble = document.createElement("div");
    bubble.id = "harbor-ship-bubble";
    bubble.setAttribute("role", "status");
    viewport.appendChild(bubble);

    ship.style.left = ENTER_LEGS[0][0] + "%";
    ship.style.top = ENTER_LEGS[0][1] + "%";

    ship.querySelector(".ship-bob").addEventListener("click", () => {
      showBubble(pickMessage(), 4200);
    });

    if (reducedMotion) {
      ship.style.transition = "none";
      ship.style.left = ENTER_LEGS[ENTER_LEGS.length - 1][0] + "%";
      ship.style.top = ENTER_LEGS[ENTER_LEGS.length - 1][1] + "%";
      ship.classList.add("visible");
      setInterval(() => showBubble(pickMessage(), 6000), VISIT_INTERVAL);
      setTimeout(() => showBubble(pickMessage(), 6000), 1500);
      return;
    }

    setTimeout(() => {
      ship.classList.add("visible");
      visit();
    }, FIRST_DELAY);
    setInterval(visit, VISIT_INTERVAL);

    // Вернулся во вкладку, а кораблик давно не приходил - зовём через 10 секунд
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden && !busy &&
          Date.now() - lastAttempt > VISIT_INTERVAL - 30000) {
        setTimeout(() => { if (!document.hidden) visit(); }, 10000);
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // отладочный крючок: window.HarborShip.visit() — внеочередной заход
  window.HarborShip = { visit };
})();
