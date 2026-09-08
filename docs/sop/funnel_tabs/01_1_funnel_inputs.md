# 1. Funnel inputs

Five standing sources feed the two pipelines.

| Source | Feeds | What it is |
|---|---|---|
| Private Codebase Tracker | Scraped | IT-services sheet, upstream via service account |
| Tracxn sheet | Scraped | startups, upstream via service account |
| GoodFirms scrape | Scraped | IT services |
| OutFlo outreach | Campaign | startups |
| LinkedIn campaign | Campaign | IT services |

**LinkedIn Sales Navigator** is *not* a standing input. It was a one-off CSV of 49 rows
uploaded on 21 July. The 35 rows that never moved past Cold Call were retired on 5 August;
the 8 that were worked remain.

**Known data gap:** 337 of 1,013 live deals carry no `lead_source` at all, and Tracxn-sourced
deals carry no Tracxn label anywhere. Every funnel count by source is understated until that
is backfilled.

---
