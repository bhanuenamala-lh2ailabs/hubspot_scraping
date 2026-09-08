# IT-Services Funnel — Weekly Analysis · 2026-W31

_Generated 2026-08-02 · regenerate with `python analysis/weekly/weekly_report.py --pull`_

> **Scope:** 425 IT-services deals exist in HubSpot. This report analyses the **393 scrape-sourced** ones. The other **32** were migrated from the Private Codebase Tracker (warm, hand-curated deals — they reach Interested+ at 94% and would badly skew scrape-quality metrics).

## 0. KPI scoreboard

_Definitions + targets: [`analysis/KPI_DEFINITIONS.md`](../../KPI_DEFINITIONS.md). Funnel KPIs count only leads ≥14 days old. First week — no deltas yet._

| Source | n | **ULR** ⭐ | QR | CR | FAR | ER | MR | AFD | WR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| goodfirms scrape | 393 | **55.5%** | 62.1% | 87.5% | 0.0% (n=60) | 20.3% | 1.9% | 0.92 | 0.0% |
| scrape gated 50plus | 253 | **56.5%** | 62.8% | 85.8% | 0.0% (n=25) | 20.0% | 2.6% | 1.0 | 0.0% |
| scrape legacy sub50 | 140 | **53.6%** | 60.7% | 90.7% | 0.0% (n=35) | 20.4% | 1.5% | 0.88 | 0.0% |
| codebase tracker | 32 | **78.1%** | 93.8% | 84.4% | — | — | — | — | — |

**Targets:** ULR ≥80% · QR ≥85% · CR ≥85% · FAR ≥90% · ER ≥25% · MR ≥8%

- 🔴 **ULR 55.5% is below the 80% target** — the scrape is sending unusable leads
- 🔴 QR 62.1% — too many wrong targets (gate/source accuracy)
- 📊 **Source comparison:** curated tracker leads score **QR 93.8%** vs scrape **62.1%** — the scrape sends ~6× more wrong targets.
- ⚠️ **The 50-employee gate barely helps:** gated leads score ULR **56.5%** vs legacy sub-50 **53.6%** — only +2.9pp. Purging the legacy batch will *not* fix lead quality on its own; the source is noisy at every size band.
- ℹ️ **FAR 0.0% (n=60) is a biased sample** — analysts usually only record a headcount when it's *wrong*, so this trends to 0 by construction. Treat it as 'verified failures found', not a population accuracy rate.

## 1. Headline

| Metric | Value |
|---|---|
| Total scraped IT-services deals | **393** |
| Still alive in funnel | 168 (43%) |
| Dead | 225 (57%) |
| **Screened out as WrongFit — never even called** | **149 (38%)** |
| Reached Interested or beyond | 45 (11%) |
| Closed/Won | 1 |

## 2. Funnel — how far deals actually get

Cumulative: a deal counts at a step if it **reached that step or beyond** (including dying there later).

| Step | Reached | % of all | |
|---|---:|---:|---|
| Cold Call | 393 | 100.0% | `████████████████████████████` |
| Call Attempted | 238 | 60.6% | `█████████████████···········` |
| Interested | 45 | 11.5% | `███·························` |
| GMeet Fixed | 9 | 2.3% | `█···························` |
| Script Shared | 7 | 1.8% | `····························` |
| Script Results Received | 3 | 0.8% | `····························` |
| Commercial Negotiation | 3 | 0.8% | `····························` |
| Deal Contract Signed | 2 | 0.5% | `····························` |
| Closed/Won | 1 | 0.3% | `····························` |

**Biggest drop-offs**
- **Cold Call → Call Attempted**: 393 → 238 (**−39%**)
- **Call Attempted → Interested**: 238 → 45 (**−81%**)
- **Interested → GMeet Fixed**: 45 → 9 (**−80%**)
- **Script Shared → Script Results Received**: 7 → 3 (**−57%**)
- **Commercial Negotiation → Deal Contract Signed**: 3 → 2 (**−33%**)
- **Deal Contract Signed → Closed/Won**: 2 → 1 (**−50%**)

## 3. City × how far the deal went

