import os

from dotenv import load_dotenv

load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL") or None  # empty means OpenAI default
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
]

SYSTEM_PROMPT = (
    "You are an airline booking assistant. Be concise and friendly. "
    "If you do not know something, say so instead of guessing."
)