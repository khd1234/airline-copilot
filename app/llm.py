import logging
from datetime import date

import openai
from openai import OpenAI

from .config import PROVIDERS, SYSTEM_PROMPT

log = logging.getLogger("copilot.llm")

_clients = [
    (
        p["name"],
        p["model"],
        OpenAI(
            api_key=p["api_key"] or "missing",
            base_url=p["base_url"],
            timeout=30.0,
            max_retries=0,  # we handle failover ourselves
        ),
    )
    for p in PROVIDERS
]

FALLBACK_ERRORS = (
    openai.APIConnectionError,   # includes timeouts
    openai.RateLimitError,
    openai.InternalServerError,  # 5xx
    openai.AuthenticationError,
    openai.NotFoundError,        # wrong model name
)


def _should_fallback(e: Exception) -> bool:
    if isinstance(e, FALLBACK_ERRORS):
        return True
    if isinstance(e, openai.BadRequestError):
        # Groq's llama models sometimes fail to format a tool call.
        text = str(e).lower()
        return "tool_use_failed" in text or "failed to call a function" in text
    return False


def _call(messages: list[dict], stream: bool = False, **kwargs):
    last = None
    for name, model, client in _clients:
        try:
            result = client.chat.completions.create(
                model=model, messages=messages, stream=stream, **kwargs
            )
            return result, name
        except Exception as e:
            if not _should_fallback(e):
                raise
            log.warning("provider %s failed (%s); trying next", name, type(e).__name__)
            last = e
    raise last


def chat_completion(messages: list[dict], **kwargs):
    """Returns (response, provider_name). Pass tools=... for tool calling."""
    return _call(messages, **kwargs)


def create_stream(messages: list[dict]):
    """Returns (stream, provider_name)."""
    return _call(messages, stream=True)


def with_system(messages: list[dict]) -> list[dict]:
    today = date.today().strftime("%A, %Y-%m-%d")
    return [{"role": "system", "content": SYSTEM_PROMPT.format(today=today)}, *messages]