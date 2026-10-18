/**
 * eVo Command Center — Languages & Localization dictionary
 */

const LANG = {
    ru: {
        commandCenter: "Центр управления",
        systemSubtitle: "Персональная операционная система eVo",
        platformAlive: "Платформа активна",
        heartbeat: "Пульс ядра: 1.2с",
        barrymoreTitle: "Стюард Бэрримор",
        barrymoreStatus: "Наблюдение активно • 3 вектора в фокусе",
        barrymoreBriefing: "«Сэр, все подсистемы функционируют штатно. Архитектурный переход от Foundation к Interface завершён. Ожидаю указаний по рабочим кабинетам.»",
        toWorkspaceBtn: "🚪 Перейти в рабочий кабинет",
        backToCommandCenter: "← Вернуться в Центр управления",
        
        currentStateLabel: "СОСТОЯНИЕ СИСТЕМЫ",
        currentTitle: "Основа → Интерфейс",
        currentText: "eVo развивается от идеи и фундаментальных правил к наглядному пространственному интерфейсу.",
        
        gitStateLabel: "GIT-СОСТОЯНИЕ",
        branchTitle: "Ветка experiment",
        gitClean: "● Рабочее дерево чисто",
        latestCommitLabel: "Последний коммит:",
        commitHash: "cad8c27 (refactor: boundaries v2)",
        
        attentionLabel: "ТОЧКА ВНИМАНИЯ",
        attentionTitle: "Command Center",
        statusBuilding: "● В процессе разработки",
        attentionDesc: "Первый визуальный интерфейс управления системой eVo.",
        
        agentsLabel: "СТАТУС АГЕНТОВ & ПОДСИСТЕМ",
        agentBarrymore: "Barrymore: Активен (Steward, Read-Only)",
        agentContext: "Context Engine: Синхронизирован",
        agentMemory: "Memory Store: Снимок 2026-07-12 верифицирован",
        
        leverageLabel: "КЛЮЧЕВЫЕ РЫЧАГИ (NEXT LEVERAGE)",
        leverageTitle: "Задачи панели управления",
        taskVisualState: "Визуальное состояние системы (Estate Level 2)",
        taskMemory: "Интеграция долговременной памяти (Context / Decisions)",
        taskSystemMap: "Пространственная карта Estate и шлюз рабочих кабинетов",
        addTaskPlaceholder: "Новый рычаг или задача...",
        addTaskBtn: "+ Добавить",
        
        evolutionLabel: "ЭВОЛЮЦИЯ СИСТЕМЫ",
        evolutionTitle: "Хроника развития",
        evolutionFlow: "Platform → eVo → Command Center → Estate",
        estateLevel1: "Уровень 1: Мир Estate (Пространственная модель)",
        estateLevel2: "Уровень 2: Command Center (Центр управления)",
        estateLevel3: "Уровень 3: Рабочий кабинет (Фокусное исполнение)",
        
        workspaceTitle: "Рабочий кабинет: eVo Core Workspace",
        workspaceSubtitle: "Уровень 3 — Непосредственное выполнение задач и редактирование контекста",
        activeTaskSection: "Активная задача",
        taskName: "Архитектурная сборка Command Center v0.2",
        taskDesc: "Объединение пространственной метафоры Estate, стюарда Бэрримора и рабочего интерфейса.",
        checklistTitle: "Контрольный список:",
        check1: "Реализовать атмосферную глубину и визуальную иерархию",
        check2: "Интегрировать стюарда Бэрримора как точку входа",
        check3: "Обеспечить бесшовный переход между уровнями 2 и 3",
        statusSelectorLabel: "Статус задачи:",
        statusBuildingOpt: "В разработке",
        statusOperationalOpt: "Завершена / Готова",
        saveTaskBtn: "Сохранить изменения"
    },
    en: {
        commandCenter: "Command Center",
        systemSubtitle: "eVo Personal Operating System",
        platformAlive: "Platform alive",
        heartbeat: "Core heartbeat: 1.2s",
        barrymoreTitle: "Steward Barrymore",
        barrymoreStatus: "Vigilant • 3 vectors in focus",
        barrymoreBriefing: "\"Sir, all subsystems are operating within nominal parameters. The transition from Foundation to Interface is stable. Awaiting your directive for the workspace.\"",
        toWorkspaceBtn: "🚪 Enter Workspace",
        backToCommandCenter: "← Return to Command Center",
        
        currentStateLabel: "CURRENT STATE",
        currentTitle: "Foundation → Interface",
        currentText: "eVo is evolving from fundamental concept and architectural rules into a spatial command center.",
        
        gitStateLabel: "GIT STATE",
        branchTitle: "Branch: experiment",
        gitClean: "● Working tree clean",
        latestCommitLabel: "Latest commit:",
        commitHash: "cad8c27 (refactor: boundaries v2)",
        
        attentionLabel: "ATTENTION POINT",
        attentionTitle: "Command Center",
        statusBuilding: "● Building",
        attentionDesc: "First visual operating interface for the eVo system.",
        
        agentsLabel: "AGENTS & SUBSYSTEMS STATUS",
        agentBarrymore: "Barrymore: Active (Steward, Read-Only)",
        agentContext: "Context Engine: Synchronized",
        agentMemory: "Memory Store: Snapshot 2026-07-12 verified",
        
        leverageLabel: "NEXT LEVERAGE",
        leverageTitle: "Priority Vectors",
        taskVisualState: "Visual state & spatial depth (Estate Level 2)",
        taskMemory: "Long-term memory integration (Context / Decisions)",
        taskSystemMap: "Estate spatial world map & workspace portal",
        addTaskPlaceholder: "New leverage vector or task...",
        addTaskBtn: "+ Add",
        
        evolutionLabel: "EVOLUTION",
        evolutionTitle: "System Chronicle",
        evolutionFlow: "Platform → eVo → Command Center → Estate",
        estateLevel1: "Level 1: Estate World (Spatial Model)",
        estateLevel2: "Level 2: Command Center (Current Layer)",
        estateLevel3: "Level 3: Workspace (Focused Execution)",
        
        workspaceTitle: "Focused Workspace: eVo Core",
        workspaceSubtitle: "Level 3 — Direct execution, context manipulation and task management",
        activeTaskSection: "Active Task",
        taskName: "Architectural synthesis of Command Center v0.2",
        taskDesc: "Merging Estate spatial depth, Steward Barrymore, and tactile operations.",
        checklistTitle: "Checklist:",
        check1: "Implement atmospheric depth and strict visual hierarchy",
        check2: "Anchor Steward Barrymore as primary system gateway",
        check3: "Provide seamless Level 2 ↔ Level 3 transition",
        statusSelectorLabel: "Task Status:",
        statusBuildingOpt: "Building",
        statusOperationalOpt: "Operational / Completed",
        saveTaskBtn: "Save Changes"
    }
};

let currentLanguage = localStorage.getItem("evo_language") || "ru";