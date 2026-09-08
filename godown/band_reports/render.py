# -*- coding: utf-8 -*-
"""Renders the four band-followup emails as HTML, using data already read from
band_followup_data.json plus hand-written Issue/Action text (today's send — the note-reading
judgment step that a bare script can't replicate; see the mail sent to Bhanu for the caveat).
"""
import os, sys, json, datetime

HUB = "/Users/bhanu/Desktop/hubspot"
sys.path.insert(0, os.path.join(HUB, "crm_mirror", "enrich"))
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
TODAY = datetime.datetime.now(IST).strftime("%d %b")

TD = "padding:6px 10px;border-bottom:1px solid #e6e9ef;font:13px system-ui;vertical-align:top"
TH = "padding:7px 10px;text-align:left;font:600 11px system-ui;color:#6b7280;text-transform:uppercase;border-bottom:2px solid #d1d5db"

def table(headers, rows):
    h = "".join(f'<th style="{TH}">{c}</th>' for c in headers)
    body = ""
    for r in rows:
        body += "<tr>" + "".join(f'<td style="{TD}">{c}</td>' for c in r) + "</tr>"
    return f'<table style="border-collapse:collapse;width:100%;margin:8px 0 18px"><tr>{h}</tr>{body}</table>'

def section(title, sub, tbl_html):
    return (f'<div style="font:700 14px system-ui;color:#111827;margin:22px 0 4px">{title}</div>'
            f'<div style="color:#9ca3af;font:12px system-ui;margin-bottom:4px">{sub}</div>{tbl_html}')

def wrap(name, intro_html, body_html, closing_html):
    return f'''<div style="max-width:900px;margin:0 auto;padding:24px;font-family:system-ui;color:#111827">
      <div style="font:15px system-ui">Hi {name},</div>
      <div style="margin-top:10px;font:14px/1.5 system-ui">{intro_html}</div>
      {body_html}
      <div style="margin-top:18px;font:14px/1.6 system-ui">{closing_html}</div>
      <div style="color:#9ca3af;font:12px system-ui;margin-top:20px;border-top:1px solid #e6e9ef;padding-top:10px">
        Source: HubSpot, {TODAY}.
      </div>
    </div>'''

