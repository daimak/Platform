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