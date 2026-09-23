# PoC: Agentic AI-система прогнозирования выработки ВЭС на 24–48 часов

## 1. Цель проекта

Цель проекта — разработать Proof of Concept автономной Agentic AI-системы для прогнозирования почасовой выработки ветроэлектростанции на горизонте 24–48 часов.

Система должна воспроизводить реальный сценарий эксплуатации: в каждый момент прогнозирования она использует только ту информацию, которая была доступна на этот момент времени, самостоятельно получает архивный прогноз погоды, выполняет подготовку данных, запускает несколько моделей прогнозирования, объединяет их результаты, анализирует качество полученного прогноза и при необходимости инициирует повторный расчёт.

Ключевая особенность PoC состоит в том, что LLM не используется непосредственно как модель численного прогнозирования мощности. Численный прогноз формируется специализированными ML/DL-моделями, а LLM выполняет роль интеллектуального Supervisor Agent, управляющего всем процессом прогнозирования.

Система строится как гибрид из:

* исторических данных ВЭС;
* архивных метеорологических прогнозов;
* ML-моделей;
* DL-модели;
* физически интерпретируемой модели кривой мощности;
* ансамблевого прогнозирования;
* механизма оценки неопределённости;
* LLM-агента;
* автоматической валидации результатов.

---

# 2. Исходные данные

В рамках PoC используются исторические данные двух ветровых турбин.

Для каждой турбины доступны:

* статистическое время;
* средняя скорость ветра;
* нормализованная активная мощность;
* средняя температура окружающей среды.

Исходные данные имеют временной шаг 10 минут и покрывают период с марта 2023 года по 31 января 2026 года. Февраль 2026 года используется как тестовый период и отсутствует в предоставленной исторической части.

В данных имеются пропуски временных интервалов, поэтому отсутствие записи не должно интерпретироваться как нулевая генерация. Особенно это важно для первой турбины, где доля пропусков существенно выше.

Две турбины находятся на одной площадке и характеризуются очень похожими условиями работы. Историческая корреляция скорости ветра между ними составляет около 0.99, а мощности — около 0.964. Это позволяет использовать общую метеорологическую модель и совместное обучение моделей с признаком `turbine_id`.

---

# 3. Основная идея PoC

PoC реализует следующий автономный цикл:

```text
Получение погодного прогноза
            ↓
Проверка качества данных
            ↓
Подготовка признаков
            ↓
Запуск ML/DL моделей
            ↓
Получение нескольких прогнозов
            ↓
Ансамблирование
            ↓
Оценка неопределённости
            ↓
Физическая и статистическая валидация
            ↓
LLM-анализ результата
            ↓
Сохранение прогноза / повторный расчёт
```

При появлении нового прогноза погоды или обнаружении проблем во входных данных система может автоматически повторить вычисления.

Таким образом, Agentic AI используется не как декоративный интерфейс над ML-моделью, а как управляющий слой всей системы.

---

# 4. Общая архитектура

```text
                         ┌────────────────────────┐
                         │     LLM Supervisor     │
                         │    Decision Agent      │
                         └───────────┬────────────┘
                                     │
                                LangGraph
                                     │
              ┌──────────────────────┼───────────────────────┐
              │                      │                       │
              ↓                      ↓                       ↓
      ┌──────────────┐       ┌──────────────┐       ┌──────────────┐
      │ Weather Tool │       │  Data Tool   │       │ Feature Tool │
      └──────┬───────┘       └──────┬───────┘       └──────┬───────┘
             │                      │                       │
             └──────────────────────┼───────────────────────┘
                                    ↓
                          Feature Engineering
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                  │
                 ↓                  ↓                  ↓
             LightGBM             TFT             Power Curve
                 │                  │                  │
                 └──────────────────┼──────────────────┘
                                    ↓
                              Ensemble Model
                                    ↓
                              P10 / P50 / P90
                                    ↓
                            Validation Agent
                                    ↓
                       ┌────────────┴────────────┐
                       │                         │
                      OK                      WARNING
                       │                         │
                       ↓                         ↓
                  Save forecast          Recompute/Fallback
                       │
                       ↓
                   LLM Report
```

---

# 5. Agentic AI слой

## 5.1. Supervisor Agent

Главным управляющим компонентом является LLM Supervisor.

