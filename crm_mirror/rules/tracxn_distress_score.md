# Tracxn Distress Score — Ranking Logic

How the **"LH2 Ranked Targets"** tab (6,654 companies) is scored and ordered. Reconstructed from the per-row `explanation` column, which the scorer stamps into every row.

**Goal:** rank Tracxn companies (funded + unfunded) by how **distressed / dormant** they look — a shut-down or struggling company is the best candidate to sell its dormant codebase.

> This score only measures **distress** (dying + cheap + reachable). It does **not** measure whether the company owns a *buyable asset*. That second question — pre-2024 codebase vs ops data — is scored separately in [asset_fit_score.md](asset_fit_score.md) (`codebase_fit` + `opsdata_fit`), which reranks the distressed list by asset value.

## Score model
- **`composite` (0–50)** = `internal` + `external`.
- `external` is **0 for every row** (no external distress feeds wired in yet), so in practice **composite = internal**.
- **`internal`** = sum of the triggered distress signals below, **capped at 50**.

## Distress signals & weights (with source columns)
Each signal reads a specific **Tracxn funded/unfunded column** and fires on a condition:

| Signal | Tracxn column(s) read | Fires when | Weight |
|---|---|---|---|
| **Deadpooled / shut down** | `Is Deadpooled` (+ `Company Stage`, `Deadpooled Date`) | = **Yes** | **+20** |
| **Funding stale** | `Latest Funded Date` | months-since ≈ **50+** | **+20** |
| **Funding aging** | `Latest Funded Date` | months-since ≈ **24–36** (only one of stale/aging fires) | **+12** |
| **Loss-making** | `Annual Net Profit (USD)` | value **< 0** | **+10** |
| **Website down** | `Website Status` (Tracxn's own crawl) | ∈ **{404, 403, −1, non-200}** | **+10** |
| **No revenue at revenue-stage** | `Annual Revenue (USD)` + `Founded Year`/`Company Stage` | revenue **= 0** while old/funded enough to expect revenue | **+8** |
| **Very small team** | `Total Employee Count` | **≤ ~5** | **+7** |

Score is the sum of whichever fire, **capped at 50**. (Funding "stale" and "aging" are the same underlying data point — `Latest Funded Date` — at two thresholds; only one fires.) "Months-since funding" = (as-of date − `Latest Funded Date`).

**Verified example — NuShala (rank #1):** `Is Deadpooled: Yes` (+20) · `Latest Funded Date: Dec 2021` ≈ 55 mo → stale (+20) · `Annual Net Profit: −14,045` (+10) · `Website Status: 404` (+10) = **50**. Team = 12 → *no* small-team bonus.

## Confidence (`coverage`)
`coverage` = the share of the **7 tracked data points** that actually had data to evaluate (e.g. `0.571` = 4 of 7). It's a **confidence** measure, **not** added to the score — a high score with low coverage is a less certain read. Mean coverage ≈ 0.47.

## Tiers
| Tier | Composite band | Count | Meaning |
|---|---|---|---|
| **Medium** | ≈ 37 – 50 | 546 | Strong stack of signals — typically deadpooled + stale funding + loss-making + website down |
| **Low** | 0 – 32 | 6,108 | Weak/partial signals |
| **High** | above Medium | 0 | Reserved band — no company reached it (ceiling seen = 50) |

*(There's a clean gap: Low tops out at 32, Medium starts at 37.)*

## Ranking
- Sort by **`composite` descending** (most distressed first) → `rank` = 1 … 6,654.
- Composite is an integer (sum of weights), so there are many ties; ties are broken by a finer secondary ordering (confidence + sub-signal granularity).
- Row #1–79 are all **deadpooled, composite 50** (e.g. NuShala, Oye Rickshaw, Stoa).

## Which rows to actually pull for outreach
- **Deadpooled is a TARGET, not an exclusion** — a shut-down company with no acquirer is the prime candidate (dormant codebase, founders still reachable). It's the top-weighted signal on purpose.
- **Exclude `acquired` and `ipo`** — those codebases now belong to an acquirer / a public entity and aren't freely sellable.
- Work **highest `rank` first**, prefer **Medium tier**, and require a usable founder contact (`email`/`phone`/`linkedin`; `contact_source` says where it came from).
- Dedup by `domain` against the CRM mirror (`crm_mirror/data/index/by_domain.json`) — net-new only.

## Regenerating
The scored sheet is maintained upstream (the scorer writes `composite/internal/external/coverage/tier/rank/explanation`). The local copy lives at `crm_mirror/sources/tracxn/` (`sync.py tracxn`). If we ever re-implement the scorer, this weight table is the spec.
