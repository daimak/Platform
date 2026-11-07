# Промпт: базовая карта Мира (v2.1 — раздолье океана) — 07.11, ZCode

Заказ Sovereign: гигантский мир, где 3 архипелага поместья — лишь домашняя малая часть. База = суша+океан; кораблики, облака, извержения — позже, HTML-слоями (как гермбы/клик-зоны Эстейта). Референсы приложит Sovereign (стиль только для домашних островов).

**v2.1 (правка Дмитрия 07.11):** расстояния между континентами ×3 — водная гладь главенствует; в открытом море — мелкие «морские обидатели» + пара течений, ТОЛЬКО дополняющие акценты; архипелаги меньше, но без потери качества (меньше за счёт океана, не за счёт детализации).

## Промпт (EN — основной, для image-модели)

```
Hand-painted fantasy world map, painterly digital illustration in the spirit of classic
MMORPG world atlases (World of Warcraft style cartography). Top-down illustrated map view —
not a satellite photo, not a 3D render. The artwork fills the entire frame edge to edge,
wide 16:9 banner, no borders, no frame, no text, no letters, no labels, no watermark.

COMPOSITION — THE OCEAN DOMINATES: vast open water is the main character of this map.
Landmasses together cover roughly a third of the frame, separated by WIDE stretches of open
sea — three times the natural spacing, generous negative space of ocean between every
region. Every landmass keeps full internal detail and a readable silhouette; it looks
smaller only because the ocean is grander, never because it is emptier.

One continuous world ocean with six distinct regions:

SOUTH-WEST — THE HOME WATERS (use the attached island images strictly as STYLE reference
for this cluster only; do not copy their composition): a small, cozy, sunlit archipelago of
three islands — a warm estate island with a manor, gardens and a lighthouse; a compact
industrial atoll with pipes and a glowing core; a wild storm-swirl island. Turquoise shallow
water, coral reefs, soft golden light. The tiniest region of the map — home must feel safe,
small and loved.

CENTER-OCEAN — THE TURTLE OF POSSIBILITIES: a colossal ancient sea turtle resting on the
surface, its island-sized shell overgrown with a lush tropical island — waterfall pouring
off the shell rim, palm groves, tiny glowing campfires, drifting light-motes above it like
sparks of possibilities. Calm radiant ocean around it.

SOUTH-EAST — PIRATE REACHES: scattered jagged islets, shipwreck hulls on reefs, smuggler
coves with lantern glow, tattered black sails hanging in coves, darker teal water with foam.

NORTH — THE FROZEN REACH (Northrend-like): a vast continent of glaciers and fjords, a frozen
spire city, pale aurora on the horizon, steel-blue palette, snow squalls.

FAR WEST — THE ASHEN LANDS: a gloomy continent with one huge DORMANT volcano (no smoke, no
eruption), obsidian beaches, dead forests, glowing ember cracks, blood-red dusk light.

EAST — THE UNKNOWN: the map's eastern edge dissolves into mist and an unexplored coastline;
faint silhouettes of uncharted islands in fog, subtle darker water suggesting deep-sea
monsters below — a deliberately unfinished, inviting feeling.

OPEN-OCEAN LIFE — TINY ACCENTS ONLY: a handful of small sea creatures scattered across the
vast empty waters — a small sea serpent arching once between the waves, a single kraken
tentacle tip curling above the surface far from any land, two whale backs, a glinting school
of fish — each creature occupies well under 2% of the frame, subtle, painted in the map's
own palette, purely decorative, calm and unhurried, never the center of attention. Two or
three delicate ocean currents drawn as thin elegant swirls of lighter foam and drifting
glints, flowing between the regions like faint routes across the sea.

Painterly textures, hand-drawn coastlines with subtle ink outlines, hachure-style mountain
shading, rich saturated colors unified by warm light, readable silhouettes at small scale,
moderate detail density, slight vignette only at extreme corners.

Strictly avoid: any text or letters, ships on open water (seas must be empty of vessels —
ships added later), clouds, active volcanic eruptions, people, modern objects, UI elements,
photo-realism, letterbox bars or empty margins, oversized or scary sea monsters.
```

## Зеркало (RU — для понимания/моделей, любящих русский)

