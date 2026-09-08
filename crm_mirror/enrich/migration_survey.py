# -*- coding: utf-8 -*-
"""Everything that touches the stages we are about to change, before we change any of them.

Live deals are the obvious blast radius. The ones that bite later are the archived deals,
the deals whose HISTORY passes through a stage, and the code that hardcodes a stage id.
"""
import os, sys, json, time, collections, urllib.request, urllib.error
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
            return e.code,{"raw":e.read().decode()[:200]}
        except Exception:
            if a==4: raise
            time.sleep(2)

PS=hs("/crm/v3/pipelines/deals")[1]["results"]
PNAME={p["id"]:p["label"] for p in PS}
LAB={s["id"]:(p["id"],s["label"]) for p in PS for s in p["stages"]}
CA={sid for sid,(pid,l) in LAB.items() if l=="Call Attempted"}
DIN={sid for sid,(pid,l) in LAB.items() if l=="Dead/Interested/NoShow"}

print("="*78); print("1.  STAGE METADATA — what a new stage must look like"); print("="*78)
for p in PS:
    print(f"\n{p['label']} ({p['id']}) — {len(p['stages'])} stages")
    for s in sorted(p["stages"], key=lambda x: x["displayOrder"])[:3]:
        print(f"   order {s['displayOrder']:>2} | {s['label'][:34]:<36} "
              f"isClosed={s['metadata'].get('isClosed')} prob={s['metadata'].get('probability')}")
    ex=[s for s in p["stages"] if s["label"].startswith("Dead/")][:1]
    for s in ex:
        print(f"   a dead one: {s['label'][:34]:<36} isClosed={s['metadata'].get('isClosed')} "
              f"prob={s['metadata'].get('probability')}")

print()
print("="*78); print("2.  LIVE deals on the stages being changed"); print("="*78)
for name, ids in (("Call Attempted", CA), ("Dead/Interested/NoShow", DIN)):
    tot=collections.Counter()
    s,r=hs("/crm/v3/objects/deals/search","POST",{"filterGroups":[{"filters":[
        {"propertyName":"dealstage","operator":"IN","values":list(ids)}]}],
        "properties":["pipeline"],"limit":1})
    print(f"  {name:<26}{r.get('total',0):>5} live")

print()
print("="*78); print("3.  ARCHIVED deals on those stages (recycle bin)"); print("="*78)
arch=[];after=None
while True:
    u="/crm/v3/objects/deals?archived=true&limit=100&properties=dealstage,dealname"
    if after: u+="&after="+after
    s,d=hs(u)
    arch+=d.get("results",[]); after=(d.get("paging") or {}).get("next",{}).get("after")
    if not after: break
    time.sleep(0.1)
ac=collections.Counter(x["properties"].get("dealstage") for x in arch)
print(f"  {len(arch):,} archived deals total")
print(f"  on Call Attempted        : {sum(ac[i] for i in CA)}")
print(f"  on Dead/Interested/NoShow: {sum(ac[i] for i in DIN)}")
unknown=[i for i in ac if i and i not in LAB]
print(f"  referencing a stage id that no longer exists: {sum(ac[i] for i in unknown)} "
      f"across {len(unknown)} id(s) {unknown[:4]}")

print()
print("="*78); print("4.  HISTORY — deals that PASSED THROUGH Call Attempted but sit elsewhere now")
print("="*78)
print("  (these keep the stage in their history forever; deleting the stage orphans those")
print("   history entries, which is why reports need an old->new mapping)")
live=[];after=None
while True:
    b={"properties":["dealstage"],"limit":200}
    if after: b["after"]=after
    s,d=hs("/crm/v3/objects/deals/search","POST",b)
    live+=d.get("results",[]); after=(d.get("paging") or {}).get("next",{}).get("after")
    if not after: break
    time.sleep(0.1)
sample=[x for x in live if x["properties"].get("dealstage") not in CA][:200]
passed=0
for x in sample:
    s,h=hs(f"/crm/v3/objects/deals/{x['id']}?propertiesWithHistory=dealstage")
    if any(e["value"] in CA for e in (h.get("propertiesWithHistory") or {}).get("dealstage") or []):
        passed+=1
    time.sleep(0.02)
print(f"  sampled {len(sample)} deals NOT currently on Call Attempted -> {passed} "
      f"({100*passed//max(1,len(sample))}%) have it in their history")

print()
print("="*78); print("5.  CODE that hardcodes a stage id or label"); print("="*78)
import subprocess, re
ids = sorted(CA | DIN)
pats = ids + ["Call Attempted", "Dead/Interested/NoShow"]
for pat in pats:
    try:
        out=subprocess.run(["grep","-rl",pat,HUB,"--include=*.py","--include=*.html",
                            "--include=*.json","--exclude-dir=node_modules",
                            "--exclude-dir=.venv","--exclude-dir=__pycache__"],
                           capture_output=True, text=True, timeout=90).stdout.strip()
    except Exception:
        out=""
    files=[f.replace(HUB+os.sep,"").replace(HUB+"/","") for f in out.split("\n") if f]
    files=[f for f in files if not f.startswith(("crm_mirror/data","analysis/","crm_mirror/outflo"))]
    if files:
        print(f"  {pat}")
        for f in files[:8]: print(f"      {f}")
