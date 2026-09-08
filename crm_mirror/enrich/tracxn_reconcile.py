# -*- coding: utf-8 -*-
"""Tracxn sheet reconciled against HubSpot, same partition as the Codebase Tracker.

Tracxn carries a domain on every row, so matching is far firmer here than on the Codebase
Tracker, which had none.

Per instruction: a deal that was pushed, never moved past Cold Call and then archived counts
as NEVER TOUCHED — it is still available supply, just sitting in the recycle bin.
"""
import os, sys, json, re, collections
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
A = os.path.join(ROOT, "sources", "_audit")

deals = {d["id"]: d for d in json.load(open(os.path.join(A, "hubspot_deals.json"), encoding="utf-8"))}
contacts = json.load(open(os.path.join(A, "contacts.json"), encoding="utf-8"))
trx = json.load(open(os.path.join(A, "tracxn.json"), encoding="utf-8"))

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

rank = trx.get("LH2 Ranked Targets", [])
out  = {ndom(r.get("domain", "")) or nn(r.get("company", "")): r
        for r in trx.get("LH2 Ranked Targets Outreach Tracker", [])}

uniq, seen = [], set()
for r in rank:
    k = ndom(r.get("domain", "")) or nn(r.get("company", ""))
    if not k or k in seen: continue
    seen.add(k); r["_k"] = k; uniq.append(r)
print(f"{len(rank)} ranked rows -> {len(uniq)} unique companies\n")

WORKED_REMARK = {"no response","not interested","international number"}
b = collections.Counter(); stages = collections.Counter(); how = collections.Counter()
never_pool = []
arch_untouched = 0

for r in uniq:
    dom, nm = ndom(r.get("domain", "")), nn(r.get("company", ""))
    o = out.get(r["_k"], {})
    li, ph = nli(o.get("linkedin", "")), nph(o.get("phone", ""))
    dids = set()
    if dom and dom in DOM2D: dids = DOM2D[dom]; how["domain"] += 1
    elif nm and nm in NM2D: dids = NM2D[nm]; how["name"] += 1
    elif li and li in LI2D: dids = LI2D[li]; how["linkedin"] += 1
    elif ph and ph in PH2D: dids = PH2D[ph]; how["phone"] += 1
    ds = [deals[d] for d in dids]
    live = [d for d in ds if d["state"] == "live"]
    arch = [d for d in ds if d["state"] == "archived"]
    worked_live = [d for d in live if d["stage"] != "Cold Call"]
    worked_arch = [d for d in arch if d["stage"] != "Cold Call"]
    remark = (r.get("Remarks") or "").strip().lower()
    sheet_worked = any(w in remark for w in WORKED_REMARK) or (remark and len(remark) > 12)

    if worked_live or worked_arch:
        b["worked in HubSpot"] += 1
        for d in (worked_live or worked_arch): stages[d["stage"]] += 1
    elif sheet_worked:
        b["worked in the sheet only"] += 1
    else:
        # never past Cold Call anywhere — archived or not, it is still available
        if arch: arch_untouched += 1
        b["NEVER worked (incl. archived at Cold Call)"] += 1
        r["_out"] = o; never_pool.append(r)

tot = len(uniq)
print("match method:", dict(how))
print("=" * 76)
print("TRACXN — every company in exactly one bucket")
print("=" * 76)
for k in ["worked in HubSpot", "worked in the sheet only",
          "NEVER worked (incl. archived at Cold Call)"]:
    print(f"  {k:<46}{b[k]:>6}   {100*b[k]/tot:>5.1f}%")
print(f"  {'TOTAL':<46}{tot:>6}")
print(f"\n  of the never-worked, pushed then archived at Cold Call: {arch_untouched}")

print("\n" + "=" * 76)
print("STAGE REACHED — the ones that were worked")
print("=" * 76)
for k, v in sorted(stages.items(), key=lambda x: -x[1]): print(f"  {k:<46}{v:>5}")
print(f"  {'TOTAL':<46}{sum(stages.values()):>5}")

print("\n" + "=" * 76)
print(f"NEVER-WORKED POOL — {len(never_pool)} companies, is it usable?")
print("=" * 76)
hp = [r for r in never_pool if nph((r.get("_out") or {}).get("phone", ""))]
hl = [r for r in never_pool if nli((r.get("_out") or {}).get("linkedin", ""))]
he = [r for r in never_pool if (r.get("_out") or {}).get("email", "").strip()]
nn_ = [r for r in never_pool if not nph((r.get("_out") or {}).get("phone", ""))
       and not nli((r.get("_out") or {}).get("linkedin", ""))]
n = len(never_pool) or 1
print(f"  has a phone            {len(hp):>6}   {100*len(hp)/n:>4.0f}%   callable today")
print(f"  has founder LinkedIn   {len(hl):>6}   {100*len(hl)/n:>4.0f}%   enrichable")
print(f"  has an email           {len(he):>6}   {100*len(he)/n:>4.0f}%")
print(f"  has NEITHER phone nor LinkedIn {len(nn_):>6}   {100*len(nn_)/n:>4.0f}%")
print("\n  by company stage:")
for k, v in collections.Counter(r.get("stage") or "(blank)" for r in never_pool).most_common():
    print(f"    {k:<24}{v:>6}")
print("\n  by tier:")
for k, v in collections.Counter(r.get("tier") or "(blank)" for r in never_pool).most_common(6):
    print(f"    {k:<24}{v:>6}")