# ================================================================== ISHPREET
def ishpreet_html():
    sec1 = table(["Deal","Days","Metadata / Results Link","Issue","Action"], [
        ["Lakhan Jain","9d","EMPTY",
         "At Script Results Received for 9 days. Last note (1d ago) says he's out sick and will connect in the second half of the week — no results link recorded regardless.",
         "Once output is actually in hand, add the Drive link to Metadata / Results Link, note LoC/PR counts, then hand to Shobit."],
        ["Lise","1d","EMPTY",
         "At Script Results Received for 1 day with zero notes of any kind — nothing records what happened here at all.",
         "Check in and record the outcome; add the results link once output exists."],
    ])
    sec2 = table(["Deal","Days","Owner","Issue","Action"], [
        ["WebGuruz Technologies Pvt Ltd","7d","Lamiya","Meeting link is on the deal, but latest note says no-show, follow-up sent asking to reschedule — no response yet.","Chase the reschedule; if silent, try WhatsApp."],
        ["iFour Technolab Pvt. Ltd.","1d","Lamiya","Meeting link present, fixed yesterday.","Attend / confirm the meeting happened, record outcome."],
        ["Infynno Solutions","0d","Lamiya","Link present. Note says no-show, rescheduled to next day.","Confirm the reschedule happens; attend."],
        ["CodiFly IT Solutions","0d","Lamiya","Link present, fixed for Friday.","Attend and record outcome."],
    ])
    sec3 = table(["Deal","Days","Owner","Issue","Action"], [
        ["Mayank Chawla","21d","Ishpreet","Note (9d old) says the lead was engaged by Yash and you were to call again — no call recorded since.","Call and record the outcome."],
        ["Vaibhav Tayal","21d","Ishpreet","Same handover note as Mayank Chawla, no follow-up recorded.","Call and record the outcome."],
        ["OpeninApp","16d","Ishpreet","Tried calling (1d ago), no response — will try a new number.","Follow through on the new number; record the outcome."],
        ["AltWorld","16d","Ishpreet","He's caught up with his current company, asked to bump the mail, said he'll give output next week.","Chase; the promised week is now — call today."],
        ["Zensar","14d","Ishpreet","Note (1d ago): chase this week or drop him — hard to get.","Redial this week; if silent again, drop."],
        ["Zepto","14d","Ishpreet","Note (1d ago): output next week, he's AFK this week.","Wait out this week, then chase — do not let it go stale again."],
        ["Brandsmashers Tech","14d","Ishpreet","Note (1d ago): hard to catch, not very interested, group never responds.","One more attempt; if silent, treat as low-priority / consider dropping."],
        ["Encureit","13d","Lamiya","Note (7d ago): said he'd get back next week — that week has passed.","Agreed week has passed — call today."],
        ["Vikas Chauhan","13d","Yuktha","Note (7d ago): travelling, promised output “tomorrow” — that was a week ago.","Agreed day has long passed — call today."],
    ])
    sec4 = table(["Deal","Days","Owner","Issue","Action"], [
        ["Nishant Vispute","12d","Yuktha","No response to call (8d ago), followed up over mail — nothing since.","Redial; if silent again, try WhatsApp."],
        ["Mayur Patki","7d","Yuktha","Latest note (13d old) is about a GMeet, not a script send — nothing records a script actually going out.","Confirm the script was sent at all; call and record."],
        ["Techify Solutions Pvt Ltd","7d","Yuktha","Script + NDA sent 7d ago, no reply since.","Already sent — call instead of resending."],
        ["Vah Vah","6d","Yuktha","Has codebases with maintained PRs; checking whether the data is still on Git.","Chase; check-in is overdue."],
        ["Credence Digital Health","6d","Lamiya","Script shared 6d ago, no contact since.","Call and record the outcome."],
    ])
    sec5 = table(["Deal","Days","Owner","Issue","Action"], [
        ["C4Scale","2d","Yuktha","Call was fixed for 4:30 PM two days ago — nothing confirms the script itself was sent.","Call and record the outcome."],
        ["Uday Tanwar","2d","Yuktha","Script shared over mail 2 days ago.","Give it a day more, then call if silent."],
        ["Queppelin","2d","Yuktha","He'll check if he wants to proceed at all.","Follow up for a decision."],
        ["Big Oh Tech","1d","Yuktha","Script shared over mail yesterday.","Give it a day, then call if silent."],
        ["Rebin Infotech","1d","Yuktha","Script shared yesterday.","Give it a day, then call if silent."],
        ["Alphonic Network Solutions Pvt. Ltd.","1d","Lamiya","Script shared yesterday.","Give it a day, then call if silent."],
        ["Ayasya Digital Solutions LLP","0d","Yuktha","GMeet fixed for tomorrow 2:30 PM.","Attend, then move stage per outcome."],
        ["Thirdessential IT Solutions Pvt. Ltd.","0d","Lamiya","GMeet fixed today.","Attend, then move stage per outcome."],
        ["TechZarInfo Software & Consulting Services","0d","Yuktha","Follow-up agreed for Monday 24 Aug for script output.","Wait for the agreed date; nothing to chase yet."],
        ["keylines","0d","Yuktha","Script shared today, he'll review and get back.","Give it a couple of days, then call if silent."],
        ["Floatinity Systems LLP","0d","Yuktha","Script shared today; mentioned a shut-down company, likely has PRs.","Give it a couple of days, then call if silent."],
        ["Ruth Haephrati - Upwork","0d","Shobit","Currently vacationing, connected via WhatsApp, will loop in her team to run the script.","Wait for her team intro; nothing to chase yet."],
    ])
    returned = table(["Deal","Days","Owner","Note"], [
        ["Aexonic Technologies","0d","Yuktha","[Founder Search] GMeet fixed for 9:30 AM tomorrow — no meeting link on the deal yet, so this stays with Yuktha until the link is added."],
    ])

    intro = ("Your band: from the moment a GMeet is genuinely fixed, through attending it, sharing the "
             "script and chasing the output, to results received. <b>32 deals.</b>")
    rule = ('<div style="font:700 14px system-ui;margin-top:16px">One hard rule, unchanged from last time</div>'
            '<div style="font:14px/1.5 system-ui;margin-top:4px">Once results are received, the Drive link '
            'must be recorded on the deal in <b>Metadata / Results Link</b> (<code>metadata_link</code>). '
            'A deal at Script Results Received with that field empty is not counted as delivered, and Shobit '
            'cannot begin commercials without it. Ignore the unused Script Output Link field — same rule as before.</div>')

    body = rule
    body += section("1 — Results received but no Drive link recorded (2 deals)", "", sec1)
    body += section("2 — GMeet Fixed with a link: attend (4 deals)", "", sec2)
    body += section("3 — Script Shared, stale: 13 days or more (9 deals)", "", sec3)
    body += section("4 — Script Shared, ageing: 5 to 12 days (5 deals)", "", sec4)
    body += section("5 — Script Shared, fresh: last 48 hours (12 deals)", "", sec5)
    body += section("Returned to callers — no meeting link (1 deal)",
                     "Sits at GMeet Fixed but has no link on the deal, so it is not yours yet. Listed for visibility only.",
                     returned)

    closing = ("<b>Two points.</b><br>"
               "Lise carries zero notes of any kind — same blind spot as last time: a deal with no recorded "
               "contact can't be told apart from one that was never worked.<br>"
               "Three deals (Mayank Chawla, Vaibhav Tayal from the same Yash handover, plus Encureit and Vikas "
               "Chauhan on separately promised dates) are all past an agreed callback date with nothing logged since — "
               "call these first today.<br><br>"
               "32 deals: 2 Script Results Received, 4 GMeet Fixed (link present), 26 Script Shared. A further "
               "1 sits at GMeet Fixed without a link and remains with Yuktha.")

    return wrap("Ishpreet", intro, body, closing)


