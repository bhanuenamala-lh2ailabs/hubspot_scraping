# Lead-Quality KPIs — definitions

The fixed set we come back to **every week** and use to compare **sources against each other**
(GoodFirms scrape · Private Codebase Tracker · Tracxn · OutFlo) and **week against week**.

Computed automatically by `analysis/weekly/weekly_report.py`; every run appends to
`analysis/weekly/_data/kpi_history.json` so the trend is preserved.

---

## The one number: **ULR — Usable Lead Rate**

> **ULR = leads that were both correctly qualified AND contactable ÷ leads pushed**

A lead is **usable** if it did **not** die as `WrongFit` (it was a real target) **and** was not
written off as *contact unreachable* (we could actually reach someone).

This is the headline because it isolates **what the source controls**. It says nothing about how
good the pitch is — that's Tier 2. If ULR is low, fix sourcing; if ULR is high but ER is low, fix
the pitch.

**Target: ≥ 80%.** Below 60% the source is wasting caller time.

---

## Tier 1 — Source quality (judges the scrape / data source)

| KPI | Formula | Measures | Target |
|---|---|---|---|
| **QR** — Qualification Rate | `1 − WrongFit ÷ pushed` | Did the source send **real targets**? | ≥ 85% |
| **CR** — Contactability Rate | `1 − contact_unreachable ÷ pushed` | Is the **contact data usable**? | ≥ 85% |
| **FAR** — Firmographic Accuracy Rate | `verified-correct ÷ verified` | When an analyst checked, did the **claimed size/facts hold**? | ≥ 90% |
| **ULR** — Usable Lead Rate | `qualified ∧ contactable ÷ pushed` | **Headline** — usable leads delivered | ≥ 80% |

`FAR` is only computable where an analyst recorded a real value in the notes — it's a sample,
not a census. Report the denominator alongside it.

## Tier 2 — Funnel performance (judges outreach, **not** the source)

| KPI | Formula | Measures | Target |
|---|---|---|---|
| **ER** — Engagement Rate | `Interested+ ÷ contacted` | Does the **pitch land** on valid leads? | ≥ 25% |
| **MR** — Meeting Rate | `GMeet Fixed+ ÷ pushed` | Fast proxy for real progress | ≥ 8% |
| **AFD** — Avg Funnel Depth | `mean(level)` on 0–11 | Overall progression | ↑ |

**`contacted` deliberately excludes WrongFit** — otherwise a bad list makes a good pitch look
bad, and the two problems become impossible to tell apart.

## Tier 3 — Outcome (slow, low-n; trend only)

| KPI | Formula | Note |
|---|---|---|
| **WR** — Win Rate | `Closed/Won ÷ pushed` | Long cycle — read as a trend over months, never week-to-week |

---

## Funnel levels (the 0–11 scale)

`Cold Call 0 · Call Attempted 1 · Interested 2 · GMeet Fixed 3 · Script Shared 4 ·
Script Results 5 · Commercial Negotiation 6 · Contract Signed 7 · Data Migration 8 ·
Metadata Matched 9 · Payment Initiation 10 · Closed/Won 11`

A dead deal keeps the level it **reached** (`Dead/GMeet/*` → 3), so dying late still counts as
progress. All funnel counts are **cumulative** — "reached this step **or beyond**".

---

## WNR — Wrong Number Rate  *(added 2026-08-04)*

```
WNR = deals at Dead/ColdCall/WrongNumber ÷ deals that were actually dialled
```

**What it measures: our enrichment, not our targeting.** Every other cold-call dead stage
tells you something about the *lead* — wrong fit, not interested. WrongNumber tells you
something about *us*: we pushed a number that does not reach the person. Until now that
failure was invisible, absorbed into `Call Attempted` where it looked like a lead who simply
never picked up.

**Read it against the source.** WNR is per-source or it is meaningless — it is the field
verdict on whichever provider supplied that number:

| WNR | Verdict |
|---|---|
| **< 5%** | healthy — SignalHire-verified mobiles should sit here |
| **5–15%** | provider drift; re-verify the affected batch |
| **> 15%** | the source's phone data is not trustworthy — stop pushing from it |

The Tracxn sheet measured ~14% wrong by call feedback, which is what triggered the
SignalHire-only rule and the +91 hard gate. WNR is how we catch the next such source in
week one instead of after 154 pushed leads.

**It counts as a call attempt.** A WrongNumber deal sits at funnel depth **1**, the same as
`Call Attempted` — the caller picked up the phone and dialled; only the number was bad. It
therefore appears in Called+ / Call Attempted on the dashboard and in the weekly report.
Contrast `Dead/ColdCall/WrongFit` at depth 0, which was screened from the profile and never
dialled at all.

**Denominator care:** exclude `Dead/ColdCall/WrongFit` — those were never dialled, so they
could not have had a wrong number. Only count leads someone actually tried to ring.

**Do not confuse with CR (Contactability Rate).** CR is measured *before* the push — did we
find a valid-looking +91 number. WNR is measured *after the call* — did that number actually
work. CR high + WNR high means our validator passes numbers that are well-formed but wrong.

---

## Rules that keep the comparison honest

1. **Segment by source, always.** Scrape leads and hand-curated tracker leads are not
   comparable — mixing them hid a 94%-vs-11% gap in W31.
2. **Cohort by push date, and let leads mature.** Funnel KPIs (ER/MR/AFD/WR) are only counted
   for leads pushed **≥14 days ago**; a lead pushed yesterday hasn't had a chance to convert.
   Tier-1 KPIs (QR/CR/ULR) can be read immediately — they're judged at first contact.
3. **Report the denominator.** `n < 25` is directional only; don't act on it.
4. **Never compare a KPI across different owners** without noting it — analyst behaviour
   (how aggressively they mark WrongFit) shifts QR materially.
5. **One change at a time.** Change the gate *or* the source *or* the pitch in a given week,
   so the KPI move is attributable.

## How to read a weekly move

| Symptom | Likely cause | Where to look |
|---|---|---|
| **QR ↓** | source sending wrong targets | gate thresholds, source data accuracy (`FAR`) |
| **CR ↓** | enrichment degraded | provider coverage / quota |
| **WNR ↑** | the numbers we push don't work | the source's phone field; re-verify via SignalHire |
| **ULR ↓ but ER stable** | list quality problem, pitch is fine | sourcing |
| **ULR stable but ER ↓** | pitch/targeting mismatch, not sourcing | script, ICP fit |
| **FAR ↓** | the *source's* data is drifting | consider a second verification source |
