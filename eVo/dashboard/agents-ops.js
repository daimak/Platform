// Диспетчерская суб-агентов («Под ковром»): живая фактура ZCode-агентов
// по GET /api/agents/ops (metadata.json + output.txt каждого агента).
// Автообновление 20 с. Панель только читает.
(function () {
  'use strict';

  const box = document.getElementById('ops-flights');
  const updated = document.getElementById('ops-updated');
  if (!box) return;

  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  const ago = (min) => {
    if (min < 1) return 'только что';
    if (min < 60) return `${Math.round(min)} мин назад`;
    return `${Math.floor(min / 60)} ч ${Math.round(min % 60)} мин назад`;
  };

  const artifactLink = (path) => {
    const name = path.split(/[\\/]/).pop();
    if (/eVo[\\/]dashboard[\\/]/i.test(path)) {
      return `<a class="ops-artifact" href="${esc(name)}">📄 ${esc(name)}</a>`;
    }
    return `<span class="ops-artifact" title="${esc(path)}">📄 ${esc(name)}</span>`;
  };

  function render(data) {
    const flights = data.flights || [];
    if (!flights.length) {
      box.innerHTML = '<p class="ops-empty">Фактуры нет: живых суб-агентов не заведено.</p>';
    } else {
      box.innerHTML = flights.map((f) => {
        const tail = f.tail ? esc(f.tail.slice(-320)) : '(журнал пуст)';
        return `<article class="ops-flight ops-${esc(f.state)}">
          <span class="ops-dot" aria-hidden="true"></span>
          <div class="ops-main">
            <header><strong>${esc(f.task)}</strong><span class="ops-ago">${ago(f.age_min)}</span></header>
            <pre class="ops-tail">${tail}</pre>
            <footer>
              ${f.artifact ? artifactLink(f.artifact) : ''}
              <span class="ops-bytes">${(f.bytes / 1024).toFixed(0)} КБ · ${esc(f.state === 'writing' ? 'пишет' : 'молчит')}</span>
            </footer>
          </div>
        </article>`;
      }).join('');
    }
    if (updated) {
      updated.textContent = 'обновлено ' + new Date(data.generated_at).toLocaleTimeString('ru-RU');
    }
  }

  async function tick() {
    try {
      const response = await fetch('/api/agents/ops', { cache: 'no-store' });
      render(await response.json());
    } catch (error) {
      if (updated) updated.textContent = 'эндпоинт недоступен — рестартни сервер';
    }
  }

  tick();
  setInterval(tick, 20000);
})();
