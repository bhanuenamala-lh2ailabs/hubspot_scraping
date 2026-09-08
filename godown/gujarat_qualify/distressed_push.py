# -*- coding: utf-8 -*-
"""Push the final India Distressed Startups ready-list, 50:50 Lamiya/Ishpreet. Final re-dedup
against HubSpot right before writing, lead_source="LinkedIn Sales Nav ( Distressed Startups )",
source_tab="distressed_startups_salesnav", contact website set from the company's email domain
where derivable. Domain conflicts auto-attach the contact to the existing deal instead of failing.

Usage: python3 distressed_push.py [--apply]
"""
import os, sys, json, re, time, collections, urllib.request, urllib.error, csv
sys.path.insert(0, "/Users/bhanu/Desktop/hubspot/crm_mirror/enrich")
from indian_number import to_e164, classify

HUB = "/Users/bhanu/Desktop/hubspot"
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, ".env"), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
HH = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}
SOURCE = "distressed_live"  # added as a lead_source dropdown option 2026-08-31 per user rename
QUOTA = [("96574824", "Lamiya"), ("166322228", "Ishpreet")]
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


CORP = re.compile(r"\b(pvt|private|limited|ltd|inc|llp|llc|co|company|technologies|technology|"
                   r"solutions|solution|softwares|software|systems|system|services|service|"
                   r"consulting|consultancy|infotech|infosystems|infosystem|labs|studio|studios|"
                   r"digital|group|india|the)\b", re.I)


def core(name):
    n = (name or "").lower(); n = re.sub(r"[^\w\s]", " ", n); n = CORP.sub(" ", n)
    return re.sub(r"\s+", " ", n).strip()


FREEMAIL = {"gmail.com", "yahoo.com", "yahoo.in", "yahoo.co.in", "hotmail.com", "outlook.com",
            "rediffmail.com", "live.com", "icloud.com", "protonmail.com", "aol.com", "ymail.com"}

enriched = list(csv.DictReader(open(os.path.join(HUB, "temporary", "Distressed_Startups_qualified_enriched.csv"),
                                     encoding="utf-8")))
print(f"enriched rows: {len(enriched)}")

ready = []
for r in enriched:
    e164 = to_e164(r.get("Phone"))
    if e164 and classify(e164) == "mobile":
        r["_e164"] = e164
        ready.append(r)
print(f"with a valid +91 mobile: {len(ready)}/{len(enriched)}")

# final re-check against HubSpot right before writing
contacts = []; after = None
while True:
    b = {"limit": 100, "properties": ["linkedin_url", "email", "phone", "mobilephone"]}
    if after: b["after"] = after
    s, d = hs("/crm/v3/objects/contacts/search", "POST", b)
    contacts += d.get("results", [])
    after = (d.get("paging") or {}).get("next", {}).get("after")
    if not after: break
LI_SET = set(nli(c["properties"].get("linkedin_url")) for c in contacts if c["properties"].get("linkedin_url"))
EM_SET = set(nem(c["properties"].get("email")) for c in contacts if c["properties"].get("email"))
PH_SET = set()
for c in contacts:
    for x in (c["properties"].get("phone"), c["properties"].get("mobilephone")):
        e = to_e164(x)
        if e: PH_SET.add(e)

deals = []; after = None
while True:
    b = {"limit": 200, "properties": ["dealname", "lh2_domain"]}
    if after: b["after"] = after
    s, d = hs("/crm/v3/objects/deals/search", "POST", b)
    deals += d.get("results", [])
    after = (d.get("paging") or {}).get("next", {}).get("after")
    if not after: break
DEAL_NAMES = set(core(d["properties"].get("dealname")) for d in deals if d["properties"].get("dealname"))
DOMAIN_TO_DEAL = {d["properties"]["lh2_domain"].strip().lower(): d["id"]
                  for d in deals if d["properties"].get("lh2_domain")}

push = []
skipped = 0
for r in ready:
    li = nli(r.get("LinkedIn URL"))
    em = nem(r.get("Email"))
    ph = r.get("_e164") or to_e164(r.get("Phone"))
    if (li and li in LI_SET) or (em and em in EM_SET) or (ph and ph in PH_SET) or core(r.get("Company")) in DEAL_NAMES:
        skipped += 1; continue
    push.append(r)
print(f"re-checked against current HubSpot state: {skipped} now-duplicate, {len(push)} to push")

if not APPLY:
    print("\nDRY RUN — nothing written. Re-run with --apply")
    for x in push[:10]:
        print(f'   {(x.get("Company") or "")[:28]:<30}{x.get("First Name")} {x.get("Last Name"):<20}{x["_e164"]}')
    sys.exit()

made = attached = fail = 0
qi = 0
s2, d2 = hs("/crm/v3/pipelines/deals")
DEFAULT = [p for p in d2["results"] if p["id"] == "default"][0]
COLD = [st["id"] for st in DEFAULT["stages"] if st["label"] == "Cold Call"][0]
for x in push:
    owner_id, owner_name = QUOTA[qi % 2]
    email = nem(x.get("Email"))
    dom = email.split("@")[-1] if email and email.split("@")[-1] not in FREEMAIL else ""
    cp = {"firstname": x.get("First Name") or "", "lastname": x.get("Last Name") or "",
          "email": email, "phone": x["_e164"], "mobilephone": x["_e164"],
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
            attached += 1; qi += 1
            print(f'   ATTACHED [{attached}] {(x.get("Company") or "")[:28]:<30}'
                  f'{x.get("First Name")} {x.get("Last Name")} -> existing deal {existing_deal}', flush=True)
        else:
            fail += 1; print(f'  ! attach {(x.get("Company") or "")[:26]}: {sA} {dA}')
        time.sleep(0.12)
        continue

    dp = {"dealname": x.get("Company") or f'{x.get("First Name")} {x.get("Last Name")}',
          "pipeline": DEFAULT["id"], "dealstage": COLD, "hubspot_owner_id": owner_id, "poc": owner_id,
          "lead_source": SOURCE, "source_tab": "distressed_startups_salesnav",
          "lh2_domain": dom, "linkedin_url": (x.get("LinkedIn URL") or "").strip(),
          "description": f'{x.get("First Name")} {x.get("Last Name")} ({x.get("Title","")}) '
                          f'via India Distressed Startups LinkedIn Sales Nav; {x.get("_e164")}'}
    s3, d3 = hs("/crm/v3/objects/deals", "POST", {"properties": dp,
                "associations": [{"to": {"id": cid}, "types": [{"associationCategory": "HUBSPOT_DEFINED",
                                                                 "associationTypeId": 3}]}]})
    if s3 not in (200, 201):
        fail += 1; print(f'  ! deal {(x.get("Company") or "")[:26]}: {s3} {d3}'); continue
    made += 1; qi += 1
    if dom: DOMAIN_TO_DEAL[dom] = d3["id"]
    x["owner"] = owner_name
    print(f'   NEW [{made}] {owner_name:<8}{(x.get("Company") or "")[:28]:<30}{x.get("First Name")} {x.get("Last Name")}', flush=True)
    time.sleep(0.12)

c2 = collections.Counter(x.get("owner") for x in push if x.get("owner"))
print(f"\ncreated {made} deals, attached {attached} to existing deals"
      + (f", {fail} FAILED" if fail else "")
      + f" | totals -> Lamiya {c2['Lamiya']}, Ishpreet {c2['Ishpreet']}")
