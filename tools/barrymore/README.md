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