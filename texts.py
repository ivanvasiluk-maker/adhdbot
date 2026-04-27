# ============================================================
# TEXTS.PY — Все текстовые константы и клавиатуры
# ============================================================

import random
from datetime import datetime
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

# Совместимость деплоя: этот объект импортируется в некоторых версиях bot.py.
kb_skill_more = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Ещё навык", callback_data="skill_more")]
    ]
)


def __getattr__(name: str):
    # Защита от падения при from texts import kb_skill_more в старых сборках.
    if name == "kb_skill_more":
        return kb_skill_more
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

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


def skill_card_text(skill: dict, trainer_key: str = "marsha") -> str:
    """Короткая карточка навыка дня для экрана skill_entry."""
    name = skill.get("name", "Навык")
    goal = skill.get("goal") or ""
    micro = skill.get("micro") or skill.get("minimum") or ""

    parts = [f"🧩 Навык дня: {name}"]
    if goal:
        parts.append(f"🎯 Цель: {goal}")
    if micro:
        parts.append(f"⚡ Минимум: {micro}")

    return "\n".join(parts)


def skill_training_text(skill: dict, trainer_key: str = "marsha") -> str:
    """Строгий формат тренировки: только действие без объяснений."""
    name = skill.get("name", "Навык")
    _, step1, step2, step3, _, _ = _skill_format_parts(skill)

    steps = [s for s in [step1, step2, step3] if s]
    if not steps:
        steps = [skill.get("micro") or skill.get("minimum") or "Открой задачу и сделай 2 минуты."]

    lines = [f"🧩 Навык: {name}", "", "Сделай:"]
    for idx, step in enumerate(steps[:3], start=1):
        lines.append(f"{idx}. {step}")
    lines.extend(["", "Все."])
    return "\n".join(lines)

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

kb_crisis_mode = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎙 Кризис голосом")],
        [KeyboardButton(text="✍️ Кризис текстом")],
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
        [KeyboardButton(text="😐 норм"), KeyboardButton(text="😣 тяжело")],
    ],
    resize_keyboard=True,
)

kb_evening_close = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👍 сделал")],
        [KeyboardButton(text="😐 частично")],
        [KeyboardButton(text="❌ не сделал")],
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

# ============================================================
# PATCH: Simplified 2-3 button navigation
# ============================================================

kb_skill_entry = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💪 Давай тренировать навык")],
        [KeyboardButton(text="📊 Мой прогресс"), KeyboardButton(text="🆘 Кризис")],
    ],
    resize_keyboard=True,
)

kb_training_run = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Сделал(а)"), KeyboardButton(text="↩️ Вернулся(лась)")],
        [KeyboardButton(text="📊 Мой прогресс"), KeyboardButton(text="🆘 Кризис")],
    ],
    resize_keyboard=True,
)

kb_progress_only = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Мой прогресс")],
        [KeyboardButton(text="💪 Давай тренировать навык")],
        [KeyboardButton(text="🆘 Кризис")],
    ],
    resize_keyboard=True,
)


def progress_screen_text(u: dict, skill_name: str = "") -> str:
    trainer_key = u.get("trainer_key") or "marsha"
    day = int(u.get("day") or 1)
    points = int(u.get("points") or 0)
    level = int(u.get("level") or 1)
    streak = int(u.get("streak") or 0)
    done_count = int(u.get("done_count") or 0)
    return_count = int(u.get("return_count") or 0)
    crisis_count = int(u.get("crisis_count") or 0)
    bucket = u.get("bucket") or "mixed"
    today_target = (u.get("today_target") or "").strip()

    bucket_labels = {
        "anxiety": "тревожный вход",
        "low_energy": "низкий ресурс / тяжело начать",
        "distractibility": "отвлекаемость / удержание",
        "mixed": "смешанный профиль",
    }

    if not skill_name:
        skill_name = "ещё не выбран"
    if not today_target:
        today_target = "не задана"

    coach_line = {
        "skinny": "Факт важнее настроения. Продолжай короткими заходами.",
        "marsha": "Даже маленькие шаги считаются. Ты уже в процессе.",
        "beck": "Стабильность строится повторением. Даже 1 короткий круг — это тренировка.",
    }.get(trainer_key, "Ты уже в процессе.")

    return (
        "📊 Мой прогресс\n\n"
        f"День: {day}\n"
        f"Профиль: {bucket_labels.get(bucket, bucket)}\n"
        f"Навык дня: {skill_name}\n"
        f"Задача дня: {today_target}\n\n"
        f"✅ Запусков: {done_count}\n"
        f"↩️ Возвратов: {return_count}\n"
        f"🆘 Кризисов: {crisis_count}\n\n"
        f"🏅 Очки: {points}\n"
        f"📈 Уровень: {level}\n"
        f"🔥 Стрик: {streak}\n\n"
        f"{coach_line}"
    )

