# Implementation Verdict — Intersection Pipeline for LH2 AI Labs
_Prepared 17 August 2026_

## PART A — Verdict (implementation)
Keep the intersection design, but implement it **name-first, not dump-first**: because you already hold the MCA director NAME, the primary discovery actor is **harvestapi/linkedin-profile-search-by-name** (cookieless, no ban risk), fed `firstName`+`lastName`+`currentCompanies=[LinkedIn company URL]`, which returns 1–3 candidate rows to disambiguate rather than a 40-row employee dump — roughly $0.10 per firm versus ~$0.18 for a 40-person Short dump. Run **Exa People Search (~$0.007/query)** as an even-cheaper first pass and fall back to the HarvestAPI by-name actor only on misses. There **is one resolution hop** — the by-name actor's `currentCompanies` filter expects LinkedIn company URLs — but it is a one-time ~$1 bulk job for 349 firms via **harvestapi/linkedin-company** ("find company URL by name/domain in bulk"), and those URLs are reused for the employee-dump backstop too. Keep the **company-employees dump ($4/1k Short) only as a fallback** when name-search returns nothing, and MCA as the 100% backstop for the LinkedIn-zero ~57%. **The single biggest risk is LinkedIn coverage of obscure sub-50-employee Indian IT firms: there is no published benchmark and the indirect evidence (vendors admit coverage "drops for smaller companies"; tiny Indian firms often have only a founder's personal profile, not a company page) is discouraging** — resolve it with a 10-firm empirical bake-off that measures intersection rate and cost-per-useful-lead before full rollout.

## PART B — Verdict / comparison table

| Tool | Input accepted | Key output fields | Cookieless | Price / 1k | Est. cost-per-useful-lead @40-emp firm | Coverage confidence (small Indian firms) | Verdict |
|---|---|---|---|---|---|---|---|
| **harvestapi/linkedin-profile-search-by-name** | name (req) + company URL, location, school filters | linkedinUrl, name, position/headline, location | Yes | ~$0.10/search page (10 results); Full +$0.004/profile (inferred from sibling) | **~$0.10** | Medium (live LinkedIn) | **PRIMARY** given MCA name held |
| **Exa People Search** | name + company (semantic) | profile URL, name, snippet | Yes (API) | **$7/1k = $0.007/query** | **~$0.007** | Unknown | **Cheap first pass** |
| harvestapi/linkedin-company-employees | company URL **or** company name | linkedinUrl, name, headline, location, positions | Yes | **Short $4 / Full $8 / Full+email $12** | ~$0.18 (full dump) / ~$0.03 (name-filtered) | Medium | Fallback / backstop dump |
| harvestapi/linkedin-company | company **name or domain** | linkedinUrl, universalName, website, HQ, headcount | Yes | ~$2–3/1k | n/a (resolution hop) | High (firmographic) | **Resolution hop** |
| harvestapi/linkedin-profile-search ("Find all people") | title/company/location filters | profile list, linkedinUrl | Yes | $0.10/page (25 results); 2,500/query cap | ~$0.10+ | Medium | Broad discovery only |
| apimaestro/linkedin-company-employees-no-cookies | company URL | name, title, position | Yes | low | ~$0.10 | Low–Med | **Skip (2.9★)** |
| People Data Labs person-enrich | name+company+location / LinkedIn URL | linkedin_url, sometimes phone/email | Yes (API) | free 100/mo, then $0.28/match (Pro) | ~$0 (free tier) | Low–Med (India) | Free supplementary probe |
| SignalHire Person API | LinkedIn `/in/` URL / email / phone | work+personal email, direct phone, mobile, socials | Yes (API) | 5,000 credits held; **no-find-no-charge** | 1 credit/success | n/a (reveal) | **Reveal engine** |

**Reliability signals (2026):** harvestapi/linkedin-company-employees 4.6★ (42 reviews), 23K users, 4.1K MAU, ~18h issue response; by-name 4.4★ (12), 6K users; linkedin-profile-search 37K users, 4.4★; apimaestro employees 2.9★ (avoid). All HarvestAPI actors are cookieless → **no account-ban risk**; cookie-based actors (e.g., dev_fusion, memo23 cookie mode) carry permanent-ban risk and are excluded.

## Key Findings (verified)

