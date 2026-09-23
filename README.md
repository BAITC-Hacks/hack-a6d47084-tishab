# Agentic AI for Vintage-Aware Wind Power Forecasting

## Overview

PoC web-системы для просмотра почасового прогноза нормализованной выработки двух ветровых турбин на горизонте 24–48 часов. Web-слой объединяет weather, forecasting и agent-модули через стабильные интерфейсы и показывает uncertainty, provenance, knowledge boundary и историю версий.

> Forecast the future. Prove what information you used. Validate the result. Recompute when the evidence changes.

Сейчас FastAPI и React полностью работают с явно обозначенными mock-данными. Реальные weather, ML и LLM-модули ещё не подключены; mock-результаты нельзя считать benchmark-метриками.

## Windows Quick Start

Перед началом установите Git, Python 3.12 и Node.js LTS версии 22.12+ или более новой. Команды ниже не требуют активации Python virtual environment и поэтому работают при строгой PowerShell ExecutionPolicy.

```powershell
git clone https://github.com/BAITC-Hacks/hack-a6d47084-tishab.git
cd hack-a6d47084-tishab

# Backend
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Оставьте backend запущенным и откройте второй PowerShell:

```powershell
cd path\to\hack-a6d47084-tishab\frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Откройте:

- Dashboard: `http://localhost:5173`
- Swagger: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/api/health`

## Prerequisites

| Инструмент | Рекомендация | Проверка |
| --- | --- | --- |
| Git | актуальный Git for Windows | `git --version` |
| Python | 3.12 recommended | `py -3.12 --version` |
| Node.js | LTS 22.12+ или более новая LTS | `node --version` |
| npm | устанавливается вместе с Node.js | `npm --version` |

Backend проверен на Python 3.12. Frontend использует Vite 8, его фактическое ограничение — Node `^20.19.0` или `>=22.12.0`; production build также проверен на Node 24.19.0. Python 3.13 не выбран рекомендуемой версией, чтобы будущие ML-зависимости команды подключались с меньшим риском несовместимости.

## Windows Setup

### 1. Git

Проверьте Git:

```powershell
git --version
```

Если команда не найдена, установите [Git for Windows](https://git-scm.com/download/win) или выполните:

```powershell
winget install Git.Git
```

Закройте и заново откройте PowerShell, затем снова выполните `git --version`.

### 2. Clone

```powershell
git clone https://github.com/BAITC-Hacks/hack-a6d47084-tishab.git
cd hack-a6d47084-tishab
git status
```

После чистого clone ожидается ветка `main` без локальных изменений.

### 3. Python

Проверьте доступные команды и PATH:

```powershell
python --version
py --version
where.exe python
where.exe py
```

На Windows предпочтителен Python Launcher `py`. Если `python` открывает Microsoft Store или ведёт на Windows Store alias, используйте `py` либо отключите alias в Windows Settings → App execution aliases.

Если Python отсутствует, установите [Python 3.12 с python.org](https://www.python.org/downloads/windows/) или:

```powershell
winget install Python.Python.3.12
```

Откройте новый PowerShell и проверьте:

```powershell
py -3.12 --version
```

### 4. Backend virtual environment

Из корня репозитория:

```powershell
cd backend
py -3.12 -m venv .venv
Get-ChildItem .venv\Scripts
```

В `.venv\Scripts` должны присутствовать `python.exe`, `pip.exe`, `Activate.ps1` и `activate.bat`.

#### PowerShell ExecutionPolicy

Активация окружения необязательна. Самый надёжный вариант — напрямую вызывать Python из `.venv`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Если нужна активация и PowerShell выдаёт `PSSecurityException` или `execution of scripts is disabled`, разрешите скрипты только для текущего процесса:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

`-Scope Process` действует только в текущем PowerShell и не меняет постоянную системную политику. Команда `.venv\Scripts\activate` не является корректной командой PowerShell: используйте `Activate.ps1` с префиксом `.\`.

### 5. Backend dependencies

Без активации:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

При активированном окружении:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`uvicorn` устанавливается из `backend/requirements.txt`; до установки зависимостей команда запуска недоступна.

### 6. Backend environment

```powershell
Copy-Item .env.example .env
Get-Content .env
```

Фактическая mock-конфигурация:

```env
APP_NAME=Vintage-Aware Wind Forecast API
APP_ENV=development
DATABASE_URL=sqlite:///./wind_forecasts.db
CORS_ORIGINS=["http://localhost:5173"]
FORECAST_PROVIDER=mock
WEATHER_PROVIDER=mock
AGENT_PROVIDER=mock
```

### 7. Backend startup

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Uvicorn по умолчанию слушает `127.0.0.1:8000`. При активированном venv эквивалентная команда:

```powershell
python -m uvicorn app.main:app --reload
```

### 8. Backend verification

Проверьте в браузере или PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

- Root: `http://127.0.0.1:8000/`
- Swagger: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/api/health`

### 9. Port 8000 troubleshooting

При `WinError 10013`, access denied или занятом порте:

```powershell
netstat -ano | findstr :8000
Get-Process -Id <PID>
```

Останавливайте процесс только если убедились, что он принадлежит вашему предыдущему запуску:

```powershell
Stop-Process -Id <PID>
```

Или запустите backend на 8001:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

Проверка зарезервированных Windows диапазонов:

```powershell
netsh interface ipv4 show excludedportrange protocol=tcp
```

Для порта 8001 Swagger и health будут доступны по `http://127.0.0.1:8001/docs` и `http://127.0.0.1:8001/api/health`. Обязательно обновите `frontend/.env`: `VITE_API_URL=http://127.0.0.1:8001`.