kb_after_done = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🙂 Чуть легче")],
        [KeyboardButton(text="😐 Скучно")],
        [KeyboardButton(text="😣 Тяжело")],
        [KeyboardButton(text="🤔 Не понял, зачем это")],
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

BTN_CONTINUE_PLAN = "📅 Хочу продолжить по плану"
BTN_THINK = "🤔 Пока думаю"
BTN_WHAT_NEXT = "❓ Что я получу дальше"
BTN_PAY = "💳 Продолжить"

kb_day2_offer = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=BTN_CONTINUE_PLAN)],
        [KeyboardButton(text=BTN_THINK)],
    ],
    resize_keyboard=True,
)

kb_paywall = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=BTN_PAY)],
        [KeyboardButton(text=BTN_WHAT_NEXT)],
    ],
    resize_keyboard=True,
)

kb_pay_simple = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=BTN_PAY)],
        [KeyboardButton(text=BTN_THINK)],
    ],
    resize_keyboard=True,
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

ONBOARDING_SCREENS = [
    (
        "Похоже, ты уже не раз пробовал(а) разобраться —\n"
        "но в какой-то момент всё равно знаешь, что делать, и не начинаешь.\n\n"
        "С этим можно работать."
    ),
    (
        "Я помогу понять, где именно у тебя сейчас стоп,\n"
        "и собрать под это короткий рабочий план.\n\n"
        "Это не терапия и не диагноз.\n"
        "Если станет резко тяжело — нажми «🆘 Кризис»."
    ),
]

# ============================================================
# 7) SALES & ONBOARDING TEXTS (карта, гарантия, таймеры)
# ============================================================

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


def personal_route_text(name: str, trainer_key: str, bucket: str) -> str:
    routes = {
        "anxiety": (
            "Сначала уберём перегруз на входе.\n"
            "Потом научимся не сцепляться с тревогой.\n"
            "Потом закрепим спокойный возврат в задачу."
        ),
        "low_energy": (
            "Сначала вернём более мягкий вход в день.\n"
            "Потом соберём запуск без давления.\n"
            "Потом будем удерживать ритм без самоедства."
        ),
        "distractibility": (
            "Сначала сузим вход в задачу.\n"
            "Потом потренируем возврат внимания.\n"
            "Потом будем удерживать один рабочий канал дольше."
        ),
        "mixed": (
            "Сначала поймаем твою главную точку стопа.\n"
            "Потом подберём короткий рабочий вход.\n"
            "Потом закрепим возврат без слива дня."
        ),
    }

    route = routes.get(bucket, routes["mixed"])

    if trainer_key == "skinny":
        return f"{name}, вот твой маршрут.\n\n{route}\n\nНе общая схема. Под твою ситуацию."
    if trainer_key == "beck":
        return f"{name}, по тому, что уже видно, маршрут такой:\n\n{route}\n\nЭто рабочая гипотеза под твой паттерн."
    return f"{name}, я собрала для тебя такой маршрут:\n\n{route}\n\nНе шаблон для всех, а опора под твою ситуацию."

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

# ============================================================
# DAILY CHECK-IN TEXTS (Morning / Midday / Evening)
# ============================================================

def morning_checkin_text(trainer_key: str, name: str = "ты") -> str:
    """Утренний check-in: как ты себя чувствуешь?"""
    return "Доброе утро.\n\nКак ты сейчас?"


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
