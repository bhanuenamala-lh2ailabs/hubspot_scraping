# -*- coding: utf-8 -*-
"""Phase 4 — retire `Call Attempted`, and Phase 5 — verify the whole migration.

Retire means RENAME, not delete. ~10% of deals that are not on that stage still have it in
their history, and history keeps the stage id forever. The portal already carries proof of
what deleting costs: 13 archived deals point at 4 stage ids that no longer resolve to
anything. Renaming keeps every one of those history entries readable while taking the stage
out of the working board.

Refuses to run if any deal is still sitting on the stage.

Usage: python mig_p4_retire.py [--apply]
"""
import os, sys, json, time, collections, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); HUB=os.path.dirname(ROOT)
env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open(os.path.join(HUB,'.env'),encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
H={"Authorization":"Bearer "+env["hubspot_key"],"Content-Type":"application/json"}
APPLY="--apply" in sys.argv
RETIRED="Call Attempted (retired)"

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

PS=hs("/crm/v3/pipelines/deals")[1]["results"]
CA={p["id"]: next((s for s in p["stages"] if s["label"] in ("Call Attempted", RETIRED)), None)
    for p in PS}

# ---- safety gate: nothing may still be sitting there ----
ids=[s["id"] for s in CA.values() if s]
s,r=hs("/crm/v3/objects/deals/search","POST",{"filterGroups":[{"filters":[
    {"propertyName":"dealstage","operator":"IN","values":ids}]}],"properties":["dealname"],"limit":1})
still=r.get("total",0)
print(f"deals still on Call Attempted: {still}")
if still:
    sys.exit("REFUSING — migrate them first (Phase 3), then re-run.")

for p in PS:
    st=CA[p["id"]]
    if not st: continue
    if st["label"]==RETIRED:
        print(f"  {p['label']}: already retired"); continue
    print(f"  {p['label']}: rename '{st['label']}' -> '{RETIRED}', move to end, mark closed")
    if APPLY:
        md=dict(st["metadata"]); md["isClosed"]="true"; md["probability"]="0.0"
        s,r=hs(f"/crm/v3/pipelines/deals/{p['id']}/stages/{st['id']}","PATCH",
               {"label":RETIRED,"displayOrder":99,"metadata":md})
        print("     ", "ok" if s==200 else f"! {s} {r}")

if not APPLY:
    print("\nDRY RUN — re-run with --apply"); sys.exit()

# ================= PHASE 5 — VERIFY =================
print("\n"+"="*74); print("PHASE 5 — VERIFICATION"); print("="*74)
PS=hs("/crm/v3/pipelines/deals")[1]["results"]
LAB={s["id"]:s["label"] for p in PS for s in p["stages"]}

print("\n1. Both pipelines carry identical labels and order")
seq={p["label"]:[s["label"] for s in sorted(p["stages"],key=lambda x:x["displayOrder"])] for p in PS}
names=list(seq)
same = seq[names[0]]==seq[names[1]]
print(f"   {'PASS' if same else 'FAIL'} — {len(seq[names[0]])} vs {len(seq[names[1]])} stages, identical: {same}")

print("\n2. No Pickup is OPEN in both")
for p in PS:
    st=next((s for s in p["stages"] if s["label"]=="No Pickup"), None)
    good = st and st["metadata"].get("isClosed") in (False,"false")
    print(f"   {'PASS' if good else 'FAIL'} — {p['label']}: isClosed={st['metadata'].get('isClosed') if st else 'MISSING'}")

print("\n3. All five new stages exist in both")
NEW=["No Pickup","Dead/ColdCall/NoPickup","Dead/GMeet/NoShow","Dead/GMeet/Cancelled",
     "Dead/ScriptShared/NoShow"]
for p in PS:
    have={s["label"] for s in p["stages"]}
    miss=[n for n in NEW if n not in have]
    print(f"   {'PASS' if not miss else 'FAIL'} — {p['label']}: {'all present' if not miss else miss}")

print("\n4. Live deals by stage now")
deals=[];after=None
while True:
    b={"properties":["dealstage","pipeline","hubspot_owner_id"],"limit":200}
    if after: b["after"]=after
    s,d=hs("/crm/v3/objects/deals/search","POST",b)
    deals+=d.get("results",[]); after=(d.get("paging") or {}).get("next",{}).get("after")
    if not after: break
    time.sleep(0.12)
c=collections.Counter(LAB.get(x["properties"].get("dealstage"),"?") for x in deals)
for k,v in c.most_common(12): print(f"   {k:<42}{v:>5}")

print("\n5. Reconcile against the pre-migration snapshot")
snap=json.load(open(os.path.join(ROOT,"holding","pre_migration_snapshot_2026-08-05.json"),
                    encoding="utf-8"))
print(f"   snapshot deals: {len(snap['deals']):,}   now: {len(deals):,}   "
      f"{'PASS' if len(deals)>=len(snap['deals']) else 'CHECK — deals went missing'}")
before=collections.Counter(d["stage_label"] for d in snap["deals"])
print(f"   Call Attempted before: {before['Call Attempted']}   No Pickup now: {c['No Pickup']}")

print("\n6. Retired stage is out of the working board")
for p in PS:
    st=next((s for s in p["stages"] if s["label"]==RETIRED), None)
    print(f"   {p['label']}: {'PASS' if st else 'FAIL'} — "
          f"order {st['displayOrder'] if st else '?'}, closed={st['metadata'].get('isClosed') if st else '?'}")
