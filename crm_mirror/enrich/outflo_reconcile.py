# -*- coding: utf-8 -*-
"""OutFlo reconciled against HubSpot, same partition as the other sources.

OutFlo has its own funnel BEFORE HubSpot: a lead is sequenced, a connection request goes
out, they connect, they reply. Only engaged leads were ever meant to be pushed. So "never
worked" here splits two ways — never worked by US in HubSpot, versus never even contacted
by the tool.
"""
import os, sys, json, re, collections
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
A = os.path.join(ROOT, "sources", "_audit")

deals = {d["id"]: d for d in json.load(open(os.path.join(A, "hubspot_deals.json"), encoding="utf-8"))}
contacts = json.load(open(os.path.join(A, "contacts.json"), encoding="utf-8"))
leads = json.load(open(os.path.join(ROOT, "outflo", "leads.json"), encoding="utf-8"))

def nli(u):
    u = (u or "").strip().lower().split("?")[0].rstrip("/")
    if "linkedin.com" not in u: return ""
    u = re.sub(r"^https?://", "", u)
    return re.sub(r"^([a-z]{2}\.)?linkedin\.com", "linkedin.com", u).replace("www.", "")
STOP = {"pvt","private","ltd","limited","llp","inc","technologies","technology","tech",
        "solutions","solution","software","systems","services","labs","india","co","corp","company"}
def nn(s):
    s = re.sub(r"\([^)]*\)", " ", s or "")
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return "".join(w for w in s.split() if w and w not in STOP)

LI2D, NM2D = collections.defaultdict(set), collections.defaultdict(set)
for did, d in deals.items():
    if d.get("linkedin"): LI2D[nli(d["linkedin"])].add(did)
    if d["name"]: NM2D[nn(d["name"])].add(did)
for c in contacts:
    p = c["properties"]
    for did in c.get("deal_ids", []):
        if did in deals and nli(p.get("linkedin_url")): LI2D[nli(p["linkedin_url"])].add(did)

# one row per person (the same profile can appear in several campaigns)
uniq, seen = [], set()
for l in leads:
    k = nli(l.get("linkedin")) or (nn(l.get("company", "")) + "|" + (l.get("name") or "").lower())
    if not k or k in seen: continue
    seen.add(k); l["_k"] = k; uniq.append(l)
print(f"{len(leads):,} lead rows -> {len(uniq):,} unique people\n")

b = collections.Counter(); stages = collections.Counter(); how = collections.Counter()
pool = collections.Counter(); engaged_not_pushed = []
for l in uniq:
    li, nm = nli(l.get("linkedin")), nn(l.get("company", ""))
    dids = set()
    if li and li in LI2D: dids = LI2D[li]; how["linkedin"] += 1
    elif nm and nm in NM2D: dids = NM2D[nm]; how["name"] += 1
    ds = [deals[d] for d in dids]
    worked = [d for d in ds if d["stage"] != "Cold Call"]
    conn = (l.get("conn") or "").strip()
    rep  = (l.get("reply") or "").strip()
    engaged = rep == "Replied" or conn in ("Connected", "Previously Connected")

    if worked:
        b["worked in HubSpot"] += 1
        for d in worked: stages[d["stage"]] += 1
    elif ds:
        b["in HubSpot, never worked"] += 1
    else:
        b["never reached HubSpot"] += 1
        if engaged: engaged_not_pushed.append(l)
        # what stage of OutFlo's own funnel are they at
        if rep == "Replied": pool["replied — engaged, not pushed"] += 1
        elif conn in ("Connected", "Previously Connected"): pool["connected — engaged, not pushed"] += 1
        elif conn in ("Request Sent", "Previously Request Sent"): pool["request sent, no answer"] += 1
        elif conn == "Checking": pool["queued in OutFlo, not yet actioned"] += 1
        elif conn == "Failed": pool["request failed"] += 1
        else: pool["never contacted by OutFlo"] += 1

tot = len(uniq)
print("match method:", dict(how))
print("=" * 76)
print("OUTFLO — every unique person in exactly one bucket")
print("=" * 76)
for k in ["worked in HubSpot", "in HubSpot, never worked", "never reached HubSpot"]:
    print(f"  {k:<44}{b[k]:>7}   {100*b[k]/tot:>5.1f}%")
print(f"  {'TOTAL':<44}{tot:>7}")

print("\n" + "=" * 76)
print("STAGE REACHED — the ones that were worked")
print("=" * 76)
for k, v in sorted(stages.items(), key=lambda x: -x[1]): print(f"  {k:<46}{v:>5}")
print(f"  {'TOTAL':<46}{sum(stages.values()):>5}")

print("\n" + "=" * 76)
print("THE NEVER-PUSHED POOL — where they sit in OutFlo's own funnel")
print("=" * 76)
for k, v in pool.most_common(): print(f"  {k:<44}{v:>7}")
print(f"\n  ENGAGED but never pushed to HubSpot: {len(engaged_not_pushed)}")
print("  ^ these are the ones worth pushing — a human already responded")
print("\n  engaged-not-pushed by bucket:",
      dict(collections.Counter(l.get("bucket") for l in engaged_not_pushed)))
print("  engaged-not-pushed by campaign:")
for k, v in collections.Counter((l.get("campaign") or "?")[:44] for l in engaged_not_pushed).most_common(8):
    print(f"    {k:<46}{v:>5}")
json.dump(engaged_not_pushed, open(os.path.join(A, "outflo_engaged_not_pushed.json"), "w",
                                   encoding="utf-8"), ensure_ascii=False, indent=1)
