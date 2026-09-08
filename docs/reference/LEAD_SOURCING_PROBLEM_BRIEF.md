# Lead Sourcing & Enrichment — Problem Brief for Research

**Purpose of this document:** hand to a researcher/assistant to find ways around the bottlenecks below. It is self-contained — no prior context needed. All numbers are **measured**, from real runs on 2026-07-30/31, not estimates.

---

## 1. The business

**LH2 AI Labs** acquires two kinds of dormant assets from Indian companies, to build specialised training datasets for US frontier AI models:

| Line | What we buy | Typical target |
|---|---|---|
| **Codebase acquisition** | dormant **pre-2024 software codebases** — written-off IT projects, abandoned MVPs, retired internal tools | Indian **IT-services firms** (dev shops/agencies) + dead/struggling startups |
| **Ops-data acquisition** | **internal operating know-how** — SOPs, playbooks, process docs, internal tooling/workflows, org & vendor setup | companies that **actually ran an operation** (logistics, delivery, fulfilment, commerce, field-services) |

The pitch is a fast liquidity event for assets the founder has already written off. Deals are small ($5k–20k typical), so **volume of qualified, contactable leads is the whole game.**

### Target profile (the "gate")
- **HQ: India**
- **Founded ≤ 2022** (real operating history)
- **50–1,000 employees**
- **Not a large outsourcer** (TCS/Infosys/Wipro/HCL/Cognizant… blocklisted — never targets)
- Must be **net-new** (not already in our CRM)

### What "a usable lead" requires
- **Cold calling:** a working **+91 phone**, and ideally an email
- **LinkedIn ads (matched audience):** **email OR first+last name**, plus company/title to raise match rate. LinkedIn wants **10k–300k** contacts for best results; **our best list so far is 1,000.**
- **LinkedIn/email outreach:** a founder-level **named person** at the company

---

## 2. Current stack

| Layer | Tool |
|---|---|
| Sourcing (crawl) | **custom Python crawler** — GoodFirms directory |
| Storage | SQLite (`pipeline.sqlite`: `raw_listings`, `companies`, `people`) |
| Contact enrichment | **SignalHire API** (`searchByQuery` → find person; `candidate/search` → reveal phone/email) |
| Judgment/extraction | **Anthropic Claude** (Haiku) |
| Target scoring | **Wayback Machine CDX** + Claude (see §5) |
| CRM | **HubSpot** (2 portals) |
| LinkedIn outreach | **OutFlo** (3 campaigns, ~6.2k leads) |
| Startup data | **Tracxn** (static sheet export, 6,654 ranked companies) |
| Env | Windows, Python 3.14, **Playwright installed and working** |

**Pipeline phases:** `crawl → build (canonicalise/dedupe/gate) → enrich → score (namesake guard + confidence) → export → HubSpot push`

---

## 3. ✅ What works

- **Crawling is free, reliable and productive.** One run: **140 pages → 5,456 rows → 5,369 unique companies → 1,121 gate-passed net-new firms.** No blocking, polite crawl (1 req/host, 2–5s delay).
- **SignalHire *reveal*** (once you have a person) works well and is cheap — **cached reveals cost 0 credits**; ~90 credits covered a whole day of work.
- **Tracxn export** is rich where it applies: founder name + email + phone + funding + employee counts in one row. Our distressed-startup push (110 deals) worked *because of this*.
- **Claude-based vetting** works: classifying company type, scoring asset fit, reading call notes for re-engagement signals.

---

## 4. 🔴 THE CORE BOTTLENECK: company → founder identity

**We can find companies for free. We cannot find their people.**

Measured funnel: **1,121 gate-passed IT firms → only ~91 with a resolved founder (≈8%).**

Every route tested and its measured result:

| Route | Result | Evidence |
|---|---|---|
| **GoodFirms profile pages** | ❌ **no people data at all** | Fetched profiles directly. "Founder/CEO" strings are GoodFirms' own site nav and **client reviewers'** names ("X, Managing Director at [their own company]" — customers, not the firm's leadership). Only LinkedIn link on page is GoodFirms' own. No `tel:`. JSON-LD is GoodFirms' org markup. |
| **SignalHire `searchByQuery`** (title-search: company + "Founder OR CEO…") | ⚠️ **works, but hard daily cap** | **HTTP 402 "daily search attempts quota"**. One run: **881 attempts → 0 usable results** once capped. Quota did **not** reset after 24h. Credits were fine (409 left) — it's the *search* quota, not credits. |
| **Company's own website** (+ Claude extraction of /about, /team, /leadership) | ❌ **~5% hit rate** | 20 firms sampled → 1 founder found. Small Indian agencies don't publish leadership. |
| **Claude's own knowledge** | ⚠️ **depends entirely on company notability** | **0/12** on obscure IT-services SMEs (WebOsmotic, V2Soft, Teknotrait… — correctly refuses to guess, they aren't in training data). **BUT 59/80 = 74%** on *funded/notable deadpooled startups* (31 high + 26 medium confidence, 44 with LinkedIn URLs) — from a prior batch run preserved at `crm_mirror/sources/ailabs_research/`. **Conclusion: LLM founder-research is viable for funded startups, useless for small agencies.** |
| **Indian corporate registry (MCA/ZaubaCorp/Tofler)** — *directors are public legal record* | ❌ **source went paid/gated** | Module already built (`registry_founders.py`). Today: ZaubaCorp search returns an **empty shell** (nav shows *Login/Pricing/Get Started/Prime Research*), no result links. Tofler = Cloudflare challenge. MCA = 403. IndiaFilings = 404. **Playwright loads the pages fine (200, no CF challenge) — the data is simply behind a paywall now.** |

