# _archive — old root-level CSVs, sorted out of the way

These were loose at the repo root, cluttering it. Nothing here was deleted — just moved and
split into two folders, based on a HubSpot dealname check run on 8 Sep 2026:

## `already_in_hubspot/`
Every company in these files already exists as a HubSpot deal (or the file *is* a direct
HubSpot export — `DEALS_MASTER.csv`, `DEALS_NOTES.csv`, `DEALS_ENGAGEMENTS.csv`,
`DEALS_TRANSITIONS.csv` are literal pulls of live HubSpot data, not a separate source of
truth — see the root README's rule: HubSpot is always the live truth, never a CSV here).
Kept for historical reference only.

## `discarded/`
Old one-off exports and working files superseded by later, cleaner batches — e.g.
`tobe_top100_enriched.csv` is a stale 34%-matched subset of `tobe_enriched.csv`, which is
100% already in HubSpot; `wiza_export (2).csv` is a broad raw pull that was never curated
further; the `SOURCE_FUNNEL*.csv` files are point-in-time funnel snapshots superseded by
`analysis/weekly/`. None of this is source-of-truth data — don't build on it, regenerate
from HubSpot instead if you need current numbers.

`companies.csv` at the repo root was **not** moved — it's the attached file for
`INTERN_TASK.md`'s take-home exercise and needs to stay there.
