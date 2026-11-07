import json
import re

import httpx

from .config import BOOKING_API_URL

IATA = re.compile(r"^[A-Za-z]{3}$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PNR = re.compile(r"^[A-Za-z0-9]{6}$")


def _get(path: str, params: dict | None = None):
    """Call the booking API. Errors become {"error": ...} so the model can explain."""
    try:
        r = httpx.get(f"{BOOKING_API_URL}{path}", params=params, timeout=10)
    except httpx.HTTPError:
        return {"error": "Booking service is unreachable"}
    if r.status_code == 200:
        return r.json()
    try:
        detail = r.json().get("detail", "")
    except ValueError:
        detail = ""
    return {"error": detail or f"Booking service error {r.status_code}"}


# ---- tool implementations (READ-only) ----

def search_flights(origin: str, destination: str, date: str):
    if not (IATA.match(origin) and IATA.match(destination)):
        return {"error": "origin and destination must be 3-letter airport codes"}
    if not DATE.match(date):
        return {"error": "date must be YYYY-MM-DD"}
    data = _get("/flights/search", {"origin": origin, "destination": destination, "date": date})
    if isinstance(data, dict) and "error" in data:
        return data
    return {"count": len(data), "flights": data}


def get_booking(pnr: str):
    if not PNR.match(pnr):
        return {"error": "pnr must be 6 letters or digits"}
    return _get(f"/bookings/{pnr}")


def get_fare_rules(fare_type: str):
    if not re.match(r"^[A-Za-z]{3,10}$", fare_type):
        return {"error": "invalid fare type"}
    return _get(f"/fare-rules/{fare_type}")


# ---- what the model sees ----

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_flights",
            "description": "Search available flights between two airports on a given date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "IATA code, e.g. DEL"},
                    "destination": {"type": "string", "description": "IATA code, e.g. BOM"},
                    "date": {"type": "string", "description": "Travel date, YYYY-MM-DD"},
                },
                "required": ["origin", "destination", "date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_booking",
            "description": "Look up an existing booking by its 6-character PNR.",
            "parameters": {
                "type": "object",
                "properties": {"pnr": {"type": "string", "description": "e.g. ABC123"}},
                "required": ["pnr"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_fare_rules",
            "description": "Get change, cancellation and baggage rules for a fare type (SAVER or FLEX).",
            "parameters": {
                "type": "object",
                "properties": {"fare_type": {"type": "string", "description": "SAVER or FLEX"}},
                "required": ["fare_type"],
            },
        },
    },
]

REGISTRY = {
    "search_flights": search_flights,
    "get_booking": get_booking,
    "get_fare_rules": get_fare_rules,
}


def run_tool(name: str, raw_arguments: str):
    """Run a tool the model asked for. Never raises: errors go back to the model."""
    fn = REGISTRY.get(name)
    if not fn:
        return {"error": f"unknown tool '{name}'"}
    try:
        args = json.loads(raw_arguments or "{}")
    except json.JSONDecodeError:
        return {"error": "arguments were not valid JSON"}
    if not isinstance(args, dict):
        return {"error": "arguments must be a JSON object"}
    try:
        return fn(**args)
    except TypeError as e:
        return {"error": f"bad arguments: {e}"}