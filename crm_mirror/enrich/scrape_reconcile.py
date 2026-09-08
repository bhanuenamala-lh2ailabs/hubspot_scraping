# -*- coding: utf-8 -*-
"""The scraped pool (GoodFirms et al.) reconciled against HubSpot.

Same partition as the Codebase Tracker and Tracxn. A deal pushed, never moved past Cold Call
and then archived counts as NEVER TOUCHED — still available, just in the recycle bin.
"""
import os, sys, json, re, sqlite3, collections
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
HUB = os.path.dirname(ROOT); A = os.path.join(ROOT, "sources", "_audit")
DB = os.path.join(HUB, "lh2-pipeline", "data", "pipeline.sqlite")

deals = {d["id"]: d for d in json.load(open(os.path.join(A, "hubspot_deals.json"), encoding="utf-8"))}
contacts = json.load(open(os.path.join(A, "contacts.json"), encoding="utf-8"))

def ndom(s):
    s = (s or "").lower().strip()
    s = re.sub(r"^https?://", "", s).split("/")[0]
    return s.replace("www.", "")
def nli(u):
    u = (u or "").strip().lower().split("?")[0].rstrip("/")
    if "linkedin.com" not in u: return ""
    u = re.sub(r"^https?://", "", u)
    return re.sub(r"^([a-z]{2}\.)?linkedin\.com", "linkedin.com", u).replace("www.", "")
def nph(p):
    d = re.sub(r"[^0-9]", "", p or "")
    return d[-10:] if len(d) >= 10 else ""
STOP = {"pvt","private","ltd","limited","llp","inc","technologies","technology","tech",
        "solutions","solution","software","systems","services","labs","india","co","corp","company"}
def nn(s):
    s = re.sub(r"\([^)]*\)", " ", s or "")
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return "".join(w for w in s.split() if w and w not in STOP)

DOM2D, NM2D, LI2D, PH2D = (collections.defaultdict(set) for _ in range(4))
for did, d in deals.items():
    if d.get("domain"): DOM2D[ndom(d["domain"])].add(did)
    if d["name"]: NM2D[nn(d["name"])].add(did)
for c in contacts:
    p = c["properties"]
    for did in c.get("deal_ids", []):
        if did not in deals: continue
        if nli(p.get("linkedin_url")): LI2D[nli(p["linkedin_url"])].add(did)
        for ph in (p.get("phone"), p.get("mobilephone")):
            if nph(ph): PH2D[nph(ph)].add(did)

con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
print("scrape sources:")
for r in con.execute("SELECT source, COUNT(*) n FROM raw_listings GROUP BY source ORDER BY n DESC"):
    print(f"   {r['source']:<24}{r['n']:>7}")
comps = [dict(r) for r in con.execute("SELECT * FROM companies")]
people = collections.defaultdict(list)
for r in con.execute("SELECT * FROM people"):
    people[(r["domain"] or "").lower()].append(dict(r))
print(f"\n{len(comps)} companies in the scrape DB | {sum(len(v) for v in people.values())} people enriched\n")

b = collections.Counter(); stages = collections.Counter(); how = collections.Counter()
pool = []; arch_untouched = 0
for c in comps:
    dom, nm = ndom(c.get("domain") or c.get("website")), nn(c.get("company_name"))
    ppl = people.get((c.get("domain") or "").lower(), [])
    dids = set()
    if dom and dom in DOM2D: dids = DOM2D[dom]; how["domain"] += 1
    elif nm and nm in NM2D: dids = NM2D[nm]; how["name"] += 1
    else:
        for p in ppl:
            if nli(p.get("linkedin_url")) in LI2D: dids = LI2D[nli(p["linkedin_url"])]; how["linkedin"] += 1; break
            if nph(p.get("phone")) in PH2D and nph(p.get("phone")): dids = PH2D[nph(p["phone"])]; how["phone"] += 1; break
    ds = [deals[d] for d in dids]
    arch = [d for d in ds if d["state"] == "archived"]
    worked = [d for d in ds if d["stage"] != "Cold Call"]
    if worked:
        b["worked in HubSpot"] += 1
        for d in worked: stages[d["stage"]] += 1
    else:
        if arch: arch_untouched += 1
        b["NEVER worked (incl. archived at Cold Call)"] += 1
        c["_people"] = ppl; pool.append(c)

tot = len(comps)
print("match method:", dict(how))
print("=" * 76)
print("SCRAPED POOL — every company in exactly one bucket")
print("=" * 76)
for k in ["worked in HubSpot", "NEVER worked (incl. archived at Cold Call)"]:
    print(f"  {k:<46}{b[k]:>6}   {100*b[k]/tot:>5.1f}%")
print(f"  {'TOTAL':<46}{tot:>6}")
print(f"\n  of the never-worked, pushed then archived at Cold Call: {arch_untouched}")

print("\n" + "=" * 76)
print("STAGE REACHED — the ones that were worked")
print("=" * 76)
for k, v in sorted(stages.items(), key=lambda x: -x[1]): print(f"  {k:<46}{v:>5}")
print(f"  {'TOTAL':<46}{sum(stages.values()):>5}")

print("\n" + "=" * 76)
print(f"NEVER-WORKED POOL — {len(pool)} companies, is it usable?")
print("=" * 76)
hp = [c for c in pool if any(nph(p.get("phone")) for p in c["_people"])]
hl = [c for c in pool if any(nli(p.get("linkedin_url")) for p in c["_people"])]
nop = [c for c in pool if not c["_people"]]
n = len(pool) or 1
print(f"  has a phone                 {len(hp):>6}   {100*len(hp)/n:>4.0f}%   callable today")
print(f"  has a founder LinkedIn      {len(hl):>6}   {100*len(hl)/n:>4.0f}%   enrichable")
print(f"  no contact person at all    {len(nop):>6}   {100*len(nop)/n:>4.0f}%   needs sourcing first")
print("\n  by size band:")
for k, v in collections.Counter((c.get("size_band") or "(blank)") for c in pool).most_common(8):
    print(f"    {k:<26}{v:>6}")
print("\n  by city (top 8):")
for k, v in collections.Counter((c.get("city") or "(blank)") for c in pool).most_common(8):
    print(f"    {k:<26}{v:>6}")
