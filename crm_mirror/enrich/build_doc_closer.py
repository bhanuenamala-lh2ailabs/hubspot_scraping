# -*- coding: utf-8 -*-
"""Doc 4 — the Lead Closer SoP: Script Results Received through Closed/Won.

Same conventions as the other role SoPs: roles not names, nothing described as enforced by
HubSpot, one diagram, blank template boxes with guidance on what each must contain.

Usage: python build_doc_closer.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
import docx_kit as K
import md_to_gdoc as G

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "docs", "sop",
                   "4_LH2_Lead_Closer_SoP.docx")
MERMAID = open(os.path.join(HERE, "mermaid.min.js"), encoding="utf-8").read()

FLOW = """
flowchart TD
    IN(["Handed to you at Script Results Received"]) --> SRR["Script Results Received"]
    SRR --> RO{"Evaluation - is it worth an offer?"}
    RO -->|"not worth it"| DRR["Dead/ResultsReceived/WrongFit-Rejected"]
    RO -->|"worth it"| CN["Commercial Negotiation<br/>offer made, terms being agreed"]
    CN --> NO{"Did terms land?"}
    NO -->|"cannot agree a price"| DNPR["Dead/Negotiation/Pricing"]
    NO -->|"cannot agree terms"| DNC["Dead/Negotiation/Contractual"]
    NO -->|"agreed"| DCS["Deal Contract Signed<br/>the only signing in the whole flow"]
    DCS --> DMD["Data Migration Done<br/>codebase transferred to us"]
    DMD --> MM["Metadata Matched<br/>verified in writing"]
    MM --> PI["Payment Initiation<br/>enter Deal Cost"]
    PI --> WON(["Closed/Won"])

    classDef stage fill:#e8eff8,stroke:#1f4e87,color:#0e2440,stroke-width:1.5px;
    classDef decision fill:#fbf3e3,stroke:#b0730c,color:#4a3005,stroke-width:1.5px;
    classDef dead fill:#fbecea,stroke:#a3392f,color:#4d150f,stroke-width:1.5px;
    classDef won fill:#e8f2ec,stroke:#2f6b4f,color:#14301f,stroke-width:2.5px;
    classDef start fill:#eef1f5,stroke:#6b7789,color:#2a3442,stroke-width:1.5px;
    class IN start;
    class SRR,CN,DCS,DMD,MM,PI stage;
    class RO,NO decision;
    class DRR,DNPR,DNC dead;
    class WON won;
