# Solving name+company → linkedin.com/in URL from one bot-walled IP: verdict + ready-to-paste Claude Code prompt

## TL;DR
- **Exa AI's `/search` "people" category is the answer.** It runs server-side on Exa's infrastructure (immune to your IP wall), takes a natural-language name+company+city query, returns the `linkedin.com/in/` URL in `results[].url` plus structured `company.name`/`location` for verification, costs $0.007/lookup, and its free tier ($20 signup + $10/month, no card) covers your entire 3,349-person workload (349 now + ~3,000 later) for roughly $0–$24.
- **Every HTML-scraping path stays dead and both classic free SERP APIs are gone**: per Google's official Custom Search JSON API page, "The Custom Search JSON API is closed to new customers" (existing customers have "until January 1, 2027 to transition"); Brave killed its free tier in Feb 2026 and now requires a card. Your working fallbacks are all server-side APIs: Jina `s.jina.ai` (server-side search, free token grant), Serper (2,500 free, no card), and People Data Labs person-enrichment (100 free/month, returns the LinkedIn URL directly).
- **SignalHire will not collapse the problem**: its reveal endpoint only accepts LinkedIn URL / email / phone / UID as identifiers — not name+company — so the LinkedIn URL remains the required key. Use async waterfall (callbackUrl) mode for maximum contact coverage and only reveal rows that already carry a regex-verified URL.

## Key Findings

### The primary route: Exa People Search
Exa is an AI-native search API (formerly Metaphor Systems, YC S21) that indexes 1B+ people profiles with 50M+ updates/week. As of December 19, 2025 it exposes a `people` search category (which replaced the older `linkedin` category) on the standard endpoint `POST https://api.exa.ai/search`. It:
- **Bypasses your IP wall entirely** — the request executes on Exa's servers; your single residential IP never touches a search surface or LinkedIn.
- **Takes name+company+city as a natural-language query** and returns each match's `url` (the `linkedin.com/in/` profile), `title`, and a structured `entities[].properties` object containing `workHistory[].company.name`, `location`, `firstName`/`lastName` — exactly the fields needed to verify the person co-mentions the target company and city without ever fetching LinkedIn.
- **Costs $0.007 per request** (base `/search` = $7/1k, up to 10 results, page contents for the first 10 results bundled free since the March 2026 pricing update). People Search carries no premium over the base rate.
- **Free tier requires no credit card**: per Exa's official pricing page, "New accounts get $20 in free credits (around 2,800 searches) and the Free Tier adds $10 in credits every month." At $0.007/lookup that is ~2,857 one-time + ~1,428/month; combined first-month allowance ≈ $30 ≈ ~4,285 lookups — enough to cover all 349 now and ~3,000 later at 1 query each with margin for retries. (A third-party "20,000 requests/month" figure circulates, but the reliable constraint is the dollar credit ÷ $0.007 ≈ ~1,428/month.)

Key constraints from the docs: for the `people` category, `includeDomains` accepts **only** `linkedin.com`; the filters `excludeDomains`, `includeText`, `excludeText`, and all date filters are unsupported and return HTTP 400. Auth accepts either `Authorization: Bearer $KEY` or `x-api-key: $KEY`.

**The one real risk**: Exa's published benchmarks and examples are US/Western; there is no published evidence on coverage quality for low-profile individuals at small/obscure Indian IT-services firms. Coverage depends on how publicly discoverable each person's profile is. Treat Indian obscure-profile hit rate as unverified — this is why fallbacks matter.

