# LH2 — Lead Sourcing & HubSpot Operations

**Source of truth for where everything lives.** Read this before adding a file.

LH2 acquires two dormant assets from Indian companies: **pre-2024 software codebases**
(from IT-services firms and dead startups) and **internal operating know-how / ops data**.
This repo sources, qualifies, enriches and pushes those leads into HubSpot, then measures them.

---

## 🔑 The rule

| | |
|---|---|
| **Live truth for deals/contacts** | **HubSpot** — never a spreadsheet or CSV here |
| **Local mirror of HubSpot** | `crm_mirror/data/` (refresh: `python crm_mirror/sync.py hubspot`) |
| **How each source works** | `crm_mirror/rules/*.md` — one file per input source |
| **Weekly performance** | `analysis/weekly/<YYYY-Www>/README.md` |
| **Anything in `exports/`** | a **point-in-time artefact**. Never a source of truth — regenerate, don't edit |

---

## 📁 Directory map

```
.env                          credentials (hubspot_key, hubspot_kartik, signal_hire, anthropic, outflo)
lh2-pipeline-9982aa4422f5.json  Google service-account key
gmail_oauth_client.json       Gmail OAuth desktop client — see docs/reference/VCF_LEAD_NOTIFIER_SETUP.md
build_dashboard.py  index.html  dashboard_data.json    ← CI deploys these from ROOT (do not move)

lh2-pipeline/     the scraper engine (crawl → build → enrich → score → export)
  config.yaml       gates, cities, source toggles
  data/pipeline.sqlite   raw_listings · companies · people
  src/lh2_pipeline/ crawl/ transform/ enrich/ judge/ export/

crm_mirror/       HubSpot mirror + push machinery
  sync.py           pull HubSpot / OutFlo / Tracxn into data/
  data/             deals.json, contacts.json, companies.json + index/ (dedup keys)
  rules/            ← HOW EACH SOURCE WORKS (start here)
  sources/          local copies of Tracxn + preserved research
  enrich/           push + enrichment scripts (see below)

analysis/         measurement
  KPI_DEFINITIONS.md      the KPI contract (ULR/QR/CR/FAR/ER/MR/AFD/WR)
  weekly/weekly_report.py runs the weekly analysis
  weekly/<YYYY-Www>/      one folder per week
  weekly/_data/           raw pulls + caches (regenerable)

docs/
  sop/          caller SOPs & flowcharts (CALLER_SOP, OPSDATA_SOP, COmpanyOpsDataFlow…)
  reference/    LEAD_SOURCING_PROBLEM_BRIEF, SA_GOOGLE_ACCESS, outflo-api-reference…
  archive/      superseded PDFs, screenshots, scratch

exports/        point-in-time outputs — regenerable, never edit by hand
  linkedin_audiences/   LinkedIn contact-match CSVs
  lead_batches/         historical caller batches
  source_files/         inbound spreadsheets we were given

godown/         active scratch workspace — NOT a source of truth
  one subfolder per sourcing exercise (cad_leads_2/, india_startups_ops/, shutdown-radar/,
  prequal/, nasscom/, ...). The .py scripts in here are real and reusable; the .json/.csv
  outputs sitting next to them are regenerable intermediate artifacts of a specific run
  (raw scrapes, profile dumps, search results) and are gitignored — re-run the script that
  produced them if you need them again. `godown/prequal/prequal_out/reserve.csv` and
  `godown/shutdown-radar/data/out/` are the two exceptions worth knowing about — see `reserve/`.

temporary/      inbox — drop a file here to be enriched/deduped/pushed, then it's done.
  Nothing in here is a source of truth either; treat it as a working surface, not storage.

reserve/        curated copies of the untouched-against-HubSpot candidate pools worth working
  next — see reserve/README.md for what's in each and the standing rules on how to use them
```

---

## 🔁 Lead sources (`lead_source` on the deal)

The original five, still active:

| Source | What | Rules | Target |
|---|---|---|---|
| **GoodFirms scrape** | crawler over Indian IT-services directories | [`it_services_scrape.md`](crm_mirror/rules/it_services_scrape.md) | codebases |
| **Tracxn sheet** | funded/unfunded startup export, distress-ranked | [`tracxn_sheet.md`](crm_mirror/rules/tracxn_sheet.md) · [`tracxn_distress_score.md`](crm_mirror/rules/tracxn_distress_score.md) | codebases |
| **Deadpool waves** | dead startups by sector cohort — highest mobile-hit rate we have | [`deadpool_waves.md`](crm_mirror/rules/deadpool_waves.md) | codebases |
| **Private Codebase Tracker** | the team's curated deal sheet | [`private_codebase_tracker.md`](crm_mirror/rules/private_codebase_tracker.md) | codebases |
| **OutFlo** | LinkedIn outreach campaigns (India + Indonesia) | [`outflo_to_hubspot.md`](crm_mirror/rules/outflo_to_hubspot.md) | both |

