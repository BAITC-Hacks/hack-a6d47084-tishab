# React frontend

Операционный интерфейс для просмотра прогнозов, uncertainty, weather vintage, knowledge boundary, provenance, agent activity, lineage, истории и результатов backtest.

Frontend общается только с FastAPI и не содержит forecasting, leakage, revision или metrics business logic.

## Запуск

```bash
cd frontend
copy .env.example .env
npm install
npm run dev
```

Приложение: `http://localhost:5173`. Backend URL задаётся через `VITE_API_URL`; внутри React-компонентов адрес не хардкодится.

## Проверка сборки

```bash
npm run build
```

Интерфейс поддерживает loading, empty, failed и partial-unavailable состояния. Список моделей строится динамически по `model_predictions`, поэтому optional TFT/ensemble отображаются только при наличии в API.
