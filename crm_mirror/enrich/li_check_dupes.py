# -*- coding: utf-8 -*-
"""A matching CONTACT is not the same as a lead already in the pipeline.

The dedup flagged 5 rows on contact-email. If any of those contacts has no associated deal,
the lead is sitting in HubSpot owned by nobody and working nothing — skipping it as a
"duplicate" would quietly lose a real lead. Check each one before deciding.
"""
import json, os, sys, time, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); HUB=os.path.dirname(ROOT)
env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open(os.path.join(HUB,'.env'),encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
HS=env["hubspot_key"]
OWNERS={"166262056":"Shobit","166322228":"Ishpreet","166420402":"Shreyas","166483631":"Yash",
        "96574824":"Lamiya","96573782":"Yuktha","166322218":"Ashish","95472647":"Bhanu"}

def hs(path, method="GET", body=None):
    url="https://api.hubapi.com"+path; data=json.dumps(body).encode() if body is not None else None
    for a in range(5):
        try:
            req=urllib.request.Request(url,data=data,method=method,headers={"Authorization":"Bearer "+HS,"Content-Type":"application/json"})
            with urllib.request.urlopen(req,timeout=40) as r:
                t=r.read().decode(); return r.status,(json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504) and a<4: time.sleep(2*(a+1)); continue
            return e.code,{"raw":e.read().decode()[:300]}
        except Exception:
            if a==4: raise
            time.sleep(2)

EMAILS=["akhtharedv@gmail.com","rishabhvv0@gmail.com","aayushjain6020@gmail.com",
        "chakravarthyvp@gmail.com","noahsaark@gmail.com"]
orphans=[]
for em in EMAILS:
    s,r=hs("/crm/v3/objects/contacts/search","POST",{"filterGroups":[{"filters":[
        {"propertyName":"email","operator":"EQ","value":em}]}],
        "properties":["email","firstname","lastname","hubspot_owner_id","createdate"],"limit":1})
    c=(r.get("results") or [None])[0]
    if not c: print(f"{em:<32} NO CONTACT?"); continue
    cid=c["id"]; p=c["properties"]
    own=OWNERS.get(p.get("hubspot_owner_id") or "", p.get("hubspot_owner_id") or "unowned")
    s,a=hs(f"/crm/v4/objects/contacts/{cid}/associations/deals")
    dids=[x["toObjectId"] for x in (a.get("results") or [])]
    names=[]
    for did in dids:
        s,d=hs(f"/crm/v3/objects/deals/{did}?properties=dealname,dealstage,hubspot_owner_id,lead_source")
        dp=d.get("properties",{})
        names.append(f"{dp.get('dealname')} [{OWNERS.get(dp.get('hubspot_owner_id') or '','?')}] "
                     f"src={dp.get('lead_source')}")
    tag = "OK - has deal" if dids else ">>> ORPHAN CONTACT, NO DEAL"
    print(f"{em:<32} contact={cid} owner={own:<9} deals={len(dids)}  {tag}")
    for n in names: print(f"      {n}")
    if not dids: orphans.append({"email":em,"contact_id":cid,"created":p.get("createdate")})

print(f"\n{len(orphans)} orphan contact(s) — these are NOT duplicates and still need a deal")
json.dump(orphans, open(os.path.join(HERE,"li_aug5_orphans.json"),"w",encoding="utf-8"), indent=1)
