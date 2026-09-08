# -*- coding: utf-8 -*-
"""Mail Ishpreet one .vcf covering today's LinkedIn leads — the 10 moved off Shobit and
the 13 newly created.

Reuses vcard() from lead_vcf_notifier so the saved contact name carries the company suffix
and every number is forced to +91, exactly like the nightly notifier. Recipient address
comes from the HubSpot owners API, not a hardcoded string.

Usage: python li_vcf_ishpreet.py [--send]
"""
import json, os, re, sys, time, datetime, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); HUB=os.path.dirname(ROOT)
sys.path.insert(0, HERE)
import gmail_sender
from lead_vcf_notifier import vcard

env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open(os.path.join(HUB,'.env'),encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
HS=env["hubspot_key"]; ISHPREET="166322228"
SEND="--send" in sys.argv

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

# the deals in scope: reassigned-off-Shobit + newly-created
SOURCES={"LinkedIn Lead-Gen Form - Jul 31 2026",
         "LinkedIn Lead-Gen Form - ITservices_targeted_message"}
moved=[d["id"] for d in json.load(open(os.path.join(HERE,"shobit_all_deals.json"),encoding="utf-8"))
       if (d["properties"].get("lead_source") or "") in SOURCES]
fresh=[x["deal_id"] for x in json.load(open(os.path.join(HERE,"li_aug5_pushed.json"),encoding="utf-8"))]
dids=list(dict.fromkeys(moved+fresh))
print(f"{len(moved)} moved + {len(fresh)} new = {len(dids)} deals\n")

CPROPS="firstname,lastname,email,mobilephone,phone,linkedin_url,jobtitle,company"
cards=[]; lines=[]; nophone=0
for did in dids:
    s,d=hs(f"/crm/v3/objects/deals/{did}?properties=dealname,dealstage,hubspot_owner_id")
    dn=d.get("properties",{}).get("dealname") or ""
    if d.get("properties",{}).get("hubspot_owner_id")!=ISHPREET:
        print(f"  ! {dn} is not owned by Ishpreet — skipping"); continue
    s,a=hs(f"/crm/v4/objects/deals/{did}/associations/contacts")
    for x in (a.get("results") or []):
        s,c=hs(f"/crm/v3/objects/contacts/{x['toObjectId']}?properties={CPROPS}")
        p=c.get("properties") or {}
        cards.append(vcard(p, dn, dn, "Ishpreet Sood"))
        ph=(p.get("mobilephone") or p.get("phone") or "").strip()
        if not ph: nophone+=1
        nm=f"{p.get('firstname','')} {p.get('lastname','')}".strip()
        lines.append(f"  - {nm or '(no name)':26} {dn[:28]:30} {ph or 'no phone'}")

print(f"{len(cards)} contacts\n" + "\n".join(lines))
if nophone: print(f"\n{nophone} with no phone")

s,ow=hs("/crm/v3/owners?limit=200")
to=next((o.get("email") for o in ow.get("results",[]) if o["id"]==ISHPREET), None)
if not to: sys.exit("no email for Ishpreet in HubSpot owners")

body=("Hi Ishpreet,\n\n"
      "These are newly assigned lead contacts. Open the attached .vcf on your phone "
      "to add them all at once.\n\n"
      + "\n".join(lines) + "\n\n"
      "Please log the outcome against the deal in HubSpot after you call.\n")
fname=f"lh2_leads_ishpreet_sood_{datetime.date.today().isoformat()}.vcf"
subject=f"{len(cards)} new LH2 leads assigned to you"
vcf=("\r\n".join(cards)).encode("utf-8")
open(os.path.join(HERE,fname),"wb").write(vcf)
print(f"\nwrote {fname} ({len(vcf)} bytes) -> {to}")

if SEND:
    t,detail=gmail_sender.send(to, subject, body, [(fname, vcf, "text/vcard")])
    print(f"sent via [{t}] {detail}")
else:
    print("DRY RUN — re-run with --send")
