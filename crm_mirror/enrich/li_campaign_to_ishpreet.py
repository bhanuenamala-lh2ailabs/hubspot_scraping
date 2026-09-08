# -*- coding: utf-8 -*-
"""Hand the whole "Linkedin Campaign ( IT Services )" book from Lamiya and Yuktha to Ishpreet.

Every stage moves, dead ones included — the instruction is the source, not the stage, so a
deal already marked Dead/ColdCall/WrongFit still belongs in Ishpreet's book for the record.

Contacts follow the deal. A caller who owns a deal but not its contact cannot see the
number on the contact record, so leaving contacts behind would hand over a half-usable book.

SAFETY — this is a bulk hubspot_owner_id write, exactly what the 15-minute VCF notifier
reads as "new assignment" and mails about. That task is disabled; this refuses to run if it
is ever switched back on.

Usage: python li_campaign_to_ishpreet.py [--apply]
"""
import os, sys, json, time, collections, subprocess, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); HUB=os.path.dirname(ROOT)
env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open(os.path.join(HUB,'.env'),encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
H={"Authorization":"Bearer "+env["hubspot_key"],"Content-Type":"application/json"}
ISHPREET="166322228"; LAMIYA="96574824"; YUKTHA="96573782"
WHO={LAMIYA:"Lamiya", YUKTHA:"Yuktha"}
SOURCE="Linkedin Campaign ( IT Services )"
APPLY="--apply" in sys.argv

def hs(u,m="GET",b=None):
    d=json.dumps(b).encode() if b is not None else None
    for a in range(5):
        try:
            r=urllib.request.Request("https://api.hubapi.com"+u,data=d,method=m,headers=H)
            with urllib.request.urlopen(r,timeout=45) as x:
                t=x.read().decode(); return x.status,(json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504) and a<4: time.sleep(2*(a+1)); continue
            return e.code,{"raw":e.read().decode()[:300]}
        except Exception:
            if a==4: raise
            time.sleep(2)

# ---- refuse to write while the auto-mailer could fire ----
try:
    q=subprocess.run(["schtasks","/query","/tn","LH2 VCF lead notifier","/fo","LIST","/v"],
                     capture_output=True, text=True, timeout=30).stdout
    if "Disabled" not in q:
        sys.exit("ABORT: 'LH2 VCF lead notifier' is not disabled — it would mail everyone. "
                 "Disable it first: schtasks /change /tn \"LH2 VCF lead notifier\" /disable")
    print("guard: VCF notifier is disabled, safe to reassign")
except FileNotFoundError:
    print("guard: schtasks unavailable, skipping notifier check")

s,d=hs("/crm/v3/pipelines/deals")
LAB={x["id"]:x["label"] for p in d["results"] for x in p["stages"]}

deals=[];after=None
while True:
    b={"filterGroups":[{"filters":[
        {"propertyName":"hubspot_owner_id","operator":"IN","values":[LAMIYA,YUKTHA]},
        {"propertyName":"lead_source","operator":"EQ","value":SOURCE}]}],
       "properties":["dealname","dealstage","pipeline","lead_source","hubspot_owner_id"],"limit":200}
    if after: b["after"]=after
    s,dd=hs("/crm/v3/objects/deals/search","POST",b); deals+=dd.get("results",[])
    after=(dd.get("paging") or {}).get("next",{}).get("after")
    if not after: break
    time.sleep(0.12)

print(f'\n{len(deals)} deals tagged "{SOURCE}" held by Lamiya/Yuktha\n')
print("  from owner:", dict(collections.Counter(WHO[x["properties"]["hubspot_owner_id"]] for x in deals)))
print("  by stage:  ", dict(collections.Counter(LAB.get(x["properties"].get("dealstage")) for x in deals)))

# contacts on those deals, batched
ids=[x["id"] for x in deals]; d2c={}
for i in range(0,len(ids),100):
    s,a=hs("/crm/v4/associations/deals/contacts/batch/read","POST",
           {"inputs":[{"id":x} for x in ids[i:i+100]]})
    for res in (a.get("results") or []):
        d2c[str(res.get("from",{}).get("id"))]=[str(t["toObjectId"]) for t in res.get("to",[])]
    time.sleep(0.08)
cids=sorted({c for v in d2c.values() for c in v})
print(f"  contacts to move alongside: {len(cids)}")

if not APPLY:
    print("\nDRY RUN — nothing written. Re-run with --apply")
    for x in deals[:10]:
        p=x["properties"]
        print(f'   {WHO[p["hubspot_owner_id"]]:<8}{(p.get("dealname") or "")[:38]:<40}{LAB.get(p.get("dealstage"))}')
    sys.exit()

# ---- deals in batches of 100 ----
moved=0
for i in range(0,len(ids),100):
    chunk=ids[i:i+100]
    s,r=hs("/crm/v3/objects/deals/batch/update","POST",
           {"inputs":[{"id":x,"properties":{"hubspot_owner_id":ISHPREET}} for x in chunk]})
    if s in (200,201,207): moved+=len(chunk)
    else: print(f"  ! deal batch {i}: {s} {r}")
    time.sleep(0.1)

# ---- contacts in batches of 100 ----
cmoved=0
for i in range(0,len(cids),100):
    chunk=cids[i:i+100]
    s,r=hs("/crm/v3/objects/contacts/batch/update","POST",
           {"inputs":[{"id":c,"properties":{"hubspot_owner_id":ISHPREET}} for c in chunk]})
    if s in (200,201,207): cmoved+=len(chunk)
    else: print(f"  ! contact batch {i}: {s} {r}")
    time.sleep(0.1)

print(f"\nmoved {moved} deals and {cmoved} contacts to Ishpreet")
json.dump([{"id":x["id"],"name":x["properties"].get("dealname"),
            "from":WHO[x["properties"]["hubspot_owner_id"]],
            "stage":LAB.get(x["properties"].get("dealstage"))} for x in deals],
          open(os.path.join(HERE,"li_campaign_to_ishpreet.json"),"w",encoding="utf-8"),
          ensure_ascii=False, indent=1)
