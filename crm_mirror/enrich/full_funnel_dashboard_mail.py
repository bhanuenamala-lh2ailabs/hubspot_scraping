# -*- coding: utf-8 -*-
"""Full HubSpot Funnel — Dashboard Format. Revenue-Dashboard-style layout: a 3-number top strip
(Wins to Date / 7-Day Leads Engaged / Daily Leads Engaged) plus a table of 11 deal-stage rows
(Leads Assigned .. Deal Contract Signed, then Closed/Won, then Dead combined), each with
Inception-to-Date / Rolling 7 Days / Daily columns.

Decision record for this format: docs/reference/FUNNEL_DASHBOARD_TOP_STRIP_DECISION.md.

Depends on full_funnel_report.py's snapshot store (crm_mirror/data/snapshots/full_funnel_<date>.json)
having run for at least the last 14 days with dashboard_flow/cumulative/engaged_deal_ids populated —
run full_funnel_report.py daily to keep that store current before running this.

Usage: python3 full_funnel_dashboard_mail.py [--send --to you@lh2.ai]
"""
import sys, datetime
from full_funnel_report import DASHBOARD_ROWS, read_snapshot, today_ist, IST
import gmail_sender

ARG = sys.argv
SEND = "--send" in ARG
TO = ARG[ARG.index("--to") + 1] if "--to" in ARG else "bhanu.enamala@lh2.ai"

UP = "#1a7f37"; DOWN = "#c0362c"; INK = "#1c2130"; MUTED = "#6b7280"
GROUPBG = "#eceef2"; SUBBG = "#f5f6f8"; BASEBG = "#eaf1fb"; TOTALBG = "#eef2f7"
BORDER = "#e2e4e8"


def pct_change(cur, prev):
    if prev in (0, None):
        return None if not cur else 100.0
    return (cur - prev) / prev * 100


def chip(pct):
    if pct is None:
        return f'<span style="color:{MUTED};">flat</span>'
    arrow = "&#8595;" if pct < 0 else "&#8593;"
    color = DOWN if pct < 0 else UP
    return f'<span style="color:{color};font-weight:700;">{arrow} {abs(round(pct))}%</span>'


def fmt(n):
    return "—" if n is None else f"{n:,}"


def window(d0, days_back_start, days_back_end):
    """Snapshots from days_back_start..days_back_end (inclusive) back from d0."""
    return [read_snapshot(d0 - datetime.timedelta(days=i)) for i in range(days_back_start, days_back_end + 1)]


def build_rows():
    d0 = today_ist()
    today_snap = read_snapshot(d0)
    yest_snap = read_snapshot(d0 - datetime.timedelta(days=1))
    roll7_snaps = window(d0, 0, 6)
    prev7_snaps = window(d0, 7, 13)
    have_roll7 = all(roll7_snaps)
    have_prev7 = all(prev7_snaps)

    rows = []
    for label, _, _ in DASHBOARD_ROWS:
        inception = today_snap["cumulative"][label]
        today_v = today_snap["dashboard_flow"][label]
        yest_v = yest_snap["dashboard_flow"][label] if yest_snap else None
        roll7_v = sum(s["dashboard_flow"][label] for s in roll7_snaps) if have_roll7 else None
        prev7_v = sum(s["dashboard_flow"][label] for s in prev7_snaps) if have_prev7 else None
        rows.append({"label": label, "inception": inception, "today": today_v, "yest": yest_v,
                     "roll7": roll7_v, "prev7": prev7_v})
    return rows, today_snap, roll7_snaps, prev7_snaps


def leads_engaged(today_snap, roll7_snaps, prev7_snaps):
    """Deduplicated by deal ID via a real set union across each window, not a sum of daily counts."""
    today_n = len(today_snap.get("engaged_deal_ids", []))
    roll7_n = len(set().union(*(set(s["engaged_deal_ids"]) for s in roll7_snaps))) if all(roll7_snaps) else None
    prev7_n = len(set().union(*(set(s["engaged_deal_ids"]) for s in prev7_snaps))) if all(prev7_snaps) else None
    return today_n, roll7_n, prev7_n