**This is the single highest-value problem to solve.** Everything downstream (cold calling, LinkedIn ads, outreach) is starved by it.

---

## 5. Secondary bottlenecks

### 5a. Crawl coverage — 1 of 6 adapters live
Built but **switched off**: `clutch.py`, `techbehemoths.py`, `designrush.py`, `nasscom.py`, `manifest.py`.
- **Clutch** — largest agency directory; crawler built, selectors "not live-verified"
- **TechBehemoths** — selectors verified, but the listing lacks website/founded/size → needs a profile-page fetch
Finishing these is free coverage, but doesn't solve §4 (they're also company-only sources).

### 5b. Contact quality — the namesake problem
SignalHire reveals frequently return the **right name at the wrong company**:
- `Infintus` → an `@infosys.com` address + US phone
- `GramFactory` → `@ril.com` (Reliance)
- Stoa / Blue Sky Analytics → US numbers
**Mitigation built:** only accept a **company-domain email** or a genuine **+91 phone**; reject US numbers (`+1`, 11-digit leading 1) and other-corp domains. This works but **discards a lot of otherwise-paid-for data.**

### 5c. Email coverage is low for this segment
Measured: **IT-services SMEs ≈ 15–30%** email coverage; **startup founders ≈ 45–60%**. Phone coverage is much better. Any solution should assume **email is the scarce field.**

### 5d. Vetting throughput (Wayback)
Asset-scoring uses **Wayback CDX** (first-capture year = pre-2024 proof; last-capture = death timing) + a homepage snapshot + Claude classification.
- Throttles hard: **~1 company / 15s** even with backoff; 3 parallel workers barely help.
- **31% of a 100-company run returned no page text** on the first pass (needed a retry pass).
- At 6,654 companies this is hours-to-days. Needs a faster archive/snapshot approach.

### 5e. Dead/parked domains & domain reuse
Deadpooled companies' domains are usually parked, expired, or **sold to a different business** (e.g. `stoa.com` was a wedding-speech site before the edtech; `oyerickshaw.com` is now a coffee shop).
**Mitigation built:** bound Wayback snapshots to `[founded_year … +7]` and have Claude flag "this page describes a different business." Works, but costs an LLM call per company.

---

## 6. Constraints

- **Budget-sensitive** — appetite is roughly **$100–200/month**, not $15k/yr enterprise data contracts.
- **Geography: India** — most US-centric B2B databases are thin on 30–200-person Indian dev shops.
- **Compliance matters** — we will not do anything that breaches a platform's ToS (e.g. bulk LinkedIn scraping/export). Needs to be defensible.
- **Scale needed:** ~1,000–5,000 contactable leads per line to keep callers and ad audiences fed; LinkedIn ads ideally want 10k+.
- **Already have:** HubSpot, SignalHire (low tier), Anthropic API, Playwright, a working crawler, Tracxn (static export).

---

## 7. What we want researched

1. **Indian SME founder/director data at scale** — what is the best *cheap or free* route to directors/founders of Indian private limited companies? Is **MCA** data available in **bulk** (open data dumps, state datasets, third-party mirrors, paid APIs)? What do the paid tiers of ZaubaCorp / Tofler / Probe42 / SignalX actually cost and allow (export limits, API)?
2. **Best-value enrichment provider for India** — compare **Apollo.io, Clay, Lusha, Snov, Hunter, Findymail, Prospeo, Dropcontact, Anymailfinder, Coresignal, Proxycurl** on: Indian SME coverage, **search-volume limits** (our current killer), export rights, phone vs email coverage, and price at ~1–5k lookups/month.
3. **ToS-compliant company → people mapping** — what's the legitimate path from a company to its founder? (Sales Navigator + approved export tools? Official APIs? Licensed datasets?) Where is the line, concretely?
4. **Better Indian company directories** — beyond GoodFirms/Clutch/DesignRush/TechBehemoths: **Nasscom member lists, Justdial, IndiaMART, Google Maps/Places, StartupIndia, state IT-association registries.** Which expose founder/contact info, and which allow programmatic access?
5. **Faster archive/liveness signals** — alternatives to Wayback CDX for (a) proving a site existed pre-2024, (b) detecting when it died, (c) getting an active-era homepage snapshot. (CommonCrawl index? Bulk WARC? DNS/WHOIS history? Certificate transparency logs?)
6. **Distressed-company signals** — beyond Tracxn: free/cheap sources for **shutdown, layoff, insolvency (IBC/NCLT), strike-off, and domain-expiry** signals for Indian companies.
7. **Sanity-check the buying plan** — is `SignalHire paid (~$83/mo, lifts the search quota) + Apollo (~$49–99/mo)` genuinely the best ~$150/mo configuration, or is there a better combination for **India-heavy SME data**?

---

## 8. The one-line version

> We can crawl thousands of qualifying Indian IT-services companies for free, but only **~8%** of them can we attach a real founder contact to — because directories have no people data, the corporate registry went paid, company sites don't list leadership, and our enrichment vendor caps *daily searches* (not credits). **Find us a cheap, compliant, high-coverage way to go from "company name + website" to "founder name + phone/email" at India-SME scale.**