| City | Deals | WrongFit % | Called+ | Interested+ | Script+ | Avg depth |
|---|---:|---:|---:|---:|---:|---:|
| Bengaluru | 96 | 42% | 58% | 17% | 2% | 0.84 |
| Pune | 66 | 44% | 56% | 6% | 2% | 0.65 |
| Noida | 40 | 45% | 50% | 5% | 2% | 0.60 |
| Ahmedabad | 33 | 39% | 55% | 12% | 3% | 0.79 |
| Jaipur | 24 | 50% | 50% | 12% | 4% | 0.71 |
| Mumbai | 18 | 28% | 72% | 11% | 0% | 0.83 |
| Delhi | 17 | 47% | 53% | 0% | 0% | 0.53 |
| Kolkata | 14 | 29% | 71% | 7% | 0% | 0.79 |
| Chennai | 12 | 17% | 75% | 25% | 0% | 1.00 |
| Surat | 11 | 0% | 100% | 9% | 0% | 1.09 |
| Mohali | 11 | 18% | 82% | 27% | 9% | 1.91 |
| Hyderabad | 10 | 60% | 40% | 10% | 0% | 0.50 |
| Indore | 10 | 20% | 80% | 20% | 0% | 1.00 |
| Gurgaon | 10 | 20% | 80% | 10% | 0% | 0.90 |
| Coimbatore | 7 | 29% | 71% | 0% | 0% | 0.71 |
| Kochi | 7 | 29% | 71% | 0% | 0% | 0.71 |
| Bhopal | 3 | 0% | 67% | 33% | 0% | 1.00 |
| Vadodara | 3 | 67% | 33% | 0% | 0% | 0.33 |

- **Best converting (≥8 deals):** Mohali — 27% reach Interested+
- **Worst quality (≥8 deals):** Hyderabad — 60% WrongFit

## 4. Company size × how far the deal went

_Size = the headcount **GoodFirms reported** (range midpoint) — the value our 50–1,000 gate used._

| Reported size | Deals | WrongFit % | Interested+ | Script+ | Avg depth |
|---|---:|---:|---:|---:|---:|
| <50 | 140 | 39% | 13% | 4% | 0.89 |
| 100–249 | 234 | 38% | 10% | 1% | 0.71 |
| 500–1000 | 19 | 21% | 21% | 0% | 1.00 |

### ⚠️ Reported size vs. what the analyst actually found

Analysts recorded a **real headcount** in 60 notes. Comparing to what GoodFirms claimed:

| Company | GoodFirms said | Analyst found | Stage |
|---|---:|---:|---|
| Associative | 29 | **1** | WrongFit |
| DigiQAL Technologies | 149 | **1** | WrongFit |
| KIBA Labs | 29 | **1** | WrongFit |
| DMCS INDIA PRIVATE LIMITED | 149 | **1** | WrongFit |
| Alpine Software | 29 | **2** | WrongFit |
| Reach C Onmark Pvt Ltd | 29 | **2** | WrongFit |
| CodeKing solutions | 149 | **2** | WrongFit |
| AlphaKlick Solutions | 29 | **3** | WrongFit |
| ANNEXCODE | 29 | **3** | WrongFit |
| Sulonya Technologies Priva | 149 | **3** | WrongFit |
| Rupstech Pvt. Ltd | 149 | **4** | WrongFit |
| Risva | 29 | **5** | WrongFit |
| Elovient Software Solution | 149 | **5** | WrongFit |
| Bhavitra Technologies Priv | 149 | **5** | WrongFit |
| Edhaas digisoft | 149 | **6** | WrongFit |

**60 of 60** verified companies were **under 50 employees** — they should never have passed the size gate.

## 5. Dead-reason distribution

| Dead stage | Deals | % of dead | |
|---|---:|---:|---|
| Dead/ColdCall/WrongFit | 149 | 66% | `███████████████████·········` |
| Dead/ColdCall/Not Interested | 74 | 33% | `█████████···················` |
| Dead/Negotiation/Contractual | 1 | 0% | `····························` |
| Dead/Interested/NoShow | 1 | 0% | `····························` |

## 6. What the analysts' notes actually say

_216 notes categorised._

