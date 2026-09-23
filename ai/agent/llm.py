"""Russian briefings; the LLM cannot change forecasts or decisions."""
import json
import os
import re
from decimal import Decimal, InvalidOperation

from ai import config

PRECISION = 4
NUMBER = re.compile(r"(?<![\d.])[+-]?\d+(?:[.,]\d+)?(?:[eE][+-]?\d+)?")
SYSTEM_PROMPT = (
    "Объясни факты диспетчеру энергосистемы по-русски, не более 120 слов. "
    "Используй только числа из JSON фактов. Не прогнозируй новые числа. "
    "Время доступности погоды является допущением. Не изменяй решение."
)


def template(facts: dict) -> str:
    decision = {"PUBLISH": "Опубликовать", "SHADOW": "Сохранить без публикации", "REJECT": "Отклонить"}
    lines = [f"Выпуск: {facts['issue_time']}. Решение: {decision[facts['decision']]}. "
             f"Причина: {facts['reason']}."]
    if facts.get("weather_run_id"):
        lines.append(f"Погода: {facts['weather_run_id']}; доступна с {facts['available_at']} "
                     f"по допущению {facts['availability_basis']}.")
    if facts.get("energy_change_pct") is not None:
        lines.append(f"Изменение энергии на общих часах: {facts['energy_change_pct']:.4f}%.")
    for turbine, stats in facts.get("power", {}).items():
        lines.append(f"{turbine}: минимум {stats['min']:.4f}, максимум {stats['max']:.4f}, "
                     f"среднее {stats['mean']:.4f}.")
    if facts.get("warnings"):
        lines.append("Предупреждения: " + "; ".join(facts["warnings"]) + ".")
    return " ".join(lines)


def _numbers(text: str) -> set[Decimal]:
    # Hyphens within ISO dates/run identifiers are separators, not numeric signs.
    text = re.sub(r"(?<=\d)-(?=\d)", " ", text)
    text = re.sub(r"(?<=\d),(?=\d)", ".", text)
    return {Decimal(token).quantize(Decimal("0.0001")) for token in NUMBER.findall(text)}


def _fact_numbers(value) -> set[Decimal]:
    """Read each scalar separately so JSON separators cannot become decimal commas."""
    if isinstance(value, dict):
        return set().union(*(_fact_numbers(item) for pair in value.items() for item in pair))
    if isinstance(value, (list, tuple)):
        return set().union(*(_fact_numbers(item) for item in value))
    if value is None or isinstance(value, bool):
        return set()
    return _numbers(str(value))


def grounded(reply: str, facts: dict) -> bool:
    try:
        return (bool(reply.strip()) and len(reply.split()) <= 120 and bool(re.search("[А-Яа-я]", reply))
                and _numbers(reply) <= _fact_numbers(facts))
    except (InvalidOperation, ValueError):
        return False


def _request(facts: dict, key: str, model: str, base_url: str | None = None) -> str:
    from openai import OpenAI
    with OpenAI(api_key=key, base_url=base_url, timeout=30, max_retries=0,
                default_headers={"Accept-Encoding": "identity"}) as client:
        params = {"model": model, "timeout": 30,
                  "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                               {"role": "user", "content": json.dumps(facts, ensure_ascii=False, allow_nan=False)}]}
        result = client.chat.completions.create(**params)
    return result.choices[0].message.content or ""


def brief(facts: dict, mode: str = "off") -> dict:
    fallback = template(facts)
    result = {"text": fallback, "llm_used": False, "reason": "llm_off"}
    if mode == "off":
        return result
    try:
        from dotenv import load_dotenv
        load_dotenv(config.ROOT / ".env")
        key, model = os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_MODEL")
        if not key:
            return {**result, "reason": "missing_api_key"}
        if not model:
            return {**result, "reason": "missing_model"}
        reply = _request(facts, key, model, os.getenv("OPENAI_BASE_URL") or None)
        if not grounded(reply, facts):
            return {**result, "reason": "grounding_guard_failed"}
        return {"text": reply, "llm_used": True, "reason": "grounding_guard_passed"}
    except Exception:
        # Never expose provider exceptions: they may contain credentials or request data.
        return {**result, "reason": "llm_request_failed"}
