# -*- coding: utf-8 -*-
"""Tier-1 aggregator pull, Bengaluru-scoped: 10times (via query+country, since the actor's
city-dropdown IDs aren't documented for API use) + Eventbrite (via its real India--Bengaluru
technology category URL, safer than guessing the actor's city-slug format).
"""
import os, json, time

HUB = "/Users/bhanu/Desktop/hubspot"
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, ".env"), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
TOKEN = env["apify_token"]
from apify_client import ApifyClient
client = ApifyClient(TOKEN)

OUT = os.path.dirname(os.path.abspath(__file__))


def run_actor(actor_id, run_input, label):
    print(f"\n=== {label} ({actor_id}) ===")
    run = client.actor(actor_id).call(run_input=run_input, wait_secs=0)
    run_id = run["id"]
    while True:
        r = client.run(run_id).get()
        status = r["status"]
        if status in ("SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"):
            break
        time.sleep(10)
    print(f"  status: {status}")
    if status != "SUCCEEDED":
        print(f"  !! {label} failed, continuing with other sources")
        return []
    items = list(client.dataset(r["defaultDatasetId"]).iterate_items())
    print(f"  items: {len(items)}")
    return items


tentimes = run_actor("zen-studio/10times-events-scraper", {
    "query": "Bangalore",
    "country": "IN",
    "category": "156",  # IT & Technology
    "maxItems": 100,
}, "10times (Bengaluru, IT & Technology)")
json.dump(tentimes, open(os.path.join(OUT, "raw_10times.json"), "w"), indent=1, ensure_ascii=False)

eventbrite = run_actor("parseforge/eventbrite-scraper", {
    "city": "india--bengaluru",
    "category": "technology",
    "maxItems": 60,
}, "Eventbrite (Bengaluru technology)")
json.dump(eventbrite, open(os.path.join(OUT, "raw_eventbrite.json"), "w"), indent=1, ensure_ascii=False)

print(f"\nwrote raw_10times.json ({len(tentimes)}) + raw_eventbrite.json ({len(eventbrite)})")
