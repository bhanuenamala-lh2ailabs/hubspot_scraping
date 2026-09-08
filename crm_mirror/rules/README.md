# LH2 CRM — Sources, Rules & Mirror

This folder is the source-of-truth for **how leads get into HubSpot** and the **local mirror** that makes deduping cheap. One MD file per input source.

## The four input sources

| Source | What it is | HubSpot pipeline | Tag (`scraped_type` / `lead_source`) | Rules file |
|---|---|---|---|---|
| **IT-services scrape** | GoodFirms directory crawl of Indian IT-services firms (`lh2-pipeline`) | Scraped | `scraped_type = ITservices` | [it_services_scrape.md](it_services_scrape.md) |
| **Tracxn** | Funded + unfunded startups exported from Tracxn, ranked into targets | Scraped | `scraped_type = Distressed startups` | [tracxn_sheet.md](tracxn_sheet.md) |
| **Private Codebase Tracker** | Yash/team's curated deal tracker (Google Sheet) | Scraped | `scraped_type = ITservices` or `Distressed startups` (by `IT-`/`S-` prefix) | [private_codebase_tracker.md](private_codebase_tracker.md) |
| **OutFlo** | LinkedIn outreach campaigns (India + Indonesia) | Campaign | `lead_source = Outflo Outreach – India / Indonesia` | [outflo_to_hubspot.md](outflo_to_hubspot.md) |

## Ranking / scoring logic

| Model | What it answers | File |
|---|---|---|
| **Distress score** | is this Tracxn company dying, cheap, reachable? (ranks all 6,654) | [tracxn_distress_score.md](tracxn_distress_score.md) |
| **Asset-fit** (`codebase_fit` + `opsdata_fit`) | do they own a **buyable asset** — a pre-2024 codebase and/or ops data? | [asset_fit_score.md](asset_fit_score.md) |

Distress finds the dying companies; asset-fit reranks them by *what's actually worth buying* (two separate scores because a codebase buy and an ops-data buy want opposite things). See [asset_fit_score.md](asset_fit_score.md).

## HubSpot pipelines & stages (both use the same SOP cadence)

**Pipelines:** `Scraped` (id `default`) · `Campaign` (id `2425754306`).

**Stages (SOP):** Cold Call → Call Attempted → Interested → GMeet Fixed → Script Shared → Script Results Received → Commercial Negotiation → Deal Contract Signed → Data Migration Done → Metadata Matched → Payment Initiation → Closed/Won, plus `Dead/{Stage}/{Reason}` stages.

**Owners (hubspot_owner_id):** Shreyas `166420402` · Ishpreet `166322228` · Shobit `166262056` · Yash `166483631` · Ashish `166322218` · Bhanu `95472647`.

## The local mirror (`crm_mirror/`)

```
data/
  deals.json        every HubSpot deal + its contact_ids/company_ids + key props
  contacts.json     every associated contact (name, email, phone, linkedin)
  companies.json    every associated company (name, domain)
  index/
    by_linkedin.json   linkedin_url -> deal_id   (dedup key: OutFlo)
    by_domain.json     domain       -> deal_id   (dedup key: scrape / tracker / Tracxn)
    by_name.json       norm(name)   -> deal_id
  snapshots/        dated mirror summaries
outflo/
  leads.json        latest full OutFlo pull (all 3 campaigns)
  snapshots/        dated OutFlo pulls (daily)
sync.py             pull HubSpot + OutFlo -> refresh data/ + index/
```

## Dedup rule (the whole point)

> **Dedup on DEALS, never on companies or contacts.** (Rule set 2026-08-03.)
> A company record with no deal is **not** a worked lead — HubSpot accumulates company/contact
> records from associations, cleanups and imports. Keying dedup on them silently hides valid
> leads (it hid 9stacks, Singularity Automation, Bric Spaces and Logipe until caught).
> `analysis/weekly/_data/hubspot_index.json` is therefore built **from deals only**.

**Before creating any deal, look it up in the local index — not HubSpot:**
1. OutFlo → `index/by_linkedin.json[norm_linkedin]`
2. Scrape / Tracxn / Tracker → `index/by_domain.json[domain]`, fall back to `index/by_name.json[norm_name]`
3. If found → **update** that deal id; else → **create** and **append it to `deals.json` + the index** as part of the push.

## Sync cadence

- `python sync.py all` — full refresh (HubSpot mirror + OutFlo pull). **Run weekly**, and before any large push.
- `python sync.py outflo` — OutFlo only. **Run daily** (we pull OutFlo often).
- Push scripts also write each new deal into the mirror as they go, so it stays current between full syncs.

_This is the only chat used to push to HubSpot, so this mirror + these rules stay authoritative here._