"""

d = K.new_doc(
    "Lead Closer SoP — Script Results Received to Closed/Won",
    "Your half of the funnel: from a returned script output to a paid, closed deal",
    ["A deal reaches you the moment the Lead Manager logs Script Results Received and hands "
     "over ownership. You own it from there to the end.",
     "You are not the PoC. Whoever made the first call keeps that field for the life of the "
     "deal, and the Lead Manager ran the technical call — both are worth talking to before "
     "you make an offer."])

K.callout(d, "⛔  Never make up data.",
          "No number, no name, no answer → leave it blank and write a note saying why. "
          "A blank is correct. At your stage an invented number becomes an offer, a contract "
          "and a payment — it does not stay a data-quality problem for long.",
          color=K.RED, bg=K.DEAD_BG)

K.callout(d, "Nothing here is enforced by HubSpot.",
          "HubSpot will let you move a deal to Closed/Won with no cost recorded and no "
          "confirmation that anything was delivered. Every rule in this document is a "
          "working agreement between us, not a system check.",
          color=K.BLUE, bg=K.HDR_BG)

# ---------------------------------------------------------------- 1
d.add_heading("1.  Your half of the funnel", 1)
d.add_paragraph(
    "Blue boxes are stages a deal sits in, amber diamonds are decisions rather than stages, "
    "red boxes are dead ends, and green is a closed-won deal. Each part is explained in the "
    "sections that follow.")
K.image(d, G.render_mermaid_png(FLOW.strip(), MERMAID, width=1700), width_in=6.5)

# ---------------------------------------------------------------- 2
d.add_heading("2.  Start of your day", 1)
K.steps(d, [
    "HubSpot → CRM → Deals → Board view. Filter Deal owner = you, save it as \"My Deals\".",
    "Work anything newly handed to you at Script Results Received first — a deal that has "
    "just arrived is the one where their side is still warm and waiting.",
    "Then anything at Commercial Negotiation with a follow-up due.",
    "Last, sweep post-signature deals: Data Migration Done, Metadata Matched and Payment "
    "Initiation. These stall quietly because nobody is chasing them.",
])

# ---------------------------------------------------------------- 3
d.add_heading("3.  Evaluating the script output", 1)
d.add_paragraph(
    "The evaluation is done jointly with the Lead Manager — you both look at the same output "
    "and agree whether it is worth an offer. That is deliberate: it is the decision with the "
    "most money attached, and it should not rest on one reading.")
d.add_paragraph(
    "Read the raw output on the Script Results link, not only the summary numbers on the "
    "deal. Cumulative LoC tells you the scale, but Total PRs tells you whether the code was "
    "actively worked or dumped in one commit, and those are very different assets.")

K.table(d, ["Outcome", "Move the deal to", "What you do"],
        [["Not worth an offer", "Dead/ResultsReceived/WrongFit-Rejected",
          "Note specifically what disqualified it — scale, quality, licensing, or ownership. "
          "This is what stops us paying to look at the same codebase again."],
         ["Worth an offer", "Commercial Negotiation",
          "Make the offer, then record it on the deal. See Section 4."]],
        widths=[2.0, 2.2, 2.6], mono_cols=(1,),
        row_bg=lambda i, r: K.DEAD_BG if r[1].startswith("Dead/") else None)

# ---------------------------------------------------------------- 4
d.add_heading("4.  Commercial Negotiation", 1)
d.add_paragraph(
    "You have made an offer and are agreeing price and terms. This stage is where deals sit "
    "longest, so it is also where they quietly die from neglect rather than disagreement.")

d.add_heading("Step 1 — make the offer and write it down", 2)
d.add_paragraph(
    "Put three things in the deal notes: what we offered, what they asked for, and where it "
    "currently stands. Update that note every time the position moves. A negotiation you "
    "carry in your head cannot be picked up by anyone else, and it cannot be reviewed.")

K.template_box(d, "OFFER EMAIL — to be filled in",
               ["Subject:", "", "Body:", "", "", "", ""],
               note="Must include: what we are acquiring and its scope in their terms, the "
                    "figure, what happens after they accept, and a date by which you would "
                    "like an answer.")

d.add_heading("Step 2 — keep a live follow-up on it", 2)
d.add_paragraph(
    "Never leave this stage without a dated next action on the deal. Silence in a negotiation "
    "is almost never a decision — it is usually an internal conversation happening without "
    "us, and a scheduled nudge is what keeps us in it.")

d.add_heading("Step 3 — close it honestly, either way", 2)
K.table(d, ["Outcome", "Move the deal to"],
        [["Terms agreed", "Deal Contract Signed"],
         ["Could not agree a price", "Dead/Negotiation/Pricing"],
         ["Could not agree terms — liability, IP, timelines", "Dead/Negotiation/Contractual"]],
        widths=[3.6, 3.2], mono_cols=(1,))
d.add_paragraph(
    "Splitting the two dead reasons matters. A deal lost on price tells us our number was "
    "wrong; a deal lost on contract terms tells us our paperwork is wrong. Those need "
    "different fixes, and lumping them together hides both.")

# ---------------------------------------------------------------- 5
d.add_heading("5.  After signature — delivery to payment", 1)
d.add_paragraph(
    "Four stages, in order, and none of them should be skipped. This is the part of the "
    "funnel where a deal is effectively won but can still go wrong, and where a stage left "
    "stale is most expensive — we may already be committed to paying.")

d.add_heading("Deal Contract Signed", 2)
d.add_paragraph(
    "Terms are agreed and the contract is signed. This is the only contract signing anywhere "
    "in the flow. Attach the signed copy to the deal, then arrange the transfer.")

d.add_heading("Data Migration Done", 2)
d.add_paragraph(
    "Their codebase has been transferred to us. Once it lands, request the metadata match in "
    "writing and wait for a written confirmation back. Do not advance the stage on a verbal "
    "or a chat message — this is the check that what arrived matches what we agreed to buy, "
    "and it needs to be auditable later.")

K.template_box(d, "METADATA MATCH REQUEST — to be filled in",
               ["Subject:", "", "Body:", "", "", ""],
               note="Must include: the deal and company, where the delivered code sits, the "
                    "agreed metadata to check it against (LoC, repos, PRs), and an explicit "
                    "ask for written confirmation.")

d.add_heading("Metadata Matched", 2)
d.add_paragraph(
    "Delivered code has been verified against the agreed metadata and confirmed in writing. "
    "Move the stage only once that confirmation exists, and keep it on the deal.")
K.callout(d, "If the metadata does not match, stop.",
          ["Do not advance to Payment Initiation and sort it out afterwards. A short delay "
           "before payment is recoverable; a payment made against a shortfall is a "
           "commercial conversation nobody wants to have.",
           "Note the discrepancy on the deal and take it back to them."])

d.add_heading("Payment Initiation", 2)
d.add_paragraph(
    "Payment is being processed to the client. Enter the Deal Cost — the amount we are "
    "actually paying for the codebase — before you move the stage. That figure is what every "
    "report on what the pipeline cost is built from, and it is the one number nobody else "
    "can reconstruct later.")

d.add_heading("Closed/Won", 2)
d.add_paragraph("Paid and delivered. Move it once the money has actually gone out, not when "
                "it was approved.")

# ---------------------------------------------------------------- 6
d.add_heading("6.  Notes — what a good one looks like", 1)
d.add_paragraph(
    "Every Dead/* stage needs a note, and so does every position change in a negotiation. "
    "The test: could a colleague pick this deal up in three months and know exactly what "
    "happened, without asking you?")
K.table(d, ["Not acceptable", "Acceptable"],
        [["rejected", "1.2M LoC but 90% is vendored dependencies and generated code. Real "
          "hand-written surface is roughly 40k LoC across two repos. Not worth an offer at "
          "any price we would pay."],
         ["price", "Offered $X. They came back at $Y, held firm across two calls citing a "
          "competing offer. Gap was too wide to close."],
         ["contract", "Agreed on price. Could not agree indemnity — they wanted uncapped "
          "liability on our side. Their counsel would not move."],
         ["waiting", "Contract signed 2 Aug. Migration completed 6 Aug. Metadata match "
          "requested 6 Aug, confirmation still outstanding — chased 8 Aug."]],
        widths=[2.0, 4.8])

d.save(OUT)
print("wrote", OUT)
