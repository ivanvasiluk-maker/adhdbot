from __future__ import annotations

from templates import SHORT_ANALYSIS_TEMPLATE
from state_machine import BotState


def render_short_analysis(short_analysis: str) -> dict:
    return {
        "state": BotState.ANALYSIS.value,
        "text": SHORT_ANALYSIS_TEMPLATE.format(short_analysis=short_analysis.strip()),
        "buttons": ["Подробнее", "Давай действие"],
    }


def render_long_analysis(long_analysis: str) -> dict:
    return {
        "state": BotState.DETAILS.value,
        "text": long_analysis.strip(),
        "buttons": ["Давай действие"],
    }
