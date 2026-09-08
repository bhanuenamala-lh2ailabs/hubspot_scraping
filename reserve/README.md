# Reserve — candidate pools checked against HubSpot, not yet worked

Everything here has been cross-checked against live HubSpot deal names as of **8 Sep 2026**.
"Untouched" means the company doesn't already exist as a deal — it does **not** mean the
contact info is enriched or callable yet. Most of these need the full pipeline run first:
founder search → LinkedIn profile confirm → India-location check → phone/email enrichment
(Apollo and/or SignalHire) → push. See `crm_mirror/rules/*.md` and `godown/*/`'s scripts for
the pattern — nearly every sourcing exercise this session followed the same shape.

| File | Rows | What it is |
|---|---|---|
| `prequal_reserve_2655_untouched.csv` | 2,655 | GoodFirms/NASSCOM-scored IT-services companies. Same scoring pipeline as the whale list below (`rank`, `score`, `owned_ip`, `pre2024_grade` columns) — median score ~35/100, only ~8% have a contact name yet. The whale list already skimmed the highest-scoring 30 off this pool. |
| `shutdown_radar_10829_untouched.csv` | 10,829 | Indian startup **shutdowns**, sourced from `godown/shutdown-radar/` with real corporate-registry evidence (CIN, company status, shutdown date). 2,735 rows are `tier=confirmed`, the rest `probable`. This is the real "distressed/dead startup" pool — separate from the whale/reserve pool above, which is *active, healthy* companies. Only 402 rows have a prequal score computed. |
| `tracker_it_services_firms_442.csv` | 442 total (284 untouched, rest already dealt with — file kept whole for context) | The pre-HubSpot "IT Services Firms" tab from the master tracker (`crm_mirror/sources/_audit/private_codebase_tracker.json`). Has richer fields than the others — `Founder(s)`, `Founder LinkedIn (verified)`, `Contact Number`, `Status`, `Notes`, `SPOC` — some rows may already have call history from before the HubSpot migration even though the company itself isn't a HubSpot deal. Check `Notes` before treating as cold. |
| `whale_list_27_NEVER_PUSH_TO_HUBSPOT.csv` | 27 | ⚠️ **Standing rule: this list must never be pushed to HubSpot, under any circumstance.** High-value IT-services targets (same scoring pipeline as `prequal_reserve`, top-scoring 30, minus 3 since found already in HubSpot). 25 of the 27 already have a confirmed real decision-maker (name + LinkedIn, company-match verified) sitting ready for phone/email enrichment whenever Apollo/SignalHire credits allow — see the description column and cross-reference `godown/prequal/`'s scripts for how they were found. Ask before doing anything with this list beyond local enrichment. |
| `GUJARAT_IT_FIRMS_MASTER.csv`, `LEADS_10_untouched.csv`, `LEADS_200_founder_needed.csv`, `LEADS_200_never_tried.csv`, `linkedin_netnew_26_2026-08-12.csv` | small | Older, smaller working batches from mid-August, kept for reference — same "untouched against HubSpot" status, lower priority than the four above. |

**Before using any of these:** re-run the HubSpot dedup check yourself — this snapshot is
already stale the moment new leads get pushed. The pattern (core-normalize company name,
compare against a fresh pull of `/crm/v3/objects/deals/search`) is used identically across
almost every script in `godown/`.
