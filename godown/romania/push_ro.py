# -*- coding: utf-8 -*-
"""Push the enriched Romanian leads, split 50:50 between Ishpreet and Shobit.

NO +91 GATE — these are Romanian firms, so the Indian rule cannot apply. Any dialable number
qualifies; romania_number.py labels what it is so the caller knows what they are ringing.

WHAT A CALLER IS ACTUALLY GETTING, and why the deal note says so explicitly:
  * 4 leads carry a PERSONAL number revealed from the founder's LinkedIn profile
  * 25 carry the COMPANY number published on the firm's own contact page — of which 20 are
    +40 7xx, genuinely mobiles rather than switchboards, which is normal for firms this size
  * 17 have a named founder; the rest are company-level only
A company line with no name still opens differently from a founder's mobile, so the distinction
is written onto the deal rather than left for the caller to discover on the call.

Live dedup against HubSpot immediately before creating anything, as always.

Usage: python3 push_ro.py [--apply]
"""
import os, re, sys, json, time, collections, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HUB, "crm_mirror", "enrich"))
from romania_number import to_e164, classify

env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}

SRC = os.path.join(HERE, "ro50_enriched.json")
DONE = os.path.join(HERE, "pushed_ro.json")
ISHPREET, SHOBIT = "166322228", "166262056"
NAME = {ISHPREET: "Ishpreet", SHOBIT: "Shobit"}
PIPE, COLD = "default", "3992480462"
SOURCE, TAB = "Romania ( IT Services )", "romania"
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
    d = re.sub(r"\D", "", str(s or "")); return d[-9:] if len(d) >= 9 else ""


def nm(s):
    s = (s or "").lower(); s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"\b(srl|sa|ltd|limited|llc|inc|technologies|technology|solutions|software|"
               r"systems|labs|services|consulting|group|romania|digital)\b", " ", s)
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
    ph = set()
    after = None
    while True:
        b = {"limit": 200, "properties": ["phone", "mobilephone"],
             "filterGroups": [{"filters": [{"propertyName": "hs_object_id", "operator": "HAS_PROPERTY"}]}]}
        if after: b["after"] = after
        _, d = hs("/crm/v3/objects/contacts/search", "POST", b)
        for x in d.get("results", []):
            for k in ("phone", "mobilephone"):
                if d10(x["properties"].get(k)): ph.add(d10(x["properties"][k]))
        after = (d.get("paging") or {}).get("next", {}).get("after")
        if not after: break
    for s in (dom, dn, ph): s.discard("")
    return dom, dn, ph


def push(r, owner):
    parts = (r.get("person") or "").split()
    cp = {"firstname": parts[0] if parts else "", "lastname": " ".join(parts[1:]) if len(parts) > 1 else "",
          "email": r.get("email") or "", "phone": r["phone"], "mobilephone": r["phone"],
          "jobtitle": r.get("title") or "", "company": r["name"],
          "linkedin_url": r.get("linkedin") or "", "country": "Romania"}
    if not cp["firstname"] and not cp["lastname"]:
        cp["firstname"] = r["name"][:40]        # company-level lead: no named person yet
    s, d = hs("/crm/v3/objects/contacts", "POST", {"properties": {k: v for k, v in cp.items() if v}})
    if s not in (200, 201): return None, f"contact {s} {str(d)[:110]}"
    ctid = d["id"]
    note = (f'{r.get("phone_source","")}, {r.get("phone_kind") or "unclassified"}'
            f'{" | no named contact yet" if not r.get("person") else ""}')
    dp = {"dealname": r["name"], "pipeline": PIPE, "dealstage": COLD,
          "hubspot_owner_id": owner, "poc": owner, "lead_source": SOURCE,
          "source_tab": TAB, "lh2_domain": r["domain"], "description": note}
    s, d = hs("/crm/v3/objects/deals", "POST", {"properties": dp})
    if s not in (200, 201):
        dp.pop("description", None)
        s, d = hs("/crm/v3/objects/deals", "POST", {"properties": dp})
        if s not in (200, 201): return None, f"deal {s} {str(d)[:110]}"
    did = d["id"]; time.sleep(0.2)
    hs(f"/crm/v4/objects/deals/{did}/associations/default/contacts/{ctid}", "PUT")
    return did, ""


def main():
    rows = [r for r in json.load(open(SRC, encoding="utf-8")) if r.get("phone")]
    done = json.load(open(DONE, encoding="utf-8")) if os.path.exists(DONE) else {}
    rows = [r for r in rows if r["domain"] not in done]
    print(f"enriched with a phone: {len(rows) + len(done)} | already pushed {len(done)} | candidates {len(rows)}")

    dom, dn, ph = crm_keys()
    ready, skip = [], []
    for r in rows:
        why = ""
        if r["domain"].lower() in dom: why = "domain already on a deal"
        elif nm(r["name"]) in dn: why = "deal name already exists"
        elif d10(r["phone"]) in ph: why = "phone already in CRM"
        (skip if why else ready).append((r, why))
    print(f"after LIVE dedup: {len(ready)} to push, {len(skip)} skipped")
    for r, w in skip: print(f"   SKIP {r['name'][:34]:<36}{w}")

    ready.sort(key=lambda x: -x[0]["score"])
    plan, c = [], collections.Counter()
    for r, _ in ready:
        o = ISHPREET if c["Ishpreet"] <= c["Shobit"] else SHOBIT
        c[NAME[o]] += 1; plan.append((r, o))
    print(f"\nPLAN ({len(plan)}) — Ishpreet {c['Ishpreet']}, Shobit {c['Shobit']}\n")
    for r, o in plan:
        print(f'   {r["score"]:>3} {r["name"][:30]:<32}{(r.get("person") or "(company only)")[:22]:<24}'
              f'{r["phone"]:<16}{(r.get("phone_kind") or ""):<10}-> {NAME[o]}')
    if not APPLY:
        print("\nDRY RUN — nothing created. Re-run with --apply.")
        return
    ok = fail = 0
    for r, o in plan:
        did, err = push(r, o)
        if did:
            ok += 1
            done[r["domain"]] = {"deal": did, "owner": NAME[o], **{k: r.get(k, "") for k in
                                 ("name", "person", "title", "phone", "phone_kind", "phone_source",
                                  "email", "linkedin", "score", "band", "website")}}
        else:
            fail += 1; print(f'   FAIL {r["name"][:32]:<34}{err}')
        json.dump(done, open(DONE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        time.sleep(0.3)
    c2 = collections.Counter(v["owner"] for v in done.values())
    print(f"\npushed {ok}, failed {fail} | total {len(done)}  Ishpreet {c2['Ishpreet']}  Shobit {c2['Shobit']}")


main()
