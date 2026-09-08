# -*- coding: utf-8 -*-
"""Push net-new, +91-phone-ready IT-services firms -> HubSpot Scraped pipeline (tag ITservices).
Source: itservices_candidates.json (from the GoodFirms scrape). Dedup vs pushed_itservices.json + HubSpot.
Usage: python push_itservices.py --owner <id> --limit N   (reports per batch of 10)
"""
import json, os, re, sys, time, urllib.request, urllib.error
HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
env = {}
for l in open(os.path.join(HUB, ".env"), encoding="utf-8-sig"):
    if "=" in l and not l.strip().startswith("#"):
        k, v = l.split("=", 1); env[k.strip().lower()] = v.strip()
HS = env["hubspot_key"]; COLDCALL = "3992480462"; TAG = "ITservices"
SHORT = {"goo.gl","bit.ly","tinyurl.com","lnkd.in","rb.gy","t.co"}
def hs(path, method="GET", body=None):
    url = "https://api.hubapi.com" + path; data = json.dumps(body).encode() if body is not None else None
    for a in range(5):
        try:
            req = urllib.request.Request(url, data=data, method=method,
                headers={"Authorization": "Bearer " + HS, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=40) as r: t = r.read().decode(); return r.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504) and a < 4: time.sleep(2*(a+1)); continue
            return e.code, {"raw": e.read().decode()[:200]}
        except Exception:
            if a == 4: raise
            time.sleep(2)
def main():
    owner = None; limit = 50
    for i, a in enumerate(sys.argv):
        if a == "--owner": owner = sys.argv[i+1]
        if a == "--limit": limit = int(sys.argv[i+1])
    cand = json.load(open(os.path.join(HERE, "itservices_candidates.json"), encoding="utf-8"))
    pf = os.path.join(HERE, "pushed_itservices.json")
    pushed = json.load(open(pf, encoding="utf-8")) if os.path.exists(pf) else []
    done_dom = {r["domain"] for r in pushed}
    print(f"candidates={len(cand)} already_pushed={len(pushed)} | pushing up to {limit} to owner {owner}", flush=True)
    n = 0
    for r in cand:
        if n >= limit: break
        dom = (r["domain"] or "").strip().lower(); comp = r["company_name"]
        if dom in done_dom or dom in SHORT or "." not in dom or len(dom) < 5: continue
        s, d = hs("/crm/v3/objects/companies/search", "POST", {"filterGroups":[{"filters":[{"propertyName":"domain","operator":"EQ","value":dom}]}],"properties":["name"],"limit":1})
        if d.get("results"): done_dom.add(dom); continue                 # already in HubSpot -> skip
        s, d = hs("/crm/v3/objects/companies", "POST", {"properties":{"name":comp,"domain":dom,"city":(r.get("city") or "").split(",")[0]}})
        coid = d.get("id")
        if not coid: print("  ERR company", comp, d, flush=True); continue
        nm = (r["name"] or "").split(); email = (r.get("email") or "").strip()
        cp = {"firstname": nm[0] if nm else comp, "lastname": " ".join(nm[1:]) if len(nm) > 1 else "",
              "company": comp, "phone": r["e164"], "mobilephone": r["e164"], "jobtitle": r.get("role") or ""}
        if email and "@" in email: cp["email"] = email
        if r.get("linkedin_url"): cp["linkedin_url"] = r["linkedin_url"]
        ctid = None
        if email and "@" in email:
            s, d = hs("/crm/v3/objects/contacts/search", "POST", {"filterGroups":[{"filters":[{"propertyName":"email","operator":"EQ","value":email}]}],"properties":["email"],"limit":1})
            ctid = d["results"][0]["id"] if d.get("results") else None
        if not ctid:
            s, d = hs("/crm/v3/objects/contacts", "POST", {"properties":{k:v for k,v in cp.items() if v}}); ctid = d.get("id")
        dp = {"dealname": comp, "pipeline": "default", "dealstage": COLDCALL, "hubspot_owner_id": owner, "poc": owner,
              "scraped_type": TAG, "lh2_domain": dom}
        if r.get("linkedin_url"): dp["linkedin_url"] = r["linkedin_url"]
        s, d = hs("/crm/v3/objects/deals", "POST", {"properties": dp}); did = d.get("id")
        if not did: print("  ERR deal", comp, d, flush=True); continue
        time.sleep(0.3)
        hs(f"/crm/v4/objects/deals/{did}/associations/default/companies/{coid}", "PUT")
        if ctid:
            hs(f"/crm/v4/objects/deals/{did}/associations/default/contacts/{ctid}", "PUT")
            hs(f"/crm/v4/objects/contacts/{ctid}/associations/default/companies/{coid}", "PUT")
        n += 1; done_dom.add(dom)
        pushed.append({"company": comp, "domain": dom, "deal_id": did, "contact": r["name"], "phone": r["e164"], "owner": owner})
        json.dump(pushed, open(pf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        if n % 10 == 1: print(f"  --- batch {(n//10)+1} ---", flush=True)
        print(f"  [{n}] {comp[:26]:26} deal={did} {r['name'][:16]:16} {r['e164']}", flush=True)
        time.sleep(0.15)
    print(f"\nPUSHED {n} IT-services deals to owner {owner}", flush=True)
if __name__ == "__main__": main()
