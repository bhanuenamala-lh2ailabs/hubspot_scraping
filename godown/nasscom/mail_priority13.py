# -*- coding: utf-8 -*-
"""One-off: mail the 13 Priority NASSCOM firms to Ishpreet.

Deliberately a manual script, not a scheduled job. The only automated mail in this repo is the
6:30pm report; anything else runs when a human asks for it.

The mail leads with what is CHECKABLE — repo evidence, the pre-2024 proof, and where each
contact name came from — because every name here was read off the company's own leadership page
rather than bought from a data provider, and Ishpreet should be able to see the basis before he
uses one. The two known-weak rows are called out in the mail itself, not buried.

Usage: python3 mail_priority13.py [--send] [--to addr]
"""
import os, sys, json, glob, html

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HUB, "crm_mirror", "enrich"))

TO = "ishpreet.sood@lh2.ai"
SEND = "--send" in sys.argv
for i, a in enumerate(sys.argv):
    if a == "--to": TO = sys.argv[i+1]

sc = {}
for f in glob.glob(os.path.join(HERE, "score_batches", "scored_*.json")):
    for r in json.load(open(f, encoding="utf-8")): sc[r["domain"]] = r
bun = {r.get("domain"): r for r in json.load(open(os.path.join(HERE, "score_bundles.json"), encoding="utf-8"))}
fo = {}
for f in glob.glob(os.path.join(HERE, "people_batches", "found_*.json")):
    for r in json.load(open(f, encoding="utf-8")): fo[r["domain"]] = r

pri = sorted([r for r in sc.values() if r["band"] == "Priority"], key=lambda x: -x["score"])
e = html.escape

rows = []
for i, r in enumerate(pri, 1):
    d = r["domain"]; b = bun.get(d, {}); f = fo.get(d, {})
    org = (b.get("own_vcs_orgs") or [{}])[0] if b.get("own_vcs_orgs") else {}
    repo = (f'<a href="https://github.com/{e(org["org"])}">github.com/{e(org["org"])}</a><br>'
            f'<span style="color:#666">{org["merged_prs"]} merged PRs · {org["human_authors"]} humans · since {str(org.get("first_merge"))[:10]}</span>'
            ) if org.get("merged_prs") else '<span style="color:#999">—</span>'
    if f.get("person"):
        who = f'<b>{e(f["person"])}</b><br><span style="color:#666">{e(f.get("title") or "")}</span>'
        if f.get("linkedin"):
            who += f'<br><a href="{e(f["linkedin"])}">LinkedIn</a>'
        if (f.get("confidence") or "") == "low":
            who += '<br><span style="color:#b00">⚠ unconfirmed</span>'
    else:
        who = '<span style="color:#999">not on their site</span>'
    ver = ' <span style="color:#0a0;font-weight:600">✓</span>' if r["confidence"] == "Verified" else ""
    rows.append(f"""<tr>
      <td style="padding:9px 8px;border-bottom:1px solid #eee;color:#888">{i}</td>
      <td style="padding:9px 8px;border-bottom:1px solid #eee"><b>{e(r["name"])}</b>{ver}<br>
          <a href="{e(b.get('website') or '')}" style="color:#06c;font-size:12px">{e((b.get('website') or '').replace('https://','').replace('http://','')[:44])}</a>
          <span style="color:#888;font-size:12px"> · {e(b.get('city') or '')}</span></td>
      <td style="padding:9px 8px;border-bottom:1px solid #eee;text-align:center;font-size:17px"><b>{r["score"]}</b></td>
      <td style="padding:9px 8px;border-bottom:1px solid #eee;font-size:13px">{who}</td>
      <td style="padding:9px 8px;border-bottom:1px solid #eee;font-size:12px">{repo}</td>
      <td style="padding:9px 8px;border-bottom:1px solid #eee;font-size:12px;color:#555">{e((r.get("pre2024_status") or "")[:78])}</td>
    </tr>""")

nvcs = sum(1 for r in pri if (bun.get(r["domain"], {}).get("own_vcs_orgs")))
nper = sum(1 for r in pri if fo.get(r["domain"], {}).get("person"))

HTML = f"""<div style="font-family:-apple-system,Segoe UI,Arial,sans-serif;max-width:1000px;color:#222">
<h2 style="margin-bottom:4px">NASSCOM — 13 Priority firms</h2>
<p style="color:#666;margin-top:0">Scored against the IT Firm Relevancy rubric (engineering maturity + shipped software pre-2024). These are the ≥70 band out of a 200-firm sample.</p>

<table style="border-collapse:collapse;width:100%;font-size:14px">
<tr style="background:#f5f5f5;text-align:left">
  <th style="padding:8px"></th><th style="padding:8px">Company</th>
  <th style="padding:8px;text-align:center">Score</th><th style="padding:8px">Contact</th>
  <th style="padding:8px">Public repo</th><th style="padding:8px">Pre-2024 evidence</th>
</tr>
{''.join(rows)}
</table>

<p style="margin-top:22px"><b>How to read this</b></p>
<ul style="color:#444;line-height:1.65">
  <li><b>✓ = Verified</b> — a Tier A signal was actually found (public repo with merged PRs, or a real engineering blog). The rest are Inferred from careers-page and process evidence.</li>
  <li><b>Contacts came from the companies' own leadership/about pages</b>, not from a data provider. Where a LinkedIn link is shown, that URL was printed on their page.</li>
  <li><b>{nper} of 13 have a named contact; {nvcs} have a verified public repo.</b></li>
</ul>

<p style="margin-top:18px"><b>Two to treat carefully</b></p>
<ul style="color:#444;line-height:1.65">
  <li><b>Rishabh Software</b> — the contact is marked unconfirmed. Their page only said "Shah's leadership philosophy" and there is a second Shah on it. Verify before using the name.</li>
  <li><b>MCO MyCompliance</b> — Brian Fahey is the group founder, not an India MD. Same for Inadev in the sized list. Right company, possibly the wrong person to approach about the Indian entity.</li>
  <li><b>Zediant</b> — scored 80 on process evidence but markets AI-augmented delivery heavily, which is exactly what the pre-2024 gate exists to screen out. Worth a closer look than the score implies.</li>
</ul>

<p style="margin-top:18px;color:#444"><b>Not yet done:</b> none of these 13 have been headcount-checked against the 250–600 band, and none have a phone number — so nothing here can go into HubSpot yet under the +91 rule.</p>

<p style="color:#999;font-size:12px;margin-top:26px">Full scoring detail, evidence and the other 187 firms are in godown/nasscom/nasscom_200_scored.csv</p>
</div>"""

TEXT = "NASSCOM — 13 Priority firms\n\n" + "\n".join(
    f'{i}. {r["name"]} [{r["score"]}] — {(fo.get(r["domain"],{}) or {}).get("person") or "no contact found"}'
    for i, r in enumerate(pri, 1))

subj = f"NASSCOM: {len(pri)} priority firms for outreach"
print(f"to      : {TO}")
print(f"subject : {subj}")
print(f"firms   : {len(pri)} | with contact {nper} | with repo {nvcs}")
if not SEND:
    open(os.path.join(HERE, "priority13_mail.html"), "w", encoding="utf-8").write(HTML)
    print("\npreview written to priority13_mail.html — re-run with --send to mail it")
else:
    import gmail_sender
    t, detail = gmail_sender.send(TO, subj, TEXT, html=HTML)
    print(f"\nsent to {TO} via [{t}] {detail}")
