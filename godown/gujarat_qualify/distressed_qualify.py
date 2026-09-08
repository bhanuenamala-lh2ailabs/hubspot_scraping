# -*- coding: utf-8 -*-
"""Title-filter + dedup pass for the India Distressed Startups Sales Nav CSV. Keeps only
founder/CEO/CTO/CPO/owner-type titles per instruction (drops Tech Lead, Member, Director-only,
Chairman, Partner, LP, VP, advisors, etc.) — those are real decision-makers with authority over
a dormant codebase; the rest usually aren't. Then dedupes against local + HubSpot state before
spending SignalHire/Apollo credits.

Output: /tmp/distressed_qualified.json
"""
import csv, json, re, os, time, urllib.request, urllib.error

HUB = "/Users/bhanu/Desktop/hubspot"
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, ".env"), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
HH = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}

IN_CSV = os.path.join(HUB, "temporary", "India_Distressed_Startups_SalesNav.csv")
OUT_JSON = "/tmp/distressed_qualified.json"
RESERVE_CSV = os.path.join(HUB, "godown", "prequal", "prequal_out", "reserve.csv")

KEEP_TITLE = re.compile(
    r'found|\bceo\b|chief executive|\bcto\b|chief technology|\bcpo\b|chief product|'
    r'\bowner\b|proprietor', re.I)


def hs(path, method="GET", body=None):
    d = json.dumps(body).encode() if body else None
    req = urllib.request.Request("https://api.hubapi.com" + path, data=d, method=method, headers=HH)
    for a in range(5):
        try:
            r = urllib.request.urlopen(req, timeout=45); t = r.read().decode()
            return r.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504) and a < 4: time.sleep(2 * (a + 1)); continue
            t = e.read().decode(); return e.code, (json.loads(t) if t else {"raw": t})
        except Exception:
            if a == 4: raise
            time.sleep(2)


def nli(u):
    u = (u or "").strip().lower().split("?")[0].rstrip("/")
    u = re.sub(r"^https?://", "", u); u = re.sub(r"^([a-z]{2}\.)?linkedin\.com", "linkedin.com", u)
    return u.replace("www.", "")


CORP = re.compile(r"\b(pvt|private|limited|ltd|inc|llp|llc|co|company|technologies|technology|"
                   r"solutions|solution|softwares|software|systems|system|services|service|"
                   r"consulting|consultancy|infotech|infosystems|infosystem|labs|studio|studios|"
                   r"digital|group|india|the)\b", re.I)


def core(name):
    n = (name or "").lower(); n = re.sub(r"[^\w\s]", " ", n); n = CORP.sub(" ", n)
    return re.sub(r"\s+", " ", n).strip()


rows = list(csv.DictReader(open(IN_CSV, encoding="utf-8")))
print(f"raw rows: {len(rows)}")

# 1. exact LinkedIn URL dedup, keep first
seen_li = set(); dedup1 = []
for r in rows:
    li = nli(r.get("LinkedIn URL"))
    if not li or li in seen_li: continue
    seen_li.add(li); dedup1.append(r)
print(f"after LinkedIn URL dedup: {len(dedup1)}")

# 2. title filter — the actual "remove tech lead / insignificant" instruction
dedup2 = [r for r in dedup1 if KEEP_TITLE.search(r.get("Title") or "")]
dropped_titles = [r.get("Title") for r in dedup1 if not KEEP_TITLE.search(r.get("Title") or "")]
print(f"after title filter (founder/CEO/CTO/CPO/owner only): {len(dedup2)} (-{len(dedup1)-len(dedup2)})")

# 3. drop rows missing company/name/malformed LinkedIn URL
dedup3 = [r for r in dedup2 if (r.get("Company") or "").strip() and (r.get("First Name") or "").strip()
          and "/in/" in (r.get("LinkedIn URL") or "")]
print(f"after missing-field drop: {len(dedup3)}")

# 4. one row per company (core-normalized), prefer Founder/CEO-titled row
import collections
def title_rank(r):
    t = (r.get("Title") or "").lower()
    if "found" in t: return 0
    if "ceo" in t or "chief executive" in t: return 1
    if "cto" in t or "chief technology" in t: return 2
    return 3

by_company = collections.defaultdict(list)
for r in dedup3:
    by_company[core(r.get("Company"))].append(r)
dedup4 = [sorted(v, key=title_rank)[0] for v in by_company.values()]
print(f"after one-per-company dedup: {len(dedup4)} ({len(by_company)} unique companies)")

# 5. drop anything already in the local prequal reserve queue
reserve_names = set()
if os.path.exists(RESERVE_CSV):
    for r in csv.DictReader(open(RESERVE_CSV, encoding="utf-8")):
        n = core(r.get("name"))
        if n: reserve_names.add(n)
dedup5 = [r for r in dedup4 if core(r.get("Company")) not in reserve_names]
print(f"after prequal-reserve dedup: {len(dedup5)} (-{len(dedup4)-len(dedup5)})")

# 6. drop anything already in HubSpot (contact LinkedIn URL, or deal dealname core-match)
print("pulling HubSpot contacts + deals for dedup...")
contacts = []; after = None
while True:
    b = {"limit": 100, "properties": ["linkedin_url"]}
    if after: b["after"] = after
    s, d = hs("/crm/v3/objects/contacts/search", "POST", b)
    contacts += d.get("results", [])
    after = (d.get("paging") or {}).get("next", {}).get("after")
    if not after: break
LI_SET = set(nli(c["properties"].get("linkedin_url")) for c in contacts if c["properties"].get("linkedin_url"))

deals = []; after = None
while True:
    b = {"limit": 200, "properties": ["dealname"]}
    if after: b["after"] = after
    s, d = hs("/crm/v3/objects/deals/search", "POST", b)
    deals += d.get("results", [])
    after = (d.get("paging") or {}).get("next", {}).get("after")
    if not after: break
DEAL_NAMES = set(core(d["properties"].get("dealname")) for d in deals if d["properties"].get("dealname"))

dedup6 = [r for r in dedup5 if nli(r.get("LinkedIn URL")) not in LI_SET and core(r.get("Company")) not in DEAL_NAMES]
print(f"after HubSpot dedup: {len(dedup6)} (-{len(dedup5)-len(dedup6)})")

json.dump(dedup6, open(OUT_JSON, "w"), indent=1)
print(f"\nwrote {OUT_JSON}: {len(dedup6)} ready for enrichment")
