// English source text is the stable key; unknown provider text stays unchanged.
export const messages = {
  "Saved January 2026 holdout: power curve and persistence, not LightGBM or the organizer metric. nMAE and chart series are not supplied.": {"ru":"Сохранённая проверка за январь 2026: power curve и persistence. Это не оценка LightGBM и не метрика организаторов. nMAE и ряды для графика не переданы.","kk":"2026 жылғы қаңтардағы сақталған тексеру: power curve және persistence. Бұл LightGBM бағасы да, ұйымдастырушылар метрикасы да емес. nMAE және график қатарлары берілмеген."},
  "Demo protection check: this rejection is intentional. Select ML + agent for a real forecast.": {"ru":"Демо-проверка защиты: отклонение намеренное. Для реального прогноза выберите «ML + агент» и запустите расчёт.","kk":"Қорғаныстың демо тексеруі: болжам әдейі қабылданбаған. Нақты болжам үшін «ML + агент» режимін таңдап, есепті іске қосыңыз."},
  "Run mode": {"ru":"Режим запуска","kk":"Іске қосу режимі"},
  "ML + agent": {"ru":"ML + агент","kk":"ML + агент"},
  "Demo scenarios": {"ru":"Демо-сценарии","kk":"Демо сценарийлер"},
  "Issue time (UTC)": {"ru":"Время выпуска (UTC)","kk":"Шығарылған уақыты (UTC)"},
  "Trained LightGBM · cached weather · 48 hours. LLM briefing is optional.": {"ru":"Обученная LightGBM · погода из кэша · 48 часов. LLM-сводка опциональна.","kk":"Үйретілген LightGBM · кэштегі ауа райы · 48 сағат. LLM түйіндемесі міндетті емес."},
  "API online": {"ru":"API доступен","kk":"API қолжетімді"},
  "Point forecast from trained LightGBM. P10/P90 are not supplied.": {"ru":"Точечный прогноз обученной LightGBM. Интервалы P10/P90 не рассчитаны.","kk":"Үйретілген LightGBM нүктелік болжамы. P10/P90 аралықтары есептелмеген."},
  "Forecast blocked": {"ru":"Прогноз заблокирован","kk":"Болжам бұғатталды"},
  "Validation failed. See the knowledge boundary and agent log; this run must not be published.": {"ru":"Проверка не пройдена. Причина — в границе данных и журнале агента; этот прогноз нельзя публиковать.","kk":"Тексеру сәтсіз өтті. Себебі деректер шекарасы мен агент журналында; бұл болжамды жариялауға болмайды."},
  "First-hour prediction": {"ru":"Прогноз первого часа","kk":"Бірінші сағат болжамы"},
  "Prediction": {"ru":"Прогноз","kk":"Болжам"},
  "Availability basis": {"ru":"Основание доступности","kk":"Қолжетімділік негізі"},
  "Model cutoff": {"ru":"Граница обучения","kk":"Оқыту шекарасы"},
  "assumed:init+7h": {"ru":"Допущение: запуск + 7 часов","kk":"Болжам: іске қосылу + 7 сағат"},
  "LLM briefing": {"ru":"Сводка LLM","kk":"LLM түйіндемесі"},
  "Template briefing": {"ru":"Шаблонная сводка","kk":"Үлгілік түйіндеме"},
  "llm_off": {"ru":"LLM выключена","kk":"LLM өшірілген"},
  "missing_api_key": {"ru":"API-ключ не задан","kk":"API кілті берілмеген"},
  "missing_model": {"ru":"LLM-модель не задана","kk":"LLM моделі берілмеген"},
  "grounding_guard_failed": {"ru":"Ответ LLM не прошёл проверку фактов","kk":"LLM жауабы фактілер тексеруінен өтпеді"},
  "grounding_guard_passed": {"ru":"Проверка чисел пройдена","kk":"Сандар тексеруден өтті"},
  "llm_request_failed": {"ru":"LLM недоступна — использован шаблон","kk":"LLM қолжетімсіз — үлгі қолданылды"},
  "PUBLISH": {"ru":"ОПУБЛИКОВАТЬ","kk":"ЖАРИЯЛАУ"},
  "REJECT": {"ru":"ОТКЛОНИТЬ","kk":"ҚАБЫЛДАМАУ"},
  "first_publication": {"ru":"Первая публикация","kk":"Алғашқы жариялау"},
  "no_published_overlap": {"ru":"Нет общих часов с прошлым прогнозом","kk":"Алдыңғы болжаммен ортақ сағаттар жоқ"},
  "energy_change_ge_threshold": {"ru":"Изменение достигло порога публикации","kk":"Өзгеріс жариялау шегіне жетті"},
  "energy_change_below_threshold": {"ru":"Изменение ниже порога — сохранено без публикации","kk":"Өзгеріс шектен төмен — жарияламай сақталды"},
  "no_legal_weather": {"ru":"Нет доступной архивной погоды для этого выпуска","kk":"Осы шығарылымға қолжетімді архивтік ауа райы жоқ"},
  "model_cutoff_after_issue": {"ru":"Модель обучена на данных после времени выпуска","kk":"Модель шығарылым уақытынан кейінгі деректермен оқытылған"},
  "future_weather": {"ru":"Погода ещё не была доступна на момент выпуска","kk":"Ауа райы шығарылған сәтте әлі қолжетімсіз болған"},
  "cutoff_unknown": {"ru":"Неизвестна граница обучения модели","kk":"Модельдің оқыту шекарасы белгісіз"},
  "select_weather": {"ru":"Выбор погоды","kk":"Ауа райын таңдау"},
  "leakage_check": {"ru":"Проверка утечки","kk":"Дерек ағып кетуін тексеру"},
  "fetch_weather": {"ru":"Загрузка погоды","kk":"Ауа райын жүктеу"},
  "validate_weather": {"ru":"Проверка погоды","kk":"Ауа райын тексеру"},
  "predict": {"ru":"Расчёт прогноза","kk":"Болжамды есептеу"},
  "validate_forecast": {"ru":"Проверка прогноза","kk":"Болжамды тексеру"},
  "decide": {"ru":"Решение","kk":"Шешім"},
  "store": {"ru":"Сохранение","kk":"Сақтау"},
  "brief": {"ru":"Сводка","kk":"Түйіндеме"},
  "Overview": {
    "ru": "Обзор",
    "kk": "Шолу"
  },
  "History": {
    "ru": "История",
    "kk": "Тарих"
  },
  "Backtest": {
    "ru": "Проверка на истории",
    "kk": "Тарихи тексеру"
  },
  "Forecast OS": {
    "ru": "Система прогнозов",
    "kk": "Болжам жүйесі"
  },
  "Windline home": {
    "ru": "Главная Windline",
    "kk": "Windline басты беті"
  },
  "Mock grid": {
    "ru": "Демо-режим",
    "kk": "Демо режим"
  },
  "Hybrid grid": {
    "ru": "Смешанный режим",
    "kk": "Аралас режим"
  },
  "Offline": {
    "ru": "Нет связи",
    "kk": "Байланыс жоқ"
  },
  "System": {
    "ru": "Система",
    "kk": "Жүйе"
  },
  "Vintage-aware energy": {
    "ru": "Энергия с учётом версий данных",
    "kk": "Дерек нұсқаларын ескеретін энергия"
  },
  "Almaty wind field": {
    "ru": "Ветропарк Алматы",
    "kk": "Алматы жел паркі"
  },
  "Operations deck": {
    "ru": "Панель управления",
    "kk": "Басқару панелі"
  },
  "UTC · Vintage safe": {
    "ru": "UTC · Контроль данных",
    "kk": "UTC · Деректерді бақылау"
  },
  "Switch to light theme": {
    "ru": "Включить светлую тему",
    "kk": "Ашық тақырыпқа ауысу"
  },
  "Switch to dark theme": {
    "ru": "Включить тёмную тему",
    "kk": "Қараңғы тақырыпқа ауысу"
  },
  "Light theme": {
    "ru": "Светлая тема",
    "kk": "Ашық тақырып"
  },
  "Dark theme": {
    "ru": "Тёмная тема",
    "kk": "Қараңғы тақырып"
  },
  "Light": {
    "ru": "Светлая",
    "kk": "Ашық"
  },
  "Dark": {
    "ru": "Тёмная",
    "kk": "Қараңғы"
  },
  "Language": {
    "ru": "Язык",
    "kk": "Тіл"
  },
  "Agentic AI for Vintage-Aware Wind Power Forecasting": {
    "ru": "AI-прогнозирование ветровой выработки с учётом версий данных",
    "kk": "Дерек нұсқаларын ескеретін жел энергиясын AI арқылы болжау"
  },
  "Web layer · PoC": {
    "ru": "Веб-интерфейс · Прототип",
    "kk": "Веб-интерфейс · Прототип"
  },
  "Vintage-aware operations": {
    "ru": "Прогнозы с учётом версий данных",
    "kk": "Дерек нұсқаларын ескеретін болжам"
  },
  "See the wind": {
    "ru": "Предвидеть ветер",
    "kk": "Желді алдын ала"
  },
  "before it arrives.": {
    "ru": "до его прихода.",
    "kk": "біліңіз."
  },
  "One living view of generation, uncertainty, weather provenance and every decision behind the forecast.": {
    "ru": "Выработка, неопределённость, источники погоды и решения, на которых основан прогноз, — в одном интерфейсе.",
    "kk": "Өндіріс, белгісіздік, ауа райы деректерінің көздері және болжам негізіндегі шешімдер — бір интерфейсте."
  },
  "24–48h": {
    "ru": "24–48 ч",
    "kk": "24–48 сағ"
  },
  "Forecast horizon": {
    "ru": "Горизонт прогноза",
    "kk": "Болжам көкжиегі"
  },
  "Live topology": {
    "ru": "Состав ветропарка",
    "kk": "Жел паркінің құрамы"
  },
  "No leak": {
    "ru": "Без утечки",
    "kk": "Дерек ағып кетпейді"
  },
  "Vintage boundary": {
    "ru": "Граница данных",
    "kk": "Деректер шекарасы"
  },
  "Forecast console": {
    "ru": "Настройки прогноза",
    "kk": "Болжам баптаулары"
  },
  "Historical replay": {
    "ru": "Исторический сценарий",
    "kk": "Тарихи сценарий"
  },
  "Issue time": {
    "ru": "Время выпуска",
    "kk": "Шығарылған уақыты"
  },
  "Horizon": {
    "ru": "Горизонт",
    "kk": "Көкжиек"
  },
  "Scenario": {
    "ru": "Сценарий",
    "kk": "Сценарий"
  },
  "24 hours": {
    "ru": "24 часа",
    "kk": "24 сағат"
  },
  "48 hours": {
    "ru": "48 часов",
    "kk": "48 сағат"
  },
  "A · Normal": {
    "ru": "A · Обычный",
    "kk": "A · Қалыпты"
  },
  "B · Baselines": {
    "ru": "B · Базовые модели",
    "kk": "B · Базалық модельдер"
  },
  "C · Revision V1→V2": {
    "ru": "C · Пересмотр V1→V2",
    "kk": "C · Қайта қарау V1→V2"
  },
  "D · Leakage rejected": {
    "ru": "D · Блокировка утечки",
    "kk": "D · Дерек ағып кетуін бұғаттау"
  },
  "E · Agent unavailable": {
    "ru": "E · Агент недоступен",
    "kk": "E · Агент қолжетімсіз"
  },
  "F · Optional models": {
    "ru": "F · Дополнительные модели",
    "kk": "F · Қосымша модельдер"
  },
  "Running pipeline…": {
    "ru": "Расчёт прогноза…",
    "kk": "Болжам есептелуде…"
  },
  "Launch forecast": {
    "ru": "Запустить прогноз",
    "kk": "Болжамды іске қосу"
  },
  "All generated values are marked as demo data.": {
    "ru": "Все сгенерированные значения помечены как демонстрационные.",
    "kk": "Барлық жасалған мәндер демо деректер ретінде белгіленген."
  },
  "Backend unavailable": {
    "ru": "Сервер недоступен",
    "kk": "Сервер қолжетімсіз"
  },
  "No forecast available": {
    "ru": "Прогноз пока отсутствует",
    "kk": "Болжам әзірге жоқ"
  },
  "No forecast available.": {
    "ru": "Прогноз пока отсутствует.",
    "kk": "Болжам әзірге жоқ."
  },
  "Run one of the mock scenarios to validate the integration flow.": {
    "ru": "Запустите один из демо-сценариев для проверки работы системы.",
    "kk": "Жүйенің жұмысын тексеру үшін демо сценарийлердің бірін іске қосыңыз."
  },
  "MOCK MODE": {
    "ru": "ДЕМО-РЕЖИМ",
    "kk": "ДЕМО РЕЖИМ"
  },
  "Synthetic data for integration and UI testing only.": {
    "ru": "Синтетические данные только для проверки интеграции и интерфейса.",
    "kk": "Тек интеграция мен интерфейсті тексеруге арналған синтетикалық деректер."
  },
  "Protection worked as designed": {
    "ru": "Защита сработала корректно",
    "kk": "Қорғаныс дұрыс іске қосылды"
  },
  "This demo run intentionally contains weather unavailable at issue time. Publication was blocked before future information could be used.": {
    "ru": "В этом демо-сценарии намеренно использована погода, недоступная на момент выпуска. Публикация заблокирована для защиты от данных из будущего.",
    "kk": "Бұл демо сценарийде шығарылған сәтте қолжетімсіз ауа райы деректері әдейі қолданылған. Болашақ деректерді қолдануға жол бермеу үшін жариялау бұғатталды."
  },
  "Current run": {
    "ru": "Текущий расчёт",
    "kk": "Ағымдағы есеп"
  },
  "Wind power forecast": {
    "ru": "Прогноз ветровой выработки",
    "kk": "Жел энергиясының болжамы"
  },
  "Vintage-aware output with uncertainty, provenance and decisions.": {
    "ru": "Прогноз с диапазоном неопределённости, источниками данных и журналом решений.",
    "kk": "Белгісіздік ауқымы, дерек көздері және шешімдер журналы бар болжам."
  },
  "First-hour P50": {
    "ru": "P50 первого часа",
    "kk": "Бірінші сағаттың P50 мәні"
  },
  "Integrity": {
    "ru": "Проверка данных",
    "kk": "Деректерді тексеру"
  },
  "Agent": {
    "ru": "Агент",
    "kk": "Агент"
  },
  "Blocked diagnostic output": {
    "ru": "Диагностика заблокированного прогноза",
    "kk": "Бұғатталған болжам диагностикасы"
  },
  "Power outlook": {
    "ru": "Прогноз выработки",
    "kk": "Өндіріс болжамы"
  },
  "{hours}-hour forecast": {
    "ru": "Прогноз на {hours} ч",
    "kk": "{hours} сағатқа болжам"
  },
  "{hours} hours": {
    "ru": "{hours} ч",
    "kk": "{hours} сағат"
  },
  "h": {
    "ru": "ч",
    "kk": "сағ"
  },
  "PLANT": {
    "ru": "ВЭС",
    "kk": "ЖЭС"
  },
  "Signals": {
    "ru": "Показатели",
    "kk": "Көрсеткіштер"
  },
  "Model comparison": {
    "ru": "Сравнение моделей",
    "kk": "Модельдерді салыстыру"
  },
  "Dynamic provider output": {
    "ru": "Данные прогнозного провайдера",
    "kk": "Болжам провайдерінің деректері"
  },
  "Loading forecast…": {
    "ru": "Загрузка прогноза…",
    "kk": "Болжам жүктелуде…"
  },
  "Forecast unavailable": {
    "ru": "Прогноз недоступен",
    "kk": "Болжам қолжетімсіз"
  },
  "Stored runs": {
    "ru": "Сохранённые расчёты",
    "kk": "Сақталған есептер"
  },
  "Forecast history": {
    "ru": "История прогнозов",
    "kk": "Болжамдар тарихы"
  },
  "Repeated historical replays persisted by the application layer.": {
    "ru": "Сохранённые результаты запусков исторических сценариев.",
    "kk": "Тарихи сценарийлерді іске қосудың сақталған нәтижелері."
  },
  "Loading history…": {
    "ru": "Загрузка истории…",
    "kk": "Тарих жүктелуде…"
  },
  "History unavailable:": {
    "ru": "История недоступна:",
    "kk": "Тарих қолжетімсіз:"
  },
  "No stored forecasts yet.": {
    "ru": "Сохранённых прогнозов пока нет.",
    "kk": "Сақталған болжамдар әзірге жоқ."
  },
  "Forecast": {
    "ru": "Прогноз",
    "kk": "Болжам"
  },
  "Version": {
    "ru": "Версия",
    "kk": "Нұсқа"
  },
  "Status": {
    "ru": "Статус",
    "kk": "Күйі"
  },
  "Model": {
    "ru": "Модель",
    "kk": "Модель"
  },
  "Created": {
    "ru": "Создан",
    "kk": "Жасалған"
  },
  "Evaluation interface": {
    "ru": "Оценка качества",
    "kk": "Сапаны бағалау"
  },
  "The web layer renders team metrics without calculating or inventing them.": {
    "ru": "Интерфейс отображает переданные командой метрики, не рассчитывая и не подменяя их.",
    "kk": "Интерфейс команда ұсынған метрикаларды есептемей және өзгертпей көрсетеді."
  },
  "Backtest unavailable:": {
    "ru": "Проверка на истории недоступна:",
    "kk": "Тарихи тексеру қолжетімсіз:"
  },
  "MOCK PLACEHOLDER": {
    "ru": "ДЕМО-ЗАГЛУШКА",
    "kk": "ДЕМО ҮЛГІ"
  },
  "Actual vs Forecast will appear when the evaluation module supplies a series.": {
    "ru": "Сравнение факта и прогноза появится, когда модуль оценки передаст временной ряд.",
    "kk": "Нақты мәндер мен болжамды салыстыру бағалау модулі уақыт қатарын бергенде пайда болады."
  },
  "N/A": {
    "ru": "Нет данных",
    "kk": "Деректер жоқ"
  },
  "Supervisor activity": {
    "ru": "Действия агента",
    "kk": "Агент әрекеттері"
  },
  "Agent result": {
    "ru": "Результат агента",
    "kk": "Агент нәтижесі"
  },
  "No agent events. Deterministic forecast remains available.": {
    "ru": "Событий агента нет. Численный прогноз остаётся доступен.",
    "kk": "Агент оқиғалары жоқ. Сандық болжам қолжетімді болып қалады."
  },
  "Forecast uncertainty chart": {
    "ru": "График неопределённости прогноза",
    "kk": "Болжам белгісіздігінің графигі"
  },
  "Forecast receipt": {
    "ru": "Паспорт прогноза",
    "kk": "Болжам паспорты"
  },
  "Weather source": {
    "ru": "Источник погоды",
    "kk": "Ауа райы деректерінің көзі"
  },
  "Weather run": {
    "ru": "Запуск погодной модели",
    "kk": "Ауа райы моделінің іске қосылуы"
  },
  "Available at": {
    "ru": "Время доступности",
    "kk": "Қолжетімді болған уақыты"
  },
  "Model version": {
    "ru": "Версия модели",
    "kk": "Модель нұсқасы"
  },
  "Feature version": {
    "ru": "Версия признаков",
    "kk": "Белгілер нұсқасы"
  },
  "Future observations": {
    "ru": "Наблюдения из будущего",
    "kk": "Болашақ бақылаулар"
  },
  "YES": {
    "ru": "ДА",
    "kk": "ИӘ"
  },
  "NO": {
    "ru": "НЕТ",
    "kk": "ЖОҚ"
  },
  "Knowledge-boundary result unavailable": {
    "ru": "Результат проверки границы данных недоступен",
    "kk": "Деректер шекарасын тексеру нәтижесі қолжетімсіз"
  },
  "Knowledge boundary": {
    "ru": "Граница доступных данных",
    "kk": "Қолжетімді деректер шекарасы"
  },
  "Future data blocked": {
    "ru": "Данные из будущего заблокированы",
    "kk": "Болашақ деректер бұғатталды"
  },
  "Evidence is time-legal": {
    "ru": "Данные доступны на момент выпуска",
    "kk": "Деректер шығарылған сәтте қолжетімді"
  },
  "Weather available": {
    "ru": "Погода доступна с",
    "kk": "Ауа райы деректерінің қолжетімді уақыты"
  },
  "Future information": {
    "ru": "Данные из будущего",
    "kk": "Болашақ деректер"
  },
  "Safety rule triggered.": {
    "ru": "Сработало правило защиты.",
    "kk": "Қорғаныс ережесі іске қосылды."
  },
  "No model predictions supplied": {
    "ru": "Прогнозы моделей не переданы",
    "kk": "Модель болжамдары берілмеген"
  },
  "Metrics: N/A until the evaluation module supplies them.": {
    "ru": "Метрики недоступны, пока их не передаст модуль оценки.",
    "kk": "Бағалау модулі бермейінше метрикалар қолжетімсіз."
  },
  "Provenance": {
    "ru": "Происхождение данных",
    "kk": "Деректердің шығу тегі"
  },
  "Traceable forecast inputs": {
    "ru": "Источники и версии данных",
    "kk": "Деректердің көздері мен нұсқалары"
  },
  "Forecast ID": {
    "ru": "ID прогноза",
    "kk": "Болжам ID"
  },
  "No lineage supplied": {
    "ru": "История версий не передана",
    "kk": "Нұсқалар тарихы берілмеген"
  },
  "Forecast lineage": {
    "ru": "Версии прогноза",
    "kk": "Болжам нұсқалары"
  },
  "Compute → publish history": {
    "ru": "От расчёта к публикации",
    "kk": "Есептеуден жариялауға дейін"
  },
  "No reason supplied": {
    "ru": "Причина не указана",
    "kk": "Себебі көрсетілмеген"
  },
  "Weather unavailable": {
    "ru": "Погодные данные недоступны",
    "kk": "Ауа райы деректері қолжетімсіз"
  },
  "Weather context": {
    "ru": "Погодные условия",
    "kk": "Ауа райы жағдайлары"
  },
  "Unknown source": {
    "ru": "Неизвестный источник",
    "kk": "Белгісіз дерек көзі"
  },
  "DEMO DATA": {
    "ru": "ДЕМО-ДАННЫЕ",
    "kk": "ДЕМО ДЕРЕКТЕР"
  },
  "Selected run": {
    "ru": "Выбранный запуск",
    "kk": "Таңдалған іске қосу"
  },
  "Run time": {
    "ru": "Время запуска",
    "kk": "Іске қосылған уақыты"
  },
  "Available": {
    "ru": "Доступно с",
    "kk": "Қолжетімді уақыты"
  },
  "First-hour wind": {
    "ru": "Ветер в первый час",
    "kk": "Бірінші сағаттағы жел"
  },
  "m/s @ 100m": {
    "ru": "м/с на высоте 100 м",
    "kk": "м/с, 100 м биіктікте"
  },
  "Temperature": {
    "ru": "Температура",
    "kk": "Температура"
  },
  "Direction": {
    "ru": "Направление",
    "kk": "Бағыт"
  },
  "Animated wind farm visualization": {
    "ru": "Анимация ветропарка",
    "kk": "Жел паркінің анимациясы"
  },
  "Three animated wind turbines in a curved landscape": {
    "ru": "Три вращающиеся ветряные турбины на фоне холмов",
    "kk": "Төбелер аясындағы айналып тұрған үш жел турбинасы"
  },
  "Wind farm live status": {
    "ru": "Состояние ветропарка",
    "kk": "Жел паркінің күйі"
  },
  "Wind farm telemetry": {
    "ru": "Телеметрия ВЭС",
    "kk": "ЖЭС телеметриясы"
  },
  "Wind field": {
    "ru": "Ветровое поле",
    "kk": "Жел өрісі"
  },
  "Live": {
    "ru": "Активно",
    "kk": "Белсенді"
  },
  "Farm state": {
    "ru": "Состояние ВЭС",
    "kk": "ЖЭС күйі"
  },
  "Nominal": {
    "ru": "В норме",
    "kk": "Қалыпты"
  },
  "PASS": {
    "ru": "ПРОЙДЕНО",
    "kk": "ӨТТІ"
  },
  "FAILED": {
    "ru": "ОШИБКА",
    "kk": "ҚАТЕ"
  },
  "PUBLISHED": {
    "ru": "ОПУБЛИКОВАН",
    "kk": "ЖАРИЯЛАНДЫ"
  },
  "REJECTED": {
    "ru": "ОТКЛОНЁН",
    "kk": "ҚАБЫЛДАНБАДЫ"
  },
  "COMPLETED": {
    "ru": "ЗАВЕРШЕНО",
    "kk": "АЯҚТАЛДЫ"
  },
  "UNAVAILABLE": {
    "ru": "НЕДОСТУПНО",
    "kk": "ҚОЛЖЕТІМСІЗ"
  },
  "COMPUTED": {
    "ru": "РАССЧИТАН",
    "kk": "ЕСЕПТЕЛДІ"
  },
  "SHADOW": {
    "ru": "ТЕНЕВОЙ РЕЖИМ",
    "kk": "КӨЛЕҢКЕЛІ РЕЖИМ"
  },
  "BLOCKED": {
    "ru": "ЗАБЛОКИРОВАНО",
    "kk": "БҰҒАТТАЛДЫ"
  },
  "UNKNOWN": {
    "ru": "НЕИЗВЕСТНО",
    "kk": "БЕЛГІСІЗ"
  },
  "HIGH": {
    "ru": "ВЫСОКАЯ",
    "kk": "ЖОҒАРЫ"
  },
  "MEDIUM": {
    "ru": "СРЕДНЯЯ",
    "kk": "ОРТАША"
  },
  "LOW": {
    "ru": "НИЗКАЯ",
    "kk": "ТӨМЕН"
  },
  "Failed to fetch": {
    "ru": "Не удалось связаться с сервером. Проверьте запуск backend и адрес API.",
    "kk": "Сервермен байланысу мүмкін болмады. Backend іске қосылғанын және API мекенжайын тексеріңіз."
  },
  "Request failed ({status})": {
    "ru": "Ошибка запроса ({status})",
    "kk": "Сұрау қатесі ({status})"
  },
  "No team backtest result has been integrated. Metrics are intentionally N/A.": {
    "ru": "Результаты проверки от команды ещё не подключены. Метрики намеренно не заполнены.",
    "kk": "Команданың тексеру нәтижелері әлі қосылмаған. Метрикалар әдейі толтырылмаған."
  },
  "Demo scenario: weather was not available at issue time.": {
    "ru": "Демо-сценарий: погодные данные не были доступны на момент выпуска.",
    "kk": "Демо сценарий: ауа райы деректері шығарылған сәтте қолжетімсіз болған."
  },
  "DEMO weather fixture": {
    "ru": "Демонстрационные погодные данные",
    "kk": "Демонстрациялық ауа райы деректері"
  },
  "Agent provider is unavailable; numerical forecast is preserved.": {
    "ru": "Провайдер агента недоступен; численный прогноз сохранён.",
    "kk": "Агент провайдері қолжетімсіз; сандық болжам сақталды."
  },
  "Agent is unavailable; numerical mock forecast remains accessible.": {
    "ru": "Агент недоступен; численный демо-прогноз остаётся доступен.",
    "kk": "Агент қолжетімсіз; сандық демо болжам қолжетімді болып қалады."
  },
  "weather validation": {
    "ru": "Проверка погоды",
    "kk": "Ауа райын тексеру"
  },
  "forecast validation": {
    "ru": "Проверка прогноза",
    "kk": "Болжамды тексеру"
  },
  "publication": {
    "ru": "Публикация",
    "kk": "Жариялау"
  },
  "Future weather detected in demo scenario.": {
    "ru": "В демо-сценарии обнаружены погодные данные из будущего.",
    "kk": "Демо сценарийде болашақ ауа райы деректері анықталды."
  },
  "Mock weather vintage verdict received.": {
    "ru": "Получен результат проверки времени доступности демо-погоды.",
    "kk": "Демо ауа райының қолжетімділік уақытын тексеру нәтижесі алынды."
  },
  "Forecast rejected by upstream boundary result.": {
    "ru": "Прогноз отклонён по результату проверки границы данных.",
    "kk": "Деректер шекарасын тексеру нәтижесі бойынша болжам қабылданбады."
  },
  "Structured forecast received from provider.": {
    "ru": "Получен структурированный прогноз от провайдера.",
    "kk": "Провайдерден құрылымдалған болжам алынды."
  },
  "Publication blocked.": {
    "ru": "Публикация заблокирована.",
    "kk": "Жариялау бұғатталды."
  },
  "Mock forecast published.": {
    "ru": "Демо-прогноз опубликован.",
    "kk": "Демо болжам жарияланды."
  },
  "Demo forecast rejected.": {
    "ru": "Демо-прогноз отклонён.",
    "kk": "Демо болжам қабылданбады."
  },
  "Demo forecast accepted.": {
    "ru": "Демо-прогноз принят.",
    "kk": "Демо болжам қабылданды."
  },
  "Do not use this run: mock future weather was detected.": {
    "ru": "Не используйте этот расчёт: обнаружены демо-данные погоды из будущего.",
    "kk": "Бұл есепті қолданбаңыз: болашақ ауа райының демо деректері анықталды."
  },
  "Mock run passed the provided validation verdict.": {
    "ru": "Демо-расчёт прошёл предусмотренную проверку.",
    "kk": "Демо есеп берілген тексеруден өтті."
  },
  "Initial mock forecast": {
    "ru": "Первоначальный демо-прогноз",
    "kk": "Бастапқы демо болжам"
  },
  "Mock weather update for lineage demonstration": {
    "ru": "Демо-обновление погоды для показа истории версий",
    "kk": "Нұсқалар тарихын көрсетуге арналған ауа райының демо жаңартуы"
  },
  "publish_revision": {
    "ru": "Публикация новой версии",
    "kk": "Жаңа нұсқаны жариялау"
  },
  "publish": {
    "ru": "Опубликовать",
    "kk": "Жариялау"
  },
  "reject": {
    "ru": "Отклонить",
    "kk": "Қабылдамау"
  },
  "Demo scenario: a team module requested publication": {
    "ru": "Демо-сценарий: модуль команды запросил публикацию",
    "kk": "Демо сценарий: команда модулі жариялауды сұрады"
  }
};

export const locales = { en: "en-GB", ru: "ru-RU", kk: "kk-KZ" };
export const languages = [
  { code: "kk", name: "Қазақша" },
  { code: "ru", name: "Русский" },
  { code: "en", name: "English" },
];
export const normalizeLanguage = (value) => Object.hasOwn(locales, value) ? value : "en";

export function translate(language, key, values = {}) {
  if (key == null) return "";
  const source = String(key);
  const text = messages[source]?.[normalizeLanguage(language)] || source;
  return text.replace(/\{(\w+)\}/g, (match, name) => values[name] ?? match);
}

export function formatDate(language, value, options) {
  if (!value || Number.isNaN(new Date(value).getTime())) return translate(language, "N/A");
  return new Intl.DateTimeFormat(locales[normalizeLanguage(language)], options || {
    day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit",
  }).format(new Date(value));
}

export function formatNumber(language, value) {
  if (value == null) return translate(language, "N/A");
  return typeof value === "number"
    ? new Intl.NumberFormat(locales[normalizeLanguage(language)], { maximumFractionDigits: 3 }).format(value)
    : value;
}
