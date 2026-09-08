# -*- coding: utf-8 -*-
"""Week-on-week metrics from project start to now, mailed to Shobit. 11 metrics x weeks.

Same funnel definitions as the daily/weekly reports (imported from daily_activity_report), so
these numbers can't drift. Stage KPIs = deals that ENTERED a qualifying stage that week, human
moves only (sourceType=CRM_UI). LoC from the deal `loc` property (shown in Mn).

Metrics (exactly the 11 requested):
  1 Calls attempted (att)      2 Calls connected (conn)   3 VCs done (vc)
  4 Scripts shared (ss)        5 Script output recvd (rr) 6 Commercial negotiation (cn)
  7 Deal Contract signed (dcs) 8 Closed/Won (won)
  9 LoC closed        = sum(loc) of deals that entered Closed/Won that week
 10 LoC in pipeline   = sum(loc) of deals OPEN as of each week's end (created <= end, not yet
                        won or dead by end) — a real week-by-week pipeline trajectory
 11 Net New Leads Engaged = deals whose FIRST human (CRM_UI) stage move happened that week

Usage: python3 monthly_wow_report.py [--send]
"""
import os, sys, re, json, datetime, collections
import daily_activity_report as D

# Wrong-SPOC lives only in call notes (no dedicated stage). Wrong-number is the WrongNumber
# stage OR a Bad-number note. Both are DATA-QUALITY rejects, not genuine engagement, so they
# come out of Net New Leads Engaged — which should mean "a real prospect got worked."
WRONG_SPOC = re.compile(r"wrong\s*spoc|wrong\s*poc|wrong\s+(person|contact)|"
                        r"not\s+the\s+(right|correct)\s+(person|spoc|poc|contact)|"
                        r"not\s+a\s+founder|not\s+(a\s+)?relevant\s+poc|different\s+(person|company)|"
                        r"is\s+not\s+the\s+right|gave\s+me\s+another\s+number", re.I)

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
TO = "shobit.gupta@lh2.ai"
SEND = "--send" in sys.argv
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
ALIAS = {"Call Attempted": "No Pickup", "Call Attempted (retired)": "No Pickup"}
RANK = {"att": 1, "conn": 2, "gm": 3, "vc": 3, "ss": 4, "rr": 5, "ev": 6, "cn": 6, "neg": 7, "dcs": 7, "won": 8}
DEPTH = {0: "Touched, screened before dial", 1: "Attempted (no further)", 2: "Connected",
         3: "Meeting / VC done", 4: "Script shared", 5: "Script output received",
         6: "Commercial negotiation", 7: "Contract signed", 8: "Closed / Won"}
WANT = [("att", "No. of calls attempted"), ("conn", "No. of calls connected"),
        ("vc", "No. of VCs done"), ("ss", "No. of scripts shared"),
        ("rr", "No. of script output received"), ("cn", "No. of commercial negotiation done"),
        ("dcs", "No. of Deal Contract signed"), ("won", "No. of Closed/Won")]


def num(v):
    try: return float(v)
    except Exception: return 0.0


