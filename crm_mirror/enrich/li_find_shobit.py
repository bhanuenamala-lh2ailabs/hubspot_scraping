# -*- coding: utf-8 -*-
"""Find the LinkedIn-form leads sitting on Shobit, whatever stage they reached."""
import json, os, sys, time, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); HUB=os.path.dirname(ROOT)
env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open(os.path.join(HUB,'.env'),encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
HS=env["hubspot_key"]
SHOBIT="166262056"

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

# every deal Shobit owns, with the fields that identify provenance
props=["dealname","dealstage","pipeline","hs_lead_source","lead_source","createdate",
       "hs_object_id","hubspot_owner_id","linkedin_url","email","phone"]
out=[]; after=None
while True:
    body={"filterGroups":[{"filters":[{"propertyName":"hubspot_owner_id","operator":"EQ","value":SHOBIT}]}],
          "properties":props,"limit":100}
    if after: body["after"]=after
    s,r=hs("/crm/v3/objects/deals/search","POST",body)
    if s!=200: print("ERR",s,r); break
    out+=r.get("results",[])
    after=(r.get("paging") or {}).get("next",{}).get("after")
    if not after: break
    time.sleep(0.2)

print(f"Shobit owns {len(out)} deals total\n")
import collections
ls=collections.Counter((d["properties"].get("hs_lead_source") or d["properties"].get("lead_source") or "(none)") for d in out)
print("by lead source:")
for k,v in ls.most_common(): print(f"  {k:<45}{v:>5}")
today=collections.Counter()
for d in out:
    c=(d["properties"].get("createdate") or "")[:10]
    today[c]+=1
print("\nby create date (last 6):")
for k,v in sorted(today.items())[-6:]: print(f"  {k}  {v}")
json.dump(out, open(os.path.join(HERE,"shobit_all_deals.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\nwrote shobit_all_deals.json")
