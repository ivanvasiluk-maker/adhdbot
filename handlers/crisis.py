from __future__ import annotations

from state_machine import BotState


CRISIS_TEXT = (
    "Похоже, сейчас перегруз.\n\n"
    "Сделай grounding 60 секунд:\n"
    "1) Назови 5 предметов вокруг\n"
    "2) Почувствуй опору ног\n"
    "3) Сделай медленный выдох 6 секунд\n\n"
    "Когда станет чуть стабильнее — вернёмся к одному микро-шагу."
)


def render_crisis() -> dict:
    return {
        "state": BotState.CRISIS.value,
        "text": CRISIS_TEXT,
        "buttons": ["Сделал grounding", "Нужен ещё круг"],
    }
