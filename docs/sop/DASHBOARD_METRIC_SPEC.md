# LH2 Dashboard — data pull and metric specification

How every number on the dashboard is pulled from HubSpot and calculated. Written to be
checkable line by line.

Last updated 2026-08-05, after the stage migration.

---

## 0. Roles

The Role Definition table is the authority for what each role is measured on. Our dashboard
panels keep our internal names, which map one-to-one:

| Role Definition table | Dashboard panel | Owns the funnel from → to |
|---|---|---|
| GTM Analyst | **GTM Analyst** | introductory calls → first VC |
| Pod Lead | **Lead Manager** | VC → negotiation stage |
| Pod Head | **Lead Closer** | negotiation → deal closure |

Each panel is split into an **Input matrix** and an **Outcome matrix**, exactly as the table
is: inputs are what the person controls, outcomes are what that effort produced.

---

## 1. What is pulled from HubSpot

Three API surfaces. Nothing else is read.

### 1.1 Pipelines — `GET /crm/v3/pipelines/deals`

Read once per run, for **both** pipelines: Scraped (`default`) and Campaign (`2425754306`).

Gives, for every stage: `id`, `label`, `metadata.isClosed`. Used to build:
- `STAGE_LABEL` — stage id → canonical label, spanning both pipelines. The two pipelines use
  **different ids for the same label**, so every lookup goes through this map.
- `DEAD` — stage ids where `isClosed == true` (minus `Closed/Won`, which is a win).
- `ORDER` — how far down the funnel a stage sits.

### 1.2 Deals — `POST /crm/v3/objects/deals/search`

Paged at 100/request until exhausted. Properties requested:

```
hubspot_owner_id, scraped_type, lead_source, pipeline, dealstage, createdate,
dealname, metadata_link, deal_value_range, loc, pr_count, num_projects, num_repos, cost
```

A deal is **skipped** if it has no owner, or if its stage id is not in `STAGE_LABEL`
(a stage deleted from the portal — skipped rather than guessed at).

### 1.3 Deal history — `GET /crm/v3/objects/deals/{id}?propertiesWithHistory=dealstage,hubspot_owner_id`

**One call per deal.** This is where every activity metric comes from — not from the deal's
current state. Each history entry looks like:

```json
{ "timestamp": "2026-07-20T07:35:41.256Z",
  "value": "3992480464",
  "sourceType": "CRM_UI",
  "sourceId": "userId:166322228",
  "updatedByUserId": 166322228 }
```

### 1.4 Owners — `GET /crm/v3/owners?limit=200`

Two uses: the member dropdown, and the **user-ID → owner-ID map** (see §2.6).

### 1.5 Notes — for the Hot & Won table only

For deals at `Script Results Received` or beyond, associated notes are fetched and the
`Remarks:` line surfaced. Display only; feeds no metric.

---

## 2. The eight calculation rules

Every metric obeys all eight.

### Rule 1 — count ENTRIES into a stage, not occupancy
A metric counts the number of times a deal **entered** a qualifying stage, on the day it
entered. Never how many sit there now. A deal that entered `Interested` on 3 August counts
on 3 August, and keeps counting there forever, whatever happens to it afterwards.

### Rule 2 — IST day boundaries
Timestamps are UTC; every one is converted to Asia/Kolkata before the date is taken. This
matches HubSpot's display zone, so a 23:40 IST stage move lands on the day the person
actually worked, not the next one.

### Rule 3 — humans only (`sourceType == "CRM_UI"`)
Roughly **42%** of stage-history entries are `sourceType == "INTEGRATION"` — bulk API writes,
including our own pushes. All are discarded.

> Without this filter the 5 August migration, which moved 245 deals in one batch, would read
> as the largest calling day in the company's history.

### Rule 4 — de-duplicate per (stage, person, day)
The same deal entering the same stage on the same day by the same person counts **once**.
Two *different* qualifying stages on the same day count **twice** — `No Pickup` in the
morning and `Dead/ColdCall/Not Interested` in the afternoon is two attempts, correctly.

### Rule 5 — a metric is a SET OF STAGES, never a threshold
Each metric names the exact stages that satisfy it.

> This replaced a numeric-level model that could not express the metrics at all.
> `Dead/ColdCall/Not Interested` and `Dead/ColdCall/WrongNumber` sat at the same level, yet
> one means a human answered and the other means the number was junk. "Calls connected" has
> to separate exactly those two, so membership must be explicit.

