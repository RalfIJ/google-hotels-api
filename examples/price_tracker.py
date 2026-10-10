"""Track hotel prices for one stay over time and see when they drop.

Run it once a day with cron, Windows Task Scheduler or a scheduled GitHub Action. Every run adds
the current prices to price_history.csv and lists the hotels that got at least 10% cheaper since
the previous run.

    pip install apify-client
    export APIFY_TOKEN=your-token        # Windows: set APIFY_TOKEN=your-token
    python examples/price_tracker.py
"""

import csv
import os
from datetime import datetime, timezone
from pathlib import Path

from apify_client import ApifyClient

SEARCH = "hotels in Barcelona"
CHECK_IN, CHECK_OUT = "2027-03-12", "2027-03-14"  # the stay you want to book; keep these fixed
DROP = 0.10  # report drops of 10% or more
HISTORY = Path("price_history.csv")

previous = {}  # the last known price per night for each hotel
if HISTORY.exists():
    with HISTORY.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            previous[row["hotel_id"]] = float(row["price_per_night"])

client = ApifyClient(os.environ["APIFY_TOKEN"])
run = client.actor("ralfij/google-hotels-scraper").call(
    run_input={"queries": [SEARCH], "checkInDate": CHECK_IN, "checkOutDate": CHECK_OUT, "currency": "EUR"}
)
hotels = [hotel for hotel in client.dataset(run.default_dataset_id).iterate_items() if hotel["totalPrice"]]

checked_at = datetime.now(timezone.utc).isoformat(timespec="minutes")
drops = []
new_file = not HISTORY.exists()
with HISTORY.open("a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    if new_file:
        writer.writerow(["checked_at", "hotel_id", "name", "price_per_night", "currency"])
    for hotel in hotels:
        per_night = round(hotel["totalPrice"] / hotel["nights"], 2)  # taxes and fees included
        writer.writerow([checked_at, hotel["hotelId"], hotel["name"], per_night, hotel["currency"]])
        before = previous.get(hotel["hotelId"])
        if before and per_night <= before * (1 - DROP):
            drops.append(f"{hotel['name']}: {before:.0f} -> {per_night:.0f} {hotel['currency']} a night ({per_night / before - 1:.0%})")

print(f"Saved {len(hotels)} prices to {HISTORY}")
if not previous:
    print("First run, so there is nothing to compare yet.")
elif drops:
    print(f"\n{len(drops)} hotels got cheaper:")
    print("\n".join(drops))
else:
    print("No price drops of 10% or more since the last run.")
