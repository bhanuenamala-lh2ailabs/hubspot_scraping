# -*- coding: utf-8 -*-
"""Enrich net-new IT-services firms and push CALLABLE ones to a caller, in batches.

Implements the 2026-W31 algorithm:
  priority 1: GoodFirms band `250 - 999`   (ULR 74% vs 55%)
  priority 2: band `50 - 249` in the top-10 cities by funnel depth
  + SignalHire headcount pre-check (search `total` >= 50) — catches the firms
    GoodFirms mislabels (6/8 in validation)
  + only push if a real +91 phone was revealed (callable)

Costs: 1 SEARCH per company (quota-limited) + 1 CREDIT per successful reveal.

Usage: python enrich_and_push_it.py --owner <id> --target 60 [--batch 10] [--dry-run]
"""
import os, sys, json, re, time, sqlite3, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB,'.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
HS, SH = env["hubspot_key"], env["signal_hire"]
COLD = "3992480462"; PIPE = "default"; TAG = "ITservices"
TOP_CITIES = ("mohali","surat","chennai","indore","gurgaon","bengaluru","mumbai","ahmedabad","kolkata","coimbatore")
MIN_HC = 50
try: from rapidfuzz import fuzz
except Exception: fuzz = None

def hs(path, method="GET", body=None):
    url = "https://api.hubapi.com" + path
    data = json.dumps(body).encode() if body is not None else None
    for a in range(5):
        try:
            req = urllib.request.Request(url, data=data, method=method,
                headers={"Authorization":"Bearer "+HS,"Content-Type":"application/json"})
            with urllib.request.urlopen(req, timeout=45) as r:
                t = r.read().decode(); return r.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504) and a < 4: time.sleep(2*(a+1)); continue
            return e.code, {"raw": e.read().decode()[:160]}
        except Exception:
            if a == 4: raise
            time.sleep(2)

