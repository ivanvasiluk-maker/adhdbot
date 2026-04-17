# ============================================================
# TEXTS.PY — Все текстовые константы и клавиатуры
# ============================================================

import json
import math
import random
from datetime import datetime
from typing import Dict, Any, Optional, List
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from skills_texts import SKILLS_TEXTS

# ============================================================
# TRAINERS (стили)
# ============================================================

TRAINERS = {
    "skinny": {
        "name": "Скинни",
        "tone": "жёсткий, прямой",
        "emoji": "🐈‍⬛",
        "short": "Без воды. Сделал — молодец. Не сделал — вернись.",
    },
    "marsha": {
        "name": "Марша",
        "tone": "мягкий, поддерживающий",
        "emoji": "🐈",
        "short": "Мягко возвращаемся. Без наказания. Навык важнее эмоций.",
    },
    "beck": {
        "name": "Бек",
        "tone": "аналитичный, структурный",
        "emoji": "🐈‍🦁",
        "short": "Тренируем конкретную функцию. Измеряем фактами.",
    },
}

# ============================================================
# 🐈 TRAINER PRESENTATION BLOCK
# ============================================================

TRAINER_INTRO_TEXT = {
    "marsha": {
        "who": "🤍 Марша — мягкий тренер",
        "for_whom": (
            "Подходит, если:\n"
            "• много самокритики\n"
            "• тревога мешает начинать\n"
            "• давление только усиливает срыв\n"
        ),
        "intro": (
            "Привет. Я Марша.\n\n"
            "Я не давлю.\n"
            "Я помогаю возвращаться без стыда.\n\n"
            "Мы будем усиливать устойчивость мягко,\n"
            "но системно.\n\n"
            "Даже если ты сорвёшься — я не исчезну."
        )
    },
    "skinny": {
        "who": "🐈‍⬛ Скинни — жёсткий тренер",
        "for_whom": (
            "Подходит, если:\n"
            "• нужен толчок\n"
            "• устал от разговоров\n"
            "• хочешь структуру и результат\n"
        ),
        "intro": (
            "Привет. Я Скинни.\n\n"
            "Я не обсуждаю бесконечно.\n"
            "Мы тренируем навык через действие.\n\n"
            "Минимум слов. Максимум выполнения.\n\n"
            "Сорвёшься — поднимем и продолжим.\n"
            "Но с дистанции не уйдёшь."
        )
    },
    "beck": {
        "who": "🧠 Бек — аналитический тренер",
        "for_whom": (
            "Подходит, если:\n"
            "• важно понимать, почему это работает\n"
            "• нужна логика и структура\n"
            "• хочешь видеть систему\n"
        ),
        "intro": (
            "Привет. Я Бек.\n\n"
            "Мы будем работать через модель.\n"
            "Я объясню, что происходит с вниманием,\n"
            "и какие функции мы тренируем.\n\n"
            "Если метод не подойдёт — адаптируем.\n"
            "Решение существует."
        )
    }
}

def trainer_say(trainer_key: str, text: str) -> str:
    t = TRAINERS.get(trainer_key, TRAINERS["marsha"])
    return f"{t['emoji']} *{t['name']}*: {text}"


def get_daytime_greeting() -> str:
    hour = datetime.now().hour

    if 5 <= hour < 12:
        return "Доброе утро"
    if 12 <= hour < 18:
        return "Добрый день"
    if 18 <= hour < 23:
        return "Добрый вечер"
    return "Привет"


def emotional_hook(day: int, progress: int) -> str:
    if day == 1:
        return "Ты уже начал. Это важнее, чем кажется."

    if day == 2:
        return "Мы не начинаем заново. Мы продолжаем."

    if progress >= 3:
        return f"Это уже {progress} запуск. Ты двигаешься."

    return "Важно не идеально. Важно - не выпадать."


async def send_trainer_introduction(m, u):
    trainer_key = u.get("trainer_key")
    if trainer_key not in TRAINER_INTRO_TEXT:
        return

    data = TRAINER_INTRO_TEXT[trainer_key]
    text = (
        f"{data['who']}\n\n"
        f"{data['for_whom']}\n"
        f"{data['intro']}\n\n"
        "Если стиль откликается — идём дальше."
    )
    await m.answer(trainer_say(trainer_key, text))


PRAISE = {
    "skinny": "Сделал. Факт есть. Это тренировка.",
    "marsha": "Это важно. Ты не бросил(а).",
    "beck": "Есть действие → есть обучение."
}

CRISIS_LIMIT = 3

# ============================================================
# TRAINER PRESENTATION & SELECTION
# ============================================================

TRAINER_INTRO_SCREEN = (
    "Перед тем как мы начнём,\n"
    "ты выберешь тренера.\n\n"
    "Это не просто стиль текста.\n"
    "Это то, КАК с тобой будут работать,\n"
    "поддерживать и вести дальше.\n\n"
    "Можно выбрать любого —\n"
    "если не подойдёт, мы сможем сменить."
)

# 🤍 Марша — поддержка и безопасность
TRAINER_MARSHA_DESC = (
    "🤍 Марша — мягкая и поддерживающая.\n\n"
    "Подойдёт, если ты часто винишь себя,\n"
    "быстро выгораешь или боишься не справиться.\n\n"
    "Она помогает возвращаться без стыда\n"
    "и не бросать после срывов."
)

# 🧱 Скинни — структура и давление на результат
TRAINER_SKINNY_DESC = (
    "🧱 Скинни — прямой и требовательный.\n\n"
    "Подойдёт, если нужен чёткий маршрут,\n"
    "жёсткие рамки и меньше разговоров.\n\n"
    "Он не давит на самооценку,\n"
    "он давит на выполнение."
)

# 🧠 Бек — объяснение и логика
TRAINER_BECK_DESC = (
    "🧠 Бек — аналитичный и спокойный.\n\n"
    "Подойдёт, если тебе важно понимать,\n"
    "что с тобой происходит и почему это работает.\n\n"
    "Он объясняет модель и даёт структуру,\n"
    "на которую можно опереться."
)

# Экран выбора тренера (с кнопками)
TRAINER_CHOICE_TEXT = (
    "Выбери тренера.\n\n"
    "Ты будешь работать с ним каждый день.\n"
    "Это можно изменить позже."
)

# Кнопки для выбора тренера
TRAINER_BUTTONS = {
    "marsha": "🤍 Марша — поддержка",
    "skinny": "🧱 Скинни — жёстко",
    "beck": "🧠 Бек — объясняю",
}

MODE_CHOICE_TEXT = (
    "Ещё один выбор перед стартом.\n\n"
    "Как тебе сейчас лучше заходить в работу?\n\n"
    "🌱 Бережно - если много давления, тревоги или усталости\n"
    "⚙️ Стандартно - если нужен обычный рабочий ритм\n"
    "🔥 Собранно - если хочешь прямее и жёстче\n\n"
    "Это не навсегда. Потом можно поменять."
)

# ============================================================
# 🐈 TRAINER PRESENTATION BLOCK
# ============================================================

TRAINER_INTRO_TEXT = {
    "marsha": {
        "who": "🤍 Марша — мягкий тренер",
        "for_whom": (
            "Подходит, если:\n"
            "• много самокритики\n"
            "• тревога мешает начинать\n"
            "• давление только усиливает срыв\n"
        ),
        "intro": (
            "Привет. Я Марша.\n\n"
            "Я не давлю.\n"
            "Я помогаю возвращаться без стыда.\n\n"
            "Мы будем усиливать устойчивость мягко,\n"
            "но системно.\n\n"
            "Даже если ты сорвёшься — я не исчезну."
        )
    },
    "skinny": {
        "who": "🐈‍⬛ Скинни — жёсткий тренер",
        "for_whom": (
            "Подходит, если:\n"
            "• нужен толчок\n"
            "• устал от разговоров\n"
            "• хочешь структуру и результат\n"
        ),
        "intro": (
            "Привет. Я Скинни.\n\n"
            "Я не обсуждаю бесконечно.\n"
            "Мы тренируем навык через действие.\n\n"
            "Минимум слов. Максимум выполнения.\n\n"
            "Сорвёшься — поднимем и продолжим.\n"
            "Но с дистанции не уйдёшь."
        )
    },
    "beck": {
        "who": "🧠 Бек — аналитический тренер",
        "for_whom": (
            "Подходит, если:\n"
            "• важно понимать, почему это работает\n"
            "• нужна логика и структура\n"
            "• хочешь видеть систему\n"
        ),
        "intro": (
            "Привет. Я Бек.\n\n"
            "Мы будем работать через модель.\n"
            "Я объясню, что происходит с вниманием,\n"
            "и какие функции мы тренируем.\n\n"
            "Если метод не подойдёт — адаптируем.\n"
            "Решение существует."
        )
    }
}

