# 4. Dashboard — how every metric is counted

**The counting rule.** Every stage metric counts **how many deals hit that stage that day** —
entered it at any point during the day, not how many are sitting in it now. Read from each
deal's stage-change history, bucketed by **IST** day.

**Filter to `sourceType == "CRM_UI"`.** Roughly 42% of stage-history entries are
`INTEGRATION` — bulk API pushes, including our own. Unfiltered, a bulk import reads as a
record-breaking calling day. `CRM_UI` entries also carry `updatedByUserId`, which gives
per-rep attribution for free and does not depend on who owns the deal.

## GTM analyst panel

| Metric | Counted from |
|---|---|
| Cold-call leads assigned | owner-change history that day |
| Calls attempted | → `WrongNumber`, `Not Interested`, `Interested`, `No Pickup`, `Dead/ColdCall/NoPickup` |
| Calls connected | → `Not Interested`, `Interested` |
| GMeets fixed | → `GMeet Fixed` |

`WrongFit` is excluded from calls attempted — that lead was screened out and never dialled.

## Post-GMeet owner panel

| Metric | Counted from |
|---|---|
| GMeets assigned | owner-change history on deals at `GMeet Fixed` |
| **VCs attended** | → `Dead/GMeet/NoShow`, `Dead/GMeet/wrong fit`, `Dead/Gmeet/Privacy Concerns`, `Script Shared` |
| Scripts shared | → `Script Shared` |
| Script outputs received | → `Script Results Received` |
| Moved to negotiation | → `Commercial Negotiation` |

**Why "attended", not "connected".** The two words measure different things, and the
distinction decides whether a no-show counts. *Connected* would mean both parties spoke — a
no-show plainly fails that. *Attended* measures whether **he** turned up, and on a no-show he
did: he joined the call and waited. That is real time spent, and a metric of his effort has
to include it. `Dead/GMeet/Cancelled` is excluded, because a meeting called off in advance is
time he never spent. That is exactly why NoShow and Cancelled are separate stages — merging
them would make this metric impossible to compute.

## Lead manager panel

| Metric | Counted from |
|---|---|
| Script evaluations conducted | → `Dead/ResultsReceived/WrongFit-Rejected`, `Commercial Negotiation` |

Counting the evaluation *outcome* rather than the `Script Results Received` staging stage
measures that the evaluation actually concluded. It is the lead manager's responsibility to
carry a deal this far.

## Lead closer panel

| Metric | Counted from |
|---|---|
| Script output evaluations conducted | same definition as the lead manager's |
| Deal negotiation calls conducted | → `Dead/Negotiation/Pricing`, `Dead/Negotiation/Contractual`, `Deal Contract Signed` |
| Deals closed | → `Closed/Won` |

The first metric appears on **both** the manager and closer panels deliberately. The two pods
do this work together, so the duplication is intended and should not be "corrected" later.

No new stages are required for the manager or closer panels — every stage already exists.

## Baseline transition counts

Lifetime totals as at 5 August 2026, with CRM_UI-only in brackets. Useful as a sanity check
when the panels first go live.

| Stage | Transitions | via CRM_UI |
|---|---:|---:|
| Script Shared | 52 | 28 |
| Script Results Received | 18 | 12 |
| Dead/ResultsReceived/WrongFit-Rejected | 14 | 12 |
| Commercial Negotiation | 13 | 8 |
| Deal Contract Signed | 8 | 6 |
| Dead/Negotiation/Pricing | 4 | 4 |
| Dead/Negotiation/Contractual | 1 | 0 |
| Closed/Won | 5 | 3 |

---
