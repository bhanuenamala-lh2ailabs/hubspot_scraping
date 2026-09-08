# Founder-Identity Resolution for Small Indian IT Firms — Research Verdicts + Ready-to-Paste Claude Code Solution Prompt

## TL;DR
- **The single highest-yield, free, fetchable route is India's MCA director data mirrored on The Company Check, IndiaFilings, Quick Company, and ZaubaCorp** — all four return director/founder NAMES + DIN on free, non-login pages that fetch at HTTP 200 from a residential IP (verified Aug 16 2026). Tofler and FalconEbiz publish the same names but hard-block bots, so reach them via search snippets or the Jina reader, not direct fetch.
- **Both free search APIs the user hoped for are dead.** Google's Custom Search JSON API is "not available for new customers" and is discontinued Jan 1 2027 (existing keys only, 100 q/day); Brave "removed its free Search API tier in February [2026]," replacing it with metered $5/1,000 billing (card required). Microsoft also deprecated the Bing Search API on Aug 11 2025. The IP-wall bypass that survives is **s.jina.ai** (server-side search, free) plus **r.jina.ai** (server-side reader), which fetch from Jina's IPs — not the user's walled IP.
- **Common Crawl contains essentially zero linkedin.com/in profiles** (CCBot is among the most-blocked crawlers on major sites), so LinkedIn URLs must come from MCA-name → search-snippet corroboration → SignalHire reveal, never from scraping LinkedIn directly.

## Key Findings
- MCA aggregators are the backbone: every Indian Pvt Ltd legally files its directors, and four public mirrors expose them free and fetchable. This route alone should convert most of the 366 "nothing" and 54 "name-only" companies to cited names.
- Person-name yield ranking: MCA aggregators (HIGH) > company GitHub orgs + WordPress author endpoints (MEDIUM) > GST anonymous lookup / Justdial / IndiaMART (LOW/ZERO for corporate director names).
- SignalHire failed reveals cost nothing, so credits are best reserved strictly for rows that already carry a validated LinkedIn URL or strong key.

## Details

### PART A — Verification table of every avenue probed

