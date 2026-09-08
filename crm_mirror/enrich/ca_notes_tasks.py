# -*- coding: utf-8 -*-
"""Read every note and task hanging off the deals parked on `Call Attempted`.

The stage records that a dial happened but not what came of it. If the callers wrote what
happened in a note, the outcome is recoverable and these deals can be sorted into the new
outcome stages instead of being swept blindly into No Pickup. This finds out how much of
that exists before any migration decision is made.

Writes ca_notes_tasks.json for follow-up work.
"""
import json, os, re, sys, time, html, datetime, collections, threading
import urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); HUB=os.path.dirname(ROOT)
env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open(os.path.join(HUB,'.env'),encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
H={"Authorization":"Bearer "+env["hubspot_key"],"Content-Type":"application/json"}

def hs(path, method="GET", body=None):
    url="https://api.hubapi.com"+path; data=json.dumps(body).encode() if body is not None else None
    for a in range(6):
        try:
            req=urllib.request.Request(url,data=data,method=method,headers=H)
            with urllib.request.urlopen(req,timeout=45) as r:
                t=r.read().decode(); return r.status,(json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504) and a<5: time.sleep(1.5*(a+1)); continue
            return e.code,{"raw":e.read().decode()[:200]}
        except Exception:
            if a==5: raise
            time.sleep(1.5)

PS=hs("/crm/v3/pipelines/deals")[1]["results"]
CA={s["id"]:("Scraped" if p["id"]=="default" else "Campaign")
    for p in PS for s in p["stages"] if s["label"]=="Call Attempted"}
OW={o["id"]:f"{o.get('firstName','')} {o.get('lastName','')}".strip()
    for o in hs("/crm/v3/owners?limit=200")[1]["results"]}

deals=[];after=None
while True:
    b={"filterGroups":[{"filters":[{"propertyName":"dealstage","operator":"IN","values":list(CA)}]}],
       "properties":["dealname","dealstage","pipeline","hubspot_owner_id","lead_source",
                     "hs_lastmodifieddate","createdate"],"limit":200}
    if after: b["after"]=after
    s,d=hs("/crm/v3/objects/deals/search","POST",b)
    deals+=d.get("results",[]); after=(d.get("paging") or {}).get("next",{}).get("after")
    if not after: break
    time.sleep(0.15)
print(f"{len(deals)} deals on Call Attempted — pulling notes + tasks\n", flush=True)

def strip_html(s):
    s=re.sub(r"<br\s*/?>", " ", s or "")
    s=re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()

lock=threading.Lock(); done={"n":0}
def work(d):
    did=d["id"]
    notes=[]; tasks=[]
    s,a=hs(f"/crm/v4/objects/deals/{did}/associations/notes")
    nids=[x["toObjectId"] for x in (a.get("results") or [])]
    for nid in nids[:20]:
        s,n=hs(f"/crm/v3/objects/notes/{nid}?properties=hs_note_body,hs_timestamp,hubspot_owner_id")
        p=n.get("properties") or {}
        body=strip_html(p.get("hs_note_body"))
        if body: notes.append({"at":(p.get("hs_timestamp") or "")[:10],
                               "by":OW.get(p.get("hubspot_owner_id"),""),"text":body})
    s,a=hs(f"/crm/v4/objects/deals/{did}/associations/tasks")
    tids=[x["toObjectId"] for x in (a.get("results") or [])]
    for tid in tids[:20]:
        s,t=hs(f"/crm/v3/objects/tasks/{tid}?properties=hs_task_subject,hs_task_status,"
               f"hs_task_body,hs_timestamp,hubspot_owner_id,hs_task_type")
        p=t.get("properties") or {}
        tasks.append({"subject":p.get("hs_task_subject") or "","status":p.get("hs_task_status") or "",
                      "due":(p.get("hs_timestamp") or "")[:10],"type":p.get("hs_task_type") or "",
                      "body":strip_html(p.get("hs_task_body")),
                      "by":OW.get(p.get("hubspot_owner_id"),"")})
    pr=d["properties"]
    row={"deal_id":did,"name":pr.get("dealname"),"owner":OW.get(pr.get("hubspot_owner_id"),"(unassigned)"),
         "pipeline":CA.get(pr.get("dealstage")),"lead_source":pr.get("lead_source") or "(none)",
         "modified":(pr.get("hs_lastmodifieddate") or "")[:10],
         "notes":notes,"tasks":tasks}
    with lock:
        done["n"]+=1
        if done["n"]%40==0: print(f"  {done['n']}/{len(deals)}", flush=True)
    return row

with ThreadPoolExecutor(max_workers=8) as ex:
    rows=list(ex.map(work, deals))

json.dump(rows, open(os.path.join(HERE,"ca_notes_tasks.json"),"w",encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---------- summary ----------
print("\n" + "="*72)
print("SPLIT ACROSS OWNERS")
print("="*72)
g=collections.defaultdict(lambda: collections.Counter())
for r in rows: g[r["owner"]][r["pipeline"]]+=1
print(f"{'owner':<20}{'Scraped':>9}{'Campaign':>10}{'total':>8}{'with notes':>12}{'with tasks':>12}")
print("-"*72)
tot=collections.Counter()
for o in sorted(g,key=lambda k:-sum(g[k].values())):
    rs=[r for r in rows if r["owner"]==o]
    sc,cp=g[o]["Scraped"],g[o]["Campaign"]
    wn=sum(1 for r in rs if r["notes"]); wt=sum(1 for r in rs if r["tasks"])
    tot["s"]+=sc; tot["c"]+=cp; tot["wn"]+=wn; tot["wt"]+=wt
    print(f"{o:<20}{sc:>9}{cp:>10}{sc+cp:>8}{wn:>12}{wt:>12}")
print("-"*72)
print(f"{'TOTAL':<20}{tot['s']:>9}{tot['c']:>10}{tot['s']+tot['c']:>8}{tot['wn']:>12}{tot['wt']:>12}")

nn=sum(len(r["notes"]) for r in rows); nt=sum(len(r["tasks"]) for r in rows)
print(f"\n{nn} notes and {nt} tasks in total")
print(f"deals with NEITHER a note nor a task: {sum(1 for r in rows if not r['notes'] and not r['tasks'])}")

print("\n" + "="*72); print("TASK STATUS"); print("="*72)
for k,v in collections.Counter(t["status"] for r in rows for t in r["tasks"]).most_common():
    print(f"  {k or '(blank)':<22}{v}")
print("\ntask subjects (top 15):")
for k,v in collections.Counter(t["subject"][:60] for r in rows for t in r["tasks"]).most_common(15):
    print(f"  {v:>4}  {k}")
od=[t["due"] for r in rows for t in r["tasks"] if t["status"]!="COMPLETED" and t["due"]]
today=datetime.date.today().isoformat()
print(f"\nopen tasks past due: {sum(1 for d in od if d < today)} of {len(od)}")

print("\n" + "="*72); print("WHAT THE NOTES ACTUALLY SAY"); print("="*72)
PAT=[("not interested",r"not\s*interested|no\s*interest|not\s*keen|declin|refus"),
     ("no pickup / unreachable",r"no\s*(pick|answer|response|reply)|didn'?t\s*(pick|answer)|unreachable|not\s*reachable|ringing|rang"),
     ("wrong number",r"wrong\s*(number|no)|invalid\s*number|incorrect\s*number|number.*not.*valid"),
     ("busy / callback later",r"busy|call\s*(back|later)|reschedul|another\s*time|asked\s*to\s*call"),
     ("interested / positive",r"interested|keen|positive|follow\s*up|shared|sent\s*(the\s*)?(deck|script|mail)"),
     ("switchboard / gatekeeper",r"switchboard|reception|gatekeep|hr\s*said|transferred"),
     ("meeting",r"meet|gmeet|demo|call\s*scheduled|calendly")]
hits=collections.Counter(); unmatched=[]
for r in rows:
    blob=" ".join(n["text"] for n in r["notes"]).lower()
    if not blob: continue
    m=[lab for lab,p in PAT if re.search(p,blob)]
    if m:
        for lab in m: hits[lab]+=1
    else: unmatched.append(r)
print("(a deal can match more than one)")
for k,v in hits.most_common(): print(f"  {v:>4}  {k}")
print(f"\n{len(unmatched)} noted deals matched no pattern — first 10 note texts:")
for r in unmatched[:10]:
    print(f"  [{r['owner']}] {r['name'][:26]:<28} {r['notes'][0]['text'][:90]}")

print("\n" + "="*72); print("SAMPLE NOTES (20)"); print("="*72)
shown=0
for r in rows:
    if not r["notes"]: continue
    print(f"\n{r['owner']:<16}{r['name'][:30]:<32}{r['pipeline']}")
    for n in r["notes"][:2]:
        print(f"   {n['at']}  {n['text'][:150]}")
    for t in r["tasks"][:2]:
        print(f"   TASK [{t['status']}] due {t['due']}: {t['subject'][:70]}")
    shown+=1
    if shown>=20: break
print(f"\n\nfull detail -> ca_notes_tasks.json")
