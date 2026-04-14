#!/usr/bin/env python3
import json
from datetime import date, timedelta, datetime
from pathlib import Path

from fast_flights import FlightQuery, Passengers, create_query, get_flights

ORIGIN = "AMS"
PRICE_CAP = 250
DEFAULT_MAX_TRIP_DAYS = 3
ICELAND_TRIP_DAYS = {4, 5}
ALLOWED_DEPARTURE_WEEKDAYS = {1, 3, 4, 5, 6}  # Tue Thu Fri Sat Sun (Python Mon=0)

DESTINATIONS = [
    {"code": "LON", "name": "London", "priority": 100, "max_trip_days": 3, "special_window": (date(2026, 6, 20), date(2026, 6, 23))},
    {"code": "KEF", "name": "Reykjavik", "priority": 95, "trip_days_set": {4, 5}},
    {"code": "BCN", "name": "Barcelona", "priority": 80, "max_trip_days": 3},
    {"code": "ATH", "name": "Athens", "priority": 78, "max_trip_days": 3},
    {"code": "CPH", "name": "Copenhagen", "priority": 76, "max_trip_days": 3},
    {"code": "DUB", "name": "Dublin", "priority": 75, "max_trip_days": 3},
    {"code": "LIS", "name": "Lisbon", "priority": 74, "max_trip_days": 3},
    {"code": "OSL", "name": "Oslo", "priority": 72, "max_trip_days": 3},
    {"code": "ARN", "name": "Stockholm", "priority": 70, "max_trip_days": 3},
    {"code": "MAD", "name": "Madrid", "priority": 68, "max_trip_days": 3},
    {"code": "PRG", "name": "Prague", "priority": 66, "max_trip_days": 3},
    {"code": "BUD", "name": "Budapest", "priority": 64, "max_trip_days": 3},
    {"code": "VIE", "name": "Vienna", "priority": 62, "max_trip_days": 3},
    {"code": "ZRH", "name": "Zurich", "priority": 60, "max_trip_days": 3},
    {"code": "MUC", "name": "Munich", "priority": 58, "max_trip_days": 3},
    {"code": "IST", "name": "Istanbul", "priority": 56, "max_trip_days": 3},
    {"code": "FCO", "name": "Rome", "priority": 45, "max_trip_days": 3},
    {"code": "CDG", "name": "Paris", "priority": 5, "max_trip_days": 3},
]


def daterange(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def allowed_trip_lengths(dest: dict):
    if "trip_days_set" in dest:
        return sorted(dest["trip_days_set"])
    return list(range(3, dest.get("max_trip_days", DEFAULT_MAX_TRIP_DAYS) + 1))


def should_use_departure(d: date):
    return d.weekday() in ALLOWED_DEPARTURE_WEEKDAYS


def return_within_tuesday(dep: date, ret: date):
    return ret.weekday() <= 1 or ret.weekday() == 0  # Mon/Tue


def build_query(dest_code: str, dep: date, ret: date):
    return create_query(
        flights=[
            FlightQuery(date=dep.isoformat(), from_airport=ORIGIN, to_airport=dest_code, max_stops=0),
            FlightQuery(date=ret.isoformat(), from_airport=dest_code, to_airport=ORIGIN, max_stops=0),
        ],
        seat="economy",
        trip="round-trip",
        passengers=Passengers(adults=1),
        language="en-US",
        currency="EUR",
    )


def get_best_roundtrip(dest: dict, search_start: date, search_end: date):
    best = None

    special_window = dest.get("special_window")
    if special_window:
        dep_start, dep_end = special_window
        candidate_departures = list(daterange(dep_start, dep_end))
    else:
        candidate_departures = [d for d in daterange(search_start, search_end) if d.weekday() in ALLOWED_DEPARTURE_WEEKDAYS][:12]

    for dep in candidate_departures:

        for trip_days in allowed_trip_lengths(dest):
            ret = dep + timedelta(days=trip_days)
            if ret > search_end + timedelta(days=7):
                continue
            if not return_within_tuesday(dep, ret):
                continue

            try:
                print(f"checking {dest['code']} {dep.isoformat()} -> {ret.isoformat()}", flush=True)
                q = build_query(dest["code"], dep, ret)
                results = get_flights(q)
                if not results:
                    continue

                cheapest = min(results, key=lambda x: x.price)
                if cheapest.price > PRICE_CAP:
                    continue

                candidate = {
                    "code": dest["code"],
                    "name": dest["name"],
                    "departure_date": dep.isoformat(),
                    "return_date": ret.isoformat(),
                    "trip_days": trip_days,
                    "price": cheapest.price,
                    "airlines": cheapest.airlines,
                    "priority": dest["priority"],
                }

                if best is None or (candidate["price"], -candidate["priority"]) < (best["price"], -best["priority"]):
                    best = candidate
            except Exception:
                continue

    return best


def main():
    today = date.today()
    search_start = today
    search_end = today + timedelta(days=35)

    results = []
    for dest in sorted(DESTINATIONS, key=lambda x: -x["priority"]):
        best = get_best_roundtrip(dest, search_start, search_end)
        if best:
            results.append(best)

    results.sort(key=lambda x: (x["price"], -x["priority"]))

    Path("results").mkdir(exist_ok=True)
    out = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "origin": ORIGIN,
        "constraints": {
            "nonstop_only": True,
            "round_trip": True,
            "price_cap_eur": PRICE_CAP,
            "default_max_trip_days": DEFAULT_MAX_TRIP_DAYS,
            "iceland_trip_days": sorted(ICELAND_TRIP_DAYS),
            "allowed_departure_weekdays": ["Tue", "Thu", "Fri", "Sat", "Sun"],
            "return_preference": "Mon/Tue",
        },
        "results": results,
    }

    with open("results/filtered_flights.json", "w") as f:
        json.dump(out, f, indent=2)

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
