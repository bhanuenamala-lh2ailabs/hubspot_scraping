# NASSCOM — full pipeline plan

**Goal:** Indian IT firms that (a) built and sold software for clients, (b) existed well before
2024, (c) show evidence of a real pull-request / code-review workflow, (d) are not giants — each
with a named founder or CEO and a dialable +91 number.

Nothing below runs until you say go.

---

## What already exists (do not repeat)

| Asset | State |
|---|---|
| NASSCOM directory scrape | 3,487 listing rows → **2,775 unique firms** |
| Deduped vs HubSpot + tracker sheet | **2,499 net-new** |
| Website read (6 pages each) | **1,724 crawled**, ranked by engineering-signal density |
| Plausible software firms | **1,681** |
| Rubric-scored (filterInstructions) | 184 → 15 Priority, 9 Secondary |
| Revealed + pushed to HubSpot | **108** (Lamiya 72 / Yuktha 36), `lead_source = NASSCOM ( IT Services )` |
| SignalHire credits | ~2,135 left. **Search pool exhausted**, reveal pool working |

So stages 1 and 2 are largely done. The plan below closes the gaps and adds what is genuinely new.

---

## Stage 1 — Complete the scrape

**Status: probably already complete, needs one check.**

The scrape walked `?page=0..232` at 15 firms a page and pagination was verified stable
(re-fetching pages 5 and 100 returned identical members). 637 names appear more than once in
NASSCOM's own listing, which is why 3,487 rows collapse to 2,775.

