from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

from state_machine import BotState, next_day_state
from templates import (
    MORNING_CHECKIN,
    SHORT_ANALYSIS_TEMPLATE,
    LONG_ANALYSIS_TEMPLATE,
    ACTION_DONE_TEMPLATE,
    ACTION_FAILED_TEMPLATE,
    WHY_TEMPLATE,
    EVENING_TEMPLATE,
    DAY3_OFFER_TEMPLATE,
    DAY4_AFTER_NO_PAYMENT_TEMPLATE,
    DAY4_TEMPLATE,
    DAY5_TEMPLATE,
    DAY6_TEMPLATE,
    DAY7_TEMPLATE,
    PAYMENT_20_STUB_TEMPLATE,
    PAYMENT_40_STUB_TEMPLATE,
    PAYMENT_COMPLETED_TEMPLATE,
    FREE_MODE_TEMPLATE,
    FREE_MODE_REOFFER_TEMPLATE,
    PAID_MODE_DEFAULT_TEMPLATE,
)

SKILLER_STATES = {s.value for s in BotState}


def _time_bucket(now: datetime | None = None) -> str:
    now = now or datetime.now()
    h = now.hour + now.minute / 60
    if 6 <= h < 11.5:
        return "morning"
    if 11.5 <= h < 18:
        return "day"
    if 18 <= h < 23:
        return "evening"
    return "night"


