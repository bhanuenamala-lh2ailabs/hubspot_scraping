# Brief: real-time dashboard + reliable scheduled reports

For whoever picks this up. You get the `lh2-pipeline` GitHub repo and a `.env` file. Everything
below must run on free tiers. Nothing here is prescriptive about *how* — the architecture is
yours to choose and defend.

Read section 2 before you plan anything. The hard part of this job is not the WebSocket.

---

## 1. What exists today

Everything you get is under `dashboard/` in the repo.

| File | What it does |
|---|---|
| `build_dashboard.py` | Pulls every deal from two HubSpot pipelines, walks each deal's stage-change history and its notes, writes `dashboard_data.json` |
| `index.html` | The whole dashboard. One self-contained page, reads that JSON. No server, no framework, no build step |
| `note_rules.py` | Note classifiers. Single source of truth — imported, never copied |
| `daily_report.py` | Builds and sends the 18:30 email. Reads `dashboard_data.json`, so the mail and the dashboard can never disagree |
| `gmail_sender.py` | OAuth send |

**How it updates now.** `.github/workflows/deploy-dashboard.yml` runs `build_dashboard.py` on a
cron, then publishes to GitHub Pages. The page is therefore only ever as fresh as the last
successful run.

**How the mail goes now.** `.github/workflows/daily-report.yml`, `cron: "0 13 * * *"` (13:00 UTC
= 18:30 IST). It pulls its own fresh HubSpot data rather than depending on the dashboard run, so
the manual "Run workflow" button always produces a correct email. There is **no weekly workflow
— that part does not exist yet.**

**A build is slow**: ~1,700 deals, one stage-history call each, plus batched note reads. Minutes,
not seconds. Rate limits are real; 429/5xx retry with backoff is already in there.

---

## 2. Why this needs changing — read the measurement, not the theory

**GitHub Actions `schedule` is dropping most of our runs.** This is measured, not suspected. From
the comment block in `deploy-dashboard.yml`:

> 50 delivered runs against ~336 attempts over two weeks on an hourly cron — **about 15%**.

It gets worse. A tidy every-2-hours schedule (7 slots/day) was tried on 5 Aug and delivered
**zero runs in its first 16 hours** — because cutting attempts cuts deliveries proportionally.
Scheduled runs are *dropped*, not queued, under load, and the top of the hour is the worst minute
available. The current cron works around this with many attempts on deliberately odd minutes
(`:07`, `:37`, `:03`, `:13`, `:23`…).

So there are two separate problems, and the second is the harder one:

1. **The dashboard is stale between builds.** Someone moves a deal and the page does not know.
2. **`daily-report.yml` has exactly ONE cron slot at 13:00 UTC.** Against a ~15% delivery rate,
   a single attempt on the worst-case minute is not a schedule — it is a lottery ticket. The
   dashboard deploy already fights this with redundancy; the mail does not. "6:30 sharp" and
   "one GitHub cron entry" cannot both be true, and reconciling that is the core of task (b).

Note the asymmetry that makes (b) harder than (a): a dropped dashboard build is invisible and
self-healing — the next run republishes fresher data. A dropped email is **gone**. Nobody gets
tomorrow's copy of today's report. Redundant attempts fix the first and would duplicate the
second, so whatever you do for the mail needs an idempotency story: at-most-once per day, and
at-least-once.

---

## 3. What you need to deliver

### (a) HubSpot → dashboard, without waiting for a rebuild
When a deal changes in HubSpot, the dashboard should reflect it. HubSpot can push change events
out; you decide how they reach the page.

Work out for yourself, with reasons:
- Where the receiving endpoint lives, given it must be publicly reachable over HTTPS and free.
  GitHub Pages serves static files only — it cannot receive a webhook. Something else must.
- Whether the page holds an open connection, polls, or something else. "WebSocket" is the shape
  that was asked for; if you conclude something simpler fits better, say so and justify it.
- **The hard part: incremental update.** Every metric is "times a deal ENTERED a qualifying
  stage, on the day it entered, counting only human moves." A HubSpot webhook payload is thin —
  object id, property, new value. It does **not** carry the history walk the metrics need. So
  decide: re-read that one deal's history, or recompute more broadly? What does each cost
  against the rate limit when 40 deals move in an hour?
- What happens to events that arrive while nothing is listening. Free tiers sleep.

### (b) Reports that actually land at 6:30
Daily 18:30 IST, plus a weekly edition 18:30 IST Friday. The weekly does not exist — you are
building it. `daily_report.py` already computes week-to-date internally (`monday`, `WK_FROM`,
`WK_TO`), so the data is there; the report and the schedule are not.

Punctuality is the requirement. Given section 2, decide what actually fires these, how you know
it fired, and what happens when it does not. **A report that silently fails is worse than one
that is late, because nobody notices.** Right now nothing would tell us.

### (c) Keep it free
Everything on free tiers. Document what you used, its limits, and where it breaks if volume
doubles. If free forces a trade-off, name it rather than hiding it.

---

## 4. Constraints — not negotiable

**Secrets.** `.env` holds live credentials — HubSpot, SignalHire, OutFlo, Google Maps, Calendly,
Anthropic. It is not in git and must never be committed. In CI they are repository secrets
(`HUBSPOT_API_KEY`, `GMAIL_TOKEN_JSON`, `GMAIL_CLIENT_JSON`) written to disk at run time and
shredded in an `if: always()` step. Keep that pattern — credentials must not survive a job even
on failure. If you leak a key, say so immediately; rotating quietly is worse.

