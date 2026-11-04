from openai import OpenAI

from .config import LLM_API_KEY, LLM_BASE_URL, SYSTEM_PROMPT

# One shared client. Swapping provider = changing .env only.
client = OpenAI(api_key=LLM_API_KEY or "missing", base_url=LLM_BASE_URL)


def with_system(messages: list[dict]) -> list[dict]:
    """Always put OUR system prompt first. Clients can't override it."""
    return [{"role": "system", "content": SYSTEM_PROMPT}, *messages]