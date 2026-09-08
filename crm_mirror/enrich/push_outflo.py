# -*- coding: utf-8 -*-
"""Push ENGAGED OutFlo leads -> HubSpot Campaign pipeline.
  India   -> SignalHire-enriched (phone/email) -> owner Ishpreet
  Indonesia -> NO enrichment                    -> owner Shobit
Priority: replied=high, connected=medium. Dedup by linkedin_url (reassign existing, create new).
Usage: python push_outflo.py [--dry-run] [--limit N] [--bucket India|Indonesia]
"""
import json, os, re, sys, time, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # OutFlo names carry emoji/unicode
except Exception: pass
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); HUB=os.path.dirname(ROOT)
env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open(os.path.join(HUB,'.env'),encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
HS=env["hubspot_key"]; SH=env["signal_hire"]
PIPE="2425754306"; COLDCALL="4002503379"
CFG={"India":{"owner":"166322228","name":"Ishpreet Sood","ls":"Outflo Outreach – India","enrich":True},
     "Indonesia":{"owner":"166262056","name":"Shobit Gupta","ls":"Outflo Outreach – Indonesia","enrich":False}}
def norm_li(u):
    u=(u or "").strip().lower().split("?")[0].rstrip("/")
    return u.replace("http://","https://").replace("https://www.","https://")
def hs(path,method="GET",body=None):
    url="https://api.hubapi.com"+path; data=json.dumps(body).encode() if body is not None else None
    for a in range(5):
        try:
            req=urllib.request.Request(url,data=data,method=method,headers={"Authorization":"Bearer "+HS,"Content-Type":"application/json"})
            with urllib.request.urlopen(req,timeout=40) as r: t=r.read().decode(); return r.status,(json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504) and a<4: time.sleep(2*(a+1)); continue
            return e.code,{"raw":e.read().decode()[:200]}
        except Exception:
            if a==4: raise
            time.sleep(2)
FREEMAIL={"gmail.com","yahoo.com","yahoo.co.in","hotmail.com","outlook.com","rediffmail.com","icloud.com","zoho.com","protonmail.com"}
def india_phone(p):
    raw=(p or "").strip(); d=re.sub(r"[^\d]","",raw)
    if raw.startswith("+1") or (len(d)==11 and d.startswith("1")): return ""
    if raw.startswith("+91") or (d.startswith("91") and len(d)==12):
        d=d[-10:]; return "+91"+d if len(d)==10 and d[0] in "23456789" else ""
    if len(d)==10 and d[0] in "6789": return "+91"+d
    if len(d)==10 and d[0] in "2345678": return "+91"+d
    return ""
def sh_enrich(ident):
    if not ident: return [],[]
    body=json.dumps({"items":[ident],"withoutWaterfall":True}).encode()
    req=urllib.request.Request("https://www.signalhire.com/api/v1/candidate/search",data=body,method="POST",headers={"apikey":SH,"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=60) as r: d=json.loads(r.read().decode())
    except Exception: return [],[]
    res=d if isinstance(d,list) else d.get("results",[])
    ph,em=[],[]
    for it in res or []:
        if isinstance(it,dict) and it.get("status")=="success":
            for c in (it.get("candidate",{}) or {}).get("contacts",[]) or []:
                t=str(c.get("type","")).lower(); v=c.get("value")
                if not isinstance(v,str): continue
                if "phone" in t: ph.append(v)
                elif "email" in t and "@" in v: em.append(v)
    return ph,em
# A deal is named after the COMPANY — that is the pointer we work with. Only fall back to
# the person when OutFlo has no real company (99% of leads do) or reports a non-company
# placeholder like "Self-employed", which is a person, not an acquisition target.
_NOT_A_COMPANY = {"self-employed","self employed","selfemployed","freelance","freelancer",
                  "independent","independent consultant","none","n/a","-","unemployed",
                  "student","retired","private","confidential"}
def deal_name(company, person):
    c = (company or "").strip()
    if c and c.lower() not in _NOT_A_COMPANY: return c
    return (person or "").strip() or "OutFlo lead"

def main():
    dry="--dry-run" in sys.argv; new_only="--new-only" in sys.argv; limit=None; only_bucket=None
    for i,a in enumerate(sys.argv):
        if a=="--limit": limit=int(sys.argv[i+1])
        if a=="--bucket": only_bucket=sys.argv[i+1]
    L=json.load(open(os.path.join(ROOT,"outflo","leads.json"),encoding="utf-8"))
    eng=[x for x in L if (x.get('reply')=='Replied' or x.get('conn')=='Connected') and x.get('linkedin')]
    if only_bucket: eng=[x for x in eng if x['bucket']==only_bucket]
    # replied first (hot), then connected
    eng.sort(key=lambda x: 0 if x.get('reply')=='Replied' else 1)
    if limit: eng=eng[:limit]
    pushed=[]; created=updated=0
    for x in eng:
        b=x['bucket']; cfg=CFG.get(b)
        if not cfg: continue
        li=x['linkedin']; nli=norm_li(li)
        replied=x.get('reply')=='Replied'; prio="high" if replied else "medium"
        first=x.get('first') or (x.get('name') or '').split(' ')[0]; last=x.get('last') or ' '.join((x.get('name') or '').split(' ')[1:])
        comp=x.get('company') or ''; title=x.get('title') or ''
        def enrich():
            if not cfg["enrich"]: return "", ""
            ph,em=sh_enrich(li)
            return (next((india_phone(p) for p in ph if india_phone(p)),""),
                    next((e for e in em if "@" in e),""))
        if dry:
            phone,email=enrich()
            pushed.append({"bucket":b,"name":x.get('name'),"company":comp,"linkedin":li,"owner":cfg["name"],"prio":prio,"replied":replied,"phone":phone,"email":email})
            print(f"  {b[:4]} {'REPL' if replied else 'conn'} {(x.get('name') or '')[:22]:22} {comp[:20]:20} -> {cfg['name'][:8]:8} ph={phone or '-':14} em={email or '-'}",flush=True)
            continue
        # dedup deal FIRST so new-only skips existing WITHOUT spending an enrich credit
        s,d=hs("/crm/v3/objects/deals/search","POST",{"filterGroups":[{"filters":[{"propertyName":"linkedin_url","operator":"EQ","value":li}]}],"properties":["dealname","dealstage"],"limit":1})
        did=d["results"][0]["id"] if d.get("results") else None
        if did and new_only:                          # already in HubSpot -> leave untouched, no enrich
            continue
        phone,email=enrich()
        rec={"bucket":b,"name":x.get('name'),"company":comp,"linkedin":li,"owner":cfg["name"],
             "prio":prio,"replied":replied,"phone":phone,"email":email}
        dprops={"pipeline":PIPE,"hubspot_owner_id":cfg["owner"],"poc":cfg["owner"],"hs_priority":prio,
                "lead_source":cfg["ls"],"linkedin_url":li,"scraped_type":""}
        if did:
            hs(f"/crm/v3/objects/deals/{did}","PATCH",{"properties":{k:v for k,v in dprops.items() if v}}); updated+=1
        else:
            dprops["dealname"]=deal_name(comp, x.get("name")); dprops["dealstage"]=COLDCALL
            s,d=hs("/crm/v3/objects/deals","POST",{"properties":{k:v for k,v in dprops.items() if v}}); did=d.get("id"); created+=1
            if not did: print("  ERR deal",x.get('name'),d,flush=True); continue
        # contact by linkedin (then email)
        ctid=None
        s,d=hs("/crm/v3/objects/contacts/search","POST",{"filterGroups":[{"filters":[{"propertyName":"linkedin_url","operator":"EQ","value":li}]}],"properties":["email"],"limit":1})
        ctid=d["results"][0]["id"] if d.get("results") else None
        cp={"firstname":first or comp,"lastname":last,"company":comp,"jobtitle":title,"linkedin_url":li}
        if email: cp["email"]=email
        if phone: cp["phone"]=phone; cp["mobilephone"]=phone
        if ctid: hs(f"/crm/v3/objects/contacts/{ctid}","PATCH",{"properties":{k:v for k,v in cp.items() if v}})
        else:
            s,d=hs("/crm/v3/objects/contacts","POST",{"properties":{k:v for k,v in cp.items() if v}}); ctid=d.get("id")
        # company by name
        coid=None
        if comp:
            s,d=hs("/crm/v3/objects/companies/search","POST",{"filterGroups":[{"filters":[{"propertyName":"name","operator":"EQ","value":comp}]}],"properties":["name"],"limit":1})
            coid=d["results"][0]["id"] if d.get("results") else None
            if not coid:
                s,d=hs("/crm/v3/objects/companies","POST",{"properties":{"name":comp}}); coid=d.get("id")
        time.sleep(0.25)
        hs(f"/crm/v4/objects/deals/{did}/associations/default/contacts/{ctid}","PUT")
        if coid: hs(f"/crm/v4/objects/deals/{did}/associations/default/companies/{coid}","PUT")
        rec["deal_id"]=did; pushed.append(rec)
        print(f"  {'NEW' if not d.get('updated') else 'UPD'} {b[:4]} {(x.get('name') or '')[:20]:20} -> {cfg['name'][:8]:8} {prio:6} ph={phone or '-':14} deal={did}",flush=True)
        json.dump(pushed,open(os.path.join(HERE,"pushed_outflo.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
        time.sleep(0.12)
    from collections import Counter
    print(f"\n{'DRY' if dry else 'DONE'} engaged={len(eng)} | by bucket:",dict(Counter(r['bucket'] for r in pushed)),
          f"| created={created} updated={updated}" if not dry else "")
if __name__=="__main__": main()
