# -*- coding: utf-8 -*-
"""Send exactly ONE pending CAD outreach email, if we're inside Indian business hours and
haven't hit today's send cap yet. Designed to be invoked every ~30 min by a launchd job so
15-20 emails land spread naturally across the business day, for as many days as it takes to
clear the pending list. No-ops harmlessly outside business hours, on weekends, once today's
cap is hit, or once everyone's been sent — safe to keep firing indefinitely.
"""
import os, sys, json, time, re, random, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HUB, "crm_mirror", "enrich"))
import gmail_sender as gs

LEADS_JSON = "/tmp/cad_callable_final.json"
STATE = os.path.join(HERE, "outreach_state.json")
PDF_PATH = os.path.join(HERE, "LH2_CAD_Data_Requirements.pdf")
CC = "ashish.ranjan@lh2.ai"
DAILY_CAP = 18
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
BUSINESS_START, BUSINESS_END = 9, 18  # 9:00 - 18:59 IST, i.e. up to but not including 19:00

LOG = os.path.join(HERE, "send_one.log")
def log(msg):
    line = f"[{datetime.datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f: f.write(line + "\n")

BODY_TEMPLATE = """Dear {first_name},

My name is Bhanu, and I lead Data Partnerships at LH2.ai out of Founder's Office.

About LH2.AI: LH2.AI is the AI research and data engineering arm of LH2 Holding. We build foundation models for engineering design generation across aerospace, mechanical, civil, architectural, and electrical/semiconductor domains. Our work spans sourcing and curating large-scale, high-quality 3D CAD and engineering datasets, and developing AI systems that can generate and iterate on functional, manufacturable designs, starting from static geometry and progressively incorporating domain-specific simulation and real human engineering workflows. We partner with data owners, content marketplaces, and engineering organizations worldwide to build the datasets that power this next generation of design AI.

We have paid more than 50 data partners between $5,000 and $10,000 for a decent volume of data.

I've attached our CAD Data Requirements document, which outlines the exact type, format, and scope of 3D CAD and engineering design data we seek to license, including our Phase 1 priorities (diverse static CAD data with descriptive metadata and edit-history/trajectory data) and Phase 2 priorities (domain-specific simulator API access and human engineering workflow data, beginning with aerospace).

We'd welcome a short call to discuss whether a licensing or data-partnership arrangement could work on your side, covering format, volume, metadata availability, and commercial structure. Please let me know the best person on your team to continue this conversation with, and a time that works for a 20–30 minute call this week.

Thank you for your time and consideration. I look forward to hearing from you.

Best regards,

Bhanu Sai Enamala,
Founder's Office, LH2.AI,
IIT Madras - Class of 2022"""


def clean_company(name):
    name = re.sub(r"\s*[|\-–].*$", "", name or "").strip()
    name = re.sub(r"\s*\(.*?\)\s*", " ", name).strip()
    return name or "your company"


def first_name(full):
    parts = (full or "").strip().split()
    return parts[0] if parts else "there"


now = datetime.datetime.now(IST)
if not (BUSINESS_START <= now.hour < BUSINESS_END):
    log(f"outside business hours ({now.hour}:00 IST) - skipping")
    sys.exit()

rows = [r for r in json.load(open(LEADS_JSON)) if r.get("contact_email")]
state = json.load(open(STATE)) if os.path.exists(STATE) else {}

today_str = now.strftime("%Y-%m-%d")
sent_today = sum(1 for v in state.values()
                  if datetime.datetime.fromtimestamp(v["sent_at"], IST).strftime("%Y-%m-%d") == today_str)
if sent_today >= DAILY_CAP:
    log(f"daily cap reached ({sent_today}/{DAILY_CAP}) - skipping")
    sys.exit()

pending = [r for r in rows if r["contact_email"] not in state]
if not pending:
    log("all leads sent - nothing pending, job can be removed")
    sys.exit()

r = pending[0]
fn = first_name(r["contact_name"])
company = clean_company(r["maps_name"])
subject = f"CAD Data Partnership - {company}"
body = BODY_TEMPLATE.format(first_name=fn)
pdf_bytes = open(PDF_PATH, "rb").read()

t, detail = gs.send(r["contact_email"], subject, body,
                    [("LH2_CAD_Data_Requirements.pdf", pdf_bytes, "application/pdf")], cc=CC)
state[r["contact_email"]] = {"company": r["maps_name"], "contact": r["contact_name"],
                              "transport": t, "detail": detail, "sent_at": time.time()}
json.dump(state, open(STATE, "w"), indent=1)
log(f"sent to {r['contact_email']} ({company}) via {t} | today: {sent_today+1}/{DAILY_CAP} | "
    f"total: {len(state)}/{len(rows)}")
