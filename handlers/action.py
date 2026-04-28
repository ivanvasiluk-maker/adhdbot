from __future__ import annotations

from templates import (
    ACTION_TEMPLATE,
    ACTION_DONE_TEMPLATE,
    ACTION_FAILED_TEMPLATE,
    WHY_TEMPLATE,
    DOWNSCALE_NO_ENERGY,
    DOWNSCALE_TOO_HARD,
)
from state_machine import BotState


def render_action(skill_title: str, why: str, steps: list[str]) -> dict:
    steps_block = "\n".join([f"{idx+1}. {s}" for idx, s in enumerate(steps)])
    return {
        "state": BotState.WAITING_RESULT.value,
        "text": ACTION_TEMPLATE.format(skill_title=skill_title, why=why, steps=steps_block),
        "buttons": ["Сделал", "Не сделал", "Стало хуже"],
    }


def render_action_done() -> dict:
    return {
        "state": BotState.REFLECTION.value,
        "text": ACTION_DONE_TEMPLATE,
        "buttons": ["Ещё 1 круг", "Хватит на сегодня"],
    }


def render_action_failed() -> dict:
    return {
        "state": BotState.ACTION_FAILED_REASON.value,
        "text": ACTION_FAILED_TEMPLATE,
        "buttons": ["Слишком сложно", "Не понял что делать", "Нет сил", "Залип"],
    }


def render_failed_reason(reason: str) -> dict:
    reason = (reason or "").strip().lower()
    if "сложно" in reason:
        text = DOWNSCALE_TOO_HARD
    elif "нет сил" in reason:
        text = DOWNSCALE_NO_ENERGY
    else:
        text = WHY_TEMPLATE
    return {
        "state": BotState.ACTION.value,
        "text": text,
        "buttons": ["Давай микро-шаг", "Хватит на сегодня"],
    }