### The fallbacks (all server-side, IP-wall-immune)
- **Jina `s.jina.ai`** — server-side web search from Jina's own IPs (confirmed bypasses your wall). `GET/POST https://s.jina.ai/<query>` with `Authorization: Bearer $JINA_KEY` and `Accept: application/json` returns a JSON list of results with `url`, `title`, `content` (snippet). Supports site restriction via `?site=linkedin.com` query param or the `X-Site` header. New API keys include a large free token grant (~10M tokens under the unified pricing model that took effect May 6, 2025); search bills at a ~10,000-token floor per request, so the grant buys on the order of ~1,000 searches. Free tier rate limits are on the order of tens of RPM. Note: keyless `s.jina.ai`/`r.jina.ai` returns 401/403 from your IP — a free key is required and, per the research, unlocks the server-side search. Per Elastic's Oct 9, 2025 Business Wire release, "Elastic (NYSE: ESTC)… has completed the acquisition of Jina AI" — no effect on the free API workflow.
- **Serper.dev** — 2,500 free one-time queries, no credit card, returns real Google SERP JSON with `link` + `snippet`, supports `site:` operators in the query. Best when you need Google's actual ranking for a hard-to-disambiguate name. After free credits, $0.30–$1.00 per 1k.
- **People Data Labs (inversion route)** — free tier is "100 person/company lookups per month, 25 IP lookups. Always free," no card. The Person Enrichment API (`GET https://api.peopledatalabs.com/v5/person/enrich`) accepts name + company + locality and returns the full profile **including the LinkedIn URL** (the free-tier obfuscation only affects email/phone contact fields, not the `linkedin_url` social field). This inverts the problem — no search/snippet parsing needed — but is capped at 100/month free and PDL warns match rates are lower in markets where LinkedIn is less dominant, which bears directly on the obscure-Indian-profile risk.
- **Tavily** (1,000 credits/month free, no card), **Linkup** ($20/month recurring credit ≈ 4,000 queries, no card), and **SerpApi** (100 searches/month free, no card) are additional server-side options if the above are exhausted.

### Dead ends (excluded from the pipeline)
- **Google Custom Search JSON API** — per Google's own overview page, "closed to new customers"; new keys get `403 PERMISSION_DENIED`; full shutdown Jan 1, 2027. Unusable for a new key.
- **Brave Search API** — free tier eliminated Feb 2026. Per Marcus Schuler (Implicator.ai, June 8, 2026): "Brave removed its free Search API tier in February, replacing the zero-cost plan available since May 2023 with a credit-based billing system that charges $5 per thousand requests"; the card previously described as an "anti-fraud measure" that "will never be charged" now bills after ~1,000 queries. Violates the no-card constraint.
- **Proxycurl** — permanently shut down July 4, 2025. Confirmed by founder Steven Goh's goodbye post: "In January earlier this year (2025), LinkedIn filed a lawsuit against Proxycurl. Today, we are shutting Proxycurl down… there is no winning in fighting this." API offline.
- **Apollo.io** — free plan has **no API access** at all; API requires a paid plan. Dead for unattended API use.
- **Bing Search API** — deprecated by Microsoft on August 11, 2025 (Microsoft directs developers to Azure AI Agents).
- All HTML-scraping surfaces (DuckDuckGo/Bing/Ecosia/Mojeek/Yandex/Searx/Startpage), LinkedIn direct fetch (HTTP 999), Common Crawl for linkedin/in, and email-as-reveal-key remain ruled out per your history.

### SignalHire reveal mechanics
Per the current SignalHire Person API docs: the reveal endpoint (`POST https://www.signalhire.com/api/v1/candidate/search`, header `apikey:`) takes an `items` array where **each item can be a LinkedIn profile URL, email, phone, or 32-char UID** — a name+company pair is **not** an accepted item type, so the name→search endpoint (banned for your account) is the only name path and the LinkedIn URL stays mandatory. Two modes: async with `callbackUrl` ("maximum contact coverage" waterfall) vs `withoutWaterfall:true` (synchronous, no callback). For best hit rate on Indian mobiles, prefer async waterfall if you can host a callback URL; keep `withoutWaterfall:true` only as the no-callback fallback. Max 100 items/request, 600 elements/minute. One credit is deducted only when at least one email/phone is returned.

---

# PART A — Verdict table

