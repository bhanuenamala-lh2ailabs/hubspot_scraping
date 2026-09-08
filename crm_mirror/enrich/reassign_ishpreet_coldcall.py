# -*- coding: utf-8 -*-
"""Move Ishpreet's Cold Call queue to Lamiya and Yuktha, and retag to the new convention.

Naming convention: "Source ( Segment )".

scraped_type = "Distressed startups" marks the Tracxn sheet as the origin, so those deals
are labelled "Tracxn ( Startups )" rather than folded into a generic "Scraped" bucket — the
segment field drives the IT-services-vs-startups comparison and must stay truthful.

Pipelines are already correct: scraped in Scraped, OutFlo and LinkedIn in Campaign. Nothing
is moved between pipelines.

Usage: python reassign_ishpreet_coldcall.py [--apply]
"""
import json, os, sys, time, collections, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); HUB=os.path.dirname(ROOT)
env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open(os.path.join(HUB,'.env'),encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
H={"Authorization":"Bearer "+env["hubspot_key"],"Content-Type":"application/json"}
ISHPREET="166322228"; LAMIYA="96574824"; YUKTHA="96573782"
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
            return e.code,{"raw":e.read().decode()[:300]}
        except Exception:
            if a==4: raise
            time.sleep(2)

LAB={s["id"]:s["label"] for p in hs("/crm/v3/pipelines/deals")[1]["results"] for s in p["stages"]}

# old lead_source (or untagged+pipeline) -> new label
RETAG = {
    "Outflo Outreach - India":                              "Outflo ( Startups )",
    "OutFlo Replied - Relevance Check":                      "Outflo ( Startups )",
    "LinkedIn Lead-Gen Form - Jul 31 2026":                  "Linkedin Message ( IT services )",
    "LinkedIn Lead-Gen Form - ITservices_targeted_message":  "Linkedin Message ( IT services )",
}
# scraped_type "Distressed startups" identifies the Tracxn sheet as the origin, so these
# carry Tracxn provenance rather than a generic "Scraped" label.
TRACXN_STARTUPS = "Tracxn ( Startups )"
NEW_LABELS = sorted(set(RETAG.values()) | {TRACXN_STARTUPS, "Scraped ( IT Services )"})

# ---- make sure every new label exists on the dropdown, else the write is rejected ----
s,prop = hs("/crm/v3/properties/deals/lead_source")
opts = prop.get("options", [])
have = {o["label"] for o in opts}
missing = [l for l in NEW_LABELS if l not in have]
print(f"dropdown options to add: {missing or 'none'}")
if missing and APPLY:
    for l in missing:
        opts.append({"label":l,"value":l,"displayOrder":len(opts),"hidden":False})
    s,r = hs("/crm/v3/properties/deals/lead_source","PATCH",{"options":opts})
    print("   ", "ok" if s==200 else f"! {s} {r}")

# ---- Ishpreet's Cold Call deals ----
deals=[];after=None
while True:
    b={"filterGroups":[{"filters":[{"propertyName":"hubspot_owner_id","operator":"EQ","value":ISHPREET}]}],
       "properties":["dealname","dealstage","pipeline","lead_source","scraped_type"],"limit":200}
    if after: b["after"]=after
    s,d=hs("/crm/v3/objects/deals/search","POST",b)
    deals+=d.get("results",[]); after=(d.get("paging") or {}).get("next",{}).get("after")
    if not after: break
    time.sleep(0.15)
cc=[x for x in deals if LAB.get(x["properties"].get("dealstage"))=="Cold Call"]
print(f"\nIshpreet has {len(cc)} deals at Cold Call\n")

plan=[]
for x in cc:
    p=x["properties"]; old=p.get("lead_source") or ""
    if old in RETAG: new=RETAG[old]
    elif not old and p.get("pipeline")=="default":
        new = TRACXN_STARTUPS if p.get("scraped_type")=="Distressed startups" else "Scraped ( IT Services )"
    else: new=None                      # leave anything unexpected alone
    plan.append({"id":x["id"],"name":p.get("dealname") or "","old":old or "(untagged)",
                 "new":new,"pipe":"Scraped" if p.get("pipeline")=="default" else "Campaign",
                 "seg":p.get("scraped_type") or ""})

print("retag plan:")
for k,v in collections.Counter(f'{d["old"]}  ->  {d["new"]}' for d in plan).most_common():
    print(f"   {k:<74}{v:>4}")

# ---- 50:50, alternating WITHIN each group so both get the same mix ----
by=collections.defaultdict(list)
for d in plan: by[d["new"]].append(d)
for grp in by.values():
    for i,d in enumerate(grp):
        d["owner"]=LAMIYA if i%2==0 else YUKTHA
        d["who"]="Lamiya" if i%2==0 else "Yuktha"
print(f'\nsplit -> Lamiya {sum(1 for d in plan if d["owner"]==LAMIYA)} | '
      f'Yuktha {sum(1 for d in plan if d["owner"]==YUKTHA)}')
for grp,ds in by.items():
    print(f'   {grp:<38}Lamiya {sum(1 for d in ds if d["owner"]==LAMIYA):>3} | '
          f'Yuktha {sum(1 for d in ds if d["owner"]==YUKTHA):>3}')

if not APPLY:
    print("\nDRY RUN — nothing written. Re-run with --apply"); sys.exit()

# ---- execute: owner + lead_source on the deal, owner on its contacts ----
moved=fail=0
for d in plan:
    props={"hubspot_owner_id":d["owner"]}
    if d["new"]: props["lead_source"]=d["new"]
    s,r=hs(f"/crm/v3/objects/deals/{d['id']}","PATCH",{"properties":props})
    if s!=200: fail+=1; print(f"  ! {d['name'][:30]}: {s} {r}"); continue
    moved+=1
    s,a=hs(f"/crm/v4/objects/deals/{d['id']}/associations/contacts")
    for c in (a.get("results") or []):
        hs(f"/crm/v3/objects/contacts/{c['toObjectId']}","PATCH",
           {"properties":{"hubspot_owner_id":d["owner"]}})
    time.sleep(0.12)
print(f"\nreassigned + retagged {moved} deals" + (f", {fail} FAILED" if fail else ""))
json.dump(plan, open(os.path.join(HERE,"ishpreet_coldcall_moved.json"),"w",encoding="utf-8"),
          ensure_ascii=False, indent=1)
