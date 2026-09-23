# Контракты данных между частями системы

> Версия **v1** (P0). Меняется только по договорённости владельцев.
> Владельцы: **M2 / Agent** — погода, данные, агент · **ML** — LightGBM · **App** — бэкенд + фронтенд.

---

## 0. Общие соглашения

| Правило | Значение |
|---|---|
| Время | Везде **UTC**, timezone-aware (`datetime64[ns, UTC]`). Локальное время только для отображения |
| Шаг | 1 час |
| Метка часа | **Начало часа.** Строка `forecast_time = 10:00` означает интервал `[10:00, 11:00)` |
| Идентификатор турбины | Строка `"T1"` / `"T2"` |
| Мощность | Нормализованная, `[0, 1]` |
| Формат файлов | Parquet (основной), CSV (для просмотра) |
| Пропуски | `NaN`, **никогда** не заменяются нулём |

---

## 1. Момент прогноза и горизонт

| Параметр | Значение | Обоснование |
|---|---|---|
| Основной `issue_time` | **ежедневно 07:00 UTC** (12:00 местного) | Запуск ECMWF 00Z становится законным ровно в 07:00 при допущении `init + 7h` |
| Горизонт | `forecast_time` = `issue_time + 1h … issue_time + 48h` (48 строк на турбину) | Покрывает требование ТЗ «24–48 часов» |
| Тестовый период | `issue_time` с 2026-01-31 07:00 по 2026-02-27 07:00 UTC | Протокол ТЗ |
| Ревизии (P1) | Дополнительные `issue_time` при появлении запусков 06Z / 12Z / 18Z | Compute ≠ Publish |

### Допущение о доступности погоды

```text
available_at = run_init_time + 7h        # ДОПУЩЕНИЕ, не проверенное время публикации
availability_basis = "assumed:init+7h"
```

| Запуск ECMWF | Считается доступным с |
|---|---|
| 00Z | 07:00 UTC |
| 06Z | 13:00 UTC |
| 12Z | 19:00 UTC |
| 18Z | 01:00 UTC следующего дня |

---

## 2. Weather-vintage таблица (M2 → ML)

**Файл:** `data/processed/weather_vintages.parquet`
**Гранулярность:** одна строка на `(issue_time, forecast_time, turbine_id)`.

| Колонка | Тип | Описание |
|---|---|---|
| `issue_time` | datetime UTC | Момент прогноза T |
| `forecast_time` | datetime UTC | Прогнозируемый час (начало часа) |
| `turbine_id` | str | `T1` / `T2` |
| `lead_time_h` | int | `forecast_time − issue_time` в часах, 1…48 |
| `weather_run_id` | str | Например `ecmwf_ifs:2026-01-31T00Z` |
| `run_init_time` | datetime UTC | Время инициализации запуска |
| `available_at` | datetime UTC | Допущенное время доступности |
| `availability_basis` | str | `assumed:init+7h` |
| `nwp_lead_h` | int | `forecast_time − run_init_time` в часах |
| `wind_speed_10m` | float, м/с | |
| `wind_speed_80m` | float, м/с | |
| `wind_speed_100m` | float, м/с | |
| `wind_speed_120m` | float, м/с | |
| `wind_direction_100m` | float, ° | 0–360 |
| `wind_gusts_10m` | float, м/с | **Может быть `NaN`** (первый час запуска) |
| `temperature_2m` | float, °C | |
| `surface_pressure` | float, гПа | |
| `relative_humidity_2m` | float, % | |

### Инварианты (проверяются M2 перед отдачей)

```python
assert (df.available_at <= df.issue_time).all()          # защита от утечки
assert df.lead_time_h.between(1, 48).all()
assert df.groupby(["issue_time", "turbine_id"]).size().eq(48).all()
assert not df.drop(columns=["wind_gusts_10m"]).isna().any().any()
```

### Замечания

- Обе турбины попадают в **одну ячейку сетки** ECMWF (43.620, 78.479), поэтому погодные колонки для T1 и T2 **идентичны**. Строки дублируются для удобства join.
- Признаки (sin/cos направления, плотность воздуха и т.п.) строит **ML**. M2 отдаёт только сырые переменные погоды.
- Та же таблица покрывает **обучение** (все `issue_time` с 2024-04-15 по 2026-01-31) и **тест** (февраль 2026).

---

## 3. SCADA hourly таблица (M2 → ML)

**Файл:** `data/processed/scada_hourly.parquet`
**Гранулярность:** одна строка на `(timestamp, turbine_id)`.

| Колонка | Тип | Описание |
|---|---|---|
| `timestamp` | datetime UTC | Начало часа |
| `turbine_id` | str | `T1` / `T2` |
| `power` | float | Среднее по 10-минутным записям часа |
| `wind_speed` | float, м/с | Среднее, анемометр гондолы |
| `temperature` | float, °C | Среднее |
| `n_samples` | int | Число 10-минутных записей в часе, 0…6 |
| `is_valid` | bool | `n_samples ≥ 4` и нет признаков остановки или ограничения |
| `flag` | str | `ok` / `low_coverage` / `possible_curtailment` / `stuck_sensor` |

### Правила

- Часовой пояс исходных данных определяет и документирует M2 (`A6`). В таблице всё уже в UTC.
- Часы без записей **присутствуют** в таблице с `n_samples = 0` и `power = NaN`.
- Для обучения ML берёт только `is_valid == True`.
- **Законные лаги:** для `issue_time = T` используются только строки с `timestamp + 1h ≤ T`, то есть час полностью завершён до T.

---

## 4. Прогноз (ML → Agent)

```python
predict(features_df: pd.DataFrame) -> pd.DataFrame
```

| Колонка | Тип | Версия |
|---|---|---|
| `forecast_time` | datetime UTC | v1 |
| `turbine_id` | str | v1 |
| `p50` | float `[0, 1]` | v1 |
| `model_version` | str, например `lgbm-v1` | v1 |
| `p10`, `p90` | float `[0, 1]` | v2, после работающего P50 end-to-end |

- Артефакт модели: `models/lgbm_v1.txt` + metadata; интерфейс `save()` / `load()`.
- Baselines: **ML** — Persistence, Climatology; **M2 / Agent** — Power Curve (он же заглушка `predict` до готовности LightGBM и проверка на физичность).

---

## 5. Выход агента (Agent → App)

**Каталог:** `outputs/`

| Файл | Содержимое |
|---|---|
| `outputs/forecasts.parquet` | Все версии прогнозов: колонки раздела 4 + `forecast_id`, `version`, `parent_forecast_id`, `issue_time`, `weather_run_id`, `status`, `decision`, `revision_reason` |
| `outputs/receipts/{forecast_id}.json` | «Чек» прогноза: issue_time, weather_run_id, run_init_time, available_at, availability_basis, model_version, результат проверки утечки, результаты валидации |
| `outputs/agent_log.jsonl` | Журнал шагов агента: `ts`, `issue_time`, `step`, `status`, `details` |
| `outputs/latest.json` | Последний запуск: для `/agent/status` |

Точная форма JSON для `/agent/status` согласуется с App (`D2`–`D4`).
