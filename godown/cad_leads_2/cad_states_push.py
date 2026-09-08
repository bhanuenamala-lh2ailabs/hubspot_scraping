# -*- coding: utf-8 -*-
"""Push the combined Gujarat + new-CAD half, all to Yuktha, lead_source=CAD_salesNav.
Final re-dedup against HubSpot right before writing. Domain conflicts auto-attach.

Usage: python3 cad_combined_push.py [--apply]
"""
import os, sys, json, re, time, urllib.request, urllib.error
sys.path.insert(0, "/Users/bhanu/Desktop/hubspot/crm_mirror/enrich")
from indian_number import to_e164, classify

HUB = "/Users/bhanu/Desktop/hubspot"
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, ".env"), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
HH = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}
SOURCE = "CAD_salesNav"
OWNER_ID, OWNER_NAME = "96573782", "Yuktha"
APPLY = "--apply" in sys.argv


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


def nem(e): return (e or "").strip().lower()


FREEMAIL = {"gmail.com", "yahoo.com", "yahoo.in", "yahoo.co.in", "hotmail.com", "outlook.com",
            "rediffmail.com", "live.com", "icloud.com", "protonmail.com", "aol.com", "ymail.com"}

push = json.load(open("/tmp/cad_states_push_half.json"))
print(f"to push: {len(push)}")

if not APPLY:
    print("\nDRY RUN — nothing written. Re-run with --apply")
    for x in push[:10]:
        print(f'   {(x.get("Company") or "")[:28]:<30}{x.get("First Name")} {x.get("Last Name"):<20}{x.get("Phone")}')
    sys.exit()

made = attached = fail = 0
s2, d2 = hs("/crm/v3/pipelines/deals")
DEFAULT = [p for p in d2["results"] if p["id"] == "default"][0]
COLD = [st["id"] for st in DEFAULT["stages"] if st["label"] == "Cold Call"][0]

# domain -> existing deal, to attach conflicts instead of failing
deals = []; after = None
while True:
    b = {"limit": 200, "properties": ["lh2_domain"]}
    if after: b["after"] = after
    s, d = hs("/crm/v3/objects/deals/search", "POST", b)
    deals += d.get("results", [])
    after = (d.get("paging") or {}).get("next", {}).get("after")
    if not after: break
DOMAIN_TO_DEAL = {d["properties"]["lh2_domain"].strip().lower(): d["id"]
                  for d in deals if d["properties"].get("lh2_domain")}

for x in push:
    email = nem(x.get("Email"))
    dom = email.split("@")[-1] if email and email.split("@")[-1] not in FREEMAIL else ""
    e164 = to_e164(x.get("Phone")) or x.get("Phone")
    cp = {"firstname": x.get("First Name") or "", "lastname": x.get("Last Name") or "",
          "email": email, "phone": e164, "mobilephone": e164,
          "jobtitle": x.get("Title") or "", "company": x.get("Company") or "",
          "linkedin_url": (x.get("LinkedIn URL") or "").strip(), "country": "India",
          "website": f"https://{dom}" if dom else ""}
    s, d = hs("/crm/v3/objects/contacts", "POST", {"properties": {k: v for k, v in cp.items() if v}})
    if s not in (200, 201):
        blob = str(d.get("message") or d.get("raw") or d)
        if s == 409 and "Existing ID" in blob:
            m = re.search(r"Existing ID: (\d+)", blob); cid = m.group(1) if m else None
        else:
            fail += 1; print(f'  ! contact {(x.get("Company") or "")[:26]}: {s} {d}'); continue
    else:
        cid = d["id"]
    if not cid:
        fail += 1; continue

    existing_deal = DOMAIN_TO_DEAL.get(dom) if dom else None
    if existing_deal:
        sA, dA = hs(f"/crm/v4/objects/deals/{existing_deal}/associations/default/contacts/{cid}", "PUT")
        if sA in (200, 201):
            attached += 1
            print(f'   ATTACHED [{attached}] {(x.get("Company") or "")[:28]:<30}'
                  f'{x.get("First Name")} {x.get("Last Name")} -> existing deal {existing_deal}', flush=True)
        else:
            fail += 1; print(f'  ! attach {(x.get("Company") or "")[:26]}: {sA} {dA}')
        time.sleep(0.12)
        continue

    dp = {"dealname": x.get("Company") or f'{x.get("First Name")} {x.get("Last Name")}',
          "pipeline": DEFAULT["id"], "dealstage": COLD, "hubspot_owner_id": OWNER_ID, "poc": OWNER_ID,
          "lead_source": SOURCE, "source_tab": "cad_states_2",
          "lh2_domain": dom, "linkedin_url": (x.get("LinkedIn URL") or "").strip(),
          "description": f'{x.get("First Name")} {x.get("Last Name")} ({x.get("Title","")}) '
                          f'via CAD Gujarat/Karnataka/Maharashtra sourcing; {e164}'}
    s3, d3 = hs("/crm/v3/objects/deals", "POST", {"properties": dp,
                "associations": [{"to": {"id": cid}, "types": [{"associationCategory": "HUBSPOT_DEFINED",
                                                                 "associationTypeId": 3}]}]})
    if s3 not in (200, 201):
        fail += 1; print(f'  ! deal {(x.get("Company") or "")[:26]}: {s3} {d3}'); continue
    made += 1
    if dom: DOMAIN_TO_DEAL[dom] = d3["id"]
    print(f'   NEW [{made}] {OWNER_NAME:<8}{(x.get("Company") or "")[:28]:<30}{x.get("First Name")} {x.get("Last Name")}', flush=True)
    time.sleep(0.12)

print(f"\ncreated {made} deals, attached {attached} to existing deals"
      + (f", {fail} FAILED" if fail else "") + f" | all to Yuktha")
