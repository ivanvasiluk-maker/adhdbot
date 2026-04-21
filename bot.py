# ============================================================
# ADHD SELF-REGULATION TRAINER BOT (REFACTORED)
# -:  (),  (),  ()
# ====================
# :
# - texts.py:     
# - skills.py:   
# - db.py:   
# - flows.py:   
# ============================================================

import os
import json
import time
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

import aiosqlite
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandStart
from aiogram.enums import ParseMode
import openai

# Import modules
from texts import (
    TEST_QUESTIONS, ONBOARDING_SCREENS,
    trainer_say, kb_trainers, kb_input_mode, kb_yes_no,
    kb_crisis_mode, kb_analysis_confirm, kb_analysis_contract,
    kb_analysis_map, kb_morning_state,
    payment_inline_full,
    kb_skill_entry, kb_training_run, kb_skill_more, kb_after_return, kb_pay_simple,
    kb_diag_start_hold, kb_diag_emotional, kb_diag_distraction,
    resolve_bucket_from_test, create_test_question_keyboard,
    analysis_contract_short, contract_full_text, month_map_text, guarantee_block,
    gamify_status_line, skill_explain, skill_detail_text, skill_card_text, get_morning_checkin_ack,
    daytime_ping, evening_close_question, evening_close_coach_reply, kb_evening_state, kb_post_done,
    morning_greeting_text, midday_ping_text, evening_check_text,
    reactivation_6h, reactivation_24h, reactivation_3d, reactivation_7d, kb_reactivation,
    reactivation_soft_return, kb_soft_return,
    day3_offer_bridge,
    build_week_plan, build_payment_offer,
    get_daytime_greeting,
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
from nlp_fallback import (
    parse_start_vs_hold,
    parse_anxiety_vs_empty,
    parse_distraction_primary,
    parse_where_stop,
    parse_yes_no_soft,
    guess_bucket_from_answers,
    anti_dead_end_reply,
    parse_tiny_reply,
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


async def _maybe_await(result):
    if asyncio.iscoroutine(result):
        return await result
    return result


def _make_openai_client(api_key: str):
    client_cls = getattr(openai, "AsyncOpenAI", None) or getattr(openai, "OpenAI", None)
    if not client_cls:
        raise RuntimeError("OpenAI client class is unavailable")
    return client_cls(api_key=api_key)


client = None
AI_ANALYSIS_ENABLED = False

if not OPENAI_API_KEY:
    log.warning("OPENAI_API_KEY not found; AI disabled.")
else:
    try:
        client = _make_openai_client(OPENAI_API_KEY)
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


def bump_retry(u: dict, field: str, limit: int = 2) -> int:
    u[field] = int(u.get(field) or 0) + 1
    if u[field] > limit:
        u[field] = limit
    return u[field]


def reset_retry(u: dict, field: str):
    u[field] = 0


def build_wow_analysis(user_text: str) -> str:
    text = user_text.lower()

    if "  " in text or "" in text:
        return (
            ",    :\n\n"
            "        '  ' \n"
            "-        \n"
            "      .\n\n"
            "  .\n"
            "   .\n\n"
            "     ' '.\n"
            "     ."
        )

    if "" in text or "" in text:
        return (
            ",  :\n\n"
            "         \n"
            "        .\n\n"
            "  ''.\n"
            "  .\n\n"
            "      '',\n"
            "   ."
        )

    if any(w in text for w in ("", "", "", "  ", "", "", "")):
        return (
            ",    :\n\n"
            "          \n"
            "  -     \n"
            "   .\n\n"
            "   .\n\n"
            " ,     \n"
            "    .\n\n"
            "      '',\n"
            "   ."
        )

    return (
        "   :\n"
        "          .\n\n"
        "        ,\n"
        "  ,   ."
    )


async def ai_micro_reflect(user_text: str, trainer_key: str, client=None, model: str = "gpt-4o-mini") -> str:
    """     (12 )."""
    user_text = clamp_str(user_text, 600)
    trainer_key = trainer_key or "marsha"

    # Fallback  
    fallback = {
        "skinny": ".  .   60120 ,  .",
        "marsha": ". ,  .        .",
        "beck": " .      .    .",
    }
    if not (client and model):
        return fallback.get(trainer_key, fallback["marsha"])

    system = (
        "   .    (12 ). "
        " : skinny=, marsha=, beck=. "
        ":          . "
        " ,  ,  ."
    )
    user = json.dumps({
        "trainer": trainer_key,
        "observation": user_text,
    }, ensure_ascii=False)

    try:
        resp = await _maybe_await(client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.35,
            max_tokens=120,
        ))
        content = (resp.choices[0].message.content or "").strip()
        if content:
            return clamp_str(content, 400)
    except Exception as e:
        log.error(f"ai_micro_reflect failed: {e}")
    return fallback.get(trainer_key, fallback["marsha"])


async def ai_fallback_answer(user_text: str) -> Optional[str]:
    try:
        client = _make_openai_client(OPENAI_API_KEY)
        resp = await _maybe_await(client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "   .  ,  ."},
                {"role": "user", "content": user_text},
            ],
            temperature=0.7,
            max_tokens=120,
        ))
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
        " :    ?\n"
        " /,   .\n"
        "    ''.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="")]],
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
        await m.answer(" AI disabled")
        return
    try:
        log.info(f"AI TEST START model={OPENAI_CHAT_MODEL}")
        resp = await _maybe_await(client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=[{"role": "user", "content": " : AI "}],
            temperature=0,
            max_tokens=20,
        ))
        text = resp.choices[0].message.content if resp.choices else "empty"
        log.info(f"AI TEST OK: {text}")
        await m.answer(f" {text}")
    except Exception as e:
        log.exception("AI TEST ERROR")
        await m.answer(f" AI error: {e}")


