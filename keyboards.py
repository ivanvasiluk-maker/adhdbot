from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def _mk(rows: list[list[str]]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t) for t in row] for row in rows],
        resize_keyboard=True,
    )


def morning_checkin_keyboard() -> ReplyKeyboardMarkup:
    return _mk([
        ["😴 плохо", "😐 норм", "🙂 хорошо"],
        ["😰 высокая", "😐 средняя", "🙂 низкая"],
        ["🔋 мало", "🔋🔋 норм", "🔋🔋🔋 много"],
    ])


def analysis_keyboard() -> ReplyKeyboardMarkup:
    return _mk([["Подробнее", "Давай действие"]])


def action_result_keyboard() -> ReplyKeyboardMarkup:
    return _mk([["Сделал", "Не сделал", "Стало хуже"]])


def action_failed_keyboard() -> ReplyKeyboardMarkup:
    return _mk([["Слишком сложно", "Не понял что делать"], ["Нет сил", "Залип"]])


def evening_keyboard() -> ReplyKeyboardMarkup:
    return _mk([["Сделал", "Пробовал", "Не получилось"]])


def offer_keyboard() -> ReplyKeyboardMarkup:
    return _mk([["7 дней — €20", "Месяц — €40"], ["Подумаю"]])
