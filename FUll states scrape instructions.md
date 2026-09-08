# SCRAPE_IT_DIRECTORIES.md — harvest Indian IT-company directories → deduped company+website universe

## 0. MISSION
Scrape the directories in Section 3 into ONE deduplicated CSV of Indian IT/software companies, each with its own website domain, ready to feed the existing prequalification pipeline. Your unit of output is a **company with a resolved website domain** — a row without a domain is a second-class row (kept, flagged, but not counted as a win). Volume matters: 20 directories at ~200 companies each beats a perfect scrape of one. Do NOT qualify, score, or profile companies here — that is a downstream stage you already have. Your job is breadth, clean domains, and honest provenance.

The source-research is already done; Section 3 is its output. Do NOT re-scrape these already-mined sources — dedupe against them but never emit them as new: GESIA, HYSEA, GTech, iTAAP, NASSCOM, GoodFirms.

## 1. CONFIG (edit before running)
```yaml
paths:
  prior_universe:   ./data/existing_universe.csv     # already-held companies (GESIA/HYSEA/GTech/iTAAP/NASSCOM/GoodFirms + prior weeks); dedupe target. If absent, skip that dedupe.
  crm_export:       ./data/DEALS_MASTER.csv           # current HubSpot export; dedupe so we never re-surface in-CRM firms. If absent, skip.
  out_companies:    ./out/it_directory_universe.csv   # THE deliverable
  out_rejects:      ./out/rejects.csv                 # dropped rows + reason (keep overlap counts, don't silently drop)
  out_source_report:./out/source_yield.csv            # per-directory: attempted, parsed, with_domain, new_after_dedupe, overlap%, barrier
  state_db:         ./state/scrape_state.sqlite        # checkpoint + per-source counters + redirect cache
  raw_html_dir:     ./raw/                             # cache every fetched page (audit + re-parse without re-fetch)

http:
  user_agent:       "Mozilla/5.0 (compatible; LH2-research/1.0)"
  base_delay_sec:   [2, 5]        # randomized politeness delay between requests to the SAME host
  max_retries:      3
  backoff_base_sec: 30            # x2 each retry
  timeout_sec:      30
  respect_robots:   true          # Section 6 lists the robots-blocked hosts — skip those, don't fight

render:
  headless_when_needed: true      # only for JS dirs (Technopark official grid, some aggregators). Prefer static mirrors first.

batch:
  checkpoint_every: 1             # checkpoint after every listing page — these runs get interrupted
```

## 2. PIPELINE ORDER
```
For each directory in Section 3, in priority order (P1 -> P4):
  A. Fetch listing pages (use the pagination pattern given) -> cache raw HTML to raw_html_dir
  B. Parse rows -> {company_name, website_raw, city, phone, email, profile_url, source}
  C. Resolve website_raw -> clean registrable domain (Section 4)   <- value-critical step
  D. Normalize + dedupe within-source, then vs prior_universe + crm_export (Section 5)
  E. Append survivors to out_companies; drop the rest to out_rejects with a reason
  F. Write per-source stats to out_source_report
Stop per source: last page reached, OR hard barrier hit (log, move on), OR pagination pattern breaks.
```
Resumable: on restart, skip pages already cached in raw_html_dir and companies already in state_db. Never re-fetch a cached page.

## 3. THE DIRECTORIES
Fields: **url · region · ~members · websites_listed · loading · barrier · note.** `websites_listed=no` means names/phones only — still scrape it (names feed a domain-resolution backfill, Section 4.D), but mark every row `domain_source=backfill_needed` and count it separately.

### P1 — verified, on-profile, real domains as plain text (scrape first)
1. **Infopark Kochi** — infopark.in/companies — Kerala — ~582 — **yes** — paginated HTML `?page=1..10`, server-rendered — none — *Each block has a plain-text domain node after the company name + a `/companies-profile/{slug}` link. No JS. Also pull variants `/companies/infopark-kochi-phase-1`, `/infopark-thrissur`, `/infopark-cherthala`.*
2. **Technopark Trivandrum (static mirror)** — technoparktoday.com/technopark-information/technopark-companies/ — Kerala — ~370+ — **yes** — plain HTML table (name+address+phone+email+website) — none — *Use this BEFORE the official grid. If stale/down, fall back to #3.*
3. **Technopark Trivandrum (official)** — technopark.in/company-list — Kerala — ~370+ — yes (on profiles) — **JS/AJAX grid** — none — *Only if mirror fails. Capture the underlying XHR/JSON call and hit that directly; else headless-render and paginate the filter.*
4. **STPI Bengaluru registered units** — blr.stpi.in/registered-units.html — Karnataka — ~174 — **yes (older extract had websites — verify live)** — plain HTML — none — *If the live page dropped the website column, treat as names-only backfill.*