LLM не получает задачу «предскажи мощность ВЭС».

Вместо этого он получает текущее состояние прогнозного процесса и набор строго определённых инструментов.

Пример состояния:

```python
{
    "issue_time": "2026-02-10T06:00",
    "horizon": 48,

    "weather_status": {},
    "weather_quality": {},

    "features_ready": False,

    "model_predictions": {},

    "ensemble_prediction": None,

    "confidence": None,

    "warnings": [],

    "decision_log": []
}
```

Supervisor анализирует состояние и определяет следующий шаг процесса.

---

# 6. Инструменты агента

Для PoC достаточно следующего набора tools:

```text
fetch_weather()
check_weather_quality()

load_scada_history()
prepare_features()

run_lightgbm()
run_tft()
run_power_curve()

build_ensemble()

estimate_uncertainty()

validate_forecast()

save_forecast()

generate_report()
```

Дополнительно может использоваться:

```text
recompute()
```

для повторного расчёта при изменении входных данных.

---

# 7. Weather Layer

Метеорологические прогнозы являются ключевым внешним источником данных.

Для каждого момента прогнозирования необходимо получать архивный weather forecast, который действительно был доступен в этот момент.

Например:

```text
issue_time:
31.01.2026 12:00

forecast horizon:
01.02.2026 00:00
...
02.02.2026 23:00
```

Нельзя использовать фактические погодные данные февраля, так как это приведёт к data leakage.

Исторический backtest должен имитировать ситуацию, как если бы система действительно работала в прошлом. Именно такое ограничение задано сценарием: на каждом шаге разрешается использовать только прогнозы, опубликованные к соответствующему моменту.

В качестве базового источника для PoC может использоваться Open-Meteo Previous Runs API, позволяющий получать предыдущие версии прогнозов. В предварительном анализе было установлено, что подходящие historical forecast данные присутствуют примерно с середины 2024 года.

---

# 8. Weather Features

Из прогноза погоды желательно использовать следующие признаки:

```text
wind_speed_10m
wind_speed_80m
wind_speed_100m
wind_speed_120m

wind_direction
wind_gusts

temperature
pressure
humidity
```

Направление ветра преобразуется:

```text
wind_direction_sin
wind_direction_cos
```

Дополнительно создаются временные признаки:

```text
hour_sin
hour_cos

day_of_year_sin
day_of_year_cos

month
lead_time
```

---

# 9. Подготовка данных

10-минутные измерения турбин агрегируются до почасового уровня.

Базовый preprocessing:

```text
raw 10-minute SCADA
        ↓
timestamp normalization
        ↓
timezone alignment
        ↓
data quality checks
        ↓
hourly aggregation
        ↓
feature generation
```

При этом:

* пропуски не заменяются автоматически нулями;
* большие временные разрывы исключаются;
* периоды возможных остановок помечаются отдельно;
* залипшие значения датчиков могут маркироваться как аномалии.

У данных присутствуют ситуации, когда при достаточно высокой скорости ветра мощность остаётся практически нулевой, что может соответствовать остановке или ограничению генерации. Такие наблюдения желательно отделять от нормальной аэродинамической зависимости.

---

# 10. Weather Bias Correction

Дополнительным компонентом PoC может стать модель коррекции прогноза ветра.

Метеорологическая модель прогнозирует ветер для определённой точки и высоты, однако фактическая скорость ветра на конкретной турбине может систематически отличаться.

Поэтому перед прогнозированием мощности используется:

```text
NWP forecast
      ↓
Weather Bias Corrector
      ↓
Corrected local wind
```

В качестве модели может использоваться LightGBM.

Пример входов:

```text
forecast wind 80m
forecast wind 100m
forecast wind 120m
temperature
direction
pressure
hour
month
lead_time
```

Target:

```text
actual turbine wind speed
```

На выходе получается оценка локального ветра непосредственно для площадки ВЭС.

Для PoC этот компонент может быть реализован после базового рабочего pipeline.

---

# 11. Модель №1 — LightGBM

LightGBM является основной ML-моделью.

Она получает:

```text
weather features
corrected wind

temperature
pressure
direction

hour
month

lead_time

turbine_id

recent power features
recent wind features
```

Target:

```text
normalized active power
```

LightGBM выбран как сильный baseline для табличных данных и основной надёжный forecasting component PoC.

