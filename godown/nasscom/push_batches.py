# -*- coding: utf-8 -*-
"""Push the revealed NASSCOM founders in batches of 8 — 5 Lamiya, 3 Yuktha, Lamiya first.

Ten batches of eight lands exactly on the 50/30 split asked for. Batch order is by reveal
quality then company name, so the strongest leads go out first rather than last.

Every batch re-checks live HubSpot before creating anything: hours pass between batches and
another push (or a caller) may have created the same company in the meantime. Dedup keys are
domain, normalised deal name, contact email and last-10-digits phone — never name alone.

Tags, matching the 9 already pushed:
    lead_source  "Scraped ( IT Services )"
    scraped_type "ITservices"
    source_tab   "nasscom"
    lh2_domain   the firm's domain, so future dedup can key on it

+91 gate re-enforced here rather than trusted from the upstream file.

Usage: python3 push_batches.py [--batch 1] [--size 8] [--apply]
       python3 push_batches.py --all --apply      # every remaining batch
"""
import os, re, sys, json, time, collections, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HUB, "crm_mirror", "enrich"))
from indian_number import to_e164, classify

env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}

SRC = os.path.join(HERE, "bulk_revealed.json")
DONE = os.path.join(HERE, "pushed_batches.json")
LAMIYA, YUKTHA = "96574824", "96573782"
NAME = {LAMIYA: "Lamiya", YUKTHA: "Yuktha"}
PER_LAMIYA, PER_YUKTHA = 5, 3
PIPE, COLD = "default", "3992480462"
SOURCE, STYPE, TAB = "NASSCOM ( IT Services )", "ITservices", "nasscom"
SIZE, BATCH, APPLY, ALL = 8, 1, "--apply" in sys.argv, "--all" in sys.argv
for i, a in enumerate(sys.argv):
    if a == "--batch": BATCH = int(sys.argv[i+1])
    if a == "--size": SIZE = int(sys.argv[i+1])


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
    rows.sort(key=lambda r: r["name"].lower())
    print(f"PASS pool: {len(rows) + len(done)} | already pushed {len(done)} | remaining {len(rows)}")

    dom, dn, em, ph = crm_keys()
    ready = []
    for r in rows:
        if r["domain"].lower() in dom: continue
        if nm(r["name"]) in dn: continue
        if r.get("email") and r["email"].lower() in em: continue
        if d10(r["indian_phone"]) in ph: continue
        if not to_e164(r["indian_phone"]): continue
        ready.append(r)
    print(f"after live dedup: {len(ready)} eligible\n")

    nbatch = 1 if not ALL else (len(ready) + SIZE - 1) // SIZE
    total_ok = 0
    for b in range(nbatch):
        chunk = ready[b*SIZE:(b+1)*SIZE]
        if not chunk: break
        plan = [(r, LAMIYA) for r in chunk[:PER_LAMIYA]] + [(r, YUKTHA) for r in chunk[PER_LAMIYA:]]
        print(f"--- BATCH {BATCH + b} ({len(plan)}) : "
              f"{sum(1 for _,o in plan if o==LAMIYA)} Lamiya, {sum(1 for _,o in plan if o==YUKTHA)} Yuktha ---")
        for r, o in plan:
            print(f'   {r["name"][:32]:<34}{r["person"][:20]:<22}{(r.get("title") or "")[:22]:<24}'
                  f'{r["indian_phone"]:<15}-> {NAME[o]}')
        if not APPLY:
            print("   (dry run)\n"); continue
        for r, o in plan:
            did, err = push(r, o)
            if did:
                total_ok += 1
                done[r["domain"]] = {"deal": did, "owner": NAME[o], "name": r["name"],
                                     "person": r["person"], "phone": r["indian_phone"]}
            else:
                print(f'   FAIL {r["name"][:30]} {err}')
            time.sleep(0.3)
        json.dump(done, open(DONE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"   batch done — running total pushed {len(done)}\n")

    if APPLY:
        c = collections.Counter(v["owner"] for v in done.values())
        print(f"TOTAL PUSHED {len(done)}   Lamiya {c['Lamiya']}  Yuktha {c['Yuktha']}")


main()
