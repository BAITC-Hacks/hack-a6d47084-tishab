# Agentic AI for Vintage-Aware Wind Power Forecasting

PoC web-системы прогнозирования почасовой нормализованной выработки двух ветровых турбин на горизонте 24–48 часов.

> Forecast the future. Prove what information you used. Validate the result. Recompute when the evidence changes.

## Problem

Диспетчеру ВЭС нужен не только численный прогноз, но и доказательство того, что при историческом replay система использовала лишь информацию, действительно доступную в момент выпуска прогноза. Web-слой объединяет выводы weather/data, forecasting и agent-модулей в один проверяемый operational view.

## Hackathon Case

Исходные данные содержат 10-минутные измерения скорости ветра, нормализованной активной мощности и температуры двух турбин с 11.03.2023 по 31.01.2026. Закрытый тестовый период — февраль 2026.

## Architecture

```text
React Frontend
      ↓ HTTP
FastAPI Backend
      ↓
Application / Integration Layer
      ├── WeatherProvider  → team weather/data module
      ├── ForecastProvider → team forecasting/ML module
      └── AgentProvider    → team supervisor/LLM module
```

FastAPI — единственная точка доступа frontend. API не знает, как обучена модель, как выбран weather vintage и как устроен LLM. Провайдеры можно заменить без изменения React, публичных схем и структуры хранения.

## Core No-Leakage Principle

Научный модуль должен проверять условие `forecast_available_time <= issue_time`. Web-слой сам не принимает научное решение: он получает и сохраняет `knowledge_boundary` со статусом, признаком `future_information_used` и причиной. UI выделяет failed run как `FORECAST REJECTED`.

## Forecasting Architecture

Целевая P0-цепочка команды:

```text
SCADA + legal historical weather vintage
                ↓
        feature engineering
                ↓
             model
                ↓
          P10 / P50 / P90
                ↓
           validation
                ↓
        structured forecast
```

Эта цепочка не реализуется в FastAPI. Сейчас её контракт воспроизводит явно помеченный `MockForecastProvider`.

## P0 Models

Командная архитектура предусматривает LightGBM и baselines Persistence, Climatology и Power Curve. В текущем репозитории эти модели не реализованы и не интегрированы. Mock-сценарии используют их имена только для проверки динамического API/UI.

## Optional P1 Models

TFT, ensemble, bias correction и adaptive approaches необязательны. `model_predictions` — динамический объект, поэтому новые модели могут появиться без изменения публичного API и компонентов React.

## Uncertainty

Каждый `ForecastPoint` принимает готовые `p10`, `p50`, `p90` от forecasting provider. FastAPI и React не рассчитывают uncertainty; UI только отображает median forecast и диапазон.

## Agentic AI

`AgentProvider` возвращает структурированные `summary`, `decision`, `warnings`, `operator_message` и `activity`. LLM может интерпретировать состояние и координировать модули, но не генерирует numerical power forecast.

## LLM-Off Mode

Если agent недоступен, backend сохраняет численный forecast и возвращает `status: unavailable`, `fallback: deterministic`. Сценарий `agent_off` подтверждает, что интерфейс продолжает работать без LLM.

## Compute vs Publish

API поддерживает статусы `computed`, `shadow`, `published`, `superseded`, `rejected`, `failed`. Решение о recompute или publication приходит из внешнего core/agent-модуля; web-слой его не вычисляет.

## Forecast Versioning

Lineage хранится как версии одного forecast (`V1 → V2`) с `parent_version`, статусом, причиной revision и временем создания. Mock-сценарий `revision` показывает опубликованную V2 после superseded V1, но не имитирует реальный revision algorithm.

## Provenance

Forecast receipt содержит forecast ID/version, issue time/horizon, weather source/run/available time, model/version, feature version, future-information flag и integrity status. Все demo provenance явно помечены `is_mock: true` и баннером `MOCK MODE`.

## FastAPI Backend

Стек: Python, FastAPI, Pydantic, SQLAlchemy, SQLite. Backend состоит из API routers, application services, provider adapters и repository. SQLite хранит только web/application сущности:

- `ForecastRun` — статус, issue time, version, weather, boundary, provenance, lineage;
- `ForecastPoint` — turbine/time, P10/P50/P90, динамические model predictions;
- `AgentEvent` — структурированная activity timeline;
- `BacktestResult` — сериализованный результат внешнего evaluation module.

Обученные модели в SQLite не хранятся.

## React Frontend

Стек: React, Vite, JavaScript, Recharts и собственный CSS без конкурирующих UI-библиотек. Реализованы dashboard с historical replay, P10/P50/P90 для Plant/T1/T2, dynamic model comparison, weather и knowledge-boundary panels, receipt/provenance, agent activity, LLM-off fallback, lineage, history и backtest table.

## Interface Boundaries

### Weather/Data → Forecasting

Концептуальный контракт: `issue_time`, `forecast_time`, `turbine_id`, `weather_run_id`, wind values, direction, temperature, pressure и lead time. Не предоставленные поля остаются `null`.

### Forecasting → Backend

`forecast_time`, `lead_hours`, `turbine_id`, `p10`, `p50`, `p90`, `model_predictions`, model/version metadata и lineage. Backend не изменяет численные значения.

### Agent → Backend

Структурированные status, summary, decision, warnings, operator message и events. Сырой LLM-текст frontend не разбирает.

### Backend → Frontend

