#!/usr/bin/env python3
import json
from datetime import date, timedelta, datetime
from pathlib import Path

from fast_flights import FlightQuery, Passengers, create_query, get_flights

ORIGIN = "AMS"
PRICE_CAP = 250
LONDON_CODES = ["LHR", "LGW", "STN", "LTN"]
AIRPORT_PRIORITY = {"LHR": 0, "LGW": 1, "LCY": 2, "STN": 3, "LTN": 4}
LONDON_WINDOW_START = date(2026, 6, 10)
LONDON_WINDOW_END = date(2026, 6, 18)

def build_query(dest_code: str, dep: date, ret: date):
    return create_query(
        flights=[
            FlightQuery(date=dep.isoformat(), from_airport=ORIGIN, to_airport=dest_code, max_stops=0),
            FlightQuery(date=ret.isoformat(), from_airport=dest_code, to_airport=ORIGIN, max_stops=0),
        ],
        seat="economy", trip="round-trip", passengers=Passengers(adults=1),
        language="en-US", currency="EUR",
    )

def main():
    results = []
    for dep in [LONDON_WINDOW_START + timedelta(days=i) for i in range((LONDON_WINDOW_END - LONDON_WINDOW_START).days + 1)]:
        for trip_days in range(3, 5):
            ret = dep + timedelta(days=trip_days)
            if ret > LONDON_WINDOW_END + timedelta(days=3): continue
            for code in LONDON_CODES:
                try:
                    print(f"checking London {code} {dep.isoformat()} -> {ret.isoformat()}", flush=True)
                    q = build_query(code, dep, ret)
                    flights = get_flights(q)
                    if not flights: continue
                    cheapest = min(flights, key=lambda x: x.price)
                    if cheapest.price > PRICE_CAP: continue
                    results.append({"code": code, "name": "London", "departure_date": dep.isoformat(),
                                    "return_date": ret.isoformat(), "trip_days": trip_days, "price": cheapest.price,
                                    "airlines": cheapest.airlines, "airport_priority": AIRPORT_PRIORITY.get(code, 99)})
                except Exception: continue
    results.sort(key=lambda x: (x["airport_priority"], x["price"], -x["trip_days"]))
    Path("results").mkdir(exist_ok=True)
    out = {"generated_at": datetime.utcnow().isoformat() + "Z", "origin": ORIGIN, "search_type": "london_vct",
           "event": "VCT Masters London", "window": {"start": LONDON_WINDOW_START.isoformat(), "end": LONDON_WINDOW_END.isoformat()},
           "constraints": {"nonstop_only": True, "round_trip": True, "price_cap_eur": PRICE_CAP},
           "results": results}
    with open("results/london_flights.json", "w") as f: json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))

if __name__ == "__main__": main()
