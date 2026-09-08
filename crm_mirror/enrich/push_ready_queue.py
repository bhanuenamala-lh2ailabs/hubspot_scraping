# -*- coding: utf-8 -*-
"""Enrich + push the pre-built distressed/codebase queue to Yuktha and Lamiya.

The queue (`ready_queue_200.json`) was built ahead of time and is already:
  * asset-fit vetted  -> real pre-2024 codebase, no services-shells, no domain-reuse
  * ranked by codebase_fit desc, then Tracxn distress rank
  * deduped against HubSpot **deals** (the 2026-08-03 rule: companies/contacts don't count)
  * excluded from the LinkedIn ad audience (no double-contact)
  * acquired / IPO filtered out
  * interleaved so both callers get equal-quality leads

HARD GATE (2026-08-03): a lead is pushed ONLY if it has a valid +91 number. No exceptions.

Usage:
  python push_ready_queue.py --dry-run              # see what would go, spends nothing
  python push_ready_queue.py --target 100           # 100 each to Yuktha and Lamiya
  python push_ready_queue.py --target 100 --only Yuktha
Resumable: anything already pushed is recorded in ready_queue_pushed.json and skipped.
"""
import os, sys, json, re, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB,'.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
HS, SH = env["hubspot_key"], env["signal_hire"]
OWNERS = {"Yuktha": "96573782", "Lamiya": "96574824"}
COLD = "3992480462"; PIPE = "default"; TAG = "Distressed startups"
try: from rapidfuzz import fuzz
except Exception: fuzz = None

def hs(p, m="GET", b=None):
    d = json.dumps(b).encode() if b is not None else None
    for a in range(5):
        try:
            req = urllib.request.Request("https://api.hubapi.com"+p, data=d, method=m,
                headers={"Authorization":"Bearer "+HS,"Content-Type":"application/json"})
            with urllib.request.urlopen(req, timeout=45) as r:
                t = r.read().decode(); return r.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504) and a < 4: time.sleep(2*(a+1)); continue
            return e.code, {"err": e.read().decode()[:160]}
        except Exception:
            if a == 4: return 500, {}
            time.sleep(2)

