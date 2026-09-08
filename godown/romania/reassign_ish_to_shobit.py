# -*- coding: utf-8 -*-
"""Move every Romania deal off Ishpreet onto Shobit — 2026-08-14, per instruction.

Selection is by lead_source = "Romania ( IT Services )" AND current owner = Ishpreet, queried
LIVE rather than replayed from pushed_ro.json: if anyone hand-moved a deal since the push, the
CRM is the truth and the local file is not. Both hubspot_owner_id and poc are updated — the
push set poc = owner and leaving it stale would keep routing reports to the wrong person.

pushed_ro.json is rewritten afterwards so the local record matches what the CRM now says.

Usage: python3 reassign_ish_to_shobit.py [--apply]
"""
import os, sys, json, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}

ISHPREET, SHOBIT = "166322228", "166262056"
SOURCE = "Romania ( IT Services )"
DONE = os.path.join(HERE, "pushed_ro.json")
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


def romania_deals():
    out, after = [], None
    while True:
        b = {"limit": 100, "properties": ["dealname", "hubspot_owner_id", "poc", "dealstage"],
             "filterGroups": [{"filters": [
                 {"propertyName": "lead_source", "operator": "EQ", "value": SOURCE}]}]}
        if after: b["after"] = after
        s, r = hs("/crm/v3/objects/deals/search", "POST", b)
        if s != 200: sys.exit(f"search {s}: {str(r)[:200]}")
        out += r.get("results", [])
        after = (r.get("paging") or {}).get("next", {}).get("after")
        if not after: break
    return out


def main():
    deals = romania_deals()
    mine = [x for x in deals if x["properties"].get("hubspot_owner_id") == ISHPREET]
    print(f"Romania deals total {len(deals)} | on Ishpreet {len(mine)} | "
          f"on Shobit {sum(1 for x in deals if x['properties'].get('hubspot_owner_id')==SHOBIT)}")
    for x in mine:
        print(f'   {x["id"]:<14}{x["properties"].get("dealname","")[:44]}')
    if not APPLY:
        print("\nDRY RUN — nothing changed. Re-run with --apply."); return

    ok = fail = 0
    for x in mine:
        s, r = hs(f"/crm/v3/objects/deals/{x['id']}", "PATCH",
                  {"properties": {"hubspot_owner_id": SHOBIT, "poc": SHOBIT}})
        if s == 200: ok += 1
        else: fail += 1; print(f'   FAIL {x["id"]} {s} {str(r)[:120]}')
        time.sleep(0.2)

    after = romania_deals()
    ci = sum(1 for x in after if x["properties"].get("hubspot_owner_id") == ISHPREET)
    cs = sum(1 for x in after if x["properties"].get("hubspot_owner_id") == SHOBIT)
    print(f"\npatched {ok}, failed {fail} | VERIFY live: Ishpreet {ci}, Shobit {cs}")

    if os.path.exists(DONE):
        done = json.load(open(DONE, encoding="utf-8"))
        moved = 0
        for v in done.values():
            if v.get("owner") == "Ishpreet": v["owner"] = "Shobit"; moved += 1
        json.dump(done, open(DONE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"pushed_ro.json: {moved} rows re-marked Shobit")


main()
