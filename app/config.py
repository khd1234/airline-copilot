import os

from dotenv import load_dotenv

load_dotenv()

ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
]
BOOKING_API_URL = os.getenv("BOOKING_API_URL", "http://localhost:8001")

# Providers are tried in order. All must speak the OpenAI API format.
PROVIDERS = [
    {
        "name": "primary",
        "api_key": os.getenv("LLM_API_KEY", ""),
        "base_url": os.getenv("LLM_BASE_URL") or None,
        "model": os.getenv("LLM_MODEL", "gpt-4o-mini"),
    }
]
if os.getenv("FALLBACK_LLM_API_KEY"):
    PROVIDERS.append(
        {
            "name": "fallback",
            "api_key": os.getenv("FALLBACK_LLM_API_KEY"),
            "base_url": os.getenv("FALLBACK_LLM_BASE_URL") or None,
            "model": os.getenv("FALLBACK_LLM_MODEL", "gemini-2.5-flash"),
        }
    )

SYSTEM_PROMPT = (
    "You are an airline booking assistant for a demo airline. Today is {today}.\n"
    "Rules:\n"
    "- For flights, bookings or fare rules, ALWAYS use the tools. Never invent "
    "flights, prices, PNR details or policies.\n"
    "- If a tool returns an error or no results, say so plainly.\n"
    "- Airport codes: Delhi=DEL, Mumbai=BOM, Bengaluru=BLR, Hyderabad=HYD, "
    "Chennai=MAA, Kolkata=CCU. Resolve relative dates like 'tomorrow' or "
    "'Friday' using today's date.\n"
    "- You cannot book, change or cancel anything yet. If asked, say it is not "
    "available yet.\n"
    "- Be concise and friendly."
)