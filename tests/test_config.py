import importlib
import sys
import types

import pytest


class DummyOpenAI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.chat = types.SimpleNamespace(
            completions=types.SimpleNamespace(create=self._chat_create)
        )
        self.audio = types.SimpleNamespace(
            transcriptions=types.SimpleNamespace(create=self._audio_create)
        )

    def _chat_create(self, **kwargs):
        msg = types.SimpleNamespace(content="AI работает")
        choice = types.SimpleNamespace(message=msg)
        return types.SimpleNamespace(choices=[choice])

    def _audio_create(self, **kwargs):
        return types.SimpleNamespace(text="decoded voice")


def load_bot(monkeypatch, api_key: str):
    monkeypatch.setenv("BOT_TOKEN", "dummy-token")
    monkeypatch.setenv("OPENAI_API_KEY", api_key)
    monkeypatch.setenv("OPENAI_CHAT_MODEL", "test-model")
    monkeypatch.setenv("OPENAI_WHISPER_MODEL", "whisper-1")
    sys.modules.pop("bot", None)
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=DummyOpenAI))
    return importlib.import_module("bot")


def test_config_without_openai_key(monkeypatch):
    bot = load_bot(monkeypatch, api_key="")
    assert bot.AI_ANALYSIS_ENABLED is False
    assert bot.client is None


def test_config_with_openai_key(monkeypatch):
    bot = load_bot(monkeypatch, api_key="sk-test")
    assert bot.AI_ANALYSIS_ENABLED is True
    assert bot.client is not None
    assert getattr(bot.client, "api_key", None) == "sk-test"


@pytest.mark.asyncio
async def test_ai_micro_reflect_smoke(monkeypatch):
    bot = load_bot(monkeypatch, api_key="sk-test")
    reply = await bot.ai_micro_reflect("sample text", "skinny", bot.client, bot.OPENAI_CHAT_MODEL)
    assert reply == "AI работает"