### Rule 6 — activity follows the ACTOR, assignment follows the OWNER
Activity is credited to `updatedByUserId` — whoever made the move. Assignment is credited to
the deal's owner.

> A handoff and a stage change are **one action**: a GTM Analyst logs `GMeet Fixed` and
> reassigns to the Lead Manager simultaneously. Crediting activity to the current owner would
> move that VC-setup onto the Lead Manager and leave the analyst at zero — and the *better*
> the handoff discipline, the more work is misattributed. Measured on live data before the
> fix: Ishpreet had booked 5 GMeets but was being credited with 10.
>
> A second benefit: numbers stop changing retroactively. Under owner attribution, reassigning
> an old deal silently rewrote last week's figures.

**User IDs are not owner IDs.** History identifies people by HubSpot *user* ID; deals by
*owner* ID — separate namespaces that coincide only by luck. The map is built explicitly
from the owners API (`userId` → `id`), with a fallback if a user has no owner record.

### Rule 7 — both pipelines, always combined
Scraped and Campaign carry identical stage labels in identical order. Nothing anywhere is
scoped by pipeline.

### Rule 8 — historical aliases
- `Call Attempted` → `No Pickup`
- `Call Attempted (retired)` → `No Pickup`
- `Dead/Gmeet/Privacy Concerns` → `Dead/GMeet/Privacy Concerns`

`Call Attempted` was retired on 5 August and its 245 deals moved to `No Pickup`, but it stays
in the history of ~100 deals. The alias keeps the series continuous across that date.
Unresolvable stage ids (4 already exist in the portal from previously deleted stages) are
skipped.

---

## 3. Metric definitions

### 3.1 GTM Analyst — *introductory calls → first VC*

**Input matrix**

| Metric | Counts | Attribution |
|---|---|---|
| # of cold-call leads assigned | owner-change events assigning the deal to this person; falls back to `createdate` if never reassigned | owner |
| # of calls attempted | entries into `No Pickup` · `Dead/ColdCall/WrongNumber` · `Dead/ColdCall/Not Interested` · `Dead/ColdCall/NoPickup` · `Interested` | actor |
| # of calls connected | entries into `Dead/ColdCall/Not Interested` · `Interested` | actor |

**Outcome matrix**

| Metric | Counts | Attribution |
|---|---|---|
| # of VCs setup | entries into `GMeet Fixed` | actor |

**`Dead/ColdCall/WrongFit` is excluded from calls attempted** — that lead was screened out
from the profile and never dialled, so counting it would inflate calling activity with work
that never happened.

Connected is a strict subset of attempted. `Interested` satisfies both — one dial that
connected and went well. That is correct, not double counting.

### 3.2 Lead Manager — *VC → negotiation stage*

**Input matrix**

| Metric | Counts | Attribution |
|---|---|---|
| # of GMeets assigned | entries into `GMeet Fixed`, credited to the person the deal landed on | **owner** |
| # of VCs attended | entries into `Dead/GMeet/NoShow` · `Dead/GMeet/wrong fit` · `Dead/GMeet/Privacy Concerns` · `Script Shared` | actor |
| # of scripts shared | entries into `Script Shared` | actor |

**Outcome matrix**

| Metric | Counts | Attribution |
|---|---|---|
| # of scripts output received | entries into `Script Results Received` | actor |
| # of script output evaluation conducted | entries into `Dead/ResultsReceived/WrongFit-Rejected` · `Commercial Negotiation` | actor |
| # of deals moved to negotiation stage | entries into `Commercial Negotiation` | actor |

**"Attended", not "connected"** — deliberate. The Role Definition table says *VCs connected*;
we measure *VCs attended*. A no-show is a call the Lead Manager joined and waited in: real
time spent. "Connected" would exclude it. `Dead/GMeet/Cancelled` **is** excluded, because a
meeting called off in advance cost no time. That distinction is the entire reason NoShow and
Cancelled are separate stages.

**GMeets assigned and VCs setup are the same events**, attributed from opposite ends — the
analyst credited for booking, the Lead Manager for receiving. With member = *All* the two
totals are **identical**; use that as an integrity check.

### 3.3 Lead Closer — *negotiation → deal closure*

**Input matrix**

| Metric | Counts | Attribution |
|---|---|---|
| # of script output evaluation conducted | entries into `Dead/ResultsReceived/WrongFit-Rejected` · `Commercial Negotiation` | actor |
| # of deal negotiation calls conducted | entries into `Dead/Negotiation/Pricing` · `Dead/Negotiation/Contractual` · `Deal Contract Signed` | actor |

