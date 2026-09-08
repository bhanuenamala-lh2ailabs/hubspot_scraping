# -*- coding: utf-8 -*-
"""Backfill LinkedIn URL onto the searchByQuery leads already pushed. The reveal returned the
URL (in social links) but the first push discarded it. Re-reveal by the stored uid (cached =
free), read the /in/ URL, PATCH the deal's associated contact. Idempotent."""
import json, os, urllib.request, urllib.error, time
env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open("../../.env",encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
H={"Authorization":"Bearer "+env["hubspot_key"],"Content-Type":"application/json"}; SH=env["signal_hire"]
def hs(u,m="GET",b=None):
    d=json.dumps(b).encode() if b is not None else None
    for a in range(5):
        try:
            r=urllib.request.Request("https://api.hubapi.com"+u,data=d,method=m,headers=H)
            with urllib.request.urlopen(r,timeout=40) as x: t=x.read().decode(); return x.status,(json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in(429,500,502,503,504) and a<4: time.sleep(2*(a+1)); continue
            return e.code,{}
        except Exception:
            if a==4: raise
            time.sleep(2)
def reveal_li(uid):
    r=urllib.request.Request("https://www.signalhire.com/api/v1/candidate/search",
        data=json.dumps({"items":[uid],"withoutWaterfall":True}).encode(),method="POST",
        headers={"apikey":SH,"Content-Type":"application/json"})
    try: d=json.loads(urllib.request.urlopen(r,timeout=60).read().decode())
    except Exception: return ""
    for it in (d if isinstance(d,list) else d.get("results",[])) or []:
        if isinstance(it,dict) and it.get("status")=="success":
            c=it.get("candidate") or {}
            return next((s.get("link") for s in (c.get("social") or []) if "linkedin.com/in/" in str(s.get("link") or "")),"")
    return ""
state={v['domain'] if 'domain' in v else k:v for k,v in json.load(open("searchq_state.json")).items()}
pushed=json.load(open("searchq_pushed.json"))
done=json.load(open("backfill_li_done.json")) if os.path.exists("backfill_li_done.json") else {}
ok=miss=skip=0
for dom,pv in pushed.items():
    if dom in done: skip+=1; continue
    st=json.load(open("searchq_state.json")).get(dom,{})
    uid=st.get("uid")
    if not uid: miss+=1; continue
    li=st.get("linkedin") or reveal_li(uid)
    if not li: miss+=1; continue
    # get the deal's associated contact
    s,a=hs(f"/crm/v4/objects/deals/{pv['deal']}/associations/contacts")
    cids=[str(x["toObjectId"]) for x in a.get("results",[])]
    if not cids: miss+=1; continue
    s,_=hs(f"/crm/v3/objects/contacts/{cids[0]}","PATCH",{"properties":{"linkedin_url":li}})
    if s==200: ok+=1; done[dom]=li; json.dump(done,open("backfill_li_done.json","w"))
    else: miss+=1
    if (ok+miss)%20==0: print(f"  {ok} patched, {miss} miss...",flush=True)
    time.sleep(0.2)
print(f"\nbackfilled LinkedIn onto {ok} contacts | {miss} missing | {skip} already done")
