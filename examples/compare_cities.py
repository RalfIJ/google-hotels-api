"""Compare hotel prices in several cities for the same dates, with a chart.

    pip install apify-client matplotlib
    export APIFY_TOKEN=your-token        # Windows: set APIFY_TOKEN=your-token
    python examples/compare_cities.py
"""

import os
from statistics import median

import matplotlib.pyplot as plt
from apify_client import ApifyClient

CITIES = ["Amsterdam", "Paris", "Barcelona", "Rome", "Berlin", "Lisbon", "Prague", "London"]
CHECK_IN, CHECK_OUT = "30 days", "32 days"  # relative to today, or dates such as "2026-12-04"

client = ApifyClient(os.environ["APIFY_TOKEN"])
run = client.actor("ralfij/google-hotels-scraper").call(
    run_input={
        "queries": [f"hotels in {city}" for city in CITIES],
        "checkInDate": CHECK_IN,
        "checkOutDate": CHECK_OUT,
        "currency": "EUR",
        "adults": 2,
    }
)

prices = {city: [] for city in CITIES}
cheapest = {}  # the cheapest hotel with a rating of 4.0 or more, per city
for hotel in client.dataset(run.default_dataset_id).iterate_items():
    if not hotel["totalPrice"]:
        continue
    city = hotel["query"].removeprefix("hotels in ")
    per_night = hotel["totalPrice"] / hotel["nights"]  # taxes and fees included
    prices[city].append(per_night)
    if (hotel["rating"] or 0) >= 4.0 and per_night < cheapest.get(city, ("", float("inf")))[1]:
        cheapest[city] = (hotel["name"], per_night)
    dates = f"{hotel['checkInDate']} to {hotel['checkOutDate']}"

cities = sorted((city for city in CITIES if prices[city]), key=lambda city: median(prices[city]))
print(f"Price per night for 2 adults, taxes included (EUR), {dates}\n")
print(f"{'city':<10} {'hotels':>6} {'median':>7}  cheapest hotel rated 4.0+")
for city in cities:
    name, price = cheapest.get(city, ("-", 0))
    print(f"{city:<10} {len(prices[city]):>6} {median(prices[city]):>7.0f}  {name} ({price:.0f})")

medians = [median(prices[city]) for city in cities]
fig, ax = plt.subplots(figsize=(9, 4.5))
bars = ax.barh(cities, medians, color="#4C72B0")
ax.bar_label(bars, labels=[f"EUR {value:.0f}" for value in medians], padding=4)
ax.set_xlabel("Median price per night for 2 adults, taxes and fees included (EUR)")
ax.set_title(f"Hotel prices on Google Hotels, {dates}\nFirst 20 hotels Google shows per city")
ax.set_xlim(0, max(medians) * 1.15)
fig.tight_layout()
fig.savefig("city_prices.png", dpi=150)
print("\nSaved city_prices.png")