def _load_skills() -> dict[str, Any]:
    path = os.path.join(os.path.dirname(__file__), "skills.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _one_skill(u: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    skills = _load_skills()
    sid = u.get("current_skill") or "two_min_start"
    if sid not in skills:
        sid = "two_min_start"
    return sid, skills[sid]


def init_skiller_user(u: dict[str, Any]) -> dict[str, Any]:
    u["current_mode"] = BotState.ONBOARDING.value
    u["current_day"] = max(1, int(u.get("current_day") or 1))
    u["onboarding_completed"] = 0
    u["today_checkin_done"] = 0
    u["today_skill_done"] = 0
    return u


def start_problem_buttons() -> list[str]:
    return ["Не могу начать", "Залипаю", "Перегруз"]


def make_keyboard(buttons: list[str]) -> list[list[str]]:
    return [buttons[i : i + 2] for i in range(0, len(buttons), 2)]


def parse_checkin_value(text: str) -> dict[str, str]:
    t = (text or "").lower()
    out: dict[str, str] = {}
    if "😴" in t or "плохо" in t or "хорошо" in t:
        if "плохо" in t:
            out["sleep"] = "bad"
        elif "норм" in t:
            out["sleep"] = "normal"
        elif "хорошо" in t:
            out["sleep"] = "good"
    if "😰" in t or "средняя" in t or "низкая" in t or "высокая" in t:
        if "высок" in t:
            out["anxiety"] = "high"
        elif "сред" in t:
            out["anxiety"] = "medium"
        elif "низ" in t:
            out["anxiety"] = "low"
    if "🔋" in t or "мало" in t or "много" in t:
        if "мало" in t:
            out["energy"] = "low"
        elif "норм" in t:
            out["energy"] = "medium"
        elif "много" in t:
            out["energy"] = "high"
    return out


def process_skiller_text(u: dict[str, Any], text: str, now: datetime | None = None) -> dict[str, Any]:
    text = (text or "").strip()
    low = text.lower()
    mode = (u.get("current_mode") or BotState.ONBOARDING.value)
    day = int(u.get("current_day") or 1)
    bucket = _time_bucket(now)
    today = (now or datetime.now()).date().isoformat()

    if bucket == "morning" and int(u.get("today_checkin_done") or 0) == 0 and mode not in {
        BotState.MORNING_CHECKIN.value,
        BotState.CRISIS.value,
        BotState.OFFER.value,
    }:
        u["current_mode"] = BotState.MORNING_CHECKIN.value
        return {
            "text": MORNING_CHECKIN,
            "buttons": ["😴 плохо", "😐 норм", "🙂 хорошо", "😰 высокая", "😐 средняя", "🙂 низкая", "🔋 мало", "🔋🔋 норм", "🔋🔋🔋 много"],
            "event": "checkin_step",
        }

    if bucket == "evening" and mode in {BotState.REFLECTION.value, BotState.ACTION.value, BotState.WAITING_RESULT.value}:
        u["current_mode"] = BotState.EVENING.value
        return {"text": EVENING_TEMPLATE, "buttons": ["Сделал", "Пробовал", "Не получилось"], "event": "day_complete"}

    u["last_greeting_date"] = today

    if "кризис" in low:
        u["current_mode"] = BotState.CRISIS.value
        return {"text": "Похоже на перегруз. Назови 5 предметов вокруг и сделай длинный выдох.", "buttons": ["Сделал grounding"], "event": "crisis_clicked"}

    if mode == BotState.ONBOARDING.value:
        u["onboarding_completed"] = 1
        u["_problem"] = text
        u["current_mode"] = BotState.ANALYSIS.value
        return {"text": "Принял. Коротко опиши, где именно стопор.", "buttons": [], "event": "problem_selected"}

    if mode == BotState.MORNING_CHECKIN.value:
        checkin = parse_checkin_value(text)
        user_state = u.get("_user_state") or {}
        user_state.update(checkin)
        u["_user_state"] = user_state
        if {"sleep", "anxiety", "energy"}.issubset(set(user_state.keys())):
            u["today_checkin_done"] = 1
            u["current_mode"] = BotState.ANALYSIS.value
            return {"text": "Что сейчас больше всего мешает начать?", "buttons": ["Страх ошибки", "Залипание", "Перегруз"], "event": "checkin_completed", "user_state_update": user_state}
        return {"text": MORNING_CHECKIN, "buttons": ["😴 плохо", "😐 норм", "🙂 хорошо", "😰 высокая", "😐 средняя", "🙂 низкая", "🔋 мало", "🔋🔋 норм", "🔋🔋🔋 много"], "event": "checkin_step", "user_state_update": user_state}

    if mode == BotState.ANALYSIS.value:
        u["current_mode"] = BotState.DETAILS.value
        short = "Ты зависаешь перед стартом.\nЭто не лень.\nЭто сбой входа в задачу."
        return {"text": SHORT_ANALYSIS_TEMPLATE.format(short_analysis=short), "buttons": ["Подробнее", "Давай действие"], "event": "analysis_shown"}

    if mode == BotState.DETAILS.value and low == "подробнее":
        u["current_mode"] = BotState.ACTION.value
        long_text = "Паттерн: стоп на входе.\nТриггер: неопределенность.\nРешение: короткий запуск без давления."
        return {"text": LONG_ANALYSIS_TEMPLATE.format(long_analysis=long_text), "buttons": ["Давай действие"], "event": "details_clicked"}

    if mode in {BotState.DETAILS.value, BotState.ACTION.value}:
        if int(u.get("today_skill_done") or 0) == 1 and mode == BotState.ACTION.value:
            return {
                "text": "На сегодня уже есть выполненный навык. Закроем день вечером или продолжим завтра.",
                "buttons": ["Хватит на сегодня"],
                "event": "day_complete",
            }
        sid, skill = _one_skill(u)
        u["current_skill"] = sid
        u["current_mode"] = BotState.WAITING_RESULT.value
        steps = "\n".join([f"{i+1}. {s}" for i, s in enumerate(skill.get("steps", []))])
        return {"text": f"{skill.get('title')}\n\n{skill.get('why')}\n\n{steps}", "buttons": ["Сделал", "Не сделал"], "event": "action_sent"}

    if mode == BotState.WAITING_RESULT.value:
        if low == "сделал":
            u["today_skill_done"] = 1
            u["current_mode"] = BotState.REFLECTION.value
            u["_awaiting_feedback"] = 1
            return {"text": ACTION_DONE_TEMPLATE, "buttons": ["🙂 легче", "😐 скучно", "😣 тяжело", "🤔 не понял"], "event": "action_done"}
        u["current_mode"] = BotState.ACTION_FAILED_REASON.value
        return {"text": ACTION_FAILED_TEMPLATE, "buttons": ["Слишком сложно", "Не понял что делать", "Нет сил", "Залип"], "event": "action_failed"}

    if mode == BotState.ACTION_FAILED_REASON.value:
        u["current_mode"] = BotState.ACTION.value
        if "сложно" in low:
            t = "Упрощаем. Не делай задачу. Просто открой её."
            event = "action_resized"
        elif "нет сил" in low:
            t = "Тогда не делаем задачу. Сядь и смотри на неё 30 секунд."
            event = "action_resized"
        else:
            t = WHY_TEMPLATE
            event = "why_requested"
        return {"text": t, "buttons": ["Давай действие"], "event": event}

    if mode == BotState.REFLECTION.value:
        if int(u.get("_awaiting_feedback") or 0) == 1:
            if low in {"🙂 легче", "😐 скучно", "😣 тяжело", "🤔 не понял"}:
                u["_awaiting_feedback"] = 0
                u["feedback"] = text
                u["_awaiting_depth"] = 1
                return {
                    "text": "Как дальше вести тебя?",
                    "buttons": ["Быстро и коротко", "С объяснениями", "Пожёстче"],
                    "event": "feedback_captured",
                }
            return {
                "text": "Оцени, как прошло:",
                "buttons": ["🙂 легче", "😐 скучно", "😣 тяжело", "🤔 не понял"],
                "event": "feedback_requested",
            }
        if int(u.get("_awaiting_depth") or 0) == 1:
            if low in {"быстро и коротко", "с объяснениями", "пожёстче"}:
                u["_awaiting_depth"] = 0
                u["preferred_depth"] = text
                if "пожёстче" in low:
                    u["trainer_style"] = "skinny"
                elif "объяснениями" in low:
                    u["trainer_style"] = "beck"
                else:
                    u["trainer_style"] = "marsha"
                return {
                    "text": "Принял стиль. Дальше:",
                    "buttons": ["Ещё 1 круг", "Хватит на сегодня"],
                    "event": "trainer_style_updated",
                }
            return {
                "text": "Как дальше вести тебя?",
                "buttons": ["Быстро и коротко", "С объяснениями", "Пожёстче"],
                "event": "depth_requested",
            }
        if bucket == "evening":
            u["current_mode"] = BotState.EVENING.value
            return {"text": EVENING_TEMPLATE, "buttons": ["Сделал", "Пробовал", "Не получилось"], "event": "day_complete"}
        u["current_mode"] = BotState.ACTION.value
        return {"text": "Делаем ещё один короткий круг.", "buttons": ["Давай действие"], "event": "action_started"}

    if mode == BotState.EVENING.value:
        if day >= 3:
            u["current_mode"] = BotState.OFFER.value
            return {"text": DAY3_OFFER_TEMPLATE, "buttons": ["7 дней — €20", "Месяц — €40", "Подумаю"], "event": "offer_shown"}
        u["current_day"] = day + 1
        u["current_mode"] = next_day_state(day + 1).value
        u["today_checkin_done"] = 0
        u["today_skill_done"] = 0
        return {"text": MORNING_CHECKIN, "buttons": ["😴 плохо", "😐 норм", "🙂 хорошо"], "event": "day_complete"}

    if mode == BotState.OFFER.value:
        if "20" in low:
            return {
                "text": PAYMENT_20_STUB_TEMPLATE,
                "buttons": [],
                "event": "payment_click_20",
            }
        if "40" in low:
            return {
                "text": PAYMENT_40_STUB_TEMPLATE,
                "buttons": [],
                "event": "payment_click_40",
            }
        if "хочу 7 дней" in low or "оплатил" in low:
            u["payment_status"] = "paid"
            u["current_mode"] = BotState.PAID_MODE.value
            u["current_day"] = max(4, day)
            return {"text": PAYMENT_COMPLETED_TEMPLATE, "buttons": ["Давай действие"], "event": "payment_completed"}
        u["free_mode"] = 1
        u["current_mode"] = BotState.FREE_MODE.value
        return {"text": DAY4_AFTER_NO_PAYMENT_TEMPLATE.format(main_pattern="сбой входа", successful_skill="2 минуты старта"), "buttons": ["Давай тренироваться", "Вернуться к программе"], "event": "payment_declined_soft"}

    if mode == BotState.FREE_MODE.value:
        if day >= 5:
            return {
                "text": FREE_MODE_REOFFER_TEMPLATE,
                "buttons": ["7 дней — €20", "Месяц — €40", "Подумаю"],
                "event": "offer_shown",
            }
        u["current_mode"] = BotState.ACTION.value
        u["current_skill"] = u.get("current_skill") or "two_min_start"
        return {"text": FREE_MODE_TEMPLATE, "buttons": ["Давай действие"], "event": "free_mode_started"}

    if mode == BotState.PAID_MODE.value:
        day_skill = {
            4: ("restart_after_break", DAY4_TEMPLATE),
            5: ("self_criticism_to_instruction", DAY5_TEMPLATE),
            6: ("one_tab_focus", DAY6_TEMPLATE),
            7: ("weekly_review_next_step", DAY7_TEMPLATE),
        }
        if day == 7:
            pattern = u.get("skiller_pattern") or "сбой входа"
            successful_skill = u.get("current_skill") or "two_min_start"
            intro = (
                f"Твой главный паттерн:\n{pattern}\n\n"
                f"Лучше всего сработало:\n{successful_skill}\n\n"
                "Следующая неделя: тренируем устойчивый вход в задачу."
            )
            sid = "weekly_review_next_step"
        else:
            sid, intro = day_skill.get(day, ("two_min_start", PAID_MODE_DEFAULT_TEMPLATE))
        u["current_skill"] = sid
        u["current_mode"] = BotState.ACTION.value
        return {"text": intro, "buttons": ["Давай действие"], "event": "paid_mode_started"}

    u["current_mode"] = BotState.MORNING_CHECKIN.value
    return {"text": MORNING_CHECKIN, "buttons": ["😴 плохо", "😐 норм", "🙂 хорошо"], "event": "start"}