| Avenue | 2026 status | Free quota (numbers) | Card? | IP-wall-immune (server-side API)? | Yields LinkedIn URL or phone directly? | Verdict |
|---|---|---|---|---|---|---|
| **Exa `/search` people category** | Live, free tier expanded Jul 2026 | $20 signup + $10/mo credit ≈ ~1,428/mo (~4,285 first month); ~$0.007 each | **No** | **Yes** | LinkedIn URL (in `results[].url`) | **PRIMARY** |
| **Jina `s.jina.ai` search** | Live (Elastic-owned since Oct 9 2025) | ~10M free tokens/new key ≈ ~1,000 searches; ~tens RPM | No | **Yes** | LinkedIn URL (in snippet `url`) | **FALLBACK 1** |
| **Serper.dev** | Live | 2,500 one-time, no reset | No | **Yes** | LinkedIn URL (SERP `link`+`snippet`) | **FALLBACK 2** |
| **People Data Labs person-enrich** | Live | 100 lookups/mo | No | **Yes** | LinkedIn URL directly (inversion) | **FALLBACK 3** |
| **Tavily** | Live (Nebius-owned) | 1,000 credits/mo | No | Yes | LinkedIn URL (content results) | Fallback (thin) |
| **Linkup** | Live | $20/mo recurring ≈ 4,000 queries | No | Yes | LinkedIn URL (results) | Fallback (thin) |
| **SerpApi** | Live | 100/mo | No | Yes | LinkedIn URL (SERP) | Fallback (thin) |
| **DuckDuckGo HTML** | Live but walled | ~8–50/day from your IP | No | No | LinkedIn URL (snippet) | Last-resort trickle |
| **Google Custom Search JSON** | Closed to new customers; shutdown Jan 1 2027 | 100/day (existing keys only) | n/a | Yes | n/a for new key | **DEAD (new key)** |
| **Brave Search API** | Free tier killed Feb 2026 | $5 metered credit only | **Yes** | Yes | — | **DEAD (card)** |
| **Apollo.io** | Live | No API on free plan | — | Yes (paid only) | — | **DEAD (no free API)** |
| **Proxycurl** | Shut down Jul 4 2025 | — | — | — | — | **DEAD** |
| **Bing Search API** | Deprecated Aug 11 2025 | — | — | — | — | **DEAD** |

**Recommendation.** Make **Exa People Search** the free primary — it is server-side (defeats the IP wall), maps name+company+city straight to a `linkedin.com/in/` URL with structured company/location fields for verification, and its no-card free credits ($20 + $10/mo) cover all ~3,349 people for roughly $0–$24. Make **Jina `s.jina.ai`** the free fallback for anyone Exa misses (server-side snippet search that also defeats the wall, ~1,000 free searches per key), with **Serper** (2,500 free) behind it and **PDL person-enrichment** (100/mo, returns the URL directly) as a zero-parsing inversion for the hardest residuals. The one paid option worth considering only if free coverage of obscure Indian profiles proves weak: simply **top up Exa credits** — at $0.007/lookup the entire 3,349 backlog costs ~$24 and the 3,000 reserve ~$21, so a single ~$25–$50 top-up removes the free-tier ceiling without changing any code. A distant second paid option — PDL Pro at $98/mo ("350 person enrichment credits… Per-credit cost: $0.28") with full contact fields — would return phone numbers directly and could bypass SignalHire for those records, but per-record economics and Indian-mobile hit rate are unproven, so prefer the Exa top-up.

---

# PART B — `SOLVE_LINKEDIN_URL.md` (paste verbatim into Claude Code)

