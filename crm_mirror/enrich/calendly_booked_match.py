# -*- coding: utf-8 -*-
"""Which LinkedIn-campaign leads have actually booked a Calendly slot with Ishpreet.

Calendly sits behind Cloudflare and rejects urllib's default User-Agent with a bare
`error code: 1010` and no JSON body — which reads exactly like an auth failure and is not one.
A browser UA is therefore mandatory, not cosmetic.

Matching is on EMAIL, normalised lower/trimmed. The Calendly invitee email is what the person
typed when booking, so it can differ from the form email; every unmatched invitee is printed
rather than silently dropped, because a miss here means a booked meeting nobody calls.

Usage: python calendly_booked_match.py
"""
import os, re, sys, json, time, datetime, collections, urllib.request, urllib.error, urllib.parse
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
CAL = env["ishpreet_calendly"]
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/126.0 Safari/537.36")
SOURCE = "Linkedin Campaign ( IT Services )"


def cal(url):
    for a in range(5):
        try:
            r = urllib.request.Request(url, headers={"Authorization": "Bearer " + CAL,
                "Content-Type": "application/json", "Accept": "application/json", "User-Agent": UA})
            with urllib.request.urlopen(r, timeout=60) as x:
                return json.loads(x.read().decode())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and a < 4: time.sleep(2*(a+1)); continue
            raise RuntimeError(f"calendly {e.code}: {e.read().decode()[:200]}")
        except Exception:
            if a == 4: raise
            time.sleep(2*(a+1))


def hs(u, m="GET", b=None):
    d = json.dumps(b).encode() if b is not None else None
    for a in range(6):
        try:
            r = urllib.request.Request("https://api.hubapi.com" + u, data=d, method=m, headers=H)
            with urllib.request.urlopen(r, timeout=60) as x:
                t = x.read().decode(); return x.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and a < 5: time.sleep(2*(a+1)); continue
            return e.code, {}
        except Exception:
            if a == 5: raise
            time.sleep(3*(a+1))


def em(s): return (s or "").strip().lower()


def main():
    me = cal("https://api.calendly.com/users/me")["resource"]
    print(f"Calendly account: {me.get('name')} <{me.get('email')}>")
    uri, org = me["uri"], me.get("current_organization")

    # every event this user hosts, past and future. Campaign started 4 Aug; widen either side.
    events, page = [], None
    while True:
        q = {"user": uri, "count": "100", "sort": "start_time:asc",
             "min_start_time": "2026-07-01T00:00:00Z", "max_start_time": "2027-01-01T00:00:00Z"}
        if page: q["page_token"] = page
        d = cal("https://api.calendly.com/scheduled_events?" + urllib.parse.urlencode(q))
        events += d.get("collection", [])
        page = (d.get("pagination") or {}).get("next_page_token")
        if not page: break
    print(f"scheduled events found: {len(events)}")
    print("  by status:", dict(collections.Counter(e.get("status") for e in events)))

    # invitees carry the email; one call per event
    inv = []
    for i, e in enumerate(events):
        d = cal(e["uri"] + "/invitees?count=100")
        for v in d.get("collection", []):
            inv.append({"email": em(v.get("email")), "name": v.get("name"),
                        "status": v.get("status"), "event_status": e.get("status"),
                        "start": e.get("start_time"), "event": e.get("name")})
        if (i+1) % 25 == 0: print(f"   invitees {i+1}/{len(events)}", flush=True)
    print(f"invitees: {len(inv)}  (active bookings: "
          f"{sum(1 for v in inv if v['event_status']=='active' and v['status']=='active')})")

    # ---------------- HubSpot: the campaign book ----------------
    after, deals = None, []
    while True:
        b = {"limit": 200, "properties": ["dealname", "dealstage", "hubspot_owner_id", "createdate"],
             "filterGroups": [{"filters": [{"propertyName": "lead_source", "operator": "EQ", "value": SOURCE}]}]}
        if after: b["after"] = after
        _, d = hs("/crm/v3/objects/deals/search", "POST", b)
        deals += d.get("results", [])
        after = (d.get("paging") or {}).get("next", {}).get("after")
        if not after: break
    ids = [x["id"] for x in deals]
    d2c = {}
    for i in range(0, len(ids), 100):
        _, a = hs("/crm/v4/associations/deals/contacts/batch/read", "POST",
                  {"inputs": [{"id": x} for x in ids[i:i+100]]})
        for res in (a.get("results") or []):
            d2c[str((res.get("from") or {}).get("id"))] = [str(t["toObjectId"]) for t in (res.get("to") or [])]
    cids = sorted({c for v in d2c.values() for c in v})
    cp = {}
    for i in range(0, len(cids), 100):
        _, r = hs("/crm/v3/objects/contacts/batch/read", "POST",
                  {"properties": ["email", "firstname", "lastname", "phone"],
                   "inputs": [{"id": c} for c in cids[i:i+100]]})
        for x in (r.get("results") or []): cp[x["id"]] = x["properties"]
    print(f"HubSpot campaign deals: {len(deals)} | contacts: {len(cp)}")

    mail2deal = {}
    for did, cl in d2c.items():
        for c in cl:
            e = em(cp.get(c, {}).get("email"))
            if e: mail2deal.setdefault(e, did)

    LABS = {}
    _, pl = hs("/crm/v3/pipelines/deals")
    for p in pl["results"]:
        for s in p["stages"]: LABS[s["id"]] = s["label"]
    byid = {x["id"]: x for x in deals}

    booked, unmatched = {}, []
    for v in inv:
        if not v["email"]: continue
        did = mail2deal.get(v["email"])
        if did: booked.setdefault(did, v)
        else: unmatched.append(v)

    print("\n" + "="*92)
    print(f"CAMPAIGN LEADS WITH A CALENDLY BOOKING: {len(booked)}")
    print("="*92)
    for did, v in sorted(booked.items(), key=lambda kv: kv[1]["start"] or ""):
        p = byid[did]["properties"]
        flag = "" if (v["event_status"] == "active" and v["status"] == "active") else \
               f"  [{v['event_status']}/{v['status']}]"
        print(f'  {(v["start"] or "")[:16]:<18}{(p.get("dealname") or "")[:26]:<28}'
              f'{v["email"][:34]:<36}{LABS.get(p.get("dealstage"),"?")}{flag}')
    print(f"\nNOT booked: {len(deals) - len(booked)} of {len(deals)} campaign leads")
    if unmatched:
        print(f"\nCalendly invitees with NO matching campaign lead ({len(unmatched)}) — "
              f"other sources, or booked with a different email:")
        for v in unmatched[:25]:
            print(f'  {(v["start"] or "")[:16]:<18}{(v["name"] or "")[:24]:<26}{v["email"][:40]}')
    json.dump({"booked": {k: v for k, v in booked.items()},
               "unmatched": unmatched},
              open(os.path.join(HERE, "calendly_booked.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=str)
    print("\nwrote calendly_booked.json — nothing changed in HubSpot")


main()
