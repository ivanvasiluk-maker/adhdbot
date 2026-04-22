# ============================================================
# DB.PY — Все функции работы с БД
# ============================================================

import json
import time
import logging
import os
from typing import Dict, Any, Optional, List
import aiosqlite

# Logging
log = logging.getLogger("bot")

# Global test switch to unlock features without paywalls
TEST_MODE = os.getenv("TEST_MODE", "").lower() in {"1", "true", "yes", "on", "debug"}

# ============================================================
# 4) DB: schema + CRUD
# ============================================================

USER_FIELDS = [
    "user_id",
    "chat_id",
    "username",
    "name",
    "trainer_key",
    "input_mode",
    "mode",
    "stage",
    "bucket",
    "analysis_json",
    "plan_json",
    "current_skill_id",
    "pending_skill_id",
    "pending_skill_day",
    "today_target",
    "day",
    "created_at",
    "points",
    "level",
    "streak",
    "last_active",
    "plan_overrides_json",
    "trial_days",
    "trial_phase",
    "pending_plan_change",
    "crisis_count",
    "test_answers",
    "done_count",
    "return_count",
    "analysis_retry_count",
    "has_started_training",
    "day_started_at",
    "last_day_ping_at",
    "last_evening_prompt_at",
    "evening_return_stage",
    "reactivation_level",
    "last_event",
    "last_event_at",
    "stuck_flag",
]

def default_user(uid: int) -> Dict[str, Any]:
    """Создать нового пользователя с дефолтными значениями"""
    return {
        "user_id": uid,
        "chat_id": uid,
        "username": "",
        "name": None,
        "trainer_key": "marsha",
        "input_mode": "text",   # text | voice | test
        "mode": "normal",
        "stage": "start",
        "bucket": "mixed",
        "analysis_json": None,
        "plan_json": None,
        "current_skill_id": None,
        "pending_skill_id": None,
        "pending_skill_day": None,
        "today_target": None,
        "day": 1,
        "points": 0,
        "level": 1,
        "streak": 0,
        "last_active": 0.0,
        "plan_overrides_json": None,
        "trial_days": 3,
        "trial_phase": "paid" if TEST_MODE else "trial3",
        "pending_plan_change": None,
        "crisis_count": 0,
        "created_at": time.time(),
        "test_answers": [],  # Временное хранилище для ответов теста
        "done_count": 0,
        "return_count": 0,
        "analysis_retry_count": 0,
        "has_started_training": 0,  # Флаг: 1 если юзер начал день 1
        "day_started_at": 0.0,      # Таймстамп старта текущего дня
        "last_day_ping_at": 0.0,    # Когда отправляли дневной пинг
        "last_evening_prompt_at": 0.0,  # Когда отправляли вечернее закрытие
        "evening_return_stage": None,
        "reactivation_level": 0,
        "last_event": "",
        "last_event_at": 0.0,
        "stuck_flag": "",
    }

