from __future__ import annotations

import os

import aiosqlite


def _admin_ids() -> set[int]:
    raw = (os.getenv("ADMIN_IDS") or "").strip()
    out = set()
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            out.add(int(part))
    return out


def is_admin(user_id: int) -> bool:
    return int(user_id) in _admin_ids()


async def build_stats_text(db_path: str = "bot.db") -> str:
    queries = {
        "users_total": "SELECT COUNT(*) FROM users",
        "new_today": "SELECT COUNT(*) FROM users WHERE date(created_at)=date('now')",
        "day1_started": "SELECT COUNT(DISTINCT user_id) FROM events WHERE event_name='onboarding_started'",
        "day1_first_action": "SELECT COUNT(DISTINCT user_id) FROM events WHERE event_name='action_done'",
        "payment_completed": "SELECT COUNT(*) FROM events WHERE event_name='payment_completed'",
        "offer_shown": "SELECT COUNT(*) FROM events WHERE event_name='offer_shown'",
        "pay_20": "SELECT COUNT(*) FROM events WHERE event_name='payment_click_20'",
        "pay_40": "SELECT COUNT(*) FROM events WHERE event_name='payment_click_40'",
        "declined": "SELECT COUNT(*) FROM events WHERE event_name='payment_declined_soft'",
        "action_sent": "SELECT COUNT(*) FROM events WHERE event_name='action_sent'",
        "action_done": "SELECT COUNT(*) FROM events WHERE event_name='action_done'",
        "action_failed": "SELECT COUNT(*) FROM events WHERE event_name='action_failed'",
        "action_resized": "SELECT COUNT(*) FROM events WHERE event_name='action_resized'",
        "free_mode": "SELECT COUNT(*) FROM users WHERE free_mode=1",
        "paid_mode": "SELECT COUNT(*) FROM users WHERE payment_status='paid'",
        "crisis_clicked": "SELECT COUNT(*) FROM events WHERE event_name='crisis_clicked'",
    }

    async with aiosqlite.connect(db_path) as db:
        metrics = {}
        for key, sql in queries.items():
            cur = await db.execute(sql)
            row = await cur.fetchone()
            metrics[key] = int(row[0] or 0)

    return (
        "📊 /stats\n"
        f"Пользователей всего: {metrics['users_total']}\n"
        f"Новых сегодня: {metrics['new_today']}\n"
        f"День 1: начали={metrics['day1_started']}, первое действие={metrics['day1_first_action']}, конверсия={metrics['payment_completed']}\n"
        f"День 3 оффер: {metrics['offer_shown']}\n"
        f"€20: {metrics['pay_20']} | €40: {metrics['pay_40']} | Подумаю: {metrics['declined']}\n"
        "Action loop: "
        f"sent={metrics['action_sent']}, done={metrics['action_done']}, failed={metrics['action_failed']}, resized={metrics['action_resized']}\n"
        f"Режимы: free={metrics['free_mode']}, paid={metrics['paid_mode']}, crisis={metrics['crisis_clicked']}"
    )
