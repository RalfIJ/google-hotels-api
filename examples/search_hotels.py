"""Hotel prices for one city and date range from Google Hotels, cheapest first.

    pip install apify-client
    export APIFY_TOKEN=your-token        # Windows: set APIFY_TOKEN=your-token
    python examples/search_hotels.py
"""

import csv
import os

from apify_client import ApifyClient

SEARCH = "hotels in Lisbon"
CHECK_IN, CHECK_OUT = "30 days", "32 days"  # relative to today, or dates such as "2026-12-04"

client = ApifyClient(os.environ["APIFY_TOKEN"])
run = client.actor("ralfij/google-hotels-scraper").call(
    run_input={"queries": [SEARCH], "checkInDate": CHECK_IN, "checkOutDate": CHECK_OUT, "currency": "EUR", "adults": 2}
)
hotels = [hotel for hotel in client.dataset(run.default_dataset_id).iterate_items() if hotel["totalPrice"]]
hotels.sort(key=lambda hotel: hotel["totalPrice"])

print(f"{'hotel':<42} {'stars':>5} {'rating':>6}  {'a night, all-in':>15}")
for hotel in hotels:
    per_night = hotel["totalPrice"] / hotel["nights"]  # taxes and fees included
    print(f"{hotel['name'][:42]:<42} {hotel['hotelClass'] or '-':>5} {hotel['rating'] or '-':>6}  {per_night:>11.0f} {hotel['currency']}")

with open("hotels.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "name", "stars", "rating", "reviews", "price_per_night", "total_price", "currency", "deal",
        "check_in", "check_out", "latitude", "longitude", "google_hotels_url",
    ])
    for hotel in hotels:
        writer.writerow([
            hotel["name"], hotel["hotelClass"], hotel["rating"], hotel["reviewCount"],
            round(hotel["totalPrice"] / hotel["nights"], 2), hotel["totalPrice"], hotel["currency"], hotel["dealText"],
            hotel["checkInDate"], hotel["checkOutDate"], hotel["latitude"], hotel["longitude"], hotel["googleHotelsUrl"],
        ])
print(f"\nSaved {len(hotels)} hotels to hotels.csv")
