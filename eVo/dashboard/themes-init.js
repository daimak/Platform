/* themes-init.js v1 — применяет сохранённую гамму (evo_theme_v1) до отрисовки.
   Подключается во ВСЕ экраны; кнопка выбора — в шлюзе ядра (nav-dock.js). */
(function () {
  try {
    var t = localStorage.getItem('evo_theme_v1');
    if (t && t !== 'evo') document.documentElement.setAttribute('data-theme', t);
  } catch (e) { /* private mode — молча */ }
})();