1. **harvestapi/linkedin-company-employees** confirmed verbatim: **Short $4/1k** (full name, profile URL, summary, location, current positions), **Full $8/1k**, **Full+email $12/1k**. Input accepts a **LinkedIn company URL (preferred) OR a company name** ("it will try to find the company on LinkedIn") — no *mandatory* resolution hop. "One by one" mode (>10 companies) adds a **$0.02 start fee per company**. Optional fuzzy `search` query (e.g., the MCA name, or "Founder") + title filters can shrink a dump to a few billed rows.

2. **harvestapi/linkedin-profile-search-by-name**: cookieless, "Pay per event," 4.4★. Input schema: `firstName` (required), `lastName` (required), `locations[]`, `currentCompanies[]` (LinkedIn company URLs), `pastCompanies[]`, `schools[]`, `industry IDs`, `maxItems`. Output: `linkedinUrl`, `firstName`/`lastName`, `position`/headline, `location`, plus full profile in Full mode. Search page = up to 10 results. **Exact per-event cents are not published** (README omits them; JS-rendered pricing tab). Its sibling **harvestapi/linkedin-profile-search** charges (verbatim GitHub README) **"$0.10 per search page… Full: $0.10 per search page + $0.004 per each full profile scraped… Full + email search: $0.10 per search page + $0.01 per each full profile"** — the by-name actor almost certainly mirrors this pattern (page size 10 vs 25). **Budget ~$0.10 per firm** for a Short by-name lookup.

3. **harvestapi/linkedin-profile-search** ("Find all people"): $0.10 per 25-result page; company/title/location filters; hard LinkedIn cap of **2,500 results/query**, worked around by splitting queries (by city/title/industry) and paginating via `startPage` ("Automatic Query Segmentation").

4. **Resolution actor**: **harvestapi/linkedin-company** explicitly "Find[s] LinkedIn company URLs by name in Bulk," accepts **company name OR domain** (`universalName`/`url`), returns `linkedinUrl`, website, HQ, employee count, ~$2–3/1k. **harvestapi/linkedin-company-search** is the filtered variant. Cheapest name/domain→company-URL hop.

5. **Exa People Search**: **$7/1k = $0.007/query** (raised from $5 in March 2026, per Exa docs and fastCRW); dedicated people index of **1B+ profiles** (50M+ updates/week ingestion); free signup credits (~$20) plus ~$10/mo free — enough to test all 349 at $0. Cheapest per query; obscure-Indian-firm coverage unverified.

6. **SignalHire Person API**: accepts a LinkedIn `/in/` URL, email, or phone as an `item` (**up to 100 items/request**, 600/min), returns work email, personal email, direct phone, mobile, socials. **Credit rule confirmed "no find, no charge"** — "No credits are consumed for failed items"; a credit is consumed only when ≥1 verified contact is returned (note: a returned *personal* Gmail still charges even if you wanted a work email). Default mode is async (callback URL required); pass **`withoutWaterfall: true` for synchronous results at slightly lower coverage.** Your banned name-search endpoint is irrelevant to URL/email/phone reveal.

7. **People Data Labs person-enrich**: free tier **100 lookups/month** (1 credit per successful 200 response), Pro $98/mo = 350 credits ($0.28/match); accepts `name`+`company`+`location` and returns `linkedin_url` and *sometimes* phone/email (contact data may require the Person Identify API at ~$0.55/match). G2 reviewers (via SyncGTM) warn PDL "trusts LinkedIn too much" and coverage "drops… for smaller companies" — so treat Indian-mobile hit-rate as low.

8. **Obscure-firm coverage — honest verdict:** No rigorous published benchmark. Indirect evidence is consistently discouraging: vendors admit small-company coverage weakness; enrichment hit-rates run 20–60% and are region-dependent; many tiny Indian IT firms are unregistered sole proprietorships whose founders maintain **personal** profiles, not company pages. This validates why the MCA backstop is essential and why only an empirical test can settle the intersection rate.

## Details

### Billing math per useful lead
Short mode, company-employees dump billed at $0.004/profile + $0.02 start fee/company:

