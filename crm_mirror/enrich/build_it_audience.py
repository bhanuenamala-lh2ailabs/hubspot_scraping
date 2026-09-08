# -*- coding: utf-8 -*-
"""IT-services LinkedIn audience (target 300+): 113 net-new + Shreyas LIVE IT deals with full info
+ SALVAGEABLE dead IT deals (Claude reads the call note -> worth a LinkedIn re-contact?)."""
import os, json, re, csv, urllib.request, urllib.error, time, html
HERE=os.path.dirname(os.path.abspath(__file__)); HUB=os.path.dirname(os.path.dirname(HERE))
env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open(os.path.join(HUB,'.env'),encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
HS=env["hubspot_key"]; ANT=env["anthropic_api_key"]
def clean(s): return re.sub(r"\s+"," ",str(s or "").replace("\n"," ")).strip()
def call(path,method="GET",body=None):
    url="https://api.hubapi.com"+path; data=json.dumps(body).encode() if body is not None else None
    for a in range(4):
        try:
            req=urllib.request.Request(url,data=data,method=method,headers={"Authorization":"Bearer "+HS,"Content-Type":"application/json"})
            with urllib.request.urlopen(req,timeout=40) as r: t=r.read().decode(); return r.status,(json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code==429 and a<3: time.sleep(2); continue
            return e.code,{}
def get(p): return json.loads(urllib.request.urlopen(urllib.request.Request("https://api.hubapi.com"+p,headers={"Authorization":"Bearer "+HS})).read())
def claude_salvage(company, note):
    prompt=(f"IT-services firm '{company}' was cold-called for a CODEBASE-ACQUISITION deal and marked DEAD. "
            f"Call note: \"{note[:600]}\"\n"
            "Is there anything here suggesting they're worth ONE more soft touch via a LinkedIn message "
            "(e.g. wrong timing, busy/call-back-later, wrong person but a referral, soft/price rejection, "
            "conditional interest)? Answer NO if it's a hard dead-end (scam, firmly not interested, defunct, "
            "wrong-number, no product). Return ONLY JSON {\"salvage\":true|false}.")
    body=json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":30,"messages":[{"role":"user","content":prompt}]}).encode()
    req=urllib.request.Request("https://api.anthropic.com/v1/messages",data=body,method="POST",headers={"x-api-key":ANT,"anthropic-version":"2023-06-01","content-type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=40) as r: d=json.loads(r.read().decode())
        t="".join(c.get("text","") for c in d.get("content",[])); m=re.search(r"\{.*\}",t,re.S)
        return bool(json.loads(m.group(0)).get("salvage")) if m else False
    except Exception: return False

stage={x["id"]:x["label"] for pid in ("default","2425754306") for x in get(f"/crm/v3/pipelines/deals/{pid}").get("stages",[])}
# 1) all Shreyas IT-services deals
after=None; deals=[]
while True:
    b={"limit":100,"properties":["dealname","dealstage"],"filterGroups":[{"filters":[
        {"propertyName":"scraped_type","operator":"EQ","value":"ITservices"},
        {"propertyName":"hubspot_owner_id","operator":"EQ","value":"166420402"}]}]}
    if after: b["after"]=after
    s,d=call("/crm/v3/objects/deals/search","POST",b); deals+=d.get("results",[]); after=d.get("paging",{}).get("next",{}).get("after")
    if not after: break
    time.sleep(0.03)
print(f"Shreyas IT deals: {len(deals)}", flush=True)
# 2) contacts
d2c={}
for i in range(0,len(deals),100):
    s,d=call("/crm/v4/associations/deals/contacts/batch/read","POST",{"inputs":[{"id":x["id"]} for x in deals[i:i+100]]})
    for r in d.get("results",[]):
        tos=[str(t["toObjectId"]) for t in r.get("to",[])]
        if tos: d2c[str(r["from"]["id"])]=tos[0]
    time.sleep(0.03)
cids=list(set(d2c.values())); contacts={}
for i in range(0,len(cids),100):
    s,d=call("/crm/v3/objects/contacts/batch/read","POST",{"properties":["firstname","lastname","email","jobtitle"],"inputs":[{"id":c} for c in cids[i:i+100]]})
    for r in d.get("results",[]): contacts[str(r["id"])]=r.get("properties",{})
    time.sleep(0.03)
def row_of(x):
    comp=clean(x["properties"].get("dealname")); c=contacts.get(d2c.get(str(x["id"]),""),{})
    fn=clean(c.get("firstname")); ln=clean(c.get("lastname")); em=clean(c.get("email"))
    if not (comp and (em or (fn and ln))): return None
    return {"email":em,"firstname":fn,"lastname":ln,"jobtitle":clean(c.get("jobtitle")) or "Founder","employeecompany":comp,"country":"IN","googleaid":""}
live=[]; deadeals=[]
for x in deals:
    lab=stage.get(x["properties"].get("dealstage"),"")
    (deadeals if lab.startswith("Dead") else live).append(x)
live_rows=[r for r in (row_of(x) for x in live) if r]
print(f"live IT deals w/ full info: {len(live_rows)} | dead to review: {len(deadeals)}", flush=True)
# 3) salvage dead via notes
salv=[]; checked=0
for x in deadeals:
    r=row_of(x)
    if not r: continue
    s,a=call(f"/crm/v4/objects/deals/{x['id']}/associations/notes")
    nids=[str(t["toObjectId"]) for t in a.get("results",[])]
    body=""
    if nids:
        s,nb=call("/crm/v3/objects/notes/batch/read","POST",{"properties":["hs_note_body"],"inputs":[{"id":n} for n in nids]})
        for n in nb.get("results",[]):
            raw=n["properties"].get("hs_note_body","") or ""; raw=html.unescape(re.sub("<[^>]+>"," ",raw))
            if raw.strip(): body+=" "+raw.strip()
    checked+=1
    if body.strip() and claude_salvage(r["employeecompany"], clean(body)):
        salv.append(r)
    if checked%25==0: print(f"  reviewed {checked}/{len(deadeals)} dead -> salvaged {len(salv)}", flush=True)
    time.sleep(0.1)
print(f"salvageable dead: {len(salv)}", flush=True)
# 4) combine with 113 net-new + dedup
netnew=list(csv.DictReader(open(os.path.join(HUB,"exports/linkedin_audiences/LinkedIn_Ads_ITservices_NetNew.csv"),encoding="utf-8")))
out=[]; seen=set()
for src in (netnew, live_rows, salv):
    for r in src:
        k=((r.get("email") or "").lower() or (r["firstname"]+r["lastname"]).lower(), r["employeecompany"].lower())
        if k in seen: continue
        seen.add(k); out.append(r)
with open(os.path.join(HUB,"exports/linkedin_audiences/LinkedIn_Ads_ITservices_Audience.csv"),"w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=["email","firstname","lastname","jobtitle","employeecompany","country","googleaid"]); w.writeheader(); w.writerows(out)
print(f"\nIT AUDIENCE = {len(out)} rows (net-new {len(netnew)} + live {len(live_rows)} + salvaged-dead {len(salv)}, deduped) | with_email={sum(1 for r in out if r['email'])}", flush=True)
