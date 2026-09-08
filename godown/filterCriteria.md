LH2 Data Labs — Startup Pre-Qualification Scorecard
Codebase Sourcing — India, Tier 1 (Dead VC-Funded Startups)
Why This Exists
We&#39;re rejecting too many leads after a Discovery call has already been booked and a founder has already engaged —
that&#39;s expensive, and it&#39;s the wrong place to filter. This scorecard moves the filtering earlier: score a lead using only
information available before any outreach happens, and route based on the score. Nothing here replaces the
Discovery call&#39;s own qualification questions — it exists so we stop spending Discovery calls and script runs on leads
that were always going to fail the LOC/PR gate.
The math that makes this necessary: at a 100M LOC/week target, single IT-services projects (100-500K LOC each)
would require 300+ closed deals a week — not achievable. Dead VC-funded startups (8-30M LOC each) need
roughly 8 closed deals a week — achievable, but only if we stop wasting calls on the ones that were never going to
qualify.
The Scorecard
Score every lead on these six criteria before a GTM Analyst makes contact. All six should be answerable from public
sources — Tracxn/Crunchbase, MCA filings, LinkedIn, GitHub — without ever speaking to the founder.
Criterion Bands Points Source
Total Funding Raised Bootstrapped / $0 → 0 pts
&lt;$500K (angel/pre-seed) → 2 pts
$500K–$2M (seed) → 5 pts
$2M–$10M (Series A) → 10 pts
$10M+ (Series B+) → 12 pts

0–12 Tracxn /
Crunchbase

Years Operated Before
Shutdown

&lt;1.5 years → 0 pts
1.5–3 years → 4 pts
3–5 years → 9 pts
5+ years → 12 pts

0–12 Tracxn / MCA
incorp date

Peak Engineering
Headcount

1–4 engineers → 1 pt
5–14 engineers → 6 pts
15–30 engineers → 10 pts
30+ engineers → 12 pts

1–12 LinkedIn alumni
search
(&quot;worked at X&quot;
+
SDE/Backend/
Engineer titles)

Sector / Product Type Backend-heavy (fintech infra, logistics, healthtech
platforms, B2B SaaS, marketplaces w/ real matching
engines) → 10 pts
Mixed (consumer app w/ meaningful backend — food
delivery, ride-hailing) → 6 pts
Frontend-thin (D2C brand site, simple booking/listing,
agency-style marketing site) → 0 pts

0–10 Company
website /
Tracxn sector
tag

Code Location &amp; Git
History

GitHub/GitLab org, full commit history intact → 15 pts
GitHub org exists, history looks shallow/squashed → 5
pts
Drive/zip only, git history unknown → 3 pts (flag: verify
.git folder before Discovery call)
No known code location yet → 0 pts, unscored

0–15 GitHub org
search by
company
name; founder
LinkedIn &quot;open
source&quot;
mentions

Legal Status
Confirmation

MCA shows Struck Off / Under Liquidation / Dissolved
→ 5 pts (confirms genuinely dead, not just quiet)
Not yet checked → 0 pts (neutral, not a penalty)

0–5 MCA (Ministry
of Corporate
Affairs) portal
Maximum possible score: 66 points. Code Location carries the heaviest single weight (15 pts) deliberately — it&#39;s
the closest pre-call proxy we have for &quot;will this actually produce a healthy LOC/PR ratio,&quot; and it directly determines
whether the eventual evaluation script can even run properly. A codebase with no git history can still be sized for

LOC, but PRs, commits, and contributor signals are all unavailable — that&#39;s a re-extraction problem, not a rejection,
but it stalls the deal until resolved.
Go / No-Go Routing
Score Routing Why
45+ Fast-track straight to Discovery call High confidence across funding, maturity, and code
signals — skip the cold-call gate question, go straight
to Deal Lead.

25–44 GTM cold-call first, PR-process gate

question mandatory

Promising but unconfirmed on 1-2 criteria. The
analyst must ask “did your team use pull requests
and code review, or was this mostly direct commits?”
before booking Discovery — a bad answer here is a
same-call disqualification.

&lt;25 Don&#39;t pursue Deprioritize. Revisit only if a specific criterion was
simply unscored (e.g. code location unknown) rather
than genuinely weak — don&#39;t let &quot;unscored&quot; and
&quot;disqualifying&quot; collapse into the same bucket.

Sourcing Channels By Criterion
● Funding + years operated: Tracxn, Crunchbase, PrivateCircle, VCCEdge — filter by status =
inactive/acquired/dormant, funding stage ≥ seed, India geography.
● Legal status confirmation: MCA (Ministry of Corporate Affairs) public filings — “struck off” or “under liquidation”
status is a hard, verifiable, India-specific signal that&#39;s genuinely underused for this kind of sourcing.
● Peak headcount: LinkedIn people-search filtered to “past” employees of the target company with
Engineer/SDE/Backend/Developer titles — gives a real headcount proxy without contacting anyone.
● Sector coverage archives: Inc42, YourStory, Entrackr shutdown-coverage — useful both for sourcing new names
and for corroborating funding/timeline details Tracxn doesn&#39;t always have.
● Code location: search GitHub for the company/product name directly, check founder LinkedIn profiles and old
engineering blog posts for repo links, and check the company&#39;s old careers page (via Wayback Machine if the site
is down) for “work with modern tools like GitHub, CI/CD” type language — a weak but real pre-call signal.
Reference: Addressable Market (India, Tier 1)
Tracxn tracks 34,700 total funded Indian startups. Applying a reasoned funnel — ~65% eventual shutdown rate,
~35% genuinely backend-heavy, ~30% matured (3+ years, 15+ peak engineers) — puts the qualifying universe at
roughly 1,000–4,700 companies, central estimate ~2,400. This is a model, not a measurement; refine it once direct
Tracxn/MCA filtering is possible. At an 8/week Tier-1 sourcing pace, this gives approximately 2.3–11.3 years of
runway (~5.7 years at the central estimate) before the India-only, VC-funded-and-dead segment is exhausted —
worth planning Tier-2 (agency bundles) and/or geographic expansion around that horizon, not after hitting it.