async def init_db(db_path: str):
    """Инициализация БД"""
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                chat_id INTEGER,
                username TEXT,
                name TEXT,
                trainer_key TEXT,
                input_mode TEXT,
                mode TEXT,
                stage TEXT,
                bucket TEXT,
                analysis_json TEXT,
                plan_json TEXT,
                current_skill_id TEXT,
                pending_skill_id TEXT,
                pending_skill_day INTEGER,
                today_target TEXT,
                day INTEGER,
                created_at REAL,
                points INTEGER,
                level INTEGER,
                streak INTEGER,
                last_active REAL,
                plan_overrides_json TEXT,
                trial_days INTEGER,
                trial_phase TEXT,
                pending_plan_change TEXT,
                crisis_count INTEGER,
                test_answers TEXT,
                done_count INTEGER,
                return_count INTEGER,
                analysis_retry_count INTEGER,
                has_started_training INTEGER,
                day_started_at REAL,
                last_day_ping_at REAL,
                last_evening_prompt_at REAL,
                evening_return_stage TEXT,
                reactivation_level INTEGER,
                last_event TEXT,
                last_event_at REAL,
                stuck_flag TEXT
            )
            """
        )
        await db.commit()

async def get_user(uid: int, db_path: str) -> Dict[str, Any]:
    """Получить пользователя из БД"""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE user_id=?", (uid,))
        row = await cur.fetchone()
        if not row:
            u = default_user(uid)
            await save_user(u, db_path)
            return u

        cols = [description[0] for description in cur.description] if cur.description else []
        if cols:
            u = dict(zip(cols, row))
        else:
            u = dict(row) if hasattr(row, 'keys') else {}
        
        # Deserialize test_answers if stored as JSON string
        if 'test_answers' in u and u.get('test_answers'):
            try:
                u['test_answers'] = json.loads(u['test_answers']) if isinstance(u['test_answers'], str) else u['test_answers']
            except Exception:
                u['test_answers'] = []
        else:
            u['test_answers'] = []
        return u

async def save_user(u: Dict[str, Any], db_path: str):
    """Сохранить пользователя в БД"""
    cols = USER_FIELDS
    vals = []
    for c in cols:
        v = u.get(c)
        # Serialize lists/dicts to JSON for storage
        if isinstance(v, (list, dict)):
            try:
                v = json.dumps(v, ensure_ascii=False)
            except Exception:
                v = None
        vals.append(v)
    placeholders = ",".join(["?"] * len(cols))
    cols_sql = ",".join(cols)

    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            f"INSERT OR REPLACE INTO users ({cols_sql}) VALUES ({placeholders})",
            tuple(vals),
        )
        await db.commit()

# ============================================================
# DB MIGRATION + EVENTS (аналитика) + GAMIFY FIELDS
# ============================================================

EXTRA_USER_COLS = {
    "username": "TEXT",
    "mode": "TEXT",
    "points": "INTEGER",
    "level": "INTEGER",
    "streak": "INTEGER",
    "last_active": "REAL",
    "plan_overrides_json": "TEXT",   # правки плана после кризиса
    "trial_days": "INTEGER",         # 3 или 7
    "trial_phase": "TEXT",           # "trial3" / "trial7" / "paid" / ...
    "pending_plan_change": "TEXT",   # отложенная правка плана после кризиса
    "crisis_count": "INTEGER",       # лимит в trial
    "test_answers": "TEXT",
    "done_count": "INTEGER",
    "return_count": "INTEGER",
    "analysis_retry_count": "INTEGER",  # сколько раз пользователь сказал "ты меня не понял"
    "has_started_training": "INTEGER",  # 1 если юзер начал день 1
    "current_skill_id": "TEXT",
    "pending_skill_id": "TEXT",
    "pending_skill_day": "INTEGER",
    "today_target": "TEXT",
    "day_started_at": "REAL",
    "last_day_ping_at": "REAL",
    "last_evening_prompt_at": "REAL",
    "evening_return_stage": "TEXT",
    "reactivation_level": "INTEGER",
    "last_event": "TEXT",
    "last_event_at": "REAL",
    "stuck_flag": "TEXT",
}

async def migrate_db(db_path: str):
    """Мигрировать БД структуру"""
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute("PRAGMA table_info(users)")
        cols = [r[1] for r in await cur.fetchall()]

        for col, ctype in EXTRA_USER_COLS.items():
            if col not in cols:
                await db.execute(f"ALTER TABLE users ADD COLUMN {col} {ctype}")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL,
            user_id INTEGER,
            stage TEXT,
            event TEXT,
            meta TEXT
        )
        """)
        await db.commit()

def compute_stuck_flag(u: dict) -> str:
    """Return a coarse stuck-state label for summary exports."""
    stage = u.get("stage") or ""
    analysis_retry = int(u.get("analysis_retry_count") or 0)
    crisis_count = int(u.get("crisis_count") or 0)
    reactivation_level = int(u.get("reactivation_level") or 0)
    done_count = int(u.get("done_count") or 0)
    day = int(u.get("day") or 1)

    if stage == "confirm_analysis":
        return "stuck_after_analysis"
    if stage == "analysis_contract":
        return "stuck_after_contract"
    if day == 1 and done_count == 0 and stage in {"training", "waiting_next_day"}:
        return "stuck_day1_no_result"
    if analysis_retry >= 2:
        return "high_doubt"
    if crisis_count >= 3:
        return "high_crisis_usage"
    if reactivation_level >= 2:
        return "reactivation_risk"
    return ""