### P2 — on-profile associations; confirm the website field on first fetch, then commit
5. **ITAO – IT Association of Odisha** — itaoodisha.org/corporate.php (also /life.php) — Odisha — ~300+ — **unverified** — plain HTML (.php) — none — *Two member classes: corporate + life. Confirm a website field renders; if not, names-only backfill.*
6. **SIDA – Software Industries Development Association** — sidatn.org (find "View Members") — S. Tamil Nadu / Madurai — few hundred — **unverified** — unverified — none — *Resolve the exact members-page URL from the nav first.*
7. **RITO – Rajasthan Information Technology Organization** — rito.org.in — Rajasthan / Jaipur — unverified — **unverified** — plain HTML — none.
8. **Mohali IT City IT Companies Association** — itcitymohaliassociation.com — Punjab / Mohali — unverified — **unverified** — unverified — none.
9. **ESC India** — escindia.in/our-members/ — Pan-India — claims 2,000–2,200 exporters — **public page may show only office-bearers** — HTML — none — *If the full list is gated, take only public content and move on; don't break a gate.*

### P3 — on-profile but names-only or bot-guarded (backfill domains via Section 4.D)
10. **Vidarbha Industries Association — software/hardware** — via-india.com/member_directory/software-hardware/ — Nagpur — unverified — **no** (name/products/email/phone) — paginated HTML — **bot detection** — *Headless + slower pacing. Names-only -> backfill.*
11. **STPI Noida units** — noida.stpi.in/units-list — UP/Noida — ~255 — **no** — HTML table — **robots.txt disallow** — *Respect robots; SKIP automated scrape. Note for manual pull only.*
12. **STPI national statutory-services units** — stpi.in/en/list-units-registered-under-statutory-services — Pan-India — large — **no** — HTML — none — *Names -> backfill.*
13. **AIT Bengaluru business directory** — ait-bengaluru.in/business-directory/ — Karnataka — ~439 — **no** — search-driven HTML ("10 random of 439") — none — *Skews to resellers/SIs; lower value. May need a search-param sweep to enumerate all 439.*

### P4 — high-volume B2B aggregators (domains behind tracked redirects — resolver mandatory, Section 4.C)
14. **TechBehemoths India** — techbehemoths.com/companies/india — Pan-India — ~10,793 — **partial (redirect)** — static HTML, **PATH pagination** `/companies/india/{n}` (n≈1..450); city pages `/companies/{city}` — none major — *Static, no headless for names. Resolve each "Visit Website" redirect. Highest raw volume.*
15. **Clutch India IT industry** — clutch.co/in/developers/information-technology-industry — Pan-India — ~3,110 — **yes (redirect)** — server HTML `?page=N` — **Cloudflare + rate limiting** — *Hardest. Conservative rate, headless with challenge handling. If per-record cost exceeds TechBehemoths, mine only top-rated profiles manually and skip automated paging.*
16. **Sortlist India** — sortlist.com/web-development/india-in (+ /app-development/india-in, /s/software-development/india-in) — Pan-India — ~898 (web-dev vertical) — **featured cards via redirect** — Next.js SSR `?page=N#directory-content` — rate limiting — *Parse SSR HTML; real domain on profile pages/featured cards.*

**Do NOT emit (already mined / rejected upstream):** GESIA, HYSEA, GTech, iTAAP, NASSCOM, GoodFirms, DSCI (enterprise + token wall), SEAP Pune (logos only), NEA (robots + mixed), CODISSIA (all-sector), AIITA (education/individuals), TiE chapters (individuals), RCTA/MAIT (hardware/traders), CSI (individuals), Startup India front-end (login-gated — if wanted, use the API Setu endpoint apisetu.gov.in/public/api/startupindia, not the React site).

## 4. WEBSITE / DOMAIN RESOLUTION (the value-critical step)
Produce a clean **registrable domain** in `domain` and record how in `domain_source`.

**4.A Plain-text domain (Infopark, Technopark mirror, STPI-BLR):** strip protocol/`www`/path/query, lowercase, keep registrable domain (`2basetechnologies.com`). `domain_source=listed`.

**4.B Anchored href on listing/profile page:** take `href`, apply 4.A. If the href is the directory's own domain (a profile link, not the company site), open the profile page and extract the outbound website link there. `domain_source=profile`.

**4.C Tracked redirect (TechBehemoths / Clutch / Sortlist "Visit Website"):** the visible href is a tracker, not the real domain. Resolve with a HEAD/GET, redirects disabled, following the `Location` chain until a non-aggregator host. Cache tracker->domain in state_db so identical trackers resolve once. If resolution fails after 2 tries: keep the row, `domain=""`, `domain_source=redirect_unresolved`. On success `domain_source=redirect`.

