# -*- coding: utf-8 -*-
"""Push the revealed, +91-passing NASSCOM founders to Lamiya on the Scraped pipeline.

Identification, using fields that already exist rather than inventing one:
    lead_source  "Scraped ( IT Services )"   the existing option for this kind of lead
    scraped_type "ITservices"                the existing radio value
    source_tab   "nasscom"                   free-text source marker; already holds "goodfirms"
                                             for the earlier directory, so NASSCOM leads stay
                                             separable from GoodFirms ones forever
    lh2_domain   the firm's domain           so future dedup can key on domain, which is the
                                             hardest key we have — the SalesNav pass could not
                                             do this and had to fall back to company name

Deal name is the COMPANY, not the person — the company is the pointer for a codebase acquisition.

Dedup runs live against HubSpot on domain, deal name, contact email and last-10-digits phone
immediately before creating anything, because hours have passed since these were scored.

+91 gate enforced: only rows whose reveal produced an Indian number are eligible, and that is
re-checked here rather than trusted from the upstream file.

Usage: python3 push_above20.py [--apply] [--owner lamiya|yuktha|split]
"""
import os, re, sys, json, time, collections, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HUB, "crm_mirror", "enrich"))
from indian_number import to_e164, classify

env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}

SRC = os.path.join(HERE, "above20_revealed.json")
LAMIYA, YUKTHA = "96574824", "96573782"
NAME = {LAMIYA: "Lamiya", YUKTHA: "Yuktha"}
PIPE, COLD = "default", "3992480462"           # Scraped / Cold Call
SOURCE, STYPE, TAB = "Scraped ( IT Services )", "ITservices", "nasscom"
APPLY = "--apply" in sys.argv
MODE = "lamiya"
for i, a in enumerate(sys.argv):
    if a == "--owner": MODE = sys.argv[i+1].lower()


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
    """Live dedup keys. Deals give domain+name; contacts give email+phone."""
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
    dom.discard(""); dn.discard(""); em.discard(""); ph.discard("")
    return dom, dn, em, ph


def push(r, owner):
    parts = (r.get("person") or "").split()
    first = parts[0] if parts else ""
    last = " ".join(parts[1:]) if len(parts) > 1 else ""
    cp = {"firstname": first, "lastname": last, "email": r.get("email") or "",
          "phone": r["indian_phone"], "mobilephone": r["indian_phone"],
          "jobtitle": r.get("title") or "", "company": r["name"],
          "linkedin_url": r.get("linkedin_confirmed") or r.get("linkedin") or "",
          "website": r.get("website") or ""}
    s, d = hs("/crm/v3/objects/contacts", "POST", {"properties": {k: v for k, v in cp.items() if v}})
    if s not in (200, 201): return None, f"contact {s} {str(d)[:120]}"
    ctid = d["id"]
    dp = {"dealname": r["name"], "pipeline": PIPE, "dealstage": COLD,
          "hubspot_owner_id": owner, "poc": owner,
          "lead_source": SOURCE, "scraped_type": STYPE, "source_tab": TAB,
          "lh2_domain": r["domain"]}
    s, d = hs("/crm/v3/objects/deals", "POST", {"properties": dp})
    if s not in (200, 201): return None, f"deal {s} {str(d)[:120]}"
    did = d["id"]; time.sleep(0.2)
    hs(f"/crm/v4/objects/deals/{did}/associations/default/contacts/{ctid}", "PUT")
    return did, ""


def main():
    rows = json.load(open(SRC, encoding="utf-8"))
    elig = [r for r in rows if to_e164(r.get("indian_phone") or "")]
    print(f"revealed {len(rows)} | pass the +91 gate {len(elig)}")
    for k, v in collections.Counter(r.get("gate", "?") for r in rows).most_common():
        print(f"   {v:>4}  {k}")

    dom, dn, em, ph = crm_keys()
    print(f"\nlive CRM: {len(dom)} deal domains, {len(dn)} deal names, {len(em)} emails, {len(ph)} phones")
    ready, skip = [], []
    for r in elig:
        why = ""
        if r["domain"].lower() in dom: why = "domain already on a deal"
        elif nm(r["name"]) in dn: why = "deal name already exists"
        elif r.get("email") and r["email"].lower() in em: why = "contact email already in CRM"
        elif d10(r["indian_phone"]) in ph: why = "phone already in CRM"
        (skip if why else ready).append((r, why))
    print(f"\nafter live dedup: {len(ready)} to push, {len(skip)} skipped")
    for r, w in skip: print(f"   SKIP {r['name'][:34]:<36}{w}")

    plan = []
    if MODE == "split":
        c = collections.Counter()
        for r, _ in sorted(ready, key=lambda x: -x[0]["score"]):
            o = LAMIYA if c[LAMIYA] <= c[YUKTHA] else YUKTHA
            c[o] += 1; plan.append((r, o))
    else:
        o = YUKTHA if MODE == "yuktha" else LAMIYA
        plan = [(r, o) for r, _ in sorted(ready, key=lambda x: -x[0]["score"])]

    print(f"\nplan ({len(plan)}) -> {'50:50' if MODE=='split' else NAME[plan[0][1]] if plan else '-'}")
    print(f"tags: lead_source='{SOURCE}'  scraped_type='{STYPE}'  source_tab='{TAB}'\n")
    for r, o in plan:
        print(f'   {r["score"]:>3}  {r["name"][:32]:<34}{r["person"][:20]:<22}'
              f'{r["indian_phone"]:<16}{classify(r["indian_phone"]):<9}-> {NAME[o]}')

    if not APPLY:
        print("\nDRY RUN — nothing created. Re-run with --apply.")
        return
    ok = fail = 0
    for r, o in plan:
        did, err = push(r, o)
        if did: ok += 1; print(f"   pushed {r['name'][:32]:<34}deal {did}  {NAME[o]}")
        else: fail += 1; print(f"   FAIL   {r['name'][:32]:<34}{err}")
        time.sleep(0.3)
    print(f"\npushed {ok}, failed {fail}")


main()
