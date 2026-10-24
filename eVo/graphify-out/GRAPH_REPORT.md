# Graph Report - eVo  (2026-10-20)

## Corpus Check
- 25 files · ~299,911 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: .css 2)

## Summary
- 123 nodes · 105 edges · 42 communities (9 shown, 33 thin omitted)
- Extraction: 72% EXTRACTED · 28% INFERRED · 0% AMBIGUOUS · INFERRED: 29 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- eVo Vision and Stewardship
- Dashboard Interaction Logic
- Archived Dashboard Logic
- Estate Dashboard Status
- Estate Island Map
- Command Center Planning
- Workspace Navigation Model
- Sunrise Visual Identity
- Workspace Task Checklist
- Archived Localization Data
- Dashboard Localization Data
- Marvel V Project
- Estate Main Hub
- Project Initialization
- Barrymore and Command Center
- AI Sandbox Module
- Career Development Module
- Workshop Module
- Knowledge Archive Module
- Memory Library Module
- Morning Brief Module
- Navigator Module
- Harbor Module
- Estate AI Sandbox
- Career Leverage
- Workshop Prototype
- Island Console UI
- Knowledge Archive Design
- Memory Library Design
- Navigator Observatory Design
- Harbor Workspace
- Barrymore Steward
- Career Guild Design
- eVo Workshop Design
- Harbor Experience
- Knowledge Archive Experience
- Main Estate Experience
- Memory Library Experience
- Navigator Experience
- Navigator Observatory Node

## God Nodes (most connected - your core abstractions)
1. `Platform Estate Command Center` - 10 edges
2. `Platform Estate Command Center` - 10 edges
3. `openIslandModal()` - 7 edges
4. `openIslandModal()` - 7 edges
5. `Visual Dashboard` - 6 edges
6. `renderLeverageTasksHTML()` - 4 edges
7. `renderLeverageTasksHTML()` - 4 edges
8. `eVo` - 4 edges
9. `eVo Steward` - 4 edges
10. `closeIslandModal()` - 3 edges

## Surprising Connections (you probably didn't know these)
- `Visual Dashboard` --conceptually_related_to--> `Dashboard Directory`  [INFERRED]
  README.md → project-tree.txt
- `Command Center v0.2 Architectural Assembly` --semantically_similar_to--> `Command Center v0.2 Architectural Assembly`  [INFERRED] [semantically similar]
  dashboard/index.html → dashboard/workspace.html
- `marvel_v Project` --references--> `marvel_v Project`  [EXTRACTED]
  dashboard/Backup/history.md → dashboard/Backup/index.html
- `Level 3 Workspace` --conceptually_related_to--> `Level 3 Workspace`  [EXTRACTED]
  dashboard/Backup/index.html → dashboard/Backup/workspace.html

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Estate Island Network** — evo_dashboard_backup_index_platform_estate, evo_dashboard_backup_index_main_estate, evo_dashboard_backup_index_barrymore, evo_dashboard_backup_index_evo_workshop, evo_dashboard_backup_index_navigator_observatory, evo_dashboard_backup_index_ai_sandbox, evo_dashboard_backup_index_memory_library, evo_dashboard_backup_index_knowledge_archive, evo_dashboard_backup_index_the_harbor, evo_dashboard_backup_index_career_guild_leverage, evo_dashboard_backup_index_island_consoles [EXTRACTED 1.00]
- **Islands of the Platform Estate** — evo_dashboard_index_main_estate, evo_dashboard_index_barrymore, evo_dashboard_index_evo_workshop, evo_dashboard_index_navigator_observatory, evo_dashboard_index_ai_sandbox, evo_dashboard_index_memory_library, evo_dashboard_index_knowledge_archive, evo_dashboard_index_harbor, evo_dashboard_index_career_guild_leverage [EXTRACTED 1.00]
- **eVo Dashboard Modules** — evo_dashboard_assets_estate_bg_morning_brief, evo_dashboard_assets_estate_bg_navigator_observatory, evo_dashboard_assets_estate_bg_memory_library, evo_dashboard_assets_estate_bg_the_harbor, evo_dashboard_assets_estate_bg_career_guild, evo_dashboard_assets_estate_bg_evo_workshop, evo_dashboard_assets_estate_bg_ai_sandbox, evo_dashboard_assets_estate_bg_knowledge_archive [EXTRACTED 1.00]
- **Platform Estate dashboard modules** — evo_dashboard_assets_estate_bg_original_main_estate, evo_dashboard_assets_estate_bg_original_navigator_observatory, evo_dashboard_assets_estate_bg_original_memory_library, evo_dashboard_assets_estate_bg_original_the_harbor, evo_dashboard_assets_estate_bg_original_evo_workshop, evo_dashboard_assets_estate_bg_original_ai_sandbox, evo_dashboard_assets_estate_bg_original_knowledge_archive, evo_dashboard_assets_estate_bg_original_career_guild [INFERRED 0.95]

