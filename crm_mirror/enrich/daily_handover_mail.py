# -*- coding: utf-8 -*-
"""Per-caller handover mail + .vcf.

Usage:
  python daily_handover_mail.py                      build only, send nothing
  python daily_handover_mail.py --send --test        send to the test mailbox
  python daily_handover_mail.py --send               send to everyone
  python daily_handover_mail.py --send --only Ishpreet   send to one person
"""
import os, sys, json, re, html, time, datetime, collections, urllib.request, urllib.error
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); HUB=os.path.dirname(ROOT)
sys.path.insert(0, HERE)
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
from lead_vcf_notifier import vcard
import gmail_sender

env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open(os.path.join(HUB,'.env'),encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
H={"Authorization":"Bearer "+env["hubspot_key"],"Content-Type":"application/json"}
TEST_TO="bhanu.enamala@lh2.ai"
# role picks the quota block: "gtm" dials a cold book against a daily number, "lead" carries
# booked meetings through to script output against a weekly one. Ishpreet is Lead Manager but
# now also holds a cold-call book, so he gets both the weekly quota and the dialling sections.
PEOPLE={"96574824":("Lamiya","lamiya.saleem@lh2.ai","gtm"),
        "96573782":("Yuktha","yuktha.anand@lh2.ai","gtm"),
        "166322228":("Ishpreet","ishpreet.sood@lh2.ai","lead")}
# Mirrors dashboard/index.html ROLES[].targets — if a quota changes, change it in both.
QUOTA={"gtm":("Daily target","40 connected calls and at least 5 VCs set up."),
       "lead":("Weekly target","40 VCs attended, 25 scripts shared, 15 script outputs received.")}
IST=datetime.timezone(datetime.timedelta(hours=5,minutes=30))
today=datetime.datetime.now(IST).date()
SEND="--send" in sys.argv; TEST="--test" in sys.argv
ONLY=(sys.argv[sys.argv.index("--only")+1].lower()
      if "--only" in sys.argv and len(sys.argv)>sys.argv.index("--only")+1 else None)
OWNERS=[o for o,v in PEOPLE.items() if not ONLY or v[0].lower()==ONLY]
if not OWNERS: sys.exit(f"--only {ONLY}: no such person. Known: "
                        + ", ".join(v[0] for v in PEOPLE.values()))

def hs(u,m="GET",b=None):
    d=json.dumps(b).encode() if b is not None else None
    for a in range(5):
        try:
            r=urllib.request.Request("https://api.hubapi.com"+u,data=d,method=m,headers=H)
            with urllib.request.urlopen(r,timeout=45) as x:
                t=x.read().decode(); return x.status,(json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504) and a<4: time.sleep(2*(a+1)); continue
            return e.code,{"raw":e.read().decode()[:200]}
        except Exception:
            if a==4: raise
            time.sleep(2)
def india(p):
    raw=(p or "").strip(); d=re.sub(r"[^\d]","",raw)
    if raw.startswith("+91") or (d.startswith("91") and len(d)==12): d=d[-10:]
    return len(d)==10 and d[0] in "6789"

# one line on what each source IS, and how to isolate it in HubSpot
SRC = {
 "Linkedin Campaign ( IT Services )":
   ("They filled in our LinkedIn lead-gen form asking to be contacted — inbound, and the "
    "warmest thing you have.", "Lead Source is <b>Linkedin Campaign ( IT Services )</b>"),
 "Outflo Outreach ( Startups )":
   ("Startup founders who accepted our LinkedIn connection request, or replied to our "
    "message. They know the name, not the pitch.", "Lead Source is <b>Outflo Outreach ( Startups )</b>"),
 "Tracxn Sheet ( Startups )":
   ("Startups pulled from the Tracxn database — mostly shut down or winding down. Cold: "
    "they have never heard from us.", "Lead Source is <b>Tracxn Sheet ( Startups )</b>"),
 "Scraping Algo ( IT services )":
   ("Indian IT-services firms found by our own scraper. Cold, but exactly our buyer profile.",
    "Lead Source is <b>Scraping Algo ( IT services )</b>"),
 "Scraping Algo ( Startups )":
   ("Dead startups from the deadpool list. Cold — the aim is to reach the founder, not the "
    "company.", "Lead Source is <b>Scraping Algo ( Startups )</b>"),
 "Private Codebase Tracker sheet ( IT services )":
   ("From the tracker sheet we kept before HubSpot. Cold, and older — check the notes before "
    "you dial.", "Lead Source is <b>Private Codebase Tracker sheet ( IT services )</b>"),
}
PRIORITY=["Linkedin Campaign ( IT Services )","Outflo Outreach ( Startups )",
          "Scraping Algo ( IT services )","Tracxn Sheet ( Startups )","Scraping Algo ( Startups )",
          "Private Codebase Tracker sheet ( IT services )"]

s,d=hs("/crm/v3/pipelines/deals"); LAB={x["id"]:x["label"] for p in d["results"] for x in p["stages"]}
deals=[];after=None
while True:
    b={"filterGroups":[{"filters":[{"propertyName":"hubspot_owner_id","operator":"IN","values":OWNERS}]}],
       "properties":["dealname","dealstage","lead_source","hubspot_owner_id"],"limit":200}
    if after: b["after"]=after
    s,dd=hs("/crm/v3/objects/deals/search","POST",b); deals+=dd.get("results",[])
    after=(dd.get("paging") or {}).get("next",{}).get("after")
    if not after: break
    time.sleep(0.12)
OPEN=[x for x in deals if not LAB.get(x["properties"].get("dealstage"),"").startswith("Dead/")
      and LAB.get(x["properties"].get("dealstage"))!="Closed/Won"]

d2c={}; ids=[x["id"] for x in OPEN]
for i in range(0,len(ids),100):
    s,a=hs("/crm/v4/associations/deals/contacts/batch/read","POST",{"inputs":[{"id":x} for x in ids[i:i+100]]})
    for res in (a.get("results") or []):
        d2c[str(res.get("from",{}).get("id"))]=[str(t["toObjectId"]) for t in res.get("to",[])]
    time.sleep(0.08)
cids=sorted({c for v in d2c.values() for c in v}); cp={}
for i in range(0,len(cids),100):
    s,r=hs("/crm/v3/objects/contacts/batch/read","POST",
           {"properties":["firstname","lastname","email","phone","mobilephone","linkedin_url",
                          "jobtitle","company"],"inputs":[{"id":c} for c in cids[i:i+100]]})
    for x in (r.get("results") or []): cp[x["id"]]=x["properties"]
    time.sleep(0.08)

tasks=[];after=None
while True:
    b={"properties":["hs_task_status","hs_timestamp","hubspot_owner_id"],"limit":200}
    if after: b["after"]=after
    s,dd=hs("/crm/v3/objects/tasks/search","POST",b); tasks+=dd.get("results",[])
    after=(dd.get("paging") or {}).get("next",{}).get("after")
    if not after: break
    time.sleep(0.12)
def tday(p):
    try: return datetime.datetime.fromisoformat((p.get("hs_timestamp") or "").replace("Z","+00:00")).astimezone(IST).date()
    except Exception: return None

E=html.escape
TH=("padding:7px 9px;background:#1447e6;color:#fff;font-size:11px;text-align:left;"
    "font-family:Arial,sans-serif;border:1px solid #1039b5")
TD=("padding:7px 9px;border:1px solid #d8dee8;font-size:12.5px;font-family:Arial,sans-serif;"
    "vertical-align:top")
TB="border-collapse:collapse;width:100%;margin:6px 0 20px"
H2=("font-family:Arial,sans-serif;font-size:15px;margin:26px 0 6px;color:#0b1220;"
    "border-left:4px solid #1447e6;padding-left:9px")

def migrated_nopickup(deal_ids):
    """How many of these landed on No Pickup by script rather than a real dial.

    The 5 Aug retirement of `Call Attempted` moved 245 deals to No Pickup with no one
    ringing anything, so the stage cannot be trusted on its own. sourceType separates a
    human move in the CRM from an API one; the mail states the real number, never "most".
    """
    n=0
    for did in deal_ids:
        s,r=hs(f"/crm/v3/objects/deals/{did}?propertiesWithHistory=dealstage")
        ev=[e for e in (r.get("propertiesWithHistory") or {}).get("dealstage",[])
            if LAB.get(e.get("value"))=="No Pickup"]
        if ev and sorted(ev,key=lambda z:z["timestamp"])[-1].get("sourceType")!="CRM_UI": n+=1
        time.sleep(0.05)
    return n

for oid in OWNERS:
    name,addr,role=PEOPLE[oid]
    mine=[x for x in OPEN if x["properties"]["hubspot_owner_id"]==oid]
    bystage=collections.Counter(LAB.get(x["properties"].get("dealstage")) for x in mine)
    bysrc=collections.Counter(x["properties"].get("lead_source") or "(untagged)" for x in mine)
    ot=[t for t in tasks if t["properties"].get("hubspot_owner_id")==oid
        and t["properties"].get("hs_task_status")!="COMPLETED"]
    due=sum(1 for t in ot if tday(t["properties"])==today)
    over=sum(1 for t in ot if (tday(t["properties"]) or today)<today)
    nophone=[]
    for x in mine:
        cs=[cp.get(c,{}) for c in d2c.get(x["id"],[])]
        if not any(india(c.get("mobilephone")) or india(c.get("phone")) for c in cs):
            nophone.append((x["properties"].get("dealname") or "",
                            LAB.get(x["properties"].get("dealstage"))))
    cc=bystage.get("Cold Call",0); npk=bystage.get("No Pickup",0)
    npk_ids=[x["id"] for x in mine if LAB.get(x["properties"].get("dealstage"))=="No Pickup"]
    npk_mig=migrated_nopickup(npk_ids)

    P=[];A=P.append
    A('<div style="font-family:Arial,sans-serif;color:#0b1220;max-width:960px">')
    A(f'<p style="font-size:14px">Hi {name},</p>')
    A(f'<p style="font-size:13px">Your queue for <b>{today.strftime("%d %b %Y")}</b>. '
      f'The attached .vcf holds every contact — open it on your phone to save them all at once.</p>')

    # 1. what you have
    A(f'<div style="{H2}">1 · What is assigned to you</div>')
    A(f'<table style="{TB}"><tr><th style="{TH}">Stage</th><th style="{TH}">Deals</th>'
      f'<th style="{TH}">What it means</th></tr>')
    for st,mean in [("Cold Call","Never contacted — fresh dials"),
                    ("No Pickup","Rang out before. Needs another attempt"),
                    ("Interested","Said yes — convert to a meeting"),
                    ("GMeet Fixed","Meeting booked"),
                    ("Script Shared","Script sent, waiting on output")]:
        if bystage.get(st):
            A(f'<tr><td style="{TD}"><b>{st}</b></td><td style="{TD};font-weight:700">{bystage[st]}</td>'
              f'<td style="{TD};color:#5b6472">{mean}</td></tr>')
    A(f'<tr style="background:#f4f6fa"><td style="{TD}"><b>TOTAL OPEN</b></td>'
      f'<td style="{TD};font-weight:700">{len(mine)}</td><td style="{TD}"></td></tr></table>')

    A(f'<div style="{H2}">Today</div>')
    A(f'<table style="{TB}"><tr><th style="{TH}">Do this</th><th style="{TH}">Count</th></tr>'
      f'<tr><td style="{TD}">Fresh cold calls waiting</td><td style="{TD};font-weight:700">{cc}</td></tr>'
      f'<tr><td style="{TD}">Follow-ups at No Pickup</td><td style="{TD};font-weight:700">{npk}</td></tr>'
      f'<tr><td style="{TD}">Callback tasks due today</td><td style="{TD};font-weight:700">{due}</td></tr>'
      f'<tr><td style="{TD}">Tasks already overdue</td><td style="{TD};font-weight:700;color:#b3261e">{over}</td></tr>'
      f'</table>')
    qlbl,qtxt=QUOTA[role]
    A(f'<p style="font-size:12.5px;background:#fbf2e0;border-left:3px solid #b06d00;padding:10px 12px">'
      f'<b>{qlbl}:</b> {qtxt}</p>')

    # 2. sources
    A(f'<div style="{H2}">2 · Where these leads came from</div>')
    A(f'<table style="{TB}"><tr><th style="{TH}">Source</th><th style="{TH}">Yours</th>'
      f'<th style="{TH}">What it means</th><th style="{TH}">HubSpot filter</th></tr>')
    # PRIORITY first so the table reads in call order, then anything else the person holds —
    # otherwise an untagged or one-off source silently vanishes and the column stops
    # summing to TOTAL OPEN.
    for src in PRIORITY+[s for s in sorted(bysrc) if s not in PRIORITY]:
        if not bysrc.get(src): continue
        mean,filt = SRC.get(src,("Not tagged to a source yet — check the deal before you dial.",
                                 "Lead Source is <b>%s</b>" % E(src)))
        A(f'<tr><td style="{TD}"><b>{E(src)}</b></td><td style="{TD};font-weight:700">{bysrc[src]}</td>'
          f'<td style="{TD};color:#5b6472">{E(mean)}</td><td style="{TD};font-size:11.5px">{filt}</td></tr>')
    A(f'<tr style="background:#f4f6fa"><td style="{TD}"><b>TOTAL</b></td>'
      f'<td style="{TD};font-weight:700">{sum(bysrc.values())}</td><td style="{TD}"></td>'
      f'<td style="{TD}"></td></tr>')
    A('</table>')
    A(f'<p style="font-size:12px;color:#5b6472">To see just one source: <b>CRM → Deals</b>, '
      f'then <b>Filters → Deal owner = you</b> and <b>Lead Source = </b> the value above. '
      f'Save it as a view so it is one click tomorrow.</p>')

    # 3. no phone — split by stage. "Cannot dial it, so decide if it is even worth enriching"
    # only makes sense for a cold lead. A deal at Script Shared is a live conversation that
    # simply has no number on the record; telling someone to vet it for relevance is wrong.
    nop_cold=[t for t in nophone if t[1] in ("Cold Call","No Pickup")]
    nop_deep=[t for t in nophone if t[1] not in ("Cold Call","No Pickup")]
    A(f'<div style="{H2}">3 · These have no mobile number</div>')
    if nop_cold:
        A(f'<p style="font-size:12.5px"><b>{len(nop_cold)}</b> of your cold leads have no '
          f'dialable +91 number. <b>Do not try to call them.</b> Look each one up, decide '
          f'whether it is relevant to us at all, and <b>write a note on the deal in HubSpot</b> '
          f'saying relevant or not relevant, and why. Let me know once you have gone through '
          f'them — anything marked relevant gets enriched with a number and comes back to you.</p>')
        A(f'<table style="{TB}"><tr><th style="{TH}">Deal</th><th style="{TH}">Stage</th>'
          f'<th style="{TH}">Note to add in HubSpot</th></tr>')
        for nm,st in nop_cold:
            A(f'<tr><td style="{TD}"><b>{E(nm)}</b></td><td style="{TD}">{E(st or "")}</td>'
              f'<td style="{TD};color:#8a94a6">Relevant / Not relevant + one line why</td></tr>')
        A('</table>')
        A(f'<p style="font-size:12px;color:#5b6472">To find these yourself: <b>CRM → Contacts</b>, '
          f'then <b>Contact owner = you</b> and <b>Phone number is unknown</b> '
          f'(add <b>Mobile phone number is unknown</b> as a second filter).</p>')
    else:
        A('<p style="font-size:12.5px">None of your cold leads are missing a number — '
          'everything at Cold Call and No Pickup is dialable.</p>')
    if nop_deep:
        A(f'<p style="font-size:12.5px;background:#eef3fb;border-left:3px solid #1447e6;'
          f'padding:10px 12px">Separately, <b>{len(nop_deep)}</b> deals you are already working '
          f'have no phone number saved on the contact. Nothing to vet — these are live '
          f'conversations. Just <b>add the number to the contact record</b> next time you speak '
          f'to them, so anyone picking the deal up can reach them.</p>')
        A(f'<table style="{TB}"><tr><th style="{TH}">Deal</th><th style="{TH}">Stage</th></tr>')
        for nm,st in nop_deep:
            A(f'<tr><td style="{TD}"><b>{E(nm)}</b></td><td style="{TD}">{E(st or "")}</td></tr>')
        A('</table>')

    # 4. order of work
    A(f'<div style="{H2}">4 · Call in this order</div>')
    A(f'<table style="{TB}"><tr><th style="{TH}">#</th><th style="{TH}">Source</th>'
      f'<th style="{TH}">Why this order</th></tr>')
    for i,(src,why) in enumerate([
        ("Linkedin Campaign ( IT Services )","They asked us to contact them. Warmest, and they go cold fastest."),
        ("Outflo Outreach ( Startups )","Already engaged with us on LinkedIn — the name is familiar."),
        ("Everything else","Fully cold: Scraping Algo and Tracxn. Work these once the two above are done."),
    ],1):
        A(f'<tr><td style="{TD};text-align:center"><b>{i}</b></td><td style="{TD}"><b>{E(src)}</b></td>'
          f'<td style="{TD};color:#5b6472">{E(why)}</td></tr>')
    A('</table>')

    # 5. the No Pickup caveat
    if npk:
        A(f'<div style="{H2}">5 · Important — check the No Pickup ones before trusting them</div>')
        howmany = ("All <b>%d</b> of your No Pickup deals were" % npk if npk_mig==npk else
                   "<b>%d</b> of your <b>%d</b> No Pickup deals were" % (npk_mig,npk))
        A(f'<p style="font-size:12.5px;background:#fbeceb;border-left:3px solid #a3392f;padding:10px 12px">'
          f'{howmany} moved there by a system migration on 5 August, not because anyone '
          f'actually rang them. Some were also transferred from another caller. '
          f'<b>Treat them as fresh</b> — check the notes, and if there is no record of a real '
          f'call, dial as if it were the first attempt.</p>')

    # 6. house rules
    A(f'<div style="{H2}">6 · Two habits that matter</div>')
    A(f'<ul style="font-size:12.5px;color:#3f4854;line-height:1.65">'
      f'<li><b>Move the stage the same day.</b> The dashboard counts the day a deal reached a '
      f'stage. Move it late and your work lands on the wrong day, or not at all.</li>'
      f'<li><b>Every ring-out gets a callback task, due the next day</b> — not two days. '
      f'A No Pickup with no task is a lead nobody comes back to.</li></ul>')
    A('<p style="font-size:12px;color:#8a94a6">Automated from HubSpot.</p></div>')
    HTML="\n".join(P)

    cards=[]
    for x in mine:
        for c in d2c.get(x["id"],[]):
            p=cp.get(c)
            if p: cards.append(vcard(p, x["properties"].get("dealname") or "",
                                     x["properties"].get("dealname") or "", name,
                                     LAB.get(x["properties"].get("dealstage")) or ""))
    vcf=("\r\n".join(cards)).encode("utf-8")
    fn=f"lh2_leads_{name.lower()}_{today.isoformat()}.vcf"
    open(os.path.join(HERE,fn),"wb").write(vcf)
    # preview alongside the .vcf, so the mail can be read in a browser before anyone gets it
    prev=os.path.join(HERE,f"preview_{name.lower()}_{today.isoformat()}.html")
    open(prev,"w",encoding="utf-8").write(HTML)
    txt=(f"Hi {name},\n\nYour queue for {today}: {len(mine)} open "
         f"({cc} cold calls, {npk} follow-ups, {due} tasks due today, {over} overdue).\n"
         f"Call order: LinkedIn first, then OutFlo, then the rest.\n"
         f"{len(nophone)} deals have no number — vet them and note on HubSpot.\n"
         f"NOTE: {npk_mig} of {npk} No Pickup deals were migrated by script, not actually "
         f"dialled — treat as fresh.\n")
    print(f"{name:<9}{role:<6}{len(mine):>4} open | {cc} cold | {npk} nopickup "
          f"({npk_mig} migrated) | {due} due | {over} overdue | {len(nophone)} no-phone | "
          f"{len(cards)} vcards ({len(vcf)}b)")
    if SEND:
        to = TEST_TO if TEST else addr
        subj = ("[TEST] " if TEST else "") + f"Your LH2 call list — {today.strftime('%d %b %Y')}"
        if TEST: subj += f" ({name})"
        t,detail = gmail_sender.send(to, subj, txt, [(fn, vcf, "text/vcard")], html=HTML)
        print(f"         sent to {to} via [{t}] {detail}")
if not SEND: print("\nnot sent — pass --send (add --test to route both to the test mailbox)")
