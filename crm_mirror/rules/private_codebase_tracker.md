# Private Codebase Tracker → HubSpot

The team's **curated deal tracker** (Google Sheet) — deals already in conversation, at various stages. Migrated to the **Scraped** pipeline, preserving each deal's real stage and metadata.

Sheet: **"Private Codebase Tracker"** (`1B9in9qK1V3IyjoyjYSqwn0gGRyoP9qVlMBGKKheoEhM`), tab **`Pipeline Tracker`** (gid 411280464). Enrichment lives in the **`IT Services Firms`** tab; LoC/PRs/prices in the **`DB`** tab.

## Which rows → what tag
- Name prefix **`IT -` / `IT-`** → `scraped_type = ITservices`.
- Name prefix **`S -` / `S-`** → `scraped_type = Distressed startups`.
- No prefix (e.g. a US intro) → `ITservices` (flag it).
- **Skip** rows where `Category = Company Ops` (ops work, not codebase deals).

## Stage mapping (Current Stage → SOP stage)
| Sheet Current Stage | HubSpot stage |
|---|---|
| Initial Talk | Interested |
| Script Shared | Script Shared |
| Script Output Received | Script Results Received |
| Agreement Shared | Deal Contract Signed |
| Deal Closed | **read the remark** — only Closed/Won if payment done; else Data Migration / Contract Signed |
| Catalogued | Commercial Negotiation |
| On Hold | its underlying stage + noted (no On-Hold property) |
| Dropped | `Dead/*` (reason from remark) |

**Always read the Remarks** — "Deal Closed" ≠ contract+migration+payment done. Price mentions in remarks → `deal_value_range`.

## Fields captured
- **Owner + PoC** = the sheet's **POC** (Shobit/Ishpreet/Ashish/Yash), mapped to owner id.
- **LoC / PRs / Projects / cost** from the Pipeline Tracker columns + the **DB** tab (Hot deals → expected price, Closed → paid price). *DB $ cells are `"$ 2,000.00"` — parse as float, don't strip to `200000`.*
- **Remarks → deal Notes.** **Action Items → Tasks** (assigned to POC, due = Next Follow-up).
- **Metadata / script links** → `metadata_link` property + note (many cells are "Click Here" with no actual URL — only capture real links).
- **hs_priority** from the Priority column.

## Dedup & phase deals
- **Dedup key:** company **name** (fuzzy) / `lh2_domain` → mirror `index/by_name.json` / `by_domain.json`. Many already exist → **update in place**.
- Phase deals: "Serpent Consulting **1** / **2**" etc. are **separate deals** (don't collapse); phase-2 metrics are its own (don't inherit phase-1's).
- Watch for **pre-existing duplicates** in HubSpot (e.g. two "Serpent Consulting" deals) — reconcile, keep the data-rich one.

## Note
- This tracker gets new rows over time; on each pass, diff against the mirror and push only **new** companies (last full migration: 49 deals; +9 later).
