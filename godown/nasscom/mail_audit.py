# -*- coding: utf-8 -*-
"""Mail the filtering audit to Ishpreet, with the CSV attached.

The point of this mail is not the 13 winners — he already has those. It is the WORKING: which
rubric line rejected each of the other 187, how often each cap fired, and where a rejection is
a genuine disqualification versus a limit of what we could read off a website. He can then argue
with a specific call instead of taking the scores on trust.

Usage: python3 mail_audit.py [--send] [--to addr]
"""
import os, sys, csv, json, glob, html, collections

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HUB, "crm_mirror", "enrich"))

CSVP = os.path.join(HERE, "nasscom_200_filtering_audit.csv")
TO = "ishpreet.sood@lh2.ai"
SEND = "--send" in sys.argv
for i, a in enumerate(sys.argv):
    if a == "--to": TO = sys.argv[i+1]

rows = list(csv.DictReader(open(CSVP, encoding="utf-8-sig")))
e = html.escape
band = collections.Counter(r["band"] for r in rows)


def cat(r):
    rr = r["REJECTION REASON"]
    if not rr: return None
    if rr.startswith("NOT SCORED"): return "Website unreachable — never scored"
    if rr.startswith("CAPPED"): return "Passed on merit, then a cap disqualified it"
    if "NO ENGINEERING EVIDENCE" in rr: return "No engineering evidence at all"
    if "capped by" in rr: return "Low score AND capped"
    return "Scored below 50"


cats = collections.Counter(cat(r) for r in rows if cat(r))
caps = collections.Counter()
for r in rows:
    for c in (r["caps_applied"] or "").split(";"):
        c = c.strip().lower()
        if not c or "not applied" in c or "non-binding" in c or "not binding" in c: continue
        if "bpo" in c: caps["BPO / back-office core business → cap 20"] += 1
        elif "agency" in c or "generalist" in c: caps["Generalist agency (dev bundled with SEO/PPC/support) → cap 30"] += 1
        elif "gold" in c or "pre-2024" in c: caps["No pre-2024 software evidence → cap 45"] += 1
        elif "careers" in c: caps["No careers AND no blog AND no team page → cap 40"] += 1
        elif "template" in c or "website" in c: caps["Template / website-builder shop → −15"] += 1
        elif "tier c" in c: caps["Tier C withheld — no Tier A/B corroboration"] += 1
        elif "training" in c or "education" in c: caps["Training / education core business → cap 30"] += 1
        else: caps[c[:60]] += 1

tiers = []
for lbl, key in (("GOLD — shipped software pre-2024", "GOLD_pre2024_pts"),
                 ("Tier A — verifiable (repo / OSS / eng blog)", "TierA_pts"),
                 ("Tier B — process proxies (code review, CI/CD, QA, certs)", "TierB_pts"),
                 ("Tier C — positioning (needs A/B corroboration)", "TierC_pts")):
    got = sum(1 for r in rows if r[key] not in ("", "0"))
    tiers.append((lbl, got))

top = [r for r in rows if r["band"] == "Priority"]
capped_pass = [r for r in rows if r["band"] == "Skip" and r["REJECTION REASON"].startswith("CAPPED")]

rowhtml = "".join(
    f'<tr><td style="padding:6px 8px;border-bottom:1px solid #eee">{e(r["name"][:44])}</td>'
    f'<td style="padding:6px 8px;border-bottom:1px solid #eee;text-align:center">{e(r["raw_before_caps"])}</td>'
    f'<td style="padding:6px 8px;border-bottom:1px solid #eee;text-align:center"><b>{e(r["score"])}</b></td>'
    f'<td style="padding:6px 8px;border-bottom:1px solid #eee;font-size:12px;color:#a00">{e(r["caps_applied"][:80])}</td></tr>'
    for r in capped_pass)

