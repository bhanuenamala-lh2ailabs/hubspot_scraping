# -*- coding: utf-8 -*-
"""Move Ishpreet's LinkedIn-campaign Cold Call deals across to Yuktha and Lamiya.

Scope is deliberately narrow: ONLY deals that are (a) at Cold Call, (b) owned by Ishpreet, and
(c) lead_source is the LinkedIn campaign. Anything of his from another source, or already past
Cold Call, is left alone — he carries the downstream funnel (VCs, scripts, negotiation) and
sweeping those into a caller's book would break work in progress.

Contacts follow their deal. Leaving the contact behind splits ownership of the same person
across two people and the caller loses the phone number on the record they were handed.

Split is even, then ties break toward the SMALLER live Cold Call book, so redistribution does
not deepen an existing imbalance.

Usage: python3 ishpreet_redistribute.py [--apply]
"""
import os, sys, json, time, collections, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(HERE)
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}

YUKTHA, LAMIYA, ISHPREET = "96573782", "96574824", "166322228"
NAME = {YUKTHA: "Yuktha", LAMIYA: "Lamiya", ISHPREET: "Ishpreet"}
APPLY = "--apply" in sys.argv


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
    _, pl = hs("/crm/v3/pipelines/deals")
    LAB = {s["id"]: s["label"] for p in pl["results"] for s in p["stages"]}
    CC = [s for s, l in LAB.items() if l == "Cold Call"]

    after, rows = None, []
    while True:
        b = {"limit": 200, "properties": ["dealname", "dealstage", "pipeline",
                                          "hubspot_owner_id", "lead_source", "createdate"],
             "filterGroups": [{"filters": [{"propertyName": "dealstage", "operator": "IN", "values": CC}]}]}
        if after: b["after"] = after
        _, d = hs("/crm/v3/objects/deals/search", "POST", b)
        rows += d.get("results", [])
        after = (d.get("paging") or {}).get("next", {}).get("after")
        if not after: break

    book = collections.Counter(x["properties"].get("hubspot_owner_id") for x in rows)
    print(f"live Cold Call queue: {len(rows)}")
    for o in (YUKTHA, LAMIYA, ISHPREET):
        print(f"   {NAME[o]:<10}{book.get(o,0):>4}")

    mine = [x for x in rows if x["properties"].get("hubspot_owner_id") == ISHPREET]
    li = [x for x in mine if "linkedin" in (x["properties"].get("lead_source") or "").lower()]
    other = [x for x in mine if x not in li]
    print(f"\nIshpreet at Cold Call: {len(mine)}")
    print(f"   LinkedIn campaign (moving) : {len(li)}")
    print(f"   other sources (left alone) : {len(other)}")
    for x in other:
        print(f"      keep  {x['properties']['dealname'][:34]:<36}{x['properties'].get('lead_source')}")

    # oldest first, so the longest-waiting leads land with whoever gets dealt first
    li.sort(key=lambda x: x["properties"].get("createdate") or "")
    live = {YUKTHA: book.get(YUKTHA, 0), LAMIYA: book.get(LAMIYA, 0)}
    given = collections.Counter()
    plan = []
    for x in li:
        # even split; ties go to the smaller live book
        if given[YUKTHA] < given[LAMIYA]: o = YUKTHA
        elif given[LAMIYA] < given[YUKTHA]: o = LAMIYA
        else: o = YUKTHA if live[YUKTHA] + given[YUKTHA] <= live[LAMIYA] + given[LAMIYA] else LAMIYA
        given[o] += 1
        plan.append((x, o))
    print(f"\nplan ({len(plan)}):")
    for x, o in plan:
        print(f"   {x['properties']['dealname'][:36]:<38}{(x['properties'].get('createdate') or '')[:10]}  -> {NAME[o]}")
    print(f"\nsplit: Yuktha {given[YUKTHA]}  Lamiya {given[LAMIYA]}")
    print(f"resulting Cold Call books: Yuktha {live[YUKTHA]+given[YUKTHA]}  "
          f"Lamiya {live[LAMIYA]+given[LAMIYA]}  Ishpreet {len(other)}")

    if not APPLY:
        print("\nDRY RUN — nothing changed. Re-run with --apply.")
        return

    ok = fail = cok = 0
    for x, o in plan:
        did = x["id"]
        s, _ = hs(f"/crm/v3/objects/deals/{did}", "PATCH",
                  {"properties": {"hubspot_owner_id": o, "poc": o}})
        if s in (200, 201): ok += 1
        else: fail += 1; print(f"   FAIL deal {did} -> {s}")
        # contact follows the deal
        _, a = hs(f"/crm/v4/objects/deals/{did}/associations/contacts")
        for t in (a.get("results") or []):
            cid = t.get("toObjectId")
            if cid:
                cs, _c = hs(f"/crm/v3/objects/contacts/{cid}", "PATCH",
                            {"properties": {"hubspot_owner_id": o}})
                if cs in (200, 201): cok += 1
        time.sleep(0.15)
    print(f"\nmoved {ok} deals ({fail} failed), reassigned {cok} contacts")


main()
