# Activity tracking when everyone works the whole funnel

Draft plan — 7 Aug 2026. Written after checking what HubSpot actually holds, not from assumption.

---

## 1. The diagnosis, in numbers

Yesterday (6 Aug), these are **all** the events the system counted:

| Person | Countable events |
|---|---|
| Lamiya | 33 |
| Yuktha | 31 |
| Ishpreet | 4 |
| Yash | 3 |
| Shobit | 2 |

Ishpreet did not do 4 things yesterday. He did 4 things **that moved a deal from one stage to another**.

The cause is structural. Every activity number we report is derived from one source: a `dealstage`
change with `sourceType = CRM_UI`, credited to whoever clicked it. Nothing else is counted, because
nothing else is recorded:

| HubSpot object | Records in last 7 days |
|---|---|
| **Calls** | **0** |
| **Meetings** | **0** |
| Notes | 411 |
| Tasks | 91 |

**There is not a single call object in this portal.** "Calls attempted" and "calls connected" are not
call records — they are the deal arriving at the `Call Attempted` and `Interested` stages. So:

- A caller who dials 40 numbers and reaches nobody generates **0** "attempted" if those deals were
  already past Cold Call.
- A caller who spends the day chasing three script results generates **0** of anything until a
  result actually lands.

That second line is exactly the complaint: the GTM analysts' call numbers looked terrible because they
were doing work the instrument cannot see.

---

## 2. The core confusion to fix

Two different questions are being answered with one field:

| Question | Correct home | Cardinality |
|---|---|---|
| *What state is this deal in?* | `dealstage` | **one per deal**, moves forward |
| *What did this person do today?* | activity objects | **many per deal per day** |

A deal occupies exactly one stage. Three follow-up calls to chase one script result produce **at most
one** stage change, and usually zero. No amount of stage redesign changes that — it is a cardinality
mismatch, not a granularity problem.

> **So: adding stages will not fix this.** More stages give a finer description of the *deal*. They
> give no extra room to record *repeated effort by a person*. This is the main question asked, and the
> answer is no.

---

## 3. Options considered

| Option | Fixes the problem? | Cost | Verdict |
|---|---|---|---|
| **A. Add more stages** | No — cardinality mismatch above | Medium (pipeline surgery, retraining) | **Reject** |
| **B. Everyone writes a note per touch; we parse text** | Partly | Low to set up, high to maintain | **Fallback only** |
| **C. Log calls as Call objects with dispositions** | **Yes** | Low — native HubSpot, one click | **Recommend** |
| **D. Do nothing, judge by outcomes only** | No — punishes chase work | Zero | **Reject** |

**Why not B as the primary.** Free text needs parsing and never stops needing it; every new phrasing
is a silent miss. I already hit this exact failure today — a `not relevant` regex that read
*"Not fully relevant…"* as an approval. Two of four notes misclassified. Text parsing is a
maintenance tax we should pay only where nothing structured exists.

Note compliance is also uneven: over 7 days Lamiya wrote **3** notes but completed **60** tasks;
Yuktha wrote 28. Building the primary metric on the least consistent behaviour is the wrong bet.

**Why C.** The Call object is what HubSpot ships for precisely this. It is timestamped, owned,
attaches to the deal **without moving its stage**, and carries `hs_call_disposition` (Connected /
No answer / Left voicemail / Busy / Wrong number) and `hs_call_duration`. One tap in the mobile app.
It makes the invisible work visible without touching the pipeline at all.

Right now `hs_call_disposition` exists in the portal but **has no options configured** — that is a
5-minute settings change and is step 1 below.

---

## 4. Recommended plan

### Phase 1 — make the work recordable (this week)

1. **Configure call dispositions** in HubSpot settings: `Connected`, `No answer`, `Left voicemail`,
   `Busy`, `Wrong number`, `Not reachable`.
2. **Rule for the team, one line:** *every dial gets a call log with a disposition — including the
   ones nobody picks up.* This is the whole behaviour change.
3. **Non-call chases** (email / WhatsApp / LinkedIn follow-up) get a note prefixed `CHASE:`.
   One structured token, not free-form parsing.
