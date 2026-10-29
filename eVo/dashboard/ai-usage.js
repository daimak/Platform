const htmlEscape = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;"
})[char]);

const numberFormat = (value) => value === null || value === undefined
  ? "Нет данных"
  : new Intl.NumberFormat("ru-RU").format(value);

function costFormat(amount, currency) {
  if (amount === null || amount === undefined || !currency) return "Неизвестно";
  return `${Number(amount).toFixed(6)} ${currency}`;
}

function timeFormat(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? htmlEscape(value) : new Intl.DateTimeFormat("ru-RU", {
    timeZone: "Asia/Tashkent",
    dateStyle: "short",
    timeStyle: "short"
  }).format(date);
}

async function requestJson(path, options = {}) {
  const response = await fetch(path, {
    cache: "no-store",
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(options.headers || {})
    }
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || `Ошибка сервера (${response.status}).`);
  return result;
}

function renderUsage(data) {
  const summary = data.summary;
  document.getElementById("metric-requests").textContent = numberFormat(summary.request_count);
  const tokenTotal = summary.total_tokens === null ? null : summary.total_tokens;
  document.getElementById("metric-tokens").textContent = numberFormat(tokenTotal);
  document.getElementById("metric-token-coverage").textContent = summary.known_token_requests
    ? `Счётчики есть для ${summary.known_token_requests} из ${summary.request_count} вызовов`
    : "Провайдер пока не сообщил счётчики токенов";
  document.getElementById("metric-cost").textContent = summary.costs.length
    ? summary.costs.map(({ amount, currency }) => costFormat(amount, currency)).join(" · ")
    : "Нет подтверждённых сумм";

  const snapshotRows = document.getElementById("snapshot-rows");
  snapshotRows.innerHTML = data.snapshots.length
    ? data.snapshots.map((snapshot) => `
      <tr>
        <td>${htmlEscape(snapshot.provider_name)}</td>
        <td>${snapshot.credits_used_percent == null ? "Нет данных" : `${htmlEscape(snapshot.credits_used_percent)}%`}</td>
        <td>${snapshot.input_tokens == null && snapshot.output_tokens == null ? "Нет данных" : `${numberFormat(snapshot.input_tokens)} / ${numberFormat(snapshot.output_tokens)}`}</td>
        <td>${costFormat(snapshot.cost_amount, snapshot.currency)}</td>
        <td>${htmlEscape([snapshot.period, snapshot.note].filter(Boolean).join(" · ") || "—")}</td>
        <td>${timeFormat(snapshot.recorded_at)}</td>
      </tr>`).join("")
    : `<tr><td colspan="6">Снимков пока нет. Добавьте подтверждённые значения вручную.</td></tr>`;

  const requestRows = document.getElementById("request-rows");
  requestRows.innerHTML = data.requests.map((request) => `
    <tr>
      <td>${timeFormat(request.recorded_at)}</td>
      <td>${htmlEscape(request.provider_name)}<br><span class="usage-muted">${htmlEscape(request.model)}</span></td>
      <td>${htmlEscape(request.purpose)}</td>
      <td>${numberFormat(request.input_tokens)} / ${numberFormat(request.output_tokens)}<br><span class="usage-muted">${request.usage_source === "provider_response" ? "данные ответа" : "неизвестно"}</span></td>
      <td>${costFormat(request.cost_amount, request.currency)}</td>
      <td>${htmlEscape(request.result_summary)}</td>
    </tr>`).join("");
  document.getElementById("empty-requests").hidden = data.requests.length > 0;
  document.getElementById("include-in-brief").checked = data.settings.include_in_morning_brief;

  const providerSelect = document.getElementById("snapshot-provider");
  const currentValue = providerSelect.value;
  const providers = [...data.providers, ...data.custom_providers.map(([id, name]) => ({ id, name }))];
  providerSelect.innerHTML = providers.map((provider) =>
    `<option value="${htmlEscape(provider.id)}">${htmlEscape(provider.name)}</option>`
  ).join("") + `<option value="custom">Другой сервис…</option>`;
  if (providers.some((provider) => provider.id === currentValue)) providerSelect.value = currentValue;
}

async function loadUsage() {
  const data = await requestJson("/api/ai-usage");
  renderUsage(data);
}

document.getElementById("refresh-usage").addEventListener("click", async () => {
  try {
    await loadUsage();
  } catch (error) {
    window.alert(error.message);
  }
});

document.getElementById("snapshot-provider").addEventListener("change", (event) => {
  document.getElementById("custom-provider-wrap").hidden = event.target.value !== "custom";
});

document.getElementById("snapshot-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const values = Object.fromEntries(new FormData(form));
  const selectedProvider = document.getElementById("snapshot-provider").value;
  const snapshot = {
    provider_id: selectedProvider === "custom"
      ? document.getElementById("custom-provider-name").value.trim().toLowerCase().replace(/[^a-z0-9._-]+/g, "-")
      : selectedProvider,
    ...(selectedProvider === "custom" ? { provider_name: document.getElementById("custom-provider-name").value.trim() } : {}),
    ...Object.fromEntries(["credits_used_percent", "input_tokens", "output_tokens", "cost_amount"]
      .map((key) => [key, values[key] === "" ? null : Number(values[key])])),
    currency: values.currency ? values.currency.toUpperCase() : null,
    period: values.period || null,
    note: values.note || ""
  };
  const status = document.getElementById("snapshot-status");
  try {
    await requestJson("/api/ai-usage/snapshots", {
      method: "POST",
      headers: { "X-Estate-Action": "ai-usage" },
      body: JSON.stringify(snapshot)
    });
    status.textContent = "Снимок сохранён.";
    form.reset();
    document.getElementById("custom-provider-wrap").hidden = true;
    await loadUsage();
  } catch (error) {
    status.textContent = `Не удалось сохранить: ${error.message}`;
  }
});

document.getElementById("include-in-brief").addEventListener("change", async (event) => {
  const checkbox = event.currentTarget;
  checkbox.disabled = true;
  try {
    const data = await requestJson("/api/ai-usage/settings", {
      method: "POST",
      headers: { "X-Estate-Action": "ai-usage" },
      body: JSON.stringify({ include_in_morning_brief: checkbox.checked })
    });
    checkbox.checked = data.settings.include_in_morning_brief;
  } catch (error) {
    checkbox.checked = !checkbox.checked;
    window.alert(error.message);
  } finally {
    checkbox.disabled = false;
  }
});

document.getElementById("ask-barrymore").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  const output = document.getElementById("barrymore-usage-result");
  button.disabled = true;
  output.hidden = false;
  output.textContent = "Бэрримор проверяет сохранённые сведения…";
  try {
    const data = await requestJson("/api/ai-usage/ask-barrymore", {
      method: "POST",
      headers: { "X-Estate-Action": "ai-usage" }
    });
    output.textContent = data.summary;
    await loadUsage();
  } catch (error) {
    output.textContent = `Не удалось получить обзор: ${error.message}`;
  } finally {
    button.disabled = false;
  }
});

loadUsage().catch((error) => {
  document.getElementById("snapshot-status").textContent = `Не удалось загрузить статистику: ${error.message}`;
});