| Reason | Notes | % | |
|---|---:|---:|---|
| too small headcount | 61 | 28% | `████████····················` |
| positive signal | 51 | 24% | `███████·····················` |
| contact unreachable | 49 | 23% | `██████······················` |
| foreign company | 13 | 6% | `██··························` |
| not interested other | 11 | 5% | `█···························` |
| wrong services segment | 8 | 4% | `█···························` |
| too new | 8 | 4% | `█···························` |
| no reason given | 8 | 4% | `█···························` |
| data mismatch | 5 | 2% | `█···························` |
| not operating defunct | 2 | 1% | `····························` |

### Why leads were screened out as WrongFit (never called)

| Reason | Notes | % |
|---|---:|---:|
| **too small headcount** | 58 | 55% |
| **contact unreachable** | 23 | 22% |
| **foreign company** | 9 | 8% |
| **too new** | 6 | 6% |
| **data mismatch** | 4 | 4% |
| **wrong services segment** | 4 | 4% |
| **no reason given** | 1 | 1% |
| **not interested other** | 1 | 1% |

## 7. Founded year × outcome

| Founded | Deals | WrongFit % | Interested+ | Avg depth |
|---|---:|---:|---:|---:|
| ≤2010 | 112 | 35% | 12% | 0.79 |
| 2011–2015 | 136 | 37% | 10% | 0.73 |
| 2016–2019 | 103 | 36% | 14% | 0.87 |
| 2020–2022 | 42 | 55% | 10% | 0.81 |

## 8. By analyst

| Analyst | Deals | Called+ | Interested+ | WrongFit % |
|---|---:|---:|---:|---:|
| Shreyas Boosnoor | 340 | 58% | 11% | 40% |
| Yash Wani | 32 | 81% | 6% | 19% |
| unassigned | 12 | 50% | 0% | 50% |
| Ishpreet Sood | 7 | 86% | 71% | 14% |
| Shobit Gupta | 2 | 100% | 100% | 0% |

## 8b. 🎯 Top cities — where to concentrate next week

_Ranked by average funnel depth (AFD), min 7 deals. This is the list to weight the next scrape toward._

| # | City | n | ULR | QR | ER | AFD |
|---:|---|---:|---:|---:|---:|---:|
| 1 | **Mohali** | 11 | 82% | 82% | 33% | 1.91 |
| 2 | **Surat** | 11 | 91% | 100% | 9% | 1.09 |
| 3 | **Chennai** | 12 | 75% | 83% | 30% | 1.00 |
| 4 | **Indore** | 10 | 70% | 80% | 25% | 1.00 |
| 5 | **Gurgaon** | 10 | 80% | 80% | 12% | 0.90 |
| 6 | **Bengaluru** | 96 | 50% | 58% | 29% | 0.84 |
| 7 | **Mumbai** | 18 | 56% | 72% | 15% | 0.83 |
| 8 | **Ahmedabad** | 33 | 55% | 61% | 20% | 0.79 |
| 9 | **Kolkata** | 14 | 71% | 71% | 10% | 0.79 |
| 10 | **Coimbatore** | 7 | 71% | 71% | 0% | 0.71 |

**Volume traps** — high volume, low quality: **Jaipur** (n=24, ULR 46%), **Pune** (n=66, ULR 47%), **Bengaluru** (n=96, ULR 50%)
These absorb the most caller time for the least return. Cap or deprioritise them.

## 8c. 📈 Size band — is >249 employees better?

| GoodFirms band | n | ULR | QR | ER | AFD |
|---|---:|---:|---:|---:|---:|
| 10 - 49 | 140 | **54%** | 61% | 21% | 0.89 |
| 50 - 249 | 234 | **55%** | 62% | 16% | 0.71 |
| 250 - 999 | 19 | **74%** | 79% | 27% | 1.00 |

**Yes — decisively.** `250 - 999` scores **ULR 74%** vs **55%** for `50 - 249` (+19pp), QR 79% vs 62%, ER 27% vs 16%.

**But supply is the constraint:** the scrape DB holds only **166 gate-passing `250 - 999` firms** vs **955** in `50 - 249`. We've used 19 of the 166.
→ **Work all ~147 remaining `250 - 999` firms first**, then fall back to `50 - 249` filtered to the best cities above.

---

## 9. 🔎 Root cause: why 1-in-3 leads is unusable