def trainer_confirm_text(trainer_key: str) -> str:
    """Мини-подтверждение после выбора тренера"""
    if trainer_key == "marsha":
        return (
            "🤍 Хороший выбор.\n"
            "Мы будем двигаться мягко,\n"
            "без давления и самокритики."
        )
    if trainer_key == "skinny":
        return (
            "🧱 Ок.\n"
            "Будем работать чётко и по плану.\n"
            "Без лишних разговоров."
        )
    return (
        "🧠 Отлично.\n"
        "Я буду объяснять,\n"
        "что происходит и зачем мы это делаем."
    )

# ============================================================
# TEST QUESTIONS (для быстрого узнавания bucket)
# ============================================================

TEST_QUESTIONS = [
    {
        "id": 1,
        "text": "Ты собираешься что-то сделать — но не делаешь. Что чаще всего происходит?",
        "options": {
            "anxiety": "Голова начинает гонять мысли — а вдруг не так, а вдруг не выйдет",
            "low_energy": "Просто нет энергии. Тело как будто против",
            "distractibility": "Начинаю — и через минуту уже занят чем-то другим",
            "mixed": "По-разному. Иногда одно, иногда другое"
        }
    },
    {
        "id": 2,
        "text": "Что даётся хуже всего?",
        "options": {
            "low_energy": "Начать. Вообще сдвинуться с места",
            "distractibility": "Удержаться на одном деле до конца",
            "anxiety": "Выключить голову и просто сделать",
            "mixed": "Всё примерно одинаково тяжело"
        }
    },
    {
        "id": 3,
        "text": "Снова не вышло. Что первым появляется в голове?",
        "options": {
            "anxiety": "Ну вот, я снова подвёл(а) себя",
            "low_energy": "Я просто слишком вымотан(а) для этого",
            "distractibility": "Ну я же знал(а), что не смогу сосредоточиться",
            "mixed": "Что-то со мной не так — но не пойму что именно"
        }
    },
    {
        "id": 4,
        "text": "Утро. Список дел. Что дальше?",
        "options": {
            "anxiety": "Начинаю думать, что не успею — ещё до того, как начал(а)",
            "low_energy": "Смотрю на него и откладываю на потом",
            "distractibility": "Берусь, переключаюсь, снова берусь",
            "mixed": "Зависит от дня — нет одного сценария"
        }
    },
    {
        "id": 5,
        "text": "Если бы всё наладилось — что изменилось бы первым?",
        "options": {
            "low_energy": "Я просто брал(а) и делал(а), без этой тяжести",
            "distractibility": "Я наконец доводил(а) хоть что-то до конца",
            "anxiety": "Голова была бы тише — меньше прокручивания",
            "mixed": "Просто несколько дней подряд было бы стабильно"
        }
    }
]

def resolve_bucket_from_test(answers: list) -> str:
    """Определить bucket по ответам на тест"""
    from collections import Counter
    c = Counter(answers)
    if c:
        return c.most_common(1)[0][0]
    return "mixed"

def create_test_question_keyboard(question_id: int) -> InlineKeyboardMarkup:
    """Создать клавиатуру для вопроса теста"""
    q = next((x for x in TEST_QUESTIONS if x["id"] == question_id), None)
    if not q:
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Ошибка", callback_data="noop")]])
    
    buttons = []
    for bucket_key, option_text in q["options"].items():
        buttons.append([InlineKeyboardButton(text=option_text, callback_data=f"test_q{question_id}_{bucket_key}")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _skill_format_parts(skill: dict):
    goal = skill.get("goal") or ""
    step1 = skill.get("step1") or ""
    step2 = skill.get("step2") or ""
    step3 = skill.get("step3") or ""

    if not any([step1, step2, step3]):
        raw_steps = skill.get("simple") or skill.get("steps") or []
        if raw_steps:
            step1 = raw_steps[0] if len(raw_steps) > 0 else ""
            step2 = raw_steps[1] if len(raw_steps) > 1 else ""
            step3 = raw_steps[2] if len(raw_steps) > 2 else ""
        elif skill.get("how"):
            step1 = skill.get("how") or ""

    micro = skill.get("micro") or skill.get("minimum") or step1
    why = skill.get("why_short") or skill.get("explain") or ""
    return goal, step1, step2, step3, micro, why


def skill_explain(trainer_key: str, skill: dict) -> str:
    goal, step1, step2, step3, micro, why = _skill_format_parts(skill)
    if not why:
        why = "Это снижает порог входа и помогает не выпасть сразу."

    parts = []

    if goal:
        parts.append(f"🎯 Зачем: {goal}")

    if step1:
        parts.append(f"\n👉 Делай раз: {step1}")
    if step2:
        parts.append(f"👉 Делай два: {step2}")
    if step3:
        parts.append(f"👉 Делай три: {step3}")
    if micro:
        parts.append(f"\n⚡ Минимум: {micro}")
    if why:
        parts.append(f"\n🧠 Почему это работает: {why}")

    return "\n".join(parts)

# Раскрытая подача навыка для кнопки «ℹ️ Подробнее»
TRACK_RATIONALE = {
    "anxiety": "Останавливает тревожный цикл и возвращает в действие через микрошаг.",
    "low_energy": "Снижает порог входа: начинаем без мотивации и не выгораем.",
    "distractibility": "Сужает поток стимулов и тренирует быстрый возврат внимания.",
    "mixed": "Базовые навыки для возврата, ясности и мягкого старта при прокрастинации.",
}

def skill_detail_text(skill: dict) -> str:
    """Форматирует навык в стандартный вид: Зачем / Делай раз / Минимум / Почему"""
    name = skill.get("name", "Навык")
    goal, step1, step2, step3, micro, why = _skill_format_parts(skill)
    if not why:
        why = "Это снижает порог входа и помогает не выпасть сразу."

    parts = [f"🧩 {name}"]

    if goal:
        parts.append(f"\n🎯 Зачем: {goal}")

    if step1:
        parts.append(f"\n👉 Делай раз: {step1}")
    if step2:
        parts.append(f"👉 Делай два: {step2}")
    if step3:
        parts.append(f"👉 Делай три: {step3}")

    if micro:
        parts.append(f"\n⚡ Минимум: {micro}")

    if why:
        parts.append(f"\n🧠 Почему это работает: {why}")

    return "\n".join(parts)

# ============================================================
# 3) KEYBOARDS
# ============================================================

kb_input_mode = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧠 Диагностика текстом")],
        [KeyboardButton(text="🎙 Диагностика голосом")],
        [KeyboardButton(text="❓ Быстрый тест (5 вопросов)")],
    ],
    resize_keyboard=True,
)

kb_trainers = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🐈‍⬛ Скинни (жёстко)")],
        [KeyboardButton(text="🐈 Марша (мягко)")],
        [KeyboardButton(text="🐈‍🦁 Бек (аналитично)")],
    ],
    resize_keyboard=True,
)

kb_mode_choice = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🌱 Бережно")],
        [KeyboardButton(text="⚙️ Стандартно")],
        [KeyboardButton(text="🔥 Собранно")],
    ],
    resize_keyboard=True,
)

# ============================================================
# EXTRA KEYBOARDS — Training / Crisis / Payment options
# ============================================================

kb_training_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💪 Сделать шаг"), KeyboardButton(text="↩️ Вернуться")],
    ],
    resize_keyboard=True
)

kb_crisis_mode = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎙 Кризис голосом")],
        [KeyboardButton(text="✍️ Кризис текстом")],
        [KeyboardButton(text="⬅️ Назад")],
    ],
    resize_keyboard=True
)

# Keyboard shown after user requests more details — allows asking for clarification
kb_more_clarify = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Ты меня не понял")],
        [KeyboardButton(text="⬅️ Назад")],
    ],
    resize_keyboard=True
)

kb_doubt_response = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👍 Понял(а), продолжаем")],
        [KeyboardButton(text="📚 Подробнее почему это работает")],
    ],
    resize_keyboard=True
)

kb_yes_no = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="✅ Да"), KeyboardButton(text="❌ Нет")]],
    resize_keyboard=True
)

kb_morning_checkin = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="тревожно"), KeyboardButton(text="не хочу начинать")],
        [KeyboardButton(text="пусто / нет сил"), KeyboardButton(text="отвлекаюсь")],
        [KeyboardButton(text="нормально, идём")],
        [KeyboardButton(text="напишу сам")],
    ],
    resize_keyboard=True,
)

