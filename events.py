from __future__ import annotations

import json
import logging
import time

import aiosqlite

log = logging.getLogger("bot")


async def log_event(user_id: int, event_name: str, event_data: dict | None = None, db_path: str = "bot.db") -> None:
    payload = json.dumps(event_data or {}, ensure_ascii=False)
    created_at = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        async with aiosqlite.connect(db_path) as db:
            await db.execute(
                "INSERT INTO events(user_id, event_name, event_data, created_at, synced) VALUES(?,?,?,?,0)",
                (user_id, event_name, payload, created_at),
            )
            await db.commit()
    except Exception:
        log.exception("Failed to log event %s for user %s", event_name, user_id)
