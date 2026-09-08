# -*- coding: utf-8 -*-
"""Reveal the resolved deadpool-wave founders on SignalHire, gate them, push to HubSpot.

Source  : deadpool_resolved.json (built by resolve_deadpool_founders.py)
Pipeline: Scraped (default) / stage Cold Call / scraped_type = "Distressed startups"
Owners  : split round-robin between Ishpreet and Shobit, whole companies kept together
          so two callers never phone the same dead startup.

HARD GATE — a lead without a valid Indian number does not go to HubSpot. Numbers come
from SignalHire ONLY (the research table has none) and run through indian_number.py;
mobile beats landline because a landline at a dead company reaches nobody.

Resumable: every push is appended to pushed_deadpool.json and skipped on re-run.
Dry and --limit runs never write the pushed log.

Usage:
  python push_deadpool.py --dry-run            # reveal + gate, show what would go
  python push_deadpool.py --batch 10           # push, 10 at a time
  python push_deadpool.py --max-credits 150
"""
import os, re, sys, json, time, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indian_number import to_e164, classify, pick_best

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(HUB, "crm_mirror", "sources", "deadpool_waves")
LOG = os.path.join(HERE, "pushed_deadpool.json")
REVEALS = os.path.join(HERE, "deadpool_reveals.json")
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
HS = env["hubspot_key"]; SH = env["signal_hire"]

COLDCALL = "3992480462"; PIPELINE = "default"; TAG = "Distressed startups"
OWNERS = [("166322228", "Ishpreet Sood"), ("166262056", "Shobit Gupta")]

def norm(s): return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", (s or "").lower())).strip()
def base(c): return re.sub(r"\s*\([^)]*\)\s*$", "", c).strip()

def hs(path, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    for a in range(5):
        try:
            req = urllib.request.Request("https://api.hubapi.com" + path, data=data, method=method,
                headers={"Authorization": "Bearer " + HS, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=45) as r:
                t = r.read().decode(); return r.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504) and a < 4: time.sleep(2*(a+1)); continue
            return e.code, {"raw": e.read().decode()[:250]}
        except Exception:
            if a == 4: raise
            time.sleep(2)

def credits():
    try:
        r = urllib.request.Request("https://www.signalhire.com/api/v1/credits", headers={"apikey": SH})
        return json.loads(urllib.request.urlopen(r, timeout=30).read().decode()).get("credits", 0)
    except Exception: return -1

def reveal(uid):
    """-> {phones:[], emails:[], linkedin:str}. Cached re-reveals are free."""
    req = urllib.request.Request("https://www.signalhire.com/api/v1/candidate/search",
        data=json.dumps({"items": [uid], "withoutWaterfall": True}).encode(), method="POST",
        headers={"apikey": SH, "Content-Type": "application/json"})
    for a in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90) as r: d = json.loads(r.read().decode())
            break
        except urllib.error.HTTPError as e:
            if e.code == 402: return {"quota": True}
            if e.code in (429, 502, 503, 504) and a < 2: time.sleep(4*(a+1)); continue
            return {}
        except Exception:
            if a < 2: time.sleep(3); continue
            return {}
    else: return {}
    res = d if isinstance(d, list) else d.get("results", [])
    ph, em, li = [], [], ""
    for it in res or []:
        if not (isinstance(it, dict) and it.get("status") == "success"): continue
        cand = it.get("candidate") or {}
        for s in cand.get("social") or []:
            l = s.get("link") or ""
            if "linkedin.com/in/" in l and not li: li = l
        for c in cand.get("contacts") or []:
            t = str(c.get("type", "")).lower(); v = c.get("value")
            if not isinstance(v, str): continue
            if "phone" in t: ph.append(v)
            elif "email" in t and "@" in v: em.append(v)
    return {"phones": ph, "emails": em, "linkedin": li}

