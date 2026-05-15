from __future__ import annotations

from state_machine import BotState
from templates import EVENING_TEMPLATE, DAY3_OFFER_TEMPLATE


def render_evening(day: int) -> dict:
    return {
        "state": BotState.EVENING.value,
        "text": EVENING_TEMPLATE,
        "buttons": ["Сделал", "Пробовал", "Не получилось"],
        "day": int(day or 1),
    }


def render_day3_offer() -> dict:
    return {
        "state": BotState.OFFER.value,
        "text": DAY3_OFFER_TEMPLATE,
        "buttons": ["7 дней — €20", "Месяц — €40", "Подумаю"],
    }
