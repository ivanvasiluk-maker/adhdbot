# ============================================================
# ADHD SELF-REGULATION TRAINER BOT (REFACTORED)
# Тренеры-коты: Скинни (жёсткий), Марша (мягкая), Бек (аналитик)
# ====================
# СТРУКТУРА:
# - texts.py: все текстовые константы и клавиатуры
# - skills.py: навыки и планы
# - db.py: работа с БД
# - flows.py: основные логические потоки
# ============================================================

import os
import re
import json
import time
import asyncio
import logging
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List

import aiosqlite
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandStart
from aiogram.enums import ParseMode
from openai import OpenAI

# Import modules
from texts import (
    TRAINERS, PRAISE, DAILY_LIVE_LINES, TRAINER_REPLIES, get_trainer_reply,
    TEST_QUESTIONS, ONBOARDING_SCREENS,
    trainer_say, trainer_confirm_text, kb_trainers, kb_input_mode, kb_yes_no,
    kb_training_main, kb_crisis_mode, kb_analysis_confirm, kb_analysis_contract,
    kb_analysis_map, kb_pay_choice, kb_payment_continue, kb_morning_checkin,
    kb_doubt_response, kb_more_clarify, payment_inline_discount, payment_inline_full,
    CRISIS_LIMIT, resolve_bucket_from_test, create_test_question_keyboard,
    analysis_contract_short, contract_full_text, month_map_text, guarantee_block, offer_day_3_text,
    gamify_status_line, skill_explain, skill_detail_text, get_morning_checkin_ack,
    daytime_ping, evening_close_question, evening_close_coach_reply, kb_evening_close,
    reactivation_6h, reactivation_24h, reactivation_3d, reactivation_7d, kb_reactivation,
    reactivation_soft_return, kb_soft_return,
    kb_mode_choice, MODE_CHOICE_TEXT,
    emotional_hook, get_daytime_greeting,
    build_week_plan, build_payment_offer, build_hesitation_response,
)
from dialog_engine import (
    detect_dialog_pattern,
    get_dialog_reply,
    need_clarify,
    clarify_question,
    render_behavior_chain,
    anti_churn_message,
    trainer_block,
    MISUNDERSTOOD_FALLBACK,
    guidance_micro_phrase,
)
from skills import (
    SKILLS_DB,
    get_current_plan,
    build_28_day_plan,
    build_plan,
    propose_plan_override,
    suggest_alternative_skill,
    format_skill,
)
from db import (
    USER_FIELDS, default_user, init_db, migrate_db, get_user, save_user, 
    log_event, gamify_apply, is_paid, EXTRA_USER_COLS,
    push_user_summary, compute_stuck_flag,
)
from flows import (
    start_day, start_day1, start_day_simple, advance_day, handle_crisis,
    send_trainer_photo_if_any, send_trainer_introduction, run_analysis,
    send_weekly_summary, send_progress_report, ai_analyze, ai_analyze_comprehensive,
    _extract_json, clamp_str
)

# ============================================================
# CONFIG
# ============================================================

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bot")

APP_VERSION = "2026-03-28-v3"

BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()
OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY") or "").strip()
OPENAI_CHAT_MODEL = (os.getenv("OPENAI_CHAT_MODEL") or "gpt-4o-mini").strip()
OPENAI_WHISPER_MODEL = (os.getenv("OPENAI_WHISPER_MODEL") or "whisper-1").strip()
DB_PATH = (os.getenv("DB_PATH") or "bot.db").strip()
PAYMENT_URL = (os.getenv("PAYMENT_URL") or "").strip()
PAYMENT_URL_DISCOUNT = (os.getenv("PAYMENT_URL_DISCOUNT") or "").strip()
PAYMENT_URL_FULL = (os.getenv("PAYMENT_URL_FULL") or "").strip()
SHEETS_WEBHOOK_URL = (os.getenv("SHEETS_WEBHOOK_URL") or "").strip()

log.info(f"SHEETS_WEBHOOK_URL set: {bool(SHEETS_WEBHOOK_URL)}")
log.info(f"SHEETS_WEBHOOK_URL preview: {SHEETS_WEBHOOK_URL[:90] if SHEETS_WEBHOOK_URL else 'EMPTY'}")

TEST_MODE = (os.getenv("TEST_MODE") or "").lower() in {"1", "true", "yes", "on", "debug"}
ENABLE_PAYMENTS = (os.getenv("ENABLE_PAYMENTS") or "").lower() in {"1", "true", "yes", "on"}

log.info(f"APP_VERSION: {APP_VERSION}")
log.info(f"TEST_MODE: {TEST_MODE}")
log.info(f"ENABLE_PAYMENTS: {ENABLE_PAYMENTS}")


def log_payment_startup_status() -> None:
    reasons = []
    if not ENABLE_PAYMENTS:
        reasons.append("ENABLE_PAYMENTS is false")
    if TEST_MODE:
        reasons.append("TEST_MODE is true")
    if not PAYMENT_URL_DISCOUNT:
        reasons.append("PAYMENT_URL_DISCOUNT is empty")
    if not PAYMENT_URL_FULL:
        reasons.append("PAYMENT_URL_FULL is empty")

    if reasons:
        log.warning("Payments startup status: DISABLED or PARTIAL")
        log.warning("Payments details: %s", "; ".join(reasons))
    else:
        log.info("Payments startup status: READY")


log_payment_startup_status()

client = None
AI_ANALYSIS_ENABLED = False

if not OPENAI_API_KEY:
    log.warning("OPENAI_API_KEY not found; AI disabled.")
else:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        AI_ANALYSIS_ENABLED = True
        log.info("OpenAI client initialized successfully.")
    except Exception as e:
        client = None
        AI_ANALYSIS_ENABLED = False
        log.exception("OpenAI init failed: %s", e)

print(f"BOT_TOKEN loaded: {bool(BOT_TOKEN)}")
print(f"DB_PATH: {DB_PATH}")
print(f"AI_ANALYSIS_ENABLED: {AI_ANALYSIS_ENABLED}")
print(f"OPENAI_CHAT_MODEL: {OPENAI_CHAT_MODEL}")
print(f"OPENAI_WHISPER_MODEL: {OPENAI_WHISPER_MODEL}")


def payments_enabled() -> bool:
    return ENABLE_PAYMENTS and not TEST_MODE


def get_starts_progress(u: Dict[str, Any]) -> int:
    metrics = u.get("metrics")
    if not isinstance(metrics, dict):
        return 0

    try:
        return int(metrics.get("starts") or 0)
    except (TypeError, ValueError):
        return 0


def increment_starts_progress(u: Dict[str, Any]) -> int:
    metrics = u.get("metrics")
    if not isinstance(metrics, dict):
        metrics = {}

    current = get_starts_progress(u) + 1
    metrics["starts"] = current
    u["metrics"] = metrics
    return current


def build_wow_analysis(user_text: str) -> str:
    text = user_text.lower()

    if "не могу начать" in text or "отклады" in text:
        return (
            "Смотри, что у тебя происходит:\n\n"
            "Ты смотришь на задачу → внутри включается давление 'надо нормально сделать' →\n"
            "из-за этого вход становится тяжёлым → ты откладываешь →\n"
            "потом делаешь в спешке → потом неприятно.\n\n"
            "Это не лень.\n"
            "Это перегруз на входе.\n\n"
            "👉 Значит мы не будем 'делать задачу'.\n"
            "Мы будем тренировать вход в неё."
        )

    if "тревога" in text or "пережива" in text:
        return (
            "Смотри, что происходит:\n\n"
            "Появляется мысль → тело напрягается → мозг начинает прокручивать →\n"
            "ты пытаешься решить всё сразу → становится только хуже.\n\n"
            "Это не 'слабость'.\n"
            "Это цикл тревоги.\n\n"
            "👉 Значит мы будем тренировать не 'решить',\n"
            "а прерывать этот цикл."
        )

    return (
        "Я вижу общий паттерн:\n"
        "ты не ленишься — ты застреваешь в моменте входа или перегруза.\n\n"
        "👉 Значит мы будем работать не с силой воли,\n"
        "а с точкой, где тебя выбивает."
    )


async def ai_micro_reflect(user_text: str, trainer_key: str, client=None, model: str = "gpt-4o-mini") -> str:
    """Короткий отклик на опыт выполнения (1–2 предложения)."""
    user_text = clamp_str(user_text, 600)
    trainer_key = trainer_key or "marsha"

    # Fallback без ИИ
    fallback = {
        "skinny": "Принял. Фиксируем выполнение. Завтра повторим 60–120 сек, без эмоций.",
        "marsha": "Вижу. Спасибо, что поделился. Бережно двигаемся дальше — завтра снова маленький шаг.",
        "beck": "Зафиксировал наблюдение. Это и есть данные для обучения. Завтра повторим и сравним.",
    }
    if not (client and model):
        return fallback.get(trainer_key, fallback["marsha"])

    system = (
        "Ты тренер навыков саморегуляции. Ответь очень коротко (1–2 предложения). "
        "Учитывай стиль: skinny=жестко, marsha=поддержка, beck=логика. "
        "Цель: отразить переживание пользователя и дать крошечный следующий ориентир без давления. "
        "Без эмодзи, без вопросов, без маркеров."
    )
    user = json.dumps({
        "trainer": trainer_key,
        "observation": user_text,
    }, ensure_ascii=False)

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.35,
            max_tokens=120,
        )
        content = (resp.choices[0].message.content or "").strip()
        if content:
            return clamp_str(content, 400)
    except Exception as e:
        log.error(f"ai_micro_reflect failed: {e}")
    return fallback.get(trainer_key, fallback["marsha"])


async def ai_fallback_answer(user_text: str) -> Optional[str]:
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI()
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты тренер навыков саморегуляции. Давай коротко, по делу."},
                {"role": "user", "content": user_text},
            ],
            temperature=0.7,
            max_tokens=120,
        )
        return (resp.choices[0].message.content or "").strip() or None
    except Exception:
        return None


