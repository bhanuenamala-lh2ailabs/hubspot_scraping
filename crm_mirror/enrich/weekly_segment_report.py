# -*- coding: utf-8 -*-
"""Four weekly funnel reports (last 4 Mon-Sun weeks), each split Scraped vs Campaign, and
Campaign further split LinkedIn vs Outflo. Renders HTML -> PDF (Chrome headless) and mails
all four PDFs to Ishpreet.

Metrics are the SAME funnel KPIs the daily reports use — imported from daily_activity_report
(METRICS/metrics_for), so these can never drift from the daily numbers. A KPI counts a deal
that ENTERED a qualifying stage on a given day, human moves only (sourceType=CRM_UI).

Segments, from each deal's pipeline + lead_source:
  scraped            pipeline = Scraped (default)
  campaign_linkedin  pipeline = Campaign AND lead_source ~ Linkedin Campaign
  campaign_outflo    pipeline = Campaign AND lead_source ~ Outflo

Usage: python3 weekly_segment_report.py [--send]   (omit --send to build PDFs without mailing)
"""
import os, sys, json, html, datetime, subprocess, collections, urllib.request, urllib.error
import daily_activity_report as D   # METRICS, metrics_for, ist_day, KPI, hs

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HUB, "godown", "weekly_reports"); os.makedirs(OUT, exist_ok=True)
TO = "ishpreet.sood@lh2.ai"
SEND = "--send" in sys.argv
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
ALIAS = {"Call Attempted": "No Pickup", "Call Attempted (retired)": "No Pickup"}
KPI_LABEL = {"att": "Call attempted", "conn": "Connected", "gm": "GMeet fixed", "vc": "VC done",
             "ss": "Script shared", "rr": "Result received", "ev": "Evaluation", "cn": "Comm. neg.",
             "neg": "Neg. calls", "dcs": "Contract signed", "won": "Closed / Won"}


def segment(pipe_label, src):
    if pipe_label == "Scraped": return "scraped"
    s = (src or "").lower()
    if "linkedin" in s: return "campaign_linkedin"
    if "outflo" in s: return "campaign_outflo"
    return "campaign_other"


def weeks():
    """Last 4 Mon-Sun weeks, most recent first. Current week runs Mon..today."""
    today = datetime.datetime.now(IST).date()
    monday = today - datetime.timedelta(days=today.weekday())
    out = []
    for i in range(4):
        wk_mon = monday - datetime.timedelta(weeks=i)
        wk_sun = wk_mon + datetime.timedelta(days=6)
        end = min(wk_sun, today)
        out.append((wk_mon, wk_sun, end))
    return out


def pull():
    s, d = D.hs("/crm/v3/pipelines/deals")
    LAB = {x["id"]: {st["id"]: st["label"] for st in x["stages"]} for x in d["results"]}
    PIPE = {x["id"]: x["label"] for x in d["results"]}
    # the SEARCH endpoint silently ignores propertiesWithHistory — only batch/read returns it.
    # So: enumerate ids via search, then batch/read (max 50 per call WITH history) for the
    # dealstage timeline. Skipping this two-step is why the first run counted zero events.
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
                     "properties": ["dealname", "pipeline", "lead_source", "createdate"],
                     "propertiesWithHistory": ["dealstage"]})
        deals += r.get("results", [])
    return deals, LAB, PIPE


def build_counts():
    deals, LAB, PIPE = pull()
    wk = weeks()

    def which_week(day):
        for idx, (mon, sun, end) in enumerate(wk):
            if mon.isoformat() <= day <= sun.isoformat(): return idx
        return None

    # counts[week_idx][segment][kpi] = n ; added[week_idx][segment] = new deals
    counts = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    added = collections.defaultdict(collections.Counter)
    for dl in deals:
        p = dl["properties"]; pipe = PIPE.get(p.get("pipeline"), p.get("pipeline", ""))
        seg = segment(pipe, p.get("lead_source"))
        stg = LAB.get(p.get("pipeline"), {})
        # new-deal count by createdate
        cday = D.ist_day(p.get("createdate"))
        wi = which_week(cday) if cday else None
        if wi is not None: added[wi][seg] += 1
        # stage-entry KPI counts, human (CRM_UI) moves only
        hist = sorted((dl.get("propertiesWithHistory", {}).get("dealstage") or []),
                      key=lambda e: e.get("timestamp", ""))
        for j, e in enumerate(hist):
            if j == 0 or e.get("sourceType") != "CRM_UI": continue
            lab = ALIAS.get(stg.get(e.get("value")), stg.get(e.get("value"), ""))
            day = D.ist_day(e.get("timestamp"))
            wi = which_week(day) if day else None
            if wi is None: continue
            for k in D.metrics_for(lab): counts[wi][seg][k] += 1
    return counts, added, wk


TD = "padding:7px 12px;border-bottom:1px solid #e6e9ef;font:14px system-ui"
TH = "padding:8px 12px;text-align:left;font:600 12px system-ui;color:#6b7280;text-transform:uppercase;letter-spacing:.04em"


