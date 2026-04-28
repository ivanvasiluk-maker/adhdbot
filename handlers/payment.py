from __future__ import annotations

from payments import handle_payment_choice
from state_machine import BotState


async def process_offer_choice(user_id: int, choice: str, db_path: str = "bot.db") -> dict:
    text = await handle_payment_choice(user_id=user_id, choice=choice, db_path=db_path)
    next_state = BotState.FREE_MODE.value if choice == "Подумаю" else BotState.PAID_MODE.value
    return {
        "state": next_state,
        "text": text,
    }