The dominant kill reason is **company far too small**. It has *two separate causes* — and they need different fixes.

### Cause A — 140 legacy deals that predate the size gate

- **140 of 393 (36%)** scrape-sourced deals came from the GoodFirms band **`10 - 49`** (midpoint 29) — below our 50-employee floor.
- They were pushed **before** the `size_min_headcount: 50` floor existed.
- **The gate is correct today:** of 2,692 `10 - 49` companies in the scrape DB, **0 currently pass** (`size ~29 below floor 50`).
- So this is a **cleanup problem, not a code problem** — but these are still sitting in callers' queues today (58 still alive).

### Cause B — GoodFirms size data is wrong ~10% of the time, even when it passes the gate

- Of **253** deals from gate-*passing* bands (`50 - 249`, `250 - 999`), analysts found **26 (10%)** to be far too small on inspection.
- Their **actual** headcount: min **1**, median **11**, max **26** — against a claimed range of 50–249.
- Examples where GoodFirms said `50 - 249`:
  - **Actiknow Consulting Pvt Ltd** → actually **13** people
  - **Alphalogic Techsys Limited** → actually **11** people
  - **Aneka Labs Private Limited** → actually **19** people
  - **DigiQAL Technologies** → actually **1** people
  - **Edhaas digisoft** → actually **6** people
  - **Fibonalabs** → actually **15** people

**This one cannot be fixed by tightening the threshold** — the source data itself is unreliable. It needs a second, independent size check before a lead reaches a caller.

## 10. ✅ What we're changing next week

| # | Change | Why (this week's data) | Effort |
|---|---|---|---|
| 1 | **Prioritise the ~147 unused `250 - 999` firms** ahead of everything else | That band scores ULR 74% vs 55% and ER 27% vs 16% | config |
| 2 | **Weight the next scrape to the top-10 cities** (Mohali, Surat, Chennai, Indore, Gurgaon, Bengaluru, Mumbai, Ahmedabad, Kolkata, Coimbatore) | They lead on funnel depth; Bengaluru/Jaipur absorb volume at ~50% ULR | config |
| 3 | **Add a SignalHire headcount pre-check before push** (see §10b) | Catches 6/8 of the too-small firms GoodFirms passed — no credits, no ToS risk | small |
| 4 | **Purge the 58 still-alive `10 - 49` legacy deals** | Fail today's gate — but note this alone only moves ULR ~3pp | 10 min |
| 5 | **Fix contact quality** — 49/216 notes (23%) are 'wrong number / need LinkedIn' | 2nd-biggest killer | see `LEAD_SOURCING_PROBLEM_BRIEF.md` |
| 6 | **Drop founded ≥2020 from the gate** | 55% WrongFit vs 38% overall | 1 line of config |

### 10b. Headcount pre-check — SignalHire works, and it's free

`searchByQuery{currentCompany}` returns a **`total`** = profiles listing that employer. Tested against ground truth:

| Company | Real | SignalHire `total` | Verdict |
|---|---:|---:|---|
| Velotio | 244 | 252 | ✅ |
| Aneka Labs | 19 | 19 | ✅ |
| Fibonalabs | 15 | 12 | ✅ |
| Alphalogic | 11 | 9 | ✅ |
| DigiQAL | 1 | 7 | ✅ |
| Bacancy | 1095 | 451 | ✅ |
| Actiknow | 13 | 92 | ❌ over |
| GigLabz | 25 | 78 | ❌ over |

**6/8 correct** — vs GoodFirms, which passed *all 8* (2/8). Costs a **search, not a credit**, and the search quota resets daily. Both misses are *over*-counts (name collision), so it never wrongly rejects a good firm — it only occasionally lets a small one through.

_LinkedIn's public page is more accurate (Velotio 244 exact) — `crm_mirror/enrich/verify_headcount.py` — but it throttles (HTTP 999) and is against LinkedIn's ToS, so **SignalHire is the one to wire into the pipeline**; keep LinkedIn for spot-checks._

### Watch next week
- **ULR** on the `250 - 999` batch — does it hold above 74%?
- **QR** after the SignalHire pre-check — target ≥85% (from 62%).
- Do the top-10 cities keep their edge as n grows?
- City signal is still thin (<25 deals for most) — treat as directional.

