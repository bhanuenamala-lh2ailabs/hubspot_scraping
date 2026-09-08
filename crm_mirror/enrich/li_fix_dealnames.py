# -*- coding: utf-8 -*-
"""Backfill company names onto the Aug 5 LinkedIn deals.

Why they were missing: candidate/search returns TWO different shapes. For an
already-revealed (cached) profile it answers synchronously with a LIST of results; only
for a fresh reveal does it answer with {"requestId": ...} to be polled. The push code
assumed the dict shape and called .get("requestId") on the list, which raised
AttributeError straight into a bare `except Exception: return "",""`. Every cached profile
— the free ones — was silently discarded, so 11 of 13 deals fell back to the person's name.

Handle both shapes, then rename the deal to the company, per the standing rule that the
deal name is the company because that is the pointer.

Usage: python li_fix_dealnames.py [--apply]
"""
import json, os, sys, time, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); HUB=os.path.dirname(ROOT)
env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open(os.path.join(HUB,'.env'),encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
HS=env["hubspot_key"]; SH=env["signal_hire"]
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

def _extract(cand):
    exp=cand.get("experience") or []
    cur=[e for e in exp if e.get("current")]
    comp=(cur[0].get("company") if cur else (exp[0].get("company") if exp else "")) or ""
    return comp.strip(), (cand.get("headLine") or "").strip()

def sh_person(li):
    """-> (company, headline). Handles BOTH the cached-list and the async-requestId shapes."""
    body=json.dumps({"items":[li],"withoutWaterfall":True}).encode()
    req=urllib.request.Request("https://www.signalhire.com/api/v1/candidate/search",data=body,
        method="POST",headers={"apikey":SH,"Content-Type":"application/json"})
    try:
        res=json.load(urllib.request.urlopen(req,timeout=40))
    except urllib.error.HTTPError as e:
        print(f"    ! signalhire {e.code}"); return "",""
    except Exception as e:
        print(f"    ! signalhire {type(e).__name__}"); return "",""

    if isinstance(res, list):                       # cached — answered immediately, free
        if res and res[0].get("status")=="success":
            return _extract(res[0].get("candidate") or {})
        return "",""

    rid=(res or {}).get("requestId")                # fresh reveal — poll
    if not rid: return "",""
    for _ in range(15):
        time.sleep(3)
        try:
            r=urllib.request.Request(f"https://www.signalhire.com/api/v1/candidate/search/{rid}",headers={"apikey":SH})
            out=json.load(urllib.request.urlopen(r,timeout=40))
        except Exception: continue
        if isinstance(out,list) and out and out[0].get("status")!="in progress":
            if out[0].get("status")=="success":
                return _extract(out[0].get("candidate") or {})
            return "",""
    return "",""

_NOT_A_COMPANY={"self-employed","self employed","freelance","freelancer","independent",
                "independent consultant","none","n/a","-","unemployed","student","retired"}
FREEMAIL={"gmail.com","yahoo.com","yahoo.co.in","hotmail.com","outlook.com","rediffmail.com",
          "icloud.com","zoho.com","protonmail.com"}
def from_email(em):
    d=(em or "").split("@")[-1].lower()
    if not d or d in FREEMAIL: return ""
    return d.split(".")[0].replace("-"," ").title()

def clean_company(c):
    """People put taglines in the company field: 'OneshopAI : Your all-in-one Destination
    for AI Growth'. The pointer is the name before the separator."""
    c=(c or "").strip()
    for sep in (" : ", ": ", " | ", " • ", " - ", " — "):
        if sep in c:
            head=c.split(sep)[0].strip()
            if len(head) >= 3: c=head
    return c.strip(" .,-|:•")

rows=json.load(open(os.path.join(HERE,"li_aug5_pushed.json"),encoding="utf-8"))
print(f"{len(rows)} deals to check\n")
fixed=unchanged=still=0
for x in rows:
    person=f"{x['first']} {x['last']}".strip()
    comp,head=sh_person(x["li"])
    comp=clean_company(comp)
    if not comp or comp.lower() in _NOT_A_COMPANY:
        comp = comp if comp and comp.lower() not in _NOT_A_COMPANY else from_email(x["email"])
    # The lead typed a work email on the form today; LinkedIn says somewhere else. Both are
    # plausibly current (founder of one, still at the other). Flag it rather than silently
    # picking — the caller needs to know before dialling.
    ed=from_email(x["email"])
    if ed and comp and ed.lower() not in comp.lower().replace(" ",""):
        x["company_conflict"]=f"form email says {ed} ({x['email'].split('@')[-1]}), LinkedIn says {comp}"
        print(f"    ! CONFLICT {person}: {x['company_conflict']}")
    if not comp:
        print(f"  - {person:<24} still no company (deal stays '{x['deal_name']}')"); still+=1; continue
    if comp == x.get("deal_name"):
        print(f"  = {person:<24} already '{comp}'"); unchanged+=1; continue
    print(f"  ~ {person:<24} '{x['deal_name']}' -> '{comp}'"
          f"{'   [' + head[:44] + ']' if head else ''}")
    fixed+=1
    if APPLY:
        hs(f"/crm/v3/objects/deals/{x['deal_id']}","PATCH",{"properties":{"dealname":comp}})
        props={"company":comp}
        if head: props["jobtitle"]=head[:100]
        hs(f"/crm/v3/objects/contacts/{x['contact_id']}","PATCH",{"properties":props})
        x["deal_name"]=comp; x["company"]=comp; x["headline"]=head
        time.sleep(0.15)

if APPLY:
    json.dump(rows, open(os.path.join(HERE,"li_aug5_pushed.json"),"w",encoding="utf-8"),
              ensure_ascii=False, indent=1)
print(f"\nrenamed {fixed} | already correct {unchanged} | no company found {still}")
if not APPLY: print("DRY RUN — re-run with --apply")
