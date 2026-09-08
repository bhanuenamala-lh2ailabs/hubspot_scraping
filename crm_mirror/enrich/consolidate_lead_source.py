# -*- coding: utf-8 -*-
"""Consolidate the deals lead_source dropdown — 2026-08-14, per instruction.

The property carries 28 options; the live portal uses 9. The other 19 — including six
LinkedIn variants minted one-per-campaign — have ZERO deals on them (verified against the
full deal export this afternoon), so removing them is pure schema cleanup: no deal is
remapped, no reporting series changes. "Combine the LinkedIn ones into one" is satisfied by
deletion because the only LinkedIn option with any usage is the canonical
"Linkedin Campaign ( IT Services )" (355 deals), which stays.

Removed options are logged to lead_source_cleanup_log.json first, so the exact list can be
restored verbatim if anyone misses one.

Usage: python3 consolidate_lead_source.py [--apply]
"""
import os, sys, json, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}
APPLY = "--apply" in sys.argv

# The 9 values that carry deals today (860/355/219/177/175/50/29/22/9 respectively).
KEEP = ["Scraping Algo ( IT services )", "Linkedin Campaign ( IT Services )",
        "NASSCOM ( IT Services )", "Outflo Outreach ( Startups )", "Tracxn Sheet ( Startups )",
        "Scraping Algo ( Startups )", "Romania ( IT Services )",
        "Private Codebase Tracker sheet ( IT services )", "Scraped ( IT Services )"]


def main():
    r = urllib.request.Request("https://api.hubapi.com/crm/v3/properties/deals/lead_source", headers=H)
    p = json.loads(urllib.request.urlopen(r, timeout=30).read().decode())
    old = p["options"]
    removed = [o["value"] for o in old if o["value"] not in KEEP]
    missing = [k for k in KEEP if k not in {o["value"] for o in old}]
    if missing: sys.exit(f"KEEP value not in property: {missing}")
    print(f"options now: {len(old)} | keeping {len(KEEP)} | removing {len(removed)}:")
    for v in removed: print("   -", v)
    if not APPLY:
        print("\nDRY RUN — property untouched. Re-run with --apply."); return
    json.dump({"removed": removed, "kept": KEEP, "when": "2026-08-14"},
              open(os.path.join(HERE, "lead_source_cleanup_log.json"), "w"), indent=1)
    new = [{"label": o["label"], "value": o["value"], "displayOrder": i, "hidden": False}
           for i, o in enumerate([o for o in old if o["value"] in KEEP])]
    rq = urllib.request.Request("https://api.hubapi.com/crm/v3/properties/deals/lead_source",
                                data=json.dumps({"options": new}).encode(), method="PATCH", headers=H)
    res = json.loads(urllib.request.urlopen(rq, timeout=30).read().decode())
    print(f"\nAPPLIED: property now has {len(res.get('options', []))} options; log written.")


main()
