# -*- coding: utf-8 -*-
"""Mail Yuktha and Lamiya ONLY the .vcf of the IT firms pushed to them TODAY. No body.

Scope is resolved from HubSpot, not from the local push log: createdate = today AND
lead_source = the scraped IT tag AND owner = the caller. The log is append-only and slicing
it by position would silently mail the wrong batch the moment a run is repeated or resumed.

+91 gate applies — a card with no dialable number is not written. Nothing should fail it here
(the push itself required a number) but the check stays, because a contact can be edited
between push and mail.

Usage: python aug11_vcf_only_mail.py [--send] [--test]
"""
import os, sys, json, time, datetime, collections, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from lead_vcf_notifier import vcard
import gmail_sender

env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}

PEOPLE = {"96573782": ("Yuktha", "yuktha.anand@lh2.ai"),
          "96574824": ("Lamiya", "lamiya.saleem@lh2.ai")}
SOURCE = "Scraping Algo ( IT services )"
TEST_TO = "bhanu.enamala@lh2.ai"
SEND = "--send" in sys.argv; TEST = "--test" in sys.argv
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
today = datetime.datetime.now(IST).date()


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


def main():
    after, deals = None, []
    while True:
        b = {"limit": 200, "properties": ["dealname", "hubspot_owner_id", "createdate", "lead_source"],
             "filterGroups": [{"filters": [
                 {"propertyName": "lead_source", "operator": "EQ", "value": SOURCE},
                 {"propertyName": "hubspot_owner_id", "operator": "IN", "values": list(PEOPLE)},
                 {"propertyName": "createdate", "operator": "GTE", "value": today.isoformat()+"T00:00:00Z"}]}]}
        if after: b["after"] = after
        _, d = hs("/crm/v3/objects/deals/search", "POST", b)
        deals += d.get("results", [])
        after = (d.get("paging") or {}).get("next", {}).get("after")
        if not after: break
    deals = [x for x in deals if (x["properties"].get("createdate") or "")[:10] == today.isoformat()]
    print(f"pushed today ({today}): {len(deals)}",
          dict(collections.Counter(PEOPLE[x['properties']['hubspot_owner_id']][0] for x in deals)))

    ids = [x["id"] for x in deals]; d2c = {}
    for i in range(0, len(ids), 100):
        _, a = hs("/crm/v4/associations/deals/contacts/batch/read", "POST",
                  {"inputs": [{"id": x} for x in ids[i:i+100]]})
        for res in (a.get("results") or []):
            d2c[str((res.get("from") or {}).get("id"))] = [str(t["toObjectId"]) for t in (res.get("to") or [])]
    cids = sorted({c for v in d2c.values() for c in v}); cp = {}
    for i in range(0, len(cids), 100):
        _, r = hs("/crm/v3/objects/contacts/batch/read", "POST",
                  {"properties": ["firstname", "lastname", "email", "phone", "mobilephone",
                                  "company", "jobtitle"],
                   "inputs": [{"id": c} for c in cids[i:i+100]]})
        for x in (r.get("results") or []): cp[x["id"]] = x["properties"]

    for oid, (who, addr) in PEOPLE.items():
        mine = [x for x in deals if x["properties"]["hubspot_owner_id"] == oid]
        cards, nophone = [], 0
        for x in mine:
            for c in d2c.get(x["id"], []):
                p = cp.get(c, {})
                if not ((p.get("mobilephone") or "").strip() or (p.get("phone") or "").strip()):
                    nophone += 1; continue
                cards.append(vcard(p, p.get("company") or x["properties"].get("dealname", ""),
                                   x["properties"].get("dealname", ""), who, "Cold Call"))
        vcf = ("\r\n".join(cards)).encode("utf-8")
        fn = f"lh2_itfirms_{who.lower()}_{today.isoformat()}.vcf"
        open(os.path.join(HERE, fn), "wb").write(vcf)
        print(f"{who:<8}{len(mine):>4} deals | {len(cards):>4} vcards | {nophone} without a number "
              f"| {len(vcf)}b -> {fn}")
        if SEND:
            to = TEST_TO if TEST else addr
            subj = f"LH2 — {len(cards)} IT firm leads assigned to you ({today:%d %b %Y})"
            body = (f"{len(cards)} contacts attached as {fn} — open on your phone to save them "
                    f"all at once.")
            t, detail = gmail_sender.send(to, subj, body, [(fn, vcf, "text/vcard")])
            print(f"         sent to {to} via [{t}] {detail}", flush=True)
    if not SEND:
        print("\nnot sent — pass --send (add --test to route both to the test mailbox)")


main()
