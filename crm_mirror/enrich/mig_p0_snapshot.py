# -*- coding: utf-8 -*-
"""Phase 0 — snapshot everything the migration can touch. This file IS the rollback.

Captures every live deal's stage and owner, plus the full stage definition of both
pipelines, so a bad create or a bad move can be replayed back to exactly this state.
"""
import os, sys, json, time, datetime, collections, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); HUB=os.path.dirname(ROOT)
HOLD=os.path.join(ROOT,"holding"); os.makedirs(HOLD, exist_ok=True)
env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open(os.path.join(HUB,'.env'),encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
H={"Authorization":"Bearer "+env["hubspot_key"],"Content-Type":"application/json"}

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

stamp=datetime.date.today().isoformat()
pipes=hs("/crm/v3/pipelines/deals")[1]["results"]
LAB={s["id"]:s["label"] for p in pipes for s in p["stages"]}

deals=[];after=None
while True:
    b={"properties":["dealname","dealstage","pipeline","hubspot_owner_id","lead_source"],"limit":200}
    if after: b["after"]=after
    s,d=hs("/crm/v3/objects/deals/search","POST",b)
    deals+=d.get("results",[]); after=(d.get("paging") or {}).get("next",{}).get("after")
    if not after: break
    time.sleep(0.12)

snap={"taken_at":datetime.datetime.now().isoformat(timespec="seconds"),
      "pipelines":pipes,
      "deals":[{"id":x["id"],"name":x["properties"].get("dealname"),
                "pipeline":x["properties"].get("pipeline"),
                "dealstage":x["properties"].get("dealstage"),
                "stage_label":LAB.get(x["properties"].get("dealstage")),
                "owner":x["properties"].get("hubspot_owner_id"),
                "lead_source":x["properties"].get("lead_source")} for x in deals]}
p=os.path.join(HOLD,f"pre_migration_snapshot_{stamp}.json")
json.dump(snap, open(p,"w",encoding="utf-8"), ensure_ascii=False, indent=1)

print(f"snapshot -> {p}")
print(f"  {len(deals):,} live deals")
print(f"  {len(pipes)} pipelines, {sum(len(x['stages']) for x in pipes)} stages total")
c=collections.Counter(LAB.get(x['properties'].get('dealstage'),'?') for x in deals)
print("\n  top stages by occupancy:")
for k,v in c.most_common(8): print(f"    {k:<40}{v:>5}")
