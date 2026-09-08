# -*- coding: utf-8 -*-
"""Build a LinkedIn-Ads contact-match CSV of 500 QUALIFIED, NET-NEW IT-services founders.
Qualified = GoodFirms gate_pass (India / founded<=2022 / 50-1000 emp / not big-outsourcer / net-new).
Founder: from the scrape `people` table, else SignalHire title-search (name-only, no reveal credit)."""
import os, sqlite3, json, re, csv, urllib.request, time, sys
HERE=os.path.dirname(os.path.abspath(__file__))
HUB=os.path.dirname(os.path.dirname(HERE))
env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open(os.path.join(HUB,'.env'),encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
SH=env["signal_hire"]
try: from rapidfuzz import fuzz
except Exception: fuzz=None
def norm(n): return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9 ]","",(n or "").lower())).strip()
def clean(s): return re.sub(r"\s+"," ",str(s or "").replace("\n"," ").replace("\r"," ")).strip()
def sh_find_founder(company):
    body=json.dumps({"currentCompany":company,"size":6,"currentTitle":"Founder OR Co-Founder OR CEO OR Owner OR Managing Director OR Director OR Proprietor"}).encode()
    req=urllib.request.Request("https://www.signalhire.com/api/v1/candidate/searchByQuery",data=body,method="POST",headers={"apikey":SH,"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=45) as r: resp=json.loads(r.read().decode())
    except Exception: return "",""
    profs=resp.get("profiles") or resp.get("requests") or resp.get("items") or []
    cl=company.lower(); best=None; bs=0
    for p in profs:
        if not isinstance(p,dict): continue
        cs=max([fuzz.token_set_ratio(cl,str(e.get("company") or "").lower()) if fuzz else (90 if cl in str(e.get('company') or '').lower() else 0) for e in (p.get("experience") or [])] or [0])
        if cs>=82 and cs>bs: bs=cs; best=p
    if not best: return "",""
    return clean(best.get("fullName")), clean(next((str(e.get("title") or "") for e in (best.get("experience") or []) if e.get("title")),"Founder"))

db=sqlite3.connect(os.path.join(HUB,"lh2-pipeline","data","pipeline.sqlite")); db.row_factory=sqlite3.Row
# people founders keyed by domain (best confidence)
ppl={}
for p in db.execute("SELECT domain,name,role,email,confidence FROM people ORDER BY confidence DESC"):
    d=(p["domain"] or "").lower()
    if d not in ppl: ppl[d]=p
comps=db.execute("SELECT domain,company_name,city FROM companies WHERE gate_pass=1").fetchall()
pushed=set(r["domain"] for r in json.load(open(os.path.join(HERE,"pushed_itservices.json"),encoding="utf-8")))
by_dom=json.load(open(os.path.join(HUB,"crm_mirror","data","index","by_domain.json"),encoding="utf-8"))
by_nm=json.load(open(os.path.join(HUB,"crm_mirror","data","index","by_name.json"),encoding="utf-8"))
# order: companies that already have a person-founder first (free), then the rest (discover)
have=[c for c in comps if (c["domain"] or "").lower() in ppl]
lack=[c for c in comps if (c["domain"] or "").lower() not in ppl]
rows=[]; disc=0
for c in have+lack:
    if len(rows)>=500: break
    d=(c["domain"] or "").lower(); comp=clean(c["company_name"])
    if d in pushed or d in by_dom or norm(comp) in by_nm: continue     # net-new only
    name=title=email=""
    p=ppl.get(d)
    if p and len((p["name"] or "").split())>=2:
        name=clean(p["name"]); title=clean(p["role"]) or "Founder"
        if p["email"] and "@" in (p["email"] or ""): email=clean(p["email"]).split(" ")[0]
    else:
        dn,dt=sh_find_founder(comp); disc+=1
        if dn and len(dn.split())>=2: name=dn; title=dt or "Founder"
        time.sleep(0.15)
    if not name or len(name.split())<2: continue
    nm=name.split(); rows.append({"email":email,"firstname":nm[0],"lastname":" ".join(nm[1:]),
        "jobtitle":title or "Founder","employeecompany":comp,"country":"IN","googleaid":""})
    if len(rows)%50==0: print(f"  {len(rows)} rows (discovered {disc})...", flush=True)
out=os.path.join(HUB,"exports/linkedin_audiences/LinkedIn_Ads_ITservices_500.csv")
with open(out,"w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=["email","firstname","lastname","jobtitle","employeecompany","country","googleaid"]); w.writeheader(); w.writerows(rows)
print(f"DONE rows={len(rows)} with_email={sum(1 for r in rows if r['email'])} discovered={disc} -> {out}")
