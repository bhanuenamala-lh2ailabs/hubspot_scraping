# -*- coding: utf-8 -*-
"""Two-stage Apify LinkedIn scrape, scoped to ONLY the Gujarat Sales Nav people who were
actually pushed to HubSpot (180 of 862 net-new rows) — a pilot to see whether LinkedIn
company data can catch wrong-ICP-fits before they ever reach HubSpot.

Stage 1: harvestapi/linkedin-profile-scraper on the 180 profile URLs.
Stage 2: extract each profile's CURRENT-role company LinkedIn URL from experience data,
         dedupe, run harvestapi/linkedin-company on the deduped list.
"""
import os, sys, csv, json, time, re

HUB = "/Users/bhanu/Desktop/hubspot"
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, ".env"), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
TOKEN = env["apify_token"]

from apify_client import ApifyClient
client = ApifyClient(TOKEN)

OUT_DIR = os.path.join(HUB, "godown", "gujarat_qualify", "apify_out")
os.makedirs(OUT_DIR, exist_ok=True)

rows = json.load(open("/tmp/gujarat_pushed_subset.json"))
print(f"input: {len(rows)} people (Gujarat Sales Nav rows that were actually pushed to HubSpot)")

urls = [r["LinkedIn URL"].strip() for r in rows if r.get("LinkedIn URL")]
urls = list(dict.fromkeys(urls))  # exact-string dedup, preserve order
print(f"unique profile URLs: {len(urls)}")

if len(urls) > 2000:
    sys.exit(f"!! {len(urls)} rows exceeds the 2,000 pause threshold — confirm before proceeding.")

# ---------------------------------------------------------------- Stage 1: people scrape
print("\n=== Stage 1: people scrape (harvestapi/linkedin-profile-scraper) ===")
print(f"est. cost: ${len(urls) * 4 / 1000:.2f} (Profile details, no email — $4/1k)")
run = client.actor("harvestapi/linkedin-profile-scraper").call(run_input={
    "profileScraperMode": "Profile details no email ($4 per 1k)",
    "queries": urls,
}, wait_secs=0)
run_id = run["id"]
print(f"run started: {run_id}")

while True:
    r = client.run(run_id).get()
    status = r["status"]
    print(f"  status: {status}", flush=True)
    if status in ("SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"):
        break
    time.sleep(15)

if status != "SUCCEEDED":
    sys.exit(f"!! people scrape run ended with status {status} — stopping.")

dataset_id = client.run(run_id).get()["defaultDatasetId"]
people_items = list(client.dataset(dataset_id).iterate_items())
print(f"people scrape returned {len(people_items)} items")

json.dump(people_items, open(os.path.join(OUT_DIR, "people_raw.json"), "w"), ensure_ascii=False, indent=1)

# figure out which input URL each item corresponds to, and what failed
scraped_urls = set()
for it in people_items:
    u = (it.get("linkedinUrl") or it.get("profileUrl") or it.get("url") or "").strip().lower().rstrip("/")
    if u: scraped_urls.add(u)
failed = [u for u in urls if u.strip().lower().rstrip("/") not in scraped_urls]
print(f"people succeeded: {len(people_items)} | failed/missing: {len(failed)}")

# ---------------------------------------------------------------- Stage 2: extract current-company URL
print("\n=== Stage 2: extracting current-company LinkedIn URLs from experience data ===")
if people_items:
    sample = people_items[0]
    print("sample top-level keys:", list(sample.keys()))
    exp_key = next((k for k in sample.keys() if "experien" in k.lower()), None)
    print("experience field name:", exp_key)
    if exp_key and sample.get(exp_key):
        print("sample experience[0] keys:", list(sample[exp_key][0].keys()))

json.dump(people_items[:2], open(os.path.join(OUT_DIR, "people_sample_for_inspection.json"), "w"),
          ensure_ascii=False, indent=1)
print(f"\nwrote inspection sample -> {os.path.join(OUT_DIR, 'people_sample_for_inspection.json')}")
print("STOPPING HERE for manual inspection of the real field structure before Stage 2 extraction logic is finalized.")