Added since (`lead_source` values, no separate rules doc yet — see deal `description` for
per-batch provenance):

| Source | What |
|---|---|
| **`Apollo Search ( IT Services )`** | Apollo people-search finds the founder/CEO at a prequal-scored company (`godown/apollo_reveal`); SignalHire does the phone reveal |
| **`Founder Search ( IT Services )`** | Google/LinkedIn founder discovery over IT-services company lists |
| **`CAD_salesNav`** | CAD/architecture/structural-engineering firms — Apify Google Maps discovery + founder search (`godown/cad_leads_2`) |
| **`distressed_live`** | Startup founders, 30–500 headcount, engineering team confirmed (`godown/india_startups_ops`) |
| **`Linkedin Campaign ( Distressed Startups )`** | Inbound — LinkedIn lead-gen form submissions, "engineering workflows form" |
| **`maxheadcount200`** | Distressed startup founders from a Sales-Nav export, headcount-capped |

Scoring: [`asset_fit_score.md`](crm_mirror/rules/asset_fit_score.md) (`codebase_fit` + `opsdata_fit`)

## 🎯 HubSpot portals

| Portal | ID | Key | Purpose |
|---|---|---|---|
| **Main** | 246754894 | `hubspot_key` | codebase acquisition — Scraped + Campaign pipelines |
| **Ops-Data (Kartik)** | 246897735 | `hubspot_kartik` | ops-data acquisition — "Company Ops Data" pipeline (29 stages) |

> When referring to the second one, say **"kartik hubspot"** — otherwise "HubSpot" means the main portal.

---

## ▶️ Common commands

```bash
# refresh the local mirror of HubSpot
python crm_mirror/sync.py hubspot          # also: outflo | tracxn | all

# scrape → gate → enrich → score → export
python -m lh2_pipeline.cli run             # inside lh2-pipeline/

# enrich net-new IT firms and push callable ones to a caller
python crm_mirror/enrich/enrich_and_push_it.py --owner <id> --target 60 --batch 10

# weekly analysis (creates analysis/weekly/<YYYY-Www>/README.md)
python analysis/weekly/weekly_report.py --pull

# verify a company's real headcount before pushing
python crm_mirror/enrich/verify_headcount.py --test

# email a caller a .vcf of every contact on a newly-assigned deal
python crm_mirror/enrich/lead_vcf_notifier.py --init      # ALWAYS first — baselines, sends nothing
python crm_mirror/enrich/lead_vcf_notifier.py --dry-run
```
Setup for the email transport: [`VCF_LEAD_NOTIFIER_SETUP.md`](docs/reference/VCF_LEAD_NOTIFIER_SETUP.md)

**Owner IDs (main portal):** Yuktha `96573782` · Lamiya `96574824` · Ishpreet `166322228` ·
Shobit `166262056` · Ashish `166322218` · Bhanu `95472647`

---

## ⚠️ Before any push — always

1. **Dedup** against `crm_mirror/data/index/` (`by_domain` / `by_name` / `by_linkedin` /
   `deal_names` ← **a deal is the dedup unit**; a company record with no deal doesn't count)
2. ~~Exclude the LinkedIn ad audience~~ — **void as of 2026-08-03**: that campaign was abandoned, nobody was contacted, and those 1,000 are fair game (record: `crm_mirror/holding/linkedin_1000_untouched.json`)
3. **Verify headcount** (SignalHire `total` ≥ 50) — GoodFirms' size band is wrong ~10% of the time
4. **Only push callable leads** — a real **+91** phone, or an explicit email-only decision
5. **Name the deal after the COMPANY**, never the person — the company is the pointer.
   (The ~241 person-named Campaign deals on Yash Wani are legacy and stay as they are.)

## 📌 Known constraints
- **SignalHire**: credits are fine; the **daily *search* quota** is the real limit (HTTP 402)
- **GoodFirms** re-crawls return the same ~5,456 rows — new supply needs new sources (Clutch is built but off)
- **HubSpot API**: ~625k calls/day on the main portal — never a constraint
