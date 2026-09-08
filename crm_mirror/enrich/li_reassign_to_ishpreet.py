# -*- coding: utf-8 -*-
"""Move the LinkedIn Lead-Gen Form leads off Shobit onto Ishpreet — deal AND its contacts.

Scope is the two ad-form lead sources only. "LinkedIn Sales Navigator" is deliberately NOT
included: that is a separate, older prospecting source (all created Jul 21), not the ad-form
batch this is about.

Stage is irrelevant — the deal moves wherever it sits in the pipeline. Owner is the only
field touched; nothing is re-staged, renamed, or re-dated.

Usage: python li_reassign_to_ishpreet.py [--apply]
"""
import json, os, sys, time, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); HUB=os.path.dirname(ROOT)
env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open(os.path.join(HUB,'.env'),encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
HS=env["hubspot_key"]
SHOBIT="166262056"; ISHPREET="166322228"
SOURCES={"LinkedIn Lead-Gen Form - Jul 31 2026",
         "LinkedIn Lead-Gen Form - ITservices_targeted_message"}
APPLY="--apply" in sys.argv

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

deals=[d for d in json.load(open(os.path.join(HERE,"shobit_all_deals.json"),encoding="utf-8"))
       if (d["properties"].get("lead_source") or "") in SOURCES]
print(f"{len(deals)} LinkedIn Lead-Gen Form deals on Shobit\n")

moved_d=moved_c=0
for d in deals:
    did=d["id"]; p=d["properties"]
    # associated contacts travel with the deal, otherwise Ishpreet owns a deal whose
    # contact record still routes to Shobit
    s,assoc=hs(f"/crm/v4/objects/deals/{did}/associations/contacts")
    cids=[a["toObjectId"] for a in (assoc.get("results") or [])]
    print(f"  {p.get('dealname','')[:34]:<34} stage={p.get('dealstage','')} contacts={len(cids)}")
    if APPLY:
        s,_=hs(f"/crm/v3/objects/deals/{did}","PATCH",{"properties":{"hubspot_owner_id":ISHPREET}})
        if s==200: moved_d+=1
        else: print(f"    ! deal patch {s}")
        for cid in cids:
            s,_=hs(f"/crm/v3/objects/contacts/{cid}","PATCH",{"properties":{"hubspot_owner_id":ISHPREET}})
            if s==200: moved_c+=1
            else: print(f"    ! contact {cid} patch {s}")
        time.sleep(0.15)

if APPLY: print(f"\nreassigned {moved_d} deals + {moved_c} contacts -> Ishpreet")
else:     print(f"\nDRY RUN — would reassign {len(deals)} deals (+their contacts). Re-run with --apply")
