# -*- coding: utf-8 -*-
"""Repair: the push created 13 contacts, then every deal failed on a bad pipeline id.

That left 13 contacts in HubSpot with no deal — invisible to the pipeline and to whoever
owns the queue. This finishes the job: reuse the contact that already exists (never create
a second one), enrich for the company name, create the deal in the CAMPAIGN pipeline, and
associate the two.

Idempotent: a contact that already has a Lead-Gen deal is skipped, so re-running is safe.

Usage: python li_repair_aug5.py [--apply]
"""
import json, os, sys, time, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); HUB=os.path.dirname(ROOT)
env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open(os.path.join(HUB,'.env'),encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
HS=env["hubspot_key"]; SH=env.get("signal_hire","")
ISHPREET="166322228"; PIPE="2425754306"; COLDCALL="4002503379"
LEAD_SOURCE="LinkedIn Lead-Gen Form - Jul 31 2026"
APPLY="--apply" in sys.argv

def hs(path, method="GET", body=None):
    url="https://api.hubapi.com"+path; data=json.dumps(body).encode() if body is not None else None
    for a in range(5):
        try:
            req=urllib.request.Request(url,data=data,method=method,headers={"Authorization":"Bearer "+HS,"Content-Type":"application/json"})
            with urllib.request.urlopen(req,timeout=40) as r:
                t=r.read().decode(); return r.status,(json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504) and a<4: time.sleep(2*(a+1)); continue
            return e.code,{"raw":e.read().decode()[:300]}
        except Exception:
            if a==4: raise
            time.sleep(2)

def sh_company(li):
    if not SH: return "",""
    body=json.dumps({"items":[li],"withoutWaterfall":True}).encode()
    req=urllib.request.Request("https://www.signalhire.com/api/v1/candidate/search",data=body,
        method="POST",headers={"apikey":SH,"Content-Type":"application/json"})
    try: rid=json.load(urllib.request.urlopen(req,timeout=40)).get("requestId")
    except Exception: return "",""
    for _ in range(15):
        time.sleep(3)
        try:
            r=urllib.request.Request(f"https://www.signalhire.com/api/v1/candidate/search/{rid}",headers={"apikey":SH})
            res=json.load(urllib.request.urlopen(r,timeout=40))
        except Exception: continue
        if not isinstance(res,list) or not res: continue
        it=res[0]
        if it.get("status")=="in progress": continue
        c=it.get("candidate") or {}
        exp=c.get("experience") or []
        cur=[e for e in exp if e.get("current")]
        comp=(cur[0].get("company") if cur else (exp[0].get("company") if exp else "")) or ""
        return comp, c.get("headLine") or ""
    return "",""

_NOT_A_COMPANY={"self-employed","self employed","freelance","freelancer","independent",
                "independent consultant","none","n/a","-","unemployed","student","retired"}
def deal_name(company, person):
    c=(company or "").strip()
    if c and c.lower() not in _NOT_A_COMPANY: return c
    return (person or "").strip() or "LinkedIn lead"

# corporate email domain is a free, reliable company hint when SignalHire has nothing
FREEMAIL={"gmail.com","yahoo.com","yahoo.co.in","hotmail.com","outlook.com","rediffmail.com",
          "icloud.com","zoho.com","protonmail.com"}
def from_email(em):
    d=(em or "").split("@")[-1].lower()
    if not d or d in FREEMAIL: return ""
    return d.split(".")[0].replace("-"," ").title()

new=json.load(open(os.path.join(HERE,"li_aug5_dedup.json"),encoding="utf-8"))["new"]
print(f"{len(new)} leads to repair\n")

done=[]
for x in new:
    person=f"{x['first']} {x['last']}".strip()
    s,r=hs("/crm/v3/objects/contacts/search","POST",{"filterGroups":[{"filters":[
        {"propertyName":"email","operator":"EQ","value":x["email"]}]}],
        "properties":["email","hubspot_owner_id"],"limit":1})
    c=(r.get("results") or [None])[0]
    if not c:
        print(f"  ? {person}: contact missing — will create"); ctid=None
    else:
        ctid=c["id"]
        s,a=hs(f"/crm/v4/objects/contacts/{ctid}/associations/deals")
        if (a.get("results") or []):
            print(f"  = {person}: already has a deal, skipping"); continue

    comp,head=sh_company(x["li"])
    if not comp: comp=from_email(x["email"])
    dn=deal_name(comp, person)
    print(f"  + {dn:<30} <- {person:<24} ({comp or 'no company'})")
    if not APPLY: continue

    if not ctid:
        cp={"firstname":x["first"],"lastname":x["last"],"email":x["email"],
            "mobilephone":x["e164"],"phone":x["e164"],"linkedin_url":x["li"],
            "hubspot_owner_id":ISHPREET,"company":comp}
        s,c=hs("/crm/v3/objects/contacts","POST",{"properties":{k:v for k,v in cp.items() if v}})
        if s not in (200,201): print(f"    ! contact {s} {c}"); continue
        ctid=c["id"]
    elif comp or head:
        hs(f"/crm/v3/objects/contacts/{ctid}","PATCH",{"properties":{
            k:v for k,v in {"company":comp,"jobtitle":head[:100] if head else ""}.items() if v}})

    dp={"dealname":dn,"pipeline":PIPE,"dealstage":COLDCALL,"hubspot_owner_id":ISHPREET,
        "lead_source":LEAD_SOURCE,"linkedin_url":x["li"]}
    s,d=hs("/crm/v3/objects/deals","POST",{"properties":dp})
    if s not in (200,201): print(f"    ! deal {s} {d}"); continue
    hs(f"/crm/v4/objects/deals/{d['id']}/associations/default/contacts/{ctid}","PUT")
    x.update({"contact_id":ctid,"deal_id":d["id"],"deal_name":dn,"company":comp,"headline":head})
    done.append(x); time.sleep(0.2)

if APPLY:
    json.dump(done, open(os.path.join(HERE,"li_aug5_pushed.json"),"w",encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\ncreated {len(done)} deals -> li_aug5_pushed.json")
else:
    print("\nDRY RUN — re-run with --apply")