**4.D Names-only sources (STPI national, VIA, AIT, any P2 lacking the field):** do NOT guess a domain. Emit the row with `domain=""`, `domain_source=backfill_needed`, all other fields populated. These go to the existing downstream domain-resolution step — hand off a clean name+city, do not invent a URL. Never slug-guess or fabricate here.

**Reject as a domain (send to rejects, `reason=non_company_domain`):** linkedin.com, facebook.com, twitter/x.com, instagram, youtube, justdial, indiamart, sulekha, google.com, blogspot, wordpress.com, the directory's own domain, url-shorteners. A social profile is not a company website.

## 5. NORMALIZE + DEDUPE
- **Name normalize (for the match key only; keep original in `company_name`):** trim, collapse whitespace, strip trailing legal/suffix tokens pvt/private/ltd/limited/llp/technologies/solutions/software/systems/labs/inc.
- **Primary dedupe key = registrable domain.** Same domain = same company; keep the most-populated row, and UNION the `source` list (a firm in 3 dirs -> `source="infopark;techbehemoths;clutch"` — provenance matters and multi-source presence is a mild quality signal).
- **Secondary key (domain empty) = normalized name + city**, fuzzy token-set >=0.92, to catch "Foo Technologies" vs "Foo Tech Pvt Ltd" same city.
- **Dedupe vs `prior_universe` and `crm_export`** on domain first, then name+city. Matches -> rejects with `reason=already_held` / `reason=already_in_crm`. Keep the counts (we want the overlap % per source, like the ~26% last run).

## 6. BARRIERS — respect, don't fight
- **robots disallow (STPI Noida, NEA):** skip the automated scrape; log `barrier=robots_skip`. Don't route around it.
- **Cloudflare / bot detection (Clutch, VIA):** one headless attempt at normal pace; on repeated challenge, log `barrier=cloudflare`, save partial, move on. No IP rotation, no solver services.
- **Login/token gate (ESC full list, Startup India front-end):** take only public content; for Startup India use the API Setu endpoint. Log `barrier=auth_gate`.
- General rule: a directory that costs more than it yields is not worth a bespoke fight — log the barrier, bank the partial, next source. Breadth over completeness.

## 7. OUTPUT SCHEMA (out_companies.csv)
```
company_name, domain, domain_source, city, state_region, phone, email,
source, profile_url, first_seen_run, notes
```
- `domain_source` in {listed, profile, redirect, backfill_needed, redirect_unresolved}
- `source` = semicolon-joined directory keys where the company appeared
- Real-`domain` rows are the deliverable; `backfill_needed`/`redirect_unresolved` rows go to the downstream domain-resolution step, not the bin.

## 8. SELF-AUDIT (run at end; print + fail loud on a broken check)
1. `out_source_report` has a row per directory attempted: {attempted_pages, rows_parsed, with_domain, new_after_dedupe, overlap_pct, barrier}.
2. No output row has a rejected/social domain (Section 4 blocklist).
3. count(out_companies) + count(rejects) == total rows parsed (nothing silently vanished).
4. Domain fill-rate reported overall and per source; flag any P1/P2 source with <50% fill (parser missed the website field — re-inspect that source's HTML).
5. Zero fabricated domains: every non-empty domain traces to `listed`/`profile`/`redirect` evidence in raw_html_dir or the redirect cache — never a guess.
6. Sample 15 random `domain=listed` rows: re-open cached HTML, confirm the domain string is actually on the page.
7. De-dupe sanity: no two output rows share a registrable domain.

## 9. FAILURE MODES -> MITIGATIONS
- **Parser returns 0 with_domain for a "yes" source** -> markup changed; check 8.4 catches it; re-inspect that source's cached HTML, don't discard the run.
- **Redirect resolver hammering aggregators** -> cache tracker->domain; dedupe trackers before resolving; pace per host.
- **Pagination pattern breaks mid-run** (path vs query, page cap) -> detect empty/duplicate page, stop that source cleanly, log last good page for resume.
- **Interrupted run** -> raw_html_dir + state_db make it resumable; never re-fetch cached pages.
- **Over-collection of off-profile firms** (aggregators list big enterprises too) -> fine here; profile-filtering is downstream. Do not filter by size/type in this scraper except to drop non-company/social domains.
- **A source turns out gated/empty** -> log barrier, bank partial, move on; one weak source never blocks the other 15.

## 10. RUN
Process P1->P4. Print a one-line progress note per page (`infopark p3/10 — 61 rows, 58 domains`). Checkpoint every page. At the end, print `out_source_report` and top-line totals (companies with domains, backfill-needed, overlap %) for a human sanity pass before handoff to prequalification.