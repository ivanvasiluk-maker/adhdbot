# ADHD Self-Regulation Trainer Bot

Telegram bot that guides users through a 28-day self-regulation practice with three trainer personas (Skinny, Marsha, Beck). Built on aiogram 3, stores state in SQLite, and can optionally use OpenAI for analysis and Whisper transcription.

## Features
- Onboarding flow with trainer selection and multiple diagnostic modes (text, voice via Whisper, quick test).
- Daily skill plan with short practice loops, progress logging, and crisis flow entry from any stage.
- Optional AI analysis (OpenAI Chat + Whisper); falls back to scripted responses when API keys are absent.
- SQLite persistence with automatic init/migrations at startup.
- Dockerfile for containerized runs.

## Requirements
- Python 3.11
- Telegram bot token
- (Optional) OpenAI API key for AI analysis and voice transcription

## Setup
1) Clone the repo and create a virtualenv (Windows example):
```powershell
python -m venv venv
./venv/Scripts/Activate.ps1
```
2) Install dependencies:
```powershell
pip install -r requirements.txt
```
3) Set environment variables (e.g., via Railway/Render/Heroku Variables). For local dev you can export them or use a local `.env` if you prefer; production should rely on platform vars.
4) Run the bot:
```powershell
python bot.py
```

## Environment variables
Env vars (set in your platform/terminal):
```
BOT_TOKEN=your-telegram-bot-token
OPENAI_API_KEY=your-openai-key-optional
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_WHISPER_MODEL=whisper-1
DB_PATH=bot.db
PAYMENT_URL=
PAYMENT_URL_DISCOUNT=
PAYMENT_URL_FULL=
SHEETS_WEBHOOK_URL=
TEST_MODE=0
```
Notes:
- Leave `OPENAI_API_KEY` empty to run without AI features.
- Set `TEST_MODE=1` to skip paywalls and unlock full flow during testing.
- `DB_PATH` points to the SQLite file; it is auto-created/migrated on start.

## Docker
Build and run with Docker:
```bash
docker build -t adhd-bot .
docker run --env-file .env adhd-bot
```

## Files of interest
- [bot.py](bot.py): entrypoint, router, background tasks.
- [flows.py](flows.py): main flow helpers (analysis, crises, day transitions).
- [texts.py](texts.py): trainer texts, keyboards, and constants.
- [skills.py](skills.py): skill catalog and plan builders.
- [db.py](db.py): SQLite helpers and migrations.
- [state_machine.py](state_machine.py): explicit behavioral states and transitions.
- [templates.py](templates.py): UI text templates for short scripted loop responses.
- [prompts.py](prompts.py): GPT prompts for analysis, skill selection, and crisis checks.
- [events.py](events.py): safe event logger with non-breaking writes.
- [sheets_sync.py](sheets_sync.py): background sync of unsynced events batches.
- [payments.py](payments.py): MVP payment stub handlers.
- [admin.py](admin.py): `/stats` aggregation helpers with ADMIN_IDS access gate.
- [skills.json](skills.json): normalized skill catalog for one-skill-per-day logic.

## Troubleshooting
- If `BOT_TOKEN` is missing, startup raises a runtime error.
- If OpenAI import fails, the bot logs a warning and continues without AI features.
- Configure env vars in your hosting (Railway/Render/Heroku/etc.). For local runs you may still source a `.env`, but production should rely on platform vars; `bot.py` reads from the environment directly.
