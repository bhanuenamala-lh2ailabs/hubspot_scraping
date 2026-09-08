# -*- coding: utf-8 -*-
"""Doc 1 — the master: what the funnel is, the flowchart, every stage and its HubSpot name.

Written to be shared with the whole team, so it describes the funnel as it stands. No
"to be created" markers, no internal stage IDs, and no individual names — roles only,
because who holds a role changes.

Usage: python build_doc_master.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
import docx_kit as K
import md_to_gdoc as G

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "docs", "sop",
                   "1_LH2_Supply_Funnel_Master.docx")
MERMAID = open(os.path.join(HERE, "mermaid.min.js"), encoding="utf-8").read()

STYLE = """
    classDef stage fill:#e8eff8,stroke:#1f4e87,color:#0e2440,stroke-width:1.5px;
    classDef decision fill:#fbf3e3,stroke:#b0730c,color:#4a3005,stroke-width:1.5px;
    classDef dead fill:#fbecea,stroke:#a3392f,color:#4d150f,stroke-width:1.5px;
    classDef won fill:#e8f2ec,stroke:#2f6b4f,color:#14301f,stroke-width:2px;
    classDef start fill:#eef1f5,stroke:#6b7789,color:#2a3442,stroke-width:1.5px;
"""

FLOW_COLD = """
flowchart TD
    START(["Lead created and assigned"]) --> CC{"Cold Call"}
    CC -->|"screened out, never dialled"| DWF["Dead/ColdCall/WrongFit"]
    CC -->|"number is wrong"| DWN["Dead/ColdCall/WrongNumber"]
    CC -->|"picked up, said no"| DNI["Dead/ColdCall/Not Interested"]
    CC -->|"rang out"| NP["No Pickup<br/>callback task +1 day"]
    CC -->|"picked up, keen"| INT["Interested"]
    NP --> CB{"Callback after +1 day"}
    CB -->|"wrong number"| DWN
    CB -->|"said no"| DNI
    CB -->|"keen"| INT
    CB -->|"rang out again"| DNP["Dead/ColdCall/NoPickup<br/>WhatsApp + email first"]
    INT --> IO{"Did they book?"}
    IO -->|"keen, never booked"| DIN["Dead/Interested/NoShow"]
    IO -->|"booked"| GM["GMeet Fixed"]
""" + STYLE + """
    class START start;
    class INT,GM,NP stage;
    class CC,CB,IO decision;
    class DWF,DWN,DNI,DIN,DNP dead;
"""

FLOW_MEET = """
flowchart TD
    GM["GMeet Fixed<br/>BOOKED, not attended"] --> GMO{"Did the meeting happen?"}
    GMO -->|"we attended, they did not"| DGN["Dead/GMeet/NoShow"]
    GMO -->|"called off in advance"| DGC["Dead/GMeet/Cancelled"]
    GMO -->|"met, wrong fit"| DGW["Dead/GMeet/wrong fit"]
    GMO -->|"met, privacy concerns"| DGP["Dead/Gmeet/Privacy Concerns"]
    GMO -->|"met, proceed"| SS["Script Shared"]
    SS --> SSO{"Script follow-up"}
    SSO -->|"stopped responding"| DSN["Dead/ScriptShared/NoShow"]
    SSO -->|"output returned"| SRR["Script Results Received"]
""" + STYLE + """
    class GM,SS,SRR stage;
    class GMO,SSO decision;
    class DGW,DGP,DGN,DGC,DSN dead;
"""

FLOW_CLOSE = """
flowchart TD
    SRR["Script Results Received"] --> RO{"Results reviewed"}
    RO -->|"rejected"| DRR["Dead/ResultsReceived/WrongFit-Rejected"]
    RO -->|"accepted"| CN["Commercial Negotiation"]
    CN --> NO{"Negotiation"}
    NO -->|"pricing"| DNPR["Dead/Negotiation/Pricing"]
    NO -->|"contractual"| DNC["Dead/Negotiation/Contractual"]
    NO -->|"agreed"| DCS["Deal Contract Signed"]
    DCS --> DMD["Data Migration Done"] --> MM["Metadata Matched"] --> PI["Payment Initiation"] --> WON(["Closed/Won"])
""" + STYLE + """
    class SRR,CN,DCS,DMD,MM,PI stage;
    class RO,NO decision;
    class DRR,DNPR,DNC dead;
    class WON won;