async def sync_user_summary_state(u: Dict[str, Any], last_event: Optional[str] = None):
    if last_event:
        u["last_event"] = last_event
        u["last_event_at"] = time.time()
    u["stuck_flag"] = compute_stuck_flag(u)
    await save_user(u, DB_PATH)
    await push_user_summary(u, SHEETS_WEBHOOK_URL)


async def track_user_event(u: Dict[str, Any], stage: str, event: str, meta: Optional[Dict[str, Any]] = None):
    u["last_event"] = event
    u["last_event_at"] = time.time()
    u["stuck_flag"] = compute_stuck_flag(u)
    await save_user(u, DB_PATH)
    await push_user_summary(u, SHEETS_WEBHOOK_URL)
    await log_event(
        u["user_id"],
        stage,
        event,
        meta or {},
        DB_PATH,
        SHEETS_WEBHOOK_URL,
        user_snapshot=u,
    )


async def ask_training_target(m: Message):
    await m.answer(
        "Перед стартом: что ты прокрастинируешь сегодня?\n"
        "Одна задача/дело, на котором потренируемся.\n"
        "Напиши коротко или нажми 'Пропустить'.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Пропустить")]],
            resize_keyboard=True,
        ),
    )

# ============================================================
# ROUTER & HANDLERS
# ============================================================

router = Router()


@router.message(Command("version"))
async def version_cmd(m: Message):
    await m.answer(
        f"version={APP_VERSION}\n"
        f"ai_enabled={AI_ANALYSIS_ENABLED}\n"
        f"model={OPENAI_CHAT_MODEL}\n"
        f"whisper={OPENAI_WHISPER_MODEL}"
    )


@router.message(Command("aitest"))
async def ai_test(m: Message):
    if not (AI_ANALYSIS_ENABLED and client):
        await m.answer("❌ AI disabled")
        return
    try:
        log.info(f"AI TEST START model={OPENAI_CHAT_MODEL}")
        resp = client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=[{"role": "user", "content": "Ответь ровно: AI работает"}],
            temperature=0,
            max_tokens=20,
        )
        text = resp.choices[0].message.content if resp.choices else "empty"
        log.info(f"AI TEST OK: {text}")
        await m.answer(f"✅ {text}")
    except Exception as e:
        log.exception("AI TEST ERROR")
        await m.answer(f"❌ AI error: {e}")


@router.message(Command("whispertest"))
async def whisper_test(m: Message):
    u = await get_user(m.from_user.id, DB_PATH)
    u["stage"] = "whisper_test_wait_voice"
    await save_user(u, DB_PATH)
    await m.answer("Пришли голосовое сообщение 🎙")


@router.message(Command("sheetstest"))
async def sheets_test(m: Message):
    u = await get_user(m.from_user.id, DB_PATH)
    u["chat_id"] = m.chat.id
    u["username"] = m.from_user.username or ""
    u["name"] = u.get("name") or (m.from_user.full_name if m.from_user else "")
    u["last_event"] = "sheetstest"
    u["last_event_at"] = time.time()
    u["stuck_flag"] = compute_stuck_flag(u)
    await save_user(u, DB_PATH)

    await push_user_summary(u, SHEETS_WEBHOOK_URL)
    await log_event(
        u["user_id"],
        "debug",
        "sheetstest",
        {"source": "manual_command"},
        DB_PATH,
        SHEETS_WEBHOOK_URL,
        user_snapshot=u,
    )

    await m.answer("Ок. Отправил тест в Google Sheets. Проверь events и users_summary.")


@router.message(CommandStart())
async def cmd_start(m: Message):
    uid = m.from_user.id
    u = await get_user(uid, DB_PATH)
    u["chat_id"] = m.chat.id
    u["username"] = m.from_user.username or ""


    # Новый порядок онбординга:
    # 1. Экраны онбординга
    u["stage"] = "ask_name"
    await track_user_event(u, "onboarding", "onboarding_started")
    for screen in ONBOARDING_SCREENS:
        await m.answer(screen)
        await asyncio.sleep(0.3)

    # 2. Вопрос имени
    await m.answer(
        "Привет! Я тренер навыков саморегуляции. Как тебя зовут? (1 слово)",
        reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Пропустить")]], resize_keyboard=True),
    )


