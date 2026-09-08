# -*- coding: utf-8 -*-
"""Which input source deserves the next big push? Evidence, not intuition.

Every deal in HubSpot carries a lead_source. This buckets those raw values into the INPUTS we
actually control — a scrape of GoodFirms is a different bet from a scrape of NASSCOM even though
both are "scraped" — and scores each on what happened AFTER the lead landed.

TWO KINDS OF INPUT, kept apart because they behave differently:
  COMPANY-FIRST  we picked a company, then went looking for a human (GoodFirms, NASSCOM,
                 Sales Navigator, Tracxn, Google Maps, Private Codebase Tracker)
  LEAD-FIRST     a person arrived already identified (LinkedIn lead-gen forms, OutFlo replies)

THE METRICS
  moved_off_cold   deals no longer sitting at Cold Call. The user's instruction: a lead still at
                   Cold Call tells us nothing yet, so it is excluded from the numerator.
  depth            average furthest stage reached, on a 0-10 ladder, over ALL deals of that tag.
                   Averaging over all candidates (not just the ones that moved) is deliberate —
                   a source that produces 500 duds and 5 stars is not a good source.
  cherry           deals that reached a genuinely valuable stage (GMeet Done and beyond,
                   Script Shared, Negotiation, Closed Won). This is the number that decides a bet.
  Stage history is read from propertiesWithHistory, so a deal that reached GMeet Fixed and was
  later marked dead still counts as having got there. Current stage alone would undercount every
  source that works its leads properly.

RESERVE = rows sitting in local files that have never been pushed. A source with a big untouched
reserve can be scaled tomorrow; one that is exhausted cannot, however well it performed.

Usage: python3 source_bet_analysis.py
"""
import os, re, sys, json, csv, glob, time, sqlite3, collections, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}
OUT = os.path.join(HERE, "source_bet_analysis.csv")


def hs(u, m="GET", b=None):
    d = json.dumps(b).encode() if b is not None else None
    for a in range(6):
        try:
            r = urllib.request.Request("https://api.hubapi.com" + u, data=d, method=m, headers=H)
            with urllib.request.urlopen(r, timeout=90) as x:
                t = x.read().decode(); return json.loads(t) if t else {}
        except Exception:
            if a == 5: raise
            time.sleep(2 * (a + 1))


# raw lead_source -> (input bucket, company-first or lead-first)
BUCKET = [
    (r"goodfirms",                      "Scrape - GoodFirms",        "company"),
    (r"nasscom",                        "Scrape - NASSCOM",          "company"),
    (r"scraped \( bangladesh",          "Scrape - Bangladesh",       "company"),
    (r"scrap.*it services|scraped \( it", "Scrape - IT services (other)", "company"),
    (r"scrap.*startup",                 "Scrape - Startups",         "company"),
    (r"google maps",                    "Google Maps",               "company"),
    (r"sales navigator",                "LinkedIn Sales Navigator",  "company"),
    (r"tracxn",                         "Tracxn",                    "company"),
    (r"deadpool",                       "Deadpool waves",            "company"),
    (r"distress",                       "LH2 Distress",              "company"),
    (r"private codebase",               "Private Codebase Tracker",  "company"),
    (r"lh2 pipeline",                   "LH2 Pipeline",              "company"),
    (r"linkedin lead-gen|linkedin campaign", "LinkedIn Ads / Lead-Gen form", "lead"),
    (r"linkedin message",               "LinkedIn Message campaign", "lead"),
    (r"outflo.*replied|relevance check", "OutFlo - replied",         "lead"),
    (r"outflo",                         "OutFlo - outreach",         "lead"),
]
LADDER = [
    (r"cold call|call attempted", 1), (r"no pickup", 1),
    (r"wrongnumber|wrong number", 1), (r"not interested", 2),
    (r"wrongfit|wrong fit", 2), (r"interested", 4),
    (r"gmeet fixed", 6), (r"noshow|no show", 5),
    (r"gmeet done|meeting done", 7), (r"script shared", 8),
    (r"script results|results received", 8), (r"evaluation", 9),
    (r"negotiation|commercial", 9), (r"term sheet|loi", 10),
    (r"closed won|won", 10), (r"diligence", 10),
]
CHERRY = re.compile(r"(gmeet done|meeting done|script shared|script results|results received|"
                    r"evaluation|negotiation|commercial|term sheet|loi|closed won|diligence)", re.I)


def bucket_of(src):
    s = (src or "").lower()
    for rx, name, kind in BUCKET:
        if re.search(rx, s): return name, kind
    return ("(untagged)" if not s else f"other: {src[:34]}"), "?"


def rung(label):
    l = (label or "").lower()
    best = 0
    for rx, v in LADDER:
        if re.search(rx, l): best = max(best, v)
    return best