def won_delta(d0, today_snap):
    s7 = read_snapshot(d0 - datetime.timedelta(days=7))
    won_today = today_snap["cumulative"]["Closed/Won"]
    won_7ago = s7["cumulative"]["Closed/Won"] if s7 else None
    delta = None if won_7ago is None else won_today - won_7ago
    return won_today, delta


def strip_box(label, value, sub_html):
    return f"""
    <td style="text-align:center;padding:18px 24px;">
      <div style="font-size:11px;font-weight:800;letter-spacing:.06em;color:{MUTED};">{label}</div>
      <div style="font-size:26px;font-weight:800;color:{INK};margin-top:4px;">{value}</div>
      <div style="font-size:13px;margin-top:4px;">{sub_html}</div>
    </td>"""


def gap_td():
    return '<td style="width:18px;border:none;"></td>'


def build_html(rows, top_strip_html, roll7_dates, prev7_dates, today_date, yest_date):
    head_group = f"""
    <tr>
      <td style="border:none;"></td>
      <td style="background:{GROUPBG};text-align:center;font-size:11px;font-weight:800;
        letter-spacing:.04em;padding:8px 6px;color:{INK};border:1px solid {BORDER};">INCEPTION TO DATE</td>
      {gap_td()}
      <td colspan="3" style="background:{GROUPBG};text-align:center;font-size:11px;font-weight:800;
        letter-spacing:.04em;padding:8px 6px;color:{INK};border:1px solid {BORDER};">ROLLING 7 DAYS</td>
      {gap_td()}
      <td colspan="3" style="background:{GROUPBG};text-align:center;font-size:11px;font-weight:800;
        letter-spacing:.04em;padding:8px 6px;color:{INK};border:1px solid {BORDER};">DAILY</td>
    </tr>"""
    head_sub = f"""
    <tr>
      <td style="border:none;"></td>
      <td style="background:{BASEBG};text-align:center;font-size:11px;font-weight:700;padding:6px;
        color:{INK};border:1px solid {BORDER};">All-time</td>
      {gap_td()}
      <td style="background:{SUBBG};text-align:center;font-size:11px;font-weight:700;padding:6px;
        color:{INK};border:1px solid {BORDER};">{roll7_dates[0]} - {roll7_dates[1]}</td>
      <td style="background:{SUBBG};text-align:center;font-size:11px;font-weight:700;padding:6px;
        color:{INK};border:1px solid {BORDER};">{prev7_dates[0]} - {prev7_dates[1]}</td>
      <td style="background:{SUBBG};text-align:center;font-size:11px;font-weight:700;padding:6px;
        color:{INK};border:1px solid {BORDER};">Change</td>
      {gap_td()}
      <td style="background:{SUBBG};text-align:center;font-size:11px;font-weight:700;padding:6px;
        color:{INK};border:1px solid {BORDER};">{today_date}</td>
      <td style="background:{SUBBG};text-align:center;font-size:11px;font-weight:700;padding:6px;
        color:{INK};border:1px solid {BORDER};">{yest_date}</td>
      <td style="background:{SUBBG};text-align:center;font-size:11px;font-weight:700;padding:6px;
        color:{INK};border:1px solid {BORDER};">Change</td>
    </tr>"""
    body = ""
    for r in rows:
        bold = r["label"] in ("Closed/Won", "Dead")
        namestyle = "font-weight:800;" if bold else "font-weight:600;"
        rowbg = TOTALBG if bold else "#ffffff"
        r7_chg = pct_change(r["roll7"], r["prev7"])
        d_chg = pct_change(r["today"], r["yest"])
        body += f"""
        <tr style="background:{rowbg};">
          <td style="{namestyle}font-size:13px;padding:7px 10px;border:1px solid {BORDER};color:{INK};">{r['label']}</td>
          <td style="background:{BASEBG};text-align:right;font-size:13px;padding:7px 10px;border:1px solid {BORDER};
            font-style:italic;color:{INK};">{fmt(r['inception'])}</td>
          {gap_td()}
          <td style="text-align:right;font-size:13px;padding:7px 10px;border:1px solid {BORDER};color:{INK};">{fmt(r['roll7'])}</td>
          <td style="text-align:right;font-size:13px;padding:7px 10px;border:1px solid {BORDER};color:{INK};">{fmt(r['prev7'])}</td>
          <td style="text-align:right;font-size:13px;padding:7px 10px;border:1px solid {BORDER};">{chip(r7_chg)}</td>
          {gap_td()}
          <td style="text-align:right;font-size:13px;padding:7px 10px;border:1px solid {BORDER};color:{INK};">{fmt(r['today'])}</td>
          <td style="text-align:right;font-size:13px;padding:7px 10px;border:1px solid {BORDER};color:{INK};">{fmt(r['yest'])}</td>
          <td style="text-align:right;font-size:13px;padding:7px 10px;border:1px solid {BORDER};">{chip(d_chg)}</td>
        </tr>"""

    return f"""
<div style="font-family:Arial,Helvetica,sans-serif;color:{INK};max-width:900px;">
<h2 style="margin-bottom:14px;">Full HubSpot Funnel — {today_date}</h2>
{top_strip_html}
<table style="border-collapse:separate;border-spacing:0;width:100%;margin-top:14px;">
  {head_group}
  {head_sub}
  {body}
</table>
</div>
"""