Нарисованная от руки фэнтези-карта мира в духе классических игровых атласов (стиль WoW), вид сверху-иллюстрация, не спутник и не 3D, без рамок, текста и надписей, 16:9. КОМПОЗИЦИЯ — ГЛАВНЫЙ ГЕРОЙ ОКЕАН: суша занимает примерно треть кадра, между всеми регионами — широкие просторы открытого моря (втрое больше естественного расстояния); каждый клочок суши сохраняет полную детализацию и читаемый силуэт — суши меньше только потому, что океан стал больше. Шесть регионов: юго-запад — малые уютные Домашние воды (три острова по приложенным референсам: усадьба с маяком, индустриальный атолл с ядром, дикий остров-шторм); в центре океана — гигантская черепаха-остров Возможностей (панцирь зарос тропическим островом, водопад с края, палмы, тлеющие костры, искры-возможности над панцирем); юго-восток — Пиратские отмели (рваные островки, остовы кораблей на рифах, контрабандистские бухты с фонарями); север — Мёрзлый Север (айсберги, фьорды, шпиль ледяного города, северное сияние); далёкий запад — Пепельные земли (огромный спящий вулкан, обсидиановые пляжи, мёртвый лес, багровый закат); восток — Неведомое (край карты в тумане, призрачные силуэты неизведанных островов). ЖИЗНЬ ОТКРЫТОГО МОРЯ — ТОЛЬКО МЕЛКИЕ АКЦЕНТЫ: несколько крошечных морских обитателей в пустых водах — морской змей, раз выгнувшийся над волной, кончик щупальца кракена вдалеке от берегов, две китовые спины, блестящая стайка рыб — каждый заметно меньше 2% кадра, в палитре карты, чисто декоративные, спокойные, не в центре внимания; плюс два-три изящных течения — тонкие вихри светлой пены и бликов, текущие между регионами, как едва заметные маршруты. Живописные текстуры, рукописные береговые линии, штриховка гор, насыщенный цвет в едином тёплом свете. Строго без: текста, кораблей в море, облаков, извержений, людей, современных предметов, фотореализма, чёрных полей, огромных страшных монстров.

## Как подавать референсы
- Приложить: стилевые исходники домашних островов (+ World_map_v1.png как «наш вайб»).
- Формулировка к модели: «The attached images are STYLE references for the home archipelago only — extend their painting style to the whole world; do not copy their layout».
- Пропорция: 16:9 (1672×941 или больше) — встанет в существующий фрейм world-map.html без вёрстки заново.

## Чек приёмки базы перед приклейкой слоёв
1. Океан занимает заметно больше половины кадра (≈2/3); между регионами — чистая гладь.
2. Суши мельче, НО детализация не просела: зум-проверка каждого региона.
3. «Обидатели»: с первого взгляда не заметны (маленькие!), при рассмотрении — радуют; никаких гигантских битв.
4. Течения: 2–3 тонкие линии пены/бликов, не спорят с будущими маршрутами корабликов.
5. Край кадра: ни чёрных полей, ни рамки (правило letterbox).
6. Нигде нет текста/букв (подписи навешиваем HTML-слоями).
7. Вулкан спящий (извержение — слой анимации позже).
8. Уменьшить до ширины дашборда (~1672px): силуэты регионов читаются.

## Правка существующего варианта (дельта-промпт для второго хода)

Механика: полный промпт в новом чате = новая случайная карта. Переделка = ТОТ ЖЕ чат + приложить текущий вариант + короткая дельта-инструкция (стиль/регионы сохраняются, меняется заказанное). Крупные правки (×3 раздолье) модель перерендерит целиком, но с исходником сохранит стиль и острова.

```
Edit the attached world map. Keep the exact painting style, palette, lighting, and the look
of all six regions unchanged. Make only these changes:

1. Push the continents and island groups three times farther apart — the open ocean now
dominates (land covers about a third of the frame). Same regions, same relative directions:
home south-west, turtle center, pirates south-east, frozen north, ashen far west, unknown
east.
2. Every region keeps its internal detail and readable silhouette — regions look smaller
only because the ocean is grander, never emptier.
3. Add tiny sea creatures in the open water: a small sea serpent arching once between the
waves, one kraken tentacle tip far from any land, two whale backs, a glinting school of
fish — each well under 2% of the frame, calm, decorative, painted in the map's own palette.
4. Add two or three delicate ocean currents — thin elegant swirls of lighter foam and
drifting glints flowing between the regions, like faint routes across the sea.

Everything else stays exactly as in the attached map. No text, no ships, no clouds, no
eruptions, no letterbox bars, no oversized monsters.
```

Если канал теряет память между сессиями — предыдущий вариант прикладывать всегда.

## Слои будущего (не в базе)
- Кораблики-агенты (анимация по events.jsonl — прототип в agents.html).
- Облака/туман (CSS-слой с parallax).
- Извержение вулкана (периодический FX — триггер по событиям).
- Клик-зоны регионов → справочники (как острова Эстейта).
