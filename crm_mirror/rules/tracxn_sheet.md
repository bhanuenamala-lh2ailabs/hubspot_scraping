# Tracxn → HubSpot

**Distressed / target startups** sourced from a **Tracxn** export, ranked into an outreach list, and pushed to the **Scraped** pipeline as `Distressed startups`.

Sheet: **"Tracxn"** (`12BLV3nv1d9Is4UHN113YVhiTBNilHe-9phIMMCEKS4A`) — SA has read access.

## Sheet structure

| Tab | Rows | What it is |
|---|---|---|
| **funded** | ~3,344 | Funded companies from Tracxn — 63 cols (funding, valuation, investors, revenue, EBITDA, key-people emails, employee count, LinkedIn, Tracxn score, deadpooled flag, …) |
| **unfunded** | ~3,357 | Unfunded companies, same schema |
| **LH2 Ranked Targets** | ~6,655 | The **processed, ranked target list** — see columns below |
| **LH2 Ranked Targets Outreach Tracker** | ~6,655 | Outreach-facing subset: rank, company, domain, city, founded_year, acquired, founder_name, email, phone, linkedin, contact_source, explanation |
| Sheet3 | ~82 | scratch |

**LH2 Ranked Targets columns:** `rank, company, source_tab (funded/unfunded), domain, cin, city, stage, founded_year, composite, internal, external, coverage, tier, deadpooled, acquired, ipo, founder_name, email, phone, linkedin, Comments, contact_source, explanation`.

## Selection rules (what to pull)
- Pull from **LH2 Ranked Targets** (already scored/ranked by a **distress score** — see [tracxn_distress_score.md](tracxn_distress_score.md)), best `rank` / `tier` / `composite` first.
- **`deadpooled = Y` is a TARGET, not an exclusion** — a shut-down company with no acquirer is the prime codebase candidate (it's the top-weighted distress signal).
- **Exclude** rows where `acquired = TRUE` or `ipo = TRUE` (codebase now belongs to an acquirer / public entity — not freely sellable).
- Require a usable **founder contact** (`email`/`phone`/`linkedin` present) — `contact_source` says where it came from.
- **Net-new** — skip if `domain` already in the mirror `index/by_domain.json` (already in HubSpot).

## Push rules (→ HubSpot)
- **Pipeline:** Scraped (`default`). **Stage:** `Cold Call`.
- **Tag:** `scraped_type = Distressed startups`.
- **Owner + PoC:** the assigned caller.
- **Company** by `domain`; **Contact** = founder (name, email, phone, linkedin); **Deal** named by company.
- **Dedup key:** `domain` → mirror `index/by_domain.json` (fall back to `by_name.json`).
- Enrichment: contacts usually already carry email/phone from Tracxn; top up missing phones via Signalhire if needed.

## Note
- This is the source of the **Distressed startups** book. As of last sync there were **513** Distressed deals in HubSpot (500 live) — the bulk being Shreyas's enriched cold-call pool (a large un-enriched batch was cleaned out on 2026-07-28; keep only leads with mobile **and** email in Cold Call).
