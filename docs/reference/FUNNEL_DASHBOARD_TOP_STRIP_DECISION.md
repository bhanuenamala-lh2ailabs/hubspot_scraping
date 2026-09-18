# Open Decision: What Goes in the Dashboard's Top Summary Strip

## Context

We're porting a "Revenue Dashboard" email format (screenshot reference, internal) to a HubSpot
funnel report. That format has a 3-number strip at the top:

```
MONTHLY REVENUE    7-DAY REVENUE    DAILY REVENUE
   $378,110            $95,751          $14,857
     ↓ 9%                ↑ 8%             ↑ 25%
```

Below it, a table: rows = accounts, columns grouped into Monthly (Extrapolated) / Rolling 7 Days /
Daily, each with a period-over-period % change.

The table part ported cleanly onto the funnel (rows = deal stages, "Monthly Extrapolated" became
"Inception to Date" — see `COMPANY_OPS_DATA_DAILY_REPORT_IMPLEMENTATION.md`-adjacent work in this
repo for the full table version). **The 3-number top strip did not port cleanly**, and that's the
open question this doc is for.

## Why this is genuinely hard

Revenue works as a single headline number because it's **one unit (dollars) that sums meaningfully
across every account, every stage, every day.** A funnel has no equivalent: "a call attempted" and
"a contract signed" are not the same kind of event, and summing them together produces a number
with no clean interpretation.

Monthly Revenue is already dropped (agreed). What replaces 7-Day and Daily — or whether a third
slot should exist at all — is the open question.

## Candidates considered, with real numbers (portal-wide, as of 2026-09-17)

| Candidate | Definition | Today | Roll7 | Prev7 | Verdict |
|---|---|---|---|---|---|
| **Leads Assigned** | Any deal entering Cold Call (any sourceType, incl. script pushes) | 51 | 85 | 467 | Rejected — dominated by push-script volume, not funnel health. A big campaign day spikes it to 400+; a quiet day drops it to 0. Measures our sourcing activity, not the pipeline. |
| **Deals Worked (event count)** | Sum of flow-events into 8 mid-funnel stages: No Pickup, Interested, GMeet Fixed, Script Shared, Script Results Received, Commercial Negotiation, LOI, Deal Contract Signed. CRM_UI-only (human-driven). | 23 | 121 | 154 | Candidate — see caveat below: this is an **event count, not a deal count**. A deal moving through 2 of these 8 stages same-day counts twice. |
| **Leads Engaged (deduplicated)** | Distinct deal IDs with at least one CRM_UI stage-move, any of the 26 stages, during the period. Deduplicated by deal ID (matches the existing per-caller daily report's "leads engaged" metric). | 32 | 209 | 281 | Candidate — the most defensible "how much did the team actually touch" number, but includes Dead-marking events (a disqualification counts as "engaged," which is arguably correct — touching a deal to kill it is still work). |
| **Closed/Won** | Deals reaching Closed/Won (CRM_UI-only) | 0 | 0 | 0 | Rejected as a *daily* headline — too rare an event; most days read as 0, which looks like nothing is happening even when the pipeline is healthy. Strong candidate for a **separate, non-strip** "wins this month" callout instead. |
| **Dead (combined)** | All 13 Dead/\* stages combined, flow-count | 12 | 110 | 139 | Rejected alone (a "how much died" headline is a strange thing to lead with) — but potentially useful as a *ratio* partner (see below). |

## A composite option worth considering

**Deals Worked : Dead ratio** — e.g. today 23 worked vs 12 dead — could work as a "conversion
health" signal rather than a raw activity count. Not computed as a trend here; flagging it as a
possibility, not a recommendation.

## The actual question to answer

Pick 2 or 3 numbers for the top strip. Options on the table:

1. **Two numbers**: Deals Worked (Roll7) + Deals Worked (Daily) — simplest, direct replacement of
   the 7-Day/Daily Revenue slots, same "event count" caveat as above.
2. **Two numbers, different metric**: Leads Engaged (Roll7) + Leads Engaged (Daily) — deduplicated,
   arguably more honest, but conflates progress and disqualification into one number.
3. **Three numbers**: reintroduce a third slot using **Inception-to-date Closed/Won** (a true
   cumulative "wins" counter, currently 12) alongside Deals Worked Roll7/Daily — gives the strip an
   "outcome" anchor the way Monthly Revenue anchored the original, without the noisy-daily problem
   of using Closed/Won as a period metric.
4. **Something else entirely** — e.g. a single blended "funnel score," or per-vertical strips
   instead of one portal-wide strip.

## What's needed back

A decision on which 2–3 numbers, and confirmation on the event-count-vs-deduplicated-deal-count
question for whichever "worked/engaged" metric is chosen — that changes the actual computation, not
just the label.