Стандартизованные forecast, weather, knowledge boundary, agent, provenance, lineage, revision и backtest resources.

## API

| Метод | Endpoint | Назначение |
| --- | --- | --- |
| GET | `/api/health` | Health и активные provider modes |
| POST | `/api/forecasts/run` | Запуск provider flow и сохранение результата |
| GET | `/api/forecasts` | История forecast runs |
| GET | `/api/forecasts/{forecast_id}` | Полный forecast |
| GET | `/api/forecasts/{forecast_id}/lineage` | Версии и publication history |
| GET | `/api/forecasts/{forecast_id}/weather` | Weather context и boundary verdict |
| GET | `/api/forecasts/{forecast_id}/agent` | Структурированный agent result |
| GET | `/api/forecasts/{forecast_id}/events` | Agent/application timeline |
| GET | `/api/backtests/latest` | Последний backtest или N/A placeholder |

Swagger: `http://localhost:8000/docs`.

## Mock Mode

По умолчанию установлены `FORECAST_PROVIDER=mock`, `WEATHER_PROVIDER=mock`, `AGENT_PROVIDER=mock`.

| Сценарий | Что проверяет |
| --- | --- |
| `normal` | P10/P50/P90 и boundary PASS |
| `baselines` | Dynamic Persistence, Power Curve, LightGBM names |
| `revision` | Lineage V1 → V2 |
| `leakage` | Boundary FAILED и rejected run |
| `agent_off` | Forecast работает при недоступном agent |
| `optional_models` | Optional TFT/ensemble без правок frontend |

Mock-значения синтетические и не являются benchmark results.

## Integration Guide

Реальные модули подключаются в `backend/app/integrations/*/real.py`:

```python
class ForecastProvider:
    def run_forecast(self, issue_time, horizon_hours, scenario): ...

class WeatherProvider:
    def get_weather_context(self, issue_time, horizon_hours, scenario): ...

class AgentProvider:
    def process(self, forecast, weather, scenario): ...
```

После реализации адаптеров переключите `.env` на `FORECAST_PROVIDER=real`, `WEATHER_PROVIDER=real`, `AGENT_PROVIDER=real`. До подключения real-адаптеры возвращают честный `503 unavailable`, а не fake forecast.

## Backtesting

Web layer не вычисляет MAE/RMSE/nMAE. Пока evaluation module не подключён, `/api/backtests/latest` возвращает `null` metrics, а UI показывает `N/A`. Реальные metrics и Actual vs Forecast должны прийти через `BacktestResult`.

## Running the Application

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env  # Windows; cp .env.example .env on Linux/macOS
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
copy .env.example .env  # Windows; cp .env.example .env on Linux/macOS
npm install
npm run dev
```

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

### Tests

```bash
cd backend && pytest -q
cd ../frontend && npm run build
```

## Project Structure

```text
ai/                    Team forecasting module boundary (not implemented here)
backend/
  app/api/             FastAPI endpoints
  app/schemas/         Public Pydantic contracts
  app/services/        Application orchestration
  app/integrations/    mock/real provider adapters
  app/db/              SQLAlchemy models and repository
  tests/               API and contract tests
frontend/
  src/components/      Forecast, provenance, weather, agent UI
  src/pages/           Dashboard, details, history, backtest
  src/services/api.js  Single FastAPI client
data/                  Original, unchanged turbine CSV files
```

## Current Implementation Status

### Implemented in Web Layer

- FastAPI REST API, Swagger, Pydantic contracts и SQLite persistence;
- Forecast, Weather и Agent provider boundaries;
- six explicit mock scenarios;
- React dashboard, forecast/uncertainty и dynamic model comparison;
- Knowledge Boundary, Weather, Provenance и Forecast Receipt UI;
- Agent Activity, LLM-off, history, lineage и backtest UI;
- backend tests и проверенная frontend production build.

### Provided / Integrated by Other Team Members

Ещё требуется подключить: SCADA preprocessing, weather retrieval, historical vintage selection, deterministic knowledge-boundary implementation, feature engineering, LightGBM, Power Curve, Persistence/Climatology, optional TFT/ensemble, uncertainty calculation, validation, revision decision logic и LLM Supervisor.

## Data

Оригинальные CSV остаются неизменными в `data/`:

| Турбина | Записей | Период | Пропуски 10-минутной сетки |
| --- | ---: | --- | ---: |
| T1 | 142 360 | 11.03.2023 — 31.01.2026 | 9 992 |
| T2 | 149 499 | 11.03.2023 — 31.01.2026 | 2 853 |

Планируемый внешний источник — Open-Meteo Previous Runs API; он пока не интегрирован. Ни frontend, ни mock backend не обращаются к внешней погоде.

## Limitations

- Все численные forecast/weather values сейчас синтетические demo fixtures.
- Реальные ML, weather и LLM modules не подключены.
- Scientific knowledge-boundary и revision algorithms не реализованы web-слоем.
- Backtest metrics и actual series отсутствуют и показываются как `N/A`.
- SQLite и локальный CORS рассчитаны на PoC, не production deployment.
- Authentication и deployed-версия отсутствуют.

## Future Work

1. Реализовать три `Real*Provider` поверх модулей команды.
2. Зафиксировать mapping реальных team outputs в Pydantic-схемы.
3. Подключить реальные backtest results без вычислений в UI.
4. Добавить integration tests с настоящими fixtures и проверить end-to-end replay.
5. После интеграции заменить mock screenshots/results на подтверждённые данные.