# ---------------- build the candidate list ----------------
def candidates():
    st = json.load(open(os.path.join(HERE, "deadpool_resolved.json"), encoding="utf-8"))
    q = json.load(open(os.path.join(SRC, "deadpool_queue.json"), encoding="utf-8"))
    meta = {c["company"]: c for c in q["companies"]}
    out = []
    for key, p in st["people"].items():                       # named founders
        if p["verify"] not in ("verified_company", "unique_name") or not p.get("hit"): continue
        out.append({"company": p["company"], "display": p["display_company"], "wave": p["wave"],
                    "name": p["hit"]["full_name"], "uid": p["hit"]["uid"],
                    "title": p["hit"].get("title_at_company") or "Founder",
                    "current": p["hit"].get("current", ""), "location": p["hit"].get("location", ""),
                    "shutdown": p["shutdown"], "funding": p["funding_raised"], "status": p["status"],
                    "confidence": p["verify"], "origin": "named"})
    for comp, v in st["companies"].items():                   # founders recovered for "various" rows
        m = meta.get(comp, {})
        for h in v["hits"]:
            out.append({"company": comp, "display": v["display"], "wave": v["wave"],
                        "name": h["full_name"], "uid": h["uid"],
                        "title": h.get("title_at_company") or "Founder",
                        "current": h.get("current", ""), "location": h.get("location", ""),
                        "shutdown": v["shutdown"], "funding": v["funding_raised"], "status": v["status"],
                        "confidence": "title_at_company", "origin": "recovered"})
    seen = set(); uniq = []
    for c in out:
        if c["uid"] in seen: continue
        seen.add(c["uid"]); uniq.append(c)
    return uniq

