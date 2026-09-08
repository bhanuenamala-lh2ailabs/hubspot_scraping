# HubSpot stage migration — runbook

Surveyed 2026-08-05. **Nothing has been executed.** Every phase below is reversible up to
Phase 5; the snapshot in Phase 0 is what makes that true.

---

## The one finding that de-risks this

`Call Attempted` was, in practice, already being used as a no-pickup stage. Classifying all
243 deals on it by what their notes and tasks actually say:

| Proposed destination | Deals |
|---|---:|
| **No Pickup** (notes say no answer / busy / callback / switchboard) | 110 |
| **No Pickup** (no note and no task — no evidence either way) | 117 |
| Dead/ColdCall/WrongNumber | 9 |
| Dead/ColdCall/Not Interested | 1 |
| Interested | 6 |

**227 of 243 land on `No Pickup`.** So this is close to a rename, not a scatter — which
means the migration is far lower-risk than the raw number suggests. Only 16 deals move
somewhere that materially changes their meaning, and those are the ones worth eyeballing.

---

## Phase 0 — Snapshot (do this first, always)

Write every live deal's `id`, `pipeline`, `dealstage`, `hubspot_owner_id` to
`crm_mirror/holding/pre_migration_snapshot_<date>.json`, plus the full stage definitions of
both pipelines.

That file is the rollback. Replaying it restores every deal to where it was, and restores
stage metadata if a create goes wrong.

---

## Phase 1 — Create the five new stages (both pipelines)

Non-destructive and reversible: a new empty stage can simply be deleted.

`POST /crm/v3/pipelines/deals/{pipelineId}/stages`

| Label | isClosed | probability | Sits after |
|---|---|---|---|
| `No Pickup` | **false** | 0.12 | Cold Call |
| `Dead/ColdCall/NoPickup` | true | 0.0 | with the other cold-call deads |
| `Dead/GMeet/NoShow` | true | 0.0 | with the other GMeet deads |
| `Dead/GMeet/Cancelled` | true | 0.0 | with the other GMeet deads |
| `Dead/ScriptShared/NoShow` | true | 0.0 | after Script Shared |

Existing metadata confirms the pattern: open stages carry `isClosed=false` with a
probability (Cold Call 0.1, Call Attempted 0.15, Interested 0.2); dead stages carry
`isClosed=true, probability=0.0`.

> **The single most important setting in this whole migration:** `No Pickup` must be
> `isClosed=false`. If it is created closed, 227 migrated deals drop out of the open funnel
> the moment they land, every callback task goes unworked, and the stage silently becomes
> the graveyard it was designed to replace.

Do both pipelines. Labels and order must stay identical between them, or one design stops
governing both.

---

## Phase 2 — Fix the naming inconsistency

`Dead/Gmeet/Privacy Concerns` → `Dead/GMeet/Privacy Concerns`.

A rename keeps the same stage id, so no deal moves and no history breaks. Safe to do at any
point; do it here while we are already in the pipeline editor.

---

## Phase 3 — Migrate the 243

**Produce a CSV first, review it, then execute.** Never bulk-move straight from a classifier.

The CSV carries one row per deal: id, name, owner, the note text it was classified on, the
proposed destination, and the rule that fired. Review focus:

1. The **16 non-No-Pickup rows** (9 WrongNumber, 6 Interested, 1 Not Interested) — these
   change meaning, so they are worth reading individually.
2. The **6 going to Interested** especially. Those are live opportunities that have been
   sitting in the wrong stage; if any is real, it needs an owner told, not just a stage move.
3. Anything touched in the last 3 days — 18 deals were touched today and 122 within three
   days. This is the team's active working set, not a dormant pile. Where an owner is
   mid-conversation, their read beats the classifier's.

Execution: batch through `POST /crm/v3/objects/deals/batch/update`, 100 at a time, logging
every id and old→new pair to `crm_mirror/holding/`.

> **A useful property:** API writes are tagged `sourceType=INTEGRATION` in stage history, and
> the dashboard metrics filter to `CRM_UI`. So the migration will **not** appear as a spike of
> fake calling activity. This is exactly why that filter is in the metric spec.

---

## Phase 4 — Retire `Call Attempted`

This is the only irreversible step, so it comes last and only after Phase 4 verifies clean.

**Recommendation: rename it, do not delete it.**

Rename to `Call Attempted (retired)` and move it to the far right of the board. It ends up
out of the working flow but its id keeps resolving.

Why not delete: 10% of live deals not currently on that stage still have it in their
**history**, and history keeps the stage id forever. We already have proof of what deleting
costs — 13 archived deals reference 4 stage ids that no longer exist and now render as
nothing. Deleting buys tidiness in the board editor and costs the readability of every
historical report that touches those ~100 deals.

If it must be deleted, it has to be empty first — HubSpot will not delete a stage holding
deals. Two archived deals also sit on it and would need handling.

---

## Phase 5 — Verify, inside HubSpot only

1. Zero live deals remain on `Call Attempted` in either pipeline.
2. `No Pickup` holds ~227; spot-check ten against their notes.
3. Both pipelines still carry identical labels in identical order.
4. `No Pickup` reports `isClosed=false` when read back from the API — verify, do not assume.
5. Re-run the owner split and confirm the totals reconcile against the snapshot.

That closes the HubSpot half. The dashboard is a separate job, below.

---

## Phase 6 — Dashboard code (SEPARATE JOB, after all of the above)

We do not use HubSpot's own dashboards or reports — data is pulled out and the dashboard is
built by our GitHub Actions workflow. So nothing inside HubSpot needs a reporting change, and
this phase is deliberately decoupled from the migration.

**Known consequence of doing it after: the dashboard undercounts in the gap.**
`build_dashboard.py` maps stages by label in `LEVEL` / `DEAD_LEVEL`. A stage in neither map
never enters `REACHED`, so deals sitting on it are silently skipped — not a crash, an
undercount. Between the migration and this phase, roughly 227 deals on `No Pickup` will be
invisible to the funnel counts.

The deploy runs hourly and unattended, so those wrong numbers publish on their own. Either
accept the gap knowingly, or disable the schedule in `deploy-dashboard.yml` until this lands.

Both copies need the change:
- `build_dashboard.py` (repo root — the one run locally)
- `lh2-pipeline/dashboard/build_dashboard.py` (the one GitHub Actions deploys)

Changes:
- add `No Pickup` at level 1 (a dial happened, same as the old Call Attempted)
- add `Dead/ColdCall/NoPickup` at level 1, `Dead/GMeet/NoShow` and `Dead/GMeet/Cancelled` at
  level 3, `Dead/ScriptShared/NoShow` at level 4
- keep `Call Attempted` in the map at the same level as `No Pickup`, so historical deals and
  the pre-migration time series still resolve

---

## What this does NOT cover

- **HubSpot workflows and automations** are not visible through the private-app token used
  here. If any workflow references `Call Attempted` by stage id it will silently stop
  matching. Worth one check by someone with portal admin access before Phase 4 — quick to
  rule out, expensive to discover later.
- **The 337 deals with no `lead_source`** are a separate cleanup and are untouched here.
