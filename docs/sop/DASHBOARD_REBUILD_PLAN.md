# Dashboard rebuild — plan

Written 2026-08-05, after the HubSpot stage migration completed. **Nothing built yet.**

---

## 1. What changes

Three things, in order of how much code they touch:

1. **Metrics are redefined** to what we agreed per role — counted as *transitions into a
   stage*, not as current occupancy.
2. **Scraped + Campaign are merged everywhere.** The pipeline toggle goes. Both pipelines
   now carry identical stages, so scoping by pipeline no longer means anything.
3. **The build must learn the new stages** and stop trusting the retired one.

---

## 2. The core problem with the current build

The dashboard today derives every milestone from a **numeric level**:

```
LEVEL = {"Cold Call":0, "Call Attempted":1, "Interested":2, "GMeet Fixed":3, ...}
d["att"] = first_at(1)   # earliest date this deal reached level >= 1
```

That model cannot express the metrics we agreed, for two reasons.

**Reason 1 — different outcomes share a level.** `Dead/ColdCall/Not Interested`,
`Dead/ColdCall/WrongNumber` and `No Pickup` are all level 1. "Calls connected" is defined as
`Not Interested + Interested` only. A level threshold cannot separate a lead who *answered
and said no* from one whose *number was wrong* — they are the same number. **Calls connected
is not computable under the current model at all.**

**Reason 2 — `first_at` records only the first time.** Under the new flow a deal legitimately
passes through the calling stages twice: `No Pickup` on Monday, then `Not Interested` on
Tuesday after the callback. That is two dials on two days. `first_at` records Monday and
discards Tuesday, so the callback loop — the whole point of the new flow — would be
invisible.

**Fix: replace level thresholds with explicit stage-set membership, and emit a list of dates
per metric rather than one date.**

```
d["ev"] = {"att": ["2026-08-03", "2026-08-04"], "conn": ["2026-08-04"], ...}
```

Counting rule: a deal counts once per (stage, day). Two different stages hit on the same day
count twice — `No Pickup` in the morning and `Not Interested` in the afternoon is two
attempts, correctly. The same stage twice in one day counts once.

---

## 3. Data-layer changes — `build_dashboard.py`

### 3.1 Filter stage history to human moves

~42% of stage-history entries are `sourceType=INTEGRATION` — bulk API writes, including our
own migration of 245 deals today. Unfiltered, that migration alone reads as the biggest
calling day in company history.

```
entries = [e for e in hist if e.get("sourceType") == "CRM_UI"]
```

`CRM_UI` entries also carry `updatedByUserId`, which gives **per-person attribution that does
not depend on who currently owns the deal** — better than today's owner-based split, because
a deal reassigned last week currently credits its whole history to the new owner.

### 3.2 Stage sets, replacing LEVEL

```
CALL_ATTEMPTED = {No Pickup, Dead/ColdCall/WrongNumber,
                  Dead/ColdCall/Not Interested, Dead/ColdCall/NoPickup, Interested}
CALL_CONNECTED = {Dead/ColdCall/Not Interested, Interested}
GMEET_FIXED    = {GMeet Fixed}
VC_ATTENDED    = {Dead/GMeet/NoShow, Dead/GMeet/wrong fit,
                  Dead/GMeet/Privacy Concerns, Script Shared}
SCRIPTS_SHARED = {Script Shared}
SCRIPT_RESULTS = {Script Results Received}
SCRIPT_EVALS   = {Dead/ResultsReceived/WrongFit-Rejected, Commercial Negotiation}
NEGOTIATION    = {Commercial Negotiation}
NEG_CALLS      = {Dead/Negotiation/Pricing, Dead/Negotiation/Contractual,
                  Deal Contract Signed}
CLOSED_WON     = {Closed/Won}
```

Deliberate exclusions, each for a stated reason:
- `Dead/ColdCall/WrongFit` is **not** a call attempt — screened out, never dialled.
- `Dead/GMeet/Cancelled` is **not** a VC attended — called off in advance, no time spent.

### 3.3 Historical continuity

`Call Attempted (retired)` still appears in the history of ~100 deals. Map it to the same
bucket as `No Pickup` so the pre-migration time series does not fall off a cliff on 5 August.
Unknown stage ids (4 already exist in the portal from previously deleted stages) are skipped,
not crashed on.

### 3.4 Owner-assignment history

"Cold-call leads assigned" and "GMeets assigned" are **not** stage events. They need
`propertiesWithHistory=hubspot_owner_id`, which I verified is available. Today the dashboard
uses `createdate` as a proxy, which is wrong the moment a lead is reassigned.

Cost: one extra API call per deal. Currently ~780 history calls per run; this adds a similar
number. Run time goes from roughly 8 minutes to 15.

### 3.5 Merge the pipelines

