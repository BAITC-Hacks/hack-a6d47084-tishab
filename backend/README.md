# FastAPI backend

Единая web-точка интеграции weather, forecasting и agent-модулей команды. Backend не содержит ML, выбор погодного vintage или LLM reasoning: он вызывает провайдеры, проверяет публичные Pydantic-контракты и хранит application-level результаты в SQLite.

## Запуск

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/api/health`

Настройки перечислены в `.env.example`. По умолчанию включены только mock-провайдеры.

## Провайдеры

- `ForecastProvider.run_forecast(issue_time, horizon_hours, scenario)` — принимает уже вычисленный forecast от модуля команды.
- `WeatherProvider.get_weather_context(issue_time, horizon_hours, scenario)` — принимает weather context и готовый knowledge-boundary verdict.
- `AgentProvider.process(forecast, weather, scenario)` — принимает структурированную интерпретацию; не генерирует числа мощности.

`real.py` в каждом integration-каталоге — явная точка подключения командного модуля. До интеграции он отвечает ошибкой unavailable, а не подменяет результат mock-значениями.

## Тесты

```bash
cd backend
pytest -q
```

Покрыты health, схема прогноза, knowledge boundary, lineage, выбор провайдеров, agent-off, динамические optional models и rejected forecast.
