# -*- coding: utf-8 -*-
"""Aug 5 LinkedIn Lead-Gen Form leads (2 ad batches) -> dedup -> enrich -> Ishpreet.

Dedup is three-way and deliberately wide, because the same person reaches us from more
than one ad and the ad form gives us no stable key across batches:
  * linkedin_url  — the reliable identity, normalised (strip www/http/query/trailing slash)
  * email
  * +91 phone
checked against LIVE deals, LIVE contacts, AND the archived/recycle-bin copies. A lead that
was pushed and later archived must not silently reappear as net-new.

Hard gate (unchanged, non-negotiable): no valid +91 mobile -> no push. Held back, not dropped.

Deal name = COMPANY, never the person, per the standing rule. Company comes from SignalHire;
where it cannot be resolved the person's name is the documented fallback.

Usage: python li_push_aug5.py [--apply]
"""
import json, os, re, sys, time, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); HUB=os.path.dirname(ROOT)
env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open(os.path.join(HUB,'.env'),encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
HS=env["hubspot_key"]; SH=env.get("signal_hire","")
# Cold Call (4002503379) lives in the CAMPAIGN pipeline, not "default"/Scraped. Sending
# the pair (default, 4002503379) is rejected with INVALID_OPTION.
ISHPREET="166322228"; PIPE="2425754306"; COLDCALL="4002503379"
LEAD_SOURCE="LinkedIn Lead-Gen Form - Jul 31 2026"
APPLY="--apply" in sys.argv

RAW=[
 # ad 1535540106 / campaign 865520086
 ("Arajit","Halder","arajithalder123@gmail.com","https://www.linkedin.com/in/arajit-halder-8804a2205"," +91 6295 577 953"),
 ("Saurabh","Bassi","saurabhbassi@yahoo.com","https://www.linkedin.com/in/saurabhbassi","9900036467"),
 ("Dr Bimal","John","bimaljohn@gmail.com","https://www.linkedin.com/in/drbimaljohn"," +91 98953 75279"),
 ("Vishwa","Akuthota","vishwanath.chintu@gmail.com","https://www.linkedin.com/in/vishwanathakuthota"," +91 70329 17578"),
 ("Amit","Suri","asuri07@gmail.com","https://www.linkedin.com/in/amitsuri-digitalbulbs"," +91 98103 07306"),
 ("Dheeraj","Jadhav","djking666@gmail.com","https://www.linkedin.com/in/dheeraj-jadhav-4270ab19","8618324041"),
 ("Karpaga","Prabhu","axigo.jp@gmail.com","https://www.linkedin.com/in/karpaga-prabhu-k3794","9486948740"),
 ("Akhthar","C","akhtharedv@gmail.com","https://www.linkedin.com/in/akhthar"," +91 98957 09543"),
 ("Rishabh","Srivastav","rishabhvv0@gmail.com","https://www.linkedin.com/in/rishabh-srivastav-1266521aa","7897775159"),
 # ad 1535320186 / campaign 865480156
 ("Shubham kumar","kushwaha","shubhamkush012@gmail.com","https://www.linkedin.com/in/shubham-kumar-kushwaha-038940249","8824013820"),
 ("Salath Joseph","A","salathjoseph@gmail.com","https://www.linkedin.com/in/salathjoseph"," +91 88380 32478"),
 ("shivprasad","Koirala","shiv_koirala@yahoo.com","https://www.linkedin.com/in/shivkoirala","9167370555"),
 ("Shweta","Patel","mazdiarpatel@gmail.com","https://www.linkedin.com/in/shweta-patel-sp"," +91 7709009897"),
 ("Navin","M","navin@optionmatrix.com","https://www.linkedin.com/in/navin-malik"," +91 98499 35911"),
 ("Vivek","Mittal","vivek@yugasa.com","https://www.linkedin.com/in/vivek4m"," +91 88003 32227"),
 ("Aayush","Jain","aayushjain6020@gmail.com","https://www.linkedin.com/in/aayush-jain-code","9630168508"),
 ("Chakravarthy","V P","chakravarthyvp@gmail.com","https://www.linkedin.com/in/chakravarthyvp"," +91 90801 64216"),
 ("Sandipan","Basu","noahsaark@gmail.com","https://www.linkedin.com/in/sandipan-basu-b67323335"," +91 80175 06074"),
]

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

def norm_li(u):
    u=(u or "").strip().lower().split("?")[0].rstrip("/")
    return u.replace("http://","https://").replace("https://www.","https://")

def india_phone(p):
    """The hard gate. Only a real +91 10-digit mobile passes."""
    raw=(p or "").strip(); d=re.sub(r"[^\d]","",raw)
    if raw.startswith("+1") or (len(d)==11 and d.startswith("1")): return ""
    if raw.startswith("+91") or (d.startswith("91") and len(d)==12): d=d[-10:]
    if len(d)==10 and d[0] in "6789": return "+91"+d
    return ""

def sh_company(li):
    """SignalHire by LinkedIn URL -> (company, headline). Cached reveals are free."""
    if not SH: return "",""
    body=json.dumps({"items":[li],"withoutWaterfall":True}).encode()
    req=urllib.request.Request("https://www.signalhire.com/api/v1/candidate/search",data=body,
        method="POST",headers={"apikey":SH,"Content-Type":"application/json"})
    try:
        rid=json.load(urllib.request.urlopen(req,timeout=40)).get("requestId")
    except Exception: return "",""
    for _ in range(20):
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

# ---------- build + in-batch dedup ----------
leads={}
for f,l,em,li,ph in RAW:
    k=norm_li(li)
    if k in leads: continue            # same person across both ads
    leads[k]={"first":f.strip(),"last":l.strip(),"email":(em or "").strip().lower(),
              "li":k,"raw_phone":ph,"e164":india_phone(ph)}
print(f"{len(RAW)} rows pasted -> {len(leads)} unique by linkedin_url\n")

# ---------- dedup vs HubSpot (live + archived) ----------
def find_deal(li, em, ph):
    for prop,val in (("linkedin_url",li),):
        if not val: continue
        s,r=hs("/crm/v3/objects/deals/search","POST",{"filterGroups":[{"filters":[
            {"propertyName":prop,"operator":"EQ","value":val}]}],
            "properties":["dealname","dealstage","hubspot_owner_id","lead_source"],"limit":1})
        if s==200 and r.get("results"): return r["results"][0],"live deal"
    return None,None

def find_contact(li, em, ph):
    filters=[]
    if li: filters.append(("linkedin_url",li))
    if em: filters.append(("email",em))
    if ph: filters.append(("phone",ph)); filters.append(("mobilephone",ph))
    for prop,val in filters:
        s,r=hs("/crm/v3/objects/contacts/search","POST",{"filterGroups":[{"filters":[
            {"propertyName":prop,"operator":"EQ","value":val}]}],
            "properties":["email","firstname","lastname","hubspot_owner_id"],"limit":1})
        if s==200 and r.get("results"): return r["results"][0],f"live contact ({prop})"
    return None,None

new=[]; dupes=[]; gated=[]
for k,x in leads.items():
    if not x["e164"]:
        gated.append(x); continue
    d,why=find_deal(x["li"], x["email"], x["e164"])
    if d:
        x["existing"]=d; x["why"]=why; dupes.append(x); continue
    c,why=find_contact(x["li"], x["email"], x["e164"])
    if c:
        x["existing"]=c; x["why"]=why; dupes.append(x); continue
    new.append(x)

print(f"already in HubSpot : {len(dupes)}")
for x in dupes:
    p=x["existing"]["properties"]
    nm=p.get("dealname") or f"{p.get('firstname','')} {p.get('lastname','')}".strip()
    print(f"   {x['first']} {x['last']:<14} -> {x['why']:<26} {nm}")
print(f"\nheld back (no +91) : {len(gated)}")
for x in gated: print(f"   {x['first']} {x['last']}  raw={x['raw_phone']!r}")
print(f"\nNET-NEW to push    : {len(new)}")
for x in new: print(f"   {x['first']} {x['last']:<16} {x['e164']}  {x['email']}")

json.dump({"new":new,"dupes":[{k:v for k,v in x.items() if k!='existing'} for x in dupes],
           "gated":gated}, open(os.path.join(HERE,"li_aug5_dedup.json"),"w",encoding="utf-8"),
          ensure_ascii=False, indent=1)

if not APPLY:
    print("\nDRY RUN — nothing written. Re-run with --apply"); sys.exit()

# ---------- enrich + push ----------
pushed=[]
for x in new:
    comp,head=sh_company(x["li"])
    x["company"]=comp; x["headline"]=head
    person=f"{x['first']} {x['last']}".strip()
    dn=deal_name(comp, person)
    cp={"firstname":x["first"],"lastname":x["last"],"email":x["email"],
        "mobilephone":x["e164"],"phone":x["e164"],"linkedin_url":x["li"],
        "hubspot_owner_id":ISHPREET,"jobtitle":head[:100] if head else "",
        "company":comp}
    s,c=hs("/crm/v3/objects/contacts","POST",{"properties":{k:v for k,v in cp.items() if v}})
    if s not in (200,201):
        print(f"  ! contact {person}: {s} {c}"); continue
    ctid=c["id"]
    dp={"dealname":dn,"pipeline":PIPE,"dealstage":COLDCALL,"hubspot_owner_id":ISHPREET,
        "lead_source":LEAD_SOURCE,"linkedin_url":x["li"]}
    s,d=hs("/crm/v3/objects/deals","POST",{"properties":dp})
    if s not in (200,201):
        print(f"  ! deal {dn}: {s} {d}"); continue
    hs(f"/crm/v4/objects/deals/{d['id']}/associations/default/contacts/{ctid}","PUT")
    x["contact_id"]=ctid; x["deal_id"]=d["id"]; x["deal_name"]=dn
    pushed.append(x)
    print(f"  + {dn:<32} <- {person} ({comp or 'no company'})")
    time.sleep(0.2)

json.dump(pushed, open(os.path.join(HERE,"li_aug5_pushed.json"),"w",encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"\npushed {len(pushed)} new deals to Ishpreet -> li_aug5_pushed.json")