Keep the `pl` field on each row for reference, but stop filtering on it. Every count becomes
Scraped + Campaign combined.

---

## 4. Metrics per panel

### GTM Analyst
| Metric | Source |
|---|---|
| Cold-call leads assigned | owner-assignment events |
| Calls attempted | → CALL_ATTEMPTED |
| Calls connected | → CALL_CONNECTED |
| GMeets fixed | → GMEET_FIXED |

### Lead Manager
| Metric | Source |
|---|---|
| GMeets assigned | owner-assignment events on deals at GMeet Fixed |
| VCs attended | → VC_ATTENDED |
| Scripts shared | → SCRIPTS_SHARED |
| Script outputs received | → SCRIPT_RESULTS |
| Script evaluations conducted | → SCRIPT_EVALS |
| Moved to negotiation | → NEGOTIATION |

### Lead Closer
| Metric | Source |
|---|---|
| Script evaluations conducted | → SCRIPT_EVALS *(same as Lead Manager — intentional, both pods do it)* |
| Negotiation calls conducted | → NEG_CALLS |
| Deals closed | → CLOSED_WON |

### Executive summary
Unchanged, except it now covers both pipelines.

---

## 5. UI changes — `index.html`

1. **Remove the pipeline toggle** (lines 134–135) and the `r.pl===F.pipeline` filters
   (lines 233, 304). Drop `F.pipeline` from state.
2. **Rewrite the `DASHBOARDS` metric definitions** to the fields above.
3. **Fix the hardcoded stage map** at line 332 — `1:'Call Attempted'` now points at a retired
   stage; it becomes `No Pickup`, and the four new dead stages are added.
4. **Panel headers** stop saying "Scraped" or "Campaign".

---

## 6. Workflow schedule

### The assumption I need confirmed

You wrote *"every 2 hours starting 10 pm till 6:30"*. I have built the plan around
**10:00 IST → 18:30 IST**, on the reading that 6:30 is end of the working day and the team
works 10:00–18:30. Overnight 22:00 → 06:30 would mean the dashboard refreshes only while
nobody is working. **If you did mean 22:00, say so and I will flip the cron — it is one line.**

### Proposed cron (GitHub Actions runs in UTC; IST = UTC+5:30)

```yaml
schedule:
  - cron: "30 4,6,8,10,12 * * *"   # 10:00, 12:00, 14:00, 16:00, 18:00 IST
  - cron: "0 13 * * *"             # 18:30 IST — day close
```

Six runs a day, down from the current 24.

### "It MUST run exactly at 6:30" — this cannot be guaranteed, and you should know why

GitHub's scheduled workflows are best-effort. They are queued on shared infrastructure and
are routinely **delayed by 5–20 minutes** at busy times; on peak hours they can be delayed
much longer or **dropped entirely**. GitHub documents this explicitly. Cron alone will not
give you an exact 18:30 run.

Three options:

1. **Add a backstop run** — schedule 18:30 *and* 18:50 IST. The build is idempotent (it
   rebuilds from live HubSpot every time), so a second run is harmless and simply publishes
   fresher data. This covers a delayed or dropped 18:30. **My recommendation** — costs one
   extra line and one extra run.
2. **Accept the drift.** The day-close number is a snapshot of a day that has ended; a run at
   18:41 captures the same day as one at 18:30.
3. **Trigger it externally** — any scheduler you control (a laptop cron, a cloud function)
   hitting `workflow_dispatch` via the API fires on time. Only worth it if exactness is a
   hard requirement.

With option 1:
```yaml
schedule:
  - cron: "30 4,6,8,10,12 * * *"   # 10:00–18:00 IST, every 2h
  - cron: "0 13 * * *"             # 18:30 IST — day close
  - cron: "20 13 * * *"            # 18:50 IST — backstop if the 18:30 slips
```

---

## 7. Risks

| Risk | Handling |
|---|---|
| Metric numbers change materially vs today | Expected — the definitions changed. I will print an old-vs-new comparison so the shift is explainable rather than alarming. |
| Run time roughly doubles (owner history) | ~15 min. Well within the 6-hour job limit. |
| `CRM_UI` filter drops legitimate history | Only API writes are dropped, and those were never human activity. Today's migration is correctly excluded. |
| Two copies of `build_dashboard.py` drift | Build in the repo root, copy to `lh2-pipeline/dashboard/`, verify byte-identical before commit. |

---

## 8. Build order

1. `build_dashboard.py` — stage sets, CRM_UI filter, owner history, merged pipelines
2. Run locally, compare old vs new counts, sanity-check against HubSpot
3. `index.html` — remove toggle, rewire metrics, fix the stage map
4. Copy both to `lh2-pipeline/dashboard/`, confirm identical
5. Update `deploy-dashboard.yml` schedule
6. Commit and push; watch the first scheduled run