def pull():
    _, pd = D.hs("/crm/v3/pipelines/deals")
    STG = {s["id"]: s["label"] for p in pd["results"] for s in p["stages"]}
    ids, after = [], None
    while True:
        b = {"limit": 100, "properties": ["dealname"], "filterGroups": []}
        if after: b["after"] = after
        _, r = D.hs("/crm/v3/objects/deals/search", "POST", b)
        ids += [x["id"] for x in r.get("results", [])]
        after = (r.get("paging") or {}).get("next", {}).get("after")
        if not after: break
    deals = []
    for i in range(0, len(ids), 50):
        _, r = D.hs("/crm/v3/objects/deals/batch/read", "POST",
                    {"inputs": [{"id": x} for x in ids[i:i + 50]],
                     "properties": ["dealname", "loc", "createdate", "dealstage", "lead_source"],
                     "propertiesWithHistory": ["dealstage"]})
        deals += r.get("results", [])
    # notes -> flag deals that are wrong-number / wrong-spoc (data-quality rejects)
    d2n, nids = {}, set()
    for i in range(0, len(ids), 100):
        _, r = D.hs("/crm/v4/associations/deals/notes/batch/read", "POST",
                    {"inputs": [{"id": x} for x in ids[i:i + 100]]})
        for row in r.get("results", []):
            ns = [str(t["toObjectId"]) for t in row.get("to", [])]
            d2n[str(row["from"]["id"])] = ns; nids |= set(ns)
    nbody = {}
    nl = sorted(nids)
    for i in range(0, len(nl), 100):
        _, r = D.hs("/crm/v3/objects/notes/batch/read", "POST",
                    {"inputs": [{"id": x} for x in nl[i:i + 100]], "properties": ["hs_note_body"]})
        for x in r.get("results", []): nbody[x["id"]] = D.plain(x["properties"].get("hs_note_body") or "")
    wrong = {}   # deal_id -> True if wrong-number or wrong-spoc in its notes
    for did, ns in d2n.items():
        for nid in ns:
            b = nbody.get(nid, "")
            if not b: continue
            if D.classify(b.lower()) == "Bad number" or WRONG_SPOC.search(b):
                wrong[did] = True; break
    return deals, STG, wrong