```markdown
# SOLVE_LINKEDIN_URL.md — name+company → linkedin.com/in URL → SignalHire reveal

## 0. MISSION + HARD BANS
You are an unattended batch resolver. INPUT: a CSV of people, each with a real
full NAME (cited to a free MCA registry page), COMPANY name, company WEBSITE
domain, and CITY. GOAL: for each person, find their LinkedIn profile URL matching
  ^https?://([a-z]{2,3}\.)?linkedin\.com/in/[^/?#]+/?$
then feed only verified URLs to SignalHire reveal to obtain phone+email.
Volume: 349 people now, ~3,000 more later. ONE non-rotatable residential IP.

DO NOT re-propose or use ANY of these (already ruled out):
- SignalHire name->company search endpoint (account-banned).
- Anthropic/Claude web-search tool (budget-dead, $20 cap consumed).
- Company website /team /about /leadership scraping (done on all 450; ~19% yield).
- LinkedIn direct fetch (HTTP 999).
- Common Crawl for linkedin.com/in (near-zero coverage; CCBot blocked).
- Email-as-reveal-key (SignalHire returns "failed").
- HTML scraping of DuckDuckGo/Bing/Ecosia/Mojeek/Yandex/Searx/Startpage
  (all bot-wall this IP). DuckDuckGo HTML is allowed ONLY as a last trickle
  at <=8 queries/day (see Stage D).
- Google Custom Search JSON API (closed to new customers; a new key 403s).
- Brave Search API (free tier removed Feb 2026; requires a card).
- Proxycurl (shut down Jul 2025), Apollo free API (no API on free plan),
  Bing Search API (deprecated Aug 2025).

CORE PRINCIPLE: every resolution route below is a SERVER-SIDE API. The search
runs on the vendor's infrastructure, so the residential IP wall never applies.
Rotate SOURCES, never IPs.

## 1. CONFIG
paths:
  input_csv:        ./data/people_input.csv     # name,company,domain,city,mca_source_url
  output_csv:       ./data/linkedin_resolved.csv
  state_db:         ./state/resolver_state.json  # checkpoint/resume
  quota_db:         ./state/quota_counters.json  # per-source daily/monthly counters
  wall_log:         ./state/wall_hits.log

api_keys:  # all free-signup, NO credit card
  EXA_API_KEY:        "<PRIMARY  - dashboard.exa.ai/api-keys>"
  JINA_API_KEY:       "<FALLBACK1 - jina.ai, 2-min signup>"
  SERPER_API_KEY:     "<FALLBACK2 - serper.dev, no card, 2500 one-time>"
  PDL_API_KEY:        "<FALLBACK3 - peopledatalabs.com, 100/mo free>"
  SIGNALHIRE_API_KEY: "<existing account; 5000 reveal credits>"

quotas:  # enforce these hard caps in quota_db before every call
  exa:    { monthly_budget_usd: 30.0, cost_per_call_usd: 0.007, hard_stop_usd: 30.0 }
  jina:   { free_tokens: 10000000, token_floor_per_search: 10000 } # ~1000 searches
  serper: { one_time_credits: 2500 }
  pdl:    { monthly_lookups: 100 }
  ddg:    { daily_queries: 8 }         # last-resort trickle only
  signalhire: { per_minute_elements: 600, batch_max: 100 }

batch:
  resolve_batch_size:     50           # people per checkpoint flush
  signalhire_batch_size:  100          # max items per reveal request

## 2. RESOLUTION PIPELINE (cost-ordered waterfall; stop at first VERIFIED URL)
For each person P (name, company, domain, city), attempt stages in order.
After each stage, run Section 4 verification. If VERIFIED, record and STOP.
If a stage hits its quota or a wall, mark the source exhausted for the run and
fall through to the next stage. Log every wall/429 to wall_log.

### STAGE A — Exa People Search (PRIMARY; server-side; no IP wall)
  Endpoint: POST https://api.exa.ai/search
  Headers:  Authorization: Bearer $EXA_API_KEY
            Content-Type: application/json
  Body:
    {
      "query": "<full_name>, <company>, <city>, India",
      "category": "people",
      "type": "auto",
      "numResults": 5,
      "includeDomains": ["linkedin.com"]
    }
  Notes:
    - people category: includeDomains may ONLY contain linkedin.com;
      do NOT send excludeDomains / includeText / date filters (HTTP 400).
    - Cost $0.007/call (<=10 results, contents bundled). Increment exa usd counter.
    - Parse results[]: candidate url = results[i].url;
      verify via results[i].entities[].properties.workHistory[].company.name
      and .location (city). Also results[i].title (name + role).
  Rate: keep <= a few req/sec; stop when exa.usd >= hard_stop_usd.
  Expected yield: highest of any source; weakest for very low-profile people.

### STAGE B — Jina s.jina.ai (FALLBACK 1; server-side; no IP wall)
  Endpoint: GET https://s.jina.ai/<url-encoded-query>?site=linkedin.com
  Headers:  Authorization: Bearer $JINA_API_KEY
            Accept: application/json
            X-Respond-With: no-content   # ask for URL+title only (may be partial)
  Query template: "<full_name>" "<company>" site:linkedin.com/in
  Notes:
    - Returns JSON data[] with {url, title, content(snippet)}.
    - Budget by tokens (~10k floor/search => ~1000 searches on 10M grant).
      Increment jina token counter by max(reported_tokens, 10000).
    - Keyless requests 401/403 from this IP; the KEY makes it work server-side.
  Rate: <= ~20 RPM. Verify per Section 4 (need co-mention of company OR city).

### STAGE C — Serper.dev (FALLBACK 2; server-side; no IP wall)
  Endpoint: POST https://google.serper.dev/search
  Headers:  X-API-KEY: $SERPER_API_KEY ; Content-Type: application/json
  Body: { "q": "\"<full_name>\" \"<company>\" site:linkedin.com/in", "gl":"in", "num":10 }
  Notes: real Google SERP; parse organic[].link + organic[].snippet.
         2,500 one-time credits, no reset — spend sparingly on hard cases only.

### STAGE C2 — People Data Labs inversion (FALLBACK 3; returns URL directly)
  Endpoint: GET https://api.peopledatalabs.com/v5/person/enrich
  Headers:  X-Api-Key: $PDL_API_KEY
  Params:   name=<full_name>&company=<company>&locality=<city>&min_likelihood=6
  Notes:
    - Returns data.linkedin_url directly (free tier obfuscates ONLY email/phone,
      not the LinkedIn/social URL). No snippet parsing needed.
    - 100 lookups/month free. Use for residuals A/B/C missed. 10 req/min limit.
    - PDL match rates are lower where LinkedIn is less dominant; still verify the
      returned linkedin_url with Section 4 regex + name-slug check.

### STAGE D — DuckDuckGo HTML (LAST-RESORT TRICKLE ONLY; <=8/day)
  Only if all above exhausted for a person AND ddg.daily_queries budget remains.
  Query: "<full_name>" "<company>" linkedin
  This is the walled path; expect a block after ~8 queries — on 202/redirect/empty,
  log wall hit, set ddg exhausted for the day, and DEFER remaining people to
  tomorrow's run (Section 6). Never loop past the daily cap.

## 3. QUERY TEMPLATES + SNIPPET PARSING
Query variants (try in this order within a stage if the first yields nothing):
  1. "<full_name>" "<company>" site:linkedin.com/in
  2. "<full_name>" "<company>" (no site: — for engines that de-rank site:)
  3. "<full_name>" <city> "founder" OR "director" linkedin
  4. "<full_name>" <domain-root-word> linkedin      # e.g. company brand token
Snippet-parsing rules (apply to any snippet/content/title field):
  - Extract every substring matching:
      https?://([a-z]{2,3}\.)?linkedin\.com/in/[^\s"'<>?#]+
  - Normalize: strip query/hash/trailing slash; lowercase host.
  - Discard /company/, /school/, /jobs/, /posts/, /pulse/ URLs.
  - Keep the URL only if the SAME snippet/title/entity ALSO mentions the person's
    name AND (company OR city OR a plausible title token).

## 4. VERIFICATION RULES (never fetch LinkedIn; never trust model memory)
A candidate URL is VERIFIED only if ALL hold:
  (a) matches ^https?://([a-z]{2,3}\.)?linkedin\.com/in/[^/?#]+/?$
  (b) came from FETCHED API/search content this run (Exa result, Jina/Serper
      snippet, or PDL field). NEVER accept a URL recalled by the model or
      hand-built from a name. If a URL was not returned by a tool call, reject it.
  (c) co-mention test: the result's snippet/title/entities co-mention the
      person's name AND at least one of {company, city, a title like
      founder/director/CEO}. For Exa, satisfy this via
      entities[].properties.workHistory[].company.name == company (fuzzy) or
      .location contains city. For snippet sources, require the co-mention text
      to appear in the same snippet as the URL.
  (d) slug plausibility: the /in/<slug> should share a token with the person's
      name (first or last name), OR the source is Exa/PDL structured match with
      company confirmed. Reject slugs that match a DIFFERENT full name.
Multi-candidate ranking (when >1 URL survives):
  1. structured company match (Exa entity / PDL) > snippet company co-mention
  2. city match adds weight; title match adds weight
  3. name-slug exactness (first+last in slug) > partial
  4. prefer canonical /in/ over localized subdomain duplicates
  Assign confidence: HIGH (company confirmed + name-slug), MED (city/title
  co-mention + name-slug), LOW (single weak signal — do NOT reveal; queue for
  manual review). Only HIGH/MED proceed to SignalHire.

## 5. FEED TO SIGNALHIRE (reveal only verified URLs; protect credits)
  Endpoint: POST https://www.signalhire.com/api/v1/candidate/search
  Headers:  apikey: $SIGNALHIRE_API_KEY ; Content-Type: application/json
  Item rule: each item MUST be a verified linkedin.com/in URL. Reveal accepts
    LinkedIn URL / email / phone / UID ONLY — never send name+company (unsupported
    and the name path is banned). Do NOT send email as key (returns "failed").
  Mode:
    - Preferred (max coverage): async waterfall — include "callbackUrl":<your_url>,
      receive requestId (HTTP 201), collect POSTed results.
    - If no callback host available: "withoutWaterfall": true for synchronous
      results in the response body.
  Batch: up to 100 items/request; keep total elements <= 600/minute (429 = back off).
  Credit safety: never reveal LOW-confidence or unverified rows. One credit is
    charged only when >=1 email/phone returns, so verified-URL-only reveal
    minimizes wasted credits AND avoids calling the wrong person.

## 6. STATE / CHECKPOINT / RESUME / BACKOFF (multi-day unattended)
  - After every resolve_batch_size people, flush output_csv and update state_db
    with per-person status: PENDING|RESOLVED|REVEALED|DEFERRED|MANUAL.
  - quota_db tracks per-source consumption (exa.usd, jina.tokens, serper.credits,
    pdl.lookups.month, ddg.today). Reset daily/monthly counters by date.
  - On any 429/403/wall: exponential backoff (1s,2s,4s,...), then mark that
    source exhausted for the window and fall through; log to wall_log.
  - When ALL server-side sources are exhausted for their windows and DDG hits its
    8/day cap, set remaining people DEFERRED and exit cleanly; next run resumes
    from state_db, refills daily counters, and continues. This makes 349-then-3000
    survivable from one IP because throughput rides free API quotas, not the IP.

## 7. OUTPUT CSV SCHEMA
  name, company, domain, city, mca_source_url, linkedin_url, url_source,
  url_snippet, confidence, reveal_status
  - url_source ∈ {exa, jina, serper, pdl, ddg}
  - url_snippet = the exact fetched text/entity proving co-mention (audit trail)
  - confidence ∈ {HIGH, MED, LOW}
  - reveal_status ∈ {NOT_ATTEMPTED, REVEALED, NO_CONTACT, SKIPPED_LOW_CONF}

## 8. SELF-AUDIT HARD CHECKS (run at end of every batch; fail loud)
  [ ] Every non-empty linkedin_url matches the /in/ regex exactly.
  [ ] Every linkedin_url has a non-empty url_snippet co-mentioning name AND
      (company|city|title). Rows failing this are downgraded to LOW/MANUAL.
  [ ] ZERO URLs without a url_source in {exa,jina,serper,pdl,ddg} (i.e. zero
      model-recalled or hand-built URLs).
  [ ] Print per-source table: {queries_used, urls_found, verified, quota_left}.
  [ ] Print wall-hit log summary (source, time, http_status).
  [ ] SignalHire: revealed count <= verified HIGH/MED count (no LOW reveals).

## 9. FAILURE MODES -> MITIGATIONS (mapped to this history)
  - IP re-walled on a surface  -> rotate SOURCES not IPs; all primaries are
    server-side APIs, so the wall is irrelevant except in Stage D.
  - Common-name false positive  -> require company OR city co-mention +
    name-slug match (Section 4c/4d); never reveal LOW confidence.
  - Wasted SignalHire credit    -> reveal ONLY verified HIGH/MED URLs; never
    email-as-key; async waterfall for coverage.
  - Free quota exhausted        -> checkpoint + resume next day (Section 6);
    refill daily counters; monthly counters (Exa $10, PDL 100) reset on the 1st.
  - Exa misses obscure Indian profiles -> cascade to Jina -> Serper -> PDL;
    if systemic, top up Exa credits (~$24 for all 3,349 at $0.007) — the only
    recommended paid lever, zero code change.
```