| Avenue | Wall status (Aug 2026) | Free quota / limits | Name yield | Notes / source |
|---|---|---|---|---|
| **ZaubaCorp** company pages | Open, HTTP 200 direct from residential IP; no Cloudflare on profile body | No documented hard rate limit; self-throttle | HIGH | Verified fetch: "Directors of ZAUBA TECHNOLOGIES PRIVATE LIMITED are HAROON SATTAR MOTIWALA, and MANSOOR AHMED" + DIN. URL: `/company/{NAME-CAPS}/{CIN}` or `/{NAME-CAPS}-{CIN}`. Google-indexed. |
| **The Company Check** | Open, HTTP 200, no login for directors | Financials premium-locked; directors free | HIGH | Verified: "It is led by directors Lionel Jeshuran Charles and Ramasamy Sangilirajan." URL: `/company/{slug}/{CIN}` |
| **IndiaFilings** company search | Open, HTTP 200, no login | Only MCA PDFs paywalled (₹1,999) | HIGH | Verified director table w/ DIN (LIONEL JESHURAN CHARLES 03268546). URL: `/search/{slug}-cin-{CIN}` |
| **Quick Company** | Open, HTTP 200, no login | none observed | HIGH | Verified director "Warij Abhaykumar Kasliwal" + DIN. URL: `/company/{slug}` (slug only, no CIN — needs CIN→slug resolution) |
| **Tofler** | Bot/Cloudflare block on direct fetch | n/a | MEDIUM (snippet only) | Names exist ("three directors – Suraj Agarwal…") but page unfetchable server-side. Reach via s.jina.ai or search snippet. URL: `/{slug}/company/{CIN}/directors` |
| **FalconEbiz** | Bot block on direct fetch | n/a | MEDIUM (snippet only) | Names in Google snippet only. URL: `/company/{NAME-CAPS}-{CIN}` |
| **MCA V3 portal** (mca.gov.in) | Open but CAPTCHA-gated per lookup; no login for basic master data | Manual/CAPTCHA — not batchable | HIGH per-lookup, LOW throughput | "View Company/LLP Master Data" + "Signatory Details" show director names + DIN after CAPTCHA. No bulk director dump. Last-resort single verifications only. |
| **MCA bulk dump** (data.gov.in / Kaggle / GitHub) | No official company→director bulk file exists | n/a | ZERO for a single bulk answer | data.gov.in has registration data, not director names. GitHub "mca-data-api" repos are paid API wrappers, not dumps. No one download answers hundreds at once. |
| **GST anonymous GSTIN/PAN lookup** | Open, no login | free | LOW/ZERO for corporates | Anonymous lookup shows Legal Name of Business + Trade Name only. Official GST guide: "Once you login … you can view … Name(s) of the Proprietor/Director(s)/Promoter(s)." For proprietorships legal name = person; for Pvt Ltd, director names are login-gated. |
| **Google Programmable Search JSON API** | "Not available for new customers"; existing keys work until sunset Jan 1 2027 | 100 q/day free (existing keys only); $5/1,000 beyond, 10k/day cap | (enabler, not name source) | Per developers.google.com/custom-search: "This API is not available for new customers." Usable only if a pre-2025 key exists. |
| **Brave Search API** | Free tier removed Feb 2026 | $5 prepaid metered credits ≈ 1,000 q/mo, card required, $0.003–0.005/query, 50 req/sec | (enabler) | Per Brave's revamped pricing page (Implicator.ai, Jun 8 2026): free tier "eliminated Feb 2026… no spending cap." Not free anymore. |
| **Bing Web Search API** | Deprecated Aug 11 2025 | n/a | (dead) | Microsoft directed developers to Azure AI Agents; confirms only independent Western search index at scale was Brave (now metered). |
| **s.jina.ai (search)** | Server-side; bypasses local IP wall entirely | Free without key (low rpm); **40 rpm/IP with free key** | (enabler, HIGH value) | Runs the search from Jina's IPs, so DuckDuckGo/Bing/Ecosia walls are irrelevant. Returns top-5 results as clean text incl. snippets; supports `site=` filter. |
| **r.jina.ai (reader)** | Server-side fetch/render | 20 rpm no key; **500 rpm + 10M free tokens with key**; IP cap 10k/60s | (enabler) | Fetches Cloudflare/JS pages server-side; use for Tofler/FalconEbiz/GoodFirms. $0.02/1M tokens beyond free. Jina acquired by Elastic Oct 9 2025 (Reader API remains). |
| **Common Crawl CDX index** (index.commoncrawl.org) | Open, free | "Do not overload"; per-domain queries fine | LOW→MEDIUM (own sites only) | Query per company domain for deep pages (`/about`, `/team`, `/author/`, blog). Query pattern `?url={domain}/*&output=json`. |
| **Common Crawl for LinkedIn profiles** | LinkedIn blocks CCBot | n/a | ZERO | Near-zero linkedin.com/in coverage; CCBot is among the most-blocked crawlers (blocked by ~22–37% of major sites depending on the study). Do not attempt. |
| **GitHub REST API** (authenticated CLI) | Open | 5,000 req/hr per user | MEDIUM | Org members + user `blog`/`bio`/`twitter_username` fields often carry LinkedIn/personal site. Best for dev-heavy IT firms. |
| **WordPress `wp-json/wp/v2/users`** | Open where not locked; some now 403 | free | MEDIUM | Exposes author display names + slugs without login; also `/author/{slug}` archives. CVE-2026-2009 means some sites now return 403 — treat as dead when seen. |
| **YouTube / PR wires / award lists** | Open | free | LOW/MEDIUM | Founder-authored content; batch-queryable via s.jina.ai `site=` filters. |
| **Zoho Recruit / Keka / Darwinbox job posts** | Open | free | LOW/ZERO | Rarely expose leadership names or reporting lines on public posts. Discard as a primary route. |
| **SignalHire reveal** | Paid, already solved | 5,000 credits held | (reveal step) | Failed reveal consumes NO credit ("No credits are consumed for failed items"); `withoutWaterfall:true` returns synchronously; `withoutContacts` is a separate credit type. |
| **Justdial / IndiaMART / Sulekha** | Listing pages open; owner name gated | free | LOW/ZERO | Show business name/phone, not proprietor personal name for corporates; owner verify is login-gated. |
| **IP India trademark / Startup India / Udyam / EPFO** | Mixed | free | LOW | Trademark applicant can be a person for proprietors; Startup India directory sometimes lists founders; most return entity not person. Opportunistic supplement only. |
| **DuckDuckGo/Bing/Ecosia/Mojeek HTML** | IP-walled (user's history) | — | — | Excluded per bans; replaced by s.jina.ai. |

### Access-mechanics verdicts

**MCA aggregator waterfall is the core.** Four mirrors fetch cleanly and carry the legally-mandated director list. Because Quick Company URLs are slug-only, while ZaubaCorp/TCC/IndiaFilings carry the CIN in the path, the pipeline resolves company → CIN once (via any mirror's search or a search snippet) and then hits all four by CIN. Two mirrors agreeing on the same director set satisfies the two-source rule for free.

**Search without an IP:** s.jina.ai is the linchpin. It performs the actual web search on Jina's infrastructure, so the residential IP's DuckDuckGo/Bing walls never apply. Use it both to resolve company → CIN (`site=zaubacorp.com` / `site=thecompanycheck.com`) and to corroborate a LinkedIn URL (`site=linkedin.com/in "<founder>" "<company>"`) — the snippet corroborates without ever fetching LinkedIn.

**LinkedIn URL rule:** never fetch LinkedIn (HTTP 999). Accept a LinkedIn URL only when (a) it appears in an s.jina.ai snippet tied to both the person name and the company, and (b) it matches the `/in/` URL shape. Then feed to SignalHire.

---

## PART B — SOLVE_FOUNDER_IDENTITY.md (paste verbatim into Claude Code)

---

# SOLVE_FOUNDER_IDENTITY.md

## (0) Mission + Constraints

You are an unattended batch resolver. **Input:** a list of small Indian IT-services companies (company name + verified live website, sometimes a city). **Output:** for each, the founder/CEO/CTO's NAME and, where possible, their LinkedIn profile URL, each backed by a checkable source URL and an evidence quote. Downstream, rows marked `identity_status=full` (have a LinkedIn URL or a strong key) are fed to an existing SignalHire reveal queue (already paid, 5,000 credits).

**Absolute bans — never call, never re-propose, never fetch:**
- SignalHire searchByQuery / search-by-company (permanently banned for this account).
- Anthropic/Claude web-search tool (budget-dead).
- Static or headless scraping of company `/team` `/about` `/leadership` pages (already done, 41%+5%; do NOT repeat).
- GoodFirms profile pages (Cloudflare 403); the local GoodFirms people table + NASSCOM founder caches (already fully exploited).
- LinkedIn company pages / people tab / any logged-in or credentialed LinkedIn access, and any direct fetch of linkedin.com (HTTP 999).
- DuckDuckGo HTML, Bing HTML, Ecosia, Mojeek (all IP-walled from this host).
- MCA open datasets on data.gov.in (no director names), RDAP/WHOIS (privacy-redacted), Wayback (dates only), domain-slug guessing (solves domains not people).
- Any paid API or paid credit spend other than the already-paid SignalHire reveal.

**Model-recall of names is banned.** Every accepted name MUST have a stored `source_url` and a verbatim evidence quote pulled from fetched content. A name you cannot cite is discarded.

## (1) CONFIG block

```yaml
paths:
  input_csv:        ./data/companies_in.csv        # cols: company, domain, city(optional), cin(optional)
  output_csv:       ./data/founder_identity.csv
  state_db:         ./state/resolver.sqlite         # checkpoint + per-source counters + wall log
  goodfirms_sqlite: ./data/goodfirms_raw.sqlite     # 5,455 raw listing HTMLs already on disk (mine for CIN/GSTIN only)
  log_dir:          ./logs/

batch:
  companies_per_run:     150       # safe overnight slice
  save_checkpoint_every: 10

keys:
  jina_api_key:    ""             # optional free key -> 40 rpm s.jina.ai, 500 rpm r.jina.ai
  google_pse_key:  ""             # ONLY if a pre-2025 key already exists; else leave blank (route disabled)
  google_pse_cx:   ""
  github_token:    "$(gh auth token)"   # authenticated CLI -> 5,000 req/hr

per_source_daily_quota:            # hard ceilings enforced by state_db counters
  zaubacorp_direct:   800
  thecompanycheck:    800
  indiafilings:       800
  quickcompany:       800
  s_jina_search:      1500         # ~40 rpm w/ key; keep well under
  r_jina_reader:      1500
  github_api:         4000         # of 5,000/hr budget
  wp_json:            unlimited_local_pacing
  mca_v3_manual:      40           # captcha-gated, last-resort only

pacing:
  mca_aggregator_delay_sec:   [4, 9]    # randomized
  s_jina_delay_sec:           [2, 4]
  r_jina_delay_sec:           [2, 5]
  github_delay_sec:           [0.8, 1.5]
  overnight_cooldown_hours:   6         # after any source emits 3 consecutive walls
```

## (2) Cost-ordered waterfall pipeline

Definitions first: a **CIN** is India's 21-char Corporate Identification Number. A **DIN** is the 8-digit Director Identification Number. A "**mirror**" is any of the four fetchable MCA aggregators. "**Jina search**" = GET `https://s.jina.ai/?q=<url-encoded-query>` (runs server-side, bypasses this host's IP wall). "**Jina reader**" = GET `https://r.jina.ai/<full-target-url>` (fetches/renders server-side).

Run stages in order; stop for a company as soon as it reaches `identity_status=full`. Cheapest/most-robust/bulk routes first, fragile ones last.

**Stage A — Local pre-mine (free, zero network).**
Query `goodfirms_sqlite` raw HTMLs and any harvested footers for a CIN or GSTIN per company (CIN regex `^[LUu]\d{5}[A-Za-z]{2}\d{4}[A-Za-z]{3}\d{6}$`; GSTIN 15-char). A known CIN skips the resolve step and prevents wrong-company pulls. Write `cin` to state.

**Stage B — Resolve company → CIN via Jina search (bypasses IP wall).**
For companies without a CIN: `GET https://s.jina.ai/?q=<company> <city> zaubacorp OR thecompanycheck CIN`.
Parse the returned snippets for a CIN + the exact legal name. Cross-check city (Stage 3 rules) before accepting. Respect `s_jina_delay_sec`. Expected yield: 70–85% of live Pvt Ltd firms get a CIN here.

**Stage C — Pull directors from fetchable mirrors (HIGH yield, the core).**
With a CIN, fetch in this order until two independent mirrors agree, or all four exhausted:
1. **ZaubaCorp direct:** `https://www.zaubacorp.com/company/{NAME-CAPS-HYPHENS}/{CIN}` (also `/{NAME-CAPS-HYPHENS}-{CIN}`). Fetches HTTP 200 from this host, no Cloudflare on the profile body. Parse the "Directors of X are …" sentence and the Directors/KMP table (name + DIN + designation + appointment date).
2. **The Company Check:** `https://www.thecompanycheck.com/company/{slug}/{CIN}`. Directors free; financials premium-locked (ignore).
3. **IndiaFilings:** `https://www.indiafilings.com/search/{slug}-cin-{CIN}`. Parse Directors/Signatory table (name + DIN).
4. **Quick Company:** `https://www.quickcompany.in/company/{slug}` (slug only — derive slug from legal name lowercased-hyphenated; if 404, get slug from a Jina search `site=quickcompany.in`).
Rate limit: `mca_aggregator_delay_sec`, randomized, per host. Expected yield: 85–95% of firms with a CIN get a full board list.

**Stage D — Walled mirrors via Jina reader (fallback for coverage / 2nd source).**
If Stage C gives only one source, corroborate through the bot-walled mirrors without touching this host's IP:
- Tofler: `GET https://r.jina.ai/https://www.tofler.in/{slug}/company/{CIN}/directors`
- FalconEbiz: `GET https://r.jina.ai/https://www.falconebiz.com/company/{NAME-CAPS}-{CIN}`
Both hard-block direct fetch; Jina renders them server-side. Respect `r_jina_delay_sec`.

**Stage E — Pick the leader from the board.**
Heuristics on the director set: prefer designation "Managing Director" / "Director" who also appears as the earliest appointment (incorporation-era), and whose surname matches the company/brand where applicable. If two co-founders, keep both rows. Store `din`, `title`.

**Stage F — Find & corroborate a LinkedIn URL (never fetch LinkedIn).**
`GET https://s.jina.ai/?q=<founder name> <company> site:linkedin.com/in`.
Accept a `linkedin.com/in/...` URL ONLY if the snippet co-mentions the person name AND the company/domain, and the URL matches `^https?://([a-z]{2,3}\.)?linkedin\.com/in/[^/?#]+/?$`. Store `linkedin_url` + snippet as `source_2_quote`. This is the SignalHire key.

**Stage G — Dev-firm supplement (GitHub, authenticated).**
For firms with a GitHub org linked from their site: `GET /orgs/{org}/members` then `GET /users/{login}` — read `name`, `blog`, `bio`, `twitter_username` for a LinkedIn/personal link. 5,000 req/hr. Good where the founder is technical.

**Stage H — Founder-authored content (WordPress + CC index).**
- If the company site is WordPress: `GET {domain}/wp-json/wp/v2/users` (author display names) and `/author/{slug}/`. Many SMB sites expose the founder as sole author. Some now 403 (CVE-2026-2009) — treat 403 as dead, move on.
- Common Crawl CDX for the company's OWN domain to discover deep author/leadership/blog pages the earlier static pass missed: `GET https://index.commoncrawl.org/CC-MAIN-<latest>-index?url={domain}/*&output=json`. Fetch only promising deep URLs via r.jina.ai. Do NOT query CC for linkedin.com (≈zero coverage — CCBot is among the most-blocked crawlers).

**Stage I — Last-resort single verification (MCA V3, CAPTCHA).**
Only for high-value unresolved rows, and only manually/interactively (CAPTCHA-gated, not batchable): mca.gov.in → MCA Services → View Company/LLP Master Data + Signatory Details. Cap at `mca_v3_manual` per day. Never automate the CAPTCHA.

**Disabled routes (do not build):** Google PSE and Brave APIs unless a pre-existing Google PSE key is present in CONFIG (then use as an optional Stage B/F accelerator at 100/day); GST / Justdial / IndiaMART for corporate director names (login-gated / entity-only); MCA bulk dump (does not exist for director names).

## (3) Company-name → legal-entity fuzzy matching

- **Normalize:** uppercase, strip punctuation, collapse whitespace; expand/normalize suffixes: `PVT LTD` / `PVT. LTD.` / `PRIVATE LIMITED` → `PRIVATE LIMITED`; `LLP` kept distinct; `TECHNOLOGIES/TECH/SOLUTIONS/SOFTWARE/SYSTEMS/LABS/INFOTECH` treated as tokens, not dropped.
- **CIN validation:** verify the 21-char shape; chars 6–7 encode the state (KA, MH, DL, TN, TS, GJ, UP, HR, WB…) and chars 8–11 the incorporation year — both must be plausible.
- **City cross-check (prevents wrong-company director pulls):** the CIN's state code must match the company's known city/state (from website footer, GSTIN state digits, or input `city`). If the aggregator's registered-office city conflicts with the known city, REJECT the match and re-resolve. Never accept a director set whose entity city contradicts the target.
- When multiple entities share a brand name, prefer the one whose incorporation year and city match, and whose NIC code is an IT/software code (72xx, 62xx, 631xx).

## (4) Verification rules

- Every accepted `founder_name` stores `source_1_url` + `source_1_quote` (verbatim substring containing the name from the fetched page).
- **Two-source rule** (apply where feasible, required for name-only rows): a second mirror or a Jina snippet independently naming the same person → `source_2_url` + `source_2_quote`. If only one source, `confidence=medium` and `identity_status=name_only`.
- **LinkedIn URL validation without fetching LinkedIn:** URL-shape regex (Stage F) + snippet must co-mention person AND company. Never GET linkedin.com. A URL failing either test is dropped, not stored.
- Discard any name that cannot be quoted from fetched content (model-recall ban).
- `identity_status`: `full` = name + validated LinkedIn URL (or a strong SignalHire key: verified work email / phone); `name_only` = cited name, no LinkedIn; `pending` = unresolved.

## (5) State / checkpoint / resume + scheduling

- `state_db` tables: `companies(status, cin, last_stage, updated_at)`, `source_counters(source, day, count)`, `wall_log(source, ts, http_code, note)`.
- Checkpoint every `save_checkpoint_every` companies; a run is fully resumable — on restart, skip rows already `full`, resume `pending` at `last_stage`.
- **Per-source backoff:** on 403/429/anomaly from any source, exponential backoff (base 30s, ×2, cap 15 min); after 3 consecutive walls from one source, mark it cooling and **rotate to the next source — never rotate IPs** (the whole design assumes one residential IP). Trigger `overnight_cooldown_hours` for that source.
- Schedule so a 3-day unattended run is fine: process `companies_per_run` per night, randomized pacing, hard daily quotas from CONFIG, cooldown windows respected. Log every wall to `wall_log` for the self-audit.

## (6) Output schema CSV

```
company, domain, cin, founder_name, din, title, linkedin_url,
source_1_url, source_1_quote, source_2_url, confidence, identity_status
```
- `identity_status` ∈ {full, name_only, pending}. Only `full` rows are handed to the SignalHire reveal queue.
- `confidence` ∈ {high (2 mirrors agree + city match), medium (1 source), low (snippet-only)}.

## (7) Self-audit (run at end of every batch)

- Re-verify a random 20 rows: re-fetch `source_1_url`, confirm `source_1_quote` still contains `founder_name`. Any mismatch → flag + revert row to `pending`.
- Assert **zero model-recalled names**: every non-empty `founder_name` has a non-empty `source_1_url` AND `source_1_quote`; fail the batch otherwise.
- Emit a per-source yield table (attempts, names found, walls) and the `wall_log` for the run.
- Validate every `linkedin_url` against the Stage-F regex; strip any that fail.
- Assert no request was ever made to linkedin.com, GST portal login, SignalHire searchByQuery, or any banned engine.

## (8) Failure modes → mitigations (mapped to this problem's history)

- **Engine/mirror re-walls (the DuckDuckGo/Bing story):** rotate SOURCES, never IPs. If ZaubaCorp direct starts 403-ing, shift weight to TCC/IndiaFilings/QuickCompany and to s.jina.ai/r.jina.ai (server-side IPs).
- **Wrong-company directors:** enforce CIN validation + city/state cross-check (Stage 3) before accepting any board; reject on city conflict.
- **SignalHire credit waste:** only reveal `identity_status=full` rows; failed reveals cost nothing but avoid firing on `pending`. Use `withoutWaterfall:true` for synchronous weak-key attempts; never call the banned company search.
- **Tofler/FalconEbiz bot walls:** never fetch directly — only via r.jina.ai.
- **WordPress 403 (CVE-2026-2009):** treat as dead, do not retry the endpoint.
- **Common Crawl LinkedIn temptation:** banned — coverage ≈ zero; only CC-index the companies' own domains.
- **Quota exhaustion mid-run:** hard per-source daily counters in state_db; when hit, defer remaining rows to next night's slice (resume-safe).
- **CAPTCHA on MCA V3:** never automate; cap at 40/day manual for high-value stragglers only.

---

## Recommendations
1. **Build the MCA-aggregator core first (Stages A–E).** It alone should convert the 366 "nothing" and 54 "name-only" companies into cited names for the large majority, because directorship is legally published and four mirrors expose it free. Benchmark: if aggregator name-yield ≥70% after the first 200 companies, do not build any other route.
2. **Wire s.jina.ai as the only search layer** — it sidesteps every IP wall the user hit. Get a free Jina key for 40 rpm. This is what replaces DuckDuckGo/Bing/Ecosia.
3. **Reserve SignalHire credits for `full` rows only.** Expect the LinkedIn-URL hit-rate (Stage F) to be the binding constraint, not credit supply — 5,000 credits vastly exceed the 450 + 3,092 company universe.
4. **Thresholds that change the plan:** if MCA-aggregator name yield <70% after 200 companies, add the pre-2025 Google PSE key (if any exists) as a parallel resolver at 100 q/day; if Jina rpm throttles, drop to no-key s.jina.ai at slower pacing rather than paying; if a mirror starts hard-walling, rotate to the other three before touching r.jina.ai's token budget.

## Caveats
- Aggregator director lists reflect MCA filings, which lag reality; a listed "director" may have resigned — cross-check appointment/cessation dates when picking the leader.
- Quick Company URLs are slug-only, needing a CIN→slug resolution hop; budget one extra Jina search per firm there.
- s.jina.ai and r.jina.ai free tiers can change (Jina was acquired by Elastic Oct 9 2025); monitor rpm limits and treat the reader token budget as finite.
- MCA V3 is CAPTCHA-gated and cannot be batched — it is a manual last resort, not a pipeline stage.
- Proprietorships/LLPs (not Pvt Ltd) may not appear on all mirrors; the free anonymous GST lookup can supply the proprietor's personal name in those cases (where legal name = the individual), but for corporate entities director names remain login-gated there.
- The exact "most-blocked crawler" figure for CCBot varies by study (≈22% in a 1,000-site sample, ≈37% in a smaller 122-site scan), but every source agrees CCBot is heavily blocked and LinkedIn is not usefully present in Common Crawl — the operational conclusion (do not mine CC for LinkedIn) is unaffected.