---

# 12. Модель №2 — Temporal Fusion Transformer

В качестве Deep Learning компонента используется Temporal Fusion Transformer.

TFT получает две категории признаков.

## Исторические наблюдения

```text
power
wind speed
temperature
```

например за предыдущие:

```text
48–168 часов
```

## Будущие известные признаки

```text
forecast wind
forecast temperature
wind direction
pressure

hour
day
month

lead_time
```

Модель сразу формирует multi-horizon прогноз:

```text
t+1
t+2
...
t+48
```

Обе турбины могут обучаться одной TFT-моделью с:

```text
group_id = turbine_id
```

Это позволяет использовать сходство между турбинами.

История мощности особенно полезна на коротких горизонтах. При этом предварительный анализ показывает, что автокорреляция мощности быстро падает: около 0.90 на горизонте одного часа, но около 0.10 на 24 часах и около 0.07 на 48 часах. Поэтому на 24–48 часах основным источником сигнала остаётся прогноз погоды.

---

# 13. Модель №3 — Physics-Based Power Curve

Третья модель должна быть простой и интерпретируемой.

Она оценивает мощность непосредственно на основании скорости ветра:

```text
wind speed
    ↓
Power Curve
    ↓
expected power
```

Для реализации можно использовать:

```text
Isotonic Regression
```

или:

```text
Monotonic Spline
```

Исторические данные демонстрируют типичную нелинейную зависимость мощности от скорости ветра: при увеличении ветра примерно с 5 до 11 м/с мощность растёт наиболее быстро, а затем выходит на плато около номинального значения.

Power Curve выполняет две функции:

1. формирует дополнительный прогноз;
2. используется как физический контроль остальных моделей.

Например:

```text
wind = 2 m/s
TFT prediction = 0.95
```

может быть автоматически помечено как подозрительное.

---

# 14. Ensemble

После выполнения моделей система получает:

```text
LightGBM prediction
TFT prediction
Power Curve prediction
```

Финальный прогноз не должен обязательно быть простым средним.

В базовой версии:

```text
Final =
0.45 × LightGBM
+
0.40 × TFT
+
0.15 × PowerCurve
```

Однако веса должны определяться по validation выборке.

Более продвинутый вариант:

```text
LightGBM prediction
TFT prediction
PowerCurve prediction
weather disagreement
lead time
        ↓
Meta Model
        ↓
Final Prediction
```

В качестве Meta Model можно использовать:

```text
Linear Regression
Ridge
LightGBM
```

---

# 15. Прогноз неопределённости

Система должна выдавать не только одну точку:

```text
P = 0.63
```

а диапазон:

```text
P10 = 0.48
P50 = 0.63
P90 = 0.78
```

Таким образом пользователь получает представление о неопределённости прогноза.

Источники uncertainty:

```text
разница между ML/DL моделями
+
неопределённость weather forecast
+
ошибка на validation
+
аномальность текущей ситуации
```

Для PoC можно использовать упрощённую оценку uncertainty на основании model disagreement.

---

# 16. Validation Agent

После получения ансамблевого результата запускается автоматическая проверка.

Минимальные правила:

```text
0 <= power <= 1
```

Дополнительно:

```text
слишком высокая мощность при очень слабом ветре
слишком низкая мощность при сильном ветре
большое расхождение моделей
отсутствие weather data
аномальный NWP forecast
```

Пример:

```text
LightGBM = 0.66
TFT = 0.69
PowerCurve = 0.64
```

Result:

```text
model agreement = HIGH
confidence = HIGH
```

Другой пример:

```text
LightGBM = 0.34
TFT = 0.82
PowerCurve = 0.41
```

Result:

```text
model disagreement = HIGH
confidence = LOW
```

В этом случае Supervisor Agent может инициировать повторную проверку.

---

# 17. Agent Decision Logic

Базовая логика:

```text
START

↓
fetch_weather

↓
weather available?

NO → fallback weather source
YES

↓
prepare_features

↓
run LightGBM
run TFT
run Power Curve

↓
build ensemble

↓
validate

↓
forecast valid?

YES
↓
save forecast
generate report

NO
↓
check model disagreement
check weather quality

↓
recompute ensemble

↓
fallback

↓
save warning forecast
```

---

# 18. Recompute Mechanism

