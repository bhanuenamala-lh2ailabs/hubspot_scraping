# -*- coding: utf-8 -*-
"""Run company-match + India-location filter on whatever CAD expansion profiles have
scraped so far, then enrich the confirmed set via SignalHire/Apollo, and report how many
have a valid +91 mobile ready to call. Used to decide when to stop the profile-scrape run."""
import json, re, os, sys, time, urllib.request, urllib.error
sys.path.insert(0, "/Users/bhanu/Desktop/hubspot/crm_mirror/enrich")
from indian_number import to_e164, classify

HUB = "/Users/bhanu/Desktop/hubspot"
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, ".env"), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
SH = env["signal_hire"]; APOLLO_KEY = env["apollo_api_key"]
AH = {"Content-Type": "application/json", "Cache-Control": "no-cache", "X-Api-Key": APOLLO_KEY}
STATE = os.path.join(os.path.dirname(__file__), "expansion_enrich_state.json")


def nli(u):
    u = (u or "").strip().lower().split("?")[0].rstrip("/")
    u = re.sub(r"^https?://", "", u); u = re.sub(r"^([a-z]{2}\.)?linkedin\.com", "linkedin.com", u)
    return u.replace("www.", "")


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


qcand = json.load(open("/tmp/cad_expansion_qcand.json"))
profiles = json.load(open(f"{HUB}/godown/cad_leads_2/expansion_profiles.json"))
by_li = {nli(p.get("linkedinUrl")): p for p in profiles}

confirmed = []
seen = set()
for company, urls in qcand.items():
    for u in urls[:2]:
        if u in seen: continue
        p = by_li.get(u)
        if not p: continue
        seen.add(u)
        cp = (p.get("currentPosition") or [{}])[0]
        cname = cp.get("companyName") or ""
        if company.replace(" ", "").lower() not in (cname or "").replace(" ", "").lower() and \
           (cname or "").replace(" ", "").lower() not in company.replace(" ", "").lower():
            continue
        loc = p.get("location") or {}
        parsed = loc.get("parsed") or {}
        is_india = (parsed.get("country") == "India") or ("india" in (loc.get("linkedinText") or "").lower())
        if not is_india: continue
        confirmed.append({"p": p, "company": company, "cname": cname, "title": cp.get("position")})
        break  # one confirmed hit per company is enough

print(f"scraped so far: {len(profiles)} | confirmed match+India: {len(confirmed)}")

state = json.load(open(STATE)) if os.path.exists(STATE) else {}
mobile_ready = []
for i, c in enumerate(confirmed, 1):
    p = c["p"]; li = (p.get("linkedinUrl") or "").strip()
    key = li
    if key in state:
        s = state[key]
    else:
        contacts = reveal_sh(li) if li else None
        work = personal = phone = None
        if contacts:
            for cc in contacts:
                if cc.get("type") == "email":
                    if cc.get("subType") == "work" and not work: work = cc["value"]
                    elif cc.get("subType") == "personal" and not personal: personal = cc["value"]
                if cc.get("type") == "phone" and cc.get("subType") == "mobile" and not phone:
                    phone = cc["value"]
        s = {"email": work or personal or "", "phone": phone or ""}
        state[key] = s
        if i % 25 == 0: json.dump(state, open(STATE, "w"))
        time.sleep(0.15)
    e164 = to_e164(s.get("phone")) if s.get("phone") else None
    if e164 and classify(e164) == "mobile":
        mobile_ready.append({**c, "email": s.get("email"), "phone": s.get("phone"), "e164": e164})

json.dump(state, open(STATE, "w"))
print(f"valid +91 mobile ready: {len(mobile_ready)}")
json.dump(mobile_ready, open("/tmp/cad_expansion_mobile_ready.json", "w"), default=str, indent=1, ensure_ascii=False)
