# 3. Stage inventory and changes

**Net: 21 stages today → 24.** Five created, two retired.

## To create

| Stage | Type | Purpose |
|---|---|---|
| `No Pickup` | **live — not closed-lost** | holding stage between first dial and callback |
| `Dead/ColdCall/NoPickup` | closed | callback also rang out |
| `Dead/GMeet/NoShow` | closed | booked, prospect did not turn up |
| `Dead/GMeet/Cancelled` | closed | called off in advance |
| `Dead/ScriptShared/NoShow` | closed | script shared, then vanished |

## To retire

| Stage | Live deals | Why |
|---|---:|---|
| `Call Attempted` | 243 | replaced by the outcome stages |
| `Dead/Interested/NoShow` | 13 | collides with `Dead/GMeet/NoShow` — same event |

## Current stages, both pipelines

| # | Stage | Scraped ID | Campaign ID |
|---:|---|---|---|
| 0 | Cold Call | 3992480462 | 4002503379 |
| 1 | Call Attempted | 3992480464 | 4018854632 |
| 2 | Interested | 3992480465 | 4018854633 |
| 3 | GMeet Fixed | 3992480469 | 4018854634 |
| 4 | Script Shared | 3992480471 | 4018854635 |
| 5 | Script Results Received | 3992480473 | 4018854636 |
| 6 | Commercial Negotiation | 4030231231 | 4018854637 |
| 7 | Deal Contract Signed | 4029653710 | 4018854638 |
| 8 | Data Migration Done | 3992480475 | 4018854639 |
| 9 | Metadata Matched | 4036632313 | 4018854640 |
| 10 | Payment Initiation | 4036633274 | 4018854641 |
| 11 | Closed/Won | 4036632309 | 4018854642 |
| 12 | Dead/ColdCall/Not Interested | 4036632310 | 4018854643 |
| 13 | Dead/ColdCall/WrongFit | 4036687547 | 4002503384 |
| 14 | Dead/ColdCall/WrongNumber | 4099250912 | 4099442394 |
| 15 | Dead/Interested/NoShow | 4061963984 | 4002503385 |
| 16 | Dead/GMeet/wrong fit | 4036632311 | 4018854644 |
| 17 | Dead/Gmeet/Privacy Concerns | 4036687548 | 4018854645 |
| 18 | Dead/ResultsReceived/WrongFit-Rejected | 4036687549 | 4018854646 |
| 19 | Dead/Negotiation/Pricing | 4035313388 | 4068768453 |
| 20 | Dead/Negotiation/Contractual | 4036632312 | 4068768454 |

Naming is inconsistent between `Dead/GMeet/wrong fit` and `Dead/Gmeet/Privacy Concerns`.
Renaming a stage moves no deals, so it is safe to correct at the same time.

---
