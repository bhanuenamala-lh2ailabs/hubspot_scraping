# -*- coding: utf-8 -*-
"""Pre-Apify qualify pass for the Kolkata Sales Nav CSV. Runs entirely on data already in the
sheet (no paid calls) so Apify/SignalHire/Apollo credits only get spent on plausible IT-services
targets: dedup to one profile per company, drop obvious non-IT/junk rows via a cheap regex net,
drop known big-tech brand names, and drop anything that already exists in HubSpot or the local
prequal reserve queue.

Output: /tmp/kolkata_qualified.json — one row per surviving company, ready for Apify scrape.
"""
import csv, json, re, os, sys, time, urllib.request, urllib.error, collections

HUB = "/Users/bhanu/Desktop/hubspot"
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, ".env"), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
HH = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}

IN_CSV = os.path.join(HUB, "temporary", "Kolkata_IT_SalesNav.csv")
OUT_JSON = "/tmp/kolkata_qualified.json"
RESERVE_CSV = os.path.join(HUB, "godown", "prequal", "prequal_out", "reserve.csv")


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


BIGTECH_EXACT = {"infosys", "wipro", "tcs", "tata consultancy services", "hcl", "hcltech",
                  "tech mahindra", "accenture", "cognizant", "capgemini", "ibm", "microsoft",
                  "google", "amazon", "meta", "deloitte", "kpmg", "ey", "pwc", "genpact",
                  "mindtree", "mphasis", "persistent systems", "tesla"}

POS_TITLE = re.compile(
    r"\b(founder|co[- ]?founder|ceo|chief executive|cto|chief technology|managing director|"
    r"\bmd\b|director|owner|proprietor|president)\b", re.I)

NEG_TEXT = re.compile(
    r"\b(motors|aviation|tea (industries|&|and)|real estate|realty|laptop repair(ing)?|"
    r"manpower consultancy|garment|silk technology|plastic surgeon|precision engineering|"
    r"moulders|event(s)? services|journalist|calcutta club|isp in india|network services pvt|"
    r"freight|logistics group|customer support freelancer|data extraction specialist|"
    r"hospital|clinic|foundation\b|trading co|exports?\b|imports?\b|constructions?\b|"
    r"educational consultant|ias academy|visiting faculty|graduate school of business|"
    r"executive search|electrosteel|agribusiness|farmneed|limtex tea|university\b|"
    r"leadership trainee|family business\b)\b", re.I)


rows = list(csv.DictReader(open(IN_CSV, encoding="utf-8")))
print(f"raw rows: {len(rows)}")

# 1. exact LinkedIn URL dedup, keep first
seen_li = set(); dedup1 = []
for r in rows:
    li = nli(r.get("LinkedIn URL"))
    if not li or li in seen_li: continue
    seen_li.add(li); dedup1.append(r)
print(f"after LinkedIn URL dedup: {len(dedup1)}")

# 2. drop rows missing company / name / malformed LinkedIn URL
dedup2 = [r for r in dedup1 if (r.get("Company") or "").strip() and (r.get("First Name") or "").strip()
          and "/in/" in (r.get("LinkedIn URL") or "")]
print(f"after missing-field drop: {len(dedup2)}")

# 3. big-tech brand exclusion
def is_bigtech(company):
    c = company.strip().lower()
    return any(c == b or c.startswith(b + " ") for b in BIGTECH_EXACT)

dedup3 = [r for r in dedup2 if not is_bigtech(r.get("Company") or "")]
print(f"after big-tech exclusion: {len(dedup3)} (-{len(dedup2)-len(dedup3)})")

# 4. positive title filter (founder/CxO/director/owner-type roles only)
dedup4 = [r for r in dedup3 if POS_TITLE.search(r.get("Title") or "") or POS_TITLE.search(r.get("Headline") or "")]
print(f"after title filter: {len(dedup4)} (-{len(dedup3)-len(dedup4)})")

# 5. cheap negative-text net on company + headline + title (obvious non-IT)
def is_neg(r):
    blob = f'{r.get("Company","")} {r.get("Headline","")} {r.get("Title","")}'
    return bool(NEG_TEXT.search(blob))

dedup5 = [r for r in dedup4 if not is_neg(r)]
print(f"after non-IT negative-text filter: {len(dedup5)} (-{len(dedup4)-len(dedup5)})")

# 6. one row per company (core-normalized), prefer Founder/CEO-titled row
def title_rank(r):
    t = (r.get("Title") or "").lower()
    if re.search(r"founder", t): return 0
    if re.search(r"\bceo\b|chief executive", t): return 1
    if re.search(r"\bcto\b|chief technology", t): return 2
    return 3

by_company = collections.defaultdict(list)
for r in dedup5:
    by_company[core(r.get("Company"))].append(r)
dedup6 = [sorted(v, key=title_rank)[0] for v in by_company.values()]
print(f"after one-per-company dedup: {len(dedup6)} ({len(by_company)} unique companies)")

# 7. drop anything already in the local prequal reserve queue
reserve_names = set()
if os.path.exists(RESERVE_CSV):
    for r in csv.DictReader(open(RESERVE_CSV, encoding="utf-8")):
        n = core(r.get("name"))
        if n: reserve_names.add(n)
dedup7 = [r for r in dedup6 if core(r.get("Company")) not in reserve_names]
print(f"after prequal-reserve dedup: {len(dedup7)} (-{len(dedup6)-len(dedup7)})")

# 8. drop anything already in HubSpot (contact LinkedIn URL, or deal dealname core-match)
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

dedup8 = [r for r in dedup7 if nli(r.get("LinkedIn URL")) not in LI_SET and core(r.get("Company")) not in DEAL_NAMES]
print(f"after HubSpot dedup: {len(dedup8)} (-{len(dedup7)-len(dedup8)})")

json.dump(dedup8, open(OUT_JSON, "w"), indent=1)
print(f"\nwrote {OUT_JSON}: {len(dedup8)} companies ready for Apify scrape")
print(f"est. Apify cost: ${len(dedup8)*4/1000:.2f} (people) + ${len(dedup8)*3/1000:.2f} (company, upper bound) "
      f"= ~${len(dedup8)*7/1000:.2f}")
