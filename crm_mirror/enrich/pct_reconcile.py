# -*- coding: utf-8 -*-
"""Reconcile the Private Codebase Tracker against HubSpot, company by company.

Company name alone is a poor key — the sheet writes "Antino (Antino Labs)" where HubSpot
holds "Antino". Founder LinkedIn is on 1,593 of 1,684 rows and is exact, so match on that
first, then phone, then name.

Partitions every unique company into exactly one bucket, so the numbers add up.
"""
import os, sys, json, re, time, collections, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
HUB = os.path.dirname(ROOT); A = os.path.join(ROOT, "sources", "_audit")
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}

def hs(path, method="GET", body=None):
    url = "https://api.hubapi.com" + path
    data = json.dumps(body).encode() if body is not None else None
    for a in range(5):
        try:
            req = urllib.request.Request(url, data=data, method=method, headers=H)
            with urllib.request.urlopen(req, timeout=45) as r:
                t = r.read().decode(); return r.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504) and a < 4: time.sleep(2*(a+1)); continue
            return e.code, {"raw": e.read().decode()[:200]}
        except Exception:
            if a == 4: raise
            time.sleep(2)

CACHE = os.path.join(A, "contacts.json")
if os.path.exists(CACHE):
    contacts = json.load(open(CACHE, encoding="utf-8"))
else:
    contacts, after = [], None
    while True:
        b = {"limit": 100, "properties": ["linkedin_url", "phone", "mobilephone",
                                          "email", "firstname", "lastname", "company"]}
        if after: b["after"] = after
        s, d = hs("/crm/v3/objects/contacts/search", "POST", b)
        contacts += d.get("results", [])
        after = (d.get("paging") or {}).get("next", {}).get("after")
        if not after: break
        time.sleep(0.1)
    # Associations in BATCHES of 100. One call per contact is thousands of round trips;
    # the batch endpoint does the same work in a fraction of the calls.
    idx = {c["id"]: c for c in contacts}
    for c in contacts: c["deal_ids"] = []
    ids = list(idx)
    for i in range(0, len(ids), 100):
        chunk = ids[i:i+100]
        s, a = hs("/crm/v4/associations/contacts/deals/batch/read", "POST",
                  {"inputs": [{"id": x} for x in chunk]})
        for res in (a.get("results") or []):
            cid = str(res.get("from", {}).get("id"))
            if cid in idx:
                idx[cid]["deal_ids"] = [str(t["toObjectId"]) for t in res.get("to", [])]
        print(f"  associations {min(i+100,len(ids))}/{len(ids)}", file=sys.stderr)
        time.sleep(0.08)
    json.dump(contacts, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
print(f"{len(contacts)} contacts")

deals = {d["id"]: d for d in json.load(open(os.path.join(A, "hubspot_deals.json"), encoding="utf-8"))}
pct = json.load(open(os.path.join(A, "private_codebase_tracker.json"), encoding="utf-8"))

# ---------------------------------------------------------------- keys
def nli(u):
    u = (u or "").strip().lower().split("?")[0].rstrip("/")
    if not u.startswith("http"): return ""
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^([a-z]{2}\.)?linkedin\.com", "linkedin.com", u)
    return u.replace("www.", "")
def nph(p):
    d = re.sub(r"[^0-9]", "", (p or ""))
    return d[-10:] if len(d) >= 10 else ""
STOP = {"pvt","private","ltd","limited","llp","inc","technologies","technology","tech",
        "solutions","solution","software","systems","services","labs","india","co","corp","company"}
def nname(s):
    s = re.sub(r"\([^)]*\)", " ", s or "")
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return "".join(w for w in s.split() if w and w not in STOP)

LI2D, PH2D, NM2D = collections.defaultdict(set), collections.defaultdict(set), collections.defaultdict(set)
for c in contacts:
    p = c["properties"]
    for did in c.get("deal_ids", []):
        if did not in deals: continue
        if nli(p.get("linkedin_url")): LI2D[nli(p["linkedin_url"])].add(did)
        for ph in (p.get("phone"), p.get("mobilephone")):
            if nph(ph): PH2D[nph(ph)].add(did)
for did, d in deals.items():
    if d["name"]: NM2D[nname(d["name"])].add(did)
    if d.get("linkedin"): LI2D[nli(d["linkedin"])].add(did)

# ---------------------------------------------------------------- sheet universe
rows = []
for tab in ("Companies (1)", "IT Services Firms", "Sheet6"):
    for r in pct.get(tab, []):
        r["_tab"] = tab; rows.append(r)
uniq, seen = [], {}
for r in rows:
    k = nname(r.get("Company", "")) or nli(r.get("Founder LinkedIn (verified)", ""))
    if not k: continue
    if k in seen:                       # keep the row that carries a worked Status
        if (r.get("Status") or "").strip(): seen[k].update(r)
        continue
    seen[k] = r; uniq.append(r)
print(f"{len(rows)} sheet rows -> {len(uniq)} unique companies\n")

WORKED_STATUS = {"reached out","not interested","call back","wrong/no number",
                 "meeting set","sent email"}
buckets = collections.Counter(); detail = collections.defaultdict(list); how = collections.Counter()

for r in uniq:
    li, ph, nm = (nli(r.get("Founder LinkedIn (verified)")), nph(r.get("Contact Number")),
                  nname(r.get("Company", "")))
    dids = set()
    if li and li in LI2D: dids |= LI2D[li]; how["linkedin"] += 1
    elif ph and ph in PH2D: dids |= PH2D[ph]; how["phone"] += 1
    elif nm and nm in NM2D: dids |= NM2D[nm]; how["name"] += 1
    ds = [deals[d] for d in dids]
    live = [d for d in ds if d["state"] == "live"]
    sheet_worked = (r.get("Status") or "").strip().lower() in WORKED_STATUS

    if not ds:
        b = "never reached HubSpot"
    elif not live:
        b = "reached HubSpot, then archived"
    elif any(d["stage"] != "Cold Call" for d in live):
        b = "in HubSpot and WORKED"
    else:
        b = "in HubSpot, sitting at Cold Call, never worked"
    buckets[b] += 1
    detail[b].append((r.get("Company", "")[:34], r.get("_tab"), r.get("Status", ""), sheet_worked))

print("match method:", dict(how))
print()
print("=" * 74)
print("PRIVATE CODEBASE TRACKER — every company placed in exactly one bucket")
print("=" * 74)
ORDER = ["in HubSpot and WORKED", "in HubSpot, sitting at Cold Call, never worked",
         "reached HubSpot, then archived", "never reached HubSpot"]
tot = sum(buckets.values())
for b in ORDER:
    n = buckets[b]
    print(f"  {b:<48}{n:>6}   {100*n/tot:>5.1f}%")
print(f"  {'TOTAL unique companies':<48}{tot:>6}")

print()
print("Of those that NEVER reached HubSpot, how many were nonetheless worked in the SHEET?")
sw = sum(1 for x in detail["never reached HubSpot"] if x[3])
print(f"  worked in the sheet but never pushed: {sw}")
print(f"  genuinely untouched anywhere:         {buckets['never reached HubSpot'] - sw}")

print()
print("Sheet Status of the companies that never reached HubSpot:")
c = collections.Counter(x[2].strip() or "(blank)" for x in detail["never reached HubSpot"])
for k, v in c.most_common(8): print(f"    {k[:40]:<42}{v}")
json.dump({k: v for k, v in buckets.items()}, open(os.path.join(A, "pct_buckets.json"), "w"))
