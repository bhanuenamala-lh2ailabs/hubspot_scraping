# -*- coding: utf-8 -*-
"""Push the enriched Priority/Secondary NASSCOM firms, split 50:50 Lamiya / Yuktha.

Source is the graded ranking, so every firm here cleared: builds software, pre-2024 evidence,
not a giant, not a captive, and survived the disqualifier caps. Enrichment added a senior contact
and a +91 number.

LIVE DEDUP IS NOT OPTIONAL HERE. The ranking's `already_in_hubspot` flag was built from the batch
push log and missed the nine pushed earlier by a different script — so seven firms in this queue
are already in the CRM. Checking HubSpot itself immediately before creating anything is what
catches that; trusting the file would have created duplicate deals on live leads.

Alternating owner rather than blocking, so an interrupted run still leaves the split even.

Usage: python3 push_144.py [--apply]
"""
import os, re, sys, json, time, collections, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HUB, "crm_mirror", "enrich"))
from indian_number import to_e164, classify

env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}

SRC = os.path.join(HERE, "nasscom144_revealed.json")
DONE = os.path.join(HERE, "pushed_144.json")
LAMIYA, YUKTHA = "96574824", "96573782"
NAME = {LAMIYA: "Lamiya", YUKTHA: "Yuktha"}
PIPE, COLD = "default", "3992480462"
SOURCE, STYPE, TAB = "NASSCOM ( IT Services )", "ITservices", "nasscom"
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


def d10(s):
    d = re.sub(r"\D", "", str(s or "")); return d[-10:] if len(d) >= 10 else ""


def nm(s):
    s = (s or "").lower(); s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"\b(pvt|private|ltd|limited|llp|inc|technologies|technology|solutions|software|"
               r"systems|labs|services|consulting|infotech|it|the|india|global|group)\b", " ", s)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


def crm_keys():
    dom, dn = set(), set()
    after = None
    while True:
        b = {"limit": 200, "properties": ["dealname", "lh2_domain"], "filterGroups": []}
        if after: b["after"] = after
        _, d = hs("/crm/v3/objects/deals/search", "POST", b)
        for x in d.get("results", []):
            p = x["properties"]
            if p.get("lh2_domain"): dom.add(p["lh2_domain"].lower().strip())
            if p.get("dealname"): dn.add(nm(p["dealname"]))
        after = (d.get("paging") or {}).get("next", {}).get("after")
        if not after: break
    em, ph = set(), set()
    after = None
    while True:
        b = {"limit": 200, "properties": ["email", "phone", "mobilephone"],
             "filterGroups": [{"filters": [{"propertyName": "hs_object_id", "operator": "HAS_PROPERTY"}]}]}
        if after: b["after"] = after
        _, d = hs("/crm/v3/objects/contacts/search", "POST", b)
        for x in d.get("results", []):
            p = x["properties"]
            if p.get("email"): em.add(p["email"].strip().lower())
            for k in ("phone", "mobilephone"):
                if d10(p.get(k)): ph.add(d10(p[k]))
        after = (d.get("paging") or {}).get("next", {}).get("after")
        if not after: break
    for s in (dom, dn, em, ph): s.discard("")
    return dom, dn, em, ph


def push(r, owner):
    parts = (r.get("person") or "").split()
    cp = {"firstname": parts[0] if parts else "", "lastname": " ".join(parts[1:]) if len(parts) > 1 else "",
          "email": r.get("email") or "", "phone": r["indian_phone"], "mobilephone": r["indian_phone"],
          "jobtitle": r.get("title") or "", "company": r["name"], "linkedin_url": r.get("linkedin") or ""}
    s, d = hs("/crm/v3/objects/contacts", "POST", {"properties": {k: v for k, v in cp.items() if v}})
    if s not in (200, 201): return None, f"contact {s} {str(d)[:110]}"
    ctid = d["id"]
    dp = {"dealname": r["name"], "pipeline": PIPE, "dealstage": COLD,
          "hubspot_owner_id": owner, "poc": owner, "lead_source": SOURCE,
          "scraped_type": STYPE, "source_tab": TAB, "lh2_domain": r["domain"]}
    s, d = hs("/crm/v3/objects/deals", "POST", {"properties": dp})
    if s not in (200, 201): return None, f"deal {s} {str(d)[:110]}"
    did = d["id"]; time.sleep(0.2)
    hs(f"/crm/v4/objects/deals/{did}/associations/default/contacts/{ctid}", "PUT")
    return did, ""


