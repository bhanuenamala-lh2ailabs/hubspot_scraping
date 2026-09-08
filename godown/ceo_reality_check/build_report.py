# -*- coding: utf-8 -*-
"""Builds the CEO reality-check report (HTML)."""
import csv, os, json, collections, statistics as st
HERE=os.path.dirname(os.path.abspath(__file__))
D=list(csv.DictReader(open(os.path.join(HERE,"DEALS_FULL.csv"),encoding="utf-8")))
def n(v):
    try: return float(v)
    except: return None
won=[d for d in D if d["stage_label"]=="Closed/Won"]
t1w=[d for d in won if d["tier1_ratio_ok"]=="True"]
live=[d for d in D if not d["stage_label"].startswith("Dead/") and d["stage_label"] not in ("Closed/Won","Call Attempted (retired)")]
resolved=len(D)-len(live)
WON_LOC=sum(n(d["loc"]) or 0 for d in won); T1_LOC=sum(n(d["loc"]) or 0 for d in t1w)
CO_T1=6; CO_T1_MEAN=6977196; CO_T1_MED=6258916
RATE_CO=CO_T1/len(D); RATE_RES=CO_T1/resolved
UNIV_LO,UNIV_HI=9000,15000; UNIV=12000
CEIL_LO=UNIV*RATE_CO*CO_T1_MEAN; CEIL_HI=UNIV*RATE_RES*CO_T1_MEAN
PER_LEAD=RATE_CO*CO_T1_MEAN
T=f"""<title>LH2 — The 1 Billion LoC Reality Check</title>
<style>
:root{{--bg:#ffffff;--fg:#0f172a;--mut:#64748b;--line:#e2e8f0;--card:#f8fafc;--acc:#0e7490;--red:#b91c1c;--grn:#15803d;--amb:#b45309;--chip:#f1f5f9}}
:root:not([data-theme="light"]){{@media (prefers-color-scheme:dark){{--bg:#0b1120;--fg:#e2e8f0;--mut:#94a3b8;--line:#1e293b;--card:#111827;--acc:#22d3ee;--red:#f87171;--grn:#4ade80;--amb:#fbbf24;--chip:#1e293b}}}}
:root[data-theme="dark"]{{--bg:#0b1120;--fg:#e2e8f0;--mut:#94a3b8;--line:#1e293b;--card:#111827;--acc:#22d3ee;--red:#f87171;--grn:#4ade80;--amb:#fbbf24;--chip:#1e293b}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 -apple-system,'Segoe UI',Roboto,system-ui,sans-serif}}
.w{{max-width:920px;margin:0 auto;padding:34px 22px 80px}}
h1{{font-size:34px;line-height:1.15;margin:0 0 6px;letter-spacing:-.5px}}
.sub{{color:var(--mut);font-size:15px;margin:0 0 8px}}
h2{{font-size:23px;margin:44px 0 10px;letter-spacing:-.3px;padding-bottom:7px;border-bottom:2px solid var(--line)}}
h3{{font-size:16px;margin:26px 0 8px;color:var(--acc);text-transform:uppercase;letter-spacing:.06em}}
p{{margin:11px 0}}
.hero{{background:linear-gradient(135deg,#0e7490,#155e75);color:#fff;border-radius:16px;padding:26px 28px;margin:22px 0 8px}}
.hero .k{{font-size:13px;text-transform:uppercase;letter-spacing:.1em;opacity:.85}}
.hero .v{{font-size:44px;font-weight:800;line-height:1.1;margin:6px 0}}
.hero .d{{font-size:15px;opacity:.95}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin:16px 0}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}}
.card .k{{font-size:11.5px;color:var(--mut);text-transform:uppercase;letter-spacing:.06em}}
.card .v{{font-size:25px;font-weight:700;margin:3px 0;letter-spacing:-.5px}}
.card .d{{font-size:12.5px;color:var(--mut)}}
.tw{{overflow-x:auto;margin:14px 0}}
table{{border-collapse:collapse;width:100%;font-size:13.5px;min-width:520px}}
th{{background:var(--chip);text-align:left;padding:9px 11px;border:1px solid var(--line);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--mut)}}
td{{padding:8px 11px;border:1px solid var(--line)}}
td.n,th.n{{text-align:right;font-variant-numeric:tabular-nums}}
.red{{color:var(--red);font-weight:600}} .grn{{color:var(--grn);font-weight:600}} .amb{{color:var(--amb);font-weight:600}}
.box{{border-left:4px solid var(--acc);background:var(--card);padding:13px 16px;border-radius:0 10px 10px 0;margin:16px 0}}
.box.r{{border-color:var(--red)}} .box.g{{border-color:var(--grn)}} .box.a{{border-color:var(--amb)}}
.big{{font-size:19px;font-weight:700}}
ul{{margin:9px 0;padding-left:22px}} li{{margin:5px 0}}
.foot{{margin-top:50px;padding-top:16px;border-top:1px solid var(--line);color:var(--mut);font-size:12.5px}}
code{{background:var(--chip);padding:1px 6px;border-radius:5px;font-size:12.5px}}
.eq{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:13px 16px;font-family:ui-monospace,Menlo,monospace;font-size:13px;margin:12px 0;overflow-x:auto}}
</style>
<div class="w">
<h1>The 1 Billion LoC Reality Check</h1>
<p class="sub">Every deal, every stage move, every note in the LH2 CRM — 2,141 deals · 4,921 stage transitions · 1,981 notes · 34 days of operating history · generated 17 Aug 2026</p>

<div class="hero">
  <div class="k">The one number</div>
  <div class="v">235M – 540M</div>
  <div class="d">The <b>maximum LoC extractable from the entire known addressable universe</b> (~12,000 companies) at our observed conversion. That is <b>24–54% of 1 Billion</b>. We would run out of companies to call long before we ran out of time.</div>
</div>

<div class="box r"><b>Verdict.</b> <span class="big">1 Billion LoC is not reachable through the current funnel.</span> Not because the team is slow — the team is performing. Because the <b>universe is too small</b>. At the observed rate we bank <b>{PER_LEAD:,.0f} LoC per lead worked</b>; 1Bn would require <b>~51,000 companies</b> to work through, and the entire known India IT-services + dead-startup universe is <b>9,000–15,000</b>. Speed changes <i>when</i> we stop, not <i>where</i>.</div>

<h2>1. What we actually know — the whole evidence base</h2>
<p>The headline caveat first, stated plainly: <b>the entire LoC record is 16 deals.</b> Of 2,141 deals in the CRM, only 16 have ever carried a LoC number, and only 11 are Closed/Won — representing <b>8 distinct companies</b> (Backspace appears as 3 deals, Serpent as 2). The CRM is <b>34 days old</b>. Every projection below rests on that base, and its uncertainty is wide.</p>
<div class="grid">
  <div class="card"><div class="k">Deals in CRM</div><div class="v">2,141</div><div class="d">34 days, 2 pipelines</div></div>
  <div class="card"><div class="k">LoC ever recorded</div><div class="v">96.3M</div><div class="d">across just 16 deals</div></div>
  <div class="card"><div class="k">Closed/Won LoC</div><div class="v">70.1M</div><div class="d">11 deals, 8 companies</div></div>
  <div class="card"><div class="k">Tier-1 LoC won</div><div class="v">41.9M</div><div class="d">9 deals after ratio gate</div></div>
  <div class="card"><div class="k">Tier-1 win rate</div><div class="v">0.42%</div><div class="d">9 of 2,141 leads</div></div>
  <div class="card"><div class="k">Quality haircut</div><div class="v">40%</div><div class="d">of won LoC fails the ratio bar</div></div>
</div>

<h3>The Tier-1 gate costs us 40% of everything we harvest</h3>
<p>Applying the CEO's own quality bar — <b>LoC/PR between 300 and 2,000</b> — to the won book removes the two largest deals:</p>
<div class="tw"><table>
<tr><th>Deal</th><th class="n">LoC</th><th class="n">PRs</th><th class="n">LoC/PR</th><th>Tier-1</th><th>Source</th></tr>
<tr><td>FabLead</td><td class="n">20,093,942</td><td class="n">7,495</td><td class="n">2,681</td><td class="red">FAIL — too sparse</td><td>Scraping Algo</td></tr>
<tr><td>Deliqt</td><td class="n">17,525,955</td><td class="n">13,793</td><td class="n">1,271</td><td class="grn">PASS</td><td>LinkedIn Campaign</td></tr>
<tr><td>Investmint</td><td class="n">8,155,217</td><td class="n">3,529</td><td class="n">2,311</td><td class="red">FAIL — too sparse</td><td>Tracxn</td></tr>
<tr><td>Serpent Consulting (2 deals)</td><td class="n">7,744,647</td><td class="n">11,375</td><td class="n">681</td><td class="grn">PASS</td><td>Scraping Algo</td></tr>
<tr><td>Backspace Technologies (3 deals)</td><td class="n">8,956,461</td><td class="n">15,763</td><td class="n">568</td><td class="grn">PASS</td><td>Scraping Algo</td></tr>
<tr><td>Gloify</td><td class="n">4,773,185</td><td class="n">6,642</td><td class="n">719</td><td class="grn">PASS</td><td>Scraping Algo</td></tr>
<tr><td>Scaletech</td><td class="n">1,539,267</td><td class="n">2,288</td><td class="n">673</td><td class="grn">PASS</td><td>Scraping Algo</td></tr>
<tr><td>Baaz</td><td class="n">1,323,660</td><td class="n">1,911</td><td class="n">693</td><td class="grn">PASS</td><td>Tracxn</td></tr>
<tr><td><b>Total won</b></td><td class="n"><b>70,112,334</b></td><td class="n"></td><td class="n"></td><td><b>41.9M passes</b></td><td></td></tr>
</table></div>
<p><b>28.25M LoC — 40% of everything won — fails the ratio bar.</b> If the CEO's Tier-1 definition is the real standard, our true banked total is 41.9M, not 70.1M. Any target must be stated in the same currency, or we are measuring two different things.</p>

<h2>2. The realistic weekly rate</h2>
<p>Three independent readings of the same 34 days:</p>
<div class="tw"><table>
<tr><th>Week</th><th class="n">New leads</th><th class="n">Connects</th><th class="n">GMeets</th><th class="n">Scripts</th><th class="n">Wins</th><th class="n">Raw LoC</th><th class="n">Tier-1 LoC</th></tr>
<tr><td>13 Jul</td><td class="n">111</td><td class="n">1</td><td class="n">0</td><td class="n">0</td><td class="n">0</td><td class="n">0</td><td class="n">0</td></tr>
<tr><td>20 Jul</td><td class="n">162</td><td class="n">37</td><td class="n">7</td><td class="n">1</td><td class="n">0</td><td class="n">0</td><td class="n">0</td></tr>
<tr><td>27 Jul</td><td class="n">409</td><td class="n">55</td><td class="n">3</td><td class="n">11</td><td class="n">3</td><td class="n">14,743,886</td><td class="n">6,588,669</td></tr>
<tr><td>3 Aug</td><td class="n">497</td><td class="n">118</td><td class="n">24</td><td class="n">27</td><td class="n">6</td><td class="n">35,474,701</td><td class="n">15,380,759</td></tr>
<tr><td>10 Aug</td><td class="n">721</td><td class="n">141</td><td class="n">11</td><td class="n">16</td><td class="n">2</td><td class="n">19,893,747</td><td class="n">19,893,747</td></tr>
<tr><td>17 Aug <span class="amb">(current)</span></td><td class="n">241</td><td class="n">29</td><td class="n">5</td><td class="n">5</td><td class="n">0</td><td class="n red">0</td><td class="n red">0</td></tr>
</table></div>
<div class="grid">
  <div class="card"><div class="k">Tier-1 over CRM life</div><div class="v">8.6M</div><div class="d">41.9M ÷ 4.86 weeks</div></div>
  <div class="card"><div class="k">Tier-1, closing weeks only</div><div class="v">14.0M</div><div class="d">mean of the 3 weeks with closes</div></div>
  <div class="card"><div class="k">Best single week</div><div class="v">19.9M</div><div class="d">week of 10 Aug</div></div>
</div>
<div class="box a"><b>Warning signal.</b> Zero closes since 10 Aug, and new-lead creation fell from 721 to 241 this week. Three weeks of closes is not a trend — it is a burst. Any weekly rate quoted from it carries a wide error bar.</div>

<h3>The arithmetic that sets the target</h3>
<div class="eq">weekly tier-1 LoC  =  leads worked/week  ×  tier-1 win rate  ×  LoC per tier-1 win<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;=  L  ×  0.28%  ×  6,977,196  =  L  ×  19,553 LoC per lead</div>
<div class="tw"><table>
<tr><th class="n">Leads worked/wk</th><th class="n">Callers needed</th><th class="n">Tier-1 LoC/week</th><th>Feasibility</th></tr>
<tr><td class="n">357 <i>(today)</i></td><td class="n">2</td><td class="n">7.0M</td><td>current supply</td></tr>
<tr><td class="n">500</td><td class="n">2</td><td class="n">9.8M</td><td class="grn">comfortable</td></tr>
<tr><td class="n">656</td><td class="n">2</td><td class="n">12.8M</td><td class="grn">within 2-caller ceiling (710)</td></tr>
<tr><td class="n">710</td><td class="n">2</td><td class="n">13.9M</td><td class="amb">2 callers at absolute max</td></tr>
<tr><td class="n">874</td><td class="n">3</td><td class="n">17.1M</td><td class="amb">needs a 3rd caller</td></tr>
<tr><td class="n">1,000</td><td class="n">3</td><td class="n">19.6M</td><td class="amb">needs 3 callers + supply</td></tr>
<tr><td class="n">1,500</td><td class="n">4–5</td><td class="n">29.3M</td><td class="red">burns universe in 8 weeks</td></tr>
</table></div>

<div class="box g"><b>The recommended target: 12–17M tier-1 LoC per week, planned at 15M.</b><br>
Measured capacity is the binding pair of walls. The two callers touch <b>49 deals/person/day on average, 71 at their best</b> — a hard ceiling of about <b>710 leads/week</b>. That ceiling produces <b>~13.9M/week</b>. Reaching <b>20M needs 874 leads/week and a third caller</b>. So the honest band is:
<ul><li><b>15M/week is achievable with today's team</b>, running near full stretch (656 leads/week).</li>
<li><b>20M/week is achievable only with a 3rd caller</b> and lead supply lifted from 357 to ~875/week.</li>
<li><b>Above 20M/week is not a staffing problem — it is a supply problem</b>, and it accelerates universe exhaustion.</li></ul>
<b>Your instinct of 15–20M/week is exactly right</b> — it is the band bounded below by lead supply and above by calling capacity.</div>

<h2>3. Why 1 Billion cannot be reached</h2>
<p>This is the part that matters most, and it is not about speed.</p>
<div class="eq">1,000,000,000 ÷ 6,977,196 LoC per winning company  =  <b>143 winning companies</b><br>
143 ÷ 0.28% company win rate  =  <b>51,143 companies that must be worked</b><br>
Known addressable universe  =  <b>9,000 – 15,000 companies</b><br>
<span style="color:#b91c1c">Shortfall: we need 3.5× to 5.7× more universe than exists.</span></div>
<div class="tw"><table>
<tr><th>Source pool</th><th class="n">Companies</th><th>Status</th></tr>
<tr><td>Prequal survivors (GoodFirms + NASSCOM, qualified)</td><td class="n">5,629</td><td>the core IT-services universe</td></tr>
<tr><td>Prequal reserve</td><td class="n">3,092</td><td>lower-quality tail</td></tr>
<tr><td>NASSCOM members</td><td class="n">2,775</td><td>heavy overlap with above</td></tr>
<tr><td>Dead startups with codebases</td><td class="n">3,274</td><td>from 11,264 raw shutdowns</td></tr>
<tr><td>Whales (large-codebase targets)</td><td class="n">30</td><td>highest LoC per win</td></tr>
<tr><td><b>De-duplicated realistic universe</b></td><td class="n"><b>9,000–15,000</b></td><td><b>the hard ceiling on the funnel</b></td></tr>
</table></div>
<div class="box r"><b>The exhaustion result.</b> Working <b>100% of a 12,000-company universe</b> with perfect execution at observed conversion yields <b>{CEIL_LO:,.0f} LoC</b> (raw basis) to <b>{CEIL_HI:,.0f} LoC</b> (resolved basis) — <b>{100*CEIL_LO/1e9:.0f}–{100*CEIL_HI/1e9:.0f}% of 1 Billion</b>. And going faster does not help: at 1,500 leads/week the universe is gone in <b>8 weeks</b>; at 357/week it lasts 34 weeks. <b>Same ceiling either way — speed changes when we stop, not where.</b></div>
<div class="tw"><table>
<tr><th>Scenario</th><th class="n">Tier-1 LoC/wk</th><th class="n">Weeks to 1Bn<br><i>if universe were infinite</i></th><th class="n">Years</th><th>Reality</th></tr>
<tr><td>Current run-rate</td><td class="n">8.6M</td><td class="n">116</td><td class="n">2.2</td><td class="red">universe gone at 24–54%</td></tr>
<tr><td>Closing-weeks mean</td><td class="n">14.0M</td><td class="n">72</td><td class="n">1.4</td><td class="red">universe gone at 24–54%</td></tr>
<tr><td><b>Recommended target</b></td><td class="n"><b>15.0M</b></td><td class="n">67</td><td class="n">1.3</td><td class="red">universe gone at 24–54%</td></tr>
<tr><td>Stretch (3rd caller)</td><td class="n">20.0M</td><td class="n">50</td><td class="n">1.0</td><td class="red">universe gone sooner</td></tr>
<tr><td>CEO implied pace</td><td class="n">50.0M</td><td class="n">20</td><td class="n">0.4</td><td class="red">not physically supported</td></tr>
</table></div>

<h2>4. What would actually have to change</h2>
<p>1Bn is reachable only if one of these four moves by a factor of 2–5×. Ranked by leverage:</p>
<div class="tw"><table>
<tr><th>Lever</th><th>Today</th><th>Needed for 1Bn</th><th class="n">Multiple</th><th>Assessment</th></tr>
<tr><td><b>Expand the universe</b></td><td>9–15k Indian IT-services + dead startups</td><td>50,000+ companies</td><td class="n">3.5–5.7×</td><td class="grn">Most viable — go beyond India, beyond IT-services, or into SE Asia / Eastern Europe</td></tr>
<tr><td><b>LoC per win</b></td><td>6.98M mean per company</td><td>~11.6M–70M</td><td class="n">2–10×</td><td class="grn">Viable via whale-only targeting — the 30 whales exist and Deliqt alone was 17.5M</td></tr>
<tr><td><b>Win rate</b></td><td>0.28% company-level</td><td>1.3%+</td><td class="n">2–5×</td><td class="amb">Hard — needs a step-change in qualification, not effort</td></tr>
<tr><td><b>Calling capacity</b></td><td>2 callers, 710 leads/wk max</td><td>10+ callers</td><td class="n">5×</td><td class="red">Does not help — supply and universe bind first</td></tr>
</table></div>

<h2>5. Where LoC is leaking right now</h2>
<div class="grid">
  <div class="card"><div class="k">Lost at pricing</div><div class="v red">13.6M</div><div class="d">IT-Antino 12.8M + Nickelfox 0.8M — both Tier-1</div></div>
  <div class="card"><div class="k">In flight, contract signed</div><div class="v grn">12.3M</div><div class="d">WebCodeGenie 12.06M + Humalect 0.2M</div></div>
  <div class="card"><div class="k">Leads on zero-win sources</div><div class="v amb">684</div><div class="d">32% of the book, no wins yet</div></div>
</div>
<div class="box r"><b>The single most expensive mistake so far:</b> <b>IT-Antino — 12,828,951 Tier-1 LoC — was lost at <code>Dead/Negotiation/Pricing</code>.</b> That one deal is worth <b>almost a full week of the 15M target</b>. Together with Nickelfox, <b>13.6M Tier-1 LoC has been lost purely on price</b>, after all the acquisition cost was already spent. Recovering deals at negotiation is the highest-ROI action available — the lead is already qualified, the script already run.</div>

<h3>Source efficiency — what actually produces LoC</h3>
<div class="tw"><table>
<tr><th>Lead source</th><th class="n">Leads</th><th class="n">Script+</th><th class="n">Wins</th><th class="n">Tier-1 LoC</th><th class="n">Tier-1 LoC per 1,000 leads</th></tr>
<tr><td>LinkedIn Campaign (IT Services)</td><td class="n">355</td><td class="n">9</td><td class="n">1</td><td class="n">17,525,955</td><td class="n grn">49,368,887</td></tr>
<tr><td>Scraping Algo (IT services)</td><td class="n">920</td><td class="n">26</td><td class="n">7</td><td class="n">20,645,768</td><td class="n grn">22,441,052</td></tr>
<tr><td>Tracxn Sheet (Startups)</td><td class="n">175</td><td class="n">15</td><td class="n">2</td><td class="n">1,323,660</td><td class="n">7,563,771</td></tr>
<tr><td>NASSCOM (IT Services)</td><td class="n">224</td><td class="n">1</td><td class="n">0</td><td class="n">0</td><td class="n red">0</td></tr>
<tr><td>Outflo Outreach (Startups)</td><td class="n">177</td><td class="n">15</td><td class="n">0</td><td class="n">0</td><td class="n red">0</td></tr>
<tr><td>Founder Search (IT Services)</td><td class="n">173</td><td class="n">0</td><td class="n">0</td><td class="n">0</td><td class="n red">0</td></tr>
<tr><td>Others (Romania, Private Tracker, Scraped)</td><td class="n">110</td><td class="n">4</td><td class="n">0</td><td class="n">0</td><td class="n red">0</td></tr>
</table></div>
<p><b>Read this with care.</b> LinkedIn Campaign ranks first on a <b>single win</b> (Deliqt). With 11 wins in total, source-level differences are mostly small-sample noise — the one safe conclusion is that <b>Scraping Algo (IT services) is the proven workhorse</b> (7 of 11 wins, 920 leads) and that <b>684 leads on Founder Search / NASSCOM / Outflo have yet to produce a single win.</b></p>

<h2>6. What to do</h2>
<div class="box g"><b>1. Re-baseline the target in Tier-1 currency.</b> Adopt <b>15M Tier-1 LoC/week</b> as the plan and <b>20M as the stretch</b>. State whether "1 Billion" means raw or Tier-1 — it is a 40% difference, and today we are measuring two different things.</div>
<div class="box"><b>2. Reopen the negotiation losses.</b> 13.6M Tier-1 LoC (IT-Antino, Nickelfox) died on price. That is ~1 week of target, already fully qualified. Re-approach with revised commercials before sourcing a single new lead.</div>
<div class="box"><b>3. Go whale-only on sourcing.</b> LoC per win is the highest-leverage variable and the only one that scales without more people. 30 whales are already identified; Deliqt alone (17.5M) equals 13 median wins. Prioritise codebase size in qualification, not just contactability.</div>
<div class="box"><b>4. Fix the supply gap before adding callers.</b> Lead supply (357/week) — not calling capacity (710/week) — is today's binding constraint. Get to ~656/week before hiring a third caller.</div>
<div class="box"><b>5. Cut or fix the zero-yield sources.</b> 684 leads on Founder Search, NASSCOM and Outflo have produced no wins. Either fix qualification or redeploy that effort to Scraping Algo.</div>
<div class="box a"><b>6. Decide the universe question at board level.</b> This is the only path to 1Bn. Expanding beyond Indian IT-services — geographically, or into adjacent categories — is a strategy decision, not an execution one. Without it, the funnel tops out at 235–540M.</div>

<h2>7. Honest caveats</h2>
<ul>
<li><b>n = 9 Tier-1 wins, 8 distinct companies, 34 days.</b> Every rate here has a wide confidence interval. The weekly target should be read as a <b>band (12–17M)</b>, not a point estimate.</li>
<li><b>One outlier dominates.</b> Deliqt (17.5M) is 42% of all Tier-1 LoC won. Remove it and the mean per-deal figure falls from 4.65M to 3.04M — a third of the model's value rests on one deal.</li>
<li><b>Only 16 of 2,141 deals carry a LoC value.</b> If LoC is being under-recorded on won deals, the per-win figure is understated and the picture improves. This is worth auditing directly.</li>
<li><b>The 11 wins are 8 companies.</b> Splitting a harvest into 3 deals (Backspace) inflates deal-level win counts. All company-level figures here correct for that; deal-level ones do not.</li>
<li><b>Zero closes in the last 7 days.</b> If that continues for another two weeks, every rate above should be revised down materially.</li>
<li><b>The universe estimate is ours, not the market's.</b> 9,000–15,000 is what our own source pools contain. A genuine market-sizing exercise could move it — that is precisely why recommendation 6 matters.</li>
</ul>

<div class="foot">Sources: HubSpot portal 246754894 — 2,141 deals with full property set, 4,921 stage transitions (human moves flagged via <code>sourceType=CRM_UI</code>), 1,981 notes, 288 tasks, 3,186 contacts, 2,635 companies. Universe pools: prequal survivors/reserve/whales, NASSCOM member list, shutdown-radar dead-company set. Tier-1 = LoC/PR ratio between 300 and 2,000. Full numeric record: <code>ANALYSIS_ALL_NUMBERS.txt</code>; complete object log: <code>EVERYTHING.jsonl</code>.</div>
</div>"""
open(os.path.join(HERE,"REALITY_CHECK.html"),"w",encoding="utf-8").write(T)
print("wrote REALITY_CHECK.html", len(T),"bytes")
print(f"ceiling raw basis   {CEIL_LO:,.0f}  ({100*CEIL_LO/1e9:.1f}% of 1Bn)")
print(f"ceiling resolved    {CEIL_HI:,.0f}  ({100*CEIL_HI/1e9:.1f}% of 1Bn)")
print(f"LoC per lead worked {PER_LEAD:,.0f}")
