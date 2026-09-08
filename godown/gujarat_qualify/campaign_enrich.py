# -*- coding: utf-8 -*-
"""Email enrichment for the campaign-leads-export sheet: Apollo people/match first (name +
company, reveal_personal_emails on since this is email-only, no phone gate needed), SignalHire
reveal-by-LinkedIn-URL as fallback whenever Apollo comes back empty or rate-limited/exhausted.
"""
import csv, json, urllib.request, urllib.error, time, os

HUB = "/Users/bhanu/Desktop/hubspot"
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, ".env"), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
SH = env["signal_hire"]; APOLLO_KEY = env["apollo_api_key"]
IN_CSV = os.path.join(HUB, "temporary", "campaign-leads-export-087a089f-5447-4dd0-9853-8563b40cfc71-2026-08-24.csv")
OUT_CSV = os.path.join(HUB, "temporary", "campaign-leads-export-2026-08-24_enriched.csv")
STATE = os.path.join(os.path.dirname(__file__), "campaign_enrich_state.json")
AH = {"Content-Type": "application/json", "Cache-Control": "no-cache", "X-Api-Key": APOLLO_KEY}

apollo_exhausted = False


def apollo_match(first, last, company):
    global apollo_exhausted
    if apollo_exhausted: return None, "exhausted"
    body = {"first_name": first, "last_name": last, "organization_name": company,
            "reveal_personal_emails": True}
    r = urllib.request.Request("https://api.apollo.io/api/v1/people/match",
                                data=json.dumps(body).encode(), method="POST", headers=AH)
    try:
        resp = urllib.request.urlopen(r, timeout=45)
        d = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 429:
            apollo_exhausted = True
            return None, "rate_limited"
        return None, f"http{e.code}"
    except Exception as e:
        return None, str(e)[:60]
    p = d.get("person") or {}
    email = p.get("email")
    if email and "email_not_unlocked" in email: email = None
    return email, "apollo" if email else "apollo_miss"


def reveal_sh(li_url):
    body = {"items": [li_url], "withoutWaterfall": True}
    r = urllib.request.Request("https://www.signalhire.com/api/v1/candidate/search",
                                data=json.dumps(body).encode(), method="POST",
                                headers={"apikey": SH, "Content-Type": "application/json"})
    try:
        d = json.loads(urllib.request.urlopen(r, timeout=60).read().decode())
    except Exception:
        return None
    for it in (d if isinstance(d, list) else d.get("results", [])) or []:
        if isinstance(it, dict) and it.get("status") == "success":
            return (it.get("candidate") or {}).get("contacts") or []
    return None


rows = list(csv.DictReader(open(IN_CSV, encoding="utf-8-sig")))
print(f"total rows: {len(rows)}")
state = json.load(open(STATE)) if os.path.exists(STATE) else {}

results = []
n_apollo = n_sh = n_none = 0
for i, r in enumerate(rows, 1):
    li = (r.get("LinkedIn URL") or "").strip()
    key = li or f"{r.get('First Name')}|{r.get('Last Name')}|{r.get('Company')}"
    if key in state:
        s = state[key]
    else:
        email, src = apollo_match(r.get("First Name"), r.get("Last Name"), r.get("Company"))
        if not email and li:
            contacts = reveal_sh(li)
            if contacts:
                work = personal = None
                for c in contacts:
                    if c.get("type") == "email":
                        if c.get("subType") == "work" and not work: work = c["value"]
                        elif c.get("subType") == "personal" and not personal: personal = c["value"]
                        elif not work and not personal and not c.get("subType"): personal = c["value"]
                if work or personal:
                    email = work or personal
                    src = "signalhire"
        s = {"email": email or "", "source": src if email else (src or "none")}
        state[key] = s
        if i % 20 == 0: json.dump(state, open(STATE, "w"), indent=0)
        time.sleep(0.2)
    if s["email"]:
        if "signalhire" in s["source"]: n_sh += 1
        else: n_apollo += 1
    else:
        n_none += 1
    r2 = dict(r); r2["Email"] = s["email"]; r2["Enrich Source"] = s["source"]
    results.append(r2)
    print(f"  [{i}/{len(rows)}] {r['First Name']} {r['Last Name']} ({r['Company'][:30]}) -> "
          f"{s['email'] or '(none)'} [{s['source']}]", flush=True)

json.dump(state, open(STATE, "w"), indent=0)
fieldnames = list(rows[0].keys()) + ["Email", "Enrich Source"]
with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for r in results: w.writerow(r)

print(f"\nwrote {OUT_CSV}")
print(f"emails found: {n_apollo + n_sh}/{len(results)} (apollo {n_apollo}, signalhire {n_sh}) | none: {n_none}")
