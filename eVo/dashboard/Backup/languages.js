/**
 * eVo Command Center — Languages & Localization dictionary
 * Supports Estate World (Level 1), Command Center Modals (Level 2), and Workspace (Level 3)
 */

const LANG = {
  ru: {
    estateTitle: "PLATFORM ESTATE",
    commandCenter: "Центр управления",
    systemSubtitle: "Персональная операционная система eVo",
    platformAlive: "Платформа активна",
    heartbeat: "Пульс ядра: 1.2с",
    estateStatusQuiet: "Спокойно",
    activeProcessesLabel: "Активные процессы: 5",
    attentionQueueLabel: "Ожидают внимания: 2",
    clickToOpenConsole: "Нажмите, чтобы открыть консоль острова",
    closeBtnText: "✕ Закрыть окно",
    backToMapBtn: "← Вернуться к карте островов",

    // Стюард Бэрримор
    barrymoreTitle: "Стюард Бэрримор",
    barrymoreRole: "Хранитель состояния и картограф",
    barrymoreGreeting: "Доброе утро, Дмитрий.",
    barrymoreSubtext: "Пока вас не было, произошло 3 изменения.",
    barrymoreBriefBtn: "ОТКРЫТЬ MORNING BRIEF →",
    barrymoreFullBrief: "«Сэр, приветствую в eVo Estate. Завершена стабилизация интерфейса 2-го уровня. Все подсистемы ядра работают штатно, рабочее дерево чисто. Архитектурный переход от Foundation к Interface зафиксирован. Ожидаю ваших указаний по рабочим кабинетам.»",
    toWorkspaceBtn: "🚪 Перейти в рабочий кабинет",
    backToCommandCenter: "← Вернуться в Центр управления",

    // Острова и локации
    islands: {
      mainEstate: {
        title: "MAIN ESTATE",
        subtitle: "Главная усадьба • Управление и принятие решений",
        shortDesc: "Центральное ядро eVo. Архитектура, фундаментальные правила и общая координация.",
        badge: "CORE NEXUS",
        stateTitle: "СОСТОЯНИЕ СИСТЕМЫ",
        stateHeading: "Foundation → Interface",
        stateDesc: "eVo развивается от фундаментальных правил к наглядному пространственному интерфейсу.",
        activeProject: "Активный проект: Marvel V (Мощный стиль, палитра Midnight/Sunrise)"
      },
      workshop: {
        title: "eVo WORKSHOP",
        subtitle: "Мастерская • Эксперименты и прототипы",
        shortDesc: "Инфраструктура кода, сборка, Git-состояние и рабочие инструменты.",
        badge: "NODE 01: GIT & INFRA",
        branchTitle: "Ветка: experiment",
        gitStatus: "● Рабочее дерево чисто",
        commitLabel: "Последний коммит:",
        commitHash: "cad8c27 (refactor: boundaries v2)",
        toolsLabel: "Инструменты: evo-check.ps1, bootstrap.ps1, release gate."
      },
      aiSandbox: {
        title: "AI SANDBOX",
        subtitle: "Песочница ИИ • Безопасные эксперименты с агентами",
        shortDesc: "Среда автономных агентов и безопасного выполнения задач.",
        badge: "NODE 02: AGENTS",
        attentionHeading: "Точка внимания: Command Center",
        attentionStatus: "● В процессе разработки",
        attentionDesc: "Первый визуальный интерфейс управления системой eVo.",
        agentBarrymore: "Barrymore: Активен (Steward, Read-Only — ADR-0001)",
        agentContext: "Context Engine: Синхронизирован",
        agentMemory: "Memory Store: Снимок 2026-07-12 верифицирован",
        securityRule: "Правило ADR-0002: Агенты никогда не обращаются к ОС напрямую, всё через Tools."
      },
      careerGuild: {
        title: "CAREER GUILD & LEVERAGE",
        subtitle: "Гильдия развития • Точки роста и ключевые рычаги",
        shortDesc: "Управление приоритетными векторами и задачами следующего шага.",
        badge: "NODE 03: LEVERAGE",
        tasksHeading: "Приоритетные рычаги (Next Leverage)",
        task1: "Визуальное состояние системы (Estate Level 2)",
        task2: "Интеграция долговременной памяти (Context / Decisions)",
        task3: "Пространственная карта Estate и шлюз рабочих кабинетов",
        addTaskPlaceholder: "Новый рычаг или задача...",
        addTaskBtn: "+ Добавить"
      },
      memoryLibrary: {
        title: "MEMORY LIBRARY",
        subtitle: "Библиотека памяти • Контекст, решения и хроника",
        shortDesc: "Хранилище долговременного контекста, решений (ADR) и истории эволюции.",
        badge: "NODE 04: MEMORY",
        evolutionHeading: "Хроника эволюции системы",
        evolutionPath: "Platform → eVo → Command Center → Estate",
        estateL1: "Уровень 1: Мир Estate (Пространственная модель)",
        estateL2: "Уровень 2: Command Center (Центр управления)",
        estateL3: "Уровень 3: Рабочий кабинет (Фокусное исполнение)",
        archiveFiles: "Снимки контекста: eVo-SNAPSHOT-2026-07-12.md, RFC-003, ADR-0001..0003."
      },
      navigator: {
        title: "NAVIGATOR OBSERVATORY",
        subtitle: "Обсерватория Навигатора • Исследования и разведка",
        shortDesc: "Дорожная карта эволюции мира Estate и перспективные направления.",
        badge: "VISION & ROADMAP",
        task1Title: "TASK 1: Здания как функциональные объекты",
        task1Desc: "Превращение зданий на карте в интерактивные объекты eVo с hover и click консолями.",
        task2Title: "TASK 2: Живой мир (Living World)",
        task2Desc: "Птицы, облака, туман, волны, динамические окна и циклы дня/ночи.",
        principle: "Принцип: «Не строить величайшее сооружение раньше времени. Создать живой фундамент»."
      },
      harbor: {
        title: "THE HARBOR",
        subtitle: "Гавань • Интеграции и внешние связи",
        shortDesc: "Морские пути коммуникации, внешние API, удаленные репозитории и интеграции.",
        badge: "CONNECTIONS",
        harborInfo: "Порт обмена сообщениями и контекстными кораблями между внешними архипелагами.",
        status: "● Все каналы связи защищены и готовы к интеграции."
      },
      knowledgeArchive: {
        title: "KNOWLEDGE ARCHIVE",
        subtitle: "Архив знаний • Документация и концепты",
        shortDesc: "База знаний, архитектурные документы Vision и принципы построения цифрового мира.",
        badge: "KNOWLEDGE",
        docsInfo: "Документы: The_Kingdom_Map_Principle.md, The_Citadel_and_Roads.md, Digital_World_Map.md.",
        quote: "«Dashboard — это не украшение. Dashboard — это карта текущего состояния королевства»."
      }
    },

    // Рабочий кабинет (Уровень 3)
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
    estateTitle: "PLATFORM ESTATE",
    commandCenter: "Command Center",
    systemSubtitle: "eVo Personal Operating System",
    platformAlive: "Platform alive",
    heartbeat: "Core heartbeat: 1.2s",
    estateStatusQuiet: "Quiet",
    activeProcessesLabel: "Active processes: 5",
    attentionQueueLabel: "Awaiting attention: 2",
    clickToOpenConsole: "Click to open island console",
    closeBtnText: "✕ Close Window",
    backToMapBtn: "← Return to Islands Map",

    // Steward Barrymore
    barrymoreTitle: "Steward Barrymore",
    barrymoreRole: "State Keeper & Cartographer",
    barrymoreGreeting: "Good morning, Dmitry.",
    barrymoreSubtext: "While you were away, 3 changes occurred.",
    barrymoreBriefBtn: "OPEN MORNING BRIEF →",
    barrymoreFullBrief: "\"Sir, welcome to eVo Estate. Interface Level 2 stabilization is complete. All core subsystems operate within nominal parameters, working tree is clean. Architecture evolution Foundation → Interface is established. Awaiting your directives for the workspaces.\"",
    toWorkspaceBtn: "🚪 Enter Workspace",
    backToCommandCenter: "← Return to Command Center",

    // Islands & Locations
    islands: {
      mainEstate: {
        title: "MAIN ESTATE",
        subtitle: "Main Citadel • Decision Making & Core Control",
        shortDesc: "The core of eVo. Architecture, fundamental rules, and system coordination.",
        badge: "CORE NEXUS",
        stateTitle: "CURRENT STATE",
        stateHeading: "Foundation → Interface",
        stateDesc: "eVo evolves from fundamental principles into a spatial visual operating system.",
        activeProject: "Active Project: Marvel V (Powerful theme, Midnight/Sunrise palette)"
      },
      workshop: {
        title: "eVo WORKSHOP",
        subtitle: "Workshop • Experiments & Prototypes",
        shortDesc: "Code infrastructure, builds, Git state, and operational developer tools.",
        badge: "NODE 01: GIT & INFRA",
        branchTitle: "Branch: experiment",
        gitStatus: "● Working tree clean",
        commitLabel: "Latest commit:",
        commitHash: "cad8c27 (refactor: boundaries v2)",
        toolsLabel: "Tools: evo-check.ps1, bootstrap.ps1, release gate."
      },
      aiSandbox: {
        title: "AI SANDBOX",
        subtitle: "AI Sandbox • Safe Agent Experiments",
        shortDesc: "Autonomous agent execution environment and safe task orchestration.",
        badge: "NODE 02: AGENTS",
        attentionHeading: "Attention Point: Command Center",
        attentionStatus: "● Building",
        attentionDesc: "First visual operating interface for the eVo system.",
        agentBarrymore: "Barrymore: Active (Steward, Read-Only — ADR-0001)",
        agentContext: "Context Engine: Synchronized",
        agentMemory: "Memory Store: Snapshot 2026-07-12 verified",
        securityRule: "Rule ADR-0002: Agents never access the OS directly, everything through Tools."
      },
      careerGuild: {
        title: "CAREER GUILD & LEVERAGE",
        subtitle: "Guild of Growth • Vectors & Key Leverage Points",
        shortDesc: "Managing priority vectors, leverage actions, and tactical deliverables.",
        badge: "NODE 03: LEVERAGE",
        tasksHeading: "Priority Vectors (Next Leverage)",
        task1: "Visual state & spatial depth (Estate Level 2)",
        task2: "Long-term memory integration (Context / Decisions)",
        task3: "Estate spatial world map & workspace portal",
        addTaskPlaceholder: "New leverage vector or task...",
        addTaskBtn: "+ Add"
      },
      memoryLibrary: {
        title: "MEMORY LIBRARY",
        subtitle: "Memory Library • Context, Decisions & Chronicle",
        shortDesc: "Long-term memory vault, Architecture Decision Records (ADRs), and evolution log.",
        badge: "NODE 04: MEMORY",
        evolutionHeading: "System Evolution Chronicle",
        evolutionPath: "Platform → eVo → Command Center → Estate",
        estateL1: "Level 1: Estate World (Spatial Model)",
        estateL2: "Level 2: Command Center (Current Layer)",
        estateL3: "Level 3: Workspace (Focused Execution)",
        archiveFiles: "Memory Snapshots: eVo-SNAPSHOT-2026-07-12.md, RFC-003, ADR-0001..0003."
      },
      navigator: {
        title: "NAVIGATOR OBSERVATORY",
        subtitle: "Navigator Observatory • Research & Reconnaissance",
        shortDesc: "Roadmap of Estate evolution, unexplored horizons, and research vectors.",
        badge: "VISION & ROADMAP",
        task1Title: "TASK 1: Buildings as Functional Objects",
        task1Desc: "Transforming map buildings into interactive eVo objects with hover and click consoles.",
        task2Title: "TASK 2: Living World",
        task2Desc: "Birds, clouds, fog, waves, dynamic lighting, and day/night transitions.",
        principle: "Principle: \"Do not build the greatest fortress ahead of time. Create a living foundation.\""
      },
      harbor: {
        title: "THE HARBOR",
        subtitle: "The Harbor • Integration & External Connections",
        shortDesc: "Maritime routes, external APIs, remote repositories, and external handoffs.",
        badge: "CONNECTIONS",
        harborInfo: "Port of message transport ships between external archipelagos and Platform Core.",
        status: "● All communication channels encrypted and operational."
      },
      knowledgeArchive: {
        title: "KNOWLEDGE ARCHIVE",
        subtitle: "Knowledge Archive • Documentation & Principles",
        shortDesc: "Knowledge vault, Vision architectural documents, and digital world principles.",
        badge: "KNOWLEDGE",
        docsInfo: "Documents: The_Kingdom_Map_Principle.md, The_Citadel_and_Roads.md, Digital_World_Map.md.",
        quote: "\"A dashboard is not a decoration. A dashboard is a map of the kingdom's current state.\""
      }
    },

    // Workspace (Level 3)
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