---

## Recommendations (staged, with thresholds)

1. **Today — stand up Exa as primary.** Do the 2-minute no-card signup at dashboard.exa.ai, grab the key, and run the 349-person batch through Stage A only. At $0.007/lookup the whole batch costs ~$2.44 against your $20 signup credit. **Benchmark to watch: Exa hit rate.** If Exa returns a verified `linkedin.com/in/` URL for ≥70% of the 349, it alone carries the project.

2. **This week — wire the fallback cascade for the residual.** Add Jina (`s.jina.ai` with free key), then Serper, then PDL person-enrichment for whoever Exa missed. This is where obscure Indian small-company founders will concentrate. **Threshold:** if the combined free cascade still leaves >15% unresolved, the bottleneck is index coverage, not quota.

3. **Reveal discipline from the start.** Only push HIGH/MED-confidence verified URLs into SignalHire async-waterfall reveal. With 5,000 credits and ~3,349 people, you have head-room — do not spend it on LOW-confidence guesses that risk calling the wrong person.

4. **Scale to the 3,000 reserve the same way.** Because throughput rides free API quotas (Exa $10/month ≈ 1,428 lookups; PDL 100/month; Jina ~1,000/key) rather than your IP, the reserve is a multi-month unattended run on the checkpoint/resume loop. **The single decision point:** if Exa coverage is strong but the free monthly credit is the only constraint, a one-time ~$25–$50 Exa top-up clears the entire backlog instantly with zero code change — this is the highest-leverage paid lever and the only one I recommend by default. Escalate to PDL Pro ($98/mo, phone numbers direct, ~$0.28/record) only if you measure Exa/SignalHire *coverage* (not quota) failing on Indian mobiles.

