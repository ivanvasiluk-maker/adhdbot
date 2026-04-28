from __future__ import annotations

import json
import logging
import os
import urllib.request

import aiosqlite

log = logging.getLogger("bot")


async def sync_unsynced_events(db_path: str = "bot.db", batch_size: int = 50, webhook_url: str | None = None) -> int:
    url = (webhook_url or os.getenv("SHEETS_WEBHOOK_URL") or "").strip()
    if not url:
        return 0

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT id, user_id, event_name, event_data, created_at FROM events WHERE synced=0 ORDER BY id LIMIT ?",
            (batch_size,),
        )
        rows = await cur.fetchall()

        if not rows:
            return 0

        payload = [dict(r) for r in rows]
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps({"kind": "events_batch", "events": payload}, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=4).read()
            ids = [int(r["id"]) for r in rows]
            placeholders = ",".join(["?"] * len(ids))
            await db.execute(f"UPDATE events SET synced=1 WHERE id IN ({placeholders})", ids)
            await db.commit()
            return len(ids)
        except Exception:
            log.exception("Failed to sync events to Google Sheets")
            return 0
