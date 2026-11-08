# Changelog

All changes in Platform are tracked here.

## Format
YYYY-MM-DD | change | reason | RFC

2026-06-30 | init decision system (D-001) | introduce structured thinking | RFC-001

2026-06-30

- Introduced Memory subsystem.
- Introduced Context Snapshots.
- Defined thinking versioning concept.
- Added architectural principle P9 (Evolution through MVP).

2026-10-19 | record first Gemini API test | added learning protocol and experiment log |

2026-10-22 | consolidate root docs into README, Docs, Notes | stop competing entry points |

2026-10-25 | engineering journal Memory/Engineering/ (protocol E-000, full audit E-001–E-008, secrets fix S-3) | durable cross-session engineering context | —

2026-10-25 | contour restructure: claude-chief-of-staff/ and Backup/ moved out of repo; graphify-out untracked; Interface/ removed; byte-identical duplicates dropped; Workspace/CURRENT.md renamed to notes-memory-design.md | one repository = one system | RFC-001

2026-10-25 | ADR consolidated into Core/Architecture/ADR (ADR-001..005 + INDEX); dangling ADR refs fixed | single ADR numbering space | RFC-001

2026-10-25 | RFC/ process created (README + RFC-001); D-002 branch model (develop / feature_X.Y.Z / release_X.Y.Z) | agreed change and release process | RFC-001

2026-10-25 | audit report archived: Memory/Archive/Reports/Report-2026-10-25-audit.md | record E-008 deliverable | —

2026-10-25 | Barrymore Morning Brief: deterministic generator + autonomous LLM agent (local FreeLLMAPI gateway, stdlib-only, ADR-003/004 compliant) | give Barrymore its own brains | —

2026-10-25 | Barrymore UX: map beacon removed, painted plaque is now the clickable entry; unread "Morning Brief" link under the plaque; user guide Docs/Barrymore.md | user request | —

2026-10-25 | Barrymore plaque becomes pure HTML over clean art: background swapped to Clear_main (painted text gone), portrait barrymore.png as separate layer, live greeting + task counter (tasks.js), "Review" link, geometry on CSS variables | user request | —

2026-10-26 | map layout: full-width frame with atmospheric blurred backdrop (no black bars, nothing cropped, plaque stays on-screen on 16:10); agent passports introduced in Memory/Agents (Barrymore partial-active, Solomon & Holmes drafts aligned with ADR-003/004) | user request + co-worked with second AI | —

2026-10-26 | new island "Holmes Study" on the map (beacon + modal + RU/EN), sidebars toggle; all 10 modals verified clickable | co-worked with second AI | —

2026-10-29 | Barrymore brief refresh button in dashboard; loopback-only local server runs the existing generator and returns the fresh report to the open modal | refresh Morning Brief on demand | —

2026-10-29 | Barrymore dashboard starts at Windows logon; source fingerprints avoid unchanged LLM runs; explicit Done tasks retain history for 48h before archival | persistent brief and task lifecycle | —

2026-10-29 | Platform v1.8.3: Tashkent time, silent Windows startup, cached Morning Brief, durable Barrymore task history and Graphify project report | on-demand, low-noise project overview | —

2026-10-29 | Maelstorm research beacons and translucent island markers | clarify island roles and reduce map clutter until hover | —

2026-10-29 | Platform v1.8.4: AI Sandbox usage ledger and security contour, Hunter cabinet in Core Citadel, project onboarding and context handoff | improve AI visibility, controlled safety checks, and continuity between sessions | —

2026-11-07 | Platform v1.8.7: planet button and worlds menu on index, world map v2 base (World_map_v2.png + generation prompt), excursion report-first tab with hard numbers, classic window controls in island modals, agents fleet panel (agents.html, dashboard-server +318 lines), kanban entity types (task/change/epic) and creation dates on cards, secret-gate phase 2 (RED on staged), ITIL task types API, evofind search, orders-triage radar | ship accepted night+day work as a version | —

2026-11-07 | cloud polygon kit Workspace/cloud/: bootstrap.sh, cloud-init for DigitalOcean and Yandex Cloud, compose stacks (DVWA, Juice Shop, n8n, Uptime Kuma, WireGuard), k3s installer, probe script, onboarding spec | one-command security/lab polygons on free cloud tiers | —

2026-11-07 | cloud workshop VM: Platform deployed to Yandex Cloud (Ubuntu 24.04, systemd dashboard service, loopback + SSH-tunnel access, read-only deploy key, runbook Docs/CLOUD-VM-RUNBOOK-2026-11-07-ZCode.md) | month-to-income workshop and showcase for the agent estate; dashboard stays private (one-way door) | —

2026-11-07 | templating protocol (Docs/TEMPLATING.md): Jinja2 templates in templates/ as source of truth, private per-host vars in Workspace/private/vars (untracked), renderer tools/render_templates.py with placeholder-safe repo mode, runbook converted to template | infra coordinates out of session memory and out of the public repo | —

2026-11-07 | cloud VM security lab: docker + compose, apt toolkit, practice targets from cloud kit bound to loopback only (fixes: compose 0.0.0.0 bindings and missing empty .env for secretless services) | docker bypasses ufw; lab targets must never face the internet; inventory kept in private zone | —

2026-11-07 | agent peer notes ("Заметка соседу"): agents may append one short note-to-a-neighbor line to routine LLM reports (run_agent.py -> Workspace/agents/peer-notes.jsonl, untracked); Barrymore plaque shows unread counter, digest panel in steward modal, GET/POST /api/peer-notes; Morning Brief gains one-line digest; ops: one-command dashboard restart script tools/ops/restart-dashboard.ps1 | agents occasionally show initiative and cross-talk at near-zero cost; launch stays manual (leash mode) | —
2026-11-09 | release 1.8.8: COMMAND CENTER штаб (топливо/конвейер/артефакты/ждёт-слова/деньги/сигналы + /api/tokens/usage), обсерватория Maelstorm (воронка/корабли/шлюпки), 14 драфт-миров + 13 превью (worlds-draft, выбор за Sovereign), принцип P12 нейтральность инструмента, план Dark Watch, intel-картотека выведена из git (visibility rule) | consolidation of 08-09.11 sessions | —
