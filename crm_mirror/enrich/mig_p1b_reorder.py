# -*- coding: utf-8 -*-
"""Phase 1b — set the board order in ONE atomic call per pipeline.

Patching stages one at a time does not work: HubSpot re-sequences displayOrder after each
write, so later patches land against numbering that has already shifted. `No Pickup` ended
up after `Interested` for exactly that reason.

PUT /crm/v3/pipelines/deals/{id} takes the whole stages array at once. Every existing stage
is sent WITH ITS ID — a stage omitted from that array is deleted, so the list is built from
what the API currently reports rather than from anything hardcoded.

Usage: python mig_p1b_reorder.py [--apply]
"""
import os, sys, json, time, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); HUB=os.path.dirname(ROOT)
env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open(os.path.join(HUB,'.env'),encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
H={"Authorization":"Bearer "+env["hubspot_key"],"Content-Type":"application/json"}
APPLY="--apply" in sys.argv

def hs(path, method="GET", body=None):
    url="https://api.hubapi.com"+path; data=json.dumps(body).encode() if body is not None else None
    for a in range(5):
        try:
            req=urllib.request.Request(url,data=data,method=method,headers=H)
            with urllib.request.urlopen(req,timeout=45) as r:
                t=r.read().decode(); return r.status,(json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504) and a<4: time.sleep(2*(a+1)); continue
            return e.code,{"raw":e.read().decode()[:400]}
        except Exception:
            if a==4: raise
            time.sleep(2)

ORDER = ["Cold Call", "No Pickup", "Interested", "GMeet Fixed", "Script Shared",
         "Script Results Received", "Commercial Negotiation", "Deal Contract Signed",
         "Data Migration Done", "Metadata Matched", "Payment Initiation", "Closed/Won",
         "Dead/ColdCall/Not Interested", "Dead/ColdCall/WrongFit",
         "Dead/ColdCall/WrongNumber", "Dead/ColdCall/NoPickup",
         "Dead/Interested/NoShow", "Dead/GMeet/NoShow", "Dead/GMeet/Cancelled",
         "Dead/GMeet/wrong fit", "Dead/GMeet/Privacy Concerns",
         "Dead/ScriptShared/NoShow", "Dead/ResultsReceived/WrongFit-Rejected",
         "Dead/Negotiation/Pricing", "Dead/Negotiation/Contractual",
         "Call Attempted"]

for p in hs("/crm/v3/pipelines/deals")[1]["results"]:
    pid, plabel = p["id"], p["label"]
    cur={s["label"]: s for s in p["stages"]}
    missing=[l for l in ORDER if l not in cur]
    extra=[l for l in cur if l not in ORDER]
    if missing: print(f"  ! {plabel}: ORDER names stages that do not exist: {missing}")
    if extra:   print(f"  ! {plabel}: pipeline has stages not in ORDER (kept at end): {extra}")

    stages=[]
    for i,lab in enumerate(ORDER):
        if lab not in cur: continue
        s=cur[lab]
        stages.append({"id":s["id"],"label":s["label"],"displayOrder":i,
                       "metadata":s["metadata"]})
    for lab in extra:                       # never drop anything we did not plan for
        s=cur[lab]
        stages.append({"id":s["id"],"label":s["label"],"displayOrder":len(stages),
                       "metadata":s["metadata"]})

    print(f"\n{plabel}: sending {len(stages)} stages (pipeline currently has {len(p['stages'])})")
    assert len(stages)==len(p["stages"]), "stage count mismatch — refusing to write"
    if APPLY:
        s,r=hs(f"/crm/v3/pipelines/deals/{pid}","PUT",
               {"label":p["label"],"displayOrder":p["displayOrder"],"stages":stages})
        print("   ", "ok" if s==200 else f"! {s} {r}")

if not APPLY:
    print("\nDRY RUN — re-run with --apply"); sys.exit()

print("\n"+"="*70); print("VERIFY"); print("="*70)
for p in hs("/crm/v3/pipelines/deals")[1]["results"]:
    got=[s["label"] for s in sorted(p["stages"], key=lambda x:x["displayOrder"])]
    want=[l for l in ORDER if l in {s["label"] for s in p["stages"]}]
    print(f"\n{p['label']}: {len(got)} stages | order correct: {got==want}")
    for s in sorted(p["stages"], key=lambda x:x["displayOrder"]):
        flag=""
        if s["label"]=="No Pickup":
            flag = "  <== OPEN ok" if s["metadata"].get("isClosed") in (False,"false") else "  <== !! CLOSED"
        print(f"   {s['displayOrder']:>2}  {s['label']:<42}closed={str(s['metadata'].get('isClosed')):<6}{flag}")