kb_evening_close = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Что-то получилось")],
        [KeyboardButton(text="🧱 Было тяжело")],
        [KeyboardButton(text="↩️ Срывался(ась), но возвращался(ась)")],
        [KeyboardButton(text="✍️ Напишу сам")],
    ],
    resize_keyboard=True,
)

kb_reactivation = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="↩️ Вернуться с сегодняшнего дня")],
        [KeyboardButton(text="🎯 Взять самый простой навык")],
        [KeyboardButton(text="🌱 Нужен мягкий вход")],
    ],
    resize_keyboard=True,
)

kb_soft_return = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🌱 Вернуться без давления")],
        [KeyboardButton(text="🎯 Взять самый простой навык")],
    ],
    resize_keyboard=True,
)


def reactivation_soft_return(trainer_key: str, name: str = "", skill_step: str = "") -> str:
    who = f"{name},\n\n" if name else ""
    step = skill_step or "открыть задачу на 2 минуты"
    bank = {
        "marsha": (
            f"{who}Ты пропал(а) — это нормально.\n\n"
            "Обычно это происходит в одном из мест:\n"
            "— стало тяжело\n"
            "— стало мутно\n"
            "— стало не до этого\n\n"
            "Давай не разгонять.\n\n"
            f"👉 Вернись с одного маленького шага:\n{step}"
        ),
        "skinny": (
            f"{who}Пропал(а). Ок.\n\n"
            "Причин обычно три:\n"
            "— стало тяжело\n"
            "— стало мутно\n"
            "— стало не до этого\n\n"
            f"Не разбираем. Просто один шаг:\n{step}"
        ),
        "beck": (
            f"{who}Пауза зафиксирована.\n\n"
            "Типичные точки разрыва:\n"
            "— нагрузка стала слишком высокой\n"
            "— задача потеряла ясность\n"
            "— внешние события вытеснили практику\n\n"
            f"Возврат не требует объяснений. Один шаг:\n{step}"
        ),
    }
    return bank.get(trainer_key) or bank["marsha"]


def reactivation_6h(trainer_key: str, name: str = "") -> str:
    who = f"{name}, " if name else ""
    bank = {
        "marsha": [
            f"{who}всё хорошо, просто проверяю. Как ты?",
            f"{who}тихо у тебя. Не нужно ничего делать — можно просто вернуться.",
            f"{who}ничего не горит. Просто если захочешь — я здесь.",
        ],
        "skinny": [
            f"{who}давно не видно. Один короткий заход — и день засчитан.",
            f"{who}долго нет. Без рывка — один шаг сейчас.",
            f"{who}появись. 60 секунд, и можно идти дальше.",
        ],
        "beck": [
            f"{who}тишина больше 6 часов. Один микро-шаг уменьшит вечерний откат.",
            f"{who}небольшая пауза засчитана. Возврат сейчас даст системе сигнал.",
            f"{who}прошло 6 часов. Возврат занимает меньше, чем кажется.",
        ],
    }
    phrases = bank.get(trainer_key) or bank["marsha"]
    return random.choice(phrases)


def reactivation_24h(trainer_key: str, name: str = "") -> str:
    who = f"{name}, " if name else ""
    bank = {
        "marsha": [
            f"{who}прошёл целый день. Я никуда не делась — и ты тоже. Готов(а) вернуться?",
            f"{who}бывает, что день выпадает. Это нормально. Давай мягко войдём обратно.",
            f"{who}день прошёл. Без упрёков — просто небольшой шаг сегодня.",
        ],
        "skinny": [
            f"{who}24 часа нет. Один шаг прямо сейчас закрывает паузу.",
            f"{who}пропустил(а) день — не страшно. Пять минут, и снова в ритме.",
            f"{who}24 часа. Напиши «держу» или сделай один шаг.",
        ],
        "beck": [
            f"{who}прошло 24 часа. Это не провал, это пауза. Возврат в любой момент работает.",
            f"{who}день без тренировки — данные, не оценка. Войдём обратно коротко.",
            f"{who}24 часа — это не разрыв паттерна, если войти сейчас.",
        ],
    }
    phrases = bank.get(trainer_key) or bank["marsha"]
    return random.choice(phrases)


def reactivation_3d(trainer_key: str, name: str = "") -> str:
    who = f"{name}.\n\n" if name else ""
    bank = {
        "marsha": [
            (
                f"{who}Ты не провалил(а) программу.\n"
                "Ты просто выпал(а) из ритма.\n\n"
                "Это случается. Правда, часто.\n"
                "И это поправимо — без перезапуска с нуля."
            ),
            (
                f"{who}Три дня — это не потеря.\n"
                "Это пауза. А пауза — часть любого процесса.\n\n"
                "Можно войти обратно мягко: не рывком, просто одним маленьким шагом."
            ),
        ],
        "skinny": [
            (
                f"{who}Три дня нет. Без лекции.\n"
                "Выпал(а) — окей. Сейчас нужен один шаг.\n"
                "Выбирай 👇"
            ),
            (
                f"{who}Три дня — паузу услышал(а).\n"
                "Программа всё ещё здесь. Войди обратно: коротко, без нажима."
            ),
        ],
        "beck": [
            (
                f"{who}Трёхдневная пауза — это не разрыв навыка.\n"
                "Мозг хранит паттерн дольше, чем кажется.\n\n"
                "Возврат сейчас — это не начало заново, это продолжение."
            ),
            (
                f"{who}Три дня без практики: паттерн ослаб, но не исчез.\n"
                "Один возврат сейчас восстанавливает цепочку."
            ),
        ],
    }
    phrases = bank.get(trainer_key) or bank["marsha"]
    return random.choice(phrases)


def reactivation_7d(trainer_key: str, name: str = "") -> str:
    who = f"{name}.\n\n" if name else ""
    bank = {
        "marsha": [
            (
                f"{who}Недели не было слышно.\n"
                "Я не ищу виноватых — ни тебя, ни программу.\n\n"
                "Просто скажи: ты ещё здесь?\n"
                "Можем начать заново — мягко, с любого места."
            ),
            (
                f"{who}Семь дней — это большая пауза.\n"
                "Но это не конец. Всё, что ты делал(а) до этого — никуда не пропало.\n\n"
                "Можно войти обратно. Без давления, когда будешь готов(а)."
            ),
        ],
        "skinny": [
            (
                f"{who}Неделя молчания. Без претензий.\n"
                "Если ты здесь — давай коротко. Один шаг, и снова в ритме."
            ),
            (
                f"{who}7 дней нет. Программа не закрыта.\n"
                "Готов(а) вернуться — выбирай способ 👇"
            ),
        ],
        "beck": [
            (
                f"{who}Семь дней вне практики. Паттерн ослаб, но не удалён.\n"
                "Мягкий перезапуск с минимального навыка — самый эффективный путь."
            ),
            (
                f"{who}Неделя без тренировки — нормальная нелинейность процесса.\n"
                "Возврат сейчас важнее, чем думать о пропущенном времени."
            ),
        ],
    }
    phrases = bank.get(trainer_key) or bank["marsha"]
    return random.choice(phrases)

MORNING_CHECKIN_OPENERS = {
    "marsha": [
        "Доброе утро. Я рядом.",
        "Привет. Давай мягко войдём в день.",
        "Начинаем спокойно. Без рывков.",
    ],
    "skinny": [
        "Утро. Входим в рабочий режим.",
        "Новый день. Нужен короткий фокус.",
        "Стартуем без разгона и драмы.",
    ],
    "beck": [
        "Утро. Зафиксируем состояние перед стартом.",
        "Начнём с короткой калибровки.",
        "Сейчас определим фон и выберем вход в задачу.",
    ],
}

MORNING_CHECKIN_ACKS = {
    "marsha": {
        "anxious": "Поняла. Тогда идём очень маленьким шагом, чтобы снизить шум.",
        "resistant": "Ок. Не уговариваю. Давай просто начнём с минимума.",
        "empty": "Слышу. Сегодня бережный режим и короткий вход.",
        "distracted": "Хорошо. Значит, делаем коротко и с мягким возвратом.",
        "ok": "Отлично. Тогда спокойно идём в задачу.",
        "custom": "Приняла. Подстроимся под это состояние.",
    },
    "skinny": {
        "anxious": "Принял. Убираем лишнее и делаем короткий заход.",
        "resistant": "Нормально. Хочется или нет - делаем минимальный старт.",
        "empty": "Ок. Нулевой режим: один короткий шаг.",
        "distracted": "Понял. Работаем короткими отрезками.",
        "ok": "Хорошо. Тогда без пауз, начинаем.",
        "custom": "Принял. План не меняем: коротко и по делу.",
    },
    "beck": {
        "anxious": "Понял. При тревоге лучше работает маленький предсказуемый шаг.",
        "resistant": "Принято. Начнём с минимального действия, чтобы запустить цикл.",
        "empty": "Понял. При низкой энергии важен короткий и простой вход.",
        "distracted": "Ясно. Тогда опора на короткие блоки и возврат в фокус.",
        "ok": "Отлично. Состояние рабочее, можно идти дальше.",
        "custom": "Принято. Используем это как входные данные на сегодня.",
    },
}


