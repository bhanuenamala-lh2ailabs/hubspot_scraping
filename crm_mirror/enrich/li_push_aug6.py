# -*- coding: utf-8 -*-
"""Push the cumulative LinkedIn lead-gen form export to Ishpreet, deduped.

SOURCE — the two "Form - Jul 31 2026" exports are two ad sets of one campaign, so they are
unioned before dedup; the same person can fill the form under either ad.

DEDUP is three-layered, because none of the keys is reliable alone:
  1. within the file       — lead_id, then LinkedIn URL, then phone, then email
  2. against HubSpot       — LinkedIn URL, phone, email against every existing contact
  3. contact-vs-deal       — a matching CONTACT is not a matching LEAD. A contact with no
                             deal is a lead sitting in HubSpot that nobody is working, so it
                             gets a deal rather than being skipped as a duplicate.

PHONE GATE is absolute: no dialable +91 number, no push. See indian_number.py.

DEAL NAME is the company, never the person. There is no company field on a lead-gen form, so
it is derived from the email domain; a free-mail address leaves no company signal and falls
back to the person's name, flagged in the output so it can be fixed by hand.

Usage: python li_push_aug6.py [--apply]
"""
import os, sys, csv, json, re, time, collections, subprocess, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); HUB=os.path.dirname(ROOT)
sys.path.insert(0, HERE)
from indian_number import to_e164, classify

