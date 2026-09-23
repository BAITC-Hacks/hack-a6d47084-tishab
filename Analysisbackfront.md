# Анализ Backend и Frontend

> Локальный handoff-документ для команды. Актуализирован по текущему рабочему дереву после frontend-редизайна. Базовая ветка — `main`; незакоммиченные UI-изменения также учтены. Файл намеренно не добавляется в Git.

## 1. Краткий вывод

Проект уже имеет рабочую web-оболочку:

- FastAPI запускается и публикует Swagger;
- React/Vite запускается и собирается;
- frontend общается только с FastAPI;
- результаты сохраняются в SQLite;
- mock providers покрывают happy path, baselines, revision, leakage, LLM-off и optional models;
- UI показывает forecast, uncertainty, models, weather metadata, knowledge boundary, provenance, agent activity и lineage;
- UI имеет тёмную и светлую темы с сохранением выбора в `localStorage`;
- Dashboard содержит адаптивную SVG-сцену ВЭС с вращающимися вокруг собственных осей роторами и анимированным ветром;
- header получает provider mode из `/api/health` и показывает offline state, когда FastAPI недоступен;
- 8 backend-тестов проходят;
- frontend production build проходит.

Текущий уровень готовности: **рабочий integration/UI PoC на mock-данных**. Это ещё не готовая прогнозная система, потому что `RealWeatherProvider`, `RealForecastProvider` и `RealAgentProvider` остаются заглушками.

Главные технические риски перед подключением реальных модулей:

1. Frontend может сдвинуть historical issue time из-за локального часового пояса браузера.
2. SQLite может вернуть сохранённые timestamps без timezone offset.
3. Lineage/revision сейчас является вложенным mock-объектом, а не настоящей связью между запусками.
4. Backtest UI не строит `Actual vs Forecast`, даже если backend передаст series.
5. Network error отображается как техническое `Failed to fetch`; для жюри желательно заменить его на прикладную инструкцию о запуске API.

Важно: сценарий `D · Leakage rejected` намеренно возвращает `status=rejected` и `integrity_status=failed`. Это не сбой приложения. Mock weather сообщает данные, доступные позже issue time, после чего knowledge boundary и Agent блокируют публикацию. Во frontend этот штатный safety outcome теперь подписан как `BLOCKED` и сопровождается поясняющим banner.

## 2. Текущая архитектура

```text
React / Vite
    │
    │ REST JSON
    ▼
FastAPI routers
    │
    ▼
ForecastService / BacktestService
    │
    ├── WeatherProvider
    ├── ForecastProvider
    └── AgentProvider
    │
    ▼
ForecastRepository → SQLAlchemy → SQLite
```

Граница ответственности проведена правильно:

- React не импортирует Python/ML-код;
- API не обучает модель и не рассчитывает forecast;
- knowledge-boundary verdict должен приходить от weather/data module;
- Agent не создаёт численные прогнозы;
- `model_predictions` остаётся динамическим словарём.

## 3. Backend

### 3.1. Структура

```text
backend/app/
├── main.py                 FastAPI app, lifespan, CORS, routers
├── config.py               environment settings
├── dependencies.py         FastAPI dependency graph
├── api/                    HTTP routes
├── schemas/                Pydantic public contracts
├── services/               application orchestration
├── integrations/           provider abstractions and adapters
└── db/                     SQLAlchemy models and repository
```

Структура подходит для дальнейшей интеграции. Scientific logic не смешана с HTTP layer.

### 3.2. Request flow

`POST /api/forecasts/run` выполняет следующий flow:

```text
ForecastRequest
    ↓
WeatherProvider.get_weather_context(...)
    ↓
ForecastProvider.run_forecast(...)
    ↓
AgentProvider.process(...)
    ↓
ForecastService формирует provenance
    ↓
ForecastRepository сохраняет run, points и events
    ↓
ForecastDetail возвращается frontend
```

Плюс: agent failure типа `ProviderUnavailableError` не уничтожает numerical forecast — backend возвращает deterministic fallback.

Минус: Weather и Forecast providers вызываются последовательно. Если реальные вызовы будут сетевыми или тяжёлыми, синхронные endpoints могут блокировать worker.

### 3.3. API endpoints

