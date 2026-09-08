# -*- coding: utf-8 -*-
"""Doc 2 — the GTM analyst SoP: Cold Call through GMeet Fixed.

Deliberately says nothing about "required fields". HubSpot does not enforce any of this —
that is exactly why the SoP exists. Every instruction here is a working agreement, and the
only thing making it happen is the person doing it.

Usage: python build_doc_gtm.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
import docx_kit as K
import md_to_gdoc as G

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "docs", "sop",
                   "2_LH2_GTM_Analyst_SoP.docx")
MERMAID = open(os.path.join(HERE, "mermaid.min.js"), encoding="utf-8").read()

FLOW = """
flowchart TD
    START(["Lead assigned to you"]) --> CC{"Cold Call - you dial"}
    CC -->|"not our profile, never dialled"| DWF["Dead/ColdCall/WrongFit"]
    CC -->|"number is wrong"| DWN["Dead/ColdCall/WrongNumber"]
    CC -->|"picked up, said no"| DNI["Dead/ColdCall/Not Interested"]
    CC -->|"rang out"| NP["No Pickup<br/>give yourself a callback task +1 day"]
    CC -->|"picked up, keen"| INT["Interested"]
    NP --> CB{"Callback next day"}
    CB -->|"wrong number"| DWN
    CB -->|"said no"| DNI
    CB -->|"keen"| INT
    CB -->|"rang out again"| WA["Send WhatsApp + email<br/>before you close it"]
    WA --> DNP["Dead/ColdCall/NoPickup"]
    INT --> IO{"Phone, WhatsApp or email - your call.<br/>Settle it within +1 day"}
    IO -->|"keen, but never books"| DIN["Dead/Interested/NoShow"]
    IO -->|"books the meeting"| GM["GMeet Fixed<br/>paste link, hand over to the Lead Manager"]

    classDef stage fill:#e8eff8,stroke:#1f4e87,color:#0e2440,stroke-width:1.5px;
    classDef decision fill:#fbf3e3,stroke:#b0730c,color:#4a3005,stroke-width:1.5px;
    classDef dead fill:#fbecea,stroke:#a3392f,color:#4d150f,stroke-width:1.5px;
    classDef action fill:#fdf0dd,stroke:#8a4b00,color:#4a2900,stroke-width:2px;
    classDef handoff fill:#e8f2ec,stroke:#2f6b4f,color:#14301f,stroke-width:2px;
    classDef start fill:#eef1f5,stroke:#6b7789,color:#2a3442,stroke-width:1.5px;
    class START start;
    class INT,NP stage;
    class CC,CB,IO decision;
    class DWF,DWN,DNI,DNP,DIN dead;
    class WA action;
    class GM handoff;