# ==================================================================== SHOBIT
def shobit_html():
    rows = table(["Deal","Days","Owner","Issue","Action"], [
        ["Logicloom","7d","Ishpreet","Note (21d old, stale): most code is post-2024/vibe-coded, low value; other projects on Microsoft/AWS. Asked him to share project details on a sheet for evaluation — nothing since.","Chase the sheet; if it doesn't arrive this week, consider this a soft no."],
        ["Vision Infotech","7d","Lamiya","Note (8d old): GMeet held, script shared — nothing recorded on where commercials actually stand.","Get a real negotiation update; record it."],
        ["Humalect","3d","Yuktha","Data migration ongoing (per 1d-old note) — already past negotiation into Contract Signed, on track.","Keep monitoring migration; no action needed unless it stalls."],
        ["Travanleo Info Solutions India Pvt.","3d","Yuktha","Note (6d old) is about the script being shared, not commercials — negotiation status not recorded.","Confirm where the actual commercial conversation stands."],
        ["3SC","2d","Lamiya","Note (13d old): relevant, has 2 companies and some projects, scripts shared — no negotiation update since.","Follow up for a real commercial status."],
        ["Propreturns","2d","Lamiya","Called to follow up 9d ago, no pickup — nothing since.","Redial; try WhatsApp if silent again."],
        ["Phyt.Health","2d","Ishpreet","Note (15d old): relevant and interested, calendly link shared — unclear if the call ever happened. (Note also carries an odd future date, likely a typo — worth a sanity check.)","Confirm whether the call happened at all; record the real status."],
    ])
    intro = "Your band: Commercial Negotiation through Contract, Migration, Metadata and Payment, to close. <b>7 deals.</b>"
    body = section("All 7 deals", "Small band right now — every deal listed.", rows)
    closing = ("<b>One point.</b> Four of these seven (Logicloom, Vision Infotech, Travanleo, 3SC) have a note "
               "that describes an earlier stage (scripts, GMeets) rather than an actual commercial-negotiation "
               "update — worth getting a clean status on each rather than assuming the stage label reflects reality.<br><br>"
               "7 deals: 1 Deal Contract Signed, 6 Commercial Negotiation.")
    return wrap("Shobit", intro, body, closing)