| Firm size | Company-employees dump (Short) | Targeted by-name (Short, ~$0.10 flat) | Exa People Search |
|---|---|---|---|
| ~15 employees | 15×$0.004 + $0.02 = **$0.08** | **$0.10** | **$0.007** |
| ~40 employees | 40×$0.004 + $0.02 = **$0.18** | **$0.10** | **$0.007** |
| ~150 employees | 150×$0.004 + $0.02 = **$0.62** | **$0.10** | **$0.007** |

The dump scales with firm size and forces you to disambiguate 15–150 rows; by-name is flat and returns 1–3 rows; Exa is another order of magnitude cheaper. **Given the MCA name is held, the broad dump is never the economical choice** except as a zero-result fallback. Hybrid middle ground: feed the MCA name as the employee-actor's fuzzy `search` query to shrink a dump to ~$0.03/firm.

### Input-resolution hop
- **By-name route**: `currentCompanies` requires LinkedIn company URLs → one-time hop: 349 × ~$0.003 ≈ **$1**; 3,000 × ~$0.003 ≈ **$9** via harvestapi/linkedin-company.
- **Employee-dump route**: hop optional (name input works) but resolving first improves accuracy and lets you reuse URLs.

### MCA-name ↔ LinkedIn-name matching
MCA names are ALL-CAPS with single-token surnames, initials, surname-first ordering, and inconsistent transliteration (MCA "RAJESH KUMAR S" vs LinkedIn "Rajesh Kumar Srinivasan"; "S RAKESH" vs "Rakesh Soni"). Documented tools:
- **`indian-namematch`** (PyPI): purpose-built; initial expansion ("A Singh" ↔ "Ajeet Singh"), honorific stripping, Soundex + custom vowel/consonant normalizer.
- **IDinsight `hindi-fuzzy-merge`** (GitHub): stepwise "tightest-match-first" + Polyglot transliteration normalization; built for transliterated Indian names where Latin-optimized matchers underperform.
- **General stack**: RapidFuzz `token_set_ratio`; Double Metaphone/Soundex phonetic fallback; Beider-Morse for multi-script.

**Recommended rule (company already anchored — the strong disambiguator, so loosen the name threshold):**
1. Normalize both names: lowercase, strip punctuation/honorifics/suffixes, collapse whitespace, tokenize to a set.
2. `score = rapidfuzz.token_set_ratio`, augmented: (a) a single-character token matches any token starting with that letter (initial expansion); (b) unmatched token pairs get a Double-Metaphone equality check.
3. **Confidence tiers:** `full` = company anchor confirmed AND (`score ≥ 80` OR surname-exact + first-initial match); `title-only` = company anchor + partial name (60–80); `mca-only` = company matched but name weak (<60) or LinkedIn empty. **Accept threshold = 80 with the company anchor** (raise to 90 if ever matching without a company anchor).

### Direct name+company → phone/email shortcut (honest)
- **PDL Person Enrichment** (free 100/mo, then $0.28/match; contact data may need Person Identify ~$0.55): the only path that can turn MCA name+company directly into an Indian mobile at $0 — but small-company + Indian-mobile hit-rate is likely low. Run free as a parallel probe, especially for the LinkedIn-zero 57%.
- **Apify Full+email ($12/1k)**: SMTP-validated **emails only** (no phones), not guaranteed per profile.
- Net: **no shortcut reliably yields Indian mobiles**; keep SignalHire as the reveal engine (URL→phone/email) and PDL as a free supplement.

## PART C — Implementation spec (hand to Claude Code)

**Stages**
1. **Load MCA** rows (held): `company, domain, city, mca_name, mca_din, mca_source_url`.
2. **Resolve company URL** — POST batch to `harvestapi~linkedin-company` `run-sync-get-dataset-items` with `{ "companies":[company_name_or_domain, …] }`; capture `linkedinUrl` → `linkedin_company_url`. Cap ~$2 for 349.
3. **Targeted discovery** —
   - First pass **Exa** `/search` (people/semantic): query `"{mca_name}" {company}`; keep top URL if score high. Cost: free credits.
   - Fallback (Exa empty/low): POST `harvestapi~linkedin-profile-search-by-name` `{ "firstName","lastName","currentCompanies":[linkedin_company_url],"profileScraperMode":"Short","maxItems":10 }`. Cap $0.10/firm.
   - Last-resort (both empty): `harvestapi~linkedin-company-employees` Short with `search` = mca_name.
