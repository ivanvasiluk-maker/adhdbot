import asyncio, sys, types

def safe(s):
    try:
        return str(s).encode('utf-8', 'replace').decode('utf-8')
    except Exception:
        return repr(s)

def p(line):
    sys.stdout.buffer.write((line + '\n').encode('utf-8', 'replace'))
    sys.stdout.buffer.flush()

async def main():
    import aiosqlite
    import bot as botmod
    import db as dbmod

    await dbmod.init_db(botmod.DB_PATH)
    await dbmod.migrate_db(botmod.DB_PATH)

    UID = 900000310

    async with aiosqlite.connect(botmod.DB_PATH) as conn:
        await conn.execute("DELETE FROM users WHERE user_id=?", (UID,))
        await conn.commit()

    sent = []

    class FakeBot:
        async def send_message(self, chat_id, text, **kw):
            sent.append(safe(text)[:70])
        async def send_photo(self, *a, **kw):
            sent.append("[photo]")

    class FakeMsg:
        def __init__(self, text):
            self.text = text
            self.chat = types.SimpleNamespace(id=UID)
            self.from_user = types.SimpleNamespace(id=UID, first_name="Иван", username="ivan_test")
            self.bot = FakeBot()
        async def answer(self, text, **kw):
            sent.append(safe(text)[:70])

    async def step(text, label, handler=None):
        sent.clear()
        msg = FakeMsg(text)
        fn = handler or botmod.main_flow
        await fn(msg)
        u = await dbmod.get_user(UID, botmod.DB_PATH)
        stage = u.get("stage", "?") if u else "?"
        p(f"{label:30s} -> {stage:30s} | msgs={len(sent)}")
        for s in sent[:2]:
            p(f"   {s[:70]}")
        return u

    await step("/start", "/start", handler=botmod.cmd_start)
    await step("Иван",                      "name")
    await step("\U0001f408 Марша (мягко)",  "trainer")
    await step("\u2705 Да",                 "trainer_intro_yes")
    await step("\U0001f9e0 Диагностика текстом", "input_mode_text")
    await step("Сложно начать новое дело",  "problem_text")
    await step("\u2705 Да, в точку",        "confirm_analysis_yes")
    await step("\U0001f4dc Принимаю контракт", "contract_accept")
    await step("\U0001f4dc Принимаю план",  "map_accept")

    # debug: check DB state before start_training
    u_pre = await dbmod.get_user(UID, botmod.DB_PATH)
    p(f"  [pre-train] stage={u_pre.get('stage')} day={u_pre.get('day')} skill={u_pre.get('current_skill_id')} has_started={u_pre.get('has_started_training')}")

    await step("\U0001f4aa Давай тренировать навык", "start_training")
    await step("\u2705 Сделал(а)",          "done")
    await step("\U0001f642 Нормально",      "post_reflection")

    async with aiosqlite.connect(botmod.DB_PATH) as conn:
        await conn.execute("UPDATE users SET stage=? WHERE user_id=?", ("day_evening", UID))
        await conn.commit()

    await step("\u2705 Что-то получилось",  "evening_ok")

asyncio.run(main())
