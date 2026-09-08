# Research brief: SignalHire `searchByQuery` API quota / limits

Hand this to a research agent. We need authoritative answers on how SignalHire's **search**
quota works, so we can plan throughput. Section 4 is the list of questions. Sections 1–3 are
everything we've observed empirically so the agent can reconcile findings against real behaviour.

---

## 1. Context — what we're doing

We use SignalHire's **Person API** (server-side, `apikey` header) in two steps:

1. **`POST /api/v1/candidate/searchByQuery`** — takes a query like
   `{currentCompany, currentTitle, location, size}` and returns matching people:
   ```json
   { "requestId": 41142721, "total": 4, "profiles": [ {"uid":"...","fullName":"...","location":"...","experience":[...]} ], "scrollId": "FGluY2x1..." }
   ```
   Each profile carries a 32-char `uid`. No contact data in this response
   (`contactsFetched: false`).

2. **`POST /api/v1/candidate/search`** — the **reveal** step. Takes `{items:[uid], withoutWaterfall:true}`
   and returns the person's phone(s) + email(s). This consumes **reveal credits**.

These are **two separate pools** — a **search quota** (for step 1) and **reveal credits**
(for step 2). We can see reveal credits via `GET /api/v1/credits` → `{"credits": 4915}`. We
have **found no equivalent endpoint that reports the remaining *search* quota**.

Account: a standard paid SignalHire API plan (exact tier below is what the agent should help
pin down). We hold ~5,000 reveal credits.

## 2. What we observed today (2026-08-17)

- We ran `searchByQuery` **~304 times** in one day (one call per company we were enriching,
  plus ~7 manual probes).
- The **first ~300 calls returned HTTP 200** with valid results (the company filter works well
  — e.g. `currentCompany:"Zealous System"` returned exactly 4 people, all at that company).
- At **~call 304, it began returning HTTP 402.** All subsequent `searchByQuery` calls 402'd.
- **Reveal (`/candidate/search`) kept working fine** throughout, and reveal credits only
  dropped from ~5,000 to 4,915 — so the 402 is on the **search** pool, not reveal.

## 3. What our own historical notes say

- Weeks earlier, an internal note quoted a **"4,000/day search limit"** — but that came from a
  **stale database row** and we flagged it as untrusted at the time.
- The **observed** rate back then was **"~300/day."**
- Today's **~304 → 402** matches that ~300 observation almost exactly, and contradicts the
  4,000 figure.
- The quota **does reset over time**: `searchByQuery` was fully exhausted weeks ago, then
  worked again today — so it refills. **We have NOT timed the reset boundary** (could be a
  calendar-day reset, a rolling 24h window, or another cadence — unknown).

**Net of our own data:** the search cap is **~300 per reset cycle** (two independent data
points agree), and it resets — but the exact **cadence** and the **plan-dependence** are
unconfirmed.

## 4. Questions we need answered (authoritatively, from SignalHire docs / support / pricing)

1. **Is the `searchByQuery` limit a DAILY quota?** What is the exact **reset cadence** — 24h
   rolling, calendar-day (which timezone?), monthly, or per-billing-cycle?

2. **What is the exact search-quota number**, and is it **fixed or plan-dependent**? Our
   observed ceiling is ~300/cycle — is that a standard tier limit, and what tiers offer more?

3. **Is `searchByQuery` quota genuinely separate from reveal credits?** (Our data says yes —
   reveal kept working after search 402'd.) Confirm the two-pool model.

4. **What exactly does HTTP `402` mean on `searchByQuery`?** Is it strictly "quota exhausted,
   wait for reset," or can it also mean "out of a paid balance you can top up"? i.e. is the
   search quota **rechargeable/purchasable**, or purely time-reset?

5. **Does pagination cost quota?** `searchByQuery` returns a `scrollId`. If we paginate through
   more results of the *same* query via `scrollId`, does each page **count as another search**
   against the quota, or is one query (all its pages) **one unit**? (Critical — it changes
   whether we spend 1 or N quota per company.)

6. **Is there an API endpoint that reports remaining SEARCH quota** (analogous to
   `/api/v1/credits` for reveal)? We couldn't find one. If none, is the only signal the 402?

7. **What does the `size` parameter cost?** Does `size:10` vs `size:50` consume more quota, or
   is quota purely per-*call* regardless of result count?

8. **Bulk / higher-tier options:** does SignalHire offer an API/Bulk plan with a **much higher
   search quota** (thousands/day), and at what price? We need to run ~3,000 more companies
   (1 search each) and the ~300/day cap is our binding throughput constraint.

9. **Any rate limit *within* the quota** (requests-per-minute/second on `searchByQuery`)
   separate from the daily cap, that we should pace against?

10. **Is `searchByQuery` a supported, stable endpoint** on our plan, or a legacy/soft-deprecated
    one that could be pulled? (We want to build our pipeline on it, so its longevity matters.)

## 5. Why it matters (so the agent weights the right answers)

Our entire enrichment pipeline now runs on this endpoint: `company → searchByQuery →
decision-maker → reveal → phone`. It works brilliantly (~36% of hard-to-find firms yield a
verified mobile). The **only** constraint left is the search quota — at ~300/day, draining our
3,000-company backlog is ~10 days. If the quota is raisable (higher tier / bulk plan) or the
reset is faster than daily, that timeline collapses. So the highest-value answers are
**#1 (cadence), #2/#8 (size + how to raise it), and #5 (does pagination multiply the cost).**
