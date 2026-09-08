# BUILD SPEC — `shutdown-radar` (FINAL v3)

**Supersedes all prior versions.** Every source fact below was verified by hand. Do not substitute assumptions.

**Goal:** A deduplicated, confidence-scored CSV of Indian companies — VC-funded *and* bootstrapped — that shut down between 2024-01-01 and today.

**Executor:** Claude Code. Build and run end-to-end. Design is settled. Ask only if a credential or file is missing.

---

## 0. Non-negotiables

- Python 3.11+, single repo, `uv` or `venv`.
- Stack: `httpx`, `pydantic`, `typer`, `feedparser`, `rapidfuzz`, `pdfplumber`, `openpyxl`, `dnspython`, `tenacity`, `python-dateutil`, `rich`. SQLite via stdlib. No `playwright`.
- Async I/O via `httpx.AsyncClient`, bounded concurrency (semaphore, default 10), `tenacity` backoff on 429/5xx.
- **Fully resumable.** Every stage checkpoints; re-running never duplicates.
- **Cache all HTTP** to `.cache/`, key = SHA256(url + body). No re-fetch unless `--no-cache`.
- Secrets from `.env`. `.env` gitignored.
- **Provenance mandatory.** An unsourced exported row is a bug.
- **Never fabricate.** Null is correct; invented is a defect.

---

## 1. Layout

```
shutdown-radar/
  pyproject.toml  .env.example  README.md
  data/
    manual/
      datagovin/     # per-state CSVs
      ibbi/          # XLSX + PDF
      mca_stk/       # 10 STK-7 C-PACE PDFs
      dpiit/         # optional
    seeds/
      seed_shutdowns.csv
      brand_cin_overrides.csv
    out/
  src/shutdown_radar/
    cli.py db.py models.py http.py resolve.py scoring.py export.py
    sources/
      newsrss.py gdelt.py media_rss.py trackers.py
      datagovin.py ibbi.py mca_stk.py dpiit.py liveness.py
  tests/
```

---

## 2. VERIFIED SOURCE FACTS

### 2a. data.gov.in Company Master Data

```
RESOURCE_ID: 4dbe5667-7b6b-41d7-82af-211562424d9a
Endpoint:    https://api.data.gov.in/resource/{RESOURCE_ID}
Updated On:  22/07/2026
Bulk zip:    NOT AVAILABLE. Downloads need a mandatory Company State Code filter.
```

**Documented fields — only these five:**
```
CORPORATE_IDENTIFICATION_NUMBER   <- CIN
DATE_OF_REGISTRATION
COMPANY_NAME
COMPANY_STATUS
COMPANY_CLASS
```

Binding consequences:
- Registered state, ROC, capital, business activity, registered office are **unavailable here**. Keep the `entity` columns, leave NULL. May be filled from STK-7 if those PDFs carry a state column.
- Filters are exact-match, single-field, no OR: `filters[COMPANY_STATUS]=<v>`, `filters[CORPORATE_IDENTIFICATION_NUMBER]=<cin>`, `filters[COMPANY_NAME]=<exact>`.
- Paginate with `offset` / `limit`.

**Mandatory runtime probe — first action of `verify` and any bulk pull:**
1. Unfiltered call, `limit=1`. Dump `field` array and `total` to `data/out/datagovin_fields.json`.
2. `field` metadata may list more than the five above and contains the real state-code field name. **Use what the API reports.**
3. Probe each `COMPANY_STATUS` spelling: `Strike Off`, `STRIKE OFF`, `Strike off`, `Struck Off`, `Under Liquidation`, `Under CIRP`, `Amalgamated`, `Dissolved`, `Dissolved-Liquidated`, `Under Process of Striking Off`, `Dormant u/s 455`, `Not Available for e-filing`. Keep only those returning `total > 0`.
4. Abort with a clear error if zero probes succeed — schema changed.

### 2b. Bulk ingest — CSV-first, API fallback

Preferred: per-state CSVs in `data/manual/datagovin/`, loaded by `ingest-manual`, `source='datagovin_csv'`.

**Truncation assertion — mandatory.** The preview-download silently row-caps. For each CSV, compare row count to the API `total` for that state filter. Short → LOUD warning in `run_report.md` + automatic API-paginator fallback for that state.

