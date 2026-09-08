# -*- coding: utf-8 -*-
"""How much of Lamiya's and Yuktha's queue is actually callable?

"Enriched" here means the thing a caller needs at the moment they open the deal: an
associated contact carrying a dialable +91 mobile. Email and LinkedIn are reported too, but
a deal without a phone cannot be cold-called whatever else it has.

Associations are read in batches — one call per deal would be hundreds of round trips.
"""
import os, sys, json, re, time, collections, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); HUB=os.path.dirname(ROOT)
env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open(os.path.join(HUB,'.env'),encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
H={"Authorization":"Bearer "+env["hubspot_key"],"Content-Type":"application/json"}
OW={"96574824":"Lamiya","96573782":"Yuktha"}

def hs(u,m="GET",b=None):
    d=json.dumps(b).encode() if b is not None else None
    for a in range(5):
        try:
            r=urllib.request.Request("https://api.hubapi.com"+u,data=d,method=m,headers=H)
            with urllib.request.urlopen(r,timeout=45) as x:
                t=x.read().decode(); return x.status,(json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504) and a<4: time.sleep(2*(a+1)); continue
            return e.code,{"raw":e.read().decode()[:200]}
        except Exception:
            if a==4: raise
            time.sleep(2)

def india(p):
    raw=(p or "").strip(); d=re.sub(r"[^\d]","",raw)
    if raw.startswith("+91") or (d.startswith("91") and len(d)==12): d=d[-10:]
    return len(d)==10 and d[0] in "6789"

s,d=hs("/crm/v3/pipelines/deals"); LAB={x["id"]:x["label"] for p in d["results"] for x in p["stages"]}
deals=[];after=None
while True:
    b={"filterGroups":[{"filters":[{"propertyName":"hubspot_owner_id","operator":"IN","values":list(OW)}]}],
       "properties":["dealname","dealstage","lead_source","hubspot_owner_id"],"limit":200}
    if after: b["after"]=after
    s,dd=hs("/crm/v3/objects/deals/search","POST",b); deals+=dd.get("results",[])
    after=(dd.get("paging") or {}).get("next",{}).get("after")
    if not after: break
    time.sleep(0.12)
OPEN=[x for x in deals if not LAB.get(x["properties"].get("dealstage"),"").startswith("Dead/")
      and LAB.get(x["properties"].get("dealstage"))!="Closed/Won"]
print(f"{len(OPEN)} open deals across Lamiya + Yuktha\n")

# deal -> contact ids, batched
d2c={}
ids=[x["id"] for x in OPEN]
for i in range(0,len(ids),100):
    s,a=hs("/crm/v4/associations/deals/contacts/batch/read","POST",
           {"inputs":[{"id":x} for x in ids[i:i+100]]})
    for res in (a.get("results") or []):
        d2c[str(res.get("from",{}).get("id"))]=[str(t["toObjectId"]) for t in res.get("to",[])]
    time.sleep(0.08)

cids=sorted({c for v in d2c.values() for c in v})
props={}
for i in range(0,len(cids),100):
    s,r=hs("/crm/v3/objects/contacts/batch/read","POST",
           {"properties":["phone","mobilephone","email","linkedin_url","firstname","lastname"],
            "inputs":[{"id":c} for c in cids[i:i+100]]})
    for x in (r.get("results") or []): props[x["id"]]=x["properties"]
    time.sleep(0.08)
print(f"{len(d2c)} deals mapped to {len(props)} contacts\n")

rows=[]
for x in OPEN:
    cs=[props.get(c,{}) for c in d2c.get(x["id"],[])]
    phone=any(india(c.get("mobilephone")) or india(c.get("phone")) for c in cs)
    email=any((c.get("email") or "").strip() for c in cs)
    li=any((c.get("linkedin_url") or "").strip() for c in cs)
    rows.append({"who":OW[x["properties"]["hubspot_owner_id"]],
                 "stage":LAB.get(x["properties"].get("dealstage")),
                 "src":x["properties"].get("lead_source") or "(untagged)",
                 "name":x["properties"].get("dealname") or "",
                 "ncontacts":len(cs),"phone":phone,"email":email,"li":li})

def block(sel,label):
    r=[x for x in rows if sel(x)]
    n=len(r) or 1
    ph=sum(1 for x in r if x["phone"]); em=sum(1 for x in r if x["email"])
    li=sum(1 for x in r if x["li"]); noc=sum(1 for x in r if x["ncontacts"]==0)
    print(f"{label:<22}{len(r):>5}{ph:>9} ({100*ph//n:>3}%){em:>9}{li:>8}{noc:>10}")

print(f"{'':<22}{'deals':>5}{'+91 phone':>16}{'email':>9}{'LinkedIn':>8}{'no contact':>10}")
print("-"*72)
for who in ("Lamiya","Yuktha"): block(lambda x,w=who: x["who"]==w, who)
print("-"*72)
block(lambda x: True, "BOTH")
print()
print("by stage:")
print(f"{'':<22}{'deals':>5}{'+91 phone':>16}{'email':>9}{'LinkedIn':>8}{'no contact':>10}")
for st in ("Cold Call","No Pickup","Interested","GMeet Fixed","Script Shared"):
    block(lambda x,s=st: x["stage"]==s, "  "+st)
print()
print("NOT enriched (no dialable +91), by source:")
bad=[x for x in rows if not x["phone"]]
for k,v in collections.Counter(x["src"] for x in bad).most_common():
    print(f"   {k:<44}{v:>4}")
print(f"\n   TOTAL not callable: {len(bad)} of {len(rows)}")
print("\n   sample:", [x["name"][:24] for x in bad[:8]])
json.dump(bad, open(os.path.join(HERE,"not_enriched.json"),"w",encoding="utf-8"),
          ensure_ascii=False, indent=1)
