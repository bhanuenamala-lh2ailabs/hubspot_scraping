# -*- coding: utf-8 -*-
"""Two-stage Apify LinkedIn scrape for the NASSCOM + Founder Search validation set: 278 deals
touched today by Yuktha/Lamiya or currently at Cold Call, plus 64 known Dead/ColdCall/WrongFit
deals used as ground truth (8 overlap) — 334 unique deals, 327 with a usable contact LinkedIn URL.
"""
import os, sys, json, time

HUB = "/Users/bhanu/Desktop/hubspot"
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, ".env"), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
TOKEN = env["apify_token"]
from apify_client import ApifyClient
client = ApifyClient(TOKEN)

OUT_DIR = os.path.join(HUB, "godown", "gujarat_qualify", "apify_out_nasscom")
os.makedirs(OUT_DIR, exist_ok=True)

urls = json.load(open("/tmp/nasscom_profile_urls.json"))
print(f"people URLs: {len(urls)} | est. cost ${len(urls)*4/1000:.2f}")

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
    sys.exit(f"people scrape ended with status {status}")

dataset_id = client.run(run_id).get()["defaultDatasetId"]
people_items = list(client.dataset(dataset_id).iterate_items())
print(f"people scrape returned {len(people_items)} items")
json.dump(people_items, open(os.path.join(OUT_DIR, "people_raw.json"), "w"), ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- extract current-company URLs
def nurl(u): return (u or "").strip().lower().rstrip("/")

comp_urls = []
no_url = 0
for p in people_items:
    cp = (p.get("currentPosition") or [{}])[0]
    exp0 = (p.get("experience") or [{}])[0]
    src = cp if cp.get("companyLinkedinUrl") else exp0
    u = src.get("companyLinkedinUrl")
    if u: comp_urls.append(nurl(u))
    else: no_url += 1

print(f"people with an extractable company URL: {len(people_items)-no_url}/{len(people_items)} "
      f"({100*(len(people_items)-no_url)/len(people_items):.1f}%)")
if no_url / max(len(people_items),1) > 0.20:
    sys.exit("!! more than 20% missing a company URL — stopping per instruction, needs review.")

dedup = list(dict.fromkeys(comp_urls))
print(f"unique company URLs: {len(dedup)}")
json.dump(dedup, open("/tmp/nasscom_company_urls.json", "w"))

# ---------------------------------------------------------------- Stage 2: company scrape
print(f"\ncompany URLs: {len(dedup)} | est. cost ${len(dedup)*3/1000:.2f}")
run2 = client.actor("harvestapi/linkedin-company").call(run_input={"companies": dedup}, wait_secs=0)
run2_id = run2["id"]
print(f"run started: {run2_id}")
while True:
    r = client.run(run2_id).get()
    status2 = r["status"]
    print(f"  status: {status2}", flush=True)
    if status2 in ("SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"):
        break
    time.sleep(15)

if status2 != "SUCCEEDED":
    sys.exit(f"company scrape ended with status {status2}")

dataset_id2 = client.run(run2_id).get()["defaultDatasetId"]
company_items = list(client.dataset(dataset_id2).iterate_items())
print(f"company scrape returned {len(company_items)} items")
json.dump(company_items, open(os.path.join(OUT_DIR, "companies_raw.json"), "w"), ensure_ascii=False, indent=1)
print("\nDONE — both stages complete.")