def main():
    pl = hs("/crm/v3/pipelines/deals")
    LAB = {s["id"]: s["label"] for p in pl["results"] for s in p["stages"]}

    after, deals = None, []
    print("pulling every deal + stage history from HubSpot...", flush=True)
    while True:
        b = {"limit": 200, "properties": ["dealname", "lead_source", "dealstage", "source_tab",
                                          "createdate", "hubspot_owner_id"], "filterGroups": []}
        if after: b["after"] = after
        d = hs("/crm/v3/objects/deals/search", "POST", b)
        deals += d.get("results", [])
        after = (d.get("paging") or {}).get("next", {}).get("after")
        if not after: break
    print(f"   {len(deals)} deals", flush=True)

    ids = [x["id"] for x in deals]
    hist = {}
    for i in range(0, len(ids), 50):
        d = hs("/crm/v3/objects/deals/batch/read", "POST",
               {"propertiesWithHistory": ["dealstage"], "properties": ["dealname"],
                "inputs": [{"id": x} for x in ids[i:i+50]]})
        for x in d.get("results", []):
            hist[x["id"]] = [LAB.get(v.get("value"), "?")
                             for v in x.get("propertiesWithHistory", {}).get("dealstage", [])]
        if (i // 50) % 8 == 0: print(f"   history {i}/{len(ids)}", flush=True)

    agg = collections.defaultdict(lambda: {"n": 0, "moved": 0, "depth": [], "cherry": 0,
                                           "cherry_names": [], "kind": "?", "stages": collections.Counter()})
    for x in deals:
        p = x["properties"]
        src = p.get("lead_source") or ""
        tab = (p.get("source_tab") or "").lower()
        name, kind = bucket_of(src)
        # source_tab is the tiebreaker the user asked for: same lead_source, different directory
        if "nasscom" in tab: name, kind = "Scrape - NASSCOM", "company"
        elif "goodfirms" in tab: name, kind = "Scrape - GoodFirms", "company"
        a = agg[name]; a["kind"] = kind; a["n"] += 1
        labs = hist.get(x["id"]) or [LAB.get(p.get("dealstage"), "?")]
        top = max((rung(l) for l in labs), default=0)
        a["depth"].append(top)
        cur = LAB.get(p.get("dealstage"), "?")
        a["stages"][cur] += 1
        if cur.lower() not in ("cold call", "call attempted (retired)"):
            a["moved"] += 1
        if any(CHERRY.search(l or "") for l in labs):
            a["cherry"] += 1
            if len(a["cherry_names"]) < 4: a["cherry_names"].append(p.get("dealname", "")[:26])

    # ---- untouched local reserves ----
    res = {}
    try:
        c = sqlite3.connect(os.path.join(HUB, "lh2-pipeline", "data", "pipeline.sqlite"))
        res["Scrape - GoodFirms"] = c.execute("SELECT COUNT(*) FROM companies WHERE gate_pass=1").fetchone()[0]
    except Exception: pass
    for f, k in (("nasscom_candidates_ALL.csv", "Scrape - NASSCOM"),):
        p = os.path.join(HERE, f)
        if os.path.exists(p): res[k] = sum(1 for _ in open(p, encoding="utf-8-sig")) - 1
    p = os.path.join(HUB, "temporary", "bangladesh_top100.csv")
    try:
        bd = list(csv.DictReader(open(os.path.join(HUB, "temporary",
              "bangladesh_software_companies_qualified - bangladesh_software_companies_qualified.csv"),
              encoding="utf-8-sig")))
        res["Scrape - Bangladesh"] = sum(1 for r in bd if r["relevance_status"].upper() == "RELEVANT")
    except Exception: pass
    for f, k in (("aug7_salesnav_ranked.json", "LinkedIn Sales Navigator"),):
        p = os.path.join(HUB, "crm_mirror", "enrich", f)
        if os.path.exists(p):
            try: res[k] = len(json.load(open(p, encoding="utf-8")))
            except Exception: pass

    rows = []
    for name, a in agg.items():
        n = a["n"]; dep = a["depth"]
        rows.append({
            "input": name, "type": "company-first" if a["kind"] == "company" else
                                   ("lead-first" if a["kind"] == "lead" else "?"),
            "deals_pushed": n,
            "moved_off_cold_call": a["moved"],
            "moved_pct": round(a["moved"] / n * 100) if n else 0,
            "avg_depth_0_10": round(sum(dep) / n, 2) if n else 0,
            "reached_interested_plus": sum(1 for d in dep if d >= 4),
            "interested_pct": round(sum(1 for d in dep if d >= 4) / n * 100) if n else 0,
            "CHERRY_gmeet_done_plus": a["cherry"],
            "cherry_pct": round(a["cherry"] / n * 100, 1) if n else 0,
            "untouched_reserve": res.get(name, ""),
            "examples_that_went_deep": "; ".join(a["cherry_names"]),
        })
    rows.sort(key=lambda r: (-r["cherry_pct"], -r["interested_pct"]))
    cols = list(rows[0].keys())
    with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

    print(f"\nwrote {os.path.basename(OUT)}\n")
    print(f"{'INPUT':<34}{'type':<15}{'n':>6}{'moved%':>8}{'depth':>7}{'int%':>6}{'CHERRY':>8}{'ch%':>7}{'reserve':>9}")
    print("-" * 102)
    for r in rows:
        print(f'{r["input"][:33]:<34}{r["type"]:<15}{r["deals_pushed"]:>6}{r["moved_pct"]:>7}%'
              f'{r["avg_depth_0_10"]:>7}{r["interested_pct"]:>5}%{r["CHERRY_gmeet_done_plus"]:>8}'
              f'{r["cherry_pct"]:>6}%{str(r["untouched_reserve"]):>9}')
    tot = sum(r["deals_pushed"] for r in rows)
    print("-" * 102)
    print(f'{"TOTAL":<34}{"":<15}{tot:>6}')


main()
