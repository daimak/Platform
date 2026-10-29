# Barrymore

Barrymore is an execution assistant for Platform.

Responsibilities:

- execute approved operations;
- validate results;
- produce reports;
- preserve audit trail.

Barrymore does not make architectural decisions.

Human remains the final authority.

The local dashboard server is installed as a current-user Windows logon task with
`install-dashboard.ps1`. It binds to loopback only; task completion is recorded
only after an explicit user action in the dashboard.
It uses `pythonw.exe` at logon and suppresses child console windows. Dashboard
timestamps and server logs use Tashkent time (UTC+5); task history is stored in UTC.

The AI Sandbox links to `eVo/dashboard/ai-usage.html`. Its local ledger is stored
outside the repository at `%LOCALAPPDATA%\Platform\AI-Usage\usage.json`. FreeLLMAPI
request metadata is recorded when the gateway includes usage; reported cost is
never estimated from token counts. Copilot, ChatGPT subscriptions, and providers
without an installed collector require a manual snapshot. New collectors should
normalize provider responses through `ai_usage.record_request`; do not store raw
prompts or responses. Barrymore can review the ledger by explicit action, and
including its summary in Morning Brief is an opt-in setting.