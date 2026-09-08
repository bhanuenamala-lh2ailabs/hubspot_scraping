# -*- coding: utf-8 -*-
"""Per-source supply and performance audit.

Two questions per source:
  SUPPLY  — how many rows exist upstream, how many reached HubSpot, how many are net-new
  OUTCOME — of what was pushed, how far did it get

Matching upstream rows to deals uses domain first (exact, reliable) and falls back to a
normalised company name. Name matching is fuzzy by nature, so every count below reports the
method that produced it rather than presenting one blended number.
"""
import os, sys, json, re, collections
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
A = os.path.join(ROOT, "sources", "_audit")

deals = json.load(open(os.path.join(A, "hubspot_deals.json"), encoding="utf-8"))
pct = json.load(open(os.path.join(A, "private_codebase_tracker.json"), encoding="utf-8"))
trx = json.load(open(os.path.join(A, "tracxn.json"), encoding="utf-8"))

# ---------------------------------------------------------------- helpers
STOP = {"pvt", "private", "ltd", "limited", "llp", "inc", "incorporated", "technologies",
        "technology", "tech", "solutions", "solution", "software", "systems", "services",
        "labs", "india", "the", "and", "co", "corp", "company"}
def nname(s):
    s = re.sub(r"[^a-z0-9 ]", " ", (s or "").lower())
    w = [x for x in s.split() if x and x not in STOP]
    return "".join(w)
def ndom(s):
    s = (s or "").lower().strip()
    s = re.sub(r"^https?://", "", s).split("/")[0]
    return s.replace("www.", "")

DEAL_BY_DOM = collections.defaultdict(list)
DEAL_BY_NAME = collections.defaultdict(list)
for d in deals:
    if d["domain"]: DEAL_BY_DOM[ndom(d["domain"])].append(d)
    if d["name"]:   DEAL_BY_NAME[nname(d["name"])].append(d)

# funnel depth, so "performance" is a ladder rather than a yes/no
DEPTH = {"Cold Call": 0, "No Pickup": 1, "Call Attempted": 1, "Call Attempted (retired)": 1,
         "Interested": 2, "GMeet Fixed": 3, "Script Shared": 4, "Script Results Received": 5,
         "Commercial Negotiation": 6, "Deal Contract Signed": 7, "Data Migration Done": 8,
         "Metadata Matched": 9, "Payment Initiation": 10, "Closed/Won": 11,
         "Dead/ColdCall/WrongFit": 0, "Dead/ColdCall/Not Interested": 1,
         "Dead/ColdCall/WrongNumber": 1, "Dead/ColdCall/NoPickup": 1,
         "Dead/Interested/NoShow": 2, "Dead/GMeet/NoShow": 3, "Dead/GMeet/Cancelled": 3,
         "Dead/GMeet/wrong fit": 3, "Dead/GMeet/Privacy Concerns": 3,
         "Dead/ScriptShared/NoShow": 4, "Dead/ResultsReceived/WrongFit-Rejected": 5,
         "Dead/Negotiation/Pricing": 6, "Dead/Negotiation/Contractual": 6}
DEAD = lambda s: s.startswith("Dead/")

def match(rows, dom_key, name_key):
    """-> (matched deals, unmatched rows, how each match was made)"""
    hit, miss, how = [], [], collections.Counter()
    seen = set()
    for r in rows:
        d = ndom(r.get(dom_key, "")) if dom_key else ""
        n = nname(r.get(name_key, "")) if name_key else ""
        got = None
        if d and d in DEAL_BY_DOM: got, why = DEAL_BY_DOM[d], "domain"
        elif n and n in DEAL_BY_NAME: got, why = DEAL_BY_NAME[n], "name"
        if got:
            how[why] += 1
            for g in got:
                if g["id"] not in seen: seen.add(g["id"]); hit.append(g)
        else:
            miss.append(r)
    return hit, miss, how