"""

d = K.new_doc(
    "GTM Analyst SoP — Cold Call to GMeet Fixed",
    "Your half of the funnel: from an untouched lead to a booked technical meeting",
    ["This covers everything you own. The moment you log GMeet Fixed, the deal leaves you "
     "and becomes the Lead Manager's.",
     "You are the PoC on every deal you call. That never changes, even after the deal moves "
     "on — your name stays attached to the outcome all the way to Closed/Won."])

K.callout(d, "⛔  Never make up data.",
          "No number, no name, no answer → leave it blank and write a note saying why. "
          "A blank is correct. An invented value is a bug someone else will act on.",
          color=K.RED, bg=K.DEAD_BG)

K.callout(d, "Nothing here is enforced by HubSpot.",
          "HubSpot will happily let you drag a deal anywhere, with no note and no task. "
          "Every rule in this document is a working agreement between us, not a system "
          "check — which is the whole reason it is written down. If you skip a step, "
          "nothing will stop you and nobody will be told.",
          color=K.BLUE, bg=K.HDR_BG)

# ---------------------------------------------------------------- 1
d.add_heading("1.  Your half of the funnel", 1)
d.add_paragraph(
    "Everything from an untouched lead to a booked meeting. Blue boxes are stages a deal "
    "sits in, amber boxes are actions you take rather than stages, and red boxes are dead "
    "ends. Each part is explained in the sections that follow.")
K.image(d, G.render_mermaid_png(FLOW.strip(), MERMAID, width=1700), width_in=6.5)

# ---------------------------------------------------------------- 2
d.add_heading("2.  Start of your day", 1)
K.steps(d, [
    "HubSpot → CRM → Deals → your pipeline, Board view.",
    "Filter Deal owner = you. Save it as \"My Deals\" so it is one click tomorrow.",
    "Work Cold Call first, then anything with a callback task due today.",
    "Do not set Priority. That is set after the GMeet, by the Lead Manager.",
])

# ---------------------------------------------------------------- 3
d.add_heading("3.  The cold call — five outcomes", 1)
d.add_paragraph(
    "Every dial ends in exactly one of these five. Move the deal the same day you make the "
    "call — the dashboard counts the day a deal reached a stage, so a stage moved late "
    "records your work on the wrong day, or not at all.")
K.table(d, ["What happened", "Move the deal to", "What you do"],
        [["Not our profile — you decided before dialling",
          "Dead/ColdCall/WrongFit",
          "Note why. No call was made, so this is not counted as a call attempt."],
         ["The number is not theirs", "Dead/ColdCall/WrongNumber",
          "Look for a better number first — LinkedIn, their website, Apollo. Only close it "
          "once you have tried. Note what you tried."],
         ["Picked up, not interested", "Dead/ColdCall/Not Interested",
          "Note the reason in their words. \"Not interested\" on its own is not a note."],
         ["Picked up, wants to know more", "Interested",
          "Go to Section 5. You now have one day to settle the next step."],
         ["Rang out, nobody answered", "No Pickup",
          "Give yourself a callback task, due +1 day. See Section 4."]],
        widths=[2.2, 1.9, 2.7], mono_cols=(1,),
        row_bg=lambda i, r: K.DEAD_BG if r[1].startswith("Dead/") else None)

# ---------------------------------------------------------------- 4
d.add_heading("4.  No Pickup — the callback loop", 1)
d.add_paragraph(
    "No Pickup is a live stage, not a dead end. A deal sitting there is still yours and still "
    "workable — nobody has said no, we simply have not reached them yet. This is the biggest "
    "leak in the funnel, which is why it has three explicit steps rather than one.")

d.add_heading("Step 1 — the moment it rings out", 2)
d.add_paragraph(
    "Move the deal to No Pickup, then immediately give yourself a callback task due the next "
    "day. On the deal: Create task → Type: Call → Assigned to: yourself → Due: tomorrow. Put "
    "the company name in the title so your task list is readable at a glance.")
d.add_paragraph(
    "Do this before you dial the next number. A deal moved to No Pickup without a task is a "
    "lead nobody will ever come back to — it looks worked, and it is silently abandoned. "
    "Most callback tasks currently open are already past their due date, and that is the "
    "habit this step exists to break.")

d.add_heading("Step 2 — the callback, the next day", 2)
d.add_paragraph(
    "Work the task on the day it is due. Call at a different time of day from your first "
    "attempt — if you tried mid-morning, try late afternoon, since a founder who cannot pick "
    "up at 11am often can at 5pm. The callback has the same four outcomes as the first dial:")
K.table(d, ["Callback outcome", "Move the deal to"],
        [["The number is not theirs", "Dead/ColdCall/WrongNumber"],
         ["Picked up, not interested", "Dead/ColdCall/Not Interested"],
         ["Picked up, wants to know more", "Interested"],
         ["Rang out again", "Dead/ColdCall/NoPickup — but only after Step 3"]],
        widths=[3.4, 3.4], mono_cols=(1,))

d.add_heading("Step 3 — before you close it as NoPickup", 2)
d.add_paragraph(
    "Two rings-out is not a no. It means we failed to make contact, and that is a different "
    "thing entirely. Before this deal is closed, send both a WhatsApp and an email — they "
    "cost nothing, they arrive when the person is free rather than when you happened to "
    "call, and a share of them come back as replies.")
d.add_paragraph(
    "Send both, log both on the deal, then move it to Dead/ColdCall/NoPickup with a note "
    "saying what you sent and when. If they reply later, move the deal back to Interested — "
    "a dead stage is not permanent.")

K.template_box(d, "WHATSAPP TEMPLATE — to be filled in",
               ["", "", "", "", ""],
               note="Must include: who you are, LH2, why you are calling them specifically, "
                    "and one clear ask — a time to talk. Keep the first line short enough to "
                    "read in the notification preview, because that decides whether it is "
                    "opened at all.")

K.template_box(d, "EMAIL TEMPLATE — to be filled in",
               ["Subject:", "", "Body:", "", "", "", ""],
               note="Must include: a subject line that says something specific, who you are, "
                    "what LH2 does, why them, and one call to action.")

# ---------------------------------------------------------------- 5
d.add_heading("5.  Interested → GMeet Fixed", 1)
d.add_paragraph(
    "They are keen. Your job now is to turn that into a booked meeting, and how you do it is "
    "deliberately left to you — phone, WhatsApp, email, or any mix of the three. Use whatever "
    "you judge will land with that particular person; you have spoken to them and nobody "
    "else has.")

K.callout(d, "The one hard rule: settle the next stage within +1 day.",
          ["Within a day of them saying they are interested, the deal must move — either to "
           "GMeet Fixed or to Dead/Interested/NoShow.",
           "It must not sit at Interested. Warm interest goes cold quickly, and a deal parked "
           "here is the most expensive kind of leak there is: someone said yes, and we let "
           "it lapse."],
          color=K.BLUE, bg=K.HDR_BG)

d.add_heading("If they book — GMeet Fixed", 2)
K.steps(d, [
    "Send the meeting invite with the GMeet link.",
    "Paste that GMeet link into the deal — the Lead Manager has no other way to find it.",
    "Move the deal to GMeet Fixed.",
    "Reassign Deal Owner → the Lead Manager. This is the handoff.",
])
d.add_paragraph(
    "You stay the PoC; only the owner changes. Note that GMeet Fixed means the meeting is "
    "booked, not that it happened — whether they actually turn up is the Lead Manager's to "
    "record, not yours.")

d.add_heading("If they never book — Dead/Interested/NoShow", 2)
d.add_paragraph(
    "Someone can say yes and still never convert. That is exactly what this stage is for: "
    "they were keen, you followed up, and no meeting ever came of it. It is a different "
    "outcome from someone who booked and then failed to show, and it belongs to you rather "
    "than to the Lead Manager.")
d.add_paragraph(
    "Before you close it, note what you tried and over how long — \"called twice and "
    "WhatsApped over four days, no reply after the first yes\" tells the next person "
    "something. \"No show\" on its own does not.")

# ---------------------------------------------------------------- 6
d.add_heading("6.  Notes — what a good one looks like", 1)
d.add_paragraph(
    "Every Dead/* stage needs a note. The test is simple: could a colleague pick this deal up "
    "in three months and know exactly what happened, without calling you to ask?")
K.table(d, ["Not acceptable", "Acceptable"],
        [["not interested", "Spoke to the founder. They sold their services arm in March and "
          "have no codebase left to sell. Hard no."],
         ["no answer", "Rang out 4 Aug 11:20 and 5 Aug 16:40. WhatsApp and email sent 5 Aug, "
          "no reply. Number verified against their website."],
         ["wrong number", "Number on the sheet reaches a logistics firm. Checked LinkedIn and "
          "their site — no alternative number listed anywhere."]],
        widths=[2.4, 4.4])

d.save(OUT)
print("wrote", OUT)
