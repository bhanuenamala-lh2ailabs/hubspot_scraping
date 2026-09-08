# -*- coding: utf-8 -*-
"""Doc 3 — the Lead Manager SoP: GMeet Fixed through Script Results Received.

Same conventions as the GTM analyst SoP: roles not names, nothing described as enforced by
HubSpot, one diagram, blank template boxes with guidance on what each must contain.

Usage: python build_doc_meeting.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
import docx_kit as K
import md_to_gdoc as G

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "docs", "sop",
                   "3_LH2_Lead_Manager_SoP.docx")
MERMAID = open(os.path.join(HERE, "mermaid.min.js"), encoding="utf-8").read()

FLOW = """
flowchart TD
    IN(["Handed to you at GMeet Fixed"]) --> GM["GMeet Fixed<br/>BOOKED - it has not happened yet"]
    GM --> GMO{"Did the meeting happen?"}
    GMO -->|"you attended, they did not"| DGN["Dead/GMeet/NoShow"]
    GMO -->|"they called it off in advance"| DGC["Dead/GMeet/Cancelled"]
    GMO -->|"met - not a fit"| DGW["Dead/GMeet/wrong fit"]
    GMO -->|"met - privacy concerns"| DGP["Dead/Gmeet/Privacy Concerns"]
    GMO -->|"met - they will run the script"| SS["Script Shared<br/>send script, set follow-up +1 day"]
    SS --> SSO{"Did the output come back?"}
    SSO -->|"they stopped responding"| DSN["Dead/ScriptShared/NoShow"]
    SSO -->|"output returned"| SRR["Script Results Received<br/>fill results, hand to Lead Closer"]

    classDef stage fill:#e8eff8,stroke:#1f4e87,color:#0e2440,stroke-width:1.5px;
    classDef decision fill:#fbf3e3,stroke:#b0730c,color:#4a3005,stroke-width:1.5px;
    classDef dead fill:#fbecea,stroke:#a3392f,color:#4d150f,stroke-width:1.5px;
    classDef handoff fill:#e8f2ec,stroke:#2f6b4f,color:#14301f,stroke-width:2px;
    classDef start fill:#eef1f5,stroke:#6b7789,color:#2a3442,stroke-width:1.5px;
    class IN start;
    class GM,SS stage;
    class GMO,SSO decision;
    class DGN,DGC,DGW,DGP,DSN dead;
    class SRR handoff;