@router.message()
async def main_flow(m: Message):
    uid = m.from_user.id
    u = await get_user(uid, DB_PATH)
    text = (m.text or "").strip()
    low = text.lower()

    KNOWN_STAGES = {
        "ask_name",
        "await_trainer",
        "trainer_intro",
        "await_mode",
        "await_input_mode",
        "choose_input_mode",
        "await_problem_text",
        "await_problem_voice",
        "run_analysis",
        "confirm_analysis",
        "analysis_more",
        "analysis_contract",
        "analysis_map",
        "analysis_refine",
        "analysis_retry_await_clarification",
        "morning_checkin",
        "morning_checkin_custom",
        "await_training_target",
        "training",
        "training_skill_more",
        "training_clarify",
        "after_return_choice",
        "waiting_next_day",
        "crisis_choose_mode",
        "crisis_text",
        "crisis_voice",
        "crisis_plan_confirm",
        "offer",
        "evening_close_wait",
        "reactivation_wait",
        "whisper_test_wait_voice",
        "test_complete_show_analysis",
        "taking_test",
    }

    if u.get("stage") not in KNOWN_STAGES:
        # если уже есть день -> возвращаем в тренировку
        if u.get("day"):
            u["stage"] = "training"
            await save_user(u, DB_PATH)
            await m.answer(
                "Состояние сбилось. Возвращаю тебя в текущий день.",
                reply_markup=kb_training_main,
            )
            return

        # если совсем пусто -> старт
        u["stage"] = "ask_name"
        await save_user(u, DB_PATH)
        await m.answer("Давай начнём заново 👇")
        return

    profile_changed = False
    username = m.from_user.username or ""
    if u.get("chat_id") != m.chat.id:
        u["chat_id"] = m.chat.id
        profile_changed = True
    if (u.get("username") or "") != username:
        u["username"] = username
        profile_changed = True
    if profile_changed:
        await sync_user_summary_state(u)

    # Сбрасываем счётчик реактивации при любой активности пользователя
    u["reactivation_level"] = 0

    # Глобальный хук: кризис доступен из любого состояния, но не перебиваем активный кризис-флоу
    if (text == "🆘 Кризис" or "кризис" in low) and u.get("stage") not in {"crisis_choose_mode", "crisis_voice", "crisis_text", "crisis_plan_confirm"}:
        u["stage"] = "crisis_choose_mode"
        await track_user_event(u, u["stage"], "crisis_open")
        await m.answer("🆘 Ок. Как удобнее?", reply_markup=kb_crisis_mode)
        return

    if u.get("stage") == "evening_close_wait":
        trainer_key = u.get("trainer_key") or "marsha"
        if not text:
            await m.answer("Можно выбрать вариант кнопкой или написать одной фразой.", reply_markup=kb_evening_close)
            return

        if text == "✍️ Напишу сам":
            await m.answer("Ок, напиши одной фразой.", reply_markup=kb_evening_close)
            return

        mapped = text
        if text == "✅ Что-то получилось":
            mapped = "Что-то получилось хотя бы частично."
        elif text == "🧱 Было тяжело":
            mapped = "Сегодня было труднее всего удержаться и продолжать."
        elif text == "↩️ Срывался(ась), но возвращался(ась)":
            mapped = "Были срывы, но я возвращался(ась)."

        await log_event(
            u["user_id"],
            "evening_close",
            "evening_close_answered",
            {
                "raw": text,
                "mapped": mapped,
                "restore_stage": u.get("evening_return_stage") or "training",
            },
            DB_PATH,
            SHEETS_WEBHOOK_URL,
        )

        reply = evening_close_coach_reply(trainer_key, mapped)
        restore_stage = u.get("evening_return_stage") or "training"
        u["stage"] = restore_stage
        u["evening_return_stage"] = None
        u["last_active"] = time.time()
        await save_user(u, DB_PATH)
        await m.answer(trainer_say(trainer_key, reply), reply_markup=kb_training_main)
        return

    # Пост-рефлексия после выполнения
        if u.get("stage") == "reactivation_wait":
            trainer_key = u.get("trainer_key") or "marsha"
            restore = u.get("evening_return_stage") or "training"

            if text == "↩️ Вернуться с сегодняшнего дня":
                u["stage"] = restore
                u["evening_return_stage"] = None
                u["last_active"] = time.time()
                u["day_started_at"] = time.time()
                await save_user(u, DB_PATH)
                await log_event(u["user_id"], "reactivation", "reactivation_returned", {"via": "start_day"}, DB_PATH, SHEETS_WEBHOOK_URL)
                day = int(u.get("day") or 1)
                await start_day(m, u, day, DB_PATH, SHEETS_WEBHOOK_URL)
                return

            if text == "🎯 Взять самый простой навык":
                plan = get_current_plan(u)
                sid = plan[0] if plan else None
                skill = SKILLS_DB.get(sid, {}) if sid else {}
                msg = skill_explain(trainer_key, skill) if skill else "Начни с 1–2 минут: просто сядь и сделай один маленький шаг."
                u["stage"] = "training"
                u["evening_return_stage"] = None
                u["day_started_at"] = time.time()
                u["last_active"] = time.time()
                await save_user(u, DB_PATH)
                await log_event(u["user_id"], "reactivation", "reactivation_returned", {"via": "simplest_skill", "sid": sid or ""}, DB_PATH, SHEETS_WEBHOOK_URL)
                await m.answer(trainer_say(trainer_key, msg), reply_markup=kb_training_main)
                return

            if text == "🌱 Нужен мягкий вход":
                u["stage"] = "morning_checkin"
                u["evening_return_stage"] = None
                u["day_started_at"] = time.time()
                u["last_active"] = time.time()
                await save_user(u, DB_PATH)
                await log_event(u["user_id"], "reactivation", "reactivation_returned", {"via": "gentle_entry"}, DB_PATH, SHEETS_WEBHOOK_URL)
                from texts import get_morning_checkin_opener
                await m.answer(trainer_say(trainer_key, get_morning_checkin_opener(trainer_key)), reply_markup=kb_morning_checkin)
                return

            if text == "🌱 Вернуться без давления":
                plan = get_current_plan(u)
                sid = plan[0] if plan else None
                skill = SKILLS_DB.get(sid, {}) if sid else {}
                step = skill.get("micro") or skill.get("minimum") or "открыть задачу на 2 минуты"
                msg = reactivation_soft_return(trainer_key, u.get("name") or "", step)
                u["stage"] = "training"
                u["evening_return_stage"] = None
                u["day_started_at"] = time.time()
                u["last_active"] = time.time()
                await save_user(u, DB_PATH)
                await log_event(u["user_id"], "reactivation", "reactivation_returned", {"via": "soft_return"}, DB_PATH, SHEETS_WEBHOOK_URL)
                await m.answer(trainer_say(trainer_key, msg), reply_markup=kb_training_main)
                return

            # Пользователь написал что-то своё — показываем soft return экран
            plan = get_current_plan(u)
            sid = plan[0] if plan else None
            skill = SKILLS_DB.get(sid, {}) if sid else {}
            step = skill.get("micro") or skill.get("minimum") or "открыть задачу на 2 минуты"
            msg = reactivation_soft_return(trainer_key, u.get("name") or "", step)
            u["stage"] = restore
            u["evening_return_stage"] = None
            u["last_active"] = time.time()
            await save_user(u, DB_PATH)
            await log_event(u["user_id"], "reactivation", "reactivation_returned", {"via": "free_text"}, DB_PATH, SHEETS_WEBHOOK_URL)
            await m.answer(trainer_say(trainer_key, msg), reply_markup=kb_soft_return)
            return

        # Пост-рефлексия после выполнения
    if u.get("stage") == "waiting_next_day":
        trainer_key = u.get("trainer_key") or "marsha"
        reply = await ai_micro_reflect(text or "", trainer_key, client, OPENAI_CHAT_MODEL)
        await log_event(u["user_id"], "training", "post_done_reflect", {"len": len(text or "")}, DB_PATH, SHEETS_WEBHOOK_URL)
        await m.answer(trainer_say(trainer_key, reply), reply_markup=kb_training_main)
        return

    if u.get("stage") == "whisper_test_wait_voice":
        if not m.voice:
            await m.answer("Пришли именно голосовое 🎙")
            return

        t = await whisper_transcribe(m)
        if not t:
            await m.answer("❌ Whisper не смог распознать голос.")
            return

        await m.answer(f"✅ Whisper:\n\n{t}")
        return


    # ============================================================
    # LIVE DIALOG PATTERN HOOK
    # ============================================================
    dialog_stages = {
        "await_problem_text",
        "analysis_refine",
        "training",
        "morning_checkin_custom",
        "await_training_target",
    }

    if u.get("stage") in dialog_stages and text:
        matched_intent = False

        if "скуч" in low:
            await m.answer(
                trainer_say(
                    u.get("trainer_key") or "marsha",
                    "Скука = ты уже у входа.\n\n👉 Сделай 1 тупое действие и остановись.",
                )
            )
            return

        pattern = detect_dialog_pattern(text)

        if u.get("stage") in {"await_problem_text", "analysis_refine"} and need_clarify(text):
            await m.answer(clarify_question(u.get("mode") or "normal"))
            return

        if pattern and u.get("stage") in {"training", "await_problem_text", "analysis_refine"}:
            reply = get_dialog_reply(
                u.get("trainer_key") or "marsha",
                u.get("mode") or "normal",
                pattern,
            )
            if reply:
                await m.answer(trainer_say(u.get("trainer_key") or "marsha", reply))
                matched_intent = True

                if pattern == "misunderstood":
                    await m.answer(MISUNDERSTOOD_FALLBACK)
                    return

        if not matched_intent:
            ai = await ai_fallback_answer(text)
            if ai:
                await m.answer(ai)
                return

    # ask_name
    if u["stage"] == "ask_name":
        if text and text.lower() != "пропустить":
            u["name"] = text[:50]
        await log_event(u["user_id"], "onboarding", "name_provided", {}, DB_PATH, SHEETS_WEBHOOK_URL)
        u["stage"] = "await_trainer"
        await save_user(u, DB_PATH)
        # Показываем всех тренеров
        trainers_intro = (
            "\U0001F408\u200D\u2B1B Тренеры: кто будет вести тебя?\n\n"
            "🤍 Марша — мягкая и поддерживающая. Помогает возвращаться без стыда и не бросать после срывов.\n"
            "🐈‍⬛ Скинни — прямой и требовательный. Даст чёткий маршрут и жёсткие рамки, без лишних разговоров.\n"
            "🧠 Бек — аналитичный и спокойный. Объяснит, что происходит и почему это работает.\n\n"
            "Выбери стиль, который тебе ближе — его можно будет сменить."
        )
        await m.answer(trainers_intro)
        await m.answer("Ок. Выбери тренера:", reply_markup=kb_trainers)
        return

    # ============================================================
    # TRAINER SELECTION
    # ============================================================
    if u["stage"] == "await_trainer":
        low = text.lower().strip()
        chosen = None
        if text == "🐈‍⬛ Скинни (жёстко)" or "скинни" in low:
            chosen = "skinny"
        elif text == "🐈 Марша (мягко)" or "марша" in low:
            chosen = "marsha"
        elif text == "🐈‍🦁 Бек (аналитично)" or "бек" in low:
            chosen = "beck"
        if not chosen:
            await m.answer("Выбери кнопкой 👇", reply_markup=kb_trainers)
            return
        u["trainer_key"] = chosen
        u["stage"] = "trainer_intro"
        await track_user_event(u, "onboarding", "trainer_selected", {"trainer_key": chosen})
        # Описание и фото тренера
        await send_trainer_photo_if_any(m.chat.id, chosen, BOT_TOKEN)
        from texts import send_trainer_introduction
        await send_trainer_introduction(m, u)
        # Личный онбординг тренера — показывать после выбора тренера
        screens = trainer_block(u.get("trainer_key") or "marsha", "onboarding")
        if screens:
            for screen in screens:
                await m.answer(screen)
        await m.answer("Готов начать разбор и перейти к первому дню?", reply_markup=kb_yes_no)
        return

    # ============================================================
    # TRAINER INTRO CONFIRM
    # ============================================================
    if u["stage"] == "trainer_intro":
        low = (text or "").lower()
        if "да" in low:
            u["stage"] = "await_mode"
            await save_user(u, DB_PATH)
            await m.answer(MODE_CHOICE_TEXT, reply_markup=kb_mode_choice)
            return
        if "нет" in low:
            u["stage"] = "await_trainer"
            await save_user(u, DB_PATH)
            await m.answer("Выбери другого тренера 👇", reply_markup=kb_trainers)
            return
        await m.answer("Выбери: ✅ Да / ❌ Нет", reply_markup=kb_yes_no)
        return

    # ============================================================
    # MODE SELECTION
    # ============================================================
    if u.get("stage") == "await_mode":
        low = (text or "").lower().strip()

        if text == "🌱 Бережно" or "береж" in low:
            u["mode"] = "easy"
        elif text == "⚙️ Стандартно" or "стандарт" in low:
            u["mode"] = "normal"
        elif text == "🔥 Собранно" or "собран" in low or "жест" in low:
            u["mode"] = "hard"
        else:
            await m.answer("Выбери режим кнопкой 👇", reply_markup=kb_mode_choice)
            return

        u["stage"] = "await_input_mode"
        await track_user_event(u, "onboarding", "mode_selected", {"mode": u["mode"]})
        await m.answer(
            f"{u.get('name') or 'Ок'}, как удобнее пройти диагностику?",
            reply_markup=kb_input_mode
        )
        return

    # ============================================================
    # INPUT MODE SELECTION
    # ============================================================
    if u["stage"] == "await_input_mode":
        low = text.lower().strip()
        if text == "🧠 Диагностика текстом" or "текст" in low:
            u["input_mode"] = "text"
            u["stage"] = "await_problem_text"
            await track_user_event(u, "onboarding", "input_mode_selected", {"input_mode": "text"})
            await track_user_event(u, "analysis", "diagnosis_started", {"input_mode": "text"})
            await m.answer("Ок. Напиши 2–5 предложений: что сейчас мешает делать важное?", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Пропустить")]], resize_keyboard=True))
            return
        if text == "🎙 Диагностика голосом" or "голос" in low:
            u["input_mode"] = "voice"
            u["stage"] = "await_problem_voice"
            await track_user_event(u, "onboarding", "input_mode_selected", {"input_mode": "voice"})
            await track_user_event(u, "analysis", "diagnosis_started", {"input_mode": "voice"})
            await m.answer("Ок. Пришли голосовое (10–30 сек): что сейчас мешает делать важное?", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Назад")]], resize_keyboard=True))
            return
        if text == "❓ Быстрый тест (5 вопросов)" or "тест" in low:
            u["input_mode"] = "test"
            u["stage"] = "taking_test"
            u["test_answers"] = []
            await track_user_event(u, "onboarding", "input_mode_selected", {"input_mode": "test"})
            await track_user_event(u, "analysis", "diagnosis_started", {"input_mode": "test"})
            first_q = TEST_QUESTIONS[0]
            msg = f"❓ Вопрос 1/5:\n\n{first_q['text']}"
            await m.answer(msg, reply_markup=create_test_question_keyboard(1))
            return
        await m.answer("Выбери кнопкой 👇", reply_markup=kb_input_mode)
        return

    # choose_input_mode
    if u["stage"] == "choose_input_mode":
        low = text.lower().strip()
        if text == "🧠 Диагностика текстом" or "текст" in low:
            u["input_mode"] = "text"
            u["stage"] = "await_problem_text"
            await save_user(u, DB_PATH)
            await m.answer("Ок. Напиши 2–5 предложений: что сейчас мешает делать важное?", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Пропустить")]], resize_keyboard=True))
            return
        if text == "🎙 Диагностика голосом" or "голос" in low:
            u["input_mode"] = "voice"
            u["stage"] = "await_problem_voice"
            await save_user(u, DB_PATH)
            await m.answer("Ок. Пришли голосовое (10–30 сек): что сейчас мешает делать важное?", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Назад")]], resize_keyboard=True))
            return
        if text == "❓ Быстрый тест (5 вопросов)" or "тест" in low:
            u["input_mode"] = "test"
            u["stage"] = "taking_test"
            u["test_answers"] = []
            await save_user(u, DB_PATH)
            first_q = TEST_QUESTIONS[0]
            msg = f"❓ Вопрос 1/5:\n\n{first_q['text']}"
            await m.answer(msg, reply_markup=create_test_question_keyboard(1))
            return
        await m.answer("Выбери кнопкой 👇", reply_markup=kb_input_mode)
        return

    # await_problem_text
    if u["stage"] == "await_problem_text":
        if not text or text.lower() == "пропустить":
            user_text = "Прокрастинация/избегание, хочу начать, но откладываю."
        else:
            user_text = text

        u["analysis_json"] = json.dumps({"user_text": clamp_str(user_text, 1000)}, ensure_ascii=False)
        u["stage"] = "run_analysis"
        await save_user(u, DB_PATH)

        wow = build_wow_analysis(user_text)
        trainer_key = u.get("trainer_key") or "marsha"
        await m.answer(trainer_say(trainer_key, wow))
        await m.answer("Ок. Детальный разбор…")
        await run_analysis(m, u, user_text, DB_PATH, SHEETS_WEBHOOK_URL, client, OPENAI_CHAT_MODEL)
        return

    # await_problem_voice
    if u["stage"] == "await_problem_voice":
        if text and text.lower() == "назад":
            u["stage"] = "await_input_mode"
            await save_user(u, DB_PATH)
            await m.answer("Ок. Выбери режим:", reply_markup=kb_input_mode)
            return
        if not m.voice:
            await m.answer("Пришли голосовое 🎙")
            return
        t = await whisper_transcribe(m)
        if not t:
            u["stage"] = "await_problem_text"
            await save_user(u, DB_PATH)
            await m.answer("Не смог разобрать голосовое. Это бывает. Можешь отправить ещё раз или написать текстом 1–3 предложения")
            return
        u["analysis_json"] = json.dumps({"user_text": clamp_str(t, 1000)}, ensure_ascii=False)
        u["stage"] = "run_analysis"
        await save_user(u, DB_PATH)
        wow = build_wow_analysis(t)
        trainer_key = u.get("trainer_key") or "marsha"
        await m.answer(trainer_say(trainer_key, wow))
        await m.answer("Ок. Детальный разбор…")
        await run_analysis(m, u, t, DB_PATH, SHEETS_WEBHOOK_URL, client, OPENAI_CHAT_MODEL)
        return

    # confirm_analysis
    if u.get("stage") == "confirm_analysis":
        low = (text or "").lower().strip()
        if text == "✅ Да, в точку" or "в точку" in low:
            u["stage"] = "analysis_contract"
            await track_user_event(u, "analysis", "analysis_accepted")
            await m.answer(
                analysis_contract_short(u.get("name") or "друг", u.get("trainer_key"), u.get("bucket")),
                reply_markup=kb_analysis_contract,
            )
            await m.answer(trainer_say(u.get("trainer_key") or "marsha", guidance_micro_phrase("point")))
            return
        if text == "🤔 Немного не так" or "не так" in low:
            u["stage"] = "analysis_refine"
            await track_user_event(u, "analysis", "analysis_refined", {"source": "confirm_analysis"})
            await m.answer(
                "Ок, уточним и пересоберём вывод.\n\n"
                "Ответь коротко (1–2 предложения):\n"
                "1) Сложнее начать или удержать?\n"
                "2) Больше тревоги или пустоты/усталости?\n"
                "3) Отвлечения — главная причина или вторично?"
            )
            return
        if text == "📚 Подробнее" or text == "ℹ️ Подробнее" or "подробнее" in low:
            comp = {}
            try:
                comp = json.loads(u.get("analysis_json") or "{}") if u.get("analysis_json") else {}
            except Exception:
                comp = {}
            u["stage"] = "analysis_more"
            await save_user(u, DB_PATH)

            trigger = (
                comp.get("why_it_happens")
                or comp.get("short_summary")
                or "напряжение перед стартом"
            )
            chain_text = render_behavior_chain([
                trigger,
                comp.get("what_is_happening", "Сейчас сложно устойчиво входить в задачу."),
                comp.get("not_your_fault_or_control_zone", "Это не про характер. Это рабочий паттерн, который можно менять шаг за шагом."),
                comp.get("training_path", "Короткий запуск, удержание фокуса и спокойный возврат."),
            ])
            timeline = comp.get("timeline", "Обычно первые изменения заметны в течение 2–3 недель регулярной практики.")

            await m.answer(
                f"{chain_text}\n\nКогда ждать первые сдвиги:\n{timeline}\n\nЭто ближе к твоей ситуации?",
                reply_markup=kb_analysis_confirm,
            )
            return
        await m.answer("Выбери кнопку 👇", reply_markup=kb_analysis_confirm)
        return

    # analysis_more
    if u.get("stage") == "analysis_more":
        low = (text or "").lower().strip()
        if text == "✅ Да, в точку" or "в точку" in low:
            u["stage"] = "analysis_contract"
            await sync_user_summary_state(u)
            await m.answer(
                analysis_contract_short(u.get("name") or "друг", u.get("trainer_key"), u.get("bucket")),
                reply_markup=kb_analysis_contract,
            )
            await m.answer(trainer_say(u.get("trainer_key") or "marsha", guidance_micro_phrase("reason")))
            return
        if text == "🤔 Немного не так" or "не так" in low:
            u["stage"] = "analysis_refine"
            await track_user_event(u, "analysis", "analysis_refined", {"source": "analysis_more"})
            await m.answer("Ок. Напиши 1–2 предложения, что именно не совпало.")
            return
        await m.answer("Посмотри, насколько это откликается, и выбери кнопку 👇", reply_markup=kb_analysis_confirm)
        return

    # analysis_contract
    if u.get("stage") == "analysis_contract":
        low = (text or "").lower().strip()
        if text == "📜 Принимаю контракт" or "принимаю" in low:
            u["stage"] = "analysis_map"
            await save_user(u, DB_PATH)
            await m.answer(month_map_text(u.get("bucket")))
            await m.answer(
                f"{guarantee_block(u.get('trainer_key'))}\n\nГотов(а) идти по этому плану?",
                reply_markup=kb_analysis_map,
            )
            return
        if text == "🤔 Немного не так" or "не так" in low:
            u["stage"] = "analysis_refine"
            await save_user(u, DB_PATH)
            await m.answer("Ок. Напиши коротко, что в контракте не подходит.")
            return
        if text == "ℹ️ Подробнее" or "подробнее" in low:
            await m.answer(
                contract_full_text(u.get("name") or "друг", u.get("trainer_key"), u.get("bucket")),
                reply_markup=kb_analysis_contract,
            )
            return
        await m.answer("Давай спокойно выберем следующий шаг 👇", reply_markup=kb_analysis_contract)
        return

    # analysis_map
    if u.get("stage") == "analysis_map":
        low = (text or "").lower().strip()
        if text == "📜 Принимаю план" or "принимаю" in low:
            u["day"] = 1
            await track_user_event(u, "analysis", "day1_started")
            await start_day(m, u, 1, DB_PATH, SHEETS_WEBHOOK_URL)
            return
        if text == "🤔 Немного не так" or "не так" in low or low == "нет":
            u["stage"] = "analysis_refine"
            await save_user(u, DB_PATH)
            await m.answer("Ок. Напиши коротко, что не совпало в плане.")
            return
        await m.answer("Можно выбрать один из вариантов ниже 👇", reply_markup=kb_analysis_map)
        return

    # analysis_retry_await_clarification
    if u.get("stage") == "analysis_retry_await_clarification":
        if not text:
            await m.answer("Напиши, пожалуйста, что не совпадает с реальностью. (1–3 предложения)")
            return
        u["analysis_json"] = json.dumps({"user_text": clamp_str(text, 1000)}, ensure_ascii=False)
        u["stage"] = "run_analysis"
        await save_user(u, DB_PATH)
        await m.answer("Ок. Переразбор…")
        await run_analysis(m, u, text, DB_PATH, SHEETS_WEBHOOK_URL, client, OPENAI_CHAT_MODEL)
        return

    # analysis_refine
    if u["stage"] == "analysis_refine":
        if not text:
            await m.answer("Напиши 1–2 предложения, чтобы я пересобрал вывод.")
            return
        # Объединяем исходный текст и уточнение, чтобы модель видела весь контекст
        base_user_text = ""
        try:
            if u.get("analysis_json"):
                prev = json.loads(u.get("analysis_json") or "{}")
                base_user_text = prev.get("user_text", "") or ""
        except Exception:
            base_user_text = ""

        combined_text = base_user_text.strip()
        if combined_text:
            combined_text += "\n\nУточнение пользователя: " + text
        else:
            combined_text = text

        u["raw_text"] = combined_text
        u["stage"] = "run_analysis"
        await save_user(u, DB_PATH)
        await m.answer("Ок. Пересобираю вывод…")
        await run_analysis(m, u, combined_text, DB_PATH, SHEETS_WEBHOOK_URL, client, OPENAI_CHAT_MODEL)
        return

    # morning_checkin
    if u.get("stage") == "morning_checkin":
        trainer_key = u.get("trainer_key") or "marsha"
        low = (text or "").lower().strip()

        mood_key = None
        if text == "тревожно" or "трев" in low:
            mood_key = "anxious"
        elif text == "не хочу начинать" or ("не хочу" in low and "нач" in low):
            mood_key = "resistant"
        elif text == "пусто / нет сил" or "нет сил" in low or "пусто" in low:
            mood_key = "empty"
        elif text == "отвлекаюсь" or "отвлек" in low:
            mood_key = "distracted"
        elif text == "нормально, идём" or "нормально" in low:
            mood_key = "ok"
        elif text == "напишу сам":
            u["stage"] = "morning_checkin_custom"
            await save_user(u, DB_PATH)
            await m.answer(
                trainer_say(trainer_key, "Ок. Напиши коротко, что сейчас больше всего мешает войти в день."),
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="тревожно"), KeyboardButton(text="не хочу начинать")],
                              [KeyboardButton(text="пусто / нет сил"), KeyboardButton(text="отвлекаюсь")],
                              [KeyboardButton(text="нормально, идём")]],
                    resize_keyboard=True,
                ),
            )
            return

        if not mood_key:
            await m.answer("Выбери вариант ниже или нажми 'напишу сам'.", reply_markup=kb_morning_checkin)
            return

        u["stage"] = "await_training_target"
        await save_user(u, DB_PATH)
        await m.answer(trainer_say(trainer_key, get_morning_checkin_ack(trainer_key, mood_key)))
        await ask_training_target(m)
        return

    # morning_checkin_custom
    if u.get("stage") == "morning_checkin_custom":
        trainer_key = u.get("trainer_key") or "marsha"
        if not text:
            await m.answer("Напиши коротко: одной фразой.")
            return

        u["stage"] = "await_training_target"
        await save_user(u, DB_PATH)
        await m.answer(trainer_say(trainer_key, get_morning_checkin_ack(trainer_key, "custom")))
        await ask_training_target(m)
        return

    # Вопрос перед выдачей навыка
    if u.get("stage") == "await_training_target":
        raw_target = (text or "").strip()
        target = clamp_str(raw_target, 200)

        if not target or target.lower() == "пропустить":
            default_targets = {
                "anxiety": "открыть задачу и побыть с ней 2 минуты",
                "low_energy": "сделать самый маленький шаг без давления",
                "distractibility": "открыть задачу и вернуть внимание 1 раз",
                "mixed": "начать с одного короткого шага",
            }
            bucket = u.get("bucket") or "mixed"
            target = default_targets.get(bucket, "начать с одного короткого шага")

        target = target.replace("пропускаю", "").strip()
        if not target:
            target = "начать с одного короткого шага"

        day = int(u.get("pending_skill_day") or u.get("day") or 1)
        plan = get_current_plan(u)
        sid = u.get("pending_skill_id")
        if not sid or sid not in SKILLS_DB:
            if plan:
                idx = max(0, min(len(plan) - 1, day - 1))
                sid = plan[idx]
            else:
                sid = next(iter(SKILLS_DB.keys()))

        trainer_key = u.get("trainer_key") or "marsha"
        skill = SKILLS_DB.get(sid) or list(SKILLS_DB.values())[0]
        how_text = skill_explain(trainer_key, skill)
        minimum = skill.get("minimum") or skill.get("micro") or ""
        msg = (
            f"📌 На чём тренируемся сегодня: {target}\n\n"
            f"🧩 Навык дня: {skill['name']}\n"
            f"🎯 Цель: {skill['goal']}\n"
            f"✅ Как: {how_text}"
        )
        if minimum:
            msg += f"\nМинимум: {minimum}"

        u["today_target"] = target
        u["pending_skill_id"] = None
        u["pending_skill_day"] = None
        u["stage"] = "training"
        await track_user_event(u, "training", "target_set", {"day": day, "text": target})

        await m.answer(trainer_say(trainer_key, msg), reply_markup=kb_training_main)
        await m.answer(gamify_status_line(u))
        return

    # TRAINING stage
    if u.get("stage") == "training":
        low = text.lower().strip()
        day = int(u.get("day") or 1)

        if text == "💪 Давай тренировать навык" or ("давай" in low and "трен" in low):
            plan = get_current_plan(u)
            idx = max(0, min(len(plan) - 1, int(u.get("day") or 1) - 1))
            sid = plan[idx]
            skill = SKILLS_DB.get(sid, {})
            detail = skill_detail_text(skill)
            trainer_key = u.get("trainer_key") or "marsha"
            prompt = (
                "Делаем серию коротких подходов: 3–4 раза за сегодня, если есть ресурс. "
                "Каждый подход ≤120 сек. Нажимай эту кнопку, когда готов к новому кругу, "
                "и после попытки отмечай результат кнопкой "
                "'✅ Сделал(а)' или '↩️ Вернулся(лась)'."
            )
            await track_user_event(u, "training", "repeat_practice", {"day": day, "sid": sid})
            await m.answer(trainer_say(trainer_key, f"{detail}\n\n{prompt}"), reply_markup=kb_training_main)
            return

        if text == "ℹ️ Подробнее про навык" or text == "📚 Подробнее":
            plan = get_current_plan(u)
            idx = max(0, min(len(plan) - 1, int(u.get("day") or 1) - 1))
            sid = plan[idx]
            skill = SKILLS_DB.get(sid, {})
            msg = skill_detail_text(skill)

            u["stage"] = "training_skill_more"
            await save_user(u, DB_PATH)

            await m.answer(msg, reply_markup=kb_more_clarify)
            return

        if text == "👍 Понял(а), продолжаем" or text == "📚 Подробнее почему это работает" or "подробнее почему" in low:
            trainer_key = u.get("trainer_key") or "marsha"
            if text == "👍 Понял(а), продолжаем" or ("понял" in low and "подробнее" not in low):
                await log_event(u["user_id"], "training", "doubt_understood", {"trainer": trainer_key}, DB_PATH, SHEETS_WEBHOOK_URL)
                await m.answer(trainer_say(trainer_key, PRAISE.get(trainer_key, "Идём дальше!")), reply_markup=kb_training_main)
                return
            else:
                await log_event(u["user_id"], "training", "doubt_details_requested", {"trainer": trainer_key}, DB_PATH, SHEETS_WEBHOOK_URL)
                if trainer_key == "skinny":
                    details_text = "📊 Почему микро-тренули работают:\n\n• 60 сек — это минимум для активации нейро-связей\n• Повторяемость важнее объёма\n• 3 дня подряд = установка нового паттерна\n• Эффект накапливается. Видно на день 3-4.\n\nСделал → умеешь. Так работает мозг."
                elif trainer_key == "beck":
                    details_text = "🧬 Нейро-механика повторения:\n\n• Синапс усиливается при каждом выполнении (Hebb's Law)\n• Миелинизация идёт на 3-7 день регулярности\n• Метрика done/return показывает адаптацию мозга\n• Долгосрочная потенциация = стабильный навык\n\nГрафики покажут, когда функция встроилась."
                else:
                    details_text = "🌱 Как работает безопасный рост:\n\n• Микро-шаги = нет перегрузки и стыда\n• Повтор = уверенность, не сомнения\n• Каждый успех закраски невидимым рост\n• Если день не пошёл — просто возвращаемся завтра\n\nЭффект видно не на неделе, а на двух."
                await m.answer(trainer_say(trainer_key, details_text), reply_markup=kb_training_main)
                return

        if text == "Ты меня не понял" or "не понял" in low:
            u["analysis_retry_count"] = int(u.get("analysis_retry_count") or 0) + 1
            retry_count = u["analysis_retry_count"]
            if retry_count > 2:
                u["stage"] = "training"
                await save_user(u, DB_PATH)
                await log_event(u["user_id"], "analysis", "retry_limit_reached", {}, DB_PATH, SHEETS_WEBHOOK_URL)
                await m.answer(trainer_say(u["trainer_key"], "Я уже трижды пытался понять. 😊\n\nДавай начнём тренировку и посмотрим, как это будет работать в жизни.\n\nМожет быть, это станет яснее когда ты начнёшь."), reply_markup=kb_training_main)
                await start_day(m=m, u=u, day=1, db_path=DB_PATH, sheets_webhook=SHEETS_WEBHOOK_URL)
                return
            await save_user(u, DB_PATH)
            u["stage"] = "analysis_retry_await_clarification"
            await save_user(u, DB_PATH)
            await m.answer(trainer_say(u["trainer_key"], f"Ок. Уточни ещё раз (попытка {retry_count}/2):\n\nЧто конкретно здесь не правда? Расскажи подробнее."))
            return

        if text == "🆘 Кризис" or "кризис" in low:
            u["stage"] = "crisis_choose_mode"
            await track_user_event(u, u["stage"], "crisis_open")
            await m.answer("🆘 Ок. Как удобнее?", reply_markup=kb_crisis_mode)
            return

        if text == "📊 Мой прогресс" or "мой прогресс" in low or "прогресс" in low:
            await send_progress_report(m, u, DB_PATH)
            return

        if text == "✅ Сделал(а)" or "сделал" in low:
            u["done_count"] = int(u.get("done_count") or 0) + 1
            gamify_apply(u, 2, "done")
            progress = increment_starts_progress(u)
            trainer = u.get("trainer_key")
            # 1️⃣ Базовая реакция
            if trainer == "skinny":
                await m.answer("🐈‍⬛ Сделал. Факт есть. Это тренировка.")
                await m.answer("Что ты почувствовал во время выполнения?")
            elif trainer == "marsha":
                await m.answer("🐶 Я рада, что ты попробовал. Это шаг.")
                await m.answer("Как тебе было это делать?")
            else:
                await m.answer("🧠 Фиксируем опыт. Это формирование навыка.")
                await m.answer("Что ты заметил во время выполнения?")
            # post_done_reflection этап убран, сразу переходим к следующему этапу
            u["stage"] = "waiting_next_day"
            await track_user_event(u, "training", "done", {"day": day})
            await m.answer(trainer_say(u.get("trainer_key") or "marsha", guidance_micro_phrase("progress")))
            await m.answer(trainer_say(u.get("trainer_key") or "marsha", emotional_hook(day, progress)))
            await m.answer("Завтра будет чуть легче, чем сегодня.")
            await save_user(u, DB_PATH)
            return

        if text == "↩️ Вернулся(лась)" or "вернулся" in low:
            u["return_count"] = int(u.get("return_count") or 0) + 1
            gamify_apply(u, 1, "return")
            progress = increment_starts_progress(u)
            await track_user_event(u, "training", "return", {"day": day})

            await m.answer(trainer_say(u.get("trainer_key") or "marsha", "Возврат засчитан. Это ключевой навык."))
            await m.answer(trainer_say(u.get("trainer_key") or "marsha", guidance_micro_phrase("reason")))
            await m.answer(trainer_say(u.get("trainer_key") or "marsha", emotional_hook(day, progress)))

            u["stage"] = "after_return_choice"
            await save_user(u, DB_PATH)

            await m.answer(
                "Хочешь ещё один короткий круг сейчас или на сегодня достаточно?",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text="💪 Ещё один круг")],
                        [KeyboardButton(text="🌙 На сегодня достаточно")],
                    ],
                    resize_keyboard=True,
                ),
            )
            return

        if text == "❓ Сомневаюсь, работает ли" or "сомневаюсь" in low:
            trainer_key = u.get("trainer_key") or "marsha"
            await log_event(u["user_id"], "training", "doubt_pressed", {"trainer": trainer_key}, DB_PATH, SHEETS_WEBHOOK_URL)
            if trainer_key == "skinny":
                doubt_text = "Поможет/не поможет — узнаем только выполнением 60 секунд.\n\nФакт есть или факта нет.\nТретьего не дано.\n\nДелай сегодня — увидишь завтра."
            elif trainer_key == "beck":
                doubt_text = "Это не вопрос веры, это вопрос эффекта.\n\nТренинг навыков работает через повторение.\nМы измеряем микро-метриками: done/return.\n\nЧерез 2 недели будет график нейро-адаптации."
            else:
                doubt_text = "Сомнение нормально.\n\nМы проверяем не верой, а маленькими фактами.\nКаждый день — один факт за 60 секунд.\n\nЕсли не подходит — меняем инструмент."
            await m.answer(trainer_say(trainer_key, doubt_text), reply_markup=kb_doubt_response)
            return

        if "не пошло" in low or "не подходит" in low or "не работает" in low or text == "🔁 Заменить навык" or "заменить" in low:
            await log_event(u["user_id"], "training", "skill_replace_requested", {"day": day, "reason": text or "button"}, DB_PATH, SHEETS_WEBHOOK_URL)

            plan = get_current_plan(u)
            if not plan:
                await m.answer(trainer_say(u.get("trainer_key") or "marsha", "План пуст — нет что заменить. Сообщи поддержке."))
                return

            idx = max(0, min(len(plan) - 1, day - 1))
            current_sid = plan[idx]
            current_skill = SKILLS_DB.get(current_sid, {})
            track = current_skill.get("track") or u.get("bucket") or "mixed"
            new_sid = suggest_alternative_skill(track, current_sid) or current_sid
            if new_sid == current_sid:
                # попытка выбрать любой другой по треку
                alt = [k for k, v in SKILLS_DB.items() if v.get("track") == track and k != current_sid]
                if alt:
                    new_sid = alt[0]

            plan[idx] = new_sid
            u["plan_json"] = json.dumps(plan, ensure_ascii=False)
            await save_user(u, DB_PATH)

            skill_msg = format_skill(new_sid, u.get("trainer_key") or "marsha") if new_sid in SKILLS_DB else "Выбран новый навык."
            await m.answer(trainer_say(u.get("trainer_key") or "marsha", "Ты не откатился.\nТы всё ещё в процессе."))
            await m.answer(trainer_say(u.get("trainer_key") or "marsha", f"Меняю на {SKILLS_DB[new_sid]['name']}" if new_sid in SKILLS_DB else "Меняю навык."))
            await m.answer(skill_msg, reply_markup=kb_training_main)
            return

        await m.answer("Выбери кнопку 👇", reply_markup=kb_training_main)
        return

    if u.get("stage") == "training_skill_more":
        low = (text or "").lower().strip()

        if text == "⬅️ Назад" or "назад" in low:
            u["stage"] = "training"
            await save_user(u, DB_PATH)
            await m.answer("Ок. Возвращаемся к тренировке.", reply_markup=kb_training_main)
            return

        if text == "Ты меня не понял" or "не понял" in low:
            u["stage"] = "training_clarify"
            await save_user(u, DB_PATH)
            await m.answer(
                "Скажи коротко: где главный стоп сейчас?\n"
                "— начать\n"
                "— удержаться\n"
                "— тревога\n"
                "— хаос"
            )
            return

        await m.answer("Выбери кнопку 👇", reply_markup=kb_more_clarify)
        return

    if u.get("stage") == "training_clarify":
        low = (text or "").lower().strip()

        if "нач" in low:
            u["clarify_stop"] = "start"
        elif "удерж" in low:
            u["clarify_stop"] = "hold"
        elif "трев" in low:
            u["clarify_stop"] = "anxiety"
        elif "хаос" in low:
            u["clarify_stop"] = "chaos"
        else:
            u["clarify_stop"] = "mixed"

        u["stage"] = "await_training_target"
        await save_user(u, DB_PATH)

        await m.answer(
            trainer_say(
                u.get("trainer_key") or "marsha",
                "Ок. Теперь не в общих словах. Назови одну реальную задачу, на которой потренируемся прямо сейчас."
            )
        )
        return

    if u.get("stage") == "after_return_choice":
        if text == "💪 Ещё один круг":
            u["stage"] = "training"
            await save_user(u, DB_PATH)
            await m.answer("Ок. Ещё один короткий подход.", reply_markup=kb_training_main)
            return

        if text == "🌙 На сегодня достаточно":
            day = int(u.get("day") or 1)

            if day == 7:
                await send_weekly_summary(m, u, DB_PATH)

            if payments_enabled() and day == 3 and u.get("trial_phase") == "trial3":
                # PATCH 2: Show weekly plan
                await m.answer(build_week_plan(u))
                
                # PATCH 2: Context message (pause)
                await m.answer(
                    "Это не теория.\n"
                    "Это конкретные действия каждый день.\n\n"
                    "И это только начало."
                )
                
                # PATCH 1: Show payment offer with new framing
                await m.answer(build_payment_offer(u), reply_markup=kb_payment_continue)
                u["stage"] = "offer_day3"
                await track_user_event(u, "offer", "offer_shown", {"variant": "discount_day3"})
                return

            if payments_enabled() and day >= 7 and u.get("trial_phase") in ("trial3", "trial7", None):
                await m.answer("Выбирай вариант оплаты:", reply_markup=kb_pay_choice)
                u["stage"] = "offer"
                await track_user_event(u, "offer", "offer_shown", {"variant": "full_day7"})
                return

            await start_day(m, u, day + 1, DB_PATH, SHEETS_WEBHOOK_URL)
            return

        await m.answer(
            "Выбери кнопкой 👇",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="💪 Ещё один круг")],
                    [KeyboardButton(text="🌙 На сегодня достаточно")],
                ],
                resize_keyboard=True,
            ),
        )
        return

    # crisis_choose_mode
    if u.get("stage") == "crisis_choose_mode":
        low = (text or "").lower().strip()

        # Если сразу прислал голосовое — обрабатываем без лишних шагов
        if m.voice:
            t = await whisper_transcribe(m)
            if t:
                await handle_crisis(m, u, t, DB_PATH, SHEETS_WEBHOOK_URL, client, OPENAI_CHAT_MODEL)
                return
            await m.answer("Не смог разобрать голос. Напиши 1–3 предложения.")
            u["stage"] = "crisis_text"
            await save_user(u, DB_PATH)
            return

        if text == "⬅️ Назад" or "назад" in low:
            u["stage"] = "training"
            await save_user(u, DB_PATH)
            await m.answer("Ок. Возвращаемся в тренировку.", reply_markup=kb_training_main)
            return
        if text == "🎙 Кризис голосом" or "голос" in low:
            u["stage"] = "crisis_voice"
            await save_user(u, DB_PATH)
            await m.answer("🎙 Запиши голосом: что происходит и что мешает прямо сейчас?")
            return
        if text == "✍️ Кризис текстом" or "текст" in low:
            u["stage"] = "crisis_text"
            await save_user(u, DB_PATH)
            await m.answer("✍️ Напиши: что происходит и что мешает прямо сейчас? (1–3 предложения)")
            return
        if text:
            # Любой текст без выбора — сразу кризис-текст
            await handle_crisis(m, u, text, DB_PATH, SHEETS_WEBHOOK_URL, client, OPENAI_CHAT_MODEL)
            return
        await m.answer("Выбери кнопкой 👇", reply_markup=kb_crisis_mode)
        return

    if u.get("stage") == "crisis_text":
        if text and text.lower().strip() in {"⬅️ назад", "назад"}:
            u["stage"] = "training"
            await save_user(u, DB_PATH)
            await m.answer("Ок. Возвращаемся в тренировку.", reply_markup=kb_training_main)
            return
        if not text:
            await m.answer("Напиши 1–3 предложения.")
            return
        await handle_crisis(m, u, text, DB_PATH, SHEETS_WEBHOOK_URL, client, OPENAI_CHAT_MODEL)
        return

    if u.get("stage") == "crisis_voice":
        if text and text.lower().strip() in {"⬅️ назад", "назад"}:
            u["stage"] = "training"
            await save_user(u, DB_PATH)
            await m.answer("Ок. Возвращаемся в тренировку.", reply_markup=kb_training_main)
            return
        if not m.voice:
            await m.answer("Пришли голосовое 🎙")
            return
        t = await whisper_transcribe(m)
        if not t:
            await m.answer("Не смог разобрать голосовое. Это бывает. Можешь отправить ещё раз или написать текстом 1–3 предложения")
            u["stage"] = "crisis_text"
            await save_user(u, DB_PATH)
            return
        await handle_crisis(m, u, t, DB_PATH, SHEETS_WEBHOOK_URL, client, OPENAI_CHAT_MODEL)
        return

    if u.get("stage") == "crisis_plan_confirm":
        low = text.lower().strip()
        if text == "✅ Да" or "да" in low:
            pending = json.loads(u.get("pending_plan_change") or "{}") if u.get("pending_plan_change") else {}
            day_num = pending.get("day_num")
            sid = pending.get("skill_id")
            if day_num and sid:
                propose_plan_override(u, int(day_num), sid)
                u["pending_plan_change"] = None
                await save_user(u, DB_PATH)
                await log_event(u["user_id"], u.get("stage", ""), "plan_change_accept", {"day": day_num, "skill": sid}, DB_PATH, SHEETS_WEBHOOK_URL)
                await m.answer("✅ Ок. Я обновил план. Завтра будет эта версия.")
            u["stage"] = "training"
            await save_user(u, DB_PATH)
            await m.answer("Возвращаемся в тренировку.", reply_markup=kb_training_main)
            return
        if text == "❌ Нет" or "нет" in low:
            u["pending_plan_change"] = None
            u["stage"] = "training"
            await save_user(u, DB_PATH)
            await log_event(u["user_id"], u.get("stage", ""), "plan_change_reject", {}, DB_PATH, SHEETS_WEBHOOK_URL)
            await m.answer("Ок. План не меняю. Возвращаемся.", reply_markup=kb_training_main)
            return
        await m.answer("Выбери: ✅ Да / ❌ Нет", reply_markup=kb_yes_no)
        return

    # OFFER_DAY3 stage (new payment moment with continue/think buttons)
    if u.get("stage") == "offer_day3":
        if not payments_enabled():
            u["stage"] = "training"
            await track_user_event(u, "payment", "payment_bypassed", {"reason": "payments_disabled"})
            await m.answer("Сейчас идёт тестовый запуск. Продолжаем без оплаты.", reply_markup=kb_training_main)
            return

        low = text.lower().strip()

        if text == "💳 Продолжить" or "продолж" in low:
            await track_user_event(u, "payment", "continue_clicked", {"variant": "discount_day3"})
            u["stage"] = "offer"
            await m.answer("Ок. Выбирай вариант оплаты:", reply_markup=kb_pay_choice)
            return

        if text == "🤔 Пока подумаю" or "подумаю" in low or "думаю" in low:
            await track_user_event(u, "payment", "offer_hesitation", {})
            await m.answer(build_hesitation_response())
            await asyncio.sleep(1)
            await m.answer(build_payment_offer(u), reply_markup=kb_payment_continue)
            return

        await m.answer("Выбери кнопкой 👇", reply_markup=kb_payment_continue)
        return

    # OFFER stage
    if u.get("stage") == "offer":
        if not payments_enabled():
            u["stage"] = "training"
            await track_user_event(u, "payment", "payment_bypassed", {"reason": "payments_disabled"})
            await m.answer("Сейчас идёт тестовый запуск. Продолжаем без оплаты.", reply_markup=kb_training_main)
            return

        low = text.lower().strip()

        if text == "💳 Оплатить со скидкой" or "со скидкой" in low:
            await track_user_event(u, "payment", "payment_clicked", {"variant": "discount"})
            await m.answer("Ок. Скидка по ссылке 👇")
            await m.answer(" ", reply_markup=payment_inline_discount(PAYMENT_URL_DISCOUNT))
            return

        if text == "💳 Оплатить без скидки" or "без скидки" in low:
            await track_user_event(u, "payment", "payment_clicked", {"variant": "full"})
            await m.answer("Ок. Полная цена по ссылке 👇")
            await m.answer(" ", reply_markup=payment_inline_full(PAYMENT_URL_FULL))
            return

        if text == "➕ Ещё 4 дня без оплаты" or "ещё" in low or "дня" in low:
            u["trial_days"] = 7
            u["trial_phase"] = "trial7"
            u["stage"] = "training"
            await track_user_event(u, "payment", "trial_extended", {"days": 4})
            await m.answer("Ок. Добавил ещё 4 дня. Продолжаем.", reply_markup=kb_training_main)
            return

        if text == "❌ Не готов(а)" or "не готов" in low:
            u["stage"] = "training"
            await track_user_event(u, "payment", "offer_declined", {})
            await m.answer("Ок. Тогда пока просто продолжаем тренировку без оплаты.", reply_markup=kb_training_main)
            return

        await m.answer("Выбирай кнопкой 👇", reply_markup=kb_pay_choice)
        return

    # Если дошли до сюда — неизвестный этап, выводим stage для отладки
    stage = str(u.get('stage')).replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('`', '\\`')
    if stage != "post_done_reflection":
        await m.answer(f"Неизвестный этап (stage): {stage}. Напиши /start чтобы начать заново или обратись к поддержке.", parse_mode=None)

