# -*- coding: utf-8 -*-
"""Phase 1 + 2 — create the five new stages in BOTH pipelines, and fix the Gmeet naming.

Reversible: a newly created stage holds no deals and can simply be deleted. The rename keeps
the same stage id, so no deal moves and no history breaks.

The one setting that must not be got wrong: `No Pickup` is an OPEN stage. Created closed,
every deal migrated into it drops out of the open funnel on arrival.

Usage: python mig_p1_stages.py [--apply]
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

# (label, isClosed, probability) — probability is what HubSpot weights the funnel by
NEW = [
    ("No Pickup",                False, "0.12"),   # LIVE stage. Not a dead end.
    ("Dead/ColdCall/NoPickup",   True,  "0.0"),
    ("Dead/GMeet/NoShow",        True,  "0.0"),
    ("Dead/GMeet/Cancelled",     True,  "0.0"),
    ("Dead/ScriptShared/NoShow", True,  "0.0"),
]
RENAME = {"Dead/Gmeet/Privacy Concerns": "Dead/GMeet/Privacy Concerns"}

# the board order we want afterwards; anything not listed keeps its relative place at the end
ORDER = ["Cold Call", "No Pickup", "Interested", "GMeet Fixed", "Script Shared",
         "Script Results Received", "Commercial Negotiation", "Deal Contract Signed",
         "Data Migration Done", "Metadata Matched", "Payment Initiation", "Closed/Won",
         "Dead/ColdCall/Not Interested", "Dead/ColdCall/WrongFit",
         "Dead/ColdCall/WrongNumber", "Dead/ColdCall/NoPickup",
         "Dead/Interested/NoShow", "Dead/GMeet/NoShow", "Dead/GMeet/Cancelled",
         "Dead/GMeet/wrong fit", "Dead/GMeet/Privacy Concerns",
         "Dead/ScriptShared/NoShow", "Dead/ResultsReceived/WrongFit-Rejected",
         "Dead/Negotiation/Pricing", "Dead/Negotiation/Contractual",
         "Call Attempted"]          # stays last for now; Phase 4 renames it

pipes=hs("/crm/v3/pipelines/deals")[1]["results"]
for p in pipes:
    pid, plabel = p["id"], p["label"]
    have={s["label"]: s for s in p["stages"]}
    print(f"\n=== {plabel} ({pid}) — {len(p['stages'])} stages now ===")

    # ---- Phase 2: rename first, so ORDER can refer to the new label ----
    for old,new in RENAME.items():
        if old in have and new not in have:
            print(f"  rename  {old}  ->  {new}")
            if APPLY:
                s,r=hs(f"/crm/v3/pipelines/deals/{pid}/stages/{have[old]['id']}","PATCH",
                       {"label":new,"displayOrder":have[old]["displayOrder"],
                        "metadata":have[old]["metadata"]})
                if s!=200: print(f"    ! {s} {r}")
        elif new in have:
            print(f"  rename  already done ({new})")

    # ---- Phase 1: create ----
    for label, closed, prob in NEW:
        if label in have:
            print(f"  create  {label:<28} already exists, skipping")
            continue
        print(f"  create  {label:<28} isClosed={str(closed).lower()} prob={prob}")
        if APPLY:
            s,r=hs(f"/crm/v3/pipelines/deals/{pid}/stages","POST",
                   {"label":label,"displayOrder":len(have)+1,
                    "metadata":{"isClosed":str(closed).lower(),"probability":prob}})
            if s not in (200,201): print(f"    ! {s} {r}")
            else: have[label]=r

    if not APPLY: continue

    # ---- reorder the whole board to ORDER ----
    p2=hs(f"/crm/v3/pipelines/deals/{pid}")[1]
    cur={s["label"]: s for s in p2["stages"]}
    rank={lab:i for i,lab in enumerate(ORDER)}
    for lab,s in cur.items():
        want=rank.get(lab, 90+s["displayOrder"])
        if s["displayOrder"]!=want:
            r=hs(f"/crm/v3/pipelines/deals/{pid}/stages/{s['id']}","PATCH",
                 {"label":s["label"],"displayOrder":want,"metadata":s["metadata"]})
            if r[0]!=200: print(f"    ! reorder {lab}: {r[0]} {r[1]}")
    print("  board reordered")

print()
if not APPLY:
    print("DRY RUN — nothing written. Re-run with --apply")
    sys.exit()

# ---- verify by reading back ----
print("="*74); print("VERIFY (read back from the API)"); print("="*74)
ok=True
for p in hs("/crm/v3/pipelines/deals")[1]["results"]:
    print(f"\n{p['label']} — {len(p['stages'])} stages")
    for s in sorted(p["stages"], key=lambda x:x["displayOrder"]):
        mark=""
        if s["label"]=="No Pickup":
            good = s["metadata"].get("isClosed") in (False,"false")
            mark=("  <== OPEN, correct" if good else "  <== !! CLOSED - WRONG, FIX THIS")
            if not good: ok=False
        elif s["label"] in [n[0] for n in NEW]: mark="  <== new"
        print(f"   {s['displayOrder']:>2}  {s['label']:<42}"
              f"closed={str(s['metadata'].get('isClosed')):<6}{mark}")
print("\nRESULT:", "all good" if ok else "!! No Pickup is closed — must be fixed before Phase 3")