"""

d = K.new_doc(
    "Lead Manager SoP — GMeet Fixed to Script Results Received",
    "Your half of the funnel: from a booked technical meeting to a returned script output",
    ["A deal reaches you the moment the GTM Analyst logs GMeet Fixed and hands over "
     "ownership. It leaves you when you log Script Results Received and hand it to the "
     "Lead Closer.",
     "You are not the PoC. Whoever made the first call keeps that field for the life of the "
     "deal — if you need context on the company before the meeting, they are who to ask."])

K.callout(d, "⛔  Never make up data.",
          "No number, no name, no answer → leave it blank and write a note saying why. "
          "A blank is correct. An invented value is a bug someone else will act on — and at "
          "your stage the numbers you enter are what the offer gets built on.",
          color=K.RED, bg=K.DEAD_BG)

K.callout(d, "Nothing here is enforced by HubSpot.",
          "HubSpot will let you move a deal anywhere, with no note, no numbers and no "
          "follow-up. Every rule in this document is a working agreement between us, not a "
          "system check — which is the whole reason it is written down.",
          color=K.BLUE, bg=K.HDR_BG)

# ---------------------------------------------------------------- 1
d.add_heading("1.  Your half of the funnel", 1)
d.add_paragraph(
    "Blue boxes are stages a deal sits in, amber diamonds are decisions rather than stages, "
    "red boxes are dead ends, and green is the handoff out of your half. Each part is "
    "explained in the sections that follow.")
K.image(d, G.render_mermaid_png(FLOW.strip(), MERMAID, width=1700), width_in=6.5)

# ---------------------------------------------------------------- 2
d.add_heading("2.  Start of your day", 1)
K.steps(d, [
    "HubSpot → CRM → Deals → Board view. Filter Deal owner = you, save it as \"My Deals\".",
    "Check today's meetings first — anything at GMeet Fixed with a date today.",
    "Then work anything at Script Shared whose follow-up is due.",
    "Last, sweep GMeet Fixed deals whose meeting date has already passed. If the date is "
    "behind us and the deal has not moved, it needs an outcome logged today.",
])
K.callout(d, "A deal at GMeet Fixed with a date in the past is the one thing to never leave.",
          "GMeet Fixed means booked, not attended. If the meeting has been and gone, the "
          "stage is now telling everyone something untrue. Move it the same day — to a dead "
          "stage or to Script Shared.")

# ---------------------------------------------------------------- 3
d.add_heading("3.  Before the meeting", 1)
d.add_paragraph(
    "The GTM Analyst has pasted the GMeet link on the deal. Read their notes before you dial "
    "in — they have already spoken to this person and the note will tell you who you are "
    "meeting and what was promised. Turning up cold to a meeting someone else booked wastes "
    "the goodwill they built.")
d.add_paragraph(
    "Send a reminder the day before. A booked meeting that nobody confirms is where most "
    "no-shows come from, and a one-line message costs nothing.")

K.template_box(d, "MEETING REMINDER MESSAGE — to be filled in",
               ["", "", "", ""],
               note="Must include: the date and time in their timezone, the GMeet link again, "
                    "who will be joining from our side, and roughly what the call will cover "
                    "so they can bring the right person.")

# ---------------------------------------------------------------- 4
d.add_heading("4.  The meeting — five outcomes", 1)
d.add_paragraph(
    "Every booked meeting ends in exactly one of these. Log it the same day — the dashboard "
    "counts the day a deal reached a stage, and your attendance number is built from these "
    "moves.")
K.table(d, ["What happened", "Move the deal to", "What you do"],
        [["You joined; they never turned up", "Dead/GMeet/NoShow",
          "Note how long you waited and whether you chased. This still counts as a meeting "
          "you attended — your time was spent."],
         ["They called it off in advance", "Dead/GMeet/Cancelled",
          "Note the reason and whether they offered to rebook. If they rebook, move it back "
          "to GMeet Fixed instead of closing it."],
         ["Met — the codebase is not a fit", "Dead/GMeet/wrong fit",
          "Note specifically what disqualified it. This is the note that stops us calling "
          "them again in six months."],
         ["Met — they will not share code on privacy grounds", "Dead/Gmeet/Privacy Concerns",
          "Note whether it is a hard policy or a solvable objection (NDA, redaction, "
          "sub-set of repos). Solvable ones are worth revisiting."],
         ["Met — they agreed to run the script", "Script Shared",
          "Send the script the same day. See Section 5."]],
        widths=[2.2, 1.9, 2.7], mono_cols=(1,),
        row_bg=lambda i, r: K.DEAD_BG if r[1].startswith("Dead/") else None)

K.callout(d, "NoShow and Cancelled are different, and the difference matters.",
          ["A no-show means you sat in the meeting and waited — that time was spent, and it "
           "counts towards the meetings you attended.",
           "A cancellation received in advance means the time was never spent, and it does "
           "not count. Logging one as the other makes your own workload read wrong."])

d.add_heading("After the meeting", 2)
d.add_paragraph(
    "Whatever the outcome, write the note while the call is fresh. Then, on deals that are "
    "still alive, enter the Deal Value Range so the commercial conversation later has a "
    "starting point. You also set Priority on the deal at this point — high, medium or low — "
    "which is what tells the Lead Closer where to spend their time first.")

# ---------------------------------------------------------------- 5
d.add_heading("5.  Script Shared — getting the output back", 1)
d.add_paragraph(
    "We send an evaluation script; they run it on their own codebase and send back the "
    "output. Nothing leaves their machine except the output itself, and there is no NDA at "
    "this point — that is usually the objection you will need to answer, so say it plainly "
    "and early.")

d.add_heading("Step 1 — send it the same day", 2)
d.add_paragraph(
    "Momentum from the call is the only thing carrying this. Send the script while they still "
    "remember agreeing to it, with instructions plain enough that a developer who was not on "
    "the call can run it without asking questions.")

K.template_box(d, "SCRIPT-SHARING EMAIL — to be filled in",
               ["Subject:", "", "Body:", "", "", "", ""],
               note="Must include: what the script does and explicitly what it does NOT do "
                    "(no code leaves their machine), how to run it, roughly how long it "
                    "takes, what to send back, and who to reply to with questions.")

d.add_heading("Step 2 — set a follow-up for the next day", 2)
d.add_paragraph(
    "Give yourself a task on the deal, due the next day. One day is deliberate: the meeting "
    "is still fresh in their mind, and a script that has not been run within a day is "
    "usually one that has been put down rather than one still in progress. Chasing early "
    "catches it before that happens.")

d.add_heading("Step 3 — chase, then close it honestly", 2)
d.add_paragraph(
    "Work the follow-up when it is due. If there is no reply, chase on a second channel — if "
    "you emailed, try WhatsApp. Ask whether they hit a problem running it rather than "
    "whether they have run it; it is easier to answer and it surfaces the real blocker.")
d.add_paragraph(
    "If they have gone quiet after a fair effort, move the deal to Dead/ScriptShared/NoShow "
    "and note what you sent and when. Do not leave it sitting at Script Shared — a stalled "
    "deal parked in a live stage makes the funnel look healthier than it is.")

K.template_box(d, "SCRIPT FOLLOW-UP NUDGE — to be filled in",
               ["", "", "", ""],
               note="Must include: a reminder of what was agreed on the call, an offer to "
                    "help if they hit a problem, and one specific ask. Keep it short — this "
                    "is a nudge, not a re-pitch.")

# ---------------------------------------------------------------- 6
d.add_heading("6.  Script Results Received — the handoff", 1)
d.add_paragraph(
    "The output is back and the code quality has been reviewed. This is where the deal leaves "
    "you, and it is the most important entry in your half of the funnel — everything the "
    "Lead Closer does is built on these numbers.")
K.table(d, ["What to enter", "Why it matters downstream"],
        [["# Repos", "Scope of what we are buying"],
         ["# Projects", "Scope of what we are buying"],
         ["Cumulative LoC", "The single biggest driver of the offer"],
         ["Total PRs", "A read on whether the code was actively worked or dumped"],
         ["Script Results link", "So the Lead Closer can see the raw output, not just your "
          "summary"]],
        widths=[2.2, 4.6], mono_cols=(0,))
K.callout(d, "Fill all five, then hand over. Not before.",
          ["Reassign Deal Owner → the Lead Closer once the numbers are in.",
           "Handing over a deal with blank numbers moves the work to someone who was not on "
           "the call and cannot fill them in. If a number genuinely is not in the output, "
           "leave it blank and say so in the note — that is different from forgetting."])

# ---------------------------------------------------------------- 7
d.add_heading("7.  Notes — what a good one looks like", 1)
d.add_paragraph(
    "Every Dead/* stage needs a note, and so does every handoff. The test: could a colleague "
    "pick this deal up in three months and know exactly what happened, without asking you?")
K.table(d, ["Not acceptable", "Acceptable"],
        [["wrong fit", "Met the CTO. Codebase is three WordPress sites and a Shopify theme — "
          "no proprietary application. Nothing here to acquire."],
         ["privacy", "Will not run anything against their repos without an NDA in place. Not "
          "a flat refusal — worth revisiting if we can offer one."],
         ["no show", "Joined at 15:00, waited 20 minutes, messaged on WhatsApp, no reply. "
          "Second time this has happened with this contact."],
         ["script sent", "Script sent 4 Aug, follow-up 6 Aug, WhatsApp 8 Aug. No reply to "
          "any. Their lead dev was reportedly on leave."]],
        widths=[2.4, 4.4])

d.save(OUT)
print("wrote", OUT)