HTML = f"""<div style="font-family:-apple-system,Segoe UI,Arial,sans-serif;max-width:1000px;color:#222">
<h2 style="margin-bottom:2px">NASSCOM — how the 200 were filtered</h2>
<p style="color:#666;margin-top:2px">Full working attached. Scored against filterInstructions.md: Tier GOLD (pre-2024) + Tier A/B/C, then Step 3 caps.</p>

<table style="border-collapse:collapse;font-size:15px;margin:14px 0">
<tr><td style="padding:5px 16px 5px 0">Priority (≥70)</td><td style="padding:5px 0"><b>{band['Priority']}</b></td></tr>
<tr><td style="padding:5px 16px 5px 0">Secondary (50–69)</td><td style="padding:5px 0"><b>{band['Secondary']}</b></td></tr>
<tr><td style="padding:5px 16px 5px 0">Skip (&lt;50)</td><td style="padding:5px 0"><b>{band['Skip']}</b></td></tr>
</table>

<h3 style="margin-bottom:4px">Why the 187 were rejected</h3>
<table style="border-collapse:collapse;width:100%;font-size:14px">
<tr style="background:#f5f5f5;text-align:left"><th style="padding:8px">Reason</th><th style="padding:8px;text-align:center">Firms</th></tr>
{''.join(f'<tr><td style="padding:7px 8px;border-bottom:1px solid #eee">{e(k)}</td><td style="padding:7px 8px;border-bottom:1px solid #eee;text-align:center"><b>{v}</b></td></tr>' for k,v in cats.most_common())}
</table>

<h3 style="margin-bottom:4px;margin-top:22px">Which caps actually fired</h3>
<table style="border-collapse:collapse;width:100%;font-size:14px">
<tr style="background:#f5f5f5;text-align:left"><th style="padding:8px">Cap</th><th style="padding:8px;text-align:center">Times</th></tr>
{''.join(f'<tr><td style="padding:7px 8px;border-bottom:1px solid #eee">{e(k)}</td><td style="padding:7px 8px;border-bottom:1px solid #eee;text-align:center"><b>{v}</b></td></tr>' for k,v in caps.most_common(9))}
</table>

<h3 style="margin-bottom:4px;margin-top:22px">How many earned each tier</h3>
<ul style="color:#444;line-height:1.7">
{''.join(f'<li>{e(l)} — <b>{n}</b> of 200</li>' for l,n in tiers)}
</ul>
<p style="color:#666">Tier A is nearly absent: only <b>4</b> firms had a public repo at all, and just <b>2</b> had merged PRs from multiple humans. That is why almost every verdict is <i>Inferred</i> rather than <i>Verified</i>, and why careers-page language ends up carrying most of the scoring.</p>

{f'''<h3 style="margin-bottom:4px;margin-top:22px">Scored ≥50 on merit, then a cap disqualified them ({len(capped_pass)})</h3>
<p style="color:#666;margin-top:0">Worth a look — the engineering evidence was real, but something structural disqualified them.</p>
<table style="border-collapse:collapse;width:100%;font-size:14px">
<tr style="background:#f5f5f5;text-align:left"><th style="padding:8px">Company</th><th style="padding:8px;text-align:center">Raw</th><th style="padding:8px;text-align:center">Final</th><th style="padding:8px">Cap that bit</th></tr>
{rowhtml}</table>''' if capped_pass else ''}

<h3 style="margin-bottom:4px;margin-top:22px">Two honest caveats</h3>
<ul style="color:#444;line-height:1.7">
  <li><b>34 firms were never scored</b> — their website would not load. That is a limit of the crawl, not a judgement on them.</li>
  <li><b>This 200 was a random slice of the raw directory</b>, taken before any software-dev or headcount filtering. A large share were never targets — JLL, Kenvue, Franklin Templeton, Maersk, Rolls-Royce, Crane, Swiggy. On firms already filtered for size, the pass rate roughly doubles (22% vs 12%).</li>
</ul>

<p style="color:#999;font-size:12px;margin-top:26px">Attached: nasscom_200_filtering_audit.csv — one row per firm with tier-by-tier points, raw score before caps, which cap bit, pages we could and could not read, repo evidence and the rejection reason.</p>
</div>"""

TEXT = (f"NASSCOM — how the 200 were filtered\n\nPriority {band['Priority']} | Secondary {band['Secondary']} | Skip {band['Skip']}\n\n"
        + "\n".join(f"{k}: {v}" for k, v in cats.most_common())
        + "\n\nFull working in the attached CSV.")

subj = f"NASSCOM filtering audit — {band['Priority']} priority, {band['Secondary']} secondary, {band['Skip']} rejected"
print(f"to      : {TO}\nsubject : {subj}")
print(f"rows    : {len(rows)} | capped-despite-passing: {len(capped_pass)}")
if not SEND:
    open(os.path.join(HERE, "audit_mail.html"), "w", encoding="utf-8").write(HTML)
    print("\npreview -> audit_mail.html; re-run with --send")
else:
    import gmail_sender
    data = open(CSVP, "rb").read()
    t, detail = gmail_sender.send(TO, subj, TEXT,
                                  attachments=[("nasscom_200_filtering_audit.csv", data, "text/csv")],
                                  html=HTML)
    print(f"\nsent to {TO} via [{t}] {detail}")