# ============================================================
# CALLBACKS
# ============================================================

@router.callback_query(F.data.in_({"yes", "no", "noop"}))
async def on_callbacks(c: CallbackQuery):
    uid = c.from_user.id
    u = await get_user(uid, DB_PATH)
    if c.data == "noop":
        await c.answer()
        return
    if u.get("stage") == "confirm_analysis":
        if c.data == "yes":
            u["stage"] = "analysis_contract"
            await save_user(u, DB_PATH)
            await c.message.answer(
                analysis_contract_short(u.get("name") or "друг", u.get("trainer_key"), u.get("bucket")),
                reply_markup=kb_analysis_contract,
            )
        else:
            u["stage"] = "analysis_refine"
            await save_user(u, DB_PATH)
            await c.message.answer("Ок. Напиши 1–2 предложения, что не совпало в разборе.")
        await c.answer()
        return
    await c.answer()

@router.callback_query(F.data.startswith("test_q"))
async def on_test_answer(c: CallbackQuery):
    uid = c.from_user.id
    u = await get_user(uid, DB_PATH)
    try:
        parts = c.data.split("_")
        if len(parts) < 3:
            await c.answer("Ошибка в данных")
            return
        q_num = int(parts[1][1:])
        bucket_answer = "_".join(parts[2:])
        test_answers = u.get("test_answers") or []
        test_answers.append(bucket_answer)
        u["test_answers"] = test_answers
        await save_user(u, DB_PATH)
        if len(test_answers) < len(TEST_QUESTIONS):
            next_q_num = len(test_answers) + 1
            next_q = next((x for x in TEST_QUESTIONS if x["id"] == next_q_num), None)
            if next_q:
                await c.message.edit_text(f"❓ Вопрос {next_q_num}/5:\n\n{next_q['text']}", reply_markup=create_test_question_keyboard(next_q_num))
            await c.answer()
        else:
            resolved_bucket = resolve_bucket_from_test(test_answers)
            u["bucket"] = resolved_bucket
            u["test_answers"] = []
            u["stage"] = "test_complete_show_analysis"
            await save_user(u, DB_PATH)
            await show_comprehensive_analysis(c.message, u)
            await c.answer()
    except Exception as e:
        log.error(f"Error in test callback: {e}")
        await c.answer("Ошибка обработки ответа")