Одним из требований PoC является автоматический повторный расчёт.

Например новый weather forecast появился в:

```text
06:00
```

Система:

```text
обнаруживает новый forecast
        ↓
получает его
        ↓
сравнивает с предыдущим
        ↓
пересчитывает признаки
        ↓
повторно запускает модели
        ↓
обновляет final forecast
```

Все действия сохраняются в журнале:

```text
06:03 Weather forecast loaded

06:04 Features generated

06:04 LightGBM completed

06:05 TFT completed

06:05 Model disagreement detected

06:05 Ensemble recomputed

06:06 Forecast saved
```

---

# 19. Historical Replay

Для оценки PoC используется rolling historical backtest.

Например:

```text
31 января
→ прогноз 1–2 февраля

1 февраля
→ прогноз 2–3 февраля

2 февраля
→ прогноз 3–4 февраля

...

27 февраля
→ прогноз 28 февраля
```

На каждом шаге используется только информация, доступная к соответствующему `issue_time`.

Таким образом воспроизводится реальный сценарий эксплуатации системы. Этот rolling replay соответствует постановке задачи.

---

# 20. Training Pipeline

Рекомендуемое временное разделение:

```text
TRAIN:
исторический период до осени 2025

VALIDATION:
последние месяцы 2025

HOLDOUT:
январь 2026
```

После выбора гиперпараметров модели могут быть переобучены на всех данных до:

```text
31.01.2026
```

Тестовый февраль при обучении не используется.

---

# 21. Базовые модели для сравнения

Для доказательства эффективности решения необходимо сравнивать Agentic Ensemble с простыми baseline.

## Baseline 1 — Persistence

```text
future power ≈ previous power
```

## Baseline 2 — Climatology

Средняя мощность по:

```text
month
hour
turbine
```

## Baseline 3 — Power Curve

```text
weather forecast
↓
wind
↓
power curve
↓
power
```

## Предлагаемые модели

```text
LightGBM
TFT
Agentic Ensemble
```

Финальная таблица:

```text
Model                MAE     RMSE     nMAE

Persistence
Climatology
Power Curve
LightGBM
TFT
Agentic Ensemble
```

---

# 22. Дополнительный Anomaly Detector

При наличии времени в PoC может быть добавлена ещё одна ML-модель:

```text
Isolation Forest
```

или:

```text
Autoencoder
```

Она используется для выявления:

```text
аномального поведения турбины
остановок
curtailment
ошибок датчиков
OOD weather conditions
```

Например:

```text
wind = 9 m/s
power = 0
```

может быть помечено как:

```text
possible shutdown / curtailment
```

а не использоваться как обычный пример для power forecasting.

---

# 23. Роль LLM

LLM не выполняет математический прогноз мощности.

LLM выполняет:

```text
orchestration
reasoning
tool selection
error handling
result interpretation
recompute decisions
report generation
```

Пример сообщения от системы:

```text
Прогноз на следующие 48 часов сформирован.

Среднее значение P50 составляет 0.61.

В период 13:00–18:00 наблюдается повышенная
неопределённость.

TFT и LightGBM расходятся примерно на 0.19
нормализованной мощности.

Основной причиной является неопределённость
прогноза скорости ветра.

Forecast confidence: MEDIUM.
```

---

# 24. Формат конечного результата

Основным машинным результатом является CSV:

```text
issue_time
forecast_time
horizon
turbine_id

weather_wind

lightgbm_prediction
tft_prediction
powercurve_prediction

p10
p50
p90

confidence
warning
```

Пример:

```text
2026-02-10 06:00,
2026-02-10 14:00,
8,
T1,
7.1,
0.63,
0.67,
0.59,
0.49,
0.64,
0.76,
HIGH,
NONE
```

---

# 25. Dashboard

Для демонстрации PoC может использоваться Streamlit.

Главный экран:

```text
Wind Generation Forecast

Issue Time:
10.02.2026 06:00

Forecast Horizon:
48 hours

Confidence:
HIGH
```

Основной график:

```text
P10
P50
P90
Actual
```

Дополнительные блоки:

```text
Weather forecast

LightGBM forecast

TFT forecast

Power Curve forecast

Model disagreement

Agent decisions
```

---

# 26. Структура проекта