**Mail discipline.** The ONLY automated mail is the 18:30 report to the Supply Head. Do not add
notification mails, alerts or digests. There is a `lead_vcf_notifier.py` with an
`--install-task` flag that once mailed 7 people every 15 minutes; its scheduled task is
**disabled and must stay disabled**. Do not run that flag. Test sends go to
`bhanu.enamala@lh2.ai` — `daily_report.py --test` already routes there.

**`daily_report.py` refuses to send stale data** (`REFUSING TO SEND — data is from …`) unless
`--force`. That guard exists because a mail built from yesterday's JSON looks completely normal
and is completely wrong. Do not paper over it with `--force` in a workflow; if it trips, fix the
build ordering.

**Never hand-copy a definition.** `note_rules.py` is imported by both the dashboard build and
the local mailer. An earlier hand-copy of the KPI definitions drifted and inflated dial counts
2.7×. If a rule changes, change it in `note_rules.py`, once.

**Only human moves count.** ~42% of stage-history entries are `sourceType=INTEGRATION` — bulk
API writes, including our own migrations. Counting those once rendered a 245-deal migration as
the biggest calling day in company history. Any code touching stage history must keep the
`sourceType == "CRM_UI"` filter. **A webhook fires for integration writes too** — including
writes made by your own code. Filter them or you will build a feedback loop.

**Timezone is IST.** HubSpot returns UTC. `ist_day()` converts. A day-boundary bug moves work
onto the wrong date and nobody spots it for a week.

**The CEO dashboard view is off limits.** Leave it exactly as it is.

---

## 5. Acceptance

Show these working, not described:

1. Move a deal in HubSpot. The dashboard reflects it without a manual rebuild. State the lag.
2. Kill your receiver, move two deals, bring it back. Show what happened to those two and
   explain what you chose to do about gaps.
3. The 18:30 mail lands at 18:30 IST three days running, on days you did not touch anything.
   Given the ~15% baseline, show *why* yours lands — the mechanism, not three lucky days.
4. The Friday weekly lands, covering Monday→Friday.
5. Make it fail deliberately — bad token, HubSpot 429, receiver down, missed slot — and show
   that a human finds out.
6. One page of architecture: what runs where, which free tier, what the limits are, what breaks
   first at 10× volume.

---

## 6. Gotchas already paid for

- **`schedule` drops runs; see §2.** Odd minutes, many attempts. Do not "tidy up" the cron list.
- **`toObjectId` comes back as an int** in the v4 associations API while every other object id is
  a string. Comparing without casting silently matches nothing — this bug once made a dedup
  check pass everything.
- **`hs_v2_date_entered_current_stage` is the only stage-date property in this portal.** There
  are no per-stage `hs_date_entered_<id>` properties; querying them returns zero rows, not an
  error. It is also only a valid filter for a window ending *now* — a later move overwrites it,
  so it under-counts for a window ending in the past.
- **Two pipelines, identical stage labels, different ids.** `default` (Scraped) and `2425754306`
  (Campaign). Resolve stage ids per pipeline; never hardcode one.
- **`Call Attempted` was retired on 2026-08-05** and its deals moved to `No Pickup`, but it
  survives in ~100 deals' history. `ALIAS` maps it so the series does not cliff.
- **Transport errors, not just HTTP errors.** ~1,700 sequential calls over minutes. Six local
  builds died on 6 Aug because `URLError`/`SSLError` escaped an `except HTTPError`. Catch
  broadly, retry.
- **`actions/upload-artifact@v4` and `deploy-pages@v4` are on the Node-20 deprecation list** and
  are being force-run on Node 24 — that already broke the dashboard workflow once. Both are on
  v5 now. Expect more of this and read the failure rather than re-running.
- **A "no data" result is usually a bug.** Twice here an empty result meant a swallowed
  exception, not an empty reality: archive.org throttling reported 193 of 200 domains as "never
  archived", and a missing file in a load list reported 498 records where 810 existed.
  Distinguish *missing* from *absent*, and log which one you got.
- **`crm_mirror/` is not in this repo.** It is a local-only sibling directory on one laptop.
  `build_dashboard.py` originally imported the note rules from there — it resolved on the laptop
  and raised `ImportError` in CI, where the note KPIs would have been silently empty on every
  deployed build. That is why `note_rules.py` now sits inside `dashboard/`. If you find yourself
  importing across that boundary, you are writing a bug that only appears in production.

---

## 7. Where to look

| Thing | Path |
|---|---|
| Dashboard builder | `dashboard/build_dashboard.py` |
| Dashboard page | `dashboard/index.html` |
| Note classifiers | `dashboard/note_rules.py` (run it directly — it self-tests) |
| Daily mailer | `dashboard/daily_report.py` |
| Gmail sending | `dashboard/gmail_sender.py` |
| Deploy workflow | `.github/workflows/deploy-dashboard.yml` (read the comments) |
| Daily mail workflow | `.github/workflows/daily-report.yml` |
| Dashboard readme | `dashboard/README.md` |

**Not in the repo, ask for it:** `daily_report.py`'s docstring points at
`docs/sop/DASHBOARD_METRIC_SPEC.md`, which lives in the local-only tree alongside `crm_mirror/`.
It is the written definition of every metric. Ask for a copy before you touch metric code —
inferring the definitions from the implementation is how the 2.7× drift happened.

**One warning about the mailer's scope:** the Gmail token has `gmail.send` and nothing else. It
can send; it cannot read, modify or recall. A mail to the wrong address cannot be pulled back —
that has already happened here once. Test sends go to `bhanu.enamala@lh2.ai` only.