API fallback: shard by state code, `limit=1000` (degrade on error), checkpoint `(state_code, last_offset, done)` in `backfill_progress`, max 3 concurrent states, background job. **Main pipeline never blocks on it.**

Priority: Karnataka, Maharashtra, Delhi, Telangana, Tamil Nadu, Haryana, Uttar Pradesh — then the rest.

### 2c. IBBI

```
data/manual/ibbi/
  "CIRPs Ending With Order of Liquidation as on 31st March 2025"  -> XLSX (openpyxl)
  "Quarterly Newsletter Jan-Mar 2026"                             -> PDF, aggregates only
```

**Currency guard, binding:** the liquidation list is as-of **2025-03-31**. For candidates with `shutdown_date > 2025-03-31`, absence from this file is **not evidence of anything**. Apply the IBBI bonus only when `shutdown_date <= as_of_date`. Parse the as-of date from filename/title (never hardcode) so newer files drop in cleanly. Store on every IBBI evidence row; surface the coverage gap in `run_report.md`.

The newsletter has no company-level rows — do not attempt to extract entities from it. Optionally parse headline aggregates for the report; nothing more.

### 2d. MCA STK-7 — C-PACE consolidated national lists

Per-ROC publishing ended ~2022–23 when strike-off centralised under ROC-C-PACE. All 2024+ files are consolidated national lists.

**10 files in `data/manual/mca_stk/`, ~7,337 companies total:**

| Date | Companies | States |
|---|---|---|
| 28-07-2026 | 904 | 30 |
| 21-07-2026 | 444 | 29 |
| 14-07-2026 | 1028 | 30 |
| 30-06-2026 | 680 | 28 |
| 23-06-2026 | 665 | 28 |
| 23-06-2026 | 927 | 28 |
| 15-06-2026 | 819 | 27 |
| 26-05-2026 | 909 | 29 |
| 12-05-2026 | 767 | 27 |
| 07-01-2025 | 194 | 23 |

Listing page (provenance only; direct URLs are tokenised and unextractable):
`https://www.mca.gov.in/content/mca/global/en/data-and-reports/rd-roc-info/companies-struck-roc.html`

Parser requirements:
- **Row-count assertion.** Each title states its company count. Parse it and assert extracted rows match. Mismatch >2% → LOUD warning in `run_report.md`. This is the only ground-truth check in the pipeline — silent table-parse failure must not pass unnoticed.
- **Stream page-by-page.** 900+ rows per file; never load whole PDFs into memory.
- Extract company name + CIN + state (if a state column exists). Populate `entity.registered_state` from it when present — this is the *only* source of state data, and it partially restores resolve-stage disambiguation.
- Two files share date 23-06-2026. Dedupe on content, not filename or date.
- Skip and log unparseable files; never crash.
- **Handle an empty directory gracefully** — the pipeline must complete regardless.

STK-5: negligible (2 non-C-PACE entries in window). Ignore.
STK-6: published one PDF per state per batch date, several hundred files in window, site pagination unreliable at volume. **Not ingested in v1.** Keep the `evidence.kind='stk56'` branch and its `+0.30` weight in the scoring code, dormant, for a later targeted pull. Sampling confirmed all 8 priority states appear in every batch date checked (5/5), so a surgical later pull is viable.

### 2e. STK date semantics — critical

**Strike-off date is not shutdown date.** Involuntary strike-off (non-filing) lags cessation by 2+ years; voluntary C-PACE exits lag 3–6 months. The 2026-dated files therefore skew toward companies that ceased operating in 2023–2024 — squarely in window, but undateable from the file alone.

- Never write STK publication date into `shutdown_date`. Store as `evidence.as_of_date` only.
- An STK match confirms death; it does **not** date it.
- Candidate whose only evidence is an STK match with no news-derived date: `shutdown_date` NULL, tier capped at `probable`, rationale must state that timing is unestablished.

### 2f. DPIIT (optional)

If a CSV exists in `data/manual/dpiit/`, load into `dpiit_startup`. Use as a false-positive filter: match → small confidence bump; non-match → **no penalty** (many real startups were never recognised).

---

## 3. Schema