def main():
    dry = "--dry-run" in sys.argv
    batch = int(sys.argv[sys.argv.index("--batch")+1]) if "--batch" in sys.argv else 10
    limit = int(sys.argv[sys.argv.index("--limit")+1]) if "--limit" in sys.argv else 10**9
    maxcr = int(sys.argv[sys.argv.index("--max-credits")+1]) if "--max-credits" in sys.argv else 10**9

    cands = candidates()
    done = json.load(open(LOG, encoding="utf-8")) if os.path.exists(LOG) else []
    pushed_uid = {r["uid"] for r in done}
    cache = json.load(open(REVEALS, encoding="utf-8")) if os.path.exists(REVEALS) else {}

    # dedup against every existing HubSpot deal name (a deal is the dedup unit)
    dn = json.load(open(os.path.join(HUB, "crm_mirror", "data", "index", "deal_names.json"), encoding="utf-8"))
    def has_deal(disp):
        k = norm(base(disp))
        return k in dn or any(kk and (kk == k or (len(k) > 5 and k in kk)) for kk in dn)

    c0 = credits(); print(f"SignalHire credits: {c0}")
    cands = [c for c in cands if c["uid"] not in pushed_uid]
    skipped_dup = [c for c in cands if has_deal(c["display"])]
    cands = [c for c in cands if not has_deal(c["display"])]
    print(f"candidates {len(cands)} (already-in-HubSpot skipped: {len(skipped_dup)}) | already pushed {len(done)}\n")

    # ---- reveal + gate ----
    ready, rejected, fresh = [], [], 0
    for i, c in enumerate(cands[:limit], 1):
        if c["uid"] in cache:
            r = cache[c["uid"]]
        else:
            if fresh and fresh % 10 == 0 and (c0 - credits()) >= maxcr:
                print(f"  !! credit ceiling {maxcr} reached — stopping reveals"); break
            fresh += 1
            r = reveal(c["uid"])
            if r.get("quota"):
                print("  !! SignalHire quota hit — stopping reveals"); break
            cache[c["uid"]] = r
            json.dump(cache, open(REVEALS, "w", encoding="utf-8"), indent=0)
            time.sleep(0.8)
        phone = pick_best(r.get("phones") or [])
        kind = classify(phone) if phone else ""
        email = next((e for e in (r.get("emails") or []) if "@" in e), "")
        rec = {**c, "phone": phone, "phone_kind": kind, "email": email,
               "linkedin": r.get("linkedin", ""), "all_phones": r.get("phones", [])}
        (ready if phone else rejected).append(rec)
        if i % 20 == 0: print(f"  ...revealed {i}/{min(len(cands),limit)}", flush=True)

    print(f"\nrevealed {len(ready)+len(rejected)} | PASS gate {len(ready)} | REJECTED (no +91) {len(rejected)}")
    mob = sum(1 for r in ready if r["phone_kind"] == "mobile")
    print(f"  of the passing: {mob} mobile, {len(ready)-mob} landline")
    json.dump(rejected, open(os.path.join(HERE, "deadpool_no_indian_number.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # ---- assign: whole companies to one owner, alternating ----
    by_co = {}
    for r in ready: by_co.setdefault(r["display"], []).append(r)
    order = sorted(by_co, key=lambda k: (-sum(1 for x in by_co[k] if x["phone_kind"] == "mobile"), k))
    for i, co in enumerate(order):
        oid, onm = OWNERS[i % 2]
        for r in by_co[co]: r["owner"], r["owner_name"] = oid, onm

    if dry:
        print("\n--- DRY RUN — would push ---")
        for i, co in enumerate(order):
            rs = by_co[co]
            print(f"  {rs[0]['owner_name'][:9]:10} {co[:30]:32} " +
                  "; ".join(f"{r['name'][:20]} {r['phone']}({r['phone_kind'][:3]})" for r in rs))
        for oid, onm in OWNERS:
            print(f"  => {onm}: {sum(1 for r in ready if r['owner']==oid)} contacts / "
                  f"{sum(1 for co in order if by_co[co][0]['owner']==oid)} companies")
        return

    # ---- push ----
    n = 0
    for i, co in enumerate(order):
        rs = by_co[co]
        s, d = hs("/crm/v3/objects/companies/search", "POST", {"limit": 1, "properties": ["name"],
            "filterGroups": [{"filters": [{"propertyName": "name", "operator": "EQ", "value": base(co)}]}]})
        coid = d["results"][0]["id"] if d.get("results") else None
        if not coid:
            s, d = hs("/crm/v3/objects/companies", "POST", {"properties": {"name": base(co)}})
            coid = d.get("id")
        r0 = rs[0]
        dprops = {"dealname": base(co), "pipeline": PIPELINE, "dealstage": COLDCALL,
                  "hubspot_owner_id": r0["owner"], "poc": r0["owner"], "scraped_type": TAG}
        s, d = hs("/crm/v3/objects/deals", "POST", {"properties": dprops})
        did = d.get("id")
        if not did: print(f"  ERR deal {co}: {d}", flush=True); continue
        time.sleep(0.3)
        if coid: hs(f"/crm/v4/objects/deals/{did}/associations/default/companies/{coid}", "PUT")
        for r in rs:
            nm = r["name"].split()
            cp = {"firstname": nm[0] if nm else base(co), "lastname": " ".join(nm[1:]) if len(nm) > 1 else "",
                  "company": base(co), "jobtitle": r["title"][:100],
                  "phone": r["phone"], "mobilephone": r["phone"] if r["phone_kind"] == "mobile" else ""}
            if r["email"]: cp["email"] = r["email"]
            if r["linkedin"]: cp["linkedin_url"] = r["linkedin"]
            ctid = None
            if r["email"]:
                s, d = hs("/crm/v3/objects/contacts/search", "POST", {"limit": 1, "properties": ["email"],
                    "filterGroups": [{"filters": [{"propertyName": "email", "operator": "EQ", "value": r["email"]}]}]})
                ctid = d["results"][0]["id"] if d.get("results") else None
            if ctid: hs(f"/crm/v3/objects/contacts/{ctid}", "PATCH", {"properties": {k: v for k, v in cp.items() if v}})
            else:
                s, d = hs("/crm/v3/objects/contacts", "POST", {"properties": {k: v for k, v in cp.items() if v}})
                ctid = d.get("id")
            if ctid:
                hs(f"/crm/v4/objects/deals/{did}/associations/default/contacts/{ctid}", "PUT")
                if coid: hs(f"/crm/v4/objects/contacts/{ctid}/associations/default/companies/{coid}", "PUT")
            r.update({"deal_id": did, "company_id": coid, "contact_id": ctid})
            done.append(r)
        n += 1
        print(f"  [{n:>2}] {r0['owner_name'][:9]:10} {base(co)[:26]:28} deal={did} "
              f"contacts={len(rs)} | " + "; ".join(f"{r['name'][:16]} {r['phone']}" for r in rs), flush=True)
        json.dump(done, open(LOG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        if n % batch == 0:
            print(f"  --- batch of {batch} done ({n}/{len(order)}) ---", flush=True); time.sleep(1.5)

    print(f"\nPUSHED {n} companies / {sum(len(by_co[c]) for c in order)} contacts")
    for oid, onm in OWNERS:
        print(f"  {onm}: {sum(1 for r in ready if r.get('owner')==oid)} contacts")
    print(f"credits: {c0} -> {credits()}")

if __name__ == "__main__":
    main()