def build_plain(rows, won_today, won_d, le_today, le_roll7, le_prev7, today_date):
    lines = [f"Full HubSpot Funnel — {today_date}", "",
             f"WINS TO DATE: {won_today}  ({'flat' if not won_d else ('+' if won_d>0 else '')+str(won_d)+' this week'})",
             f"7-DAY LEADS ENGAGED: {fmt(le_roll7)}  (vs {fmt(le_prev7)} prev7)",
             f"DAILY LEADS ENGAGED: {le_today}", "",
             f"{'Stage':<26}{'Inception':>10}{'Roll7':>8}{'Prev7':>8}{'Today':>8}{'Yest':>7}"]
    for r in rows:
        lines.append(f"{r['label']:<26}{fmt(r['inception']):>10}{fmt(r['roll7']):>8}{fmt(r['prev7']):>8}{fmt(r['today']):>8}{fmt(r['yest']):>7}")
    return "\n".join(lines)


def main():
    d0 = today_ist()
    rows, today_snap, roll7_snaps, prev7_snaps = build_rows()
    le_today, le_roll7, le_prev7 = leads_engaged(today_snap, roll7_snaps, prev7_snaps)
    won_today, won_d = won_delta(d0, today_snap)

    daily_avg_prev7 = (le_prev7 / 7) if le_prev7 is not None else None
    le_daily_chg = pct_change(le_today, daily_avg_prev7)
    le_roll7_chg = pct_change(le_roll7, le_prev7)
    won_sub = (f'<span style="color:{MUTED};font-weight:700;">flat this week</span>' if not won_d
               else f'<span style="color:{UP if won_d > 0 else DOWN};font-weight:700;">'
                    f'{"+" if won_d > 0 else ""}{won_d} this week</span>')
    top_strip = f"""
    <table style="width:100%;border-collapse:collapse;background:#fafbfc;border:1px solid {BORDER};
      border-radius:6px;margin-bottom:18px;">
      <tr>
        {strip_box("WINS TO DATE", fmt(won_today), won_sub)}
        {strip_box("7-DAY LEADS ENGAGED", fmt(le_roll7), chip(le_roll7_chg))}
        {strip_box("DAILY LEADS ENGAGED", fmt(le_today), chip(le_daily_chg))}
      </tr>
    </table>"""

    roll7_dates = ((d0 - datetime.timedelta(days=6)).strftime("%b %d"), d0.strftime("%b %d"))
    prev7_dates = ((d0 - datetime.timedelta(days=13)).strftime("%b %d"), (d0 - datetime.timedelta(days=7)).strftime("%b %d"))
    today_date = d0.strftime("%b %d, %Y")
    yest_date = (d0 - datetime.timedelta(days=1)).strftime("%b %d")

    html = build_html(rows, top_strip, roll7_dates, prev7_dates, today_date, yest_date)
    plain = build_plain(rows, won_today, won_d, le_today, le_roll7, le_prev7, today_date)

    out_path = "full_funnel_dashboard.html"
    open(out_path, "w").write(html)
    print(plain)
    print(f"\nHTML written -> {out_path}")

    if SEND:
        r = gmail_sender.send(TO, f"Full HubSpot Funnel — {today_date}", plain, html=html)
        print("send result:", r)


if __name__ == "__main__":
    main()
