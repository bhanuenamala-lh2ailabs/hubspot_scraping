# -*- coding: utf-8 -*-
"""Normalise `lead_source` values, then convert the property from free text to a dropdown.

Why: as free text it silently fragmented. 'Outflo Outreach - India' (hyphen, 174 deals) and
'Outflo Outreach – India' (EN DASH, 67 deals) render identically on screen but are two
different values, so any filter on one silently misses the other. A dropdown makes that
impossible and removes the copy-paste-the-exact-string problem when filtering.

Order matters: normalise FIRST, convert SECOND. Converting while variant spellings still
exist would either strand those deals on values outside the option list or force a junk
option per typo.

A snapshot of every deal's current value is written before anything changes, so the whole
thing is reversible.

Usage: python lead_source_to_dropdown.py [--dry-run]
"""
import os, sys, json, time, datetime, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
SNAP = os.path.join(HUB, "crm_mirror", "holding",
                    f"lead_source_snapshot_{datetime.date.today().isoformat()}.json")
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
HS = env["hubspot_key"]

# left -> right. En-dash variants collapse into the hyphen form. The deadpool value drops its
# date: a dropdown must not grow a new option every batch, and createdate already has the date.
REMAP = {
    "Outflo Outreach – India": "Outflo Outreach - India",
    "Outflo Outreach – Indonesia": "Outflo Outreach - Indonesia",
    "Deadpool Waves 2026-08-04": "Deadpool Waves",
}
OPTIONS = [
    "GoodFirms",
    "LH2 Pipeline",
    "LH2 Distress",
    "Deadpool Waves",
    "Outflo Outreach - India",
    "Outflo Outreach - Indonesia",
    "LinkedIn Sales Navigator",
    "LinkedIn Lead-Gen Form - ITservices_targeted_message",
    "Tracxn Ranked Sheet",          # used by past pushes; kept selectable
    "Private Codebase Tracker",
    "Google Maps",                  # the tier-2/3 scrape, for when it lands
]


def hs(path, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    for a in range(5):
        try:
            req = urllib.request.Request("https://api.hubapi.com" + path, data=data, method=method,
                headers={"Authorization": "Bearer " + HS, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=45) as r:
                t = r.read().decode(); return r.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504) and a < 4: time.sleep(2 * (a + 1)); continue
            return e.code, {"raw": e.read().decode()[:400]}
        except Exception:
            if a == 4: raise
            time.sleep(2)


def all_deals():
    after, out = None, []
    while True:
        b = {"limit": 200, "filterGroups": [], "properties": ["dealname", "lead_source", "pipeline"]}
        if after: b["after"] = after
        _, d = hs("/crm/v3/objects/deals/search", "POST", b)
        out += d.get("results", [])
        after = d.get("paging", {}).get("next", {}).get("after")
        if not after: break
    return out


def main():
    dry = "--dry-run" in sys.argv
    deals = all_deals()
    snap = [{"id": x["id"], "dealname": x["properties"].get("dealname"),
             "lead_source": x["properties"].get("lead_source")} for x in deals]
    os.makedirs(os.path.dirname(SNAP), exist_ok=True)
    json.dump(snap, open(SNAP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(deals)} deals | snapshot -> {SNAP}\n")

    todo = [x for x in deals if (x["properties"].get("lead_source") or "") in REMAP]
    print("STEP 1 — normalise variant spellings")
    for old, new in REMAP.items():
        n = sum(1 for x in todo if x["properties"]["lead_source"] == old)
        print(f"   {n:>4}  {old!r}  ->  {new!r}")
    if not dry:
        ok = 0
        for i in range(0, len(todo), 100):
            chunk = todo[i:i + 100]
            st, d = hs("/crm/v3/objects/deals/batch/update", "POST", {"inputs": [
                {"id": x["id"], "properties": {"lead_source": REMAP[x["properties"]["lead_source"]]}}
                for x in chunk]})
            if st in (200, 202): ok += len(chunk)
            else: print(f"   batch failed {st}: {d}")
            time.sleep(0.3)
        print(f"   updated {ok}/{len(todo)}")

    print("\nSTEP 2 — convert lead_source to a dropdown")
    st, cur = hs("/crm/v3/properties/deals/lead_source")
    print(f"   before: type={cur.get('type')} fieldType={cur.get('fieldType')} "
          f"options={len(cur.get('options') or [])}")
    if dry:
        print("   would set: type=enumeration fieldType=select with "
              f"{len(OPTIONS)} options"); return
    body = {"type": "enumeration", "fieldType": "select",
            "options": [{"label": o, "value": o, "displayOrder": i, "hidden": False}
                        for i, o in enumerate(OPTIONS)]}
    st, d = hs("/crm/v3/properties/deals/lead_source", "PATCH", body)
    print(f"   PATCH -> HTTP {st}")
    if st != 200:
        print("   FAILED:", json.dumps(d)[:400])
        print("   (values are untouched; snapshot is on disk)"); return
    st, now = hs("/crm/v3/properties/deals/lead_source")
    print(f"   after : type={now.get('type')} fieldType={now.get('fieldType')} "
          f"options={len(now.get('options') or [])}")
    for o in now.get("options", []): print(f"      - {o['label']}")

    # prove no deal lost its value
    after = all_deals()
    import collections
    c = collections.Counter(x["properties"].get("lead_source") or "(empty)" for x in after)
    print("\nVALUES AFTER CONVERSION:")
    for k, v in c.most_common(): print(f"   {v:>4}  {k}")
    lost = sum(1 for a_, b_ in zip(sorted(snap, key=lambda r: r["id"]),
                                   sorted([{"id": x["id"], "lead_source": x["properties"].get("lead_source")}
                                           for x in after], key=lambda r: r["id"]))
               if (a_["lead_source"] or "") and not (b_["lead_source"] or ""))
    print(f"\ndeals that LOST a value: {lost}")


if __name__ == "__main__":
    main()