"""

d = K.new_doc(
    "LH2 Codebase Acquisition — Supply Funnel",
    "The master reference: the funnel, every stage, and what it is called in HubSpot",
    ["This is the single source of truth for how the funnel is structured. Role-by-role "
     "instructions live in the companion SoPs.",
     "What we do: we acquire Indian IT-services firms' codebases. A lead travels cold call → "
     "technical meeting → evaluation script → negotiation → signed and paid."])

K.callout(d, "⛔  The rule above all: never make up data.",
          "No number, no name, no answer → leave it blank and note why. A blank is correct; "
          "an invented value is a bug that someone else will act on.",
          color=K.RED, bg=K.DEAD_BG)

# ---------------------------------------------------------------- 1
d.add_heading("1.  How the funnel is built", 1)
d.add_paragraph(
    "One principle governs every stage in this document: the outcome IS the stage. A stage "
    "that records only that something happened — without recording what came of it — cannot "
    "be measured, because every result piles into a single bucket. Every stage below "
    "therefore names a result, and the dashboard counts how many deals reached it.")
d.add_paragraph(
    "That has a practical consequence for everyone working the pipeline: move a deal on the "
    "same day the thing actually happens. A stage that lags reality puts the work on the "
    "wrong day, and the dashboard has no other way of knowing.")

d.add_heading("Two pipelines, one design", 2)
d.add_paragraph(
    "Both pipelines carry identical stage names in identical order, so everything in this "
    "document applies to both. Which pipeline a deal sits in depends only on where the lead "
    "came from.")
K.table(d, ["Pipeline", "Fed by"],
        [["Scraped", "Private Codebase Tracker · Tracxn sheet · GoodFirms scrape"],
         ["Campaign", "OutFlo outreach · LinkedIn campaign"]],
        widths=[1.6, 5.2])

d.add_heading("Two roles on every deal", 2)
K.bullets(d, [
    ("PoC (Point of Contact)", "the person who made the cold call. This NEVER changes for "
     "the life of the deal, so the caller stays attached to the outcome all the way to "
     "Closed/Won."),
    ("POD lead", "whoever is driving the deal right now. This is the Deal Owner, and it "
     "changes hands twice as the deal moves between roles."),
])
K.table(d, ["Phase of the funnel", "POD lead (Deal Owner)"],
        [["Cold Call → GMeet Fixed", "GTM Analyst"],
         ["GMeet Fixed → Script Results Received", "Lead Manager"],
         ["Script Results Received → Closed/Won", "Lead Closer"]],
        widths=[3.6, 3.2])

K.callout(d, "➡  Two mandatory handoffs — a rule, not a suggestion",
          ["1)  On logging GMeet Fixed: paste the GMeet link into the deal, then reassign "
           "Deal Owner → the Lead Manager.",
           "2)  On logging Script Results Received: fill in the result fields, then reassign "
           "Deal Owner → the Lead Closer.",
           "The PoC stays the same throughout. Only the POD lead (owner) moves."],
          color=K.BLUE, bg=K.HDR_BG)

# ---------------------------------------------------------------- 2
d.add_heading("2.  The funnel, half by half", 1)
d.add_paragraph("The funnel is shown in three parts, one per role, each next to the stage "
                "table that explains it. Blue boxes are live stages a deal can sit in, amber "
                "diamonds are decisions rather than stages, and red boxes are dead ends.")

# ---------------------------------------------------------------- 3
d.add_heading("3.  Every stage, what it means, what it is called", 1)

d.add_heading("Cold-call half — POD lead: GTM Analyst", 2)
K.image(d, G.render_mermaid_png(FLOW_COLD.strip(), MERMAID, width=1700), width_in=6.5)
K.table(d, ["HubSpot stage", "What it means", "How a deal leaves it"],
        [["Cold Call", "Brand-new lead, never contacted. Whoever calls it becomes the PoC.",
          "Five ways: WrongFit, WrongNumber, Not Interested, Interested, or No Pickup."],
         ["No Pickup", "It rang out. The dial happened; nobody answered. This is a LIVE "
          "stage, not a dead end — the deal is still workable.",
          "A callback task at +1 day, then the same four outcomes again."],
         ["Dead/ColdCall/WrongFit", "Screened out from the profile before any call was made. "
          "No dial happened.", "Terminal. Note why."],
         ["Dead/ColdCall/WrongNumber", "The number does not belong to the target.",
          "Terminal. Note why."],
         ["Dead/ColdCall/Not Interested", "They picked up and said no.", "Terminal. Note why."],
         ["Dead/ColdCall/NoPickup", "The callback also rang out. Unreachable, which is a "
          "different outcome from uninterested.",
          "Terminal — but only after a WhatsApp and an email have been sent. Note why."],
         ["Interested", "They want to know more.",
          "Booked → GMeet Fixed. Keen but never books → Dead/Interested/NoShow."],
         ["Dead/Interested/NoShow", "Said interested but never converted into a booked "
          "meeting. Different from a no-show at a meeting that was booked.",
          "Terminal. Note why."]],
        widths=[1.9, 2.6, 2.3], mono_cols=(0,),
        row_bg=lambda i, r: K.DEAD_BG if r[0].startswith("Dead/") else None)

d.add_heading("Meeting half — POD lead: Lead Manager", 2)
K.image(d, G.render_mermaid_png(FLOW_MEET.strip(), MERMAID, width=1700), width_in=6.5)
K.table(d, ["HubSpot stage", "What it means", "How a deal leaves it"],
        [["GMeet Fixed", "The technical meeting is BOOKED. It has not happened yet.",
          "Held → wrong fit / privacy / Script Shared. Not held → NoShow or Cancelled."],
         ["Dead/GMeet/NoShow", "We attended; they did not turn up. Our time was spent.",
          "Terminal. Counts as a VC attended."],
         ["Dead/GMeet/Cancelled", "Called off in advance, so our time was never spent.",
          "Terminal. Does NOT count as a VC attended."],
         ["Dead/GMeet/wrong fit", "The meeting happened; the codebase is not a fit.",
          "Terminal. Note why."],
         ["Dead/Gmeet/Privacy Concerns", "The meeting happened; they declined on privacy "
          "grounds.", "Terminal. Note why."],
         ["Script Shared", "Our evaluation script has been sent. They run it on their own "
          "codebase and return the output. No NDA at this point.",
          "Output returned → Script Results Received. They go quiet → Dead/ScriptShared/NoShow."],
         ["Dead/ScriptShared/NoShow", "Script went out, then they stopped responding.",
          "Terminal. Note why."],
         ["Script Results Received", "We have their output and LH2 has reviewed code quality.",
          "Result fields filled, then handoff to the Lead Closer."]],
        widths=[1.9, 2.6, 2.3], mono_cols=(0,),
        row_bg=lambda i, r: K.DEAD_BG if r[0].startswith("Dead/") else None)

d.add_heading("Closing half — POD lead: Lead Closer", 2)
K.image(d, G.render_mermaid_png(FLOW_CLOSE.strip(), MERMAID, width=1700), width_in=6.5)
K.table(d, ["HubSpot stage", "What it means", "How a deal leaves it"],
        [["Dead/ResultsReceived/WrongFit-Rejected", "Script output reviewed and rejected.",
          "Terminal. Note why."],
         ["Commercial Negotiation", "We have made an offer and are negotiating price and terms.",
          "Agreed → Deal Contract Signed. Otherwise Pricing or Contractual dead."],
         ["Dead/Negotiation/Pricing", "Could not agree a price.", "Terminal. Note why."],
         ["Dead/Negotiation/Contractual", "Could not agree terms.", "Terminal. Note why."],
         ["Deal Contract Signed", "Terms agreed and signed. This is the only contract signing "
          "in the whole flow.", "→ Data Migration Done."],
         ["Data Migration Done", "Their codebase has been transferred to us.",
          "Request the metadata match, and wait for written confirmation."],
         ["Metadata Matched", "Delivered code has been verified against agreed metadata "
          "(LoC, repos, PRs) and confirmed in writing.", "→ Payment Initiation."],
         ["Payment Initiation", "Payment is being processed to the client.",
          "→ Closed/Won once paid."],
         ["Closed/Won", "Paid. Done.", "Terminal."]],
        widths=[1.9, 2.6, 2.3], mono_cols=(0,),
        row_bg=lambda i, r: K.DEAD_BG if r[0].startswith("Dead/") else (K.LIVE_BG if r[0] == "Closed/Won" else None))

d.save(OUT)
print("wrote", OUT)