async def show_comprehensive_analysis(m: Message, u: Dict[str, Any]):
    bucket = u.get("bucket") or "mixed"
    user_text = ""
    if u.get("analysis_json"):
        try:
            analysis_data = json.loads(u.get("analysis_json") or "{}")
            user_text = analysis_data.get("user_text", "")
        except:
            pass
    if not user_text:
        user_text = f"У меня проблемы с {bucket}"
    comp = await ai_analyze_comprehensive(user_text, u.get("trainer_key", "marsha"), client, OPENAI_CHAT_MODEL)
    u["analysis_json"] = json.dumps(comp, ensure_ascii=False)
    u["bucket"] = comp.get("bucket", bucket)
    plan_ids = build_28_day_plan(u["bucket"])
    u["plan_json"] = json.dumps(plan_ids, ensure_ascii=False)
    u["day"] = 1
    u["stage"] = "confirm_analysis"
    await save_user(u, DB_PATH)
    await log_event(u["user_id"], "analysis", "analysis_shown", {"bucket": u.get("bucket")}, DB_PATH, SHEETS_WEBHOOK_URL)
    msg = f"{comp.get('short_summary', 'Похоже на тебя?')}\n\nЭто похоже на тебя?"
    await m.answer(msg, reply_markup=kb_analysis_confirm)