| Метод | Endpoint | Реальный статус |
| --- | --- | --- |
| GET | `/` | работает |
| GET | `/api/health` | работает, показывает config mode |
| POST | `/api/forecasts/run` | работает с mock providers |
| GET | `/api/forecasts` | работает, без pagination |
| GET | `/api/forecasts/{id}` | работает |
| GET | `/api/forecasts/{id}/lineage` | работает |
| GET | `/api/forecasts/{id}/weather` | работает |
| GET | `/api/forecasts/{id}/agent` | работает |
| GET | `/api/forecasts/{id}/events` | работает |
| GET | `/api/backtests/latest` | возвращает N/A placeholder, если данных нет |

Отсутствуют:

- endpoint для recompute;
- endpoint для publish/shadow/reject revision;
- endpoint загрузки настоящего backtest результата;
- pagination/filtering истории;
- readiness check, реально проверяющий SQLite и provider modules.

### 3.4. Pydantic contracts

Сильные стороны:

- `extra="forbid"` защищает public schemas от случайных полей;
- `ForecastRequest` требует timezone-aware `issue_time`;
- horizon ограничен значениями 24/48;
- P10/P50/P90 ограничены диапазоном 0–2;
- model list и `model_predictions` динамические;
- weather optional fields поддерживают `null`;
- agent response структурирован;
- mock scenario является enum.

Что требуется усилить:

- добавить validator `p10 <= p50 <= p90` на уровне schema, сейчас это проверяет только mock test;
- явно решить единицы PLANT forecast: normalized single-turbine, сумма T1+T2 или normalized plant power;
- добавить timezone validation не только request, но и все timestamps providers;
- определить допустимые значения `AgentResult.status/decision` через enum;
- определить контракт для provider metadata/version compatibility;
- решить, должен ли `scenario` быть частью production public request или отдельным demo endpoint/config.

### 3.5. Provider layer

Интерфейсы:

```python
WeatherProvider.get_weather_context(issue_time, horizon_hours, scenario)
ForecastProvider.run_forecast(issue_time, horizon_hours, scenario)
AgentProvider.process(forecast, weather, scenario)
```

Это хорошая точка подключения модулей команды. Замена mock → real не требует изменения frontend.

Состояние:

- `MockWeatherProvider` — реализован;
- `MockForecastProvider` — реализован;
- `MockAgentProvider` — реализован;
- все `Real*Provider` — stubs, выбрасывающие `ProviderUnavailableError`.

Рекомендация интеграторам: не переносить ML/weather logic в `services/`. `real.py` должен только вызвать team module и выполнить mapping результата в существующую Pydantic schema.

### 3.6. Mock scenarios

| Scenario | Что проверяет |
| --- | --- |
| `normal` | обычный forecast и PASS |
| `baselines` | динамический набор моделей |
| `revision` | mock V1 → V2 |
| `leakage` | failed boundary и rejected status |
| `agent_off` | forecast без Agent |
| `optional_models` | появление TFT/ensemble |

Mock значения детерминированы и явно маркируются `is_mock`. Это хорошо для демонстрации и frontend-разработки.

### 3.7. Persistence

SQLite хранит:

- `forecast_runs`;
- `forecast_points`;
- `agent_events`;
- `backtest_results`.

Часть структур хранится нормализованно (`ForecastPoint`, `AgentEvent`), часть — JSON внутри `ForecastRun` (`weather`, `boundary`, `provenance`, `models`, `lineage`, `revision`, `agent`). Для PoC это приемлемо.

Риски:

1. **Timezone:** SQLite не сохраняет timezone semantics так же надёжно, как PostgreSQL. После round-trip `DateTime(timezone=True)` может стать naive datetime. Для vintage-aware проекта это критично.
2. **Нет migrations:** используется `Base.metadata.create_all()`. Изменение DB schema потребует удаления локальной БД или ручной миграции.
3. **Lineage не нормализован:** версии хранятся JSON-массивом внутри одного run, а не отдельными связанными forecast records.
4. **Нет rollback handling:** ошибка во время `commit()` не обрабатывается явным `rollback()`.
5. **Нет уникальных ограничений:** отсутствует защита от дублирования `(forecast_id, turbine_id, forecast_time)`.
6. **Большой JSON:** полный hourly weather сохраняется внутри одной строки `forecast_runs`; для многих replay runs БД быстро вырастет.
7. **Нет pagination:** история загружается целиком.

