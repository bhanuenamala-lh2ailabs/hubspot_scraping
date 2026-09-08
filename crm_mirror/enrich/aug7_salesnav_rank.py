# -*- coding: utf-8 -*-
"""Rank the Sales-Navigator IT-services export and stage the best candidates.

Applies the 2026-W31 scraping filter as far as this export allows:

  priority 1 : headcount 250-999   (the band with 74% useful-lead rate vs 55%)
  priority 2 : headcount  50-249
  excluded   : <50 (too small to have a sellable codebase) and >=1000 (too big to sell one)

TWO DEVIATIONS from the standard filter, forced by the export, not chosen:
  * The standard pri-2 rule also requires one of the top-10 cities by funnel depth. This file
    has NO city column (Country/City/State/Website/Revenue are empty for all 1000 rows), so
    that leg cannot be applied. Pri-2 is therefore ranked by headcount instead.
  * Dedup normally keys on DOMAIN. There is no Website column either, so dedup falls back to
    normalised company NAME against HubSpot deals. Weaker: a firm in HubSpot under a
    different trading name will not be caught, so the push step must re-check.

Headcount here is LinkedIn's own number, not a GoodFirms band. That is the stronger signal —
the SignalHire headcount pre-check in enrich_and_push_it.py exists precisely to correct
GoodFirms mislabels (6/8 in validation) — so it is used directly for ranking.

Usage: python aug7_salesnav_rank.py
"""
import os, re, csv, sys, json, time, collections, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
HS = env["hubspot_key"]
SRC = os.path.join(HUB, "aug7", "SalesNavigator_tusharLeads - outflo_leads_salesnav_accounts_2026-08-06.csv")

IT_INDUSTRY = ("it services", "information technology", "computer and network security",
               "it system", "software development")


def hs(path, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    for a in range(6):
        try:
            req = urllib.request.Request("https://api.hubapi.com" + path, data=data, method=method,
                headers={"Authorization": "Bearer " + HS, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                t = r.read().decode(); return r.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and a < 5: time.sleep(2*(a+1)); continue
            return e.code, {}
        except Exception:
            if a == 5: raise
            time.sleep(3*(a+1))


def nm(s):
    """Same normaliser the IT push uses, so both agree on what 'already have it' means."""
    s = (s or "").lower(); s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"\b(pvt|private|ltd|limited|llp|inc|technologies|technology|solutions|software|"
               r"systems|labs|services|consulting|infotech|it|the|india|global|group)\b", " ", s)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


def main():
    rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
    print(f"export rows: {len(rows)}")

    cand = []
    drop = collections.Counter()
    for r in rows:
        name = (r.get("Account Name") or "").strip()
        ind = (r.get("Industry") or "").strip()
        d = re.sub(r"[^\d]", "", r.get("Headcount") or "")
        h = int(d) if d else None
        if not name: drop["no name"] += 1; continue
        if not any(t in ind.lower() for t in IT_INDUSTRY): drop[f"industry: {ind}"] += 1; continue
        if h is None: drop["no headcount"] += 1; continue
        if h < 50: drop["headcount <50"] += 1; continue
        if h >= 1000: drop["headcount >=1000"] += 1; continue
        cand.append({"company": name, "headcount": h, "industry": ind,
                     "li_company_id": (r.get("LinkedIn Company ID") or "").strip(),
                     "li_company_url": (r.get("LinkedIn Company URL") or "").strip(),
                     "summary": (r.get("Summary/Description") or "").strip()[:300],
                     "pri": 1 if 250 <= h < 1000 else 2})
    print("dropped:")
    for k, v in drop.most_common(): print(f"   {v:>5}  {k}")
    print(f"in scope: {len(cand)}  (pri1 {sum(1 for c in cand if c['pri']==1)}, "
          f"pri2 {sum(1 for c in cand if c['pri']==2)})")

    # ---------- dedup against HubSpot deals (name only — no domain in this export) ----------
    after, deals = None, []
    while True:
        b = {"limit": 200, "filterGroups": [], "properties": ["dealname", "lh2_domain", "lead_source"]}
        if after: b["after"] = after
        _, d = hs("/crm/v3/objects/deals/search", "POST", b)
        deals += d.get("results", [])
        after = (d.get("paging") or {}).get("next", {}).get("after")
        if not after: break
    have = {nm(x["properties"].get("dealname")) for x in deals}
    have.discard("")
    print(f"HubSpot deals: {len(deals)} -> {len(have)} distinct normalised names")

    # companies already worked inside the tracker sheet but never created in HubSpot
    try:
        sheet = set(json.load(open(os.path.join(HUB, "crm_mirror", "data", "index",
                                                "sheet_worked_exclude.json"), encoding="utf-8")).get("names", []))
    except Exception:
        sheet = set()

    fresh, dup, sheetdup = [], 0, 0
    for c in cand:
        k = nm(c["company"])
        if k in have: dup += 1; continue
        if k and k in sheet: sheetdup += 1; continue
        c["key"] = k
        fresh.append(c)
    print(f"already in HubSpot: {dup} | already called in tracker sheet: {sheetdup}")
    print(f"NET-NEW in scope: {len(fresh)}  (pri1 {sum(1 for c in fresh if c['pri']==1)}, "
          f"pri2 {sum(1 for c in fresh if c['pri']==2)})")

    # priority band first, then biggest headcount inside the band
    fresh.sort(key=lambda c: (c["pri"], -c["headcount"]))
    for i, c in enumerate(fresh, 1): c["rank"] = i

    p = os.path.join(HERE, "aug7_salesnav_ranked.json")
    json.dump(fresh, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\nwrote {os.path.basename(p)} — full ranked pool of {len(fresh)}")
    print("\ntop 25:")
    for c in fresh[:25]:
        print(f'   {c["rank"]:>4}  pri{c["pri"]}  hc={c["headcount"]:<6}{c["company"][:44]}')
    print(f"\nThe top 200 is the ask, but enrichment will not yield a +91 for every one, so the")
    print(f"push draws down this ranked list until 200 CALLABLE leads exist.")


main()