## Caveats
- **Exa's Indian-obscure-profile coverage is unverified.** Exa's own examples and benchmarks are US/Western; there is no published data on hit rate for low-profile people at small Indian IT firms. PDL similarly warns its match rates drop "in markets where LinkedIn is less dominant." Your real hit rate can only be measured empirically on the first 349 — treat step 1's benchmark as the go/no-go for the whole approach.
- **The "20,000 requests/month" Exa free figure is unreliable.** The trustworthy constraint is the dollar credit ($10/month + $20 signup) ÷ $0.007 ≈ ~1,428/month + ~2,857 one-time. Budget against dollars, not the 20K number.
- **Jina's `no-content` header may be partially ignored.** A public GitHub issue reports `s.jina.ai` consuming far more tokens than `X-Respond-With: no-content` implies; monitor your token counter and treat the ~1,000-search estimate as a ceiling, not a guarantee.
- **Free-tier terms change fast.** Brave's free tier vanished in Feb 2026 and Google CSE closed to new customers — both mid-project-lifetime events. Re-verify Exa/Jina/Serper/PDL free terms at signup; the pipeline is built to swap sources via config, not code.
- **Serper's 2,500 credits are one-time, not monthly.** Reserve them for genuinely hard disambiguation, not bulk running.
- **SignalHire charges a credit only on a returned contact**, but a *wrong* verified URL still both wastes a credit and produces a wrong phone/email — hence the strict HIGH/MED-only reveal gate.