def main():
    rows = [r for r in json.load(open(SRC, encoding="utf-8")) if r.get("gate") == "PASS"]
    done = json.load(open(DONE, encoding="utf-8")) if os.path.exists(DONE) else {}
    rows = [r for r in rows if r["domain"] not in done]
    print(f"revealed & passing: {len(rows) + len(done)} | already pushed {len(done)} | candidates {len(rows)}")

    dom, dn, em, ph = crm_keys()
    ready, skip = [], []
    for r in rows:
        why = ""
        if not to_e164(r.get("indian_phone") or ""): why = "no valid +91"
        elif r["domain"].lower() in dom: why = "domain already on a deal"
        elif nm(r["name"]) in dn: why = "deal name already exists"
        elif r.get("email") and r["email"].lower() in em: why = "contact email already in CRM"
        elif d10(r["indian_phone"]) in ph: why = "phone already in CRM"
        (skip if why else ready).append((r, why))
    print(f"\nafter LIVE dedup: {len(ready)} to push, {len(skip)} skipped")
    for r, w in skip: print(f"   SKIP {r['name'][:36]:<38}{w}")

    ready.sort(key=lambda x: -(x[0].get("score") or 0))
    # Balance against the LIVE Cold Call books, not just this batch: Lamiya was already 12 ahead
    # from the earlier 5:3 split, so an even split here would have preserved that gap.
    import json as _j, os as _o
    live = {"Lamiya": 0, "Yuktha": 0}
    try:
        live = _j.load(open(_o.path.join(HERE, "cc_now.json"), encoding="utf-8"))
    except Exception:
        pass
    plan, c = [], collections.Counter(live)
    for r, _ in ready:
        o = LAMIYA if c[NAME[LAMIYA]] <= c[NAME[YUKTHA]] else YUKTHA
        c[NAME[o]] += 1; plan.append((r, o))
    print(f"\nPLAN ({len(plan)}) — 50:50\n")
    for r, o in plan:
        print(f'   {r["name"][:34]:<36}{r["person"][:20]:<22}{(r.get("title") or "")[:24]:<26}'
              f'{r["indian_phone"]:<15}-> {NAME[o]}')
    print(f"\nresulting split: Lamiya {c['Lamiya']}  Yuktha {c['Yuktha']}")

    if not APPLY:
        print("\nDRY RUN — nothing created. Re-run with --apply.")
        return
    ok = fail = 0
    for r, o in plan:
        did, err = push(r, o)
        if did:
            ok += 1
            done[r["domain"]] = {"deal": did, "owner": NAME[o], "name": r["name"],
                                 "person": r["person"], "title": r.get("title", ""),
                                 "phone": r["indian_phone"], "email": r.get("email", ""),
                                 "linkedin": r.get("linkedin", "")}
            print(f'   pushed {r["name"][:34]:<36}{NAME[o]:<8}deal {did}')
        else:
            fail += 1; print(f'   FAIL   {r["name"][:34]:<36}{err}')
        json.dump(done, open(DONE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        time.sleep(0.3)
    c2 = collections.Counter(v["owner"] for v in done.values())
    print(f"\npushed {ok}, failed {fail}  |  total {len(done)}  Lamiya {c2['Lamiya']}  Yuktha {c2['Yuktha']}")


main()