**Outcome matrix**

| Metric | Counts | Attribution |
|---|---|---|
| # of deals closed | entries into `Closed/Won` | actor |

**Script output evaluation appears on both this panel and the Lead Manager's, on purpose** —
the two pods conduct it together. The duplication is intended; do not "fix" it.

Splitting the two negotiation dead-ends matters: a deal lost on **price** says our number was
wrong, one lost on **contract terms** says our paperwork was. Different fixes.

---

## 4. Data shape written to `dashboard_data.json`

```json
{ "generated": "2026-08-05 21:58 IST",
  "core": [["166420402","Shreyas Boosnoor"], "..."],
  "rows": [{
    "o":   "166322228",              // current owner id
    "pl":  "scraped",                // retained for reference; never filtered on
    "t":   "India",                  // lead-source bucket
    "sl":  "No Pickup",              // current stage label
    "r":   1,                        // funnel position; a dead stage maps to how far it got
    "cc":  false, "won": false, "dead": false,
    "c":   "2026-07-28",             // created (IST)
    "asg": ["2026-08-03"],           // days assigned to the CURRENT owner
    "m": {                           // [day, actorOwnerId] per metric
      "att":  [["2026-08-04","166420402"]],
      "conn": [], "gm": [], "vc": [], "ss": [],
      "rr":  [], "ev": [], "cn": [], "neg": [], "won_d": []
    },
    "nm":"Acme","ml":"","dvr":"","loc":0,"pr":0,"pj":0,"rp":0,"cost":0,"note":""
  }] }
```

| key | metric |
|---|---|
| `att` | calls attempted |
| `conn` | calls connected |
| `gm` | VCs setup / GMeets assigned *(same events, two attributions)* |
| `vc` | VCs attended |
| `ss` | scripts shared |
| `rr` | scripts output received |
| `ev` | script output evaluations conducted |
| `cn` | deals moved to negotiation |
| `neg` | deal negotiation calls conducted |
| `won_d` | deals closed |

`gma` (GMeets assigned) is **derived in the UI** from `gm` by owner attribution. It is not a
stored field.

---

## 5. How the UI turns that into a number

```js
events(row, metric, member)
  // assignment metrics → owner-based
  asg → member matches row.o ? row.asg : []
  gma → member matches row.o ? row.m.gm days : []
  // activity metrics → actor-based
  else → row.m[metric] entries whose actor == member, mapped to their day
```

The KPI is then `sum over all rows of events(row, metric, member) falling inside the selected
date range`. Charts bucket the identical event list by day or week.

Note the row set is **not** pre-filtered by member — attribution is decided per event, which
is what allows one deal to credit its calls to the analyst and its GMeet-received to the
Lead Manager.

---

## 6. Refresh schedule

GitHub Actions, `deploy-dashboard.yml`. Cron is UTC; IST is UTC+5:30.

| Cron | IST | Purpose |
|---|---|---|
| `30 4,6,8,10,12 * * *` | 10:00, 12:00, 14:00, 16:00, 18:00 | working-day refresh, every 2h |
| `0 13 * * *` | 18:30 | day close |
| `20 13 * * *` | 18:50 | backstop |

The backstop exists because **GitHub's scheduled workflows are best-effort** — routinely
delayed 5–20 minutes and occasionally dropped. The build is idempotent (it rebuilds from
live HubSpot each time), so a second run costs nothing and simply republishes with fresher
data. Exact-time firing would need an external trigger hitting `workflow_dispatch`.

---

## 7. Known limits — stated, not papered over

1. **"Calls attempted" is a floor, not a dial count.** A repeat dial that does not change the
   stage produces no history entry and is invisible. The portal contains **2 logged call
   engagements in total** (14 July, no owner, no disposition, no duration) — HubSpot's call
   object is unused. The only real fix is logging calls.
2. **A stage moved late lands on the wrong day.** The metric is the day the *stage changed*,
   not the day the work happened. This is why the SoPs require same-day stage moves.
3. **Pre-5-August splits are less trustworthy.** Before the migration every no-pickup outcome
   sat in one undifferentiated `Call Attempted` bucket, so attempted-versus-connected is only
   fully reliable from 5 August onward.
4. **A deal skipped for having no owner is invisible** to every metric, including totals.
5. **Notes feed no metric** — display only, in the Hot & Won table.