async def push_user_summary(u: dict, sheets_webhook_url: str = ""):
    """Push a flattened user summary to the webhook for dashboarding."""
    if not sheets_webhook_url:
        return

    try:
        import urllib.request

        payload = json.dumps({
            "kind": "user_summary",
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": u.get("user_id"),
            "chat_id": u.get("chat_id"),
            "username": u.get("username"),
            "name": u.get("name"),
            "trainer_key": u.get("trainer_key"),
            "mode": u.get("mode"),
            "input_mode": u.get("input_mode"),
            "stage": u.get("stage"),
            "bucket": u.get("bucket"),
            "day": u.get("day"),
            "trial_phase": u.get("trial_phase"),
            "today_target": u.get("today_target"),
            "points": u.get("points", 0),
            "level": u.get("level", 1),
            "streak": u.get("streak", 0),
            "done_count": u.get("done_count", 0),
            "return_count": u.get("return_count", 0),
            "crisis_count": u.get("crisis_count", 0),
            "analysis_retry_count": u.get("analysis_retry_count", 0),
            "reactivation_level": u.get("reactivation_level", 0),
            "last_active": u.get("last_active"),
            "last_event": u.get("last_event"),
            "last_event_at": u.get("last_event_at"),
            "is_paid": 1 if u.get("trial_phase") == "paid" else 0,
            "stuck_flag": u.get("stuck_flag", ""),
        }, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(
            sheets_webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=3).read()
    except Exception as e:
        log.exception(f"SHEETS ERROR in push_user_summary: {e}")


async def log_event(
    user_id: int,
    stage: str,
    event: str,
    meta: dict = None,
    db_path: str = "bot.db",
    sheets_webhook_url: str = "",
    user_snapshot: dict = None,
):
    """Log an event to SQLite and optionally send an expanded webhook payload."""
    meta = meta or {}
    meta_s = json.dumps(meta, ensure_ascii=False)
    ts = time.time()
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO events(ts,user_id,stage,event,meta) VALUES(?,?,?,?,?)",
            (ts, user_id, stage, event, meta_s)
        )
        await db.commit()

    if sheets_webhook_url:
        try:
            import urllib.request

            snap = user_snapshot or {}
            payload = json.dumps({
                "kind": "event",
                "ts": ts,
                "user_id": user_id,
                "chat_id": snap.get("chat_id"),
                "username": snap.get("username"),
                "name": snap.get("name"),
                "trainer_key": snap.get("trainer_key"),
                "mode": snap.get("mode"),
                "input_mode": snap.get("input_mode"),
                "stage": stage,
                "event": event,
                "day": snap.get("day"),
                "bucket": snap.get("bucket"),
                "trial_phase": snap.get("trial_phase"),
                "today_target": snap.get("today_target"),
                "meta": meta,
            }, ensure_ascii=False).encode("utf-8")

            req = urllib.request.Request(
                sheets_webhook_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=3).read()
        except Exception as e:
            log.exception(f"SHEETS ERROR in log_event: {e}")

def gamify_apply(u: dict, delta_points: int, reason: str):
    """Применить геймификацию"""
    u["points"] = int(u.get("points") or 0) + int(delta_points)
    u["level"] = max(1, int(u.get("points") or 0) // 10 + 1)

    now = time.time()
    last = float(u.get("last_active") or 0.0)
    if now - last > 18 * 3600:
        u["streak"] = 1
    else:
        u["streak"] = int(u.get("streak") or 0) + 1
    u["last_active"] = now

def is_paid(u: dict) -> bool:
    """Проверить, платит ли пользователь"""
    if TEST_MODE:
        return True
    return u.get("trial_phase") == "paid"

def should_ping(u: dict, hours: int) -> bool:
    """Проверить, нужно ли пинговать пользователя"""
    try:
        last = float(u.get("last_active") or 0)
    except (TypeError, ValueError):
        last = 0.0
    return time.time() - last > hours * 3600
