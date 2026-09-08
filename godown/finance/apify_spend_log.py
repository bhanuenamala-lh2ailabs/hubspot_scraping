# -*- coding: utf-8 -*-
"""Pulls the FULL Apify actor-run history for this account (real usageTotalUsd per run, as
actually billed — not an estimate) and writes a finance-ready ledger. Re-run anytime to refresh;
it always rebuilds from the account's live run history, so it's inherently idempotent/complete
regardless of which local scripts triggered which run.

Usage: python3 apify_spend_log.py
Writes: apify_spend_log.csv (one row per run) + prints a by-month / by-actor summary.
"""
import os, json, csv, collections, urllib.request

HUB = "/Users/bhanu/Desktop/hubspot"
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, ".env"), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
TOKEN = env["apify_token"]
OUT_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "apify_spend_log.csv")


def api(path):
    req = urllib.request.Request(f"https://api.apify.com/v2{path}",
                                  headers={"Authorization": f"Bearer {TOKEN}"})
    return json.loads(urllib.request.urlopen(req, timeout=45).read().decode())


# pull every run on the account, paginated
runs = []
offset = 0
while True:
    d = api(f"/actor-runs?limit=100&offset={offset}&desc=true")["data"]
    runs += d["items"]
    offset += len(d["items"])
    if offset >= d["total"] or not d["items"]:
        break
print(f"total runs on account: {len(runs)}")

# resolve actor IDs -> readable names
act_ids = sorted(set(r["actId"] for r in runs))
act_names = {}
for aid in act_ids:
    try:
        info = api(f"/acts/{aid}")["data"]
        act_names[aid] = f'{info.get("username","")}/{info.get("name","")}'
    except Exception:
        act_names[aid] = aid

rows = []
for r in runs:
    rows.append({
        "run_id": r["id"],
        "actor": act_names.get(r["actId"], r["actId"]),
        "status": r["status"],
        "started_at": r["startedAt"],
        "finished_at": r.get("finishedAt") or "",
        "usage_usd": r.get("usageTotalUsd") or 0,
    })
rows.sort(key=lambda x: x["started_at"])

with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["run_id", "actor", "status", "started_at", "finished_at", "usage_usd"])
    w.writeheader()
    for r in rows: w.writerow(r)
print(f"wrote {OUT_CSV}")

total = sum(r["usage_usd"] for r in rows)
print(f"\nTOTAL SPEND (all-time, all runs on account): ${total:.4f}")

by_month = collections.defaultdict(float)
by_actor = collections.defaultdict(float)
for r in rows:
    by_month[r["started_at"][:7]] += r["usage_usd"]
    by_actor[r["actor"]] += r["usage_usd"]

print("\n-- by month --")
for m in sorted(by_month):
    print(f"  {m}: ${by_month[m]:.4f}")

print("\n-- by actor --")
for a, v in sorted(by_actor.items(), key=lambda x: -x[1]):
    print(f"  {a:<45} ${v:.4f}")