4. **Name match** — normalize; `score = rapidfuzz.token_set_ratio` + initial-expansion + Double-Metaphone; require company anchor (position/headline or `currentCompanies` match). Set `name_match_score`, `confidence_tier`.
5. **Reveal** — for `full`+`title-only`, POST LinkedIn URLs to SignalHire Person API (`items[]` ≤100/req, `withoutWaterfall:true` for sync). Record `reveal_status` (success/failed/not_found) + contacts (no-find-no-charge).
6. **Backstop** — for `mca-only`/LinkedIn-zero, PDL `/v5/person/enrich` `{name, company, location}` on free tier.

**Actor endpoints**
- `POST https://api.apify.com/v2/acts/harvestapi~linkedin-company/run-sync-get-dataset-items?token=…`
- `POST https://api.apify.com/v2/acts/harvestapi~linkedin-profile-search-by-name/run-sync-get-dataset-items?token=…`
- `POST https://api.apify.com/v2/acts/harvestapi~linkedin-company-employees/run-sync-get-dataset-items?token=…`
- SignalHire: `POST https://www.signalhire.com/api/v1/candidate/search` (Person API; `items[]`), `apikey` header.
- PDL: `GET https://api.peopledatalabs.com/v5/person/enrich`, `X-Api-Key` header.

**Output CSV schema**
`company, domain, city, mca_name, mca_din, mca_source_url, linkedin_url, linkedin_name, linkedin_title, name_match_score, confidence_tier, reveal_status`

**Per-source cost caps:** company-resolution ≤ $2; Exa = free credits; by-name fallback ≤ $0.10/firm; SignalHire = existing credits (no-find-no-charge); PDL = free 100/mo. Enforce a per-batch `maxTotalChargeUsd` abort on Apify.

**10-firm bake-off harness:** Select 10 firms across sizes (~15, ~40, ~150) including several deliberately obscure sub-50 firms. Run Stages 0–5. Per firm, record: LinkedIn company page found (y/n); candidates returned; `name_match_score`; `confidence_tier`; SignalHire `reveal_status` + whether an **Indian mobile** returned; total $ spent. **Report: intersection (full-tier) rate, LinkedIn-zero rate, Indian-mobile fill-rate, blended cost-per-useful-lead.** Gate the full 349 rollout on intersection rate ≥ target and cost-per-lead within budget.

## PART D — Cost projection

**349 firms now**
- Company-URL resolution: **~$1**.
- Discovery: Exa first pass **$0** (free credits); HarvestAPI by-name fallback on ~40% misses = ~140 × $0.10 ≈ **$14** (upper bound, all-HarvestAPI = ~$35).
- SignalHire reveal: **$0 marginal** (~349 reveals from 5,000 credits held; only successes charged).
- PDL backstop: **$0** (free 100/mo; batch remainder over 2–3 months).
- **Total marginal paid spend now ≈ $1–35 (realistically ~$15).**

**~3,000 firms later**
- Resolution: **~$9**.
- Discovery: Exa ~3,000 × $0.007 ≈ **$21** (partly offset by free monthly credits); HarvestAPI by-name for ~40% misses ≈ 1,200 × $0.10 ≈ **$120** (upper bound all-HarvestAPI ≈ $300).
- SignalHire: 3,349 total reveals still < 5,000 credits held; beyond that use API/Bulk plan at **$0.04–0.10/credit**.
- PDL: free tier stretched across months; heavy use → $0.28/match.
- **Total marginal paid spend at 3,000 ≈ $30–150** on the Exa-first / HarvestAPI-fallback approach; the SignalHire credit stock absorbs reveals.

## Caveats
- **Obscure-firm LinkedIn coverage is unproven** — the biggest risk; no published benchmark; indirect signals point to low coverage for sub-50-employee Indian firms. Marked for the bake-off.
- The **by-name actor's exact per-event price is inferred** from its sibling ($0.10/page + $0.004/profile); confirm on the live pricing tab before high-volume runs.
- **Exa's People index coverage of small Indian firms is untested**; treat $0.007 as throughput cost, not a guaranteed hit.
- **PDL and Apify Full+email phone coverage for Indian mobiles is likely weak**; SignalHire remains the reveal engine.
- Respect LinkedIn ToS, India's DPDP Act, and GDPR/CAN-SPAM for outreach; use only public/business contact data.