```text
project/
│
├── app/
│
│   ├── agents/
│   │   ├── supervisor.py
│   │   ├── validator.py
│   │   └── reporter.py
│
│   ├── graph/
│   │   ├── workflow.py
│   │   ├── state.py
│   │   └── nodes.py
│
│   ├── tools/
│   │   ├── weather.py
│   │   ├── data.py
│   │   ├── features.py
│   │   └── prediction.py
│
│   ├── models/
│   │   ├── lightgbm.py
│   │   ├── tft.py
│   │   ├── power_curve.py
│   │   ├── ensemble.py
│   │   └── anomaly.py
│
│   └── schemas/
│
├── data/
│   ├── raw/
│   ├── weather/
│   ├── processed/
│   └── features/
│
├── models/
│   └── artifacts/
│
├── forecasts/
│
├── reports/
│
├── dashboard/
│
├── tests/
│
├── scripts/
│   ├── train.py
│   ├── backtest.py
│   └── demo.py
│
├── requirements.txt
├── docker-compose.yml
├── README.md
└── ANALYSIS.md
```

---

# 27. Минимальный PoC

Чтобы не перегружать MVP, обязательный минимум:

```text
Historical Weather
        ↓
Feature Engineering
        ↓
LightGBM
        +
TFT
        +
Power Curve
        ↓
Weighted Ensemble
        ↓
Validator
        ↓
LLM Supervisor
        ↓
Forecast
```

То есть обязательный стек:

```text
Python

Pandas
NumPy

LightGBM

PyTorch
PyTorch Forecasting

LangGraph

LLM API

Open-Meteo

FastAPI

Streamlit
```

---

# 28. Компоненты второй очереди

После создания рабочего end-to-end PoC можно добавить:

```text
CatBoost

Weather Bias Correction

Isolation Forest

P10/P50/P90 quantile models

несколько NWP источников

adaptive ensemble

SHAP

drift detection
```

И только после этого:

```text
automatic retraining

Kafka

production SCADA integration

model registry

monitoring

Kubernetes
```

Последние компоненты относятся уже скорее к production architecture, а не к PoC.

---

# 29. Что PoC должен доказать

PoC должен показать пять вещей.

## 1. Возможность прогнозирования

Показать, что ML/DL-модели способны преобразовать доступный прогноз погоды в почасовую оценку генерации.

## 2. Отсутствие data leakage

Каждый historical run использует исключительно данные, доступные на соответствующий момент времени.

## 3. Преимущество ансамбля

Показать, что сочетание нескольких моделей устойчивее отдельных прогнозистов.

## 4. Реальную агентность

LLM должен не просто формировать текст, а управлять:

```text
fetch
prepare
predict
validate
recompute
report
```

## 5. Воспроизводимость

Полный PoC должен запускаться одной командой.

Например:

```bash
docker compose up
```

или:

```bash
python scripts/demo.py
```

---

# 30. Итоговая концепция PoC

Итоговое решение представляет собой автономную Agentic AI-систему краткосрочного прогнозирования выработки ВЭС.

Архитектура объединяет:

```text
Historical NWP forecasts
+
SCADA history
+
LightGBM
+
Temporal Fusion Transformer
+
Physics-based Power Curve
+
Ensemble
+
Uncertainty estimation
+
Automatic validation
+
LLM Supervisor
```

Основная задача LLM состоит не в генерации численного прогноза, а в интеллектуальной оркестрации прогнозного процесса.

ML и DL модели отвечают за численную точность.

Power Curve обеспечивает физическую интерпретируемость.

Ensemble повышает устойчивость результата.

Validator контролирует качество.

LLM Supervisor принимает решение о повторном расчёте, fallback-механизмах и формирует объяснение результата.

Таким образом PoC демонстрирует полный цикл:

```text
Weather
   ↓
Data
   ↓
ML/DL
   ↓
Ensemble
   ↓
Validation
   ↓
Agent Decision
   ↓
Forecast
   ↓
Report
```

В рамках хакатона основной приоритет заключается не в создании production-grade инфраструктуры, а в демонстрации полностью работающего end-to-end сценария, который можно воспроизвести на историческом тестовом периоде.

После подтверждения работоспособности PoC архитектура может быть расширена до промышленной системы с подключением live SCADA, автоматическим переобучением, мониторингом drift, дополнительными weather providers и production MLOps.
