import datetime as dt
import hashlib

from fastapi import FastAPI, HTTPException, Query

app = FastAPI(title="Mock Airline API")

AIRPORTS = {
    "DEL": "Delhi", "BOM": "Mumbai", "BLR": "Bengaluru",
    "HYD": "Hyderabad", "MAA": "Chennai", "CCU": "Kolkata",
}

# (airline, flight number, departure hour, departure minute)
SLOTS = [
    ("Air India", "AI101", 6, 15),
    ("IndiGo", "6E202", 9, 40),
    ("Vistara", "UK303", 14, 5),
    ("IndiGo", "6E404", 19, 30),
]

BOOKINGS = {
    "ABC123": {
        "pnr": "ABC123", "status": "CONFIRMED", "passenger": "Ravi Kumar",
        "flight_no": "6E202", "origin": "DEL", "destination": "BOM",
        "departure": "2026-11-20T09:40:00", "fare_type": "SAVER",
        "total_paid_inr": 5200,
    },
    "XYZ789": {
        "pnr": "XYZ789", "status": "CANCELLED", "passenger": "Anita Rao",
        "flight_no": "AI101", "origin": "BLR", "destination": "DEL",
        "departure": "2026-11-18T06:15:00", "fare_type": "FLEX",
        "total_paid_inr": 8900,
    },
}

FARE_RULES = {
    "SAVER": {
        "changes": "Allowed up to 24h before departure. Fee INR 3000 plus any fare difference.",
        "cancellation": "Refund minus INR 3500 fee. No refund within 4h of departure.",
        "baggage": "15 kg check-in, 7 kg cabin.",
    },
    "FLEX": {
        "changes": "Free changes up to 2h before departure. Fare difference applies.",
        "cancellation": "Refund minus INR 1000 fee. No refund within 2h of departure.",
        "baggage": "25 kg check-in, 7 kg cabin.",
    },
}


def _seed(*parts) -> int:
    return int(hashlib.md5("|".join(map(str, parts)).encode()).hexdigest(), 16)


@app.get("/airports")
def airports():
    return AIRPORTS


@app.get("/flights/search")
def search_flights(
    origin: str,
    destination: str,
    travel_date: dt.date = Query(..., alias="date"),
):
    origin, destination = origin.upper(), destination.upper()
    if origin not in AIRPORTS or destination not in AIRPORTS:
        raise HTTPException(404, "Unknown airport code")
    if origin == destination:
        raise HTTPException(400, "Origin and destination must differ")
    if travel_date < dt.date.today():
        raise HTTPException(400, "Date is in the past")

    flights = []
    for airline, number, hour, minute in SLOTS:
        s = _seed(origin, destination, travel_date, number)
        dep = dt.datetime.combine(travel_date, dt.time(hour, minute))
        arr = dep + dt.timedelta(minutes=110 + s % 70)
        flights.append(
            {
                "flight_id": f"{number}-{travel_date}",
                "flight_no": number,
                "airline": airline,
                "origin": origin,
                "destination": destination,
                "departure": dep.isoformat(),
                "arrival": arr.isoformat(),
                "fare_type": "SAVER" if s % 2 else "FLEX",
                "price_inr": 3000 + (s // 7) % 5000,
                "seats_left": 1 + (s // 11) % 9,
            }
        )
    return flights


@app.get("/bookings/{pnr}")
def get_booking(pnr: str):
    booking = BOOKINGS.get(pnr.upper())
    if not booking:
        raise HTTPException(404, "Booking not found")
    return booking


@app.get("/fare-rules/{fare_type}")
def get_fare_rules(fare_type: str):
    rules = FARE_RULES.get(fare_type.upper())
    if not rules:
        raise HTTPException(404, "Unknown fare type. Known: SAVER, FLEX")
    return {"fare_type": fare_type.upper(), **rules}