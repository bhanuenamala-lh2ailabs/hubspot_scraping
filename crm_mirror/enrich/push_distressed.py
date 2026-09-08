# -*- coding: utf-8 -*-
"""
Push codebase-vetted, net-new, distressed Tracxn targets -> HubSpot Scraped pipeline.

Selection: asset_scores.json ranked by codebase_fit desc, excluding services-shells /
domain-reuse / low-data / already-in-HubSpot. Each pushed as Company + founder Contact +
Deal (stage Cold Call, tag Distressed startups), owner+PoC = the assigned caller.

Enrichment: Tracxn founder (name/email/phone/linkedin) topped up by SignalHire
(withoutWaterfall=true -> cached, synchronous, no credit charge).

Usage: python push_distressed.py --owner <id> --limit N [--dry-run]
Resumable: skips any target already recorded in pushed_distressed.json or the mirror.
"""
import json, os, re, sys, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                     # crm_mirror/
HUB  = os.path.dirname(ROOT)
env = {}
for l in open(os.path.join(HUB, ".env"), encoding="utf-8-sig"):
    if "=" in l and not l.strip().startswith("#"):
        k, v = l.split("=", 1); env[k.strip().lower()] = v.strip()
HS = env["hubspot_key"]; SH = env["signal_hire"]
COLDCALL = "3992480462"; PIPELINE = "default"; TAG = "Distressed startups"
OWNERS = {"166322228": "Ishpreet Sood", "166262056": "Shobit Gupta", "166322218": "Ashish Ranjan",
          "95472647": "Bhanu Enamala"}

def norm(n): return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", (n or "").lower())).strip()

def hs(path, method="GET", body=None):
    url = "https://api.hubapi.com" + path
    data = json.dumps(body).encode() if body is not None else None
    for a in range(5):
        try:
            req = urllib.request.Request(url, data=data, method=method,
                headers={"Authorization": "Bearer " + HS, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=40) as r:
                t = r.read().decode(); return r.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504) and a < 4: time.sleep(2*(a+1)); continue
            return e.code, {"raw": e.read().decode()[:250]}
        except Exception:
            if a == 4: raise
            time.sleep(2)