## Communities (42 total, 33 thin omitted)

### Community 0 - "eVo Vision and Stewardship"
Cohesion: 0.13
Nodes (15): Dashboard Directory, Attention Points, Context, Decisions, Direction, eVo, eVo Command Center, eVo Steward (+7 more)

### Community 1 - "Dashboard Interaction Logic"
Cohesion: 0.27
Nodes (13): bindTaskEvents(), buildIslandContentHTML(), closeIslandModal(), closeWorkspaceModal(), escapeHtml(), initIslandHotspots(), initLanguageControls(), initModalControls() (+5 more)

### Community 2 - "Archived Dashboard Logic"
Cohesion: 0.27
Nodes (13): bindTaskEvents(), buildIslandContentHTML(), closeIslandModal(), closeWorkspaceModal(), escapeHtml(), initIslandHotspots(), initLanguageControls(), initModalControls() (+5 more)

### Community 3 - "Estate Dashboard Status"
Cohesion: 0.15
Nodes (13): Active Processes, AI Sandbox, Items Awaiting Attention, Career Guild, Estate Status, eVo Workshop, Knowledge Archive, Main Estate (+5 more)

### Community 4 - "Estate Island Map"
Cohesion: 0.18
Nodes (11): AI Sandbox, Career Guild, Estate Status, eVo Workshop, Knowledge Archive, Main Estate, Memory Library, Morning Brief (+3 more)

### Community 5 - "Command Center Planning"
Cohesion: 0.33
Nodes (5): Barrymore Steward, Command Center v0.2 Architecture, Level 3 Workspace, Active Task: Command Center v0.2 Architectural Assembly, Level 3 Workspace

### Community 6 - "Workspace Navigation Model"
Cohesion: 0.50
Nodes (3): Island Console, Level 3 Workspace, Platform Estate

### Community 7 - "Sunrise Visual Identity"
Cohesion: 0.50
Nodes (4): Luminous Organic Orb, Moss-Covered Rock, Stylized Sunrise, Sunrise Logo Artwork

### Community 8 - "Workspace Task Checklist"
Cohesion: 0.67
Nodes (3): Command Center v0.2 Architectural Assembly, Command Center v0.2 Architectural Assembly, Workspace Task Checklist

## Knowledge Gaps
- **72 isolated node(s):** `Personal Operating System`, `Decisions`, `Human Capability`, `Memory`, `Direction` (+67 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 82 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **33 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Are the 10 inferred relationships involving `Platform Estate Command Center` (e.g. with `AI Sandbox` and `Career Guild`) actually correct?**
  _`Platform Estate Command Center` has 10 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Personal Operating System`, `Decisions`, `Human Capability` to the rest of the system?**
  _72 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `eVo Vision and Stewardship` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._
- **Are the 10 inferred relationships involving `Platform Estate Command Center` (e.g. with `AI Sandbox` and `Career Guild`) actually correct?**
  _`Platform Estate Command Center` has 10 INFERRED edges - model-reasoned connections that need verification._