def seg_table(title, cnt, added_n, accent):
    cells = "".join(
        f'<tr><td style="{TD};color:#374151">{KPI_LABEL[k]}</td>'
        f'<td style="{TD};text-align:right;font-weight:600;color:#111827">{cnt.get(k,0)}</td></tr>'
        for k, _ in D.KPI)
    return (f'<div style="border:1px solid #e6e9ef;border-radius:12px;overflow:hidden;margin:0 0 18px">'
            f'<div style="background:{accent};padding:12px 16px;color:#fff">'
            f'<span style="font:700 15px system-ui">{title}</span>'
            f'<span style="float:right;font:600 13px system-ui;opacity:.9">{added_n} new leads</span></div>'
            f'<table style="width:100%;border-collapse:collapse">'
            f'<tr><th style="{TH}">Funnel stage</th><th style="{TH};text-align:right">This week</th></tr>'
            f'{cells}</table></div>')


def render_week(wi, wk, counts, added):
    mon, sun, end = wk[wi]
    c = counts[wi]; a = added[wi]
    camp_total = collections.Counter()
    for seg in ("campaign_linkedin", "campaign_outflo", "campaign_other"):
        camp_total.update(c.get(seg, {}))
    body = f'''<div style="max-width:760px;margin:0 auto;padding:28px;font-family:system-ui">
      <div style="font:800 22px system-ui;color:#111827">LH2 Supply Funnel — Weekly Report</div>
      <div style="color:#6b7280;font:15px system-ui;margin:4px 0 22px">
        Week of {mon.strftime("%d %b")} – {sun.strftime("%d %b %Y")}
        {"(partial, to " + end.strftime("%d %b") + ")" if end < sun else ""}
      </div>
      <div style="font:700 13px system-ui;color:#0e7490;text-transform:uppercase;letter-spacing:.05em;margin:0 0 10px">Scraped pipeline</div>
      {seg_table("Scraped — all sources", c.get("scraped", {}), a.get("scraped", 0), "#0e7490")}
      <div style="font:700 13px system-ui;color:#7c3aed;text-transform:uppercase;letter-spacing:.05em;margin:14px 0 10px">Campaign pipeline</div>
      {seg_table("Campaign — LinkedIn", c.get("campaign_linkedin", {}), a.get("campaign_linkedin", 0), "#7c3aed")}
      {seg_table("Campaign — Outflo", c.get("campaign_outflo", {}), a.get("campaign_outflo", 0), "#9333ea")}
      {seg_table("Campaign — TOTAL", camp_total, a.get("campaign_linkedin", 0)+a.get("campaign_outflo", 0)+a.get("campaign_other", 0), "#6d28d9")}
      <div style="color:#9ca3af;font:12px system-ui;margin-top:16px">
        Counts = deals that ENTERED each stage that week, human moves only (CRM_UI). Same
        definitions as the daily funnel report. Generated {datetime.datetime.now(IST).strftime("%d %b %Y %H:%M IST")}.
      </div></div>'''
    return body


def html_to_pdf(hbody, stem):
    hp = os.path.join(OUT, stem + ".html"); pp = os.path.join(OUT, stem + ".pdf")
    open(hp, "w", encoding="utf-8").write("<!doctype html><meta charset=utf-8><body style='margin:0'>" + hbody)
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pp}", "file://" + hp], capture_output=True, timeout=60)
    return pp if os.path.exists(pp) else None


def main():
    counts, added, wk = build_counts()
    pdfs = []
    for wi in range(4):
        mon = wk[wi][0]
        stem = f"weekly_funnel_{mon.isoformat()}"
        pdf = html_to_pdf(render_week(wi, wk, counts, added), stem)
        tot = sum(sum(v.values()) for v in counts[wi].values())
        print(f"week of {mon}: {'PDF ok' if pdf else 'PDF FAILED'} | total stage-events {tot}")
        if pdf: pdfs.append((mon, pdf))
    if not SEND:
        print(f"\nbuilt {len(pdfs)} PDFs in {OUT} — re-run with --send to mail Ishpreet"); return
    import gmail_sender
    atts = [(f"LH2_weekly_{m.isoformat()}.pdf", open(p, "rb").read(), "application/pdf") for m, p in pdfs]
    span = f"{wk[3][0].strftime('%d %b')} – {wk[0][2].strftime('%d %b %Y')}"
    bodytxt = ("Hi Ishpreet,\n\nFour weekly supply-funnel reports attached (last 4 weeks, "
               f"{span}). Each PDF splits Scraped vs Campaign, and Campaign into LinkedIn vs "
               "Outflo. Counts are stage entries that week, human moves only — same definitions "
               "as the daily report.\n\n— sent via assistant")
    t, det = gmail_sender.send(TO, f"LH2 supply funnel — last 4 weekly reports ({span})", bodytxt, attachments=atts)
    print(f"\nsent {len(atts)} PDFs to {TO} via [{t}] {det}")


main()
