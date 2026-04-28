from __future__ import annotations

from events import log_event


async def show_payment_options(user_id: int, db_path: str = "bot.db") -> dict:
    await log_event(user_id, "offer_shown", db_path=db_path)
    return {
        "text": "Продолжить?",
        "buttons": ["7 дней — €20", "Месяц — €40", "Подумаю"],
    }


async def handle_payment_choice(user_id: int, choice: str, db_path: str = "bot.db") -> str:
    normalized = (choice or "").strip().lower()
    if "€20" in choice or "20" in normalized:
        await log_event(user_id, "payment_click_20", db_path=db_path)
        return (
            "Оплата почти готова.\n\n"
            "Пока тестируем MVP:\nнапиши сюда “хочу 7 дней” — и я включу доступ вручную."
        )
    if "€40" in choice or "40" in normalized:
        await log_event(user_id, "payment_click_40", db_path=db_path)
        return (
            "Месячный режим включает:\n\n"
            "— ежедневное сопровождение\n"
            "— память паттернов\n"
            "— адаптацию навыков\n"
            "— вечерние итоги\n"
            "— режим тренировки разговоров\n\n"
            "Пока оплата подключается. Я записал твой выбор."
        )

    await log_event(user_id, "payment_declined_soft", db_path=db_path)
    return "Ок, продолжаем в режиме тренировки."