def get_morning_checkin_opener(trainer_key: str) -> str:
    bank = MORNING_CHECKIN_OPENERS.get(trainer_key) or MORNING_CHECKIN_OPENERS.get("marsha", [])
    return random.choice(bank) if bank else "Доброе утро."


def get_morning_checkin_ack(trainer_key: str, mood_key: str) -> str:
    bank = MORNING_CHECKIN_ACKS.get(trainer_key) or MORNING_CHECKIN_ACKS.get("marsha", {})
    return bank.get(mood_key) or bank.get("custom") or "Принято. Идём дальше."


def daytime_ping(trainer_key: str, name: str = "") -> str:
    who = f"{name}, " if name else ""
    bank = {
        "marsha": [
            f"{who}если застрял(а), давай просто один маленький возврат.",
            f"{who}без рывка. Один короткий шаг, и уже хорошо.",
            f"{who}можно мягко вернуться: 60 секунд на задачу.",
        ],
        "skinny": [
            f"{who}короткий заход. 60 секунд и свободен.",
            f"{who}без разгона: один шаг прямо сейчас.",
            f"{who}если выпал(а) - просто вернись на минуту.",
        ],
        "beck": [
            f"{who}короткий возврат сейчас уменьшит вечерний откат.",
            f"{who}один микро-шаг даст системе сигнал ""я в процессе"".",
            f"{who}проверим минимум: 60-120 секунд действия.",
        ],
    }
    phrases = bank.get(trainer_key) or bank["marsha"]
    return random.choice(phrases)


def evening_close_question(trainer_key: str) -> str:
    intro = {
        "marsha": "Перед сном коротко:",
        "skinny": "Закроем день одним вопросом:",
        "beck": "Короткая фиксация дня:",
    }.get(trainer_key, "Коротко на вечер:")
    question = random.choice([
        "Что сегодня получилось хотя бы частично?",
        "Где сегодня было труднее всего?",
    ])
    return f"{intro}\n{question}"


def evening_close_coach_reply(trainer_key: str, user_text: str) -> str:
    low = (user_text or "").lower()
    hard = any(x in low for x in ["тяж", "слож", "не выш", "не смог", "застр", "провал"])
    partial = any(x in low for x in ["получ", "сделал", "шаг", "чуть", "немного", "частично"])
    returned = any(x in low for x in ["вернул", "срыв", "собрал", "начал заново"])

    if trainer_key == "skinny":
        if returned:
            return "Возврат засчитан. Это сильный ход."
        if partial:
            return "Факт есть. Этого достаточно на сегодня."
        if hard:
            return "Ок, день был тяжёлый. Завтра берём минимум и входим коротко."
        return "Принял. День закрыт, завтра продолжаем."

    if trainer_key == "beck":
        if returned:
            return "Отлично, возврат сработал. Это ключевая метрика устойчивости."
        if partial:
            return "Хорошая фиксация. Частичный результат тоже укрепляет паттерн."
        if hard:
            return "Понял. Сегодняшняя сложность - полезные данные для настройки завтра."
        return "Принято. Закрываем день и оставляем короткий вход на утро."

    if returned:
        return "Ты всё равно вернулся(лась). Это правда важно."
    if partial:
        return "Даже частично - уже движение. Бережно закрываем день."
    if hard:
        return "Понимаю. День был непростой. Завтра начнём с очень маленького шага."
    return "Спасибо, что поделился(ась). На сегодня достаточно."

# ============================================================
# Анализ подтверждение + уточнение
# ============================================================

kb_analysis_confirm = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Да, в точку")],
        [KeyboardButton(text="🤔 Немного не так")],
        [KeyboardButton(text="📚 Подробнее")],
    ],
    resize_keyboard=True
)

kb_analysis_contract = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📜 Принимаю контракт")],
        [KeyboardButton(text="🤔 Немного не так")],
    ],
    resize_keyboard=True,
)

kb_analysis_map = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📜 Принимаю план")],
        [KeyboardButton(text="🤔 Немного не так")],
    ],
    resize_keyboard=True,
)

kb_pay_choice = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💳 Оплатить со скидкой")],
        [KeyboardButton(text="💳 Оплатить без скидки")],
        [KeyboardButton(text="➕ Ещё 4 дня без оплаты")],
        [KeyboardButton(text="❌ Не готов(а)")],
    ],
    resize_keyboard=True
)

kb_payment_continue = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💳 Продолжить")],
        [KeyboardButton(text="🤔 Пока подумаю")],
    ],
    resize_keyboard=True
)

# ============================================================
# PATCH: Simplified 2-3 button navigation
# ============================================================

kb_skill_entry = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💪 Давай тренировать навык")],
        [KeyboardButton(text="ℹ️ Подробнее про навык")],
        [KeyboardButton(text="🆘 Кризис")],
    ],
    resize_keyboard=True,
)

kb_training_run = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Сделал(а)")],
        [KeyboardButton(text="↩️ Вернулся(лась)")],
        [KeyboardButton(text="🆘 Кризис")],
    ],
    resize_keyboard=True,
)

kb_skill_more = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💪 Давай тренировать навык")],
        [KeyboardButton(text="⬅️ Назад")],
    ],
    resize_keyboard=True,
)

kb_after_return = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💪 Ещё один круг")],
        [KeyboardButton(text="🌙 На сегодня достаточно")],
    ],
    resize_keyboard=True,
)

kb_pay_simple = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💳 Продолжить")],
        [KeyboardButton(text="🤔 Пока нет")],
    ],
    resize_keyboard=True,
)

def payment_inline_discount(payment_url_discount: str) -> InlineKeyboardMarkup:
    if not payment_url_discount:
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Скидка: ссылка не настроена", callback_data="noop")]]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Оплатить со скидкой", url=payment_url_discount)]]
    )

def payment_inline_full(payment_url_full: str) -> InlineKeyboardMarkup:
    if not payment_url_full:
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Полная: ссылка не настроена", callback_data="noop")]]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Оплатить без скидки", url=payment_url_full)]]
    )

kb_yes_no_inline = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data="yes")],
        [InlineKeyboardButton(text="❌ Нет", callback_data="no")],
    ]
)

def payment_inline(payment_url: str) -> InlineKeyboardMarkup:
    if not payment_url:
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Ссылка на оплату не настроена", callback_data="noop")]]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Оплатить", url=payment_url)]]
    )

ONBOARDING_SCREENS = [
    (
        "Ты, скорее всего, уже пробовал.\n\n"
        "И всё равно происходит одно и то же:\n"
        "знаешь, что делать — но не начинаешь.\n\n"
        "Это не лень.\n\n"
        "С этим можно работать."
    ),
]

# ============================================================
# 7) SALES & ONBOARDING TEXTS (карта, гарантия, таймеры)
# ============================================================

def month_map_short(bucket: str) -> str:
    """Короткая версия месячной карты (показываем сразу)"""
    return (
        "🗺 Твоя карта на ближайший месяц:\n\n"
        "Неделя 1 — стабилизация\n"
        "Научимся возвращаться без самокритики и запускать действия.\n\n"
        "Неделя 2 — контроль\n"
        "Начнём удерживать внимание и снижать сопротивление.\n\n"
        "Неделя 3 — устойчивость\n"
        "Меньше срывов, больше предсказуемости.\n\n"
        "Неделя 4 — закрепление\n"
        "Навыки начинают работать автоматически.\n\n"
        "Это не марафон. Это тренировка системы."
    )

def month_map_full(bucket: str) -> str:
    """Подробная версия месячной карты (по кнопке «Подробнее»)"""
    return (
        "🗺 Подробная карта тренировки:\n\n"
        "🔹 Неделя 1 — Стабилизация\n"
        "• возвращаться к задаче без самонаказания\n"
        "• запускать действие даже без мотивации\n\n"
        "🔹 Неделя 2 — Контроль\n"
        "• удерживать внимание дольше\n"
        "• не срываться при дискомфорте\n\n"
        "🔹 Неделя 3 — Устойчивость\n"
        "• меньше откатов\n"
        "• меньше внутреннего давления\n\n"
        "🔹 Неделя 4 — Закрепление\n"
        "• навыки работают без постоянного контроля\n"
        "• появляется ощущение управляемости\n\n"
        "Мы будем адаптировать маршрут, если что-то не подойдёт."
    )