def main():
    deals, STG, wrong = pull()
    today = datetime.datetime.now(IST).date()
    # weeks from the earliest create/event to now, Mon-Sun
    days = []
    for dl in deals:
        c = D.ist_day(dl["properties"].get("createdate"))
        if c: days.append(c)
    start = datetime.date.fromisoformat(min(days)) if days else today
    first_mon = start - datetime.timedelta(days=start.weekday())
    weeks = []
    m = first_mon
    while m <= today:
        weeks.append((m, min(m + datetime.timedelta(days=6), today)))
        m += datetime.timedelta(weeks=1)

    def widx(day):
        for i, (mo, en) in enumerate(weeks):
            if mo.isoformat() <= day <= (mo + datetime.timedelta(days=6)).isoformat(): return i
        return None

    kpi = collections.defaultdict(collections.Counter)      # week -> Counter(kpi)
    loc_closed = collections.Counter()                      # week -> loc(Mn) won that week
    netnew = collections.Counter()                          # week -> first-touch that week (genuine)
    excluded = collections.Counter()                        # week -> first-touch but wrong-num/spoc
    netnew_src = collections.defaultdict(collections.Counter)  # week -> Counter(lead_source) genuine
    depth = collections.defaultdict(collections.Counter)       # week -> Counter(furthest-stage rank)
    dealinfo = []
    for dl in deals:
        p = dl["properties"]
        loc = num(p.get("loc"))
        src = p.get("lead_source") or "(untagged)"
        cday = D.ist_day(p.get("createdate"))
        is_wrong = wrong.get(dl["id"], False)
        hist = sorted((dl.get("propertiesWithHistory", {}).get("dealstage") or []),
                      key=lambda e: e.get("timestamp", ""))
        won_day = dead_day = None; first_human = None; maxr = 0
        for j, e in enumerate(hist):
            lab = ALIAS.get(STG.get(e.get("value")), STG.get(e.get("value"), ""))
            day = D.ist_day(e.get("timestamp"))
            human = j > 0 and e.get("sourceType") == "CRM_UI"
            if human and first_human is None: first_human = day
            if "WrongNumber" in lab: is_wrong = True     # WrongNumber stage also = reject
            for k in D.metrics_for(lab): maxr = max(maxr, RANK.get(k, 0))   # furthest depth ever
            if human and day:
                wi = widx(day)
                if wi is not None:
                    for k in D.metrics_for(lab): kpi[wi][k] += 1
            if lab == "Closed/Won" and won_day is None: won_day = day
            if lab.startswith("Dead/") and dead_day is None: dead_day = day
        if won_day:
            wi = widx(won_day)
            if wi is not None: loc_closed[wi] += loc
        if first_human:
            wi = widx(first_human)
            if wi is not None:
                if is_wrong: excluded[wi] += 1           # first-worked but a wrong-num/spoc reject
                else:                                    # genuinely engaged prospect
                    netnew[wi] += 1; netnew_src[wi][src] += 1; depth[wi][maxr] += 1
        dealinfo.append((cday, loc, won_day, dead_day))

    # LoC in pipeline as of each week's END
    loc_pipe = {}
    for i, (mo, en) in enumerate(weeks):
        wend = (mo + datetime.timedelta(days=6)).isoformat()
        tot = 0.0
        for cday, loc, won_day, dead_day in dealinfo:
            if not cday or cday > wend: continue
            if won_day and won_day <= wend: continue
            if dead_day and dead_day <= wend: continue
            tot += loc
        loc_pipe[i] = tot

    # ---- render table: rows = metrics, cols = weeks ----
    hdr = "".join(f'<th style="{TH}">{mo.strftime("%d %b")}</th>' for mo, en in weeks)
    def row(label, vals, mn=False):
        cells = "".join(f'<td style="{TD};text-align:right;font-variant-numeric:tabular-nums">'
                        f'{(f"{v/1e6:.2f}" if mn else f"{int(v)}")}</td>' for v in vals)
        return f'<tr><td style="{TD};color:#374151">{label}</td>{cells}</tr>'
    body_rows = "".join(row(lbl, [kpi[i][k] for i in range(len(weeks))]) for k, lbl in WANT)
    body_rows += row("No. of LoC closed (Mn)", [loc_closed[i] for i in range(len(weeks))], mn=True)
    body_rows += row("No. of LoC in pipeline (Mn)", [loc_pipe[i] for i in range(len(weeks))], mn=True)
    body_rows += row("No. of Net New Leads Engaged (genuine)", [netnew[i] for i in range(len(weeks))])
    # reference row: how many were stripped as wrong-number / wrong-SPOC before counting genuine
    excl_cells = "".join(f'<td style="{TD};text-align:right;color:#b91c1c;font-variant-numeric:tabular-nums">'
                         f'−{excluded[i]}</td>' for i in range(len(weeks)))
    body_rows += (f'<tr><td style="{TD};color:#9ca3af;font-style:italic">   ↳ wrong-number / SPOC removed (ref)</td>{excl_cells}</tr>')

    # ---- section 2: genuine engaged split by lead source ----
    srcs = sorted({s for w in netnew_src.values() for s in w},
                  key=lambda s: -sum(netnew_src[i][s] for i in range(len(weeks))))
    src_rows = "".join(row(s, [netnew_src[i][s] for i in range(len(weeks))]) for s in srcs)
    # ---- section 3: genuine engaged split by furthest pipeline stage ----
    dep_rows = "".join(row(DEPTH[r], [depth[i][r] for i in range(len(weeks))]) for r in range(8, -1, -1)
                       if any(depth[i][r] for i in range(len(weeks))))

    span = f'{weeks[0][0].strftime("%d %b")} – {today.strftime("%d %b %Y")}'
    sec = lambda title, sub, rows: (
        f'<div style="font:700 14px system-ui;color:#111827;margin:26px 0 4px">{title}</div>'
        f'<div style="color:#9ca3af;font:12px system-ui;margin-bottom:8px">{sub}</div>'
        f'<div style="overflow-x:auto"><table style="border-collapse:collapse;width:100%">'
        f'<tr><th style="{TH}"></th>{hdr}</tr>{rows}</table></div>')
    HTML = f'''<div style="max-width:1000px;margin:0 auto;padding:24px;font-family:system-ui">
      <div style="font:800 21px system-ui;color:#111827">LH2 Supply Funnel — Week-on-Week</div>
      <div style="color:#6b7280;font:14px system-ui;margin:4px 0 18px">{span} · week columns show week-start (Mon)</div>
      <div style="overflow-x:auto"><table style="border-collapse:collapse;width:100%">
        <tr><th style="{TH}">Metric</th>{hdr}</tr>{body_rows}
      </table></div>
      {sec("Genuine engaged — by lead source", "Where the genuinely engaged leads came from (wrong-number / SPOC already removed).", src_rows)}
      {sec("Genuine engaged — by furthest pipeline stage", "How far each week's engaged cohort ultimately got. Sums to Net New Leads Engaged (genuine).", dep_rows)}
      <div style="margin-top:26px;border-top:1px solid #e6e9ef;padding-top:14px">
        <div style="font:700 14px system-ui;color:#111827;margin-bottom:8px">How to read this report</div>
        <div style="font:13px/1.55 system-ui;color:#4b5563">
          <b>Week columns</b> are Monday-start weeks; the last column is the current, partial week (Mon → today).<br>
          <b>Counting rule for all funnel stages:</b> a deal is counted in the week it <i>entered</i> that stage.
          Only <b>human actions count</b> — HubSpot's <code>sourceType = CRM_UI</code>; bulk API / migration / script
          writes (~42% of all stage changes) are excluded, so these are things a person actually did.
          <ul style="margin:8px 0;padding-left:20px">
            <li><b>Calls attempted</b> — a deal entered a dialled stage (No Pickup / Interested / Not-Interested / Wrong-Number). A dial happened.</li>
            <li><b>Calls connected</b> — entered Interested or Not-Interested, i.e. someone picked up and talked.</li>
            <li><b>VCs done</b> — entered a video-call / meeting-held stage (Script Shared or a Dead-after-GMeet outcome).</li>
            <li><b>Scripts shared</b> — entered Script Shared. &nbsp;<b>Script output received</b> — entered Script Results Received.</li>
            <li><b>Commercial negotiation</b> — entered Commercial Negotiation. &nbsp;<b>Deal Contract signed</b> — entered Deal Contract Signed. &nbsp;<b>Closed/Won</b> — entered Closed/Won.</li>
            <li><b>LoC closed (Mn)</b> — sum of the deal's <code>loc</code> (lines of code) for deals that reached Closed/Won that week, in millions.</li>
            <li><b>LoC in pipeline (Mn)</b> — sum of <code>loc</code> for deals still <i>open</i> (not won, not dead) as of that week's end — a running size of the open pipeline.</li>
            <li><b>Net New Leads Engaged (genuine)</b> — leads that got their <b>first human touch</b> that week, <b>after removing</b> wrong-number and wrong-SPOC rejects.</li>
            <li><b>↳ wrong-number / SPOC removed (ref)</b> — how many first-touched leads were stripped: <b>wrong-number</b> = hit the Wrong-Number stage or a "bad number" note; <b>wrong-SPOC</b> = a note saying wrong person / wrong POC / not a founder. Shown only for reference — the dialling effort still counts under Calls Attempted.</li>
          </ul>
          <b>Genuine engaged — by lead source:</b> the same genuine-engaged leads, broken out by which channel they came from.<br>
          <b>Genuine engaged — by furthest pipeline stage:</b> the same leads, each counted <b>once, at the deepest stage it ever reached</b>.
          "Touched, screened before dial" = engaged but screened out (wrong-fit) before an actual dial. This split sums to Net New Leads Engaged (genuine).
        </div>
        <div style="color:#9ca3af;font:12px system-ui;margin-top:12px">
          Same definitions as the daily report. Generated {datetime.datetime.now(IST).strftime("%d %b %Y %H:%M IST")}.
        </div>
      </div></div>'''

    TXT = [f"LH2 supply funnel — week-on-week, {span}\n"]
    for k, lbl in WANT:
        TXT.append(f"{lbl}: " + " | ".join(f"{mo.strftime('%d%b')}:{kpi[i][k]}" for i, (mo, en) in enumerate(weeks)))
    TXT.append("No. of LoC closed (Mn): " + " | ".join(f"{mo.strftime('%d%b')}:{loc_closed[i]/1e6:.2f}" for i, (mo, en) in enumerate(weeks)))
    TXT.append("No. of LoC in pipeline (Mn): " + " | ".join(f"{mo.strftime('%d%b')}:{loc_pipe[i]/1e6:.2f}" for i, (mo, en) in enumerate(weeks)))
    TXT.append("No. of Net New Leads Engaged (genuine): " + " | ".join(f"{mo.strftime('%d%b')}:{netnew[i]}" for i, (mo, en) in enumerate(weeks)))
    TXT.append("  (ref) wrong-number/SPOC removed: " + " | ".join(f"{mo.strftime('%d%b')}:{excluded[i]}" for i, (mo, en) in enumerate(weeks)))
    TXT.append("\n-- Genuine engaged by LEAD SOURCE --")
    for s in srcs:
        TXT.append(f"{s}: " + " | ".join(f"{mo.strftime('%d%b')}:{netnew_src[i][s]}" for i, (mo, en) in enumerate(weeks)))
    TXT.append("\n-- Genuine engaged by FURTHEST STAGE --")
    for r in range(8, -1, -1):
        if any(depth[i][r] for i in range(len(weeks))):
            TXT.append(f"{DEPTH[r]}: " + " | ".join(f"{mo.strftime('%d%b')}:{depth[i][r]}" for i, (mo, en) in enumerate(weeks)))
    TXT.append("""
-- HOW TO READ THIS --
Week columns are Monday-start weeks; the last is the current partial week (Mon->today).
All funnel stages: a deal is counted in the week it ENTERED that stage, human actions only
(HubSpot sourceType=CRM_UI; bulk/API/migration writes excluded).
  Calls attempted      = entered a dialled stage (a dial happened)
  Calls connected      = entered Interested / Not-Interested (someone picked up)
  VCs done             = entered a meeting-held stage
  Scripts shared       = entered Script Shared;  Script output received = Script Results Received
  Commercial negotiation / Deal Contract signed / Closed-Won = entered that stage
  LoC closed (Mn)      = sum of the deal 'loc' for deals reaching Closed/Won that week
  LoC in pipeline (Mn) = sum of 'loc' for deals still open (not won/dead) as of week end
  Net New Leads Engaged (genuine) = leads first worked that week, wrong-number/SPOC removed
  (ref) wrong-number/SPOC removed = wrong-number (WrongNumber stage or 'bad number' note) or
        wrong-SPOC (note: wrong person/POC). Effort still counts under Calls Attempted.
By lead source  = the genuine engaged, by channel.
By furthest stage = each engaged lead once, at the deepest stage it reached ('Touched, screened
        before dial' = engaged but screened out before a dial). Sums to Net New Engaged (genuine).""")
    text = "\n".join(TXT)
    print("[report built — sections: metrics, source split, depth split, definitions]")

    out = os.path.join(HUB, "godown", "weekly_reports", "wow_metrics.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write("<!doctype html><meta charset=utf-8>" + HTML)
    print(f"\nwrote {out}")
    if not SEND:
        print("DRY — re-run with --send to mail Shobit"); return
    import gmail_sender
    t, det = gmail_sender.send(TO, f"LH2 supply funnel — week-on-week metrics ({span})", text, html=HTML)
    print(f"sent to {TO} via [{t}] {det}")


TD = "padding:6px 10px;border-bottom:1px solid #e6e9ef;font:13px system-ui"
TH = "padding:7px 10px;text-align:right;font:600 11px system-ui;color:#6b7280;text-transform:uppercase;border-bottom:2px solid #d1d5db"
main()
