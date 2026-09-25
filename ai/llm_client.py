"""
ai/llm_client.py
------------------
Thin wrapper around the Anthropic Messages API. If ANTHROPIC_API_KEY
isn't set, call() returns None and the caller (structured_extraction.py)
falls back to rule-based drafting - the whole system stays demoable
without requiring an API key on setup day.
"""

import httpx

from app.config import settings

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


def is_configured() -> bool:
    return bool(settings.ANTHROPIC_API_KEY)


def call(system_prompt: str, user_prompt: str, max_tokens: int = 800) -> str | None:
    """
    Returns the model's raw text response, or None if the LLM is not
    configured or the call fails for any reason. Callers must handle
    the None case gracefully rather than let it raise - a flaky or
    missing API key should never take the whole triage flow down.
    """
    if not is_configured():
        return None

    try:
        response = httpx.post(
            ANTHROPIC_URL,
            headers={
                "x-api-key": settings.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": settings.ANTHROPIC_MODEL,
                "max_tokens": max_tokens,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=20.0,
        )
        response.raise_for_status()
        data = response.json()
        text_blocks = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
        return "\n".join(text_blocks) if text_blocks else None
    except (httpx.HTTPError, KeyError, ValueError):
        return None