def sh_enrich(ident):
    """SignalHire cached reveal -> (phones, emails). withoutWaterfall=true => no charge."""
    if not ident: return [], []
    body = json.dumps({"items": [ident], "withoutWaterfall": True}).encode()
    req = urllib.request.Request("https://www.signalhire.com/api/v1/candidate/search", data=body,
        method="POST", headers={"apikey": SH, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r: d = json.loads(r.read().decode())
    except Exception: return [], []
    res = d if isinstance(d, list) else d.get("results", [])
    ph, em = [], []
    for it in res or []:
        if isinstance(it, dict) and it.get("status") == "success":
            for c in (it.get("candidate", {}) or {}).get("contacts", []) or []:
                t = str(c.get("type", "")).lower(); v = c.get("value")
                if not isinstance(v, str): continue
                if "phone" in t: ph.append(v)
                elif "email" in t and "@" in v: em.append(v)
    return ph, em

FREEMAIL = {"gmail.com","googlemail.com","yahoo.com","yahoo.co.in","hotmail.com","outlook.com",
            "rediffmail.com","icloud.com","proton.me","protonmail.com","zoho.com"}
def india_phone(p):
    """Return E.164 +91 number, or '' if foreign/invalid. Rejects US (+1 / 11-digit leading 1)."""
    raw = (p or "").strip()
    d = re.sub(r"[^\d]", "", raw)
    if raw.startswith("+1") or (len(d) == 11 and d.startswith("1")): return ""   # US -> reject
    if raw.startswith("+91") or (d.startswith("91") and len(d) == 12):
        d = d[-10:]
        return "+91" + d if len(d) == 10 and d[0] in "23456789" else ""
    if len(d) == 10 and d[0] in "6789": return "+91" + d           # India mobile
    if len(d) == 10 and d[0] in "2345678": return "+91" + d        # India landline (STD+num)
    return ""
def company_email(e, dom):
    """Email whose domain belongs to the company (NOT free-mail) — strongest affiliation signal."""
    e = (e or "").strip().lower()
    if "@" not in e: return ""
    d = e.split("@")[1]; root = (dom or "").split(".")[0]
    if d in FREEMAIL: return ""
    return e if (d == dom or (root and len(root) > 3 and root in d)) else ""
def trusted_email(e, dom):
    """Accept only a company-domain or free-mail address; reject other-corp (namesake/other-venture)."""
    e = (e or "").strip().lower()
    if "@" not in e: return ""
    d = e.split("@")[1]
    root = (dom or "").split(".")[0]
    if d == dom or d in FREEMAIL or (root and len(root) > 3 and root in d): return e
    return ""

try:
    from rapidfuzz import fuzz
except Exception:
    fuzz = None
def sh_find_founder(company):
    """SignalHire title-search to DISCOVER a founder when Tracxn has none.
    Returns (uid, name, title) for the profile whose experience best matches the company."""
    body = json.dumps({"currentCompany": company, "size": 6,
        "currentTitle": "Founder OR Co-Founder OR Cofounder OR CEO OR Owner OR Managing Director OR Director OR Proprietor"}).encode()
    req = urllib.request.Request("https://www.signalhire.com/api/v1/candidate/searchByQuery", data=body,
        method="POST", headers={"apikey": SH, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r: resp = json.loads(r.read().decode())
    except Exception: return "", "", ""
    profs = resp.get("profiles") or resp.get("requests") or resp.get("items") or []
    cl = company.lower(); best = None; bs = 0
    for p in profs:
        if not isinstance(p, dict): continue
        cs = 0
        for exp in p.get("experience") or []:
            c = str(exp.get("company") or "").lower()
            cs = max(cs, fuzz.token_set_ratio(cl, c) if fuzz else (90 if (cl in c or c in cl) else 0))
        if cs >= 80 and cs > bs: bs = cs; best = p
    if not best: return "", "", ""
    title = next((str(e.get("title") or "") for e in (best.get("experience") or []) if e.get("title")), "")
    return (best.get("uid") or best.get("profileUid") or ""), str(best.get("fullName") or "").strip(), title

def parse_founder(t):
    """Tracxn row -> first founder {name,title,email,phone,linkedin}."""
    fn = (t.get("founder_name") or "").split("\n")[0]
    parts = [p.strip() for p in fn.split(";") if p.strip()]
    name = parts[0] if parts else ""
    title = parts[1] if len(parts) > 1 else ""
    email = ""
    for p in parts:
        if "@" in p: email = p.strip(); break
    email = email or (t.get("email") or "").split(",")[0].strip()
    phone = re.sub(r"[^\d+]", "", (t.get("phone") or "").split(",")[0]) or ""
    li = [u.strip() for u in (t.get("linkedin") or "").split(",") if "/in/" in u]
    return {"name": name, "title": title, "email": email if "@" in email else "",
            "phone": phone if len(phone) >= 10 else "", "linkedin": li[0] if li else ""}

def load_targets():
    import glob
    scores = {}                                          # merge all parallel worker outputs, best cb wins
    for fp in sorted(glob.glob(os.path.join(HERE, "asset_scores*.json"))):
        for x in json.load(open(fp, encoding="utf-8")):
            d = (x.get("domain") or "").strip().lower()
            if d and (d not in scores or x.get("codebase_fit", 0) > scores[d].get("codebase_fit", 0)):
                scores[d] = x
    scores = list(scores.values())
    rt = {norm(x.get("company")): x for x in json.load(open(os.path.join(ROOT, "sources", "tracxn", "lh2_ranked_targets.json"), encoding="utf-8"))}
    by_dom = json.load(open(os.path.join(ROOT, "data", "index", "by_domain.json"), encoding="utf-8"))
    by_nm = json.load(open(os.path.join(ROOT, "data", "index", "by_name.json"), encoding="utf-8"))
    pushed = {}
    pf = os.path.join(HERE, "pushed_distressed.json")
    if os.path.exists(pf):
        for r in json.load(open(pf, encoding="utf-8")): pushed[r["domain"]] = r
    def netnew(x):
        d = (x.get("domain") or "").strip().lower()
        return not (d in by_dom or norm(x["company"]) in by_nm or d in pushed)
    clean = [x for x in scores if not x.get("services_shell") and not x.get("domain_reuse")
             and x.get("codebase_fit", 0) > 0 and x["cls"].get("company_type") not in (None, "unknown")
             and netnew(x)]
    clean.sort(key=lambda x: -x["codebase_fit"])
    return clean, rt, pushed

def main():
    owner = None; limit = 10; dry = False
    for i, a in enumerate(sys.argv):
        if a == "--owner": owner = sys.argv[i+1]
        if a == "--limit": limit = int(sys.argv[i+1])
        if a == "--dry-run": dry = True
    assert owner in OWNERS, f"owner must be one of {OWNERS}"
    targets, rt, pushed = load_targets()
    print(f"pool: {len(targets)} net-new clean codebase targets | pushing {limit} to {OWNERS[owner]} | dry={dry}", flush=True)
    done = list(pushed.values()); results = []
    for x in targets:
        if len(results) >= limit: break
        dom = (x.get("domain") or "").strip().lower(); comp = x["company"]
        t = rt.get(norm(comp))
        f = parse_founder(t) if t else {"name": "", "title": "", "email": "", "phone": "", "linkedin": ""}
        ph, em = sh_enrich(f["linkedin"] or f["email"])
        emails = [f["email"]] + em
        # trust guard: India phone or COMPANY-DOMAIN email = strong affiliation. Free-mail is
        # stored if present but does NOT alone qualify (too namesake-prone).
        phone = next((india_phone(p) for p in (ph + [f["phone"]]) if india_phone(p)), "")
        comp_email = next((company_email(e, dom) for e in emails if company_email(e, dom)), "")
        email = comp_email or next((trusted_email(e, dom) for e in emails if trusted_email(e, dom)), "")
        ready = bool(dom and f["name"] and phone)   # HARD RULE 2026-08-03: +91 phone REQUIRED (email alone is not enough)
        if not ready:                                   # fallback: DISCOVER a founder via SignalHire title-search
            uid, dname, dtitle = sh_find_founder(comp)
            if uid:
                ph2, em2 = sh_enrich(uid)
                phone = phone or next((india_phone(p) for p in ph2 if india_phone(p)), "")
                comp_email = comp_email or next((company_email(e, dom) for e in em2 if company_email(e, dom)), "")
                email = email or comp_email or next((trusted_email(e, dom) for e in em2 if trusted_email(e, dom)), "")
                if dname and not f["name"]: f["name"] = dname
                if dtitle and not f["title"]: f["title"] = dtitle
                ready = bool(dom and f["name"] and phone)   # HARD RULE 2026-08-03: +91 phone REQUIRED (email alone is not enough)
        if not ready:
            print(f"  skip (not ready): {comp[:26]:26} dom={bool(dom)} founder={bool(f['name'])} "
                  f"trusted_contact=False (raw ph={ph[:1]} em={em[:1]})", flush=True)
            continue
        rec = {"company": comp, "domain": dom, "codebase_fit": x["codebase_fit"], "opsdata_fit": x["opsdata_fit"],
               "founder": f["name"], "email": email, "phone": phone, "linkedin": f["linkedin"], "owner": owner}
        if dry:
            print(f"  READY {comp[:24]:24} cb={x['codebase_fit']} | {f['name'][:20]:20} {phone or '-':16} {email or '-'}", flush=True)
            results.append(rec); continue
        # 1) Company (dedup by domain)
        s, d = hs("/crm/v3/objects/companies/search", "POST", {"filterGroups":[{"filters":[{"propertyName":"domain","operator":"EQ","value":dom}]}],"properties":["name"],"limit":1})
        coid = d["results"][0]["id"] if d.get("results") else None
        if not coid:
            cp = {"name": comp, "domain": dom}
            if x.get("cls", {}).get("sector"): pass
            s, d = hs("/crm/v3/objects/companies", "POST", {"properties": cp})
            coid = d.get("id")
            if not coid: print(f"  ERR company {comp}: {d}", flush=True); continue
        # 2) Contact (dedup by email if present)
        ctid = None
        if email:
            s, d = hs("/crm/v3/objects/contacts/search", "POST", {"filterGroups":[{"filters":[{"propertyName":"email","operator":"EQ","value":email}]}],"properties":["email"],"limit":1})
            ctid = d["results"][0]["id"] if d.get("results") else None
        nm = f["name"].split()
        cprops = {"firstname": nm[0] if nm else comp, "lastname": " ".join(nm[1:]) if len(nm) > 1 else "",
                  "company": comp, "jobtitle": f["title"]}
        if email: cprops["email"] = email
        if phone: cprops["phone"] = phone; cprops["mobilephone"] = phone
        if f["linkedin"]: cprops["linkedin_url"] = f["linkedin"]
        if ctid:
            hs(f"/crm/v3/objects/contacts/{ctid}", "PATCH", {"properties": {k:v for k,v in cprops.items() if v}})
        else:
            s, d = hs("/crm/v3/objects/contacts", "POST", {"properties": {k:v for k,v in cprops.items() if v}})
            ctid = d.get("id")
        # 3) Deal
        dprops = {"dealname": comp, "pipeline": PIPELINE, "dealstage": COLDCALL, "hubspot_owner_id": owner,
                  "poc": owner, "scraped_type": TAG, "lh2_domain": dom}
        if f["linkedin"]: dprops["linkedin_url"] = f["linkedin"]
        s, d = hs("/crm/v3/objects/deals", "POST", {"properties": dprops})
        did = d.get("id")
        if not did: print(f"  ERR deal {comp}: {d}", flush=True); continue
        time.sleep(0.3)  # let objects index before associating
        hs(f"/crm/v4/objects/deals/{did}/associations/default/companies/{coid}", "PUT")
        if ctid:
            hs(f"/crm/v4/objects/deals/{did}/associations/default/contacts/{ctid}", "PUT")
            hs(f"/crm/v4/objects/contacts/{ctid}/associations/default/companies/{coid}", "PUT")
        rec.update({"deal_id": did, "company_id": coid, "contact_id": ctid})
        results.append(rec); done.append(rec)
        print(f"  PUSHED {comp[:22]:22} cb={x['codebase_fit']:3} deal={did} owner={OWNERS[owner]} | {f['name'][:18]:18} {phone or '-':15} {email or '-'}", flush=True)
        json.dump(done, open(os.path.join(HERE, "pushed_distressed.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        time.sleep(0.2)
    print(f"\n{'DRY-RUN ready' if dry else 'PUSHED'}: {len(results)} to {OWNERS[owner]}", flush=True)

if __name__ == "__main__":
    main()
