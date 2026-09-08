# -*- coding: utf-8 -*-
"""Phase 3 — move every deal off `Call Attempted` onto a stage that names an outcome.

Classification reads the deal's own notes and tasks. Rule order matters and is deliberate:
the most decisive evidence wins. "wrong number" beats "call back" because a note saying
"anila jain wrong no atul need to call again" is really about a bad number.

Anything with no evidence goes to `No Pickup` — not to a dead stage. We do not know that
nobody answered; we know only that nothing was recorded, and `No Pickup` is the honest
place for that because it keeps the lead workable.

Usage:
  python mig_p3_migrate.py            -> writes the review CSV, changes nothing
  python mig_p3_migrate.py --apply    -> executes the moves in the CSV
"""
import os, sys, csv, json, re, time, datetime, collections, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); HUB=os.path.dirname(ROOT)
HOLD=os.path.join(ROOT,"holding"); os.makedirs(HOLD, exist_ok=True)
env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open(os.path.join(HUB,'.env'),encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
H={"Authorization":"Bearer "+env["hubspot_key"],"Content-Type":"application/json"}
APPLY="--apply" in sys.argv
STAMP=datetime.date.today().isoformat()
CSVP=os.path.join(HOLD, f"call_attempted_migration_{STAMP}.csv")

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
# stage id lookup PER PIPELINE — the two pipelines use different ids for the same label
SID={p["id"]: {s["label"]: s["id"] for s in p["stages"]} for p in PS}
CA={p["id"]: SID[p["id"]]["Call Attempted"] for p in PS}
OW={o["id"]:f"{o.get('firstName','')} {o.get('lastName','')}".strip()
    for o in hs("/crm/v3/owners?limit=200")[1]["results"]}

RULES=[("Dead/ColdCall/WrongNumber",
        r"wrong\s*(number|no\b)|invalid\s*number|out of service|not in service|"
        r"switched off|does not exist|incorrect number"),
       ("Dead/ColdCall/Not Interested",
        r"not\s*interested|no\s*interest|not\s*keen|declin|refus|already sold|no codebase"),
       ("Interested",
        r"\binterested\b|keen|wants? (to|more)|send (the )?(deck|details|script)|"
        r"asked (for|to send)"),
       ("No Pickup",
        r"no\s*(pick|answer|response)|did\s*n.?t\s*(pick|answer|connect)|didint pick|"
        r"unreachable|not reachable|rang|ringing|busy|call\s*back|callback|\bcb\b|"
        r"switchboard|reception|automated|inbox|need to call")]

# ---------------- gather ----------------
deals=[];after=None
while True:
    b={"filterGroups":[{"filters":[{"propertyName":"dealstage","operator":"IN",
                                   "values":list(CA.values())}]}],
       "properties":["dealname","dealstage","pipeline","hubspot_owner_id","lead_source",
                     "hs_lastmodifieddate"],"limit":200}
    if after: b["after"]=after
    s,d=hs("/crm/v3/objects/deals/search","POST",b)
    deals+=d.get("results",[]); after=(d.get("paging") or {}).get("next",{}).get("after")
    if not after: break
    time.sleep(0.12)
print(f"{len(deals)} deals on Call Attempted\n")

cache={r["deal_id"]: r for r in json.load(open(os.path.join(HERE,"ca_notes_tasks.json"),
                                              encoding="utf-8"))} \
      if os.path.exists(os.path.join(HERE,"ca_notes_tasks.json")) else {}

rows=[]
for x in deals:
    did=x["id"]; pr=x["properties"]; pid=pr.get("pipeline")
    ev=cache.get(did)
    if ev is None:                      # not in the cached survey — fetch its notes now
        ev={"notes":[],"tasks":[]}
        s,a=hs(f"/crm/v4/objects/deals/{did}/associations/notes")
        for n in [y["toObjectId"] for y in (a.get("results") or [])][:10]:
            s,nn=hs(f"/crm/v3/objects/notes/{n}?properties=hs_note_body")
            b=re.sub(r"<[^>]+>"," ",(nn.get("properties") or {}).get("hs_note_body") or "")
            if b.strip(): ev["notes"].append({"text":re.sub(r"\s+"," ",b).strip()})
        s,a=hs(f"/crm/v4/objects/deals/{did}/associations/tasks")
        for t in [y["toObjectId"] for y in (a.get("results") or [])][:10]:
            s,tt=hs(f"/crm/v3/objects/tasks/{t}?properties=hs_task_subject")
            ev["tasks"].append({"subject":(tt.get("properties") or {}).get("hs_task_subject") or ""})
        time.sleep(0.03)

    blob=(" ".join(n.get("text","") for n in ev.get("notes",[])) + " " +
          " ".join(t.get("subject","") for t in ev.get("tasks",[]))).lower()
    dest, rule = "No Pickup", "no evidence recorded"
    for stage, pat in RULES:
        if re.search(pat, blob):
            dest, rule = stage, f"note matched: {pat[:34]}..."
            break

    # ---- STILL-WORKABLE OVERRIDE ----------------------------------------------
    # A note is rarely about one clean outcome. "anila jain wrong no atul need to call
    # again" trips the wrong-number rule, but the caller explicitly recorded that there is
    # another person still to ring. Killing that lead loses a live one; parking it at
    # No Pickup loses nothing, because No Pickup is recoverable and a dead stage is not.
    #
    # So: never send a deal to a DEAD stage when the same note either states an intent to
    # retry, or carries more no-answer evidence than dead-end evidence.
    if dest.startswith("Dead/"):
        retry = re.search(r"call again|re-?attempt|need to call|will get back|call back|"
                          r"callback|try again|reach out again", blob)
        n_dead = len(re.findall(RULES[0][1], blob)) + len(re.findall(RULES[1][1], blob))
        n_open = len(re.findall(RULES[3][1], blob))
        if retry or n_open > n_dead:
            rule = (f"was {dest}, kept workable — "
                    + ("caller recorded intent to retry" if retry
                       else f"{n_open} no-answer signals vs {n_dead} dead"))
            dest = "No Pickup"
    rows.append({"deal_id":did,"dealname":pr.get("dealname") or "",
                 "pipeline":"Scraped" if pid=="default" else "Campaign",
                 "owner":OW.get(pr.get("hubspot_owner_id"),"(unassigned)"),
                 "lead_source":pr.get("lead_source") or "",
                 "last_modified":(pr.get("hs_lastmodifieddate") or "")[:10],
                 "from_stage":"Call Attempted","to_stage":dest,"why":rule,
                 "evidence":(" | ".join(n.get("text","") for n in ev.get("notes",[]))[:300]
                             or "(no notes)")})

with open(CSVP,"w",newline="",encoding="utf-8-sig") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

c=collections.Counter(r["to_stage"] for r in rows)
print("proposed destinations:")
for k,v in c.most_common(): print(f"  {k:<34}{v:>5}")
changers=[r for r in rows if r["to_stage"]!="No Pickup"]
print(f"\n{len(changers)} deals change meaning (everything not going to No Pickup):")
for r in changers:
    print(f"  [{r['owner']:<16}] {r['dealname'][:26]:<28} -> {r['to_stage']:<30}")
    print(f"      {r['evidence'][:120]}")
print(f"\nreview CSV -> {CSVP}")

if not APPLY:
    print("\nDRY RUN — nothing moved. Review the CSV, then re-run with --apply")
    sys.exit()

# ---------------- execute ----------------
by_pipe=collections.defaultdict(list)
for r in rows:
    pid = "default" if r["pipeline"]=="Scraped" else "2425754306"
    by_pipe[pid].append(r)

moved=fail=0
log=[]
for pid, rs in by_pipe.items():
    for i in range(0,len(rs),100):
        chunk=rs[i:i+100]
        inputs=[{"id":r["deal_id"],
                 "properties":{"dealstage":SID[pid][r["to_stage"]]}} for r in chunk]
        s,resp=hs("/crm/v3/objects/deals/batch/update","POST",{"inputs":inputs})
        if s in (200,202):
            moved+=len(chunk)
            log+= [{"deal_id":r["deal_id"],"from":"Call Attempted","to":r["to_stage"],
                    "pipeline":r["pipeline"]} for r in chunk]
        else:
            fail+=len(chunk); print(f"  ! batch {s} {str(resp)[:200]}")
        time.sleep(0.3)

json.dump(log, open(os.path.join(HOLD,f"migration_applied_{STAMP}.json"),"w",
                    encoding="utf-8"), indent=1)
print(f"\nmoved {moved} deals" + (f", {fail} FAILED" if fail else ""))
print(f"log -> holding/migration_applied_{STAMP}.json")
