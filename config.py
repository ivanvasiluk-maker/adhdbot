import os

BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()
OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY") or "").strip()
OPENAI_CHAT_MODEL = (os.getenv("OPENAI_CHAT_MODEL") or "gpt-4o-mini").strip()
DB_PATH = (os.getenv("DB_PATH") or "bot.db").strip()
SHEETS_WEBHOOK_URL = (os.getenv("SHEETS_WEBHOOK_URL") or "").strip()
ADMIN_IDS = (os.getenv("ADMIN_IDS") or "").strip()