@router.message(Command("whispertest"))
async def whisper_test(m: Message):
    u = await get_user(m.from_user.id, DB_PATH)
    u["stage"] = "whisper_test_wait_voice"
    await save_user(u, DB_PATH)
    await m.answer("   ")


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

    await m.answer(".    Google Sheets.  events  users_summary.")


@router.message(CommandStart())
async def cmd_start(m: Message):
    uid = m.from_user.id
    u = await get_user(uid, DB_PATH)
    u["chat_id"] = m.chat.id
    u["username"] = m.from_user.username or ""


    #   :
    # 1.  
    u["stage"] = "ask_name"
    await track_user_event(u, "onboarding", "onboarding_started")
    for screen in ONBOARDING_SCREENS:
        await m.answer(screen)
        await asyncio.sleep(0.3)

    # 2.  
    await m.answer(
        "!    .   ? (1 )",
        reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="")]], resize_keyboard=True),
    )


# ============================================================
# HELPER: Show current skill training
# ============================================================
async def show_current_skill_training(m: Message, u: Dict[str, Any]):
    """     """
    sid = u.get("current_skill_id")

    if not sid:
        plan = get_current_plan(u)
        idx = max(0, min(len(plan) - 1, int(u.get("day") or 1) - 1))
        sid = plan[idx] if plan else None
        u["current_skill_id"] = sid
        await save_user(u, DB_PATH)

    skill = SKILLS_DB.get(sid or "", {})
    trainer_key = u.get("trainer_key") or "marsha"

    if not skill:
        await m.answer(
            trainer_say(trainer_key, " .      ."),
            reply_markup=kb_skill_entry,
        )
        return

    u["stage"] = "training"
    await save_user(u, DB_PATH)

    await m.answer(
        skill_training_text(skill, trainer_key=trainer_key),
        reply_markup=kb_training_run,
    )