4. **Stop reporting per-role quotas.** They no longer describe anyone's job.

### Phase 2 — extract everything, per person, per day

One collector, five sources, all keyed on owner + IST day:

| Source | Endpoint | Gives us |
|---|---|---|
| Calls | `/crm/v3/objects/calls/search` on `hs_timestamp` | dials, disposition, duration |
| Meetings | `/crm/v3/objects/meetings/search` | VCs actually held |
| Notes | `/crm/v3/objects/notes/search` | chase work, context |
| Tasks | `/crm/v3/objects/tasks/search` on completion date | follow-through |
| Stage moves | `propertiesWithHistory=dealstage`, `sourceType=CRM_UI` | outcomes (unchanged) |

Keep the existing rule that **only `CRM_UI` moves count** — 42% of stage history is integration
writes, and counting those once rendered our own 245-deal migration as the biggest calling day in
company history.

### Phase 3 — buckets

Bucket by **type of work**, not by role. Every person gets every bucket.

| # | Bucket | Built from | Why it exists |
|---|---|---|---|
| 1 | **Dials** | call objects, any disposition | raw effort, finally visible |
| 2 | **Conversations** | calls with `Connected` + meetings held | effort that reached a human |
| 3 | **Asset progression** | stage entries: Script Shared, Results Received, Evaluation | moving the codebase forward |
| 4 | **Commercial** | Negotiation, Contract Signed, Closed/Won, LoC | money |
| 5 | **Chase** | `CHASE:` notes + completed tasks with no stage move | **the currently invisible work** |

Two summary figures per person, which matter more than any single bucket:

- **Deals touched** — distinct deals with *any* activity that day. The honest measure of a day's work.
- **Touches per outcome** — dials ÷ conversations, conversations ÷ VCs. Shows efficiency without
  punishing someone whose day was legitimately spent chasing.

### Phase 4 — end-of-day view

Extend the existing 6:30 pm mail and dashboard. One row per person, five buckets plus the two
summaries. No role column.

```
                 Dials  Conv  Asset  Comm  Chase | Touched  Notes
Yuktha             41    12      3     0      7  |    38
Lamiya             38     9      2     0     11  |    41
Ishpreet           12     6      5     1      9  |    22
Shobit              4     3      2     2      4  |     9
```

Targets move from *per-role quota* to **a floor on total touches plus a team-level outcome target**.
That way a day spent entirely on script chasing reads as a full day, because it was one.

---

## 5. What I am NOT proposing

- **No new pipeline stages for activity.** Section 2.
- **No retiring of notes.** They stay for context and for the chase bucket.
- **No change to the LoC / sprint numbers.** Those are asset facts and already work.

Separately pending, unrelated to this: the *outcome-is-the-stage* revision (5 stages to add,
`Call Attempted` to retire). That is about describing deal state accurately and should be decided on
its own merits — it does not solve the activity problem and this plan does not depend on it.

---

## 6. Risks

| Risk | Mitigation |
|---|---|
| **Call logging compliance.** The whole plan rests on it. | It is one tap in the mobile app. Report per-person logging rate for the first two weeks so gaps are visible immediately. |
| **Week-1 numbers look worse.** Dials were never counted; now no-answers count too. | Say so in advance. The first fortnight is a baseline, not a performance record. |
| **`CHASE:` prefix drifts.** | Only one token to get right. Report unparsed notes so drift is caught, rather than silently dropped. |
| **Double counting** — a call logged *and* a stage moved | Buckets are disjoint by construction: dials come only from call objects, outcomes only from stage moves. |

---

## 7. Open questions for you

1. **Mandate call logging, or trial it with one person for a week first?**
2. **Does a no-answer dial count toward a daily floor?** I would say yes — otherwise we recreate the
   exact bias we are removing.
3. **Who owns the `CHASE:` convention** and who tells the team?
4. Should Shreyas and Yash be in the same scorecard? They are on the same funnel but a different
   source book — Shreyas wrote 50 notes in 7 days, the most of anyone, and currently appears nowhere.
