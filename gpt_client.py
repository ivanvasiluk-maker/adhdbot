from __future__ import annotations

import json
from typing import Any

from openai import OpenAI


def build_client(api_key: str) -> OpenAI | None:
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def extract_json_or_none(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except Exception:
        return None
