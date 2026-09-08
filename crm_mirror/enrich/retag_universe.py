# -*- coding: utf-8 -*-
"""Fold every lead_source onto the five-source universe.

  Private Codebase Tracker sheet ( IT services )
  Tracxn Sheet ( Startups )
  Scraping Algo ( IT services | Startups )
  Outflo Outreach ( IT services | Startups )
  Linkedin Campaign ( IT Services )

`LH2 Pipeline` resolves to the scraping algo on evidence, not assumption: 106 of 106 of its
deals are present in the GoodFirms scrape database, and none are in the Codebase Tracker sheet.

Usage: python retag_universe.py [--apply]
"""
import json, os, sys, re, time, sqlite3, collections, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); HUB=os.path.dirname(ROOT)
env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open(os.path.join(HUB,'.env'),encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
H={"Authorization":"Bearer "+env["hubspot_key"],"Content-Type":"application/json"}
APPLY="--apply" in sys.argv

PCT   = "Private Codebase Tracker sheet ( IT services )"
TRX   = "Tracxn Sheet ( Startups )"
SCR_I = "Scraping Algo ( IT services )"
SCR_S = "Scraping Algo ( Startups )"
OUT_I = "Outflo Outreach ( IT services )"
OUT_S = "Outflo Outreach ( Startups )"
LIN   = "Linkedin Campaign ( IT Services )"
UNIVERSE=[PCT,TRX,SCR_I,SCR_S,OUT_I,OUT_S,LIN]

MAP = {
    "GoodFirms":                                            SCR_I,
    "LH2 Pipeline":                                         SCR_I,   # proven: 106/106 in scrape DB
    "Scraped ( IT Services )":                              SCR_I,
    "Scraped ( Startups )":                                 SCR_S,
    "Tracxn ( Startups )":                                  TRX,
    "LH2 Distress":                                         TRX,
    "Outflo Outreach - India":                              OUT_S,
    "Outflo Outreach – India":                              OUT_S,   # en-dash variant
    "Outflo ( Startups )":                                  OUT_S,
    "OutFlo Replied - Relevance Check":                     OUT_S,
    "Outflo Outreach - Indonesia":                          OUT_S,
    "Linkedin Message ( IT services )":                     LIN,
    "LinkedIn Message Campaign (IT Services)":              LIN,
    "LinkedIn Lead-Gen Form - Jul 31 2026":                 LIN,
    "LinkedIn Lead-Gen Form - ITservices_targeted_message": LIN,
    "LinkedIn Pilot - ITServices (inbound form)":           LIN,
}
# LinkedIn Sales Navigator is deliberately NOT mapped. It was a manual Sales Navigator export,
# not an ad campaign, and its companies (Sarvam, Blackboard, Suki, Instawork, FlexAI) are
# product startups rather than IT services — so it fits neither LinkedIn Campaign (IT-only
# for now) nor the scraping algo. Left alone pending a decision.
LEAVE = {"LinkedIn Sales Navigator", "UAT", "LH2 TEST"}

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

STOP={"pvt","private","ltd","limited","llp","inc","technologies","technology","tech","solutions",
      "solution","software","systems","services","labs","india","co","corp","company"}
def nn(s):
    s=re.sub(r"\([^)]*\)"," ",s or ""); s=re.sub(r"[^a-z0-9 ]"," ",s.lower())
    return "".join(w for w in s.split() if w and w not in STOP)
def ndom(s):
    s=(s or "").lower().strip(); s=re.sub(r"^https?://","",s).split("/")[0]
    return s.replace("www.","")

# reference sets for attributing the untagged
con=sqlite3.connect(os.path.join(HUB,"lh2-pipeline","data","pipeline.sqlite"))
SCRAPE_N={nn(r[0]) for r in con.execute("SELECT company_name FROM companies") if nn(r[0])}
SCRAPE_D={ndom(r[0]) for r in con.execute("SELECT domain FROM companies") if r[0]}
A=os.path.join(ROOT,"sources","_audit")
trx=json.load(open(os.path.join(A,"tracxn.json"),encoding="utf-8"))
TRX_N={nn(r.get("company","")) for r in trx.get("LH2 Ranked Targets",[]) if nn(r.get("company",""))}
TRX_D={ndom(r.get("domain","")) for r in trx.get("LH2 Ranked Targets",[]) if r.get("domain")}
pct=json.load(open(os.path.join(A,"private_codebase_tracker.json"),encoding="utf-8"))
PCT_N=set()
for tab in ("Companies (1)","IT Services Firms","Sheet6"):
    for r in pct.get(tab,[]):
        if nn(r.get("Company","")): PCT_N.add(nn(r["Company"]))
print(f"reference sets — scrape {len(SCRAPE_N):,} | tracxn {len(TRX_N):,} | tracker {len(PCT_N):,}")

deals=[];after=None
while True:
    b={"properties":["dealname","dealstage","lead_source","scraped_type","pipeline","domain","lh2_domain"],"limit":200}
    if after: b["after"]=after
    s,d=hs("/crm/v3/objects/deals/search","POST",b)
    deals+=d.get("results",[]); after=(d.get("paging") or {}).get("next",{}).get("after")
    if not after: break
    time.sleep(0.12)
LAB={s["id"]:s["label"] for p in hs("/crm/v3/pipelines/deals")[1]["results"] for s in p["stages"]}
print(f"{len(deals)} live deals\n")

plan=[]; unresolved=[]
for x in deals:
    p=x["properties"]; old=p.get("lead_source") or ""
    if old in LEAVE: continue
    if old in MAP: new=MAP[old]
    elif old in UNIVERSE: continue                       # already correct
    elif not old:
        n=nn(p.get("dealname","")); dm=ndom(p.get("domain") or p.get("lh2_domain") or "")
        seg=p.get("scraped_type") or ""
        if   n in PCT_N:                       new=PCT
        elif n in TRX_N or (dm and dm in TRX_D): new=TRX
        elif n in SCRAPE_N or (dm and dm in SCRAPE_D):
            new = SCR_S if seg=="Distressed startups" else SCR_I
        elif seg=="Distressed startups":       new=TRX   # distressed == Tracxn provenance
        elif seg=="ITservices":                new=SCR_I
        else:
            unresolved.append(x); continue
    else:
        unresolved.append(x); continue
    plan.append({"id":x["id"],"name":p.get("dealname") or "","old":old or "(untagged)","new":new,
                 "cc":LAB.get(p.get("dealstage"))=="Cold Call"})

print("retag plan:")
for k,v in collections.Counter(f'{d["old"]}' for d in plan).most_common():
    tgt={d["new"] for d in plan if d["old"]==k}
    print(f'   {k:<48}-> {"/".join(sorted(tgt)):<42}{v:>4}')
print(f'\n   total to retag: {len(plan)}   (of which at Cold Call: {sum(1 for d in plan if d["cc"])})')
print(f'   unresolved    : {len(unresolved)}')
if unresolved:
    print("   unresolved by current tag:",
          dict(collections.Counter(x["properties"].get("lead_source") or "(untagged)" for x in unresolved)))
    print("   unresolved at Cold Call  :",
          sum(1 for x in unresolved if LAB.get(x["properties"].get("dealstage"))=="Cold Call"))
print("\nresulting universe:")
final=collections.Counter()
for x in deals:
    old=x["properties"].get("lead_source") or "(untagged)"
    hit=next((d for d in plan if d["id"]==x["id"]), None)
    final[hit["new"] if hit else old]+=1
for k,v in final.most_common(): print(f"   {k:<48}{v:>4}")

if not APPLY:
    print("\nDRY RUN — nothing written. Re-run with --apply"); sys.exit()

s,prop=hs("/crm/v3/properties/deals/lead_source"); opts=prop.get("options",[])
have={o["label"] for o in opts}
for lab in UNIVERSE:
    if lab not in have: opts.append({"label":lab,"value":lab,"displayOrder":len(opts),"hidden":False})
hs("/crm/v3/properties/deals/lead_source","PATCH",{"options":opts})
print("dropdown options ensured")
ok=fail=0
for i in range(0,len(plan),100):
    chunk=plan[i:i+100]
    s,r=hs("/crm/v3/objects/deals/batch/update","POST",
           {"inputs":[{"id":d["id"],"properties":{"lead_source":d["new"]}} for d in chunk]})
    if s in (200,202): ok+=len(chunk)
    else: fail+=len(chunk); print(f"  ! batch {s} {str(r)[:160]}")
    time.sleep(0.3)
print(f"\nretagged {ok}" + (f", {fail} FAILED" if fail else ""))