def sh_post(path, body, timeout=60):
    req = urllib.request.Request("https://www.signalhire.com/api/v1"+path, data=json.dumps(body).encode(),
        method="POST", headers={"apikey":SH,"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read().decode())

def credits():
    try:
        req = urllib.request.Request("https://www.signalhire.com/api/v1/credits", headers={"apikey":SH})
        return json.loads(urllib.request.urlopen(req, timeout=20).read().decode()).get("credits")
    except Exception: return None

FOUNDER_TITLES = ("Founder OR Co-Founder OR Cofounder OR CEO OR Owner OR Managing Director OR "
                  "Director OR Proprietor OR Partner")
def sh_company(company):
    """One search -> (headcount_proxy, best_founder_profile). Search quota, no credits."""
    try:
        d = sh_post("/candidate/searchByQuery", {"currentCompany": company, "size": 1})
        total = d.get("total")
    except urllib.error.HTTPError as e:
        return ("QUOTA" if e.code == 402 else None), None
    except Exception:
        return None, None
    if total is None: return None, None
    if total < MIN_HC: return total, None          # headcount pre-check failed -> don't spend more
    try:
        d2 = sh_post("/candidate/searchByQuery",
                     {"currentCompany": company, "currentTitle": FOUNDER_TITLES, "size": 6})
    except Exception:
        return total, None
    cl = company.lower(); best = None; bs = 0
    for p in (d2.get("profiles") or []):
        if not isinstance(p, dict): continue
        cs = 0
        for e in (p.get("experience") or []):
            c = str(e.get("company") or "").lower()
            cs = max(cs, fuzz.token_set_ratio(cl, c) if fuzz else (90 if (cl in c or c in cl) else 0))
        if cs >= 82 and cs > bs: bs = cs; best = p
    return total, best

def india_phone(p):
    raw = str(p or "").strip(); d = re.sub(r"[^\d]", "", raw)
    if raw.startswith("+1") or (len(d) == 11 and d.startswith("1")): return ""
    if raw.startswith("+91") or (d.startswith("91") and len(d) == 12):
        d = d[-10:]; return "+91"+d if len(d) == 10 and d[0] in "23456789" else ""
    if len(d) == 10 and d[0] in "23456789": return "+91"+d
    return ""

def sh_reveal(uid):
    """1 credit on success. -> (phone, email)"""
    try:
        d = sh_post("/candidate/search", {"items":[uid], "withoutWaterfall": True})
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
    return (next((india_phone(x) for x in ph if india_phone(x)), ""),
            next((x for x in em if "@" in x), ""))

def nm(s):
    s = (s or "").lower(); s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"\b(pvt|private|ltd|limited|llp|inc|technologies|technology|solutions|software|systems|labs|services|consulting|infotech|it|the)\b", " ", s)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()

def _sheet_worked_exclude():
    """Companies the team already called inside the tracker sheet but that were never
    created in HubSpot. Deal-based dedup cannot see them, so exclude them explicitly
    or they get called a second time. (Added 2026-08-03.)"""
    p = os.path.join(HUB, "crm_mirror", "data", "index", "sheet_worked_exclude.json")
    try: return set(json.load(open(p, encoding="utf-8")).get("names", []))
    except Exception: return set()

def candidates():
    # DEDUP RULE (2026-08-03): key on DEALS only. A company/contact record without a deal is
    # NOT a worked lead — treating it as one silently hid 4 valid leads (9stacks, Singularity
    # Automation, Bric Spaces, Logipe). hubspot_index.json is built from deals only.
    idx = json.load(open(os.path.join(HUB,"analysis","weekly","_data","hubspot_index.json"), encoding="utf-8"))
    HDOM, HNAME = set(idx["domains"]), set(idx["names"])
    SHEET_DONE = _sheet_worked_exclude()
    done = set()
    p = os.path.join(HERE, "enriched_push_log.json")
    if os.path.exists(p):
        for r in json.load(open(p, encoding="utf-8")): done.add(r["domain"])
    db = sqlite3.connect(os.path.join(HUB,"lh2-pipeline","data","pipeline.sqlite")); db.row_factory = sqlite3.Row
    rows = db.execute("SELECT domain,company_name,city,size_source,founded_year FROM companies WHERE gate_pass=1").fetchall()
    out = []
    for r in rows:
        d = (r["domain"] or "").lower()
        if not d or d in HDOM or d in done or nm(r["company_name"]) in HNAME: continue
        if nm(r["company_name"]) in SHEET_DONE: continue   # already called in the tracker sheet
        band = (r["size_source"] or "").strip()
        city = (r["city"] or "").lower()
        pri = 1 if band == "250 - 999" else (2 if (band == "50 - 249" and any(t in city for t in TOP_CITIES)) else 3)
        if pri == 3: continue
        out.append({"domain":d,"company":r["company_name"],"city":r["city"],"band":band,
                    "founded":r["founded_year"],"pri":pri})
    out.sort(key=lambda x: x["pri"])
    return out

def push(rec, owner):
    dom, comp = rec["domain"], rec["company"]
    s, d = hs("/crm/v3/objects/companies/search","POST",{"limit":1,"properties":["name"],
        "filterGroups":[{"filters":[{"propertyName":"domain","operator":"EQ","value":dom}]}]})
    coid = d["results"][0]["id"] if d.get("results") else None
    if not coid:
        s, d = hs("/crm/v3/objects/companies","POST",
                  {"properties":{"name":comp,"domain":dom,"city":(rec.get("city") or "").split(",")[0]}})
        coid = d.get("id")
    parts = (rec["founder"] or "").split()
    cp = {"firstname":parts[0] if parts else comp, "lastname":" ".join(parts[1:]) if len(parts)>1 else "",
          "company":comp, "phone":rec["phone"], "mobilephone":rec["phone"], "jobtitle":rec.get("title") or "Founder"}
    if rec.get("email"): cp["email"] = rec["email"]
    ctid = None
    if rec.get("email"):
        s, d = hs("/crm/v3/objects/contacts/search","POST",{"limit":1,"properties":["email"],
            "filterGroups":[{"filters":[{"propertyName":"email","operator":"EQ","value":rec["email"]}]}]})
        ctid = d["results"][0]["id"] if d.get("results") else None
    if not ctid:
        s, d = hs("/crm/v3/objects/contacts","POST",{"properties":{k:v for k,v in cp.items() if v}})
        ctid = d.get("id")
    dp = {"dealname":comp,"pipeline":PIPE,"dealstage":COLD,"hubspot_owner_id":owner,"poc":owner,
          "scraped_type":TAG,"lh2_domain":dom}
    s, d = hs("/crm/v3/objects/deals","POST",{"properties":dp}); did = d.get("id")
    if not did: return None
    time.sleep(0.3)
    hs(f"/crm/v4/objects/deals/{did}/associations/default/companies/{coid}","PUT")
    if ctid:
        hs(f"/crm/v4/objects/deals/{did}/associations/default/contacts/{ctid}","PUT")
        hs(f"/crm/v4/objects/contacts/{ctid}/associations/default/companies/{coid}","PUT")
    return did

def main():
    owner = None; target = 60; batch = 10; dry = "--dry-run" in sys.argv
    for i, a in enumerate(sys.argv):
        if a == "--owner": owner = sys.argv[i+1]
        if a == "--target": target = int(sys.argv[i+1])
        if a == "--batch": batch = int(sys.argv[i+1])
    cands = candidates()
    c0 = credits()
    print(f"candidates: {len(cands)} (pri1 {sum(1 for c in cands if c['pri']==1)}, "
          f"pri2 {sum(1 for c in cands if c['pri']==2)}) | credits={c0} | target={target} batch={batch}", flush=True)
    logp = os.path.join(HERE, "enriched_push_log.json")
    log = json.load(open(logp, encoding="utf-8")) if os.path.exists(logp) else []
    ready = []; pushed = 0; scanned = 0
    stats = {"hc_fail":0,"no_founder":0,"no_phone":0,"quota":0}
    for c in cands:
        if pushed >= target: break
        scanned += 1
        total, prof = sh_company(c["company"])
        if total == "QUOTA":
            stats["quota"] += 1; print("  !! SignalHire daily SEARCH quota exhausted — stopping", flush=True); break
        if total is None or (isinstance(total,int) and total < MIN_HC):
            stats["hc_fail"] += 1; continue
        if not prof: stats["no_founder"] += 1; continue
        uid = prof.get("uid") or prof.get("profileUid")
        if not uid: stats["no_founder"] += 1; continue
        phone, email = sh_reveal(uid)
        if not phone: stats["no_phone"] += 1; time.sleep(0.4); continue
        title = next((str(e.get("title") or "") for e in (prof.get("experience") or []) if e.get("title")), "Founder")
        rec = {**c, "hc": total, "founder": str(prof.get("fullName") or "").strip(),
               "title": title, "phone": phone, "email": email}
        ready.append(rec)
        if not dry:
            did = push(rec, owner)
            if did:
                rec["deal_id"] = did; log.append(rec); pushed += 1
                json.dump(log, open(logp,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
                if pushed % batch == 1: print(f"  --- batch {(pushed//batch)+1} ---", flush=True)
                print(f"  [{pushed}] {c['company'][:26]:26} hc~{total:<5} {rec['founder'][:18]:18} {phone}", flush=True)
        else:
            pushed += 1
            print(f"  READY [{pushed}] {c['company'][:26]:26} hc~{total:<5} {rec['founder'][:18]:18} {phone}", flush=True)
        time.sleep(0.4)
    c1 = credits()
    print(f"\n{'DRY ' if dry else ''}PUSHED {pushed} | scanned {scanned} | "
          f"headcount-fail {stats['hc_fail']} no-founder {stats['no_founder']} no-phone {stats['no_phone']}")
    print(f"credits {c0} -> {c1} (used {(c0 or 0)-(c1 or 0)})")

if __name__ == "__main__":
    main()
