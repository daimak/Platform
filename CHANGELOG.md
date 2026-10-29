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

2026-10-29 | Maelstorm research beacons and translucent island markers | clarify island roles and reduce map clutter until hover | -