# 🔒 ГАРАНТИЯ (универсальная, не страшная)

GUARANTEE_TEXT = (
    "🔒 Наша гарантия:\n\n"
    "Мы не обещаем «исцеление» или быстрые чудеса.\n\n"
    "Мы гарантируем:\n"
    "• понятный план\n"
    "• сопровождение\n"
    "• адаптацию навыков под тебя\n\n"
    "Если навык не работает — мы его меняем.\n"
    "Если формат не заходит — упрощаем.\n\n"
    "Ты не останешься один(одна) с задачей."
)

GUARANTEE_SHORT = (
    "Если что-то не работает — мы это меняем.\n"
    "Ты не застрянешь один(одна)."
)

# 💰 ТАЙМЕРЫ И ДЕДЛАЙНЫ (продающие, но человеческие)

def offer_day_3(name: str) -> str:
    """Текст дня 3 — основной дожим со скидкой"""
    return (
        f"{name}, ты уже не в теории.\n\n"
        "Ты потренировал(а) навык.\n"
        "И заметил(а), что:\n"
        "• стало чуть легче возвращаться\n"
        "• меньше внутреннего давления\n\n"
        "Чтобы это стало устойчивым,\n"
        "обычно нужно несколько недель.\n\n"
        "💰 Сейчас ты можешь продолжить со скидкой.\n"
        "Она доступна ещё 4 дня."
    )

def offer_day_7(name: str) -> str:
    """Текст дня 7 — последний дедлайн по скидке"""
    return (
        f"{name}, напоминаю.\n\n"
        "Скидка заканчивается сегодня.\n\n"
        "Если хочешь продолжить системно —\n"
        "это последний день по сниженной цене.\n\n"
        "Если не готов(а) — всё ок.\n"
        "Ты уже знаешь, как это работает."
    )

REMINDER_AFTER_DECLINE = (
    "Просто напомню.\n\n"
    "Ты начал(а) тренировать навык.\n"
    "И это уже шаг.\n\n"
    "Если захочешь вернуться — я здесь."
)

# ============================================================
# 7.5) АНАЛИЗ → КОНТРАКТ → ПУТЬ (финальный продающий текст)
# ============================================================

def analysis_contract_short(name: str, trainer_key: str, bucket: str) -> str:
    """Короткая версия контракта (показывается всегда после анализа)"""
    base = {
        "anxiety": "ты часто не начинаешь из-за напряжения и ожидания угрозы",
        "low_energy": "тебе сложно начинать из-за истощения и перегруза",
        "distractibility": "ты начинаешь, но внимание быстро уносит",
        "mixed": "у тебя смешанный профиль — и старт, и удержание даются тяжело",
    }.get(bucket, "есть сложности с саморегуляцией")

    trainer_tone = {
        "marsha": (
            f"{name}, я вижу, как это выматывает.\n"
            "Это не слабость и не лень — это перегруженная система.\n\n"
            "Хорошая новость: это тренируется. И я буду рядом."
        ),
        "skinny": (
            f"{name}, проблема не в характере.\n"
            "Не хватает натренированных функций.\n\n"
            "Мы это исправим через действия. Без лишних слов."
        ),
        "beck": (
            f"{name}, то, что с тобой происходит — распространённый паттерн.\n"
            "Он хорошо описан и поддаётся тренировке.\n\n"
            "Дальше будет структура."
        ),
    }[trainer_key]

    return (
        f"🧠 Что я вижу:\n"
        f"Похоже, что {base}.\n\n"
        f"{trainer_tone}\n\n"
        "Это решаемо.\n"
        "Но не за один день."
    )


def analysis_contract_long(name: str, trainer_key: str, bucket: str) -> str:
    """Подробная версия контракта (по кнопке «Подробнее»)"""
    trainer_finish = {
        "marsha": "Даже если что-то не пойдёт — мы подстроим путь. Ты не останешься один.",
        "skinny": "Если метод не сработает — заменим. Но ты дойдёшь.",
        "beck": "Программа адаптируется под обратную связь. Это часть протокола.",
    }[trainer_key]

    return (
        f"🔍 {name}, разложу по шагам:\n\n"
        "1️⃣ Что происходит\n"
        "Навыки саморегуляции сейчас не выдерживают нагрузку.\n\n"
        "2️⃣ Почему так\n"
        "Не из-за лени и не из-за воли — функции просто не натренированы.\n\n"
        "3️⃣ Почему это решаемо\n"
        "Эти навыки тренируются так же, как мышцы.\n\n"
        "4️⃣ Как мы будем работать\n"
        "Не мотивацией, а регулярными микро-тренировками.\n\n"
        "5️⃣ Сроки\n"
        "Первые изменения — через 2–3 недели.\n"
        "Устойчивость — 4–8 недель.\n\n"
        f"{trainer_finish}\n\n"
        "Мы будем идти шаг за шагом."
    )

# Алиас для использования в bot.py
contract_full_text = analysis_contract_long

def month_map_text(bucket: str) -> str:
    """Карта тренировки на месяц (показывается сразу после анализа)"""
    return (
        "🗺 КАРТА 4 НЕДЕЛЬ\n\n"
        "1️⃣ Стабилизация — возврат и запуск\n"
        "2️⃣ Работа с тревогой / вниманием\n"
        "3️⃣ Работа с самокритикой\n"
        "4️⃣ Удержание системы\n\n"
        "Это не случайные упражнения.\n"
        "Это последовательная перестройка.\n"
    )

def guarantee_block(trainer_key: str) -> str:
    """Гарантийный блок"""
    if trainer_key == "skinny":
        return (
            "🐈‍⬛ Я не брошу тебя, даже если сорвёшься.\n"
            "Срыв — часть тренировки.\n"
            "Метод не пойдёт — заменим.\n"
            "Результат будет."
        )

    if trainer_key == "beck":
        return (
            "🧠 Если метод не даст эффекта,\n"
            "мы адаптируем программу.\n"
            "Система гибкая.\n"
            "Решение существует."
        )

    return (
        "🌿 Даже если будет откат — это нормально.\n"
        "Я буду рядом.\n"
        "Мы подстроим план.\n"
        "Ты не останешься один."
    )

MONTH_CONTRACT_TEXT = (
    "📄 Контракт на работу:\n\n"
    "• срок: 1 месяц\n"
    "• цель: натренировать навыки саморегуляции\n"
    "• формат: ежедневные микро-действия\n"
    "• срывы: допустимы\n"
    "• адаптация: гарантирована\n\n"
    "Ты не обязан быть мотивирован.\n"
    "Ты обязан возвращаться.\n\n"
    "Готов начать путь?"
)

def offer_day_3_text(u: dict) -> str:
    """Усиленный дожим после 3 дней (на основе фактов)"""
    done = u.get("done_count", 0)
    ret = u.get("return_count", 0)

    return (
        "💳 Ты уже сделал(а) реальные шаги:\n\n"
        f"✅ попытки: {done}\n"
        f"↩️ возвраты: {ret}\n\n"
        "Это не «старался(ась)».\n"
        "Это и есть сдвиг.\n\n"
        "Если продолжить — эффект закрепится.\n"
        "Со скидкой — прямо сейчас."
    )

def inactivity_ping(trainer_key: str) -> str:
    """Авто-пинг через 24 часа неактивности"""
    return {
        "marsha": "Я рядом. Даже маленький возврат сегодня — уже достаточно.",
        "skinny": "Ты пропал. Возвращаемся. 60 секунд.",
        "beck": "Перерыв зафиксирован. Возврат сейчас снизит откат.",
    }.get(trainer_key, "Пора вернуться.")

def build_week_plan(user: dict) -> str:
    """План на неделю (показывается перед оплатой)"""
    return (
        "Я собрал тебе план на ближайшую неделю:\n\n"
        "День 1–2:\n"
        "→ учимся входить в задачу без перегруза\n\n"
        "День 3–4:\n"
        "→ уменьшаем зависание и отвлечение\n\n"
        "День 5–6:\n"
        "→ закрепляем возврат без самокритики\n\n"
        "День 7:\n"
        "→ собираем устойчивый режим\n\n"
        "👉 Это не теория.\n"
        "Это конкретные действия каждый день.\n\n"
        "И это только начало."
    )

