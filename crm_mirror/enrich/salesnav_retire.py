# -*- coding: utf-8 -*-
"""Retire the Sales Navigator batch rows that never moved.

Scope is deliberately narrow: lead_source == 'LinkedIn Sales Navigator' AND still sitting
on Cold Call. The 8 rows someone actually worked today (1 Interested, 7 dead) are LEFT
ALONE — their outcomes are the only data this batch produced and deleting them would erase
the evidence that the list was the wrong profile.

A snapshot lands in crm_mirror/holding/ BEFORE anything is touched, because HubSpot's
delete is an archive (recoverable ~90 days) but the holding file is the copy that outlives
that window.

Usage: python salesnav_retire.py [--apply]
"""
import json, os, csv, sys, time, datetime, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); HUB=os.path.dirname(ROOT)
HOLD=os.path.join(ROOT,"holding"); os.makedirs(HOLD, exist_ok=True)
env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open(os.path.join(HUB,'.env'),encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
H={"Authorization":"Bearer "+env["hubspot_key"],"Content-Type":"application/json"}
APPLY="--apply" in sys.argv
OW={"166262056":"Shobit Gupta","166322228":"Ishpreet Sood"}

def hs(path, method="GET", body=None):
    url="https://api.hubapi.com"+path; data=json.dumps(body).encode() if body is not None else None
    for a in range(5):
        try:
            req=urllib.request.Request(url,data=data,method=method,headers=H)
            with urllib.request.urlopen(req,timeout=40) as r:
                t=r.read().decode(); return r.status,(json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504) and a<4: time.sleep(2*(a+1)); continue
            return e.code,{"raw":e.read().decode()[:300]}
        except Exception:
            if a==4: raise
            time.sleep(2)

LAB={s["id"]:s["label"] for p in hs("/crm/v3/pipelines/deals")[1]["results"] for s in p["stages"]}
COLDCALL=[sid for sid,l in LAB.items() if l=="Cold Call"]

s,r=hs("/crm/v3/objects/deals/search","POST",{"filterGroups":[{"filters":[
    {"propertyName":"lead_source","operator":"EQ","value":"LinkedIn Sales Navigator"}]}],
    "properties":["dealname","dealstage","hubspot_owner_id","createdate","pipeline"],"limit":100})
allrows=r.get("results",[])
targets=[x for x in allrows if x["properties"].get("dealstage") in COLDCALL]
kept=[x for x in allrows if x["properties"].get("dealstage") not in COLDCALL]

print(f"{len(allrows)} Sales Navigator deals | {len(targets)} at Cold Call -> retire | {len(kept)} worked -> keep\n")
for x in kept:
    print(f"  KEEP  {x['properties']['dealname'][:28]:<30}{LAB.get(x['properties']['dealstage'],'?')}")

snap=[]
for x in targets:
    p=x["properties"]
    s,a=hs(f"/crm/v4/objects/deals/{x['id']}/associations/contacts")
    cids=[c["toObjectId"] for c in (a.get("results") or [])]
    snap.append({"deal_id":x["id"],"dealname":p.get("dealname"),
                 "owner":OW.get(p.get("hubspot_owner_id"),p.get("hubspot_owner_id")),
                 "stage":LAB.get(p.get("dealstage")),"created":p.get("createdate"),
                 "pipeline":p.get("pipeline"),"contact_ids":cids})
    time.sleep(0.05)

print(f"\n{len(snap)} to retire:")
for x in snap: print(f"  {x['owner']:<15}{x['dealname'][:34]:<36}contacts={len(x['contact_ids'])}")

stamp=datetime.date.today().isoformat()
jp=os.path.join(HOLD,f"salesnav_coldcall_retired_{stamp}.json")
cp=os.path.join(HOLD,f"salesnav_coldcall_retired_{stamp}.csv")
json.dump(snap, open(jp,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
with open(cp,"w",newline="",encoding="utf-8-sig") as f:
    w=csv.DictWriter(f,fieldnames=["deal_id","dealname","owner","stage","created","pipeline","contact_ids"])
    w.writeheader()
    for x in snap: w.writerow({**x,"contact_ids":";".join(str(c) for c in x["contact_ids"])})
print(f"\nsnapshot -> {os.path.basename(jp)} / {os.path.basename(cp)}")

if not APPLY:
    print("\nDRY RUN — nothing deleted. Re-run with --apply"); sys.exit()

# contacts are left in place: they are people, reachable by other campaigns later. Only the
# deal (the pipeline row) is retired.
ok=fail=0
for i in range(0,len(snap),100):
    chunk=[{"id":x["deal_id"]} for x in snap[i:i+100]]
    s,_=hs("/crm/v3/objects/deals/batch/archive","POST",{"inputs":chunk})
    if s in (204,200): ok+=len(chunk)
    else: fail+=len(chunk); print(f"  ! batch {s}")
    time.sleep(0.3)
print(f"\nretired {ok} deals (archived — recoverable in HubSpot's recycle bin){' , '+str(fail)+' failed' if fail else ''}")