# ============================================================
# WHISPER TRANSCRIBE
# ============================================================

async def whisper_transcribe(m: Message) -> Optional[str]:
    from_user = getattr(m, "from_user", None)
    uid = from_user.id if from_user else "unknown"
    log.info("[WHISPER] start uid=%s", uid)

    if not (AI_ANALYSIS_ENABLED and client):
        log.warning("[WHISPER] skipped: AI disabled or client is None")
        return None

    if not m.voice:
        log.warning("[WHISPER] skipped: no voice in message")
        return None

    file_id = m.voice.file_id
    duration = getattr(m.voice, "duration", None)
    log.info("[WHISPER] voice received file_id=%s duration=%s", file_id, duration)

    try:
        log.info("[WHISPER] step=telegram.get_file")
        file = await m.bot.get_file(file_id)
        if not file or not file.file_path:
            log.warning("[WHISPER] step=telegram.get_file result=empty_path")
            return None

        log.info("[WHISPER] step=telegram.download_file path=%s", file.file_path)
        fp = await m.bot.download_file(file.file_path)
        data = fp.read() if fp else b""
        size = len(data) if data else 0
        log.info("[WHISPER] step=telegram.download_file done bytes=%s", size)

        if not data:
            log.warning("[WHISPER] downloaded empty file")
            return None

        import io
        bio = io.BytesIO(data)
        bio.name = "voice.ogg"

        log.info("[WHISPER] step=openai.transcribe model=%s", OPENAI_WHISPER_MODEL)
        tr = client.audio.transcriptions.create(
            model=OPENAI_WHISPER_MODEL,
            file=bio
        )
        log.info("[WHISPER] step=openai.transcribe done")

        text = getattr(tr, "text", None)
        if not text:
            try:
                text = tr["text"]
            except Exception:
                text = None

        text = (text or "").strip()
        if not text:
            log.warning("[WHISPER] finish: empty transcription")
            return None

        log.info("[WHISPER] finish: ok chars=%s preview=%r", len(text), text[:120])
        return text
    except Exception:
        log.exception("[WHISPER] fail uid=%s", uid)
        return None