```sql
CREATE TABLE IF NOT EXISTS candidate (
  id INTEGER PRIMARY KEY,
  brand_name TEXT NOT NULL,
  brand_name_norm TEXT NOT NULL UNIQUE,
  first_seen_at TEXT NOT NULL,
  discovery_source TEXT NOT NULL   -- google_news|gdelt|media_rss|tracker|manual_seed|stk7|ibbi
);

CREATE TABLE IF NOT EXISTS evidence (
  id INTEGER PRIMARY KEY,
  candidate_id INTEGER NOT NULL REFERENCES candidate(id),
  kind TEXT NOT NULL,              -- news|registry|ibbi|ibbi_voluntary|stk7|stk56|liveness|dpiit|manual
  source_url TEXT, source_name TEXT, published_at TEXT,
  as_of_date TEXT,                 -- point-in-time sources (IBBI, STK)
  snippet TEXT,                    -- <=300 chars, audit only
  matched_pattern TEXT, raw_json TEXT,
  fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS entity (
  cin TEXT PRIMARY KEY,
  legal_name TEXT NOT NULL, legal_name_norm TEXT NOT NULL,
  company_status TEXT, company_class TEXT, date_of_registration TEXT,
  registered_state TEXT,           -- from STK-7 only
  roc TEXT,                        -- rarely available
  source TEXT, fetched_at TEXT
);

CREATE TABLE IF NOT EXISTS candidate_entity (
  candidate_id INTEGER NOT NULL REFERENCES candidate(id),
  cin TEXT NOT NULL REFERENCES entity(cin),
  match_score REAL NOT NULL,
  match_method TEXT NOT NULL,      -- override|exact|fuzzy_token_set|manual
  is_confirmed INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY(candidate_id, cin)
);

CREATE TABLE IF NOT EXISTS liveness (
  candidate_id INTEGER PRIMARY KEY REFERENCES candidate(id),
  domain TEXT, dns_resolves INTEGER, http_status INTEGER, http_final_url TEXT,
  ssl_expired INTEGER, rdap_status TEXT, wayback_last_capture TEXT,
  liveness_score REAL, checked_at TEXT
);

CREATE TABLE IF NOT EXISTS dpiit_startup (
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, name_norm TEXT NOT NULL,
  state TEXT, sector TEXT, recognition_date TEXT
);

CREATE TABLE IF NOT EXISTS backfill_progress (
  state_code TEXT PRIMARY KEY, last_offset INTEGER NOT NULL DEFAULT 0,
  total INTEGER, done INTEGER NOT NULL DEFAULT 0, updated_at TEXT
);

CREATE TABLE IF NOT EXISTS scored (
  candidate_id INTEGER PRIMARY KEY REFERENCES candidate(id),
  confidence REAL NOT NULL, tier TEXT NOT NULL,
  shutdown_date TEXT, shutdown_year INTEGER, reason TEXT,
  sector TEXT, city TEXT, funding_usd TEXT, investors TEXT,
  rationale TEXT NOT NULL, scored_at TEXT NOT NULL
);
```

Index `entity.legal_name_norm`, `candidate.brand_name_norm`, `evidence.candidate_id`, `dpiit_startup.name_norm`.

---

## 4. CLI

```
shutdown-radar init
shutdown-radar discover [--since 2024-01-01] [--source all|news|gdelt|rss|trackers]
shutdown-radar ingest-manual
shutdown-radar backfill [--states KA,MH,...] [--background]
shutdown-radar resolve [--min-score 88] [--limit N]
shutdown-radar verify [--limit N]
shutdown-radar liveness [--limit N]
shutdown-radar score
shutdown-radar export [--tier confirmed,probable] [--format csv,json,xlsx]
shutdown-radar review
shutdown-radar run-all
```

`run-all` is the only command the human types. Completes unattended, degrades gracefully on empty `data/manual/` subdirectories.

---

## 5. DISCOVER

**Seeds first, zero network.** Load `data/seeds/seed_shutdowns.csv` (~45 known 2024–2026 shutdowns), `discovery_source='manual_seed'`, one evidence row each.

**Google News RSS:** `https://news.google.com/rss/search?q={Q}&hl=en-IN&gl=IN&ceid=IN:en`, monthly buckets 2024-01 → today via `after:` / `before:` inside `q`:
```
"startup shuts down" India
"startup ceases operations" India
Indian startup "winds up" operations
Indian startup "shuts shop"
startup "files for insolvency" India NCLT
startup "returns capital to investors" India
Indian startup "pulls the plug"
Indian startup "calls it quits"
"deadpool" Indian startup
startup shutdown Bengaluru OR Mumbai OR Delhi OR Gurugram OR Hyderabad OR Pune OR Chennai
```

