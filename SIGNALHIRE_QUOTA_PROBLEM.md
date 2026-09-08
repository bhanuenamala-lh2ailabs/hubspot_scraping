# SignalHire `searchByQuery` quota — problem statement

**For:** (a) a research pass, (b) our SignalHire account contact.
**Prepared:** 18 Aug 2026, 15:30 IST. Supersedes `SIGNALHIRE_SEARCH_QUOTA_QUESTIONS.md` (17 Aug),
which is now partly out of date — the reset-cadence question in it has been answered empirically.

---

## 1. What we use the API for

We identify the founder/CEO of small Indian IT-services companies, then get their mobile number.
Two calls per company:

1. **`POST /api/v1/candidate/searchByQuery`** — company + seniority filter → matching people
   (uid, name, title, employment history). **No contact data.** This is the call being capped.
2. **`POST /api/v1/candidate/search`** — the reveal. uid → phone + email. Spends **reveal credits**.

The two pools are clearly separate: reveal has kept working normally throughout every search
outage. Reveal balance is 4,737 and only moves when we reveal.

Our exact search payload:

```json
{ "currentCompany": "<company name>",
  "location": "India",
  "size": 3,
  "currentTitle": "founder OR co-founder OR cofounder OR owner OR CEO OR chief executive OR managing director OR CTO OR chief technology OR chairman OR president" }
```

## 2. The blocker

We get HTTP **402** far earlier than expected, and the point at which it fires is **not
reproducible between days**.

```
{"message":"You have reached your daily search attempts quota.
  Try it again later or contact support@signalhire.com to discuss a special offer."}
```

## 3. Measured facts

### 3.1 Reset cadence — ANSWERED: roughly 24 hours from exhaustion, not a calendar day

| Timestamp (IST) | Elapsed since exhaustion | `searchByQuery` |
|---|---|---|
| 17 Aug 14:39:55 | 0 — quota hit here | 402 |
| 17 Aug 22:50 | ~8 h | 402 |
| 18 Aug 08:32 | ~18 h | 402 |
| **18 Aug 14:43** | **~24 h 03 m** | **200 — working** |
| 18 Aug 15:15 | quota hit again | 402 |
| 18 Aug 15:21 (×3 probes) | — | 402 |

It is **not** a UTC calendar-day reset (that would have cleared at 05:30 IST) and **not** a local
calendar day. It cleared at almost exactly 24 hours after exhaustion.

### 3.2 The volume is inconsistent between cycles — THIS IS THE CORE PROBLEM

| Cycle | Search calls made before 402 | Profiles returned | `size` used |
|---|---|---|---|
| 17 Aug | **297** | not logged | mixed 10 → 4 → 3 |
| 18 Aug | **171** (85 + 86 in two runs) | **~318** | 3 throughout |

Same account, same endpoint, same day-length, **but 297 one cycle and 171 the next.**

### 3.3 It is almost certainly metered per CALL, not per profile

On 18 Aug we logged every response. Across the 86 calls of the second run:

- **160 profiles returned in total — 1.86 per call on average**, not 3
- **24 of 86 calls (28%) returned ZERO profiles**

Extrapolating the first run at the same rate, the whole of 18 Aug consumed roughly
**318 profiles across 171 calls** — and still hit 402.

That rules out a ~2,000-profile budget, which is what we had been planning against. The error
string itself says *"search **attempts** quota"*, which also points to calls rather than results.

**Consequence:** our optimisation of lowering `size` from 10 → 3 to conserve quota may have
achieved nothing at all. If the meter counts calls, `size` is free and we should raise it back to
improve per-company recall.

### 3.4 What we cannot reconcile

If the cap were a fixed number of calls per 24 h, both cycles should stop at the same number.
They did not (297 vs 171). Our working hypothesis is a **rolling 24-hour window**: on 18 Aug at
14:45 only the oldest slice of the previous day's calls had aged out, so we recovered ~171 slots
rather than a full allowance. We cannot confirm this from the outside — there is no endpoint that
reports remaining search quota, and the 402 body carries no counter, limit or reset timestamp.

## 4. Questions for SignalHire

1. **Is the `searchByQuery` cap counted per API CALL, or per PROFILE returned?** Our evidence says
   per call. Please confirm, because it decides whether `size` costs us anything.
2. **Is it a fixed daily allowance, or a rolling 24-hour window?** Our two cycles (297 then 171)
   are inconsistent with a fixed daily number but consistent with a rolling window.
3. **What is the exact limit on our plan?** We have never been told a number.
4. **Why 297 on one cycle and 171 on the next?** If a rolling window explains it, please confirm
   the window length and how partial recovery works.
5. **Is there any endpoint that reports remaining search quota?** We can only see reveal credits
   via `/credits`; nothing equivalent exists for search, so we discover the limit by hitting it and
   losing the run.
6. **Can the 402 response include the limit, the amount used, and a reset timestamp?** Even a
   `Retry-After` header would let us schedule instead of guess.
7. **Does `scrollId` pagination on the same query cost another unit?** We do not paginate today,
   but it changes our design if it is free.
8. **Can this limit be raised, and at what price?** This is the commercial question — see below.
9. **Is `searchByQuery` a supported long-term endpoint on our plan**, or legacy/soft-deprecated?
   We are building our pipeline on it.
10. **Is there a bulk or batch alternative** — one request carrying many company names — that is
    metered more favourably than one call per company?

## 5. Why it matters commercially — our actual constraint

Our pipeline is: **company → searchByQuery → decision-maker → reveal → mobile → sales call.**

The search cap is now the **binding constraint on the entire sales operation**, ahead of headcount:

| Stage | Capacity |
|---|---|
| Companies we can search per cycle | **~170–300** (observed) |
| Of those, yielding a dial-ready contact | ~36% |
| Dial-ready leads produced per cycle | **~60–110** |
| Leads our callers consume per day | **~54** (measured today) |

So a full day's search allowance produces barely one to two days of calling work. We hold a
qualified backlog of **~3,100 companies**; at the observed rate that is **10–18 working days** just
to enrich, before any selling happens.

**We would like to buy more search volume.** We are not asking for a favour — we want to know the
number, the price, and whether a higher tier or bulk endpoint exists. If the answer is that ~300
per 24 h is the ceiling on any plan, we need to know that too, because we would then design
around it (or add a second provider).

## 6. What we would like back, concretely

- The exact metering unit (calls vs profiles) and the exact limit on our current plan
- Whether the window is daily-fixed or rolling, and its length
- A quota-remaining endpoint, or at minimum limit/used/reset in the 402 response
- Pricing for a materially higher search allowance — we would want **1,000–3,000 company searches
  per day**, sustained
- Confirmation of whether `size` affects cost, so we can tune recall correctly

---

### Appendix — reproducibility

- Account: paid SignalHire API plan, `apikey` header auth, server-to-server.
- Reveal pool: 4,737 credits remaining, unaffected by every search outage.
- Endpoint: `https://www.signalhire.com/api/v1/candidate/searchByQuery`
- We pace calls at ~0.35 s and have never seen 429 — this is a quota wall, not rate limiting.
- Raw per-call logs (company, total, profiles returned, titles) are retained in
  `godown/founder_id/searchq_raw_log.json` and can be shared if useful.