def outcome(ds, label):
    if not ds:
        print(f"   {label}: no matched deals"); return
    live = [d for d in ds if d["state"] == "live"]
    arch = [d for d in ds if d["state"] == "archived"]
    dep = [DEPTH.get(d["stage"], 0) for d in live]
    reached = lambda n: sum(1 for d in live if DEPTH.get(d["stage"], 0) >= n)
    won = sum(1 for d in live if d["stage"] == "Closed/Won")
    dead = sum(1 for d in live if DEAD(d["stage"]))
    loc = sum(float(d["loc"] or 0) for d in live if d["stage"] == "Closed/Won")
    n = len(live) or 1
    print(f"   {label}")
    print(f"      in HubSpot        {len(ds):>5}   ({len(live)} live, {len(arch)} archived)")
    print(f"      dialled (>=1)     {reached(1):>5}   {100*reached(1)//n:>3}% of live")
    print(f"      interested (>=2)  {reached(2):>5}   {100*reached(2)//n:>3}%")
    print(f"      GMeet (>=3)       {reached(3):>5}   {100*reached(3)//n:>3}%")
    print(f"      script (>=4)      {reached(4):>5}   {100*reached(4)//n:>3}%")
    print(f"      negotiation (>=6) {reached(6):>5}   {100*reached(6)//n:>3}%")
    print(f"      WON               {won:>5}   {100*won/n:.1f}%   {loc/1e6:.2f} Mn LoC")
    print(f"      dead              {dead:>5}   {100*dead//n:>3}%")

print("=" * 84)
print("SUPPLY — what exists upstream vs what reached HubSpot")
print("=" * 84)

# ---------------- 1. Private Codebase Tracker ----------------
print("\n1. PRIVATE CODEBASE TRACKER  (IT services)")
pool = []
for tab in ("Companies (1)", "IT Services Firms", "Sheet6"):
    for r in pct.get(tab, []):
        r["_tab"] = tab; pool.append(r)
# same company appears on more than one tab
uniq, seen = [], set()
for r in pool:
    k = nname(r.get("Company", "")) or ndom(r.get("Website", ""))
    if k and k not in seen: seen.add(k); uniq.append(r)
print(f"   rows across tabs: {len(pool)}  ->  {len(uniq)} unique companies")
hit, miss, how = match(uniq, "Website", "Company")
print(f"   matched to HubSpot: {len(hit)} deals  (matched by {dict(how)})")
print(f"   NET NEW (never pushed): {len(miss)}")
outcome(hit, "performance of what was pushed:")
pct_miss = miss

# ---------------- 2. Tracxn ----------------
print("\n2. TRACXN  (startups)")
rt = trx.get("LH2 Ranked Targets", [])
print(f"   LH2 Ranked Targets: {len(rt)} ranked companies")
print(f"   funded tab {len(trx.get('funded',[]))} | unfunded tab {len(trx.get('unfunded',[]))}")
hit2, miss2, how2 = match(rt, "domain", "company")
print(f"   matched to HubSpot: {len(hit2)} deals  (matched by {dict(how2)})")
print(f"   NET NEW (never pushed): {len(miss2)}")
outcome(hit2, "performance of what was pushed:")

# ---------------- 3/4. by lead_source, which is the honest cut for pushed sources ----
print("\n" + "=" * 84)
print("OUTCOME BY LEAD SOURCE — every deal in HubSpot, live + archived")
print("=" * 84)
by = collections.defaultdict(list)
for d in deals: by[d["lead_source"] or "(none)"].append(d)
for src in sorted(by, key=lambda k: -len(by[k])):
    outcome(by[src], f"{src}  [{len(by[src])} total]")

# ---------------- IT services vs startups ----------------
print("\n" + "=" * 84)
print("IT SERVICES vs STARTUPS")
print("=" * 84)
ITS = {"GoodFirms", "LH2 Pipeline", "LinkedIn Sales Navigator",
       "LinkedIn Lead-Gen Form - Jul 31 2026",
       "LinkedIn Lead-Gen Form - ITservices_targeted_message"}
SUP = {"Deadpool Waves", "LH2 Distress", "Outflo Outreach - India",
       "Outflo Outreach - Indonesia", "OutFlo Replied - Relevance Check",
       "Tracxn Ranked Sheet"}
for label, keys in (("IT SERVICES", ITS), ("STARTUPS", SUP)):
    outcome([d for d in deals if d["lead_source"] in keys], label)

json.dump({"pct_net_new": len(pct_miss), "tracxn_net_new": len(miss2)},
          open(os.path.join(A, "net_new.json"), "w"))
