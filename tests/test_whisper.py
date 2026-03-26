import importlib
import io
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


class DummyBot:
    async def get_file(self, file_id):
        return types.SimpleNamespace(file_path="voice.ogg")

    async def download_file(self, file_path):
        return io.BytesIO(b"dummy voice data")


class DummyVoice:
    def __init__(self, file_id: str):
        self.file_id = file_id


def load_bot(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "dummy-token")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_CHAT_MODEL", "test-model")
    monkeypatch.setenv("OPENAI_WHISPER_MODEL", "whisper-1")
    sys.modules.pop("bot", None)
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=DummyOpenAI))
    return importlib.import_module("bot")


@pytest.mark.asyncio
async def test_whisper_transcribe_smoke(monkeypatch):
    bot = load_bot(monkeypatch)
    message = types.SimpleNamespace(voice=DummyVoice("file-id"), bot=DummyBot())
    text = await bot.whisper_transcribe(message)
    assert text == "decoded voice"