**GDELT 2.0:** `https://api.gdeltproject.org/api/v2/doc/doc?query={q}%20sourcecountry:IN&mode=ArtList&maxrecords=250&format=json&startdatetime=...&enddatetime=...`

**Media RSS:** Inc42, Entrackr, YourStory, Moneycontrol, Mint, VCCircle, ET Tech, Business Standard.

**Trackers** (static HTML, parse don't render): `entrackr.com/tags/shutdown`, `entrackr.com/tags/startups`, Inc42 annual shutdown articles + layoff tracker.

**Shutdown regex** (compile once, case-insensitive):
```
shuts?\s+(down|shop)|shut\s+down|shutting\s+down|ceas(e|ed|es|ing)\s+operations|
winds?\s+(up|down)|wound\s+up|shutter(s|ed)?|discontinu(e|ed|ing)\s+operations|
files?\s+for\s+(insolvency|bankruptcy)|insolvency\s+proceedings|NCLT|CIRP|
liquidation|struck\s+off|strike[- ]off|voluntary\s+winding\s+up|
returns?\s+capital\s+to\s+investors|shuts?\s+operations|
lays?\s+off\s+(entire|all)\s+(team|staff)|deadpool(ed)?|
bites?\s+the\s+dust|calls?\s+it\s+quits|pulls?\s+the\s+plug|closes?\s+shop
```

**Normalisation:** leading noun phrase before trigger verb → lowercase, strip `pvt ltd|private limited|ltd|limited|inc|technologies|labs|india`, strip punctuation, collapse whitespace. Blocklist generics ("Indian startups", "edtech firms"). Drop <3 chars. Dedupe on `brand_name_norm`.

**Sanity gate:** 300–1500 news candidates expected. Under 150 → regex or bucketing is broken; fix before proceeding.

**Note on scale:** STK-7 ingestion adds ~7,337 registry-origin candidates with no brand name and no news coverage. These are the bootstrapped long tail. They enter as candidates with `discovery_source='stk7'` and `brand_name` = legal name. Expect the final export to be dominated by them.

---

## 6. RESOLVE (brand → CIN)

Order:
1. **Override table** — `data/seeds/brand_cin_overrides.csv` (`brand_name,cin,legal_name`). Pre-seed known mismatches (Otipy → Crofarm Agriproducts, Koo → Bombinate Technologies).
2. **Exact API lookup** — normalised brand plus `{brand} PRIVATE LIMITED`, `{brand} TECHNOLOGIES PRIVATE LIMITED`, `{brand} LABS PRIVATE LIMITED`, `{brand} INDIA PRIVATE LIMITED`, `{brand} SOLUTIONS PRIVATE LIMITED`.
3. **Local fuzzy index** — `rapidfuzz.process.extract`, `token_set_ratio`, `score_cutoff=85`, top-5, against both `entity.legal_name_norm` and STK-7-derived names.
4. **Disambiguate** using only what exists: `DATE_OF_REGISTRATION <= founding_year + 1`, `COMPANY_CLASS`, name score, `registered_state` where STK-7 supplied it, DPIIT membership if loaded.

Auto-confirm only at score ≥92 **and** unique **and** registration-date check passes. Otherwise → `review_queue.csv`.

Never silently take the top fuzzy hit. Unconfirmed matches never export as `confirmed`. Expect a heavier review queue than a state-aware matcher would give — known cost of the 5-field schema, partially offset by STK-7 state data.

---

## 7. VERIFY · LIVENESS · SCORE

**Distress statuses**, strongest first, validated against the probe:
```
Dissolved · Dissolved-Liquidated · Under Liquidation · Under CIRP
Strike Off · Under Process of Striking Off · Amalgamated
Not Available for e-filing · Dormant u/s 455
```
`Active` is not proof of life — record it, don't let it veto. `Converted to LLP` is not a shutdown — exclude.

**Liveness** (only where registry confirmation is absent): domain from brand (`.com`/`.in`/`.co`/`.ai`) or news links → DNS (NXDOMAIN strong) → HTTP 10s timeout (refused / persistent 5xx / parked patterns `sedoparking`, `afternic`, `buy this domain`) → SSL `notAfter` long past → RDAP `https://rdap.org/domain/{d}` (`client hold`, `redemption period`, `pending delete`) → Wayback CDX `http://web.archive.org/cdx/search/cdx?url={d}&output=json&limit=-1`. Combine to `liveness_score` 0–1.

**Scoring:**
```
+0.45  IBBI CIRP/liquidation by CIN   [ONLY if shutdown_date <= as_of_date]
+0.40  STK-7 struck-off match by CIN
+0.40  status in {Dissolved, Dissolved-Liquidated, Under Liquidation, Under CIRP}
+0.32  status in {Strike Off, Amalgamated}
+0.30  IBBI voluntary liquidation
+0.30  STK-5/6 notice match           [dormant in v1]
+0.30  >=2 independent reputable news sources
+0.22  status = Under Process of Striking Off
+0.20  curated tracker page (Inc42/Entrackr)
+0.18  1 reputable source (Inc42/Entrackr/ET/Mint/Moneycontrol/YourStory/BS/VCCircle)
+0.15  liveness_score >= 0.8
+0.08  liveness_score 0.5-0.8
+0.05  DPIIT-recognised match
-0.25  no CIN resolved
-0.15  single low-quality/aggregator source only
```
Cap 1.0. Tiers: `confirmed` ≥0.75 · `probable` 0.50–0.75 · `possible` 0.30–0.50 · `noise` <0.30.

Apply the §2e cap: STK-only evidence with no news date → tier ceiling `probable`.

`rationale` must name specific evidence — "STK-7 2026-06-15 + MCA status Strike Off + site NXDOMAIN". Never a bare number.

---

## 8. EXPORT

`data/out/india_startup_shutdowns_{YYYYMMDD}.csv`:
```
brand_name, legal_name, cin, company_status, company_class, date_of_registration,
registered_state, tier, confidence, shutdown_date, shutdown_year, sector, city,
funding_usd, investors, reason, domain, dns_resolves, wayback_last_capture,
dpiit_recognised, evidence_count, primary_source_url, all_source_urls, rationale
```

Also emit:
- `review_queue.csv` — unconfirmed matches + `possible` tier, confidence desc.
- `run_report.md` — per-stage and per-source counts, tier distribution, **sources returning zero**, parse failures, STK-7 row-count assertion results per file, CSV truncation warnings, IBBI coverage-gap note, backfill progress, top-20 sample.
- `stk7_parse_audit.csv` — one row per STK-7 file: filename, stated company count, extracted count, delta, pass/fail.

---

## 9. Acceptance criteria

- [ ] `run-all` completes from clean clone with `.env` + current `data/manual/`
- [ ] Completes with any `data/manual/` subdirectory empty, and says so in the report
- [ ] Re-running produces zero duplicate candidates and zero duplicate evidence
- [ ] `datagovin_fields.json` exists; all status strings match observed values
- [ ] All 10 STK-7 files parse; extracted counts within 2% of stated counts (audit CSV proves it)
- [ ] The two 23-06-2026 files deduplicate correctly by content
- [ ] CSV truncation assertion fires on a deliberately truncated test file
- [ ] IBBI bonus not applied to candidates dated after 2025-03-31 (unit test)
- [ ] STK-only candidates have NULL `shutdown_date` and tier ≤ `probable` (unit test)
- [ ] ≥150 news-derived candidates; all ~45 seeds present
- [ ] ≥60% of `confirmed` rows have a non-null CIN
- [ ] Every exported row has ≥1 `primary_source_url`
- [ ] Tests: normaliser, regex (positive + negative), scoring, dedupe, resolver disambiguation, IBBI date guard, STK date guard, truncation assertion, STK row-count assertion

---

## 10. Hard rules

- Source returns zero → **fail loudly in `run_report.md`**, never silently continue.
- Never fabricate a CIN, date, funding figure, or status string.
- No LinkedIn scraping. No CAPTCHA bypass on mca.gov.in.
- **Company-level data only.** Director names are personal data under the DPDP Act — do not collect, store, or export. Excludes MCA's disqualified-directors and directors-of-struck-off-companies lists entirely.
- Respect `robots.txt`, identifiable User-Agent with contact info, 1 req/sec per domain.
- Government data (data.gov.in / MCA / IBBI) is reusable under GODL-India. Do not scrape Zaubacorp, Tofler, or similar resellers.