def build_payment_offer(user: dict) -> str:
    """Предложение оплаты (фреймирование как продолжение, а не покупка)"""
    return (
        "Смотри, где ты сейчас:\n\n"
        "— мы уже разобрали, где ты застреваешь\n"
        "— ты уже сделал(а) первые шаги\n"
        "— ты не с нуля\n\n"
        "Дальше есть два варианта:\n\n"
        "1) оставить как есть\n"
        "→ и через пару дней всё вернётся как было\n\n"
        "2) продолжить системно\n"
        "→ и закрепить результат\n\n"
        "👉 Внутри программы:\n"
        "— понятный план на 10–12 недель\n"
        "— ежедневные микро-тренировки\n"
        "— адаптация под тебя\n\n"
        "Это не мотивация.\n"
        "Это система, которая доводит до результата.\n\n"
        "Хочешь продолжить?"
    )

def build_hesitation_response() -> str:
    """Ответ на сомнение 'пока подумаю' (закрыватель лазейки)"""
    return (
        "Ок.\n\n"
        "Скажу честно:\n"
        "чаще всего люди не продолжают не потому что не надо,\n"
        "а потому что откладывают.\n\n"
        "Если тебе откликнулось — лучше продолжить сейчас,\n"
        "пока ты в процессе."
    )

# ============================================================
# DAILY CHECK-IN TEXTS (Morning / Midday / Evening)
# ============================================================

def morning_checkin_text(trainer_key: str, name: str = "ты") -> str:
    """Утренний check-in: как ты себя чувствуешь?"""
    if trainer_key == "skinny":
        return (
            "Доброе утро.\n"
            "Новый день.\n\n"
            "Как ты себя сейчас чувствуешь?\n"
            "Коротко: есть силы / тяжело / пусто / тревожно."
        )
    if trainer_key == "beck":
        return (
            "Доброе утро.\n\n"
            "Перед стартом важно понять состояние.\n"
            "Как ты себя сейчас чувствуешь?\n"
            "Коротко, 1–2 слова."
        )
    return (
        "Доброе утро.\n\n"
        "Давай мягко начнём день.\n"
        "Как ты себя сейчас чувствуешь?\n"
        "Коротко: есть силы / тяжело / пусто / тревожно."
    )


def midday_checkin_text(trainer_key: str) -> str:
    """Полдневной check-in: как сейчас?"""
    if trainer_key == "skinny":
        return (
            "Как ты сейчас?\n\n"
            "Если день расползся — не страшно.\n"
            "Делаем короткий возврат."
        )
    if trainer_key == "beck":
        return (
            "Как ты сейчас?\n\n"
            "Это не полный перезапуск дня.\n"
            "Это просто точка возврата."
        )
    return (
        "Как ты сейчас?\n\n"
        "Если день уже поехал — ничего страшного.\n"
        "Давай просто коротко вернёмся."
    )


def evening_checkin_text(trainer_key: str) -> str:
    """Вечерний check-in: что получилось?"""
    if trainer_key == "skinny":
        return (
            "Вечер.\n\n"
            "Как у тебя дела?\n"
            "Коротко:\n"
            "— получилось\n"
            "— было сложно\n"
            "— выпал(а), но вернулся(лась)"
        )
    if trainer_key == "beck":
        return (
            "Вечер.\n\n"
            "Давай коротко зафиксируем день.\n"
            "Как у тебя дела?\n"
            "Что получилось, а где было сложнее?"
        )
    return (
        "Вечер.\n\n"
        "Как у тебя дела?\n"
        "Что сегодня получилось, а где было тяжело?"
    )


def evening_close_reply(trainer_key: str, user_text: str = "") -> str:
    """Ответ на вечерний check-in (поддержка, не стыд)"""
    low = (user_text or "").lower()

    if any(x in low for x in ["получ", "сделал", "смог", "вышло", "да"]):
        if trainer_key == "skinny":
            return "Ок. День не пустой. Это уже факт."
        if trainer_key == "beck":
            return "Хорошо. Значит, день дал не ноль, а конкретный результат."
        return "Это важно. День не потерян, в нём уже есть движение."

    if any(x in low for x in ["тяжело", "сложно", "не смог", "не вышло", "выпал", "нет"]):
        if trainer_key == "skinny":
            return "Ок. Значит, завтра идём ещё короче. День не обнуляем."
        if trainer_key == "beck":
            return "Понял. Это не провал, а данные о том, где система не выдерживает."
        return "Поняла. Это не значит, что день пропал. Это значит, что завтра нужен более бережный вход."

    if trainer_key == "skinny":
        return "Ок. День зафиксирован. Завтра продолжаем."
    if trainer_key == "beck":
        return "Хорошо. Зафиксировали день, завтра пойдём дальше."
    return "Спасибо. День зафиксирован. Завтра продолжим спокойно."

DAILY_LIVE_LINES = {
    "marsha": [
        "Ты стараешься больше, чем тебе кажется.",
        "Завтра будет чуть легче, чем сегодня."
    ],
    "skinny": [
        "Факт есть. Продолжаем.",
        "Ты делаешь — система работает."
    ],
    "beck": [
        "Процесс запущен. Это важно.",
        "Повторение формирует устойчивость."
    ],
}

# ============================================================
# TRAINER REPLY BANKS
# Сценарии: done | return | doubt | after_pause | crisis_entry | evening_close
# Получить случайную реплику: get_trainer_reply(trainer_key, scenario)
# ============================================================

