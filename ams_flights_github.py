#!/usr/bin/env python3
"""
AMS Flights - GitHub Actions Version (Runs on US servers, no consent wall!)
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

try:
    from fast_flights import FlightQuery, Passengers, create_query, get_flights
    FAST_FLIGHTS_AVAILABLE = True
except ImportError:
    FAST_FLIGHTS_AVAILABLE = False
    print("❌ fast_flights not installed")
    sys.exit(1)

def scan_deals(region="europe", days=3):
    """Scan multiple destinations for deals."""
    destinations = {
        "europe": [
            ("LHR", "London"), ("CDG", "Paris"), ("FCO", "Rome"), 
            ("BCN", "Barcelona"), ("MUC", "Munich"), ("VIE", "Vienna"),
            ("ZRH", "Zurich"), ("CPH", "Copenhagen"), ("DUB", "Dublin"),
            ("LIS", "Lisbon"), ("ATH", "Athens"), ("IST", "Istanbul"),
            ("PRG", "Prague"), ("BUD", "Budapest"), ("WAW", "Warsaw"),
            ("AMS", "Amsterdam"), ("BRU", "Brussels"), ("TXL", "Berlin"),
            ("MAD", "Madrid"), ("OSL", "Oslo"), ("ARN", "Stockholm"),
        ],
        "long": [
            ("JFK", "NYC"), ("LAX", "Los Angeles"), ("SFO", "San Francisco"),
            ("MIA", "Miami"), ("ORD", "Chicago"), ("YYZ", "Toronto"),
            ("DXB", "Dubai"), ("SIN", "Singapore"), ("BKK", "Bangkok"),
            ("HKG", "Hong Kong"), ("NRT", "Tokyo"), ("ICN", "Seoul"),
            ("SYD", "Sydney"), ("CPT", "Cape Town"), ("JNB", "Johannesburg"),
        ]
    }.get(region, [])
    
    dates = [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
    
    print(f"🔍 Scanning {region} destinations from AMS...")
    print(f"Running on: {os.uname().nodename}")
    print()
    
    deals = []
    
    for code, name in destinations:
        print(f"Checking {name} ({code})...", end=' ', flush=True)
        
        for date in dates:
            try:
                q = create_query(
                    flights=[FlightQuery(date=date, from_airport="AMS", to_airport=code)],
                    seat='economy', trip='one-way', passengers=Passengers(adults=1),
                    language='en-US', currency='EUR',
                )
                
                results = get_flights(q)
                
                if results:
                    best = min(results, key=lambda x: x.price)
                    deals.append({
                        "code": code, "name": name, "date": date,
                        "price": best.price, "airlines": best.airlines
                    })
                    print(f"€{best.price} ✓")
                    break
                else:
                    print("No flights")
                    
            except Exception as e:
                print(f"Error: {e}")
        
        time.sleep(1)
    
    if not deals:
        print("❌ No deals found")
        return
    
    deals.sort(key=lambda x: x["price"])
    
    # Create results directory
    Path("results").mkdir(exist_ok=True)
    
    # Save JSON
    with open(f"results/deals_{datetime.now().strftime('%Y%m%d')}.json", 'w') as f:
        json.dump(deals, f, indent=2)
    
    # Print results
    print()
    print("💎 Top Deals from Amsterdam:")
    print("-" * 70)
    print(f"{'Price':>8}  {'Code':>5}  {'Destination':<18} {'Date':<12} {'Airlines'}")
    print("-" * 70)
    
    for d in deals[:20]:
        airlines = ', '.join(d['airlines'][:2])
        print(f"€{d['price']:>6}  {d['code']:>5}  {d['name']:<18} {d['date']:<12} {airlines}")
    
    print()
    print(f"✓ Results saved to results/deals_{datetime.now().strftime('%Y%m%d')}.json")

def main():
    import argparse
    p = argparse.ArgumentParser(description="AMS Flights - GitHub Actions Version")
    p.add_argument('command', choices=['scan'])
    p.add_argument('--region', '-r', default='europe')
    p.add_argument('--days', '-d', type=int, default=3)
    
    args = p.parse_args()
    
    if args.command == 'scan':
        scan_deals(args.region, args.days)

if __name__ == '__main__':
    main()