Рекомендуемый минимальный шаг: хранить все timestamps как UTC ISO 8601 либо реализовать единый SQLAlchemy UTC type, добавить Alembic и отдельную таблицу version relationships.

### 3.8. Backend error handling

Сейчас API специально обрабатывает:

- `ProviderUnavailableError` → 503;
- отсутствующий forecast → 404;
- Pydantic validation → стандартный 422.

Не обработаны отдельными ответами:

- DB unavailable/locked;
- unexpected provider payload;
- provider timeout;
- partial weather unavailable;
- forecast computation failure после успешной weather операции;
- idempotent retry одного request.

Для demo этого достаточно, для реальной интеграции нужен единый exception mapping и correlation/run ID в logs.

### 3.9. Backend tests

Сейчас 8 тестов проверяют:

- health и Swagger;
- forecast schema;
- dynamic models;
- knowledge boundary;
- lineage;
- provider factory;
- agent-off fallback;
- rejected leakage serialization.

Не покрыто:

- invalid horizon и naive datetime;
- 404 endpoints;
- real provider 503;
- restart/persistence round-trip;
- timezone preservation;
- CORS;
- DB locked/error rollback;
- backtest repository;
- concurrent forecast runs;
- pagination;
- Docker startup.

## 4. Frontend

### 4.1. Структура

```text
frontend/src/
├── App.jsx                router and shell
├── pages/
│   ├── Dashboard.jsx
│   ├── ForecastDetails.jsx
│   ├── History.jsx
│   └── Backtest.jsx
├── components/            forecast/weather/agent/provenance UI
├── hooks/                 data hooks
├── services/api.js        single FastAPI client
└── styles.css             responsive design
```

Frontend действительно не содержит ML, leakage или revision algorithms.

### 4.2. Navigation

Роуты:

- `/` — Dashboard;
- `/forecasts/:id` — Forecast Details;
- `/history` — History;
- `/backtest` — Backtest.

Используется `BrowserRouter`. На Vite dev server refresh работает. При deployment статический hosting должен быть настроен на SPA fallback к `index.html`, иначе прямое открытие `/forecasts/:id` может вернуть 404.

### 4.3. API client

`services/api.js` централизует base URL и endpoints. Это правильно: компоненты не хардкодят backend URL.

Плюсы:

- `VITE_API_URL` поддерживается;
- ошибки HTTP преобразуются в понятный message;
- все API calls собраны в одном месте.
- `App.jsx` использует `health()` для статуса системы и определения `Mock grid`/`Hybrid grid`.

Пробелы:

- нет timeout/AbortController;
- нет отмены request при unmount;
- нет retry policy;
- нет correlation ID;
- отсутствует дружелюбное преобразование браузерного `Failed to fetch` в инструкцию о запуске backend;
- health запрашивается один раз при mount, без периодического повторного опроса и recovery-индикации.

### 4.4. Dashboard flow

Dashboard:

1. загружает историю;
2. выбирает последний forecast;
3. позволяет создать новый mock run;
4. отображает общий `ForecastWorkspace`.

Главный риск — `datetime-local`:

```javascript
new Date(issueTime).toISOString()
```

`datetime-local` не содержит timezone. Браузер считает введённое значение локальным временем компьютера и переводит его в UTC. Например, пользователь в UTC+5 вводит `2026-02-10 06:00`, а backend получает `2026-02-10T01:00:00Z`.

Для historical replay это P0-баг. Варианты исправления:

- явно подписать input как UTC и самостоятельно дописывать `Z` без local conversion;
- использовать библиотеку timezone handling;
- передавать выбранный timezone отдельным полем;
- показывать пользователю итоговый ISO timestamp до запуска.

### 4.5. Forecast visualization

Реализовано:

- выбор `PLANT`, `T1`, `T2` на основе данных provider;
- P10/P50/P90 chart;
- dynamic model lines;
- Forecast Receipt;
- Knowledge Boundary;
- Weather Panel;
- Agent Timeline;
- Revision Timeline;
- Provenance Panel.

Сильная сторона: UI не хардкодит обязательный набор моделей. Ключи берутся из `model_predictions`.

Риски и пробелы:

