# -*- coding: utf-8 -*-
"""What can we actually count a call from?

Three candidate sources, and they do NOT agree:
  1. logged CALL engagements  — the only literal record of a dial
  2. deal stage-change history — records the OUTCOME, once per transition
  3. notes / completed tasks   — what the caller typed

Find out which of these exist and how densely, before designing the metric.
"""
import json, os, sys, time, datetime, collections, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); HUB=os.path.dirname(ROOT)
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

OW={o["id"]:f"{o.get('firstName','')} {o.get('lastName','')}".strip()
    for o in hs("/crm/v3/owners?limit=200")[1]["results"]}

def page(obj, props, extra=""):
    out=[];after=None
    while True:
        u=f"/crm/v3/objects/{obj}?limit=100&properties={','.join(props)}{extra}"
        if after: u+="&after="+after
        s,d=hs(u)
        if s!=200: print(f"  ! {obj} {s} {str(d)[:120]}"); return out
        out+=d.get("results",[])
        after=(d.get("paging") or {}).get("next",{}).get("after")
        if not after or len(out)>6000: break
        time.sleep(0.12)
    return out

print("="*74); print("1. LOGGED CALL ENGAGEMENTS"); print("="*74)
calls=page("calls",["hs_timestamp","hs_call_disposition","hs_call_duration","hs_call_direction",
                    "hubspot_owner_id","hs_call_status","hs_call_title"])
print(f"{len(calls)} call records in the portal")
if calls:
    by_day=collections.Counter((c["properties"].get("hs_timestamp") or "")[:10] for c in calls)
    print("\nmost recent 12 days:")
    for d,n in sorted(by_day.items())[-12:]: print(f"  {d}  {n}")
    print("\nby owner:")
    for k,v in collections.Counter(OW.get(c["properties"].get("hubspot_owner_id"),"(none)") for c in calls).most_common():
        print(f"  {k:<20}{v}")
    print("\ndisposition values:")
    for k,v in collections.Counter(c["properties"].get("hs_call_disposition") or "(blank)" for c in calls).most_common():
        print(f"  {k:<40}{v}")
    print("\nduration recorded on:", sum(1 for c in calls if (c['properties'].get('hs_call_duration') or '0') not in ('0','',None)))
else:
    print("  >>> NONE. Calls are not being logged as engagements at all.")

print()
print("="*74); print("2. DEAL STAGE-CHANGE HISTORY (last 14 days)"); print("="*74)
PS=hs("/crm/v3/pipelines/deals")[1]["results"]
LAB={s["id"]:s["label"] for p in PS for s in p["stages"]}
deals=[];after=None
while True:
    b={"properties":["dealname","dealstage","hubspot_owner_id"],"limit":200}
    if after: b["after"]=after
    s,d=hs("/crm/v3/objects/deals/search","POST",b)
    deals+=d.get("results",[]); after=(d.get("paging") or {}).get("next",{}).get("after")
    if not after: break
    time.sleep(0.12)
print(f"{len(deals)} live deals — sampling stage history on 250 of them")
cut=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=14))
moves=collections.Counter(); per_day=collections.Counter(); multi=collections.Counter()
for d in deals[:250]:
    s,h=hs(f"/crm/v3/objects/deals/{d['id']}?propertiesWithHistory=dealstage")
    hist=(h.get("propertiesWithHistory") or {}).get("dealstage") or []
    multi[len(hist)]+=1
    for e in hist:
        try: ts=datetime.datetime.fromisoformat(e["timestamp"].replace("Z","+00:00"))
        except Exception: continue
        if ts>=cut:
            moves[LAB.get(e["value"],e["value"])]+=1
            per_day[ts.date().isoformat()]+=1
    time.sleep(0.03)
print("\ntransitions INTO each stage, last 14d (sample of 250):")
for k,v in moves.most_common(12): print(f"  {k:<40}{v}")
print("\nby day:")
for k,v in sorted(per_day.items())[-10:]: print(f"  {k}  {v}")
print("\nhow many stage entries per deal (i.e. can we see repeat dials?):")
for k,v in sorted(multi.items())[:8]: print(f"  {k} entr{'y' if k==1 else 'ies'}: {v} deals")

print()
print("="*74); print("3. NOTES + COMPLETED TASKS as a proxy"); print("="*74)
notes=page("notes",["hs_timestamp","hubspot_owner_id"])
print(f"{len(notes)} notes")
nb=collections.Counter((n["properties"].get("hs_timestamp") or "")[:10] for n in notes)
for d,n in sorted(nb.items())[-10:]: print(f"  {d}  {n}")
tasks=page("tasks",["hs_timestamp","hs_task_status","hubspot_owner_id","hs_task_completion_date"])
print(f"\n{len(tasks)} tasks | completed: {sum(1 for t in tasks if t['properties'].get('hs_task_status')=='COMPLETED')}")
cb=collections.Counter((t["properties"].get("hs_task_completion_date") or "")[:10]
                       for t in tasks if t["properties"].get("hs_task_status")=="COMPLETED")
print("completions by day (last 10):")
for d,n in sorted(x for x in cb.items() if x[0])[-10:]: print(f"  {d}  {n}")