@router.message()
async def main_flow(m: Message):
    uid = m.from_user.id
    u = await get_user(uid, DB_PATH)
    text = (m.text or "").strip()
    low = text.lower()

    if u.get("stage") == "await_mode":
        u["stage"] = "await_input_mode"
        if not u.get("mode"):
            u["mode"] = "normal"
        await save_user(u, DB_PATH)

    KNOWN_STAGES = {
        "ask_name",
        "await_trainer",
        "trainer_intro",
        "await_input_mode",
        "await_problem_text",
        "await_problem_voice",
        "run_analysis",
        "confirm_analysis",
        "analysis_more",
        "analysis_contract",
        "analysis_map",
        "analysis_refine",
        "analysis_retry_await_clarification",
        "quick_diagnostic_start_hold",
        "quick_diagnostic_start_hold_custom",
        "quick_diagnostic_emotional",
        "quick_diagnostic_emotional_custom",
        "quick_diagnostic_distraction",
        "quick_diagnostic_distraction_custom",
        "day_morning",
        "day_midday",
        "day_evening",
        "morning_checkin",
        "morning_checkin_custom",
        "midday_checkin",
        "post_training_reflection",
        "post_training_reflection_custom",
        "day_evening_custom",
        "await_training_target",
        "skill_entry",
        "training",
        "training_skill_more",
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
        #     ->   
        if u.get("day"):
            u["stage"] = "skill_entry"
            await save_user(u, DB_PATH)
            await m.answer(
                " .     .",
                reply_markup=kb_skill_entry,
            )
            return

        #    -> 
        u["stage"] = "ask_name"
        await save_user(u, DB_PATH)
        await m.answer("   ")
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

    #       
    u["reactivation_level"] = 0

    #  :     ,     -
    if (text == "🆘 Кризис" or "кризис" in low) and u.get("stage") not in {"crisis_choose_mode", "crisis_voice", "crisis_text", "crisis_plan_confirm"}:
        u["stage"] = "crisis_choose_mode"
        await track_user_event(u, u["stage"], "crisis_open")
        await m.answer("🆘 Ок. Как удобнее?", reply_markup=kb_crisis_mode)
        return

    if u.get("stage") in {"evening_close_wait", "day_evening"}:
        trainer_key = u.get("trainer_key") or "marsha"
        if not text:
            await m.answer("       .", reply_markup=kb_evening_close)
            return

        if text == "  ":
            await m.answer(",   .", reply_markup=kb_evening_close)
            return

        mapped = text
        if text == " - ":
            mapped = "-    ."
        elif text == "  ":
            mapped = "      ."
        elif text == " (),  ()":
            mapped = " ,   ()."

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
        await m.answer(trainer_say(trainer_key, reply), reply_markup=kb_skill_entry)
        return

    # -  
        if u.get("stage") == "reactivation_wait":
            trainer_key = u.get("trainer_key") or "marsha"
            restore = u.get("evening_return_stage") or "training"

            if text == "    ":
                u["stage"] = restore
                u["evening_return_stage"] = None
                u["last_active"] = time.time()
                u["day_started_at"] = time.time()
                await save_user(u, DB_PATH)
                await log_event(u["user_id"], "reactivation", "reactivation_returned", {"via": "start_day"}, DB_PATH, SHEETS_WEBHOOK_URL)
                day = int(u.get("day") or 1)
                await start_day(m, u, day, DB_PATH, SHEETS_WEBHOOK_URL)
                return

            if text == "    ":
                plan = get_current_plan(u)
                sid = plan[0] if plan else None
                skill = SKILLS_DB.get(sid, {}) if sid else {}
                msg = skill_explain(trainer_key, skill) if skill else "  12 :       ."
                u["stage"] = "training"
                u["evening_return_stage"] = None
                u["day_started_at"] = time.time()
                u["last_active"] = time.time()
                await save_user(u, DB_PATH)
                await log_event(u["user_id"], "reactivation", "reactivation_returned", {"via": "simplest_skill", "sid": sid or ""}, DB_PATH, SHEETS_WEBHOOK_URL)
                await m.answer(trainer_say(trainer_key, msg), reply_markup=kb_training_run)
                return

            if text == "   ":
                u["stage"] = "morning_checkin"
                u["evening_return_stage"] = None
                u["day_started_at"] = time.time()
                u["last_active"] = time.time()
                await save_user(u, DB_PATH)
                await log_event(u["user_id"], "reactivation", "reactivation_returned", {"via": "gentle_entry"}, DB_PATH, SHEETS_WEBHOOK_URL)
                from texts import get_morning_checkin_opener
                await m.answer(trainer_say(trainer_key, get_morning_checkin_opener(trainer_key)), reply_markup=kb_morning_checkin)
                return

            if text == "   ":
                plan = get_current_plan(u)
                sid = plan[0] if plan else None
                skill = SKILLS_DB.get(sid, {}) if sid else {}
                step = skill.get("micro") or skill.get("minimum") or "   2 "
                msg = reactivation_soft_return(trainer_key, u.get("name") or "", step)
                u["stage"] = "training"
                u["evening_return_stage"] = None
                u["day_started_at"] = time.time()
                u["last_active"] = time.time()
                await save_user(u, DB_PATH)
                await log_event(u["user_id"], "reactivation", "reactivation_returned", {"via": "soft_return"}, DB_PATH, SHEETS_WEBHOOK_URL)
                await m.answer(trainer_say(trainer_key, msg), reply_markup=kb_training_run)
                return

            #   -    soft return 
            plan = get_current_plan(u)
            sid = plan[0] if plan else None
            skill = SKILLS_DB.get(sid, {}) if sid else {}
            step = skill.get("micro") or skill.get("minimum") or "   2 "
            msg = reactivation_soft_return(trainer_key, u.get("name") or "", step)
            u["stage"] = restore
            u["evening_return_stage"] = None
            u["last_active"] = time.time()
            await save_user(u, DB_PATH)
            await log_event(u["user_id"], "reactivation", "reactivation_returned", {"via": "free_text"}, DB_PATH, SHEETS_WEBHOOK_URL)
            await m.answer(trainer_say(trainer_key, msg), reply_markup=kb_soft_return)
            return

        # -  
    if u.get("stage") == "waiting_next_day":
        trainer_key = u.get("trainer_key") or "marsha"
        reply = await ai_micro_reflect(text or "", trainer_key, client, OPENAI_CHAT_MODEL)
        await log_event(u["user_id"], "training", "post_done_reflect", {"len": len(text or "")}, DB_PATH, SHEETS_WEBHOOK_URL)
        await m.answer(trainer_say(trainer_key, reply), reply_markup=kb_skill_entry)
        return

    if u.get("stage") == "whisper_test_wait_voice":
        if not m.voice:
            await m.answer("   ")
            return

        t = await whisper_transcribe(m)
        if not t:
            await m.answer(" Whisper    .")
            return

        await m.answer(f" Whisper:\n\n{t}")
        return


    # ============================================================
    # LIVE DIALOG PATTERN HOOK
    # ============================================================
    dialog_stages = {
        "analysis_refine",
        "training",
        "await_training_target",
    }

    if u.get("stage") in dialog_stages and text:
        matched_intent = False

        if "" in low:
            await m.answer(
                trainer_say(
                    u.get("trainer_key") or "marsha",
                    " =    .\n\n  1    .",
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
        if text and text.lower() != "":
            u["name"] = text[:50]
        await log_event(u["user_id"], "onboarding", "name_provided", {}, DB_PATH, SHEETS_WEBHOOK_URL)
        u["stage"] = "await_trainer"
        await save_user(u, DB_PATH)
        #   
        trainers_intro = (
            "\U0001F408\u200D\u2B1B :    ?\n\n"
            "     .         .\n"
            "     .      ,   .\n"
            "     . ,      .\n\n"
            " ,        ."
        )
        await m.answer(trainers_intro)
        await m.answer(".  :", reply_markup=kb_trainers)
        return

    # ============================================================
    # TRAINER SELECTION
    # ============================================================
    if u["stage"] == "await_trainer":
        low = text.lower().strip()
        chosen = None
        if text == "  ()" or "" in low:
            chosen = "skinny"
        elif text == "  ()" or "" in low:
            chosen = "marsha"
        elif text == "  ()" or "" in low:
            chosen = "beck"
        if not chosen:
            await m.answer("  ", reply_markup=kb_trainers)
            return
        u["trainer_key"] = chosen
        u["stage"] = "trainer_intro"
        await track_user_event(u, "onboarding", "trainer_selected", {"trainer_key": chosen})
        #    
        await send_trainer_photo_if_any(m.chat.id, chosen, BOT_TOKEN)
        from texts import send_trainer_introduction
        await send_trainer_introduction(m, u)
        #        
        screens = trainer_block(u.get("trainer_key") or "marsha", "onboarding")
        if screens:
            for screen in screens:
                await m.answer(screen)
        await m.answer("       ?", reply_markup=kb_yes_no)
        return
    # ============================================================
    # TRAINER INTRO CONFIRM
    # ============================================================
    if u["stage"] == "trainer_intro":
        low = (text or "").lower()
        if "да" in low:
            trainer_key = u.get("trainer_key") or "marsha"
            mode_by_trainer = {
                "marsha": "easy",
                "skinny": "hard",
                "beck": "normal",
            }
            u["mode"] = mode_by_trainer.get(trainer_key, "normal")
            u["stage"] = "await_input_mode"
            await save_user(u, DB_PATH)
            await m.answer(
                f"{u.get('name') or 'Ок'}, как удобнее пройти диагностику?",
                reply_markup=kb_input_mode
            )
            return
        if "нет" in low:
            u["stage"] = "await_trainer"
            await save_user(u, DB_PATH)
            await m.answer("Выбери другого тренера 👇", reply_markup=kb_trainers)
            return
        await m.answer("Выбери: ✅ Да / ❌ Нет", reply_markup=kb_yes_no)
        return

    # ============================================================
    # INPUT MODE SELECTION
    # ============================================================
    if u["stage"] == "await_input_mode":
        low = text.lower().strip()
        if text == "  " or "" in low:
            u["input_mode"] = "text"
            u["stage"] = "await_problem_text"
            await track_user_event(u, "onboarding", "input_mode_selected", {"input_mode": "text"})
            await track_user_event(u, "analysis", "diagnosis_started", {"input_mode": "text"})
            await m.answer(".  25 :     ?", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="")]], resize_keyboard=True))
            return
        if text == "  " or "" in low:
            u["input_mode"] = "voice"
            u["stage"] = "await_problem_voice"
            await track_user_event(u, "onboarding", "input_mode_selected", {"input_mode": "voice"})
            await track_user_event(u, "analysis", "diagnosis_started", {"input_mode": "voice"})
            await m.answer(".   (1030 ):     ?", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="")]], resize_keyboard=True))
            return
        if text == "   (5 )" or "" in low:
            u["input_mode"] = "test"
            u["stage"] = "taking_test"
            u["test_answers"] = []
            await track_user_event(u, "onboarding", "input_mode_selected", {"input_mode": "test"})
            await track_user_event(u, "analysis", "diagnosis_started", {"input_mode": "test"})
            first_q = TEST_QUESTIONS[0]
            msg = f"  1/5:\n\n{first_q['text']}"
            await m.answer(msg, reply_markup=create_test_question_keyboard(1))
            return
        await m.answer("  ", reply_markup=kb_input_mode)
        return

    # await_problem_text
    if u["stage"] == "await_problem_text":
        if not text or text.lower() == "":
            user_text = "/,  ,  ."
        else:
            user_text = text

        u["analysis_json"] = json.dumps({"user_text": clamp_str(user_text, 1000)}, ensure_ascii=False)
        u["stage"] = "run_analysis"
        await save_user(u, DB_PATH)

        wow = build_wow_analysis(user_text)
        trainer_key = u.get("trainer_key") or "marsha"
        await m.answer(trainer_say(trainer_key, wow))
        await m.answer(".  ")
        await run_analysis(m, u, user_text, DB_PATH, SHEETS_WEBHOOK_URL, client, OPENAI_CHAT_MODEL)
        return

    # await_problem_voice
    if u["stage"] == "await_problem_voice":
        if text and text.lower() == "":
            u["stage"] = "await_input_mode"
            await save_user(u, DB_PATH)
            await m.answer("Ок. Выбери формат диагностики:", reply_markup=kb_input_mode)
            return
        if not m.voice:
            await m.answer("  ")
            return
        t = await whisper_transcribe(m)
        if not t:
            u["stage"] = "await_problem_text"
            await save_user(u, DB_PATH)
            await m.answer("   .  .        13 ")
            return
        u["analysis_json"] = json.dumps({"user_text": clamp_str(t, 1000)}, ensure_ascii=False)
        u["stage"] = "run_analysis"
        await save_user(u, DB_PATH)
        wow = build_wow_analysis(t)
        trainer_key = u.get("trainer_key") or "marsha"
        await m.answer(trainer_say(trainer_key, wow))
        await m.answer(".  ")
        await run_analysis(m, u, t, DB_PATH, SHEETS_WEBHOOK_URL, client, OPENAI_CHAT_MODEL)
        return

    # confirm_analysis
    if u.get("stage") == "confirm_analysis":
        low = (text or "").lower().strip()
        if text == " ,  " or " " in low:
            u["stage"] = "analysis_contract"
            await track_user_event(u, "analysis", "analysis_accepted")
            await m.answer(
                analysis_contract_short(u.get("name") or "", u.get("trainer_key"), u.get("bucket")),
                reply_markup=kb_analysis_contract,
            )
            await m.answer(trainer_say(u.get("trainer_key") or "marsha", guidance_micro_phrase("point")))
            return
        if text == "   " or " " in low:
            u["stage"] = "quick_diagnostic_start_hold"
            reset_retry(u, "start_hold_retry")
            await track_user_event(u, "analysis", "analysis_refined", {"source": "confirm_analysis"})
            await save_user(u, DB_PATH)
            await m.answer("    ?")
            return
        if text == " " or text == " " or "" in low:
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
                or "  "
            )
            chain_text = render_behavior_chain([
                trigger,
                comp.get("what_is_happening", "     ."),
                comp.get("not_your_fault_or_control_zone", "   .   ,      ."),
                comp.get("training_path", " ,     ."),
            ])
            timeline = comp.get("timeline", "      23   .")

            await m.answer(
                f"{chain_text}\n\n   :\n{timeline}\n\n    ?",
                reply_markup=kb_analysis_confirm,
            )
            return
        await m.answer("  ", reply_markup=kb_analysis_confirm)
        return

    # analysis_more
    if u.get("stage") == "analysis_more":
        low = (text or "").lower().strip()
        if text == " ,  " or " " in low:
            u["stage"] = "analysis_contract"
            await sync_user_summary_state(u)
            await m.answer(
                analysis_contract_short(u.get("name") or "", u.get("trainer_key"), u.get("bucket")),
                reply_markup=kb_analysis_contract,
            )
            await m.answer(trainer_say(u.get("trainer_key") or "marsha", guidance_micro_phrase("reason")))
            return
        if text == "   " or " " in low:
            u["stage"] = "quick_diagnostic_start_hold"
            reset_retry(u, "start_hold_retry")
            await track_user_event(u, "analysis", "analysis_refined", {"source": "analysis_more"})
            await save_user(u, DB_PATH)
            await m.answer("    ?")
            return
        await m.answer(",   ,    ", reply_markup=kb_analysis_confirm)
        return

    # analysis_contract
    if u.get("stage") == "analysis_contract":
        low = (text or "").lower().strip()
        if text == "  " or "" in low:
            u["stage"] = "analysis_map"
            await save_user(u, DB_PATH)
            await m.answer(month_map_text(u.get("bucket")))
            await m.answer(
                f"{guarantee_block(u.get('trainer_key'))}\n\n()    ?",
                reply_markup=kb_analysis_map,
            )
            return
        if text == "   " or " " in low:
            u["stage"] = "quick_diagnostic_start_hold"
            reset_retry(u, "start_hold_retry")
            await save_user(u, DB_PATH)
            await m.answer("    ?")
            return
        if text == " " or "" in low:
            await m.answer(
                contract_full_text(u.get("name") or "", u.get("trainer_key"), u.get("bucket")),
                reply_markup=kb_analysis_contract,
            )
            return
        await m.answer("     ", reply_markup=kb_analysis_contract)
        return

    # analysis_map
    if u.get("stage") == "analysis_map":
        low = (text or "").lower().strip()
        if text == "  " or "" in low:
            u["day"] = 1
            await track_user_event(u, "analysis", "day1_started")
            await start_day(m, u, 1, DB_PATH, SHEETS_WEBHOOK_URL)
            return
        if text == "   " or " " in low or low == "":
            u["stage"] = "quick_diagnostic_start_hold"
            reset_retry(u, "start_hold_retry")
            await save_user(u, DB_PATH)
            await m.answer("    ?")
            return
        await m.answer("      ", reply_markup=kb_analysis_map)
        return

    # quick_diagnostic_start_hold
    if u.get("stage") == "quick_diagnostic_start_hold":
        parsed = parse_start_vs_hold(text)
        if parsed:
            u["start_hold"] = parsed
            reset_retry(u, "start_hold_retry")
            u["stage"] = "quick_diagnostic_emotional"
            await save_user(u, DB_PATH)
            await m.answer("  ?\n1)  \n2)   / ")
            return
        retry = bump_retry(u, "start_hold_retry")
        await save_user(u, DB_PATH)
        if retry == 1:
            await m.answer("  :       ?")
            return
        u["start_hold"] = "hold"
        u["stage"] = "quick_diagnostic_emotional"
        await save_user(u, DB_PATH)
        await m.answer(trainer_say(u.get("trainer_key") or "marsha", anti_dead_end_reply(u.get("trainer_key") or "marsha")))
        await m.answer("   :   .\n :   /?")
        return

    # quick_diagnostic_emotional
    if u.get("stage") == "quick_diagnostic_emotional":
        parsed = parse_anxiety_vs_empty(text)
        if parsed:
            u["emotional"] = parsed
            reset_retry(u, "emotional_retry")
            u["stage"] = "quick_diagnostic_distraction"
            await save_user(u, DB_PATH)
            await m.answer("       ?")
            return
        retry = bump_retry(u, "emotional_retry")
        await save_user(u, DB_PATH)
        if retry == 1:
            await m.answer("  :      /?")
            return
        u["emotional"] = "mixed"
        u["stage"] = "quick_diagnostic_distraction"
        await save_user(u, DB_PATH)
        await m.answer(trainer_say(u.get("trainer_key") or "marsha", anti_dead_end_reply(u.get("trainer_key") or "marsha")))
        await m.answer(",    .       ?")
        return

    # quick_diagnostic_distraction
    if u.get("stage") == "quick_diagnostic_distraction":
        parsed = parse_distraction_primary(text)
        if parsed:
            u["distraction"] = parsed
            reset_retry(u, "distraction_retry")
        else:
            retry = bump_retry(u, "distraction_retry")
            await save_user(u, DB_PATH)
            if retry == 1:
                await m.answer("            ?")
                return
            u["distraction"] = "secondary"
            await m.answer(trainer_say(u.get("trainer_key") or "marsha", anti_dead_end_reply(u.get("trainer_key") or "marsha")))

        data = {
            "start_hold": u.get("start_hold", ""),
            "emotional": u.get("emotional", ""),
            "distraction": u.get("distraction", ""),
            "stop_where": u.get("stop_where", ""),
        }
        u["bucket"] = guess_bucket_from_answers(data)
        u["stage"] = "confirm_analysis"
        await save_user(u, DB_PATH)
        await m.answer(
            trainer_say(
                u.get("trainer_key") or "marsha",
                ".   .       ."
            ),
            reply_markup=kb_analysis_confirm,
        )
        return

    # analysis_retry_await_clarification
    if u.get("stage") == "analysis_retry_await_clarification":
        if not text:
            await m.answer(", ,     . (13 )")
            return

        #     
        parsed_stop = parse_where_stop(text) or parse_tiny_reply(text)
        if parsed_stop:
            u["stop_where"] = parsed_stop
            reset_retry(u, "clarify_retry_count")
            data = {
                "start_hold": u.get("start_hold", ""),
                "emotional": u.get("emotional", ""),
                "distraction": u.get("distraction", ""),
                "stop_where": u.get("stop_where", ""),
            }
            u["bucket"] = guess_bucket_from_answers(data)
            u["stage"] = "confirm_analysis"
            await save_user(u, DB_PATH)
            await m.answer(
                trainer_say(
                    u.get("trainer_key") or "marsha",
                    ".  .    ."
                ),
                reply_markup=kb_analysis_confirm,
            )
            return

        retry = bump_retry(u, "clarify_retry_count")
        await save_user(u, DB_PATH)

        if retry == 1:
            await m.answer(
                "   ?\n\n"
                "1)   \n"
                "2)  ,  \n"
                "3)  ,   "
            )
            return

        #  2-     ,     
        u["stop_where"] = "during"
        data = {
            "start_hold": u.get("start_hold", ""),
            "emotional": u.get("emotional", ""),
            "distraction": u.get("distraction", ""),
            "stop_where": "during",
        }
        u["bucket"] = guess_bucket_from_answers(data)
        u["stage"] = "confirm_analysis"
        await save_user(u, DB_PATH)
        await m.answer(trainer_say(u.get("trainer_key") or "marsha", anti_dead_end_reply(u.get("trainer_key") or "marsha")))
        await m.answer(",      .     .", reply_markup=kb_analysis_confirm)
        return

    # analysis_refine
    if u["stage"] == "analysis_refine":
        if not text:
            await m.answer(" 12 ,    .")
            return
        #     ,     
        base_user_text = ""
        try:
            if u.get("analysis_json"):
                prev = json.loads(u.get("analysis_json") or "{}")
                base_user_text = prev.get("user_text", "") or ""
        except Exception:
            base_user_text = ""

        combined_text = base_user_text.strip()
        if combined_text:
            combined_text += "\n\n : " + text
        else:
            combined_text = text

        u["raw_text"] = combined_text
        u["stage"] = "run_analysis"
        await save_user(u, DB_PATH)
        await m.answer(".  ")
        await run_analysis(m, u, combined_text, DB_PATH, SHEETS_WEBHOOK_URL, client, OPENAI_CHAT_MODEL)
        return

    # morning_checkin
    if u.get("stage") == "morning_checkin":
        trainer_key = u.get("trainer_key") or "marsha"
        low = (text or "").lower().strip()

        mood_key = None
        if text == "" or "" in low:
            mood_key = "anxious"
        elif text == "  " or (" " in low and "" in low):
            mood_key = "resistant"
        elif text == " /  " or " " in low or "" in low:
            mood_key = "empty"
        elif text == "" or "" in low:
            mood_key = "distracted"
        elif text == ", " or "" in low:
            mood_key = "ok"
        elif text == " ":
            u["stage"] = "morning_checkin_custom"
            await save_user(u, DB_PATH)
            await m.answer(
                trainer_say(trainer_key, ".  ,        ."),
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text=""), KeyboardButton(text="  ")],
                              [KeyboardButton(text=" /  "), KeyboardButton(text="")],
                              [KeyboardButton(text=", ")]],
                    resize_keyboard=True,
                ),
            )
            return

        if not mood_key:
            await m.answer("     ' '.", reply_markup=kb_morning_checkin)
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
            await m.answer(" :  .")
            return

        u["stage"] = "await_training_target"
        await save_user(u, DB_PATH)
        await m.answer(trainer_say(trainer_key, get_morning_checkin_ack(trainer_key, "custom")))
        await ask_training_target(m)
        return

    #    
    if u.get("stage") == "await_training_target":
        raw_target = (text or "").strip()
        target = clamp_str(raw_target, 200)

        if not target or target.lower() == "":
            default_targets = {
                "anxiety": "      2 ",
                "low_energy": "     ",
                "distractibility": "     1 ",
                "mixed": "    ",
            }
            bucket = u.get("bucket") or "mixed"
            target = default_targets.get(bucket, "    ")

        target = target.replace("", "").strip()
        if not target:
            target = "    "

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
        u["today_target"] = target
        u["pending_skill_id"] = None
        u["pending_skill_day"] = None
        u["current_skill_id"] = sid
        u["stage"] = "skill_entry"
        await track_user_event(u, "training", "target_set", {"day": day, "text": target})
        await save_user(u, DB_PATH)

        await m.answer(
            skill_card_text(skill, trainer_key=trainer_key),
            reply_markup=kb_skill_entry,
        )
        return

    # MIDDAY_CHECKIN stage
    if u.get("stage") == "midday_checkin":
        low = (text or "").lower().strip()
        trainer_key = u.get("trainer_key") or "marsha"

        response = ""
        if any(x in low for x in [" ", "", " ", ""]):
            if trainer_key == "skinny":
                response = ". ,    ."
            elif trainer_key == "beck":
                response = ".  .  ."
            else:
                response = "!   . ."
        elif any(x in low for x in ["", "", "", "", " "]):
            if trainer_key == "skinny":
                response = ".  .     60 , ."
            elif trainer_key == "beck":
                response = ".     .   : , , ."
            else:
                response = ".     .    60 ."
        elif any(x in low for x in [" ", " ", "?"]):
            if trainer_key == "skinny":
                response = ". ,  . ,   .      ."
            elif trainer_key == "beck":
                response = ".     ."
            else:
                response = ".          ."
        else:
            if trainer_key == "skinny":
                response = ".   . ."
            elif trainer_key == "beck":
                response = ".   ."
            else:
                response = "  . ."

        await m.answer(trainer_say(trainer_key, response))
        
        # Move back to skill_entry for next action
        u["stage"] = "skill_entry"
        await save_user(u, DB_PATH)
        return

    # SKILL_ENTRY stage (after skill card is shown)
    if u.get("stage") == "skill_entry":
        if text == "   ":
            await show_current_skill_training(m, u)
            return

        if text == "   ":
            sid = u.get("current_skill_id")
            skill = SKILLS_DB.get(sid or "", {})
            u["stage"] = "training_skill_more"
            await save_user(u, DB_PATH)

            await m.answer(
                skill_detail_text(skill),
                reply_markup=kb_skill_more,
            )
            return

        if text == " ":
            u["stage"] = "crisis_choose_mode"
            await save_user(u, DB_PATH)
            await m.answer("🆘 Ок. Как удобнее?", reply_markup=kb_crisis_mode)
            return

        await m.answer("  ", reply_markup=kb_skill_entry)
        return

    # TRAINING stage
    if u.get("stage") == "training":
        low = text.lower().strip()

        if text == " ()":
            u["done_count"] = int(u.get("done_count") or 0) + 1
            gamify_apply(u, 1, "done")
            await track_user_event(u, "training", "done", {"day": u.get("day")})
            await save_user(u, DB_PATH)

            await m.answer(
                trainer_say(u.get("trainer_key") or "marsha", ".  .  .")
            )
            await m.answer(
                "     ?"
            )
            return

        if text == " ()":
            u["return_count"] = int(u.get("return_count") or 0) + 1
            gamify_apply(u, 1, "return")
            await track_user_event(u, "training", "return", {"day": u.get("day")})

            u["stage"] = "after_return_choice"
            await save_user(u, DB_PATH)

            await m.answer(
                trainer_say(u.get("trainer_key") or "marsha", " .   .")
            )
            await m.answer(
                "         ?",
                reply_markup=kb_after_return,
            )
            return

        if text == " ":
            u["stage"] = "crisis_choose_mode"
            await save_user(u, DB_PATH)
            await m.answer("🆘 Ок. Как удобнее?", reply_markup=kb_crisis_mode)
            return

        await m.answer("  ", reply_markup=kb_training_run)
        return

    if u.get("stage") == "training_skill_more":
        low = (text or "").lower().strip()

        if text == "   ":
            await show_current_skill_training(m, u)
            return

        if text == " " or "" in low:
            u["stage"] = "skill_entry"
            await save_user(u, DB_PATH)
            await m.answer(". .", reply_markup=kb_skill_entry)
            return

        await m.answer("  ", reply_markup=kb_skill_more)
        return

    if u.get("stage") == "after_return_choice":
        if text == "   ":
            await show_current_skill_training(m, u)
            return

        if text == "   ":
            day = int(u.get("day") or 1)

            if day == 7:
                await send_weekly_summary(m, u, DB_PATH)

            if payments_enabled() and day == 3 and u.get("trial_phase") == "trial3":
                await m.answer(
                    build_week_plan(u),
                )
                await m.answer(
                    build_payment_offer(u),
                    reply_markup=kb_pay_simple,
                )
                u["stage"] = "offer"
                await save_user(u, DB_PATH)
                return

            await start_day(m, u, day + 1, DB_PATH, SHEETS_WEBHOOK_URL)
            return

        await m.answer("  ", reply_markup=kb_after_return)
        return

    # crisis_choose_mode
    if u.get("stage") == "crisis_choose_mode":
        low = (text or "").lower().strip()

        #         
        if m.voice:
            t = await whisper_transcribe(m)
            if t:
                await handle_crisis(m, u, t, DB_PATH, SHEETS_WEBHOOK_URL, client, OPENAI_CHAT_MODEL)
                return
            await m.answer("   .  13 .")
            u["stage"] = "crisis_text"
            await save_user(u, DB_PATH)
            return

        if text == " " or "" in low:
            u["stage"] = "training"
            await save_user(u, DB_PATH)
            await m.answer(".   .", reply_markup=kb_training_run)
            return
        if text == "  " or "" in low:
            u["stage"] = "crisis_voice"
            await save_user(u, DB_PATH)
            await m.answer("  :       ?")
            return
        if text == "  " or "" in low:
            u["stage"] = "crisis_text"
            await save_user(u, DB_PATH)
            await m.answer(" :       ? (13 )")
            return
        if text:
            #       -
            await handle_crisis(m, u, text, DB_PATH, SHEETS_WEBHOOK_URL, client, OPENAI_CHAT_MODEL)
            return
        await m.answer("  ", reply_markup=kb_crisis_mode)
        return

    if u.get("stage") == "crisis_text":
        if text and text.lower().strip() in {" ", ""}:
            u["stage"] = "training"
            await save_user(u, DB_PATH)
            await m.answer(".   .", reply_markup=kb_training_run)
            return
        if not text:
            await m.answer(" 13 .")
            return
        await handle_crisis(m, u, text, DB_PATH, SHEETS_WEBHOOK_URL, client, OPENAI_CHAT_MODEL)
        return

    if u.get("stage") == "crisis_voice":
        if text and text.lower().strip() in {" ", ""}:
            u["stage"] = "training"
            await save_user(u, DB_PATH)
            await m.answer(".   .", reply_markup=kb_training_run)
            return
        if not m.voice:
            await m.answer("  ")
            return
        t = await whisper_transcribe(m)
        if not t:
            await m.answer("   .  .        13 ")
            u["stage"] = "crisis_text"
            await save_user(u, DB_PATH)
            return
        await handle_crisis(m, u, t, DB_PATH, SHEETS_WEBHOOK_URL, client, OPENAI_CHAT_MODEL)
        return

    if u.get("stage") == "crisis_plan_confirm":
        low = text.lower().strip()
        if text == " " or "" in low:
            pending = json.loads(u.get("pending_plan_change") or "{}") if u.get("pending_plan_change") else {}
            day_num = pending.get("day_num")
            sid = pending.get("skill_id")
            if day_num and sid:
                propose_plan_override(u, int(day_num), sid)
                u["pending_plan_change"] = None
                await save_user(u, DB_PATH)
                await log_event(u["user_id"], u.get("stage", ""), "plan_change_accept", {"day": day_num, "skill": sid}, DB_PATH, SHEETS_WEBHOOK_URL)
                await m.answer(" .   .    .")
            u["stage"] = "training"
            await save_user(u, DB_PATH)
            await m.answer("  .", reply_markup=kb_training_run)
            return
        if text == " " or "" in low:
            u["pending_plan_change"] = None
            u["stage"] = "training"
            await save_user(u, DB_PATH)
            await log_event(u["user_id"], u.get("stage", ""), "plan_change_reject", {}, DB_PATH, SHEETS_WEBHOOK_URL)
            await m.answer(".   . .", reply_markup=kb_training_run)
            return
        await m.answer(":   /  ", reply_markup=kb_yes_no)
        return

    # OFFER stage
    if u.get("stage") == "offer":
        if text == " ":
            await track_user_event(u, "payment", "payment_clicked", {"variant": "simple"})
            await m.answer(".     ")
            await m.answer(" ", reply_markup=payment_inline_full(PAYMENT_URL_FULL))
            return

        if text == "  ":
            u["stage"] = "waiting_next_day"
            await save_user(u, DB_PATH)
            await m.answer(
                ".\n\n"
                " :          ,\n"
                "   .\n\n"
                "    ,    ."
            )
            return

        await m.answer("  ", reply_markup=kb_pay_simple)
        return

    #       ,  stage  
    stage = str(u.get('stage')).replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('`', '\\`')
    if stage != "post_done_reflection":
        await m.answer(f"  (stage): {stage}.  /start       .", parse_mode=None)

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
                analysis_contract_short(u.get("name") or "", u.get("trainer_key"), u.get("bucket")),
                reply_markup=kb_analysis_contract,
            )
        else:
            u["stage"] = "analysis_refine"
            await save_user(u, DB_PATH)
            await c.message.answer(".  12 ,     .")
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
            await c.answer("  ")
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
                await c.message.edit_text(f"  {next_q_num}/5:\n\n{next_q['text']}", reply_markup=create_test_question_keyboard(next_q_num))
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
        await c.answer("  ")

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
        user_text = f"    {bucket}"
    comp = await ai_analyze_comprehensive(user_text, u.get("trainer_key", "marsha"), client, OPENAI_CHAT_MODEL)
    u["analysis_json"] = json.dumps(comp, ensure_ascii=False)
    u["bucket"] = comp.get("bucket", bucket)
    plan_ids = build_28_day_plan(u["bucket"])
    u["plan_json"] = json.dumps(plan_ids, ensure_ascii=False)
    u["day"] = 1
    u["stage"] = "confirm_analysis"
    await save_user(u, DB_PATH)
    await log_event(u["user_id"], "analysis", "analysis_shown", {"bucket": u.get("bucket")}, DB_PATH, SHEETS_WEBHOOK_URL)
    msg = f"{comp.get('short_summary', '  ?')}\n\n   ?"
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
        tr = await _maybe_await(client.audio.transcriptions.create(
            model=OPENAI_WHISPER_MODEL,
            file=bio
        ))
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

            #  :   ,    .
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
                        log.warning(f"     {chat_id}: {e}")

            #  :     +  .
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
                        log.warning(f"     {chat_id}: {e}")
        for row in rows:
            u = dict(row)
            stage = u.get("stage")

            #      
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

            #    +   
            #   ,   
            if stage in {"training", "waiting_next_day"} and _is_same_day(day_started_at):

                # -  13:  nudge   
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
                                reply_markup=kb_skill_entry,
                            )
                            await track_user_event(
                                u,
                                "training",
                                "anti_churn_ping",
                                {"day": day_num, "inactive_hours": hours_passed},
                            )
                            await save_user(u, DB_PATH)
                        except Exception as e:
                            log.warning(f"   anti_churn {chat_id}: {e}")
                        continue  #        

                #  :   ,    .
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
                            log.warning(f"     {chat_id}: {e}")

                #  :     +  .
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
                            log.warning(f"     {chat_id}: {e}")

            #    
            #     ,    
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
                        log.warning(f"    7d {chat_id}: {e}")

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
                        log.warning(f"    3d {chat_id}: {e}")

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
                        log.warning(f"    24h {chat_id}: {e}")

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
                        log.warning(f"    6h {chat_id}: {e}")

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


