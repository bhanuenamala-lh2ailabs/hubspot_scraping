# -*- coding: utf-8 -*-
"""Paced, personalized CAD data-partnership outreach to the 41 leads (of 61 total callable)
that have an email on file. Sends individually — never a bulk To/Cc blast — spread across
multiple days with delays between sends, to avoid looking like a spam pattern from a personal
Gmail/Workspace account.

Resumable: sent state tracked in outreach_state.json so re-running never double-sends.

Usage:
  python3 send_outreach.py --preview          show N sample emails, send nothing
  python3 send_outreach.py --send --limit 18  send up to 18 not-yet-sent emails today
"""
import os, sys, csv, json, time, re, random

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HUB, "crm_mirror", "enrich"))
import gmail_sender as gs

LEADS_JSON = "/tmp/cad_callable_final.json"
STATE = os.path.join(HERE, "outreach_state.json")
PDF_PATH = os.path.join(HERE, "LH2_CAD_Data_Requirements.pdf")
CC = "ashish.ranjan@lh2.ai"

ARG = sys.argv
def opt(n, d):
    return ARG[ARG.index(n) + 1] if n in ARG and ARG.index(n) + 1 < len(ARG) else d
LIMIT = int(opt("--limit", "18"))
PREVIEW = "--preview" in ARG
SEND = "--send" in ARG

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


rows = [r for r in json.load(open(LEADS_JSON)) if r.get("contact_email")]
print(f"leads with email: {len(rows)}")

state = json.load(open(STATE)) if os.path.exists(STATE) else {}
pending = [r for r in rows if r["contact_email"] not in state]
print(f"already sent: {len(state)} | pending: {len(pending)}")

pdf_bytes = open(PDF_PATH, "rb").read()

if PREVIEW:
    for r in pending[:2]:
        fn = first_name(r["contact_name"])
        company = clean_company(r["maps_name"])
        subject = f"CAD Data Partnership - {company}"
        body = BODY_TEMPLATE.format(first_name=fn)
        print("=" * 70)
        print(f"TO: {r['contact_email']}  (CC: {CC})")
        print(f"SUBJECT: {subject}")
        print(f"ATTACHMENT: LH2_CAD_Data_Requirements.pdf")
        print("-" * 70)
        print(body)
    print("\n" + "=" * 70)
    print("PREVIEW ONLY — nothing sent. Re-run with --send --limit N to send.")
    sys.exit()

if not SEND:
    print("pass --preview or --send")
    sys.exit()

batch = pending[:LIMIT]
print(f"sending {len(batch)} emails this run (paced)")
sent = 0
for i, r in enumerate(batch, 1):
    fn = first_name(r["contact_name"])
    company = clean_company(r["maps_name"])
    subject = f"CAD Data Partnership - {company}"
    body = BODY_TEMPLATE.format(first_name=fn)
    t, detail = gs.send(r["contact_email"], subject, body,
                        [("LH2_CAD_Data_Requirements.pdf", pdf_bytes, "application/pdf")],
                        cc=CC)
    state[r["contact_email"]] = {"company": r["maps_name"], "contact": r["contact_name"],
                                  "transport": t, "detail": detail, "sent_at": time.time()}
    json.dump(state, open(STATE, "w"), indent=1)
    sent += 1
    print(f"  [{i}/{len(batch)}] {r['contact_email']:<35} ({company[:30]}) -> {t}", flush=True)
    if i < len(batch):
        delay = random.uniform(60, 120)
        time.sleep(delay)

print(f"\nsent {sent} this run. total sent so far: {len(state)}/{len(rows)}")