- rejected forecast показывает численные точки только как `Blocked diagnostic output`; сверху выводится banner, поясняющий, что publication была остановлена safety rule;
- knowledge-boundary и receipt используют метку `BLOCKED` вместо неоднозначного `FAILED` для штатного leakage demo;
- uncertainty band реализован наложением двух Area, а не настоящим range band;
- нет unit label для power axis;
- `Plant` зависит от того, что provider пришлёт отдельные PLANT points; frontend ничего не агрегирует, что правильно, но контракт нужно закрепить;
- `AgentResult.warnings` не выводятся;
- `AgentResult.decision` не показан отдельным полем;
- Weather Panel показывает только первый час, а не weather timeline;
- Forecast Receipt использует поле `forecast_available_time` для weather availability, название может путать интеграторов.

### 4.6. История

History показывает основные поля и открывает detail page.

Недостатки:

- `useForecast()` на History дополнительно загружает полный latest forecast, хотя странице нужна только история;
- нет pagination/filter/search;
- timestamps отображаются в локальном timezone через `toLocaleString()` без явного UTC label;
- при сотнях replay runs таблица и API станут тяжёлыми.

### 4.7. Backtest

Таблица корректно показывает `N/A`, если metrics отсутствуют, и не придумывает значения.

Функциональный пробел: schema содержит `series`, но UI не строит `Actual vs Forecast`, когда series реально придёт. Сейчас код отображает empty-state только при пустом series, а при непустом series график тоже отсутствует.

### 4.8. Mode/status UX

Header вызывает `/api/health` при старте и показывает:

- `Mock grid`, если все три provider работают в mock mode;
- `Hybrid grid`, если хотя бы один provider отличается от mock;
- `Offline`, если FastAPI недоступен.

Ограничения текущего состояния:

- health не опрашивается повторно, поэтому восстановление backend требует reload страницы;
- hybrid mode не показывает, какой именно provider является real/mock;
- scenario selector пока остаётся доступным в hybrid/real mode;
- при network error пользователь видит исходное `Failed to fetch`.

### 4.9. Темы и анимированная сцена ВЭС

Реализованы две темы:

- тёмная диспетчерская с cyan/violet акцентами;
- светлая бело-голубая с жёлтыми акцентами.

Выбор сохраняется в `localStorage` под ключом `windline-theme`. Графики используют CSS variables, поэтому tooltip, grid, labels и uncertainty colors переключаются вместе с темой.

`WindFarmScene.jsx` содержит code-native SVG без внешних изображений. Три ротора вращаются через SVG `animateTransform` строго вокруг локальной ступицы `(0, 0)`. Потоки ветра, aurora и ground trace анимируются CSS. Телеметрия `Wind field / Farm state` объединена в одну внутреннюю строку; длинная border-линия заменена гибким разделителем, чтобы не выходить за органический контур сцены.

### 4.10. Frontend code hygiene

Неиспользуемые элементы:

- `ConfidenceBadge` создан, но не используется;
- `useAgentEvents` создан, но страницы используют events из полного `ForecastDetail`;
- отдельные API methods weather/agent/events/lineage почти не используются, потому что UI получает монолитный detail response.

Нужно решить одну стратегию:

- либо оставить полный aggregate endpoint и удалить лишние hooks/calls;
- либо загружать независимые panels отдельными endpoints и поддерживать partial failure.

Для заявленного partial-unavailable UX второй вариант архитектурно сильнее.

### 4.11. Frontend quality

Плюсы:

- responsive layout;
- две согласованные темы;
- анимированная ВЭС с `prefers-reduced-motion` fallback для CSS-анимаций;
- loading/error/empty states;
- динамические модели;
- нет ML business logic;
- production build проходит.

Риски:

- нет frontend tests;
- нет ESLint/formatter scripts;
- зависимости записаны как `latest`;
- есть `pnpm-lock.yaml`, но package-manager не закреплён;
- bundle около 660 kB, Vite предупреждает о chunk >500 kB;
- Google Fonts загружаются из внешней сети;
- нет React Error Boundary;
- accessibility не проверена автоматически;
- для production BrowserRouter потребуется hosting rewrite.

## 5. Сквозные контракты для коллег

### 5.1. Weather/Data team → Backend

Команда должна вернуть:

- source/run identifiers;
- run time и available time в UTC;
- hourly optional weather values;
- готовый `KnowledgeBoundary` verdict;
- `future_information_used`;
- причину failed status.