**To do:** confirm there is no second listing (member categories, state chapters, a "product
companies" tab) holding firms the main directory omits. ~15 min, free.

**Risk if skipped:** we may be filtering a subset and calling it the population.

---

## Stage 2 — Do they actually build and sell software?

**Method: filterInstructionsV2, applied properly.**

V2 asks for an LLM read of homepage + `/careers` + `/about`, returning `relevance_status`,
`lead_score` 1-10 and a one-line reason. That is exactly what produced the Bangladesh CSV, and
it is a better instrument than the regex pre-sort currently ranking the 1,681.

- RELEVANT 7-10: custom software development, enterprise web/mobile, dedicated engineering
  teams, explicit CI/CD, Git, pull requests, Agile, SaaS, cloud, custom backend
- IRRELEVANT 1-4: WordPress/Wix shops, SEO/marketing agencies, BPO, design studios, dead sites

**Run over all 1,681 plausible firms.** Page text is already cached from the crawl, so this is
classification only — no re-fetching.

**Measured on the 200-firm sample:** ~72% pass this bar. Expect **~1,200 RELEVANT**.

**Cost:** ~50 agent batches. Free of SignalHire credits.

---

## Stage 3 — Pre-2024 existence, and building software back then

**Method: Wayback, already built and proven.**

Fetch a 2023 / 2022 / 2020 snapshot of each firm's own site and check whether it already
advertised software work. This is stronger than a founding-year claim: "established 2011" proves
the entity existed; a 2022 capture selling custom software proves they were *building* then.

**Measured:** 73 of the 106 pushed (69%) have verified pre-2024 software evidence; 0 red flags.
On the wider 200 sample it was 78 of 200 after repair.

**Two failure modes already fixed and worth keeping:**
- archive.org throttles hard — 5 workers max, retry with backoff, and never record a throttle as
  "never archived" (an earlier run reported 193 of 200 as unarchived; all were rate limits)
- three fixed probe dates miss sites archived irregularly — fall back to a CDX lookup for the
  timestamps that actually exist

**Expect ~65-70% to clear.** From ~1,200 RELEVANT → **~800**.

---

## Stage 4 — Headcount: exclude the giants only

Your instruction is that this is flexible; the point is to exclude Infosys-scale firms, not to
hit a narrow band.

**Free source, discovered today:** the SignalHire *reveal* payload already returns `staffCount`
for the founder's current company. Every one of the 106 had it, at no extra cost. So headcount
arrives as a by-product of Stage 7 rather than needing its own lookup.

**Proposed rule:** drop above ~5,000 employees. Optionally flag the 250-999 band as priority,
since your own history gives it a 74% useful-lead rate versus 55% for 50-249.

**Reality check on this cohort:** of the 106 pushed, median headcount is **87**, with 38 under
50 and only 5 in 250-600. NASSCOM skews small. A hard 250 floor would discard most of the
directory, which is why "exclude giants" is the right framing.

---

## Stage 5 — India only

Every NASSCOM member is Indian, and city was dropped as a ranking signal after measurement showed
tier-2 firms match or beat tier-1 (70% vs 67% plausible-software, 10.5% vs 6.7% in-band).

**To do:** only strip the foreign-parent captives — Rolls-Royce, Maersk, Kenvue, Barclays,
Franklin Templeton and similar appeared in the sample and are not acquisition targets. Name and
domain heuristics plus the LLM read handle this. Free.

---

## Stage 6 — Engineering maturity, and the PR question

**How to know they use pull requests, in descending strength:**

| Signal | Where it comes from | Coverage seen |
|---|---|---|
| Public VCS org with merged PRs by ≥2 humans | GitHub search API, 1 call per org | **only ~4% of firms** |
| Published OSS package tied to their domain | npm registry, free | ~0% so far |
| Engineering blog on code review / CI-CD / branching | crawled `/blog` | low |
| **Careers/JD naming code review, PR, Git, CI/CD** | crawled `/careers` | **the realistic signal** |
| CI/CD + IaC tooling named on site | crawled pages | 44% of the 200 |
| SOC 2 / ISO 27001 / CMMI ≥3 | crawled pages | 38% of the 200 |

**The honest position: Tier A is nearly absent in this population.** Of 200 firms, 4 had a repo
and only 2 had merged PRs from multiple humans. So confidence will be *Inferred* for almost
everyone, and **careers-page language carries the scoring**.

**One gap worth closing:** many firms list roles via Greenhouse / Lever / Naukri rather than
on-page, so the JD text — the single most attainable signal — is not being captured. Following
those links would likely unblock a real slice of firms currently stuck at Tier C. This is new
work, free, and I would prioritise it.

**Also to add:** bot exclusion is already in place (dependabot was a test org's top "contributor"
with 63 merged PRs), and vendor-link rejection (a `github.com/twbs` link means the site uses
Bootstrap, not that they wrote it).

---

## Stage 6b — Learn from what actually converted

Measured across 1,656 HubSpot deals, by win rate:

| Source | Deals | Won | Win rate |
|---|---|---|---|
| Manual / hand-picked (Shobit + Ishpreet) | 24 | 5 | **20.8%** |
| Tracxn Startups | 175 | 3 | 1.71% |
| GoodFirms crawl | 493 | 2 | 0.41% |
| LinkedIn Ads | 355 | 1 | 0.28% |
| Sales Navigator | 400 | 0 | 0.00% |

**What this implies for filter design:**
- Directory scraping converts at ~0.2-0.4%. Heavier filtering is the bet being tested here.
- GoodFirms leads had a single unverified SignalHire name (**every row is `confidence: amber`,
  none green**). NASSCOM leads get a name read off the company's own leadership page *and*
  confirmed by reveal, with the title checked. That difference is the hypothesis.
- Tracxn's 1.71% is the bar to beat for a scalable source.

**Proposed extra filter, from the data:** once the 108 NASSCOM deals have been dialled for a
week, compare stage progression by score band. If Priority-band firms move materially better than
the rest, the rubric earns its cost; if not, we drop to the cheap signal-density sort. That test
needs a week of calling, not more scraping.

---

## Stage 7 — Founder / CEO discovery

**The sequence that works, cheapest first:**

1. **Scrape team / leadership / about pages** — free. Yields a LinkedIn profile URL for ~30% of
   firms, a name for a further ~25%.
2. **Render JS-only pages with Playwright** — free, recovers pages plain HTTP cannot see
   (16 of 30 on one pass).
3. **Reveal by LinkedIn URL** — 1 credit, uses the *credits* pool, no search quota. Returns name,
   title, phone, email, LinkedIn **and headcount**. This is the step that made today's 108 possible.
4. **`searchByQuery` by company name** — only when the search pool resets; it is the sole route
   for firms that publish no profile URL.

**Measured conversion:** 182 firms with a URL → 106 with a senior title and a +91 number (58%).
Filtered out: 36 not senior, 31 foreign-number-only, 9 no phone.

**Reveal returns the title, so a name is not needed beforehand** — the URL alone identifies the
person, and seniority is judged on the returned title, not on page context.

---

## Expected funnel

| Stage | Remaining |
|---|---|
| NASSCOM unique members | 2,775 |
| Net-new vs HubSpot | 2,499 |
| Website reachable + plausible | 1,681 |
| V2 classification RELEVANT | ~1,200 |
| Pre-2024 software evidence | ~800 |
| Not a giant / not a foreign captive | ~750 |
| Rubric ≥50 with PR-adjacent evidence | **~150-250** |
| Founder found + +91 number | **~90-150 callable** |

108 are already pushed, so this yields roughly **another 100-150**.

---

## Cost and time

| Stage | Cost | Time |
|---|---|---|
| 1. Verify scrape completeness | free | 15 min |
| 2. V2 classification, 1,681 firms | ~50 agent batches | 1-2 h |
| 3. Wayback pre-2024 | free | 2-3 h (archive.org is slow) |
| 4. Headcount | free (rides on reveal) | — |
| 5. India / captive filter | free | 20 min |
| 6. Rubric + JD harvesting | ~30 agent batches | 2-3 h |
| 7. Founder discovery + reveal | **~400-600 credits** of 2,135 | 3-4 h |

Total: roughly a day of wall-clock, mostly unattended, with credits the only metered resource.

---

## Decisions I need from you

1. **Rubric threshold for pushing** — ≥50 (Secondary+), or the ≥20 bar used for the 108?
2. **Headcount ceiling** — drop above 5,000, or a different line?
3. **Tier A absence** — accept `Inferred` confidence for nearly everyone, since only ~4% have a
   public repo, or require harder evidence and accept a much smaller list?
4. **JD harvesting from Greenhouse/Lever/Naukri** — worth building? It is the main route to
   genuine PR evidence for this population.
5. **Credit ceiling** — how many of the 2,135 may this consume?

---

## What I would flag before starting

**The 108 already pushed did not clear this bar.** They passed signal-density ranking, a senior
title check and the +91 gate — not the rubric, not pre-2024, not headcount. Of them, 73 do have
pre-2024 evidence and only 5 sit in 250-600. They are a reasonable cold-calling cohort but they
are not the "verified PR workflow" list this plan produces.

**And the strongest lesson in the data is not about filters.** 24 hand-picked leads produced 5
wins; 961 scraped leads produced 2. Before scaling any directory further it is worth asking
Shobit and Ishpreet where those 24 came from — that channel converts ~50x better than anything
automated, and nobody has written down what it is.