def sh(p, b):
    req = urllib.request.Request("https://www.signalhire.com/api/v1"+p, data=json.dumps(b).encode(),
        method="POST", headers={"apikey":SH,"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read().decode())

def credits():
    try:
        req = urllib.request.Request("https://www.signalhire.com/api/v1/credits", headers={"apikey":SH})
        return json.loads(urllib.request.urlopen(req, timeout=20).read().decode())["credits"]
    except Exception: return None

def india(p):
    raw = str(p or "").strip(); d = re.sub(r"[^\d]", "", raw)
    if raw.startswith(("+1","+81","+62","+44","+65")) or (len(d) == 11 and d.startswith("1")): return ""
    if raw.startswith("+91") or (d.startswith("91") and len(d) == 12):
        d = d[-10:]; return "+91"+d if len(d) == 10 and d[0] in "23456789" else ""
    if len(d) == 10 and d[0] in "23456789": return "+91"+d
    return ""

def reveal(ident):
    if not ident: return "", ""
    try: d = sh("/candidate/search", {"items":[ident], "withoutWaterfall": True})
    except urllib.error.HTTPError as e:
        if e.code == 402: return "QUOTA", ""
        return "", ""
    except Exception: return "", ""
    res = d if isinstance(d, list) else d.get("results", [])
    ph, em = [], []
    for it in res or []:
        if isinstance(it, dict) and it.get("status") == "success":
            for c in (it.get("candidate", {}) or {}).get("contacts", []) or []:
                t = str(c.get("type","")).lower(); v = c.get("value")
                if not isinstance(v, str): continue
                if "phone" in t: ph.append(v)
                elif "email" in t and "@" in v: em.append(v)
    def _mob(v):
        d = re.sub(r"[^\d]", "", str(v or ""))[-10:]
        return len(d) == 10 and d[0] in "6789"
    mobile = next((india(x) for x in ph if india(x) and _mob(x)), "")
    return (mobile or next((india(x) for x in ph if india(x)), "")), next((x for x in em if "@" in x), "")

def find_founder(company):
    try:
        d = sh("/candidate/searchByQuery", {"currentCompany": company, "size": 6,
             "currentTitle":"Founder OR Co-Founder OR CEO OR Owner OR Managing Director OR Director"})
    except Exception: return None
    cl = (company or "").lower(); best = None; bs = 0
    for p in (d.get("profiles") or []):
        if not isinstance(p, dict): continue
        cs = 0
        for e in (p.get("experience") or []):
            c = str(e.get("company") or "").lower()
            cs = max(cs, fuzz.token_set_ratio(cl, c) if fuzz else (90 if (cl in c or c in cl) else 0))
        if cs >= 80 and cs > bs: bs = cs; best = p
    return best

def push(r, owner_id, phone, email):
    comp, dom = r["company"], r.get("domain") or ""
    coid = None
    if dom:
        s, d = hs("/crm/v3/objects/companies/search","POST",{"limit":1,"properties":["name"],
            "filterGroups":[{"filters":[{"propertyName":"domain","operator":"EQ","value":dom}]}]})
        coid = d["results"][0]["id"] if d.get("results") else None
    if not coid:
        s, d = hs("/crm/v3/objects/companies","POST",
                  {"properties":{"name":comp, **({"domain":dom} if dom else {}), "city":(r.get("city") or "")}})
        coid = d.get("id")
    # reuse an existing contact if one already has this email (avoids the duplicate-create failure)
    ctid = None
    if email:
        s, d = hs("/crm/v3/objects/contacts/search","POST",{"limit":1,"properties":["email"],
            "filterGroups":[{"filters":[{"propertyName":"email","operator":"EQ","value":email}]}]})
        ctid = d["results"][0]["id"] if d.get("results") else None
    parts = (r.get("founder") or "").split()
    cp = {"firstname":parts[0] if parts else comp, "lastname":" ".join(parts[1:3]) if len(parts)>1 else "",
          "company":comp, "phone":phone, "mobilephone":phone, "jobtitle":"Founder"}
    if email: cp["email"] = email
    if r.get("ident","").startswith("http"): cp["linkedin_url"] = r["ident"]
    if ctid: hs(f"/crm/v3/objects/contacts/{ctid}","PATCH",{"properties":{"phone":phone,"mobilephone":phone}})
    else:
        s, d = hs("/crm/v3/objects/contacts","POST",{"properties":{k:v for k,v in cp.items() if v}})
        ctid = d.get("id")
    dp = {"dealname":comp,"pipeline":PIPE,"dealstage":COLD,"hubspot_owner_id":owner_id,"poc":owner_id,
          "scraped_type":TAG,"hs_priority":"high" if r["codebase_fit"] >= 70 else "medium"}
    if dom: dp["lh2_domain"] = dom
    if r.get("ident","").startswith("http"): dp["linkedin_url"] = r["ident"]
    s, d = hs("/crm/v3/objects/deals","POST",{"properties":dp}); did = d.get("id")
    if not did: return None, None
    time.sleep(0.4)                       # let the objects index before associating
    if coid: hs(f"/crm/v4/objects/deals/{did}/associations/default/companies/{coid}","PUT")
    if ctid:
        hs(f"/crm/v4/objects/deals/{did}/associations/default/contacts/{ctid}","PUT")
        if coid: hs(f"/crm/v4/objects/contacts/{ctid}/associations/default/companies/{coid}","PUT")
    return did, ctid

def _nrm(s):
    s = (s or "").lower(); s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"(pvt|private|ltd|limited|llp|inc|technologies|technology|solutions|software|systems|labs|services|consulting|infotech|it|the)", " ", s)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()

def _sheet_worked_exclude():
    """Companies the team already called inside the tracker sheet but that were never
    created in HubSpot. Deal-based dedup cannot see them, so exclude them explicitly
    or they get called a second time. (Added 2026-08-03.)"""
    p = os.path.join(HUB, "crm_mirror", "data", "index", "sheet_worked_exclude.json")
    try: return set(json.load(open(p, encoding="utf-8")).get("names", []))
    except Exception: return set()

def main():
    dry = "--dry-run" in sys.argv; target = 100; only = None; max_credits = None
    for i,a in enumerate(sys.argv):
        if a == "--target": target = int(sys.argv[i+1])
        if a == "--only": only = sys.argv[i+1]
        if a == "--max-credits": max_credits = int(sys.argv[i+1])
    queue = json.load(open(os.path.join(HERE,"ready_queue_200.json"), encoding="utf-8"))
    SHEET_DONE = _sheet_worked_exclude()
    _before = len(queue)
    queue = [q for q in queue if _nrm(q.get("company")) not in SHEET_DONE]
    if _before != len(queue):
        print(f"  excluded {_before-len(queue)} already called in the tracker sheet", flush=True)
    logp = os.path.join(HERE,"ready_queue_pushed.json")
    log = json.load(open(logp, encoding="utf-8")) if os.path.exists(logp) else []
    done = {r.get("domain") for r in log if r.get("domain")} | {r.get("company") for r in log}
    c0 = credits()
    # --target is a TOTAL per owner, not "this run" — subtract what's already pushed
    from collections import Counter as _C
    have = _C(r.get("assign_to") for r in log)
    need = {k: max(0, target - have.get(k, 0)) for k in OWNERS if (only is None or k == only)}
    print(f"  already have -> {dict(have)} ; still needed -> {need}", flush=True)
    print(f"queue={len(queue)} | already pushed={len(log)} | credits={c0} | target={need}", flush=True)
    stats = {"no_phone":0,"quota":0}
    checked = [0]; spent_now = [0]
    for r in queue:
        # hard spend cap (checked every 10 reveals, not every row, to save API calls)
        if max_credits is not None and c0 is not None and checked[0] % 10 == 0:
            spent_now[0] = c0 - (credits() or c0)
        if max_credits is not None and spent_now[0] >= max_credits:
            print(f"  !! credit budget reached ({spent_now[0]}/{max_credits}) — stopping cleanly", flush=True); break
        who = r["assign_to"]
        if who not in need or need[who] <= 0: continue
        if r.get("domain") in done or r.get("company") in done: continue
        # 2026-08-03: the Tracxn phone column is NOT trusted — measured ~14% wrong by the team,
        # 0/10 agreement vs SignalHire, office switchboards, and foreign numbers with no country
        # code. SignalHire is the only accepted source of a number.
        phone = ""; email = r.get("email_hint") or ""
        if True:
            ph, em = reveal(r.get("ident"))
            if ph == "QUOTA":
                stats["quota"] += 1; print("  !! SignalHire quota hit — stopping cleanly", flush=True); break
            checked[0] += 1
            phone = ph; email = email or em
            if not phone:
                prof = find_founder(r["company"])
                if prof:
                    uid = prof.get("uid") or prof.get("profileUid")
                    if uid:
                        ph2, em2 = reveal(uid)
                        if ph2 == "QUOTA": stats["quota"] += 1; break
                        phone = ph2; email = email or em2
            time.sleep(0.3)
        if not phone:                       # HARD GATE
            stats["no_phone"] += 1; continue
        if dry:
            need[who] -= 1
            print(f"  READY {who:7} cb={r['codebase_fit']:3} {r['company'][:26]:26} {phone}", flush=True)
            continue
        did, ctid = push(r, OWNERS[who], phone, email)
        if not did: continue
        need[who] -= 1; done.add(r.get("domain")); done.add(r.get("company"))
        log.append({**r,"deal_id":did,"phone":phone,"email":email})
        json.dump(log, open(logp,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
        n = target - need[who]
        if n % 10 == 1: print(f"  --- {who} batch {(n//10)+1} ---", flush=True)
        print(f"  [{who} {n}] cb={r['codebase_fit']:3} {r['company'][:26]:26} {phone} deal={did}", flush=True)
        time.sleep(0.2)
    c1 = credits()
    pushed = {k: target-v for k,v in need.items()}
    print(f"\n{'DRY ' if dry else ''}pushed {pushed} | skipped-no-phone {stats['no_phone']} | credits {c0} -> {c1}")

if __name__ == "__main__":
    main()
