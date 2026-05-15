from __future__ import annotations

from state_machine import BotState
from templates import MORNING_CHECKIN


def start_flow_message() -> dict:
    return {
        "state": BotState.ONBOARDING.value,
        "text": "Выбери, что мешает чаще всего: старт, фокус или тревога.",
        "buttons": ["Старт", "Фокус", "Тревога"],
    }


def onboarding_to_checkin() -> dict:
    return {
        "state": BotState.MORNING_CHECKIN.value,
        "text": MORNING_CHECKIN,
        "buttons": ["😴 плохо", "😐 норм", "🙂 хорошо", "😰 высокая", "😐 средняя", "🙂 низкая", "🔋 мало", "🔋🔋 норм", "🔋🔋🔋 много"],
    }
