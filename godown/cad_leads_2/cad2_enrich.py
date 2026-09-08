# -*- coding: utf-8 -*-
"""SignalHire enrichment for the freshly-discovered CAD companies list. Apollo is at 0 credits
so this is SignalHire-only (fallback call still attempted in case credits return mid-run).
"""
import csv, json, urllib.request, urllib.error, time, os, sys
sys.path.insert(0, "/Users/bhanu/Desktop/hubspot/crm_mirror/enrich")
from indian_number import to_e164, classify

HUB = "/Users/bhanu/Desktop/hubspot"
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, ".env"), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
SH = env["signal_hire"]; APOLLO_KEY = env["apollo_api_key"]
IN_JSON = "/tmp/cad2_ready_for_enrich.json"
OUT_CSV = os.path.join(HUB, "temporary", "CAD_new_leads_enriched.csv")
STATE = os.path.join(os.path.dirname(__file__), "cad2_enrich_state.json")
AH = {"Content-Type": "application/json", "Cache-Control": "no-cache", "X-Api-Key": APOLLO_KEY}


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


def apollo_match(first, last, company):
    body = {"first_name": first, "last_name": last, "organization_name": company,
            "reveal_personal_emails": False}
    r = urllib.request.Request("https://api.apollo.io/api/v1/people/match",
                                data=json.dumps(body).encode(), method="POST", headers=AH)
    try:
        d = json.loads(urllib.request.urlopen(r, timeout=45).read().decode())
    except Exception:
        return None
    p = d.get("person") or {}
    email = p.get("email") if p.get("email") and "email_not_unlocked" not in p.get("email", "") else None
    phone = None
    for pn in (p.get("phone_numbers") or []):
        if pn.get("type") == "mobile" or "mobile" in (pn.get("type") or ""):
            phone = pn.get("raw_number") or pn.get("sanitized_number"); break
    return {"email": email, "phone": phone}


rows = json.load(open(IN_JSON, encoding="utf-8"))
print(f"total rows: {len(rows)}")
state = json.load(open(STATE)) if os.path.exists(STATE) else {}

results = []
for i, r in enumerate(rows, 1):
    li = (r.get("LinkedIn URL") or "").strip()
    key = li or f"{r.get('First Name')}|{r.get('Last Name')}|{r.get('Company')}"
    if key in state:
        s = state[key]
    else:
        contacts = reveal_sh(li) if li else None
        work = personal = phone = None
        if contacts:
            for c in contacts:
                if c.get("type") == "email":
                    if c.get("subType") == "work" and not work: work = c["value"]
                    elif c.get("subType") == "personal" and not personal: personal = c["value"]
                    elif not work and not personal and not c.get("subType"): personal = c["value"]
                if c.get("type") == "phone" and c.get("subType") == "mobile" and not phone:
                    phone = c["value"]
        source = "signalhire" if (work or personal or phone) else ""
        ph_e164 = to_e164(phone) if phone else None
        if not (ph_e164 and classify(ph_e164) == "mobile"):
            am = apollo_match(r.get("First Name"), r.get("Last Name"), r.get("Company"))
            if am:
                if am.get("phone") and to_e164(am["phone"]) and classify(to_e164(am["phone"])) == "mobile":
                    phone = am["phone"]; source = (source + "+apollo") if source else "apollo"
                if not (work or personal) and am.get("email"):
                    personal = am["email"]; source = (source + "+apollo") if source else "apollo"
            time.sleep(0.2)
        s = {"email": work or personal or "", "is_official": bool(work), "phone": phone or "", "source": source}
        state[key] = s
        if i % 20 == 0: json.dump(state, open(STATE, "w"), indent=0)
        time.sleep(0.25)
    r2 = dict(r)
    r2["Email"] = s["email"]; r2["Is Official"] = "Yes" if s["is_official"] else ("No" if s["email"] else "")
    r2["Phone"] = s["phone"]; r2["Enrich Source"] = s.get("source", "")
    results.append(r2)
    print(f"  [{i}/{len(rows)}] {r['First Name']} {r['Last Name']} ({(r.get('Company') or '')[:30]}) -> "
          f"{s['email'] or '(none)'} / {s['phone'] or '(no mobile)'} [{s.get('source','')}]", flush=True)

json.dump(state, open(STATE, "w"), indent=0)
fieldnames = list(rows[0].keys()) + ["Email", "Is Official", "Phone", "Enrich Source"]
with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for r in results: w.writerow(r)

n_mobile = sum(1 for r in results if r["Phone"] and to_e164(r["Phone"]) and classify(to_e164(r["Phone"])) == "mobile")
print(f"\nwrote {OUT_CSV}")
print(f"valid +91 mobile: {n_mobile}/{len(results)}")
