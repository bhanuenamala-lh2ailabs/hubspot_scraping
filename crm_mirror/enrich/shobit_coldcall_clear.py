# -*- coding: utf-8 -*-
"""Clear Shobit's Cold Call queue: retag + reassign the Tracxn ones, park the Indonesian ones.

The 27 untagged are Galaxycard, BillMart, Finbingo, Zoko, DigiBoxx, Truein, Biconomy,
Cosmofeed and similar — product startups, not IT-services firms, which read as
"<name> Technologies Pvt Ltd". Tagged "Tracxn ( Startups )".

Indonesia: all 63 are parked, not just Shobit's 13. They are one cohort — same source, all at
Cold Call, not one ever dialled — and parking half of it leaves 50 identical deals sitting
unworked on Yash. Snapshotted before archiving, so restoring is one command if only the 13
were meant.

Usage: python shobit_coldcall_clear.py [--apply]
"""
import json, os, csv, sys, time, datetime, collections, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); HUB=os.path.dirname(ROOT)
HOLD=os.path.join(ROOT,"holding"); os.makedirs(HOLD, exist_ok=True)
env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open(os.path.join(HUB,'.env'),encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
H={"Authorization":"Bearer "+env["hubspot_key"],"Content-Type":"application/json"}
SHOBIT="166262056"; LAMIYA="96574824"; YUKTHA="96573782"
TAG="Tracxn ( Startups )"
APPLY="--apply" in sys.argv
STAMP=datetime.date.today().isoformat()

def hs(path, method="GET", body=None):
    url="https://api.hubapi.com"+path; data=json.dumps(body).encode() if body is not None else None
    for a in range(5):
        try:
            req=urllib.request.Request(url,data=data,method=method,headers=H)
            with urllib.request.urlopen(req,timeout=45) as r:
                t=r.read().decode(); return r.status,(json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504) and a<4: time.sleep(2*(a+1)); continue
            return e.code,{"raw":e.read().decode()[:300]}
        except Exception:
            if a==4: raise
            time.sleep(2)

LAB={s["id"]:s["label"] for p in hs("/crm/v3/pipelines/deals")[1]["results"] for s in p["stages"]}
OW={o["id"]:f'{o.get("firstName","")} {o.get("lastName","")}'.strip()
    for o in hs("/crm/v3/owners?limit=200")[1]["results"]}

deals=[];after=None
while True:
    b={"properties":["dealname","dealstage","pipeline","lead_source","scraped_type",
                     "hubspot_owner_id"],"limit":200}
    if after: b["after"]=after
    s,d=hs("/crm/v3/objects/deals/search","POST",b)
    deals+=d.get("results",[]); after=(d.get("paging") or {}).get("next",{}).get("after")
    if not after: break
    time.sleep(0.12)

cc=lambda x: LAB.get(x["properties"].get("dealstage"))=="Cold Call"
untagged=[x for x in deals if cc(x) and x["properties"].get("hubspot_owner_id")==SHOBIT
          and not x["properties"].get("lead_source")]
indo=[x for x in deals if x["properties"].get("lead_source")=="Outflo Outreach - Indonesia"]

print(f"A. Shobit untagged at Cold Call : {len(untagged)}  -> tag '{TAG}', split 50:50")
print(f"B. Indonesia OutFlo (ALL owners): {len(indo)}  -> park")
print("   by owner:", dict(collections.Counter(OW.get(x['properties'].get('hubspot_owner_id'),'?') for x in indo)))
print("   by stage:", dict(collections.Counter(LAB.get(x['properties'].get('dealstage')) for x in indo)))

for i,x in enumerate(untagged):
    x["_own"]=LAMIYA if i%2==0 else YUKTHA
    x["_who"]="Lamiya" if i%2==0 else "Yuktha"
print(f"\n   split -> Lamiya {sum(1 for x in untagged if x['_own']==LAMIYA)} | "
      f"Yuktha {sum(1 for x in untagged if x['_own']==YUKTHA)}")

# ---- snapshot the Indonesian cohort BEFORE touching it ----
snap=[{"deal_id":x["id"],"name":x["properties"].get("dealname"),
       "owner":OW.get(x["properties"].get("hubspot_owner_id")),
       "stage":LAB.get(x["properties"].get("dealstage")),
       "pipeline":x["properties"].get("pipeline")} for x in indo]
jp=os.path.join(HOLD,f"outflo_indonesia_parked_{STAMP}.json")
cp=os.path.join(HOLD,f"outflo_indonesia_parked_{STAMP}.csv")
json.dump(snap, open(jp,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
with open(cp,"w",newline="",encoding="utf-8-sig") as f:
    w=csv.DictWriter(f,fieldnames=list(snap[0].keys())); w.writeheader(); w.writerows(snap)
print(f"\nsnapshot -> {os.path.basename(jp)} / {os.path.basename(cp)}")

if not APPLY:
    print("\nDRY RUN — nothing written. Re-run with --apply"); sys.exit()

# ---- ensure the tag exists on the dropdown ----
s,prop=hs("/crm/v3/properties/deals/lead_source")
opts=prop.get("options",[])
if not any(o["label"]==TAG for o in opts):
    opts.append({"label":TAG,"value":TAG,"displayOrder":len(opts),"hidden":False})
    hs("/crm/v3/properties/deals/lead_source","PATCH",{"options":opts})
    print(f"added dropdown option: {TAG}")

ok=0
for x in untagged:
    s,r=hs(f"/crm/v3/objects/deals/{x['id']}","PATCH",
           {"properties":{"hubspot_owner_id":x["_own"],"lead_source":TAG}})
    if s!=200: print(f"  ! {x['properties'].get('dealname')}: {s} {r}"); continue
    ok+=1
    s,a=hs(f"/crm/v4/objects/deals/{x['id']}/associations/contacts")
    for c in (a.get("results") or []):
        hs(f"/crm/v3/objects/contacts/{c['toObjectId']}","PATCH",
           {"properties":{"hubspot_owner_id":x["_own"]}})
    time.sleep(0.1)
print(f"\nA. retagged + reassigned {ok} deals")

arch=0
ids=[x["id"] for x in indo]
for i in range(0,len(ids),100):
    s,_=hs("/crm/v3/objects/deals/batch/archive","POST",
           {"inputs":[{"id":d} for d in ids[i:i+100]]})
    if s in (200,204): arch+=len(ids[i:i+100])
    else: print(f"  ! archive batch {s}")
    time.sleep(0.3)
print(f"B. parked {arch} Indonesian deals (archived — recoverable from the recycle bin)")
