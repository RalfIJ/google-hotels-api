"""Find the cheapest weekend for a city trip: hotel prices for the next 8 weekends.

It runs one search per weekend (Friday to Sunday), one after the other, so it takes a few minutes.

    pip install apify-client
    export APIFY_TOKEN=your-token        # Windows: set APIFY_TOKEN=your-token
    python examples/cheapest_weekend.py
"""

import os
from datetime import date, timedelta
from statistics import median

from apify_client import ApifyClient

SEARCH = "hotels in Amsterdam"
WEEKENDS = 8

today = date.today()
first_friday = today + timedelta(days=(4 - today.weekday()) % 7 or 7)

client = ApifyClient(os.environ["APIFY_TOKEN"])
weekends = []
for week in range(WEEKENDS):
    friday = first_friday + timedelta(weeks=week)
    sunday = friday + timedelta(days=2)
    run = client.actor("ralfij/google-hotels-scraper").call(
        run_input={"queries": [SEARCH], "checkInDate": friday.isoformat(), "checkOutDate": sunday.isoformat(), "currency": "EUR"}
    )
    hotels = client.dataset(run.default_dataset_id).iterate_items()
    per_night = [hotel["totalPrice"] / hotel["nights"] for hotel in hotels if hotel["totalPrice"]]
    if not per_night:
        print(f"{friday:%a %d %b}: no prices found")
        continue
    weekends.append((friday, median(per_night)))
    print(f"{friday:%a %d %b} to {sunday:%a %d %b}: median EUR {median(per_night):.0f}, cheapest EUR {min(per_night):.0f} a night")

if weekends:
    friday, price = min(weekends, key=lambda weekend: weekend[1])
    print(f"\nCheapest weekend: {friday:%d %B} (median EUR {price:.0f} a night, taxes included)")