### 10. Backend tests

Из каталога `backend`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Тесты проверяют health и Swagger, forecast schemas, dynamic model fields, knowledge boundary, rejected leakage run, lineage, provider selection и LLM-off fallback.

### 11. Node.js and npm

До установки frontend dependencies проверьте:

```powershell
node --version
npm --version
where.exe node
where.exe npm
```

Если Node.js или npm отсутствуют, установите [Node.js LTS](https://nodejs.org/) или:

```powershell
winget install OpenJS.NodeJS.LTS
```

Полностью закройте терминал и откройте новый, чтобы обновился PATH. Затем повторите `node --version` и `npm --version`.

### 12. Frontend setup and startup

Из корня проекта:

```powershell
cd frontend
Copy-Item .env.example .env
Get-Content .env
npm install
npm run dev
```

Откройте `http://localhost:5173`. Vite настроен на порт 5173.

Репозиторий содержит `pnpm-lock.yaml`, но не содержит `package-lock.json`, поэтому инструкция для npm использует `npm install`, а не `npm ci`. Если команда использует pnpm, можно выполнить `pnpm install --frozen-lockfile` и `pnpm run dev`.

`frontend/.env` связывает React с FastAPI:

```env
VITE_API_URL=http://localhost:8000
```

Если backend работает на 8001, измените значение до запуска Vite:

```env
VITE_API_URL=http://127.0.0.1:8001
```

После изменения `.env` перезапустите `npm run dev`.

### 13. Frontend build check

```powershell
npm run build
```

Готовая production-сборка создаётся в `frontend/dist/` и исключена из Git.

## Linux/macOS Setup

Backend:

```bash
git clone https://github.com/BAITC-Hacks/hack-a6d47084-tishab.git
cd hack-a6d47084-tishab/backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload
```

В новом терминале:

```bash
cd hack-a6d47084-tishab/frontend
cp .env.example .env
npm install
npm run dev
```

## Demo Startup

Terminal 1:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Terminal 2:

```powershell
cd frontend
npm run dev
```

Откройте Dashboard `http://localhost:5173`, Swagger `http://127.0.0.1:8000/docs` и Health `http://127.0.0.1:8000/api/health`.

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

React обращается только к FastAPI. Web-слой не выбирает weather vintage, не рассчитывает P10/P50/P90, не обучает ML и не генерирует численный forecast через LLM.

## P0 Forecast Pipeline

```text
Historical issue time
        ↓
SCADA history
        ↓
ECMWF archived runs
        ↓
Vintage selection
        ↓
available_at <= issue_time
        ↓
Knowledge Boundary PASS
        ↓
Feature preparation
        ↓
LightGBM
        ↓
T1/T2 24–48h forecast
        ↓
Provenance
```

Этот scientific pipeline ещё не интегрирован. FastAPI принимает его будущий структурированный результат через adapters.

## Weather / Vintage Assumption

Для P0 replay команда рассматривает инженерное предположение:

```text
available_at = initialization_time + 7 hours
```

Это engineering replay assumption, а не подтверждённый timestamp публикации ECMWF. Его должен реализовать и подтвердить weather/data module; текущий FastAPI самостоятельно timestamp не вычисляет.

При issue time `06:00 UTC` запуск `00Z` с допущением `+7h` становится доступен только в `07:00 UTC`. Следовательно, `00Z` run не является legal в `06:00`, и внешний vintage selector должен выбрать более ранний доступный run.

## Project Structure

```text
hack-a6d47084-tishab/
├── ai/                     placeholder для team forecasting modules
├── backend/
│   ├── app/api/            FastAPI routes
│   ├── app/db/             SQLAlchemy models и repository
│   ├── app/integrations/   mock/real provider adapters
│   ├── app/schemas/        Pydantic API contracts
│   ├── app/services/       application orchestration
│   ├── tests/              backend tests
│   ├── .env.example
│   └── requirements.txt
├── data/                   неизменяемые исходные CSV
├── frontend/
│   ├── src/components/     forecast, weather, provenance, agent UI
│   ├── src/pages/          dashboard, history, backtest
│   ├── src/services/api.js FastAPI client
│   ├── .env.example
│   └── package.json
└── README.md
```

`ANALYSIS.md`, `docs/`, отдельные `models/`, `outputs/` и processed-data каталоги в текущей `main` отсутствуют.

## Team Modules

| Зона | Ответственность |
| --- | --- |
| Weather/Data | SCADA, ECMWF retrieval, vintage selection, available-at и knowledge boundary |
| Forecasting | features, LightGBM, baselines, P10/P50/P90, validation |
| Agent | orchestration и human-readable interpretation; не numerical forecast |
| Backend | integration adapters, contracts, persistence и REST API |
| Frontend | navigation, API calls, visualization и error states |

## Interface Contracts

Фактические абстракции находятся в `backend/app/integrations/`:

```python
class WeatherProvider:
    def get_weather_context(self, issue_time, horizon_hours, scenario): ...

class ForecastProvider:
    def run_forecast(self, issue_time, horizon_hours, scenario): ...

class AgentProvider:
    def process(self, forecast, weather, scenario): ...
```

Параметр `scenario` используется mock-реализациями для демонстрационных состояний. Real adapters должны преобразовать результат командного модуля в существующие Pydantic schemas без изменения public API.

## Run Modes

### Mode A — Web development with mocks

```env
FORECAST_PROVIDER=mock
WEATHER_PROVIDER=mock
AGENT_PROVIDER=mock
```

Работает сейчас без внешних модулей. Все значения синтетические и помечены `MOCK MODE`.

### Mode B — Real forecasting integration

```env
FORECAST_PROVIDER=real
WEATHER_PROVIDER=real
AGENT_PROVIDER=mock
```

Требует реализации `RealForecastProvider` и `RealWeatherProvider`. Сейчас эти adapters отвечают `503 unavailable`.

### Mode C — Full integrated demo

```env
FORECAST_PROVIDER=real
WEATHER_PROVIDER=real
AGENT_PROVIDER=real
```

Требует подключения всех трёх team modules. Это ещё не реализовано.

## Mock Mode

| Scenario | Назначение |
| --- | --- |
| `normal` | P10/P50/P90 и boundary PASS |
| `baselines` | dynamic model list |
| `revision` | lineage V1 → V2 |
| `leakage` | boundary FAILED и rejected run |
| `agent_off` | forecast работает без Agent |
| `optional_models` | optional TFT/ensemble fields |

Mock output предназначен только для разработки API/UI. Его нельзя использовать как MAE, RMSE, coverage или реальный прогноз.

## Real Integration

Реализации находятся в:

- `backend/app/integrations/weather/real.py`
- `backend/app/integrations/forecast/real.py`
- `backend/app/integrations/agent/real.py`

После подключения кода команды переключите соответствующую переменную provider с `mock` на `real`. Frontend и публичные endpoints менять не требуется.

## API

| Method | Endpoint | Назначение |
| --- | --- | --- |
| GET | `/` | API name и ссылка на docs |
| GET | `/api/health` | Health и provider modes |
| POST | `/api/forecasts/run` | Запуск configured provider flow |
| GET | `/api/forecasts` | История forecast runs |
| GET | `/api/forecasts/{forecast_id}` | Полный forecast |
| GET | `/api/forecasts/{forecast_id}/lineage` | Version lineage |
| GET | `/api/forecasts/{forecast_id}/weather` | Weather context и boundary |
| GET | `/api/forecasts/{forecast_id}/agent` | Structured agent result |
| GET | `/api/forecasts/{forecast_id}/events` | Agent events |
| GET | `/api/backtests/latest` | Последний backtest или N/A placeholder |

Полные request/response schemas доступны в Swagger: `http://127.0.0.1:8000/docs`.

## Data and Outputs

| Данные | Фактическое расположение | Формат / статус |
| --- | --- | --- |
| Исходные турбины | `data/*.csv` | CSV; не изменять |
| Web persistence | `backend/wind_forecasts.db` при стандартном запуске | SQLite; generated, Git ignored |
| Forecast points | таблица `forecast_points` | SQLite + JSON model predictions |
| Provenance/weather/lineage | поля `forecast_runs` | SQLite JSON |
| Agent events | таблица `agent_events` | SQLite |
| Backtest results | таблица `backtest_results` | SQLite JSON; real results не подключены |
| Weather cache | `data/cache/` зарезервирован и Git ignored | Not implemented yet |
| Processed data | отдельный путь не определён | Not implemented yet |
| File-based forecast outputs | `outputs/` Git ignored | Not implemented yet |
| Отдельные agent logs | путь не определён | Not implemented yet |

Оригинальные CSV должны оставаться неизменными. Generated web state можно удалить вместе с локальным `backend/wind_forecasts.db`, если нужен чистый mock-demo запуск.

## Testing

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

Frontend:

```powershell
cd frontend
npm run build
```

На текущей реализации проверено: 8 backend tests pass; Vite production build completes. Vite предупреждает о JS chunk больше 500 kB, но сборку это не блокирует.

## Environment Variables

### Backend

| Variable | Meaning | Default в коде/example |
| --- | --- | --- |
| `APP_NAME` | Название FastAPI приложения | `Vintage-Aware Wind Forecast API` |
| `APP_ENV` | Маркер окружения | `development` |
| `DATABASE_URL` | SQLAlchemy connection URL | `sqlite:///./wind_forecasts.db` |
| `CORS_ORIGINS` | JSON-массив разрешённых frontend origins | `["http://localhost:5173"]` |
| `FORECAST_PROVIDER` | `mock` или `real` | `mock` |
| `WEATHER_PROVIDER` | `mock` или `real` | `mock` |
| `AGENT_PROVIDER` | `mock` или `real` | `mock` |

### Frontend

| Variable | Meaning | Default/example |
| --- | --- | --- |
| `VITE_API_URL` | Base URL FastAPI | `http://localhost:8000` |

`.env` загружается при старте процесса. После изменения backend `.env` перезапустите Uvicorn; после изменения frontend `.env` перезапустите Vite.

## Troubleshooting

### Python command not found

**Причина:** Python не установлен или не добавлен в PATH.

**Исправление:** установите Python 3.12, откройте новый PowerShell и используйте `py -3.12 --version`.

### `python` открывает Microsoft Store

**Причина:** Windows Store App Execution Alias.

**Исправление:** используйте `py`, либо отключите aliases `python.exe`/`python3.exe` в Windows Settings.

### `uvicorn` is not recognized

**Причина:** зависимости не установлены или используется глобальная команда вне venv.

**Исправление:**

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

### `Activate.ps1` blocked

**Причина:** PowerShell ExecutionPolicy.

**Исправление:** не активируйте venv и вызывайте `.\.venv\Scripts\python.exe` напрямую; либо используйте `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

### `WinError 10013` or port 8000 already used

**Причина:** порт занят или зарезервирован Windows.

**Исправление:** проверьте `netstat -ano | findstr :8000`, завершите только известный процесс либо запустите `--port 8001` и измените `VITE_API_URL`.

### `npm` is not recognized

**Причина:** Node.js/npm не установлены или отсутствуют в PATH.

**Исправление:** выполните `winget install OpenJS.NodeJS.LTS`, полностью перезапустите терминал, затем проверьте `where.exe node` и `where.exe npm`.

### Node установлен, но npm не виден

**Причина:** старый PowerShell ещё использует прежний PATH.

**Исправление:** закройте все терминалы, откройте новый. Если проблема остаётся, переустановите Node.js LTS с опцией добавления в PATH.

### Frontend cannot reach backend

**Причина:** backend не запущен, указан неверный порт или Vite использует старое `.env`.

**Исправление:** откройте `/api/health`, проверьте `frontend/.env`, затем перезапустите `npm run dev`.

### CORS error

**Причина:** frontend origin отсутствует в `CORS_ORIGINS`.

**Исправление:** используйте `http://localhost:5173` либо добавьте фактический origin в JSON-массив backend `.env`, например `["http://localhost:5173","http://127.0.0.1:5173"]`, и перезапустите backend.

### `.env` missing

**Причина:** example не был скопирован.

**Исправление:** выполните `Copy-Item .env.example .env` отдельно в `backend` и `frontend`.

### Mock provider selected unexpectedly

**Причина:** example по умолчанию использует `mock`.

**Исправление:** проверьте `/api/health` и backend `.env`. Переключайте на `real` только после реализации соответствующего real adapter.

### Real provider unavailable

**Причина:** текущие `Real*Provider` являются integration stubs.

**Исправление:** подключите командный модуль в соответствующем `real.py` или верните provider в `mock`.

### Tests cannot import `app`

**Причина:** pytest запущен не из `backend` или используется другой Python.

**Исправление:**

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

### `.venv` exists but its `python.exe` does not start

**Причина:** virtual environment был перемещён, создан несовместимым Python runtime либо повреждён синхронизацией/антивирусом.

**Исправление:** удалите только generated-каталог `backend/.venv`, создайте его заново официальным Python 3.12 и повторите установку. Не удаляйте исходники проекта:

```powershell
cd backend
Remove-Item -Recurse -Force .venv
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Health Check Checklist

- Backend health: `GET http://127.0.0.1:8000/api/health`
- Swagger: `http://127.0.0.1:8000/docs`
- Frontend: `http://localhost:5173`
- Backend tests: `.\.venv\Scripts\python.exe -m pytest -q`
- Frontend build: `npm run build`

## Clean-Machine Verification

- [ ] Clone выполнен в новую папку.
- [ ] Git, Python 3.12, Node.js и npm найдены в PATH.
- [ ] `backend/.venv` создан.
- [ ] Backend dependencies установлены.
- [ ] `backend/.env` создан из example.
- [ ] Backend запускается.
- [ ] Root, health и Swagger открываются.
- [ ] Backend tests проходят.
- [ ] `frontend/.env` создан из example.
- [ ] Frontend dependencies установлены.
- [ ] Frontend запускается и достигает backend.
- [ ] Mock scenario создаёт явно помеченный demo forecast.
- [ ] `npm run build` проходит.
- [ ] Real integration mode проверен только если real modules действительно подключены.

## Security

Никогда не коммитьте `.env` с API keys или другими секретами. `.gitignore` исключает `.env`, `.venv/`, `node_modules/`, `__pycache__/`, SQLite `.db`, build artifacts, outputs и cache. `.env.example` содержит только безопасные defaults и остаётся в Git.

## Git Workflow

```powershell
git status
git add README.md
git commit -m "docs: improve clean Windows setup"
git push
```

Сообщение `no changes added to commit` означает, что изменённые файлы не добавлены в staging area либо изменений нет. Повторно проверьте `git status`.

## Pre-Demo Checklist

- [ ] Backend tests pass.
- [ ] Frontend build passes.
- [ ] `.env` и secrets не staged.
- [ ] Mock results не описаны как реальные metrics.
- [ ] Backend и `VITE_API_URL` используют один порт.
- [ ] Swagger и health открываются.
- [ ] README-команды проверены в PowerShell.
- [ ] Исходные CSV не изменены.

## Current Status

### Implemented

- FastAPI REST API, Swagger и CORS config.
- Pydantic contracts и SQLite persistence.
- Forecast, Weather и Agent provider boundaries.
- Six mock scenarios.
- React dashboard, uncertainty и dynamic model comparison.
- Knowledge Boundary, Weather, Provenance и Forecast Receipt UI.
- Agent activity, LLM-off, history, lineage и backtest UI.
- Backend tests и frontend production build.

### Not yet integrated

- Real SCADA preprocessing.
- ECMWF/weather retrieval и verified vintage timestamps.
- Knowledge-boundary scientific implementation.
- Feature engineering, LightGBM и baselines.
- Real uncertainty/validation/revision logic.
- Real LLM Supervisor.
- Real backtest metrics и file-based outputs.

## Limitations

- Численные forecast/weather values сейчас синтетические mock fixtures.
- `real` providers пока возвращают unavailable.
- SQLite и локальный CORS рассчитаны на PoC, а не production deployment.
- Authentication и deployed-версия отсутствуют.
- npm clean install не зафиксирован `package-lock.json`; репозиторий содержит pnpm lockfile.
- Vite build проходит с предупреждением о JS chunk больше 500 kB.

## Future Work

1. Реализовать `RealWeatherProvider`, `RealForecastProvider`, `RealAgentProvider`.
2. Подтвердить ECMWF publication latency и заменить инженерное `+7h` реальными metadata.
3. Добавить реальные backtest results и outputs через существующие schemas.
4. Добавить integration fixtures и clean-machine CI.
5. Зафиксировать единый package-manager workflow для frontend.