TRAINER_REPLIES: dict = {
    "marsha": {
        "done": [
            "Получилось. Даже если было тяжело — получилось.",
            "Это не мелочь. За этим стоит усилие.",
            "Я рада. Ты двигаешься, даже когда непросто.",
            "Вот и всё. Сделал — и это уже много.",
            "Ты вернулся и сделал. Это важнее, чем кажется.",
            "Хорошо. Маленький шаг, но он реальный.",
            "Спасибо, что не бросил. Завтра будет чуть легче.",
            "Ты держишься. И это — самое главное.",
            "Сделано. Как тебе сейчас?",
            "Заметил(а)? Становится немного легче, чем было раньше.",
        ],
        "return": [
            "Ты вернулся — это и есть навык.",
            "Срыв не стирает всё предыдущее. Ты снова здесь.",
            "Хорошо, что написал(а). Возвращаемся без давления.",
            "Между побегом и возвратом ты выбрал(а) вернуться. Это считается.",
            "Всё нормально. Бывает. Идём дальше.",
            "Возврат без самонаказания — именно это мы и тренируем.",
            "Не важно, сколько прошло. Важно, что ты вернулся(лась).",
            "Я рада тебя видеть. Начнём с самого маленького шага.",
            "Это нормально — сбиваться. Ненормально — не возвращаться совсем. Ты возвращаешься.",
            "Ты здесь — этого уже достаточно, чтобы начать.",
        ],
        "doubt": [
            "Сомнение — не причина останавливаться. Попробуем 60 секунд и посмотрим.",
            "Не нужно верить, что это работает. Нужно просто попробовать.",
            "Понимаю. Если скажешь, что именно не верится — разберёмся вместе.",
            "Сомнение нормально. Особенно если раньше что-то не работало.",
            "Ты не обязан(а) быть уверен(а). Просто один следующий шаг.",
            "Мы не просим доверия — мы просим одну попытку.",
            "Расскажи, что именно кажется неправдой. Я услышу.",
            "Иногда сомнение — это способ не начинать. Давай начнём с самого маленького.",
            "Если бы оно точно не работало — ты бы уже закрыл(а). Но ты здесь.",
            "Продолжаем?",
        ],
        "after_pause": [
            "Ты не пропадал(а) — брал(а) паузу. Разница есть.",
            "Хорошо, что снова здесь. Начнём с самого простого.",
            "Перерыв — это не провал. Это часть любого пути.",
            "Я не буду спрашивать, где ты был(а). Давай просто вернёмся.",
            "Всё на месте. Выдохни — и сделаем один маленький шаг.",
            "Иногда нужна пауза. Главное — что ты вернулся(лась).",
            "Ничего не обнулилось. Начнём оттуда, где тебе сейчас комфортно.",
            "Долго не заходил(а) — и всё равно вернулся(лась). Это уже много.",
            "Без лекций. Как ты сейчас?",
            "Важно только одно: ты снова здесь. Идём.",
        ],
        "crisis_entry": [
            "Слышу тебя. Расскажи, что сейчас происходит.",
            "Я здесь. Не нужно объяснять всё сразу.",
            "Хорошо, что написал(а). Разберёмся вместе.",
            "Это трудный момент. Ты не один(одна).",
            "Сейчас важно одно: выдохни и скажи, что происходит.",
            "Я рядом. Без оценок, без давления.",
            "Расскажи своими словами — что сейчас тяжелее всего.",
            "Ты сделал(а) правильно, что обратился(лась). Слушаю.",
            "Сейчас не нужно быть в порядке. Просто побудь здесь.",
            "Слышу. Давай медленно — что происходит прямо сейчас?",
        ],
        "evening_close": [
            "День закрыт. Ты справился(лась) — в той мере, в которой мог(ла).",
            "Как ты сегодня?",
            "Сегодня было что-то хорошее — пусть даже маленькое.",
            "Отдыхай. Завтра — новый круг.",
            "Даже если день был тяжёлым, ты дошёл(дошла) до вечера. Этого достаточно.",
            "Не оценивай себя слишком строго. Сегодня ты делал(а) что мог(ла).",
            "До завтра. Я буду рядом.",
            "Отпусти этот день. Завтра начнём свежо.",
            "Ты сегодня постарался(ась). Этого достаточно.",
            "Ложись отдыхать. За сегодня можно не переживать.",
        ],
    },

    "skinny": {
        "done": [
            "Сделал(а). Есть факт.",
            "Зачёт. Идём дальше.",
            "Это и есть тренировка.",
            "Готово. Одно выполнение есть.",
            "Факт есть. Продолжаем.",
            "Сделал(а) — и это уже больше, чем ничего.",
            "Один шаг закрыт. Теперь следующий.",
            "Работа сделана. Точка.",
            "Молодец — без лишних слов. Идём.",
            "Оставь разбор на потом, сейчас просто зафиксируй.",
        ],
        "return": [
            "Вернулся(лась) — уже хорошо. Начинаем.",
            "Пауза была. Теперь — действие.",
            "Долго не было, неважно. Ты здесь — значит продолжаем.",
            "Без разбора полётов. Следующий шаг.",
            "Нет смысла объяснять. Нужно только начать.",
            "Возврат есть. Этого достаточно.",
            "Хватит тормозить — 60 секунд прямо сейчас.",
            "Возвращаться — это и есть система. Значит, тренируешься.",
            "Факт возврата засчитан. Двигаемся.",
            "Один раз сделал(а) — остальное потом.",
        ],
        "doubt": [
            "Сомнение — это не причина. Причина — действие.",
            "Проверяй делом, не головой.",
            "60 секунд. Потом можешь сомневаться.",
            "Если не веришь — проверь. Других способов нет.",
            "Думать будем потом. Сначала один шаг.",
            "Сомнения не работают. Действия — работают.",
            "Это не вопрос веры. Это вопрос повторения.",
            "Понял(а) сомнение. Игнорируем, делаем.",
            "Не нужно верить. Нужно попробовать.",
            "Сомневаешься — нормально. Начни и проверь сам(а).",
        ],
        "after_pause": [
            "Долго не было. Неважно. Начинаем.",
            "Пауза окончена. Возврат засчитан.",
            "Всё остальное неважно. Один шаг — прямо сейчас.",
            "Пришёл(пришла) — хорошо. Сентиментальности не будет. Делаем.",
            "Пропустил(а) много — ничего страшного. Сегодня начинаем заново.",
            "Паузы бывают. Возврат — это и есть навык.",
            "Хорошо, что вернулся(лась). Теперь — 60 секунд.",
            "Смотреть назад нет смысла. Только вперёд.",
            "Это не первый раз, когда ты возвращаешься. Это система.",
            "Тело помнит, как это делается. Начни — и увидишь.",
        ],
        "crisis_entry": [
            "Слышу. Что конкретно сейчас не работает?",
            "Ок. Разбираемся. Говори.",
            "Коротко: что происходит?",
            "Кризис — это сигнал, а не катастрофа. Что случилось?",
            "Слушаю. Одним предложением — что именно не так.",
            "Это решаемо. Рассказывай.",
            "Стоп. Сначала — что именно не так прямо сейчас?",
            "Не нужно объяснять всё. Главное — скажи, что происходит.",
            "Принято. Что делаем первым?",
            "Ситуация понятна. Найдём точку входа.",
        ],
        "evening_close": [
            "День сделан. Завтра — свежий старт.",
            "Результат зафиксирован. Иди отдыхать.",
            "Закрываем день. Ничего лишнего.",
            "Всё что нужно — сделано. Отдыхай.",
            "Спокойной ночи. Завтра продолжим.",
            "День закрыт.",
            "Лечь спать вовремя — тоже часть тренировки.",
            "Конец дня. Не анализируй — просто отдыхай.",
            "Хватит на сегодня. Завтра снова.",
            "Сегодня было — нормально. Этого достаточно.",
        ],
    },

    "beck": {
        "done": [
            "Действие выполнено. Это формирует паттерн.",
            "Фиксирую: попытка засчитана. Продолжаем серию.",
            "Одно повторение есть. Это уже данные.",
            "Навык тренируется именно так — через действие.",
            "Каждое выполнение снижает порог следующего. Хорошо.",
            "Попытка есть. Анализ потом — сейчас просто зафиксируй ощущение.",
            "Это и есть обучение. Не быстро, но системно.",
            "Хорошая работа. Завтра повторим и сравним.",
            "Выполнено. Завтра будет немного легче — это механика повторения.",
            "Записал(а). Это важная точка в процессе.",
        ],
        "return": [
            "Возврат — это полноценный навык, не извинение.",
            "Перерыв случился. Возобновляем с этой точки.",
            "Нейронные связи не разрываются от одной паузы. Возвращаемся.",
            "Это называется резилентность — умение возвращаться. Ты его тренируешь.",
            "Хорошо. Что помешало — полезная информация. Потом разберём.",
            "Возврат зафиксирован. Начинаем с того места, где остановились.",
            "Ты не «выпал(а) из системы». Ты просто сделал(а) паузу.",
            "Возврат — это не слабость. Это часть протокола.",
            "Снова здесь — хорошо. Данные продолжают накапливаться.",
            "Паузы бывают у всех. Важно — что ты делаешь после них.",
        ],
        "doubt": [
            "Сомнение — нормальная часть процесса. Оно не блокирует действие.",
            "Это вопрос не веры, а повторений. Попробуй и посмотри на результат.",
            "У тебя есть данные за прошлые попытки. Что они говорят?",
            "Скептицизм — это хорошо. Только проверять надо делом, не рассуждением.",
            "Расскажи, что конкретно кажется неработающим. Разберём по шагам.",
            "Ты сделал 1 запуск. Это уже не ноль. Большинство даже не начинают.",
            "Давай сделаем ещё одну попытку и посмотрим на ощущение.",
            "Нет смысла спорить с сомнением — его нужно проверить практикой.",
            "Маленький эксперимент: один шаг сейчас, потом замерим, что изменилось.",
            "Твоё сомнение — это данные. Что именно оно говорит?",
        ],
        "after_pause": [
            "Перерыв зафиксирован. Возобновляем с текущей точки.",
            "Долго не было — понятно. Сейчас главное — один шаг.",
            "Пауза не обнуляет всё предыдущее. Паттерны стабильнее, чем кажется.",
            "Это нормально — делать перерывы. Ненормально — не возвращаться совсем.",
            "Любой перерыв можно прервать и начать. Ты уже это делаешь.",
            "Хорошо, что вернулся(лась). Расскажи коротко — что мешало.",
            "Системы дают сбой — это предсказуемо. Важно — как ты реагируешь.",
            "Пауза была. Теперь — следующий шаг. Без анализа потерь.",
            "Мозгу нужно время на возобновление. Начнём мягко.",
            "Покажи, что помнишь. Начнём с самого простого.",
        ],
        "crisis_entry": [
            "Слышу. Что происходит — опиши как можешь.",
            "Принял(а) сигнал. Разбираемся по шагам.",
            "Кризисные состояния — часть цикла. Расскажи, что сейчас острее всего.",
            "Нет ничего, что нельзя было бы разобрать структурно. Говори.",
            "Сначала — просто описание ситуации. Без оценок.",
            "Расскажи: что конкретно не работает прямо сейчас?",
            "Ты сделал(а) правильно. Разберём и найдём точку опоры.",
            "Это состояние поддаётся работе. Расскажи, с чего начать.",
            "Я здесь. Без спешки — что происходит?",
            "Хорошо, что обратился(лась). Начнём с самого заметного — что сейчас труднее всего?",
        ],
        "evening_close": [
            "День завершён. Полезно отметить хотя бы одно выполненное действие.",
            "Итог дня: что получилось?",
            "Хорошая практика — завершать день не с самокритикой, а с наблюдением.",
            "Спокойной ночи. Сон — часть восстановления.",
            "Ночной отдых восстанавливает ресурс. Это не метафора.",
            "Зафиксируй одно: сегодня ты что-то сделал(а). Этого достаточно.",
            "Закрываем сессию. До завтра.",
            "День дал данные. Что заметил(а)?",
            "Анализ — завтра. Сейчас — отдыхай.",
            "Восстановление тоже часть системы. Отдыхай.",
        ],
    },
}


