# ============================================================
# NLP_FALLBACK.PY
# Понимание кривых ответов и анти-тупик логика
# ============================================================

from typing import Dict, Optional


def norm_text(text: str) -> str:
    return (text or "").strip().lower()


def parse_tiny_reply(text: str) -> Optional[str]:
    t = norm_text(text)

    if t in {"там", "потом", "дальше"}:
        return "during"

    if t in {"сразу", "сначала"}:
        return "start"

    if t in {"не знаю", "хз", "по-разному"}:
        return "mixed"

    return None


def parse_start_vs_hold(text: str) -> Optional[str]:
    t = norm_text(text)

    hold_markers = [
        "удерж", "потом", "после", "через", "в процессе", "спустя",
        "несколько итерац", "съезжаю", "сливаюсь", "пару итерац",
        "после нескольких", "разваливаюсь",
    ]
    start_markers = [
        "нач", "сразу", "подойти", "войти", "старт", "заставить себя начать",
        "первый шаг", "на старте",
    ]

    if any(x in t for x in hold_markers):
        return "hold"
    if any(x in t for x in start_markers):
        return "start"

    if t in {"там", "потом", "дальше"}:
        return "hold"

    return None


def parse_anxiety_vs_empty(text: str) -> Optional[str]:
    t = norm_text(text)

    anxiety_markers = [
        "трев", "страх", "бою", "напряг", "давление", "стыд", "паник", "нерв",
    ]
    empty_markers = [
        "пусто", "нет сил", "устал", "усталость", "выгор", "апат",
        "не хочу", "никакой", "не тяну", "вообще пусто",
    ]

    if any(x in t for x in anxiety_markers):
        return "anxiety"
    if any(x in t for x in empty_markers):
        return "empty"

    if "и то и то" in t or "оба" in t:
        return "mixed"

    return None


def parse_distraction_primary(text: str) -> Optional[str]:
    t = norm_text(text)

    secondary_markers = [
        "вторич", "потом", "не главная", "скорее вторично",
    ]
    primary_markers = [
        "главная", "основная", "первично", "из-за этого", "сначала отвлекаюсь",
    ]
    distraction_markers = [
        "отвлек", "ютуб", "телефон", "вкладк", "соцсет", "видео",
    ]

    if any(x in t for x in secondary_markers):
        return "secondary"
    if any(x in t for x in primary_markers):
        return "primary"
    if any(x in t for x in distraction_markers):
        return "primary"

    return None


def parse_where_stop(text: str) -> Optional[str]:
    t = norm_text(text)

    mapping = {
        "start": ["сразу", "в начале", "начать", "на старте", "первый шаг"],
        "during": [
            "потом", "после", "в процессе", "через время", "спустя",
            "после нескольких", "после пары итерац", "несколько итерац",
            "пару итерац",
        ],
        "finish": ["в конце", "сдать", "завершить", "доделать", "отправить"],
        "mixed": ["везде", "по-разному", "и там и там", "хз", "не знаю"],
    }

    for key, markers in mapping.items():
        if any(x in t for x in markers):
            return key

    if t in {"там", "потом", "дальше"}:
        return "during"

    return None


def parse_yes_no_soft(text: str) -> Optional[bool]:
    t = norm_text(text)

    yes_markers = ["да", "угу", "ага", "похоже", "в точку", "похоже на меня", "да, это так"]
    no_markers = ["нет", "не", "мимо", "не то", "не похоже"]

    if any(t == x or x in t for x in yes_markers):
        return True
    if any(t == x or x in t for x in no_markers):
        return False

    return None


def guess_bucket_from_answers(data: Dict[str, str]) -> str:
    """
    data:
      start_hold: start|hold
      emotional: anxiety|empty|mixed
      distraction: primary|secondary
      stop_where: start|during|finish|mixed
    """
    start_hold = data.get("start_hold")
    emotional = data.get("emotional")
    distraction = data.get("distraction")
    stop_where = data.get("stop_where")

    if emotional == "empty":
        return "low_energy"

    if distraction == "primary" and start_hold == "hold":
        return "distractibility"

    if emotional == "anxiety" and stop_where in {"start", "mixed"}:
        return "anxiety"

    if start_hold == "hold" and distraction == "primary":
        return "distractibility"

    return "mixed"


def anti_dead_end_reply(trainer_key: str = "marsha") -> str:
    if trainer_key == "skinny":
        return "Не будем вязнуть в формулировках. Я беру рабочую гипотезу и веду дальше."
    if trainer_key == "beck":
        return "Не обязательно формулировать идеально. Для движения достаточно рабочей гипотезы."
    return "Ок. Не будем мучить формулировку. Я возьму рабочую версию и поведу дальше."
