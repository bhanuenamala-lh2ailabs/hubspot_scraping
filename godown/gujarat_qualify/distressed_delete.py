# -*- coding: utf-8 -*-
"""Removes today's distressed-startups Lamiya/Ishpreet push per explicit user request.

Deals: archived via the standard DELETE endpoint. NOTE — this is HubSpot's only public-API
delete operation for deals; it moves them to the recycle bin (recoverable ~90 days), not an
instant permanent purge. HubSpot doesn't expose an immediate-permanent-purge API for deals.

Contacts: permanently removed via the GDPR-delete endpoint, which HubSpot documents as an
actual permanent erasure (not a soft-delete) — this one genuinely satisfies "permanent purge".
"""
import json, os, urllib.request, urllib.error, time

env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open("/Users/bhanu/Desktop/hubspot/.env", encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
HH = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}


def hs(path, method="GET", body=None):
    d = json.dumps(body).encode() if body else None
    req = urllib.request.Request("https://api.hubapi.com" + path, data=d, method=method, headers=HH)
    for a in range(5):
        try:
            r = urllib.request.urlopen(req, timeout=45)
            t = r.read().decode() if r.length != 0 else ""
            return r.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504) and a < 4: time.sleep(2 * (a + 1)); continue
            t = e.read().decode(); return e.code, (json.loads(t) if t else {"raw": t})
        except Exception:
            if a == 4: raise
            time.sleep(2)


deal_ids = json.load(open("/tmp/deals_to_delete.json"))
contact_ids = json.load(open("/tmp/contacts_to_delete.json"))
print(f"deals to archive: {len(deal_ids)} | contacts to GDPR-delete: {len(contact_ids)}")

d_ok = d_fail = 0
for did in deal_ids:
    s, d = hs(f"/crm/v3/objects/deals/{did}", "DELETE")
    if s in (204, 200):
        d_ok += 1
    else:
        d_fail += 1
        print(f"  ! deal {did} archive failed: {s} {d}")
    time.sleep(0.1)
print(f"deals archived: {d_ok}, failed: {d_fail}")

c_ok = c_fail = 0
for cid in contact_ids:
    s, d = hs("/crm/v3/objects/contacts/gdpr-delete", "POST", {"objectId": cid})
    if s in (204, 200):
        c_ok += 1
    else:
        c_fail += 1
        print(f"  ! contact {cid} gdpr-delete failed: {s} {d}")
    time.sleep(0.15)
print(f"contacts permanently deleted: {c_ok}, failed: {c_fail}")