# ============================================================ YUKTHA / LAMIYA
def caller_html(name, stats, gmeet_rows, interested13_rows):
    nopickup, i13, i512, i04, coldcall = stats
    intro = ("Your band: Cold Call through No Pickup and Interested, plus fixing the GMeet (the link is what "
             "hands it to Ishpreet, not the note). Summary below, full detail only for the exceptions that "
             "need a specific look.")
    summary_rows = table(["Bucket","Count","Note"], [
        ["Cold Call (live queue)", str(coldcall), "Being worked continuously — not a staleness signal."],
        ["No Pickup", str(nopickup), "Known migration artifact from 5 Aug — most of these were moved by script and never actually dialled. Re-verify before treating any single one as a scheduled callback; not itemized here for that reason."],
        ["Interested — fresh (0-4d)", str(i04), "Recently engaged, still within normal follow-up window."],
        ["Interested — ageing (5-12d)", str(i512), "Getting old without a recorded next step — worth a sweep this week even though not itemized individually below."],
        ["Interested — stale (13d+)", str(i13), "Itemized below — genuinely overdue."],
    ])
    body = section("Summary", "", summary_rows)

    if interested13_rows:
        t = table(["Deal","Days","Issue","Action"], interested13_rows)
        body += section(f"Interested, stale 13+ days ({len(interested13_rows)} deal{'s' if len(interested13_rows)!=1 else ''})",
                        "Genuinely overdue — full detail.", t)
    else:
        body += section("Interested, stale 13+ days (0 deals)", "None right now — clean.", "")

    if gmeet_rows:
        t = table(["Deal","Days","Issue","Action"], gmeet_rows)
        body += section(f"GMeet Fixed with NO link ({len(gmeet_rows)} deal{'s' if len(gmeet_rows)!=1 else ''}) — hard rule",
                        "Stays yours until the link is added — a note is not proof a meeting exists.", t)
    else:
        body += section("GMeet Fixed with NO link (0 deals)", "None right now — clean.", "")

    closing = "Nothing else needs individual attention right now — the Interested 5-12d bucket is worth a general sweep this week before it ages into the 13+ tier."
    return wrap(name, intro, body, closing)


def yuktha_html():
    gmeet = [["Aexonic Technologies","0d",
              "GMeet fixed for 9:30 AM tomorrow — no meeting link on the deal.",
              "Add the real meeting link once scheduled, or it can't hand off to Ishpreet."]]
    return caller_html("Yuktha", (261,0,30,30,63), gmeet, [])

def lamiya_html():
    interested13 = [
        ["TMRW House of Brands","14d","Note: “relevant lead” — nothing since, no next step recorded.","Call and record a real next step."],
        ["Sayy AI","14d","Sent a WhatsApp message; he said he would not run the script.","Likely a soft no — confirm and close out or reassign."],
        ["Olyv","13d","Left a WhatsApp message asking him to check with others — no reply since.","Follow up on WhatsApp; call if still silent."],
    ]
    return caller_html("Lamiya", (210,3,34,29,63), [], interested13)


if __name__ == "__main__":
    out = {
        "Ishpreet": ishpreet_html(),
        "Shobit": shobit_html(),
        "Yuktha": yuktha_html(),
        "Lamiya": lamiya_html(),
    }
    for name, html_ in out.items():
        path = f"/Users/bhanu/Desktop/hubspot/godown/band_reports/{name.lower()}.html"
        open(path, "w", encoding="utf-8").write("<!doctype html><meta charset=utf-8>" + html_)
        print("wrote", path)
