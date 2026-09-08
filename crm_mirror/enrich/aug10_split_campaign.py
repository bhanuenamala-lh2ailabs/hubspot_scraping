# -*- coding: utf-8 -*-
"""Split the un-booked LinkedIn-ad Cold Call pile: 150 Lamiya / 150 Yuktha / 23 Ishpreet.

Only deals that are BOTH still at Cold Call AND have no Calendly booking are moved. The 17
with a slot booked stay with Ishpreet untouched — moving those would hand a caller a lead who
is already meeting someone else. Deals past Cold Call (Script Shared, Contract Signed, the
dead ones) are left alone for the same reason.

CONTACTS FOLLOW THE DEAL. A caller who owns a deal but not its contact cannot see the phone
number on the contact record, so transferring one without the other hands over a half-usable
book — the same rule li_campaign_to_ishpreet.py established.

Allocation is by largest-deficit over deals sorted OLDEST FIRST, so each person gets an even
spread of lead ages rather than one of them inheriting every stale 5-Aug form-fill. These are
paid inbound ad leads; age is the thing that kills them.

SAFETY: this is a bulk hubspot_owner_id write, exactly what the 15-minute VCF notifier reads
as "new assignment" and mails about. That scheduled task is disabled and must stay disabled.

Usage: python aug10_split_campaign.py [--apply]
"""
import os, re, sys, json, time, collections, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}

QUOTA = [("96574824", "Lamiya", 150), ("96573782", "Yuktha", 150), ("166322228", "Ishpreet", 23)]
SOURCE = "Linkedin Campaign ( IT Services )"
APPLY = "--apply" in sys.argv
OUT = os.path.join(HERE, "aug10_campaign_split.json")


def hs(u, m="GET", b=None):
    d = json.dumps(b).encode() if b is not None else None
    for a in range(6):
        try:
            r = urllib.request.Request("https://api.hubapi.com" + u, data=d, method=m, headers=H)
            with urllib.request.urlopen(r, timeout=60) as x:
                t = x.read().decode(); return x.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and a < 5: time.sleep(2*(a+1)); continue
            return e.code, {"raw": e.read().decode()[:200]}
        except Exception:
            if a == 5: raise
            time.sleep(3*(a+1))


def main():
    booked = set(json.load(open(os.path.join(HERE, "calendly_booked.json"),
                                encoding="utf-8"))["booked"].keys())
    _, pl = hs("/crm/v3/pipelines/deals")
    LAB = {s["id"]: s["label"] for p in pl["results"] for s in p["stages"]}
    after, deals = None, []
    while True:
        b = {"limit": 200, "properties": ["dealname", "dealstage", "hubspot_owner_id", "createdate"],
             "filterGroups": [{"filters": [{"propertyName": "lead_source", "operator": "EQ", "value": SOURCE}]}]}
        if after: b["after"] = after
        _, d = hs("/crm/v3/objects/deals/search", "POST", b)
        deals += d.get("results", [])
        after = (d.get("paging") or {}).get("next", {}).get("after")
        if not after: break

    pool = [x for x in deals
            if x["id"] not in booked and LAB.get(x["properties"].get("dealstage")) == "Cold Call"]
    pool.sort(key=lambda x: x["properties"].get("createdate") or "")
    print(f"campaign deals {len(deals)} | booked {len(booked)} | "
          f"eligible (Cold Call, not booked): {len(pool)}")
    want = sum(q for _, _, q in QUOTA)
    if len(pool) != want:
        print(f"!! pool is {len(pool)}, quotas total {want} — allocating proportionally instead "
              f"of failing, and reporting the real counts below.")

    # largest-deficit allocation over the age-sorted pool
    assigned = {oid: [] for oid, _, _ in QUOTA}
    tot = sum(q for _, _, q in QUOTA)
    for i, x in enumerate(pool, 1):
        best, bd = None, None
        for oid, nm, q in QUOTA:
            if len(assigned[oid]) >= q: continue
            deficit = q * i / tot - len(assigned[oid])
            if bd is None or deficit > bd: best, bd = oid, deficit
        if best is None: break              # every quota full
        assigned[best].append(x)

    for oid, nm, q in QUOTA:
        got = assigned[oid]
        ds = [ (g["properties"].get("createdate") or "")[:10] for g in got ]
        print(f"   {nm:<10}{len(got):>4}/{q}   lead dates {min(ds) if ds else '-'} .. {max(ds) if ds else '-'}")

    json.dump({nm: [{"id": g["id"], "name": g["properties"].get("dealname"),
                     "created": g["properties"].get("createdate")} for g in assigned[oid]]
               for oid, nm, _ in QUOTA},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\nwrote {os.path.basename(OUT)}")

    if not APPLY:
        print("DRY RUN — nothing moved. Re-run with --apply.")
        return

    # deal -> contacts, so the contact can be moved with it
    ids = [g["id"] for oid in assigned for g in assigned[oid]]
    d2c = {}
    for i in range(0, len(ids), 100):
        _, a = hs("/crm/v4/associations/deals/contacts/batch/read", "POST",
                  {"inputs": [{"id": x} for x in ids[i:i+100]]})
        for res in (a.get("results") or []):
            d2c[str((res.get("from") or {}).get("id"))] = [str(t["toObjectId"]) for t in (res.get("to") or [])]

    moved = collections.Counter(); cmoved = collections.Counter(); fail = 0
    for oid, nm, _ in QUOTA:
        print(f"\n--- moving {len(assigned[oid])} to {nm} ---", flush=True)
        for g in assigned[oid]:
            s, _r = hs(f"/crm/v3/objects/deals/{g['id']}", "PATCH",
                       {"properties": {"hubspot_owner_id": oid, "poc": oid}})
            if s in (200, 201):
                moved[nm] += 1
            else:
                fail += 1; print(f"   FAIL deal {g['id']} -> {s}", flush=True)
            for c in d2c.get(g["id"], []):
                sc, _ = hs(f"/crm/v3/objects/contacts/{c}", "PATCH",
                           {"properties": {"hubspot_owner_id": oid}})
                if sc in (200, 201): cmoved[nm] += 1
            time.sleep(0.12)
            if moved[nm] % 50 == 0 and moved[nm]: print(f"   {moved[nm]}...", flush=True)
    print(f"\ndeals moved: {dict(moved)}   contacts moved: {dict(cmoved)}   failures: {fail}")


main()
