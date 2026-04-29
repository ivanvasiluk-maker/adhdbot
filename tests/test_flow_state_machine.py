import importlib
import sys
import types

import pytest


class DummyOpenAI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.chat = types.SimpleNamespace(
            completions=types.SimpleNamespace(create=lambda **kwargs: types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="ok"))]))
        )
        self.audio = types.SimpleNamespace(
            transcriptions=types.SimpleNamespace(create=lambda **kwargs: types.SimpleNamespace(text="decoded"))
        )


def load_bot(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "dummy-token")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    sys.modules.pop("bot", None)
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=DummyOpenAI))
    return importlib.import_module("bot")


class FakeMessage:
    def __init__(self, text: str):
        self.text = text
        self.voice = None
        self.from_user = types.SimpleNamespace(id=42, username="u", full_name="User")
        self.chat = types.SimpleNamespace(id=100)
        self.answers = []

    async def answer(self, text, reply_markup=None, parse_mode=None):
        self.answers.append((text, reply_markup, parse_mode))


@pytest.mark.asyncio
async def test_morning_checkin_moves_to_target(monkeypatch):
    bot = load_bot(monkeypatch)
    user = {
        "user_id": 42,
        "stage": "morning_checkin",
        "trainer_key": "marsha",
        "day": 2,
    }

    async def fake_get_user(uid, db):
        return user

    async def fake_save_user(u, db):
        user.update(u)

    monkeypatch.setattr(bot, "get_user", fake_get_user)
    monkeypatch.setattr(bot, "save_user", fake_save_user)

    m = FakeMessage("нормально")
    await bot.main_flow(m)

    assert user["stage"] == "await_training_target"
    assert any("Перед стартом" in a[0] for a in m.answers)


@pytest.mark.asyncio
async def test_evening_close_maps_returned_option(monkeypatch):
    bot = load_bot(monkeypatch)
    user = {
        "user_id": 42,
        "stage": "evening_close_wait",
        "trainer_key": "marsha",
        "day": 2,
        "evening_return_stage": "training",
    }

    events = []

    async def fake_get_user(uid, db):
        return user

    async def fake_save_user(u, db):
        user.update(u)

    async def fake_log_event(*args, **kwargs):
        events.append((args, kwargs))

    monkeypatch.setattr(bot, "get_user", fake_get_user)
    monkeypatch.setattr(bot, "save_user", fake_save_user)
    monkeypatch.setattr(bot, "log_event", fake_log_event)

    m = FakeMessage("↩️ срывался, но возвращался")
    await bot.main_flow(m)

    assert user["stage"] == "training"
    payload = events[0][0][3]
    assert payload["mapped"] == "Срывался, но возвращался"