env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open(os.path.join(HUB,'.env'),encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
H={"Authorization":"Bearer "+env["hubspot_key"],"Content-Type":"application/json"}
ISHPREET="166322228"
SOURCE="Linkedin Campaign ( IT Services )"
DL=r"c:\Users\naani\Downloads"
FILES=["Lead generation  Aug 5 2026_Form  Jul 31 2026_leads_20250805_20260806.csv",
       "Lead generation  Bhanu Split_Form  Jul 31 2026_leads_20250805_20260806.csv"]
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

# ---- guard: a bulk owner write must not wake the mailer ----
try:
    q=subprocess.run(["schtasks","/query","/tn","LH2 VCF lead notifier","/fo","LIST","/v"],
                     capture_output=True,text=True,timeout=30).stdout
    if q.strip() and "Disabled" not in q:
        sys.exit("ABORT: 'LH2 VCF lead notifier' is armed — it would mail everyone.")
except FileNotFoundError: pass

def nli(u):
    u=(u or "").strip().lower().split("?")[0].rstrip("/")
    if not u: return ""
    u=re.sub(r"^https?://","",u); u=re.sub(r"^([a-z]{2}\.)?linkedin\.com","linkedin.com",u)
    return u.replace("www.","")
def nem(e): return (e or "").strip().lower()

def person(first, last):
    """LinkedIn's form lets people type a headline into the surname box.

    "Dipti Hait -" / "Enabling IT, Risk, Analytics, Cybersecurity, AI" is one person, not a
    first and last name. A comma or an over-long value means it is a headline, so drop it
    rather than write it into the contact record and every vCard downstream.
    """
    def tidy(s):
        s=(s or "").strip().strip('"').strip()
        s=re.sub(r"[^\w\s.'-]+","",s,flags=re.UNICODE)   # emoji, stray symbols
        return re.sub(r"[\s\-.]+$","",s).strip()
    f,l = tidy(first), tidy(last)
    if "," in (last or "") or len(l)>24: l=""
    return f,l

FREEMAIL={"gmail.com","yahoo.com","yahoo.in","yahoo.co.in","hotmail.com","outlook.com",
          "rediffmail.com","live.com","icloud.com","protonmail.com","aol.com","ymail.com"}
def company_from(email, first, last):
    dom=nem(email).split("@")[-1]
    if dom and dom not in FREEMAIL:
        base=dom.rsplit(".",1)[0]
        base=re.sub(r"\.(co|com|org|net|gov|ac)$","",base)
        return re.sub(r"[-_.]+"," ",base).strip().title(), True
    f,l=person(first,last)
    return (f+" "+l).strip(), False

# ---------------------------------------------------------------- 1. read + internal dedup
def clean_rows(path):
    """The export carries a doubled BOM, so the first header survives as '\\ufeff"lead_id"' —
    the leading BOM stops csv treating the quote as a quote. Strip both from every key."""
    out=[]
    for r in csv.DictReader(open(path,encoding="utf-8-sig")):
        out.append({(k or "").lstrip("﻿").strip().strip('"'):v for k,v in r.items()})
    return out

rows=[]
for f in FILES:
    got=clean_rows(os.path.join(DL,f))
    rows+=got
    print(f"  {f[:58]:<60}{len(got):>4} rows")
print(f"\n{len(rows)} rows across {len(FILES)} exports")
rows=[r for r in rows if (r.get("test_lead") or "").lower()!="true"]

seen=set(); uniq=[]; dupe_in_file=0
for r in rows:
    ph=to_e164(r.get("Phone number"))
    keys=[("id",r.get("lead_id")), ("li",nli(r.get("LinkedIn profile URL"))),
          ("ph",ph), ("em",nem(r.get("Email address")))]
    keys=[k for k in keys if k[1]]
    if any(k in seen for k in keys): dupe_in_file+=1; continue
    seen.update(keys); r["_phone"]=ph; uniq.append(r)
print(f"   {dupe_in_file} duplicates inside the exports -> {len(uniq)} unique people")

# ---------------------------------------------------------------- 2. phone gate
gated=[r for r in uniq if r["_phone"]]
blocked=[r for r in uniq if not r["_phone"]]
mob=sum(1 for r in gated if classify(r["_phone"])=="mobile")
print(f"   phone gate: {len(gated)} pass ({mob} mobile), {len(blocked)} BLOCKED (no +91)")

# ---------------------------------------------------------------- 3. against HubSpot
s,d=hs("/crm/v3/pipelines/deals")
CAMP=[p for p in d["results"] if p["label"]=="Campaign"][0]
COLD=[st["id"] for st in CAMP["stages"] if st["label"]=="Cold Call"][0]
LAB={st["id"]:st["label"] for p in d["results"] for st in p["stages"]}

contacts=[];after=None
while True:
    b={"limit":100,"properties":["email","phone","mobilephone","linkedin_url","firstname","lastname"]}
    if after: b["after"]=after
    s,r=hs("/crm/v3/objects/contacts/search","POST",b); contacts+=r.get("results",[])
    after=(r.get("paging") or {}).get("next",{}).get("after")
    if not after: break
    time.sleep(0.08)
print(f"\n   {len(contacts)} existing contacts pulled for matching")

EM,LI,PH={},{},{}
for c in contacts:
    p=c["properties"]
    if nem(p.get("email")): EM[nem(p["email"])]=c["id"]
    if nli(p.get("linkedin_url")): LI[nli(p["linkedin_url"])]=c["id"]
    for x in (p.get("phone"),p.get("mobilephone")):
        if to_e164(x): PH[to_e164(x)]=c["id"]

matched={r["lead_id"]:cid for r in gated for cid in
         [EM.get(nem(r.get("Email address"))) or LI.get(nli(r.get("LinkedIn profile URL")))
          or PH.get(r["_phone"])] if cid}
# does the matched contact already have a deal? a contact without one is NOT a duplicate lead
c2d={}
mids=sorted(set(matched.values()))
for i in range(0,len(mids),100):
    s,a=hs("/crm/v4/associations/contacts/deals/batch/read","POST",
           {"inputs":[{"id":x} for x in mids[i:i+100]]})
    for res in (a.get("results") or []):
        c2d[str(res.get("from",{}).get("id"))]=[str(t["toObjectId"]) for t in res.get("to",[])]
    time.sleep(0.08)

plan=[]
for r in gated:
    cid=matched.get(r["lead_id"])
    has_deal=bool(c2d.get(cid or "",[]))
    name,from_dom=company_from(r.get("Email address"), r.get("First name"), r.get("Last name"))
    fn,ln=person(r.get("First name"), r.get("Last name"))
    plan.append({"lead_id":r["lead_id"],"name":name,"named_from_domain":from_dom,
                 "first":fn,"last":ln,
                 "email":nem(r.get("Email address")),"phone":r["_phone"],
                 "li":(r.get("LinkedIn profile URL") or "").strip(),
                 "contact_id":cid,
                 "verdict":"already in pipeline" if has_deal else
                           ("contact exists, no deal" if cid else "net new")})

by=collections.Counter(x["verdict"] for x in plan)
print("\n" + "="*70)
print(f"{'verdict':<32}{'count':>6}")
print("-"*70)
for k in ("net new","contact exists, no deal","already in pipeline"):
    print(f"   {k:<29}{by.get(k,0):>6}")
print(f"   {'BLOCKED - no +91 number':<29}{len(blocked):>6}")
print("-"*70)
print(f"   {'TOTAL unique people':<29}{len(uniq):>6}")

push=[x for x in plan if x["verdict"]!="already in pipeline"]
print(f"\nwould push {len(push)} deals to Ishpreet, Campaign pipeline, Cold Call, "
      f'lead_source="{SOURCE}"')
noname=[x for x in push if not x["named_from_domain"]]
print(f"   {len(push)-len(noname)} named from the email domain, "
      f"{len(noname)} fall back to the person's name (free-mail, no company signal)")
if blocked:
    print("\nBLOCKED (no dialable +91) — not pushed:")
    for r in blocked:
        print(f'   {(r.get("First name") or "")+" "+(r.get("Last name") or ""):<28}'
              f'{(r.get("Phone number") or "").strip()[:24]:<26}{nem(r.get("Email address"))}')

if not APPLY:
    print("\nsample of what would be created:")
    for x in push[:12]:
        flag="" if x["named_from_domain"] else "   <- person name, no company signal"
        print(f'   {x["name"][:26]:<28}{x["first"]+" "+x["last"]:<24}{x["phone"]:<16}'
              f'{x["verdict"]}{flag}')
    print("\nDRY RUN — nothing written. Re-run with --apply")
    sys.exit()

# ---------------------------------------------------------------- 4. write
made=reused=fail=0
for x in push:
    cid=x["contact_id"]
    if not cid:
        props={"firstname":x["first"],"lastname":x["last"],"email":x["email"],
               "mobilephone":x["phone"],"phone":x["phone"],"hubspot_owner_id":ISHPREET}
        if x["li"]: props["linkedin_url"]=x["li"]
        s,r=hs("/crm/v3/objects/contacts","POST",{"properties":props})
        if s not in (200,201):
            # a contact can exist under an email we never indexed; reuse it rather than fail
            if "CONFLICT" in json.dumps(r).upper() and x["email"]:
                s2,f=hs("/crm/v3/objects/contacts/search","POST",
                        {"filterGroups":[{"filters":[{"propertyName":"email","operator":"EQ",
                                                     "value":x["email"]}]}],"limit":1})
                got=(f.get("results") or [None])[0]
                if got: cid=got["id"]; reused+=1
            if not cid: fail+=1; print(f'  ! contact {x["name"][:28]}: {s} {r}'); continue
        else: cid=r["id"]
    else: reused+=1
    # deal AFTER the contact exists, and associated in the same call — a deal-less contact or
    # a contact-less deal is exactly the orphan state this script exists to avoid
    s,r=hs("/crm/v3/objects/deals","POST",{"properties":{
        "dealname":x["name"],"pipeline":CAMP["id"],"dealstage":COLD,
        "lead_source":SOURCE,"hubspot_owner_id":ISHPREET,
        "linkedin_url":x["li"]},
        "associations":[{"to":{"id":cid},"types":[{"associationCategory":"HUBSPOT_DEFINED",
                                                   "associationTypeId":3}]}]})
    if s not in (200,201): fail+=1; print(f'  ! deal {x["name"][:28]}: {s} {r}'); continue
    x["deal_id"]=r["id"]; made+=1
    hs(f"/crm/v3/objects/contacts/{cid}","PATCH",{"properties":{"hubspot_owner_id":ISHPREET}})
    time.sleep(0.1)

print(f"\ncreated {made} deals ({reused} reused an existing contact)"
      + (f", {fail} FAILED" if fail else ""))
json.dump(plan, open(os.path.join(HERE,"li_push_aug6.json"),"w",encoding="utf-8"),
          ensure_ascii=False, indent=1)