Backend не должен самостоятельно выводить legality из timestamps.

### 5.2. Forecasting team → Backend

На каждый point требуются:

- timezone-aware `forecast_time`;
- `lead_hours`;
- `turbine_id`;
- `p10`, `p50`, `p90`;
- произвольный `model_predictions` dictionary.

Также нужны:

- model descriptors;
- model/feature versions;
- status;
- lineage/revision result, если core его поддерживает.

Нужно заранее договориться о contract для `PLANT`: provider должен возвращать PLANT самостоятельно либо UI не покажет plant series.

### 5.3. Agent team → Backend

Agent должен возвращать структурированный объект:

- status;
- summary;
- decision;
- warnings;
- operator message;
- timestamped activity.

Agent не должен изменять numerical points и не должен быть обязательным для показа forecast.

### 5.4. Backend → Frontend

Публичные Pydantic schemas уже являются контрактом. Любые изменения названий полей должны проходить через согласованную API versioning strategy, иначе UI сломается.

## 6. Приоритеты исправлений

### P0 — до реального historical replay

| Задача | Владелец |
| --- | --- |
| Исправить UTC semantics `datetime-local` | Frontend |
| Гарантировать UTC timezone после SQLite round-trip | Backend |
| Реализовать и проверить RealWeatherProvider | Weather + Backend |
| Реализовать RealForecastProvider | ML + Backend |
| Зафиксировать semantics PLANT и power units | ML + Backend + Frontend |
| Не публиковать failed boundary как обычный forecast | Backend + Frontend |
| Добавить end-to-end test с реальным fixture contract | Все интеграторы |

### P1 — до демонстрации жюри

| Задача | Владелец |
| --- | --- |
| Добавить polling/recovery для health и детализацию hybrid provider mode | Frontend |
| Заменить raw `Failed to fetch` на понятную offline-инструкцию | Frontend |
| Отобразить Agent decision/warnings | Frontend |
| Actual vs Forecast graph | Frontend |
| Реальная lineage model или честно ограничить demo | Backend |
| Pagination истории | Backend + Frontend |
| Alembic migrations | Backend |
| Provider timeout и structured errors | Backend |
| Tests на timezone, 404, 503, persistence | Backend |
| Минимальные component/e2e tests | Frontend |

### P2 — после работающего end-to-end

- code splitting для Recharts/routes;
- offline/local fonts;
- lint/format pipeline;
- CI clean-machine check;
- accessibility audit;
- structured logging и correlation IDs;
- Docker Compose только если он реально понадобится для demo.

## 7. Что уже можно демонстрировать

Сейчас безопасно показывать:

- UI architecture;
- dark/light theme и анимированную ВЭС;
- mock forecast 24/48h;
- uncertainty rendering;
- dynamic model list;
- leakage rejected scenario;
- LLM-off fallback;
- provenance receipt;
- mock revision lineage;
- history persistence;
- Swagger contracts.

Нельзя представлять как готовое:

- реальную погоду;
- реальный LightGBM;
- реальные P10/P50/P90;
- настоящую ECMWF vintage legality;
- реальные backtest metrics;
- настоящий LLM Supervisor;
- рабочий recompute/revision algorithm.

## 8. Рекомендованный интеграционный порядок

1. Исправить UTC input и SQLite timezone round-trip.
2. Получить один зафиксированный WeatherContext fixture от weather/data команды.
3. Подключить `RealWeatherProvider` к fixture без сетевых вызовов.
4. Получить один ForecastProviderResult fixture от ML-команды.
5. Подключить `RealForecastProvider` и проверить full UI.
6. Согласовать PLANT semantics и model names.
7. Подключить реальные backtest results.
8. Подключить Agent последним: numerical pipeline должен работать при LLM OFF.
9. Только после этого реализовать recompute/publish flow и настоящую lineage persistence.

## 9. Итоговая оценка

Backend и frontend хорошо разделены и уже дают понятную основу для командной интеграции. Главная ценность текущей реализации — стабильные публичные schemas, provider boundaries и полноценный mock UI. Основной технический долг находится не в визуальной части, а на границах времени, persistence и real-module contracts.

Если команда сначала исправит UTC/timezone вопросы и подключит по одному реальному fixture через каждый adapter, текущую оболочку можно сохранить без архитектурной переделки.
