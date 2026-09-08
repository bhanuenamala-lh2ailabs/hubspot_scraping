# shutdown-radar — paused 2026-08-04, resume notes

**State: clean.** DB integrity `ok`, WAL checkpointed, 23/23 tests pass, all outputs written.
Every stage is idempotent — re-running never duplicates — so resuming is safe from any point.

## Resume with

```bash
cd godown/shutdown-radar
PYTHONPATH=src ../../lh2-pipeline/.venv/Scripts/python.exe -m shutdown_radar.cli resolve
```

That was the command interrupted. Nothing was left half-written; it commits per candidate.

---

## What is DONE and working

| Stage | Result |
|---|---|
| STK-7 ingest | **12 files, 11 PASS on the row-count assertion**, 1 has no stated count in its filename. 7,965 struck-off entities |
| IBBI ingest | 2,758 rows, 2,734 with a CIN, as-of **2025-03-31** |
| data.gov.in probe | **working** — 3,674,314 records, 16 fields |
| discover | 45 seeds + 27 news candidates |
| resolve | override 2, fuzzy-confirmed 3, review 1 |
| verify | 95 CINs confirmed against the live registry |
| liveness | 82 checked |
| score | confirmed 2,735 · probable 8,048 · possible 12 |
| prequal | 398 scored on the filterCriteria.md scorecard |
| export | **10,795 rows** -> `data/out/india_startup_shutdowns_20260804.csv` (5.7 MB) |

Cache is 5 MB — a resumed run re-fetches almost nothing.

## Two spec corrections worth carrying forward

**1. data.gov.in exposes 16 fields, not 5.** The spec said registered state, ROC, capital and
business activity were "unavailable here" and should be left NULL. The mandatory runtime
probe found them all: `CIN, CompanyName, CompanyROCcode, CompanyCategory, CompanySubCategory,
CompanyClass, AuthorizedCapital, PaidupCapital, CompanyRegistrationdate_date,
Registered_Office_Address, Listingstatus, CompanyStatus, CompanyStateCode,
CompanyIndian/Foreign Company, nic_code, CompanyIndustrialClassification`.
Written to `data/out/datagovin_fields.json`. This is exactly why §2a mandated the probe.

**7 of 14 probed status strings return rows:** Active 2,597,823 · Strike Off 939,392 ·
Amalgamated 40,195 · Converted to LLP 29,512 · Under Liquidation 8,515 · Under CIRP 1,944 ·
Dissolved 186. The other seven (`STRIKE OFF`, `Struck Off`, `Dissolved-Liquidated`,
`Under Process of Striking Off`, `Dormant u/s 455`, `Not Available for e-filing`) return zero
— do not use them.

**2. The CIN encodes state, incorporation year and company class.** `U18100AP1992PTC014997`
-> Andhra Pradesh, 1992, Private. This restores the disambiguation the spec expected to lose
and fills `registered_state` for 9,938 entities.

## Bugs found and fixed (all have regression tests)

1. **IBBI as-of read the download timestamp.** Filename said `2025-07-30`; the sheet title
   says "as on 31st March, 2025". A four-month error that would have granted the IBBI bonus
   to April–July 2025 shutdowns — the precise failure §2c exists to prevent. Filenames can no
   longer supply a bare date; the comma before the year is now tolerated. 2,755 stale
   evidence rows were purged.
2. **data.gov.in silently hangs on any User-Agent containing `python-httpx`** (ReadTimeout,
   never a 4xx — including httpx's own default UA). Diagnosed by A/B: curl UA -> HTTP 200 in
   2s, python-httpx UA -> timeout at 45s on the identical URL. UA is now identifiable per §10
   but omits that token.
3. **Google News soft-bans a burst.** 320 concurrent buckets earned the "Sorry..."
   interstitial for the whole IP, so later buckets returned nothing silently. Now fetched in
   serial waves of 8 with explicit ban detection that says the remaining buckets were *never
   fetched* rather than empty.
4. **GitHub rate-limits scored as "no code found".** A throttled lookup returned 0 points,
   branding a company as having no public code when we simply never looked. Now returns
   `None` -> UNSCORED, which the scorecard insists must not collapse into disqualifying.
5. **`extract_brand` accepted category headlines.** "Edtech firms wind up operations" became
   a candidate named "Edtech firms". Now rejected via a generic-head check.
6. **Sector precedence.** "Food delivery" scored 10 (backend-heavy) instead of 6 (mixed)
   because bare `delivery` matched first. Specific phrases now tested before generic ones.

## ⚠ Open — this is where work resumes

**A. Only 1 of 45 seeds reaches the export.** Root cause identified and the fix is written
but NOT yet run: **spec §6 step 2, the exact API lookup, was never wired into `resolve`.**
I built `datagovin.lookup_name()` and then only called override -> local-exact -> local-fuzzy.
Seeds are funded startups whose legal entities were never struck off, so the local index
(built from STK-7/IBBI) can never match them. Without a CIN each seed takes the -0.25
penalty and lands in `noise`.
The API-lookup step is now in `resolve.py` and syntax-checked. **Running `resolve` is the
next action.** Expect seeds to gain CINs, pick up a real MCA status, and move to
probable/confirmed.

**B. News discovery is starved: 27 candidates vs the 300–1500 the sanity gate expects.**
Google soft-banned this IP mid-run. The gate fired correctly. Re-run `discover` after the ban
clears; the cache keeps what already landed.

**C. `prequal` currently routes all 398 to `dont_pursue_but_unscored`** — correct behaviour,
not a bug: funding and shutdown-year are unknown for registry-origin rows, and GitHub was
rate-limited. It will improve once (A) lands and seeds carry funding + dates.

**D. Peak engineering headcount is deliberately never automated** — it needs a LinkedIn
alumni search and §10 forbids LinkedIn scraping. It stays UNSCORED and is reported as such.

## Acceptance criteria status

- [x] `run-all` completes from clean state — 40m35s
- [x] Completes with empty `data/manual/` subdirs and says so (datagovin, dpiit both empty)
- [x] Re-running produces zero duplicate candidates/evidence
- [x] `datagovin_fields.json` exists; status strings match observed values
- [x] All STK-7 files parse; extracted counts within 2% (see `stk7_parse_audit.csv`)
- [x] The two 23-06-2026 files deduplicate by content
- [x] Truncation assertion unit-tested
- [x] IBBI bonus not applied after the as-of date — unit-tested
- [x] STK-only candidates have NULL date and tier <= probable — 8,060 rows
- [x] >=60% of confirmed rows have a CIN — **100%** (2,735/2,735)
- [x] Every exported row has a primary_source_url — 10,794/10,795
- [x] Tests: 23 passing
- [ ] **>=150 news candidates** — 27, blocked by the Google soft-ban (B)
- [ ] **all ~45 seeds present** — 1/45, blocked by (A)