def get_trainer_reply(trainer_key: str, scenario: str) -> str:
    """Вернуть случайную реплику тренера для заданного сценария.

    trainer_key: 'marsha' | 'skinny' | 'beck'
    scenario:    'done' | 'return' | 'doubt' | 'after_pause' | 'crisis_entry' | 'evening_close'
    """
    import random
    bank = TRAINER_REPLIES.get(trainer_key) or TRAINER_REPLIES.get("marsha", {})
    phrases = bank.get(scenario) or []
    if not phrases:
        # Попытка через fallback-тренера
        for fallback in ("marsha", "skinny", "beck"):
            phrases = (TRAINER_REPLIES.get(fallback) or {}).get(scenario) or []
            if phrases:
                break
    if not phrases:
        return ""
    return random.choice(phrases)


def day_task_text(name: str, trainer_key: str, day: int, skill: dict) -> str:
    intro = {
        "skinny": "Минимум слов. Максимум выполнения.",
        "marsha": "Мягко. Без давления. Главное — вернуться.",
        "beck": "Сегодня тренируем конкретную функцию."
    }.get(trainer_key, "")
    how_text = skill_explain(trainer_key, skill)

    return (
        f"🌅 {name}, День {day}\n\n"
        f"{intro}\n\n"
        f"🧩 Навык: {skill['name']}\n"
        f"🎯 Цель: {skill['goal']}\n"
        f"✅ Как: {how_text}\n\n"
        "Важно:\n"
        "60–120 секунд — считается.\n"
        "Не результат, а попытка."
    )

def midday_ping(name: str, trainer_key: str) -> str:
    if trainer_key == "skinny":
        return f"⏱ {name}, 60 секунд. Потом свободен."
    if trainer_key == "beck":
        return f"⏱ {name}, это тренировка процесса, не результата."
    return f"⏱ {name}, если не сделал — просто вернись. Этого достаточно."

def gamify_status_line(u: dict) -> str:
    pts = int(u.get("points") or 0)
    lvl = int(u.get("level") or 1)
    streak = int(u.get("streak") or 0)
    return f"🏅 Очки: {pts} | Уровень: {lvl} | Стрик: {streak}"


# ============================================================
# DAY 2 PERSONAL PLAN
# ============================================================

def day2_personal_plan_text(name: str, trainer_key: str, bucket: str, target: str = "") -> str:
    """Персональный план на день 2 — показываем, что поняли человека"""
    target = (target or "одной рабочей задачи").strip()

    if trainer_key == "skinny":
        return (
            f"{name}, вот твой план на сегодня.\n\n"
            "Что у тебя ломается:\n"
            "— вход в задачу слишком тяжёлый\n"
            "— мозг ждёт идеального начала\n"
            "— потом всё уходит в откладывание\n\n"
            "Что делаем сегодня:\n"
            "1. Не берём всю задачу\n"
            "2. Заходим в неё на 5–10 минут\n"
            "3. Останавливаемся раньше, чем устанешь\n\n"
            f"На чём проверяем:\n{target}\n\n"
            "Задача дня — не сделать идеально.\n"
            "Задача дня — начать без цирка."
        )

    if trainer_key == "beck":
        return (
            f"{name}, на сегодня у нас короткий рабочий план.\n\n"
            "Что видно по твоему паттерну:\n"
            "— на старте включается давление\n"
            "— из-за этого вход в задачу становится слишком дорогим\n"
            "— дальше система выбирает избегание\n\n"
            "Что делаем сегодня:\n"
            "1. Сужаем задачу до маленького фрагмента\n"
            "2. Заходим в неё на ограниченное время\n"
            "3. Смотрим, где появляется сопротивление\n\n"
            f"На чём проверяем:\n{target}\n\n"
            "Сегодня нам нужен не идеальный результат,\n"
            "а данные: как именно у тебя запускается работа."
        )

    return (
        f"{name}, давай на сегодня очень простой личный план.\n\n"
        "Что у тебя сейчас происходит:\n"
        "— задача кажется слишком тяжёлой\n"
        "— внутри много давления\n"
        "— поэтому вход всё время откладывается\n\n"
        "Что делаем сегодня:\n"
        "1. Не пытаемся сделать всё\n"
        "2. Берём очень маленький кусочек\n"
        "3. Делаем его спокойно и коротко\n\n"
        f"На чём проверяем:\n{target}\n\n"
        "Сегодня важно не победить всё сразу.\n"
        "Важно — войти в задачу по-другому."
    )


# ============================================================
# ANTI-CHURN TEXTS (days 1-3)
# ============================================================

ANTI_CHURN_DAY_TEXTS = {
    1: {
        "marsha": (
            "Первый день почти никогда не идёт идеально.\n\n"
            "И нам это не нужно.\n"
            "Нужен один реальный вход.\n\n"
            "Даже если ты сделал(а) совсем чуть-чуть — это уже начало."
        ),
        "skinny": (
            "Первый день не про результат.\n"
            "Первый день про вход.\n\n"
            "Один шаг = день не слит."
        ),
        "beck": (
            "Первый день нужен не для победы.\n"
            "Он нужен, чтобы система получила первый повтор.\n\n"
            "Даже короткий вход уже полезен."
        ),
    },
    2: {
        "marsha": (
            "Второй день часто сложнее первого.\n"
            "Потому что новизна уже ушла.\n\n"
            "Поэтому сегодня нам особенно важен очень маленький и бережный шаг."
        ),
        "skinny": (
            "Второй день — место, где обычно сливаются.\n"
            "Поэтому сегодня просто делаем минимум и не спорим."
        ),
        "beck": (
            "На второй день снижается эффект новизны.\n"
            "Именно поэтому сегодня особенно важен короткий повтор."
        ),
    },
    3: {
        "marsha": (
            "Третий день важен.\n"
            "На нём уже становится видно, что тебе подходит, а что нет.\n\n"
            "Даже если было неровно — это всё ещё полезный день."
        ),
        "skinny": (
            "Третий день — контрольный.\n"
            "Либо ты снова заходишь,\n"
            "либо всё откладывается дальше.\n\n"
            "Сделай короткий вход."
        ),
        "beck": (
            "Третий день даёт уже не случайный, а повторяющийся результат.\n"
            "Это важная точка для настройки системы."
        ),
    },
}


def anti_churn_day_text(day: int, trainer_key: str) -> str:
    """Возвращает текст анти-слива для дня 1-3"""
    trainer_key = trainer_key if trainer_key in ("marsha", "skinny", "beck") else "marsha"
    return ANTI_CHURN_DAY_TEXTS.get(day, {}).get(trainer_key, "")


# ============================================================
# AI SYSTEM PROMPTS
# ============================================================

AI_ANALYSIS_SYSTEM_PROMPT = """
Ты — AI-ассистент тренинга навыков саморегуляции.
Это НЕ психотерапия и НЕ диагноз.

Твоя задача:
— объяснить человеку, что с ним происходит
— показать, что проблема решаема
— продать путь тренировки на 1–2 месяца
— дать ощущение сопровождения и адаптации

Ограничения:
— нельзя ставить диагнозы
— нельзя использовать клинические термины
— нельзя обещать лечение
— нельзя говорить, что человек «сломан»

ВАЖНО:
Существует ТОЛЬКО 4 пути:
1) anxiety — тревожное избегание
2) low_energy — трудно начинать (апатия / истощение)
3) distractibility — высокая отвлекаемость
4) mixed — сочетание нескольких факторов

Также учитывай:
— почти всегда есть самокритика и самообвинение
— сначала тренируются НАВЫКИ
— работа с мыслями подключается ПОТОМ, мягко, не как терапия

Ты ОБЯЗАН внушать:
— «ты справишься»
— «это тренируется»
— «если метод не подойдёт — его заменят»

Верни СТРОГО JSON без комментариев.
"""

def build_ai_system_prompt() -> str:
    return (
        "Ты — ассистент тренинга навыков саморегуляции. Это НЕ терапия, НЕ диагноз.\n"
        "Твоя задача: по короткому описанию определить рабочий bucket и дать краткий разбор.\n"
        "Выход строго JSON без текста вокруг.\n"
        "Формат:\n"
        "{\n"
        '  "bucket": "anxiety|low_energy|distractibility|mixed",\n'
        '  "summary": "1-2 предложения о паттерне",\n'
        '  "confidence": 0.0-1.0,\n'
        '  "top_signals": ["...","..."],\n'
        '  "first_action": "1 конкретный шаг на сегодня"\n'
        "}\n"
        "Не придумывай диагнозов. Не говори про лечение. Без морали.\n"
    )