# ============================================================
# BACKGROUND TASKS
# ============================================================

async def background_ping(bot):
    while True:
        now_ts = time.time()
        now_local = datetime.now()

        def _is_same_day(ts: float) -> bool:
            if not ts:
                return False
            try:
                return datetime.fromtimestamp(float(ts)).date() == now_local.date()
            except Exception:
                return False

        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM users")
            rows = await cur.fetchall()

        for row in rows:
            u = dict(row)
            stage = u.get("stage")
            if stage not in {"training", "waiting_next_day"}:
                continue

            day_started_at = float(u.get("day_started_at") or 0)
            if not _is_same_day(day_started_at):
                continue

            trainer_key = u.get("trainer_key") or "marsha"
            name = (u.get("name") or "").strip()
            chat_id = u.get("chat_id")
            if not chat_id:
                continue

            last_active = float(u.get("last_active") or 0)
            inactive_seconds = now_ts - last_active if last_active else 10**9

            # Дневной пинг: пользователь начал день, но долго не пишет.
            if 11 <= now_local.hour < 19 and inactive_seconds >= 3 * 3600:
                if not _is_same_day(float(u.get("last_day_ping_at") or 0)):
                    try:
                        u["last_day_ping_at"] = now_ts
                        await bot.send_message(chat_id, trainer_say(trainer_key, daytime_ping(trainer_key, name)))
                        await track_user_event(
                            u,
                            "training",
                            "day_ping_sent",
                            {
                                "inactive_hours": round(inactive_seconds / 3600, 2),
                                "hour": now_local.hour,
                            },
                        )
                        await save_user(u, DB_PATH)
                    except Exception as e:
                        log.warning(f"Не удалось отправить дневной пинг {chat_id}: {e}")

            # Вечернее закрытие: один из двух вопросов + варианты ответа.
            if 20 <= now_local.hour < 23:
                if not _is_same_day(float(u.get("last_evening_prompt_at") or 0)):
                    try:
                        await bot.send_message(
                            chat_id,
                            trainer_say(trainer_key, evening_close_question(trainer_key)),
                            reply_markup=kb_evening_close,
                        )
                        u["last_evening_prompt_at"] = now_ts
                        u["evening_return_stage"] = stage
                        u["stage"] = "evening_close_wait"
                        await save_user(u, DB_PATH)
                    except Exception as e:
                        log.warning(f"Не удалось отправить вечернее закрытие {chat_id}: {e}")
        for row in rows:
            u = dict(row)
            stage = u.get("stage")

            # Не трогаем пользователей в ожидании ответа
            if stage in {"evening_close_wait", "reactivation_wait"}:
                continue

            trainer_key = u.get("trainer_key") or "marsha"
            name = (u.get("name") or "").strip()
            chat_id = u.get("chat_id")
            if not chat_id:
                continue

            last_active = float(u.get("last_active") or 0)
            inactive_seconds = now_ts - last_active if last_active else 10**9
            day_started_at = float(u.get("day_started_at") or 0)

            # ── Дневной пинг + вечернее закрытие ──
            # только для тренирующихся, начавших день сегодня
            if stage in {"training", "waiting_next_day"} and _is_same_day(day_started_at):

                # Анти-слив дни 1–3: прицельный nudge при первой неактивности
                day_num = int(u.get("day") or 1)
                if day_num in {1, 2, 3} and inactive_seconds >= 2 * 3600:
                    if not _is_same_day(float(u.get("last_day_ping_at") or 0)):
                        hours_passed = round(inactive_seconds / 3600, 1)
                        msg = anti_churn_message(
                            u.get("trainer_key") or "marsha",
                            u.get("mode") or "normal",
                            day_num,
                        )
                        try:
                            u["last_day_ping_at"] = now_ts
                            await bot.send_message(
                                chat_id,
                                trainer_say(trainer_key, msg),
                                reply_markup=kb_training_main,
                            )
                            await track_user_event(
                                u,
                                "training",
                                "anti_churn_ping",
                                {"day": day_num, "inactive_hours": hours_passed},
                            )
                            await save_user(u, DB_PATH)
                        except Exception as e:
                            log.warning(f"Не удалось отправить anti_churn {chat_id}: {e}")
                        continue  # не дублируем дневной пинг в тот же час

                # Дневной пинг: пользователь начал день, но долго не пишет.
                if 11 <= now_local.hour < 19 and inactive_seconds >= 3 * 3600:
                    if not _is_same_day(float(u.get("last_day_ping_at") or 0)):
                        try:
                            u["last_day_ping_at"] = now_ts
                            await bot.send_message(chat_id, trainer_say(trainer_key, daytime_ping(trainer_key, name)))
                            await track_user_event(
                                u,
                                "training",
                                "day_ping_sent",
                                {
                                    "inactive_hours": round(inactive_seconds / 3600, 2),
                                    "hour": now_local.hour,
                                },
                            )
                            await save_user(u, DB_PATH)
                        except Exception as e:
                            log.warning(f"Не удалось отправить дневной пинг {chat_id}: {e}")

                # Вечернее закрытие: один из двух вопросов + варианты ответа.
                if 20 <= now_local.hour < 23:
                    if not _is_same_day(float(u.get("last_evening_prompt_at") or 0)):
                        try:
                            await bot.send_message(
                                chat_id,
                                trainer_say(trainer_key, evening_close_question(trainer_key)),
                                reply_markup=kb_evening_close,
                            )
                            u["last_evening_prompt_at"] = now_ts
                            u["evening_return_stage"] = stage
                            u["stage"] = "evening_close_wait"
                            await save_user(u, DB_PATH)
                        except Exception as e:
                            log.warning(f"Не удалось отправить вечернее закрытие {chat_id}: {e}")

            # ── Реактивация молчащих ──
            # только если пользователь начинал тренировку, но сегодня не появлялся
            _REACTIVATION_STAGES = {
                "training", "waiting_next_day", "morning_checkin",
                "morning_checkin_custom", "await_training_target",
            }
            if (
                int(u.get("has_started_training") or 0) == 1
                and stage in _REACTIVATION_STAGES
                and not _is_same_day(day_started_at)
                and 10 <= now_local.hour < 22
            ):
                level = int(u.get("reactivation_level") or 0)

                if inactive_seconds >= 7 * 86400 and level < 4:
                    try:
                        u["reactivation_level"] = 4
                        u["evening_return_stage"] = stage
                        u["stage"] = "reactivation_wait"
                        await bot.send_message(
                            chat_id,
                            trainer_say(trainer_key, reactivation_7d(trainer_key, name)),
                            reply_markup=kb_reactivation,
                        )
                        await track_user_event(
                            u,
                            "reactivation",
                            "no_response_7d",
                            {"inactive_hours": round(inactive_seconds / 3600, 1)},
                        )
                        await save_user(u, DB_PATH)
                    except Exception as e:
                        log.warning(f"Не удалось отправить реактивацию 7d {chat_id}: {e}")

                elif inactive_seconds >= 3 * 86400 and level < 3:
                    try:
                        u["reactivation_level"] = 3
                        u["evening_return_stage"] = stage
                        u["stage"] = "reactivation_wait"
                        await bot.send_message(
                            chat_id,
                            trainer_say(trainer_key, reactivation_3d(trainer_key, name)),
                            reply_markup=kb_reactivation,
                        )
                        await track_user_event(
                            u,
                            "reactivation",
                            "no_response_3d",
                            {"inactive_hours": round(inactive_seconds / 3600, 1)},
                        )
                        await save_user(u, DB_PATH)
                    except Exception as e:
                        log.warning(f"Не удалось отправить реактивацию 3d {chat_id}: {e}")

                elif inactive_seconds >= 24 * 3600 and level < 2:
                    try:
                        u["reactivation_level"] = 2
                        await bot.send_message(
                            chat_id,
                            trainer_say(trainer_key, reactivation_24h(trainer_key, name)),
                        )
                        await track_user_event(
                            u,
                            "reactivation",
                            "no_response_24h",
                            {"inactive_hours": round(inactive_seconds / 3600, 1)},
                        )
                        await save_user(u, DB_PATH)
                    except Exception as e:
                        log.warning(f"Не удалось отправить реактивацию 24h {chat_id}: {e}")

                elif inactive_seconds >= 6 * 3600 and level < 1:
                    try:
                        u["reactivation_level"] = 1
                        await bot.send_message(
                            chat_id,
                            trainer_say(trainer_key, reactivation_6h(trainer_key, name)),
                        )
                        await track_user_event(
                            u,
                            "reactivation",
                            "no_response_6h",
                            {"inactive_hours": round(inactive_seconds / 3600, 1)},
                        )
                        await save_user(u, DB_PATH)
                    except Exception as e:
                        log.warning(f"Не удалось отправить реактивацию 6h {chat_id}: {e}")

        await asyncio.sleep(3600)

# ============================================================
# MAIN
# ============================================================

async def main():
    try:
        if not BOT_TOKEN:
            raise RuntimeError("BOT_TOKEN is empty")
        bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
        dp = Dispatcher()
        dp.include_router(router)
        await init_db(DB_PATH)
        await migrate_db(DB_PATH)
        asyncio.create_task(background_ping(bot))
        log.info("Bot started")
        await dp.start_polling(bot)
    except asyncio.exceptions.CancelledError:
        log.info("Polling cancelled, shutting down...")
    except KeyboardInterrupt:
        log.info("Bot stopped by user (KeyboardInterrupt)")
    except Exception as e:
        log.exception(f"Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
