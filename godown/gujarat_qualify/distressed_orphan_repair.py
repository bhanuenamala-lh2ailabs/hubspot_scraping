# -*- coding: utf-8 -*-
"""Fix-up for the distressed_push.py bug: the first --apply run used an invalid lead_source
enum value, so every deal create 400'd AFTER the contact had already been created — leaving
~155 contacts live in HubSpot with zero associated deal. The second (fixed) run's own top-of-run
dedup then treated those contacts as "already exists" and silently skipped them, so they never
got a deal either.

This script finds every contact from the distressed-startups ready-list that exists in HubSpot
but has NO associated deal, and creates+associates the missing deal for it now, continuing the
same 50:50 Lamiya/Ishpreet alternation from the last count.

Usage: python3 distressed_orphan_repair.py [--apply]
"""
import os, sys, json, re, time, collections, urllib.request, urllib.error, csv
sys.path.insert(0, "/Users/bhanu/Desktop/hubspot/crm_mirror/enrich")
from indian_number import to_e164, classify

HUB = "/Users/bhanu/Desktop/hubspot"
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, ".env"), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
HH = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}
SOURCE = "LinkedIn Sales Nav ( IT Services )"
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


FREEMAIL = {"gmail.com", "yahoo.com", "yahoo.in", "yahoo.co.in", "hotmail.com", "outlook.com",
            "rediffmail.com", "live.com", "icloud.com", "protonmail.com", "aol.com", "ymail.com"}

enriched = list(csv.DictReader(open(os.path.join(HUB, "temporary", "Distressed_Startups_qualified_enriched.csv"),
                                     encoding="utf-8")))
ready = []
for r in enriched:
    e164 = to_e164(r.get("Phone"))
    if e164 and classify(e164) == "mobile":
        r["_e164"] = e164
        ready.append(r)
print(f"ready-list (valid +91 mobile): {len(ready)}")

# pull all contacts (id, linkedin_url) once
contacts = []; after = None
while True:
    b = {"limit": 100, "properties": ["linkedin_url"]}
    if after: b["after"] = after
    s, d = hs("/crm/v3/objects/contacts/search", "POST", b)
    contacts += d.get("results", [])
    after = (d.get("paging") or {}).get("next", {}).get("after")
    if not after: break
LI_TO_CID = {}
for c in contacts:
    li = nli(c["properties"].get("linkedin_url"))
    if li: LI_TO_CID[li] = c["id"]

# find which of our ready-list rows already have a contact in HubSpot
candidates = []
for r in ready:
    li = nli(r.get("LinkedIn URL"))
    cid = LI_TO_CID.get(li)
    if cid:
        candidates.append((r, cid))
print(f"already-exist-as-contact: {len(candidates)}")

# batch-check deal associations for those contacts; keep only the ones with ZERO deals
orphans = []
cids = [cid for _, cid in candidates]
assoc = {}
for i in range(0, len(cids), 100):
    _, a = hs("/crm/v4/associations/contacts/deals/batch/read", "POST",
              {"inputs": [{"id": x} for x in cids[i:i+100]]})
    for res in (a.get("results") or []):
        fid = str((res.get("from") or {}).get("id"))
        assoc[fid] = len(res.get("to") or [])
for r, cid in candidates:
    if assoc.get(cid, 0) == 0:
        orphans.append((r, cid))
print(f"orphans (contact exists, ZERO deals): {len(orphans)}")

if not APPLY:
    print("\nDRY RUN — nothing written. Re-run with --apply")
    for r, cid in orphans[:10]:
        print(f'   cid={cid}  {(r.get("Company") or "")[:28]:<30}{r.get("First Name")} {r.get("Last Name")}')
    sys.exit()

# continue the 50:50 alternation — count what's already been assigned this batch via
# source_tab, so this repair keeps the running total balanced rather than resetting the pool
s, d = hs("/crm/v3/objects/deals/search", "POST", {
    "filterGroups": [{"filters": [{"propertyName": "source_tab", "operator": "EQ",
                                    "value": "distressed_startups_salesnav"}]}],
    "limit": 100, "properties": ["hubspot_owner_id"]})
existing = d.get("results", [])
after = (d.get("paging") or {}).get("next", {}).get("after")
while after:
    s, d = hs("/crm/v3/objects/deals/search", "POST", {
        "filterGroups": [{"filters": [{"propertyName": "source_tab", "operator": "EQ",
                                        "value": "distressed_startups_salesnav"}]}],
        "limit": 100, "after": after, "properties": ["hubspot_owner_id"]})
    existing += d.get("results", [])
    after = (d.get("paging") or {}).get("next", {}).get("after")
cnt = collections.Counter(x["properties"].get("hubspot_owner_id") for x in existing)
LAMIYA, ISHPREET = "96574824", "166322228"
QUOTA = [(LAMIYA, "Lamiya"), (ISHPREET, "Ishpreet")]
qi = 0 if cnt[LAMIYA] <= cnt[ISHPREET] else 1
print(f"current split before repair: Lamiya {cnt[LAMIYA]}, Ishpreet {cnt[ISHPREET]} -> starting with {QUOTA[qi][1]}")

s2, d2 = hs("/crm/v3/pipelines/deals")
DEFAULT = [p for p in d2["results"] if p["id"] == "default"][0]
COLD = [st["id"] for st in DEFAULT["stages"] if st["label"] == "Cold Call"][0]

made = fail = 0
for r, cid in orphans:
    owner_id, owner_name = QUOTA[qi % 2]
    email = (r.get("Email") or "").strip().lower()
    dom = email.split("@")[-1] if email and email.split("@")[-1] not in FREEMAIL else ""
    dp = {"dealname": r.get("Company") or f'{r.get("First Name")} {r.get("Last Name")}',
          "pipeline": DEFAULT["id"], "dealstage": COLD, "hubspot_owner_id": owner_id, "poc": owner_id,
          "lead_source": SOURCE, "source_tab": "distressed_startups_salesnav",
          "lh2_domain": dom, "linkedin_url": (r.get("LinkedIn URL") or "").strip(),
          "description": f'{r.get("First Name")} {r.get("Last Name")} ({r.get("Title","")}) '
                          f'via India Distressed Startups LinkedIn Sales Nav; {r.get("_e164")}'}
    s3, d3 = hs("/crm/v3/objects/deals", "POST", {"properties": dp,
                "associations": [{"to": {"id": cid}, "types": [{"associationCategory": "HUBSPOT_DEFINED",
                                                                 "associationTypeId": 3}]}]})
    if s3 not in (200, 201):
        fail += 1; print(f'  ! deal {(r.get("Company") or "")[:26]}: {s3} {d3}'); continue
    made += 1; qi += 1
    r["owner"] = owner_name
    print(f'   REPAIRED [{made}] {owner_name:<8}{(r.get("Company") or "")[:28]:<30}{r.get("First Name")} {r.get("Last Name")}', flush=True)
    time.sleep(0.12)

c2 = collections.Counter(r.get("owner") for r, _ in orphans if r.get("owner"))
print(f"\nrepaired {made} deals" + (f", {fail} FAILED" if fail else "")
      + f" | this-run totals -> Lamiya {c2['Lamiya']}, Ishpreet {c2['Ishpreet']}")
