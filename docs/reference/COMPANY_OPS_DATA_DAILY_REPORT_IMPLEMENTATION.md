# Company Ops Data — Daily Full-Funnel Report: Implementation Spec + Prompt

This applies the methodology in [`DAILY_FULLFUNNEL_METHODOLOGY.md`](DAILY_FULLFUNNEL_METHODOLOGY.md)
(the LH2 Codebase-Supply funnel's end-of-day pull → report → mail system) to the **Company Ops
Data** funnel — a different HubSpot portal, described by the `GTM_Caller_SOP.pdf` the team
shared (33-stage funnel, cold-call + LinkedIn entry, ending Closed/Won).

Read the methodology doc first — this file does not repeat *why* each mechanism works, only
*how it maps* onto this specific funnel's vocabulary. Where a design decision needed real
historical data I don't have (this is a different HubSpot portal/codebase), it's flagged as a
**decision point** rather than asserted as fact — confirm each one before shipping.

---

## 1. Stage vocabulary, extracted from the SOP

These are the exact stage names as written in `GTM_Caller_SOP.pdf`. The SOP's own footer states
"33-stage funnel" — the list below has 30 named boxes from the diagram/table; **before writing
any code, pull the authoritative list from the portal itself**:
```
GET /crm/v3/pipelines/deals          (using whichever key this portal uses — hubspot_kartik
                                       per this repo's README, not the hubspot_key used for
                                       the Scraped/Campaign pipelines)
```
Reconcile that live list against the table below and fix any gap (a stage the SOP didn't
diagram, or a naming mismatch) before finalizing `METRICS`.

| # | Stage (as written in SOP) | Kind |
|---|---|---|
| 1 | Cold called assigned | Live — entry point |
| 2 | LinkedIn sent | Live — automated, LinkedIn branch |
| 3 | LinkedIn connected | Live — automated, LinkedIn branch, feeds same queue |
| 4 | No pickup | Live/loop — callback task set +1 day |
| 5 | Dead: Cold Call / Wrong Fit | Dead — never dialled (screened out) |
| 6 | Dead: Cold Call / Wrong Number | Dead — number invalid/unreachable |
| 7 | Dead: Cold Call / Not Interested | Dead — picked up, said no |
| 8 | Dead: Cold Call / No Pickup | Dead — rang out after repeated tries |
| 9 | Replied | Live — picked up and engaged |
| 10 | Dead: Replied / Not Interested | Dead — replied once, then declined |
| 11 | 1st interest sent | Live |
| 12 | 1st interest follow up | Live |
| 13 | Dead: 1st Interest / No Response | Dead — went quiet |
| 14 | Dead: 1st Interest / Not Interested | Dead — responded, said no |
| 15 | Discovery call | Live — mandatory GMeet Link rule applies |
| 16 | Call rescheduled | Live/loop — lead asked to move it |
| 17 | Dead: Discovery Call / No Show | Dead — booked, didn't join |
| 18 | Dead: Discovery Call / Rejected by LH2 | Dead — we declined after the call |
| 19 | Dead: Discovery Call / Not Interested | Dead — they declined after the call |
| 20 | One pager requested | Live |
| 21 | One pager follow up | Live |
| 22 | Dead: One Pager / Not Received | Dead — never sent back |
| 23 | One pager received | Live — mandatory One Pager Results rule applies |
| 24 | Dead: One Pager / Low Data Quality | Dead — didn't meet the bar |
| 25 | LOI signed | Live |
| 26 | Dead: LOI / Pricing Not Agreed | Dead |
| 27 | Dead: LOI / Contractual Not Agreed | Dead |
| 28 | Contract signed | Live — closer's track |
| 29 | Ops data handover done | Live |
| 30 | Payment initiation | Live |
| 31 | Closed/Won | Terminal |

Two mandatory deal-property rules the SOP calls out, which have no LH2 equivalent — see §5:
- **GMeet Link** (or `GMeet1 Link` for a second meeting) must be set the moment a Discovery Call
  is booked or held.
- **One Pager Results** must be set the moment a deal reaches One pager received.

---

## 2. `METRICS` — proposed mapping

Following the methodology's own rule: **explicit membership, never cascading** — every stage
that should count toward a KPI is listed, full stop.

```python
METRICS = {
    "att":  {"No Pickup", "Dead: Cold Call / Wrong Number", "Dead: Cold Call / Not Interested",
             "Dead: Cold Call / No Pickup", "Replied"},
    "conn": {"Dead: Cold Call / Not Interested", "Replied"},
    "rep":  {"Replied"},
    "int1": {"1st interest sent"},
    "fu1":  {"1st interest follow up"},
    "dc":   {"Discovery call", "Dead: Discovery Call / No Show",
              "Dead: Discovery Call / Rejected by LH2", "Dead: Discovery Call / Not Interested"},
    "resch":{"Call rescheduled"},
    "opr":  {"One pager requested"},
    "opfu": {"One pager follow up"},
    "oprec":{"One pager received"},
    "loi":  {"LOI signed"},
    "cs":   {"Contract signed"},
    "handover": {"Ops data handover done"},
    "pay":  {"Payment initiation"},
    "won":  {"Closed/Won"},
}
```

**Decisions baked in here, mirroring the two exclusion examples in the methodology doc — confirm
each one with the team before trusting the numbers:**

1. `Dead: Cold Call / Wrong Fit` is **excluded from `att`**, on the same logic as LH2's own
   `Dead/ColdCall/WrongFit` exclusion — the SOP's own flowchart labels this branch "screened out,
   **never dialled**," so it's not a dial attempt.
2. `dc` (discovery-call-slot-consumed) **includes** `Dead: Discovery Call / No Show`, using the
   same "did the caller's time actually get consumed" test the methodology doc used to justify
   including `Dead/GMeet/NoShow` in LH2's `vc` — the caller held the slot even though the lead
   didn't join. It also includes `Rejected by LH2` and `Not Interested`, because both explicitly
   happen **after** the call per the SOP's own wording ("after the call"). **`Call rescheduled`
   is deliberately excluded from `dc`** — the call hasn't happened yet, it's a loop back to
   waiting, analogous to `Dead/GMeet/Cancelled` being excluded from LH2's `vc` (no time
   consumed). This is the single most debatable call in this mapping — verify it matches how the
   team actually thinks about a "discovery call held" count before shipping.
3. `Dead: One Pager / Not Received` and `Dead: One Pager / Low Data Quality` are **not** folded
   into `oprec` — receiving nothing, or receiving bad data, is not the same event as receiving
   usable data. They're real dead-ends, just not KPI-countable as "received."
4. `Dead: 1st Interest / No Response` and `Dead: 1st Interest / Not Interested` are left **out**
   of every KPI except appearing in the eventual "why deals died" note-adjacent breakdown (there
   is no direct LH2 analog metric for this — the methodology's `KPI` list is deliberately
   minimal, one number per real milestone, not one per dead-end).
5. `LinkedIn sent` / `LinkedIn connected` are **automated, non-human stage moves** — per the SOP,
   OutFlo drives them, not a caller. They should **not** appear in `METRICS` at all (a caller
   didn't do anything to cause them) — but see §6, they still matter for excluding these deals
   from `sourceType == "CRM_UI"` attribution correctly, since a bot-driven move must not be
   misread as human work the same way `daily_fullfunnel_mail.py` already excludes non-`CRM_UI`
   history entries in the source funnel.

Human-facing `KPI` list (display order/labels only, once `METRICS` above is confirmed):
```python
KPI = [("att","Calls attempted"), ("conn","Calls connected"), ("rep","Replied"),
       ("int1","1st interest sent"), ("fu1","1st interest follow-up"),
       ("dc","Discovery calls held"), ("resch","Discovery calls rescheduled"),
       ("opr","One-pagers requested"), ("opfu","One-pager follow-ups"),
       ("oprec","One-pagers received"), ("loi","LOIs signed"), ("cs","Contracts signed"),
       ("handover","Ops data handovers done"), ("pay","Payments initiated"),
       ("won","Closed/Won")]
```

---

## 3. `NOTE_RULES` — starter set, NOT empirically derived (see decision point below)

The methodology doc is explicit that these must come from reading **real notes this team
actually wrote**, not be invented — "Note buckets were derived by reading the actual 106 notes
written on 6-7 Aug, not invented." I have no access to this portal's real note history, so the
list below is a **starting point built from the SOP's own procedural language**, ordered with
the same negation-before-positive discipline the methodology doc insists on. Treat it as a
draft to be corrected against a real sample — porting checklist item 5 in the methodology doc
applies directly here.

```python
NOTE_RULES = [
    ("System note",        r"deadpool wave|relevance check|test deal|lead.?gen form import"),
    ("Wrong number",       r"wrong number|invalid number|disconnected|unreachable"),
    ("No pickup",          r"no answer|didn.?t pick|voicemail|switched off|ring(?:ing)? out|no pickup"),
    ("Wrong fit",          r"wrong fit|not a fit|doesn.?t match|out of scope"),
    ("Not interested",     r"not interested|declined|said no"),
    ("Callback booked",    r"call(?:ed)? back|reschedul(?:e|ed|ing)|callback"),
    ("Chase sent",         r"whatsapp|followed up|email sent|chased"),
    ("GMeet fixed",        r"gmeet|discovery call (?:fixed|booked|scheduled|held)"),
    ("One pager progress", r"one.?pager"),
    ("LOI progress",       r"\bloi\b"),
    ("Contract progress",  r"contract (?:signed|sent)"),
    ("Handover progress",  r"handover|data migrat"),
    ("Payment progress",   r"payment"),
    ("Interested",         r"\binterested\b"),
]
```
`BUCKETS = [b for b, _ in NOTE_RULES] + ["Other"]`.

**Decision point:** run this against a real week of this team's notes once collected, look at
what falls into `Other`, and add a rule per real pattern found — exactly the porting procedure
the methodology doc describes. Do not ship this list unverified.

---

## 4. `BUCKET_MAP` — suppressing double-counts

Same test as the methodology doc: *"if I already counted this via a stage move, would counting
the note too be counting the same real-world action twice?"*

```python
BUCKET_MAP = {
    "GMeet fixed":        None,   # already counted via the "dc" KPI
    "One pager progress": None,   # already counted via "opr"/"opfu"/"oprec"
    "LOI progress":       None,   # already counted via "loi"
    "Contract progress":  None,   # already counted via "cs"
    "Handover progress":  None,   # already counted via "handover"
    "Payment progress":   None,   # already counted via "pay"
    "Interested":         None,   # restates "conn"/"rep"
}
```
All seven still add their deal to that owner's engaged-set (§6) — they just don't inflate the
note-only tally a second time.

`NOTE_ONLY` table (the buckets that survive into the report, i.e. everything above **not**
mapped to `None`):
```python
NOTE_ONLY = {
    "No pickup":       "Dialled, nobody answered (re-dials included)",
    "Wrong number":    "Number wrong / dead — needs re-enrichment",
    "Wrong fit":       "Screened out before or after the dial",
    "Not interested":  "Said no on the call",
    "Callback booked": "Reached them, call arranged for later",
    "Chase sent":      "Followed up by WhatsApp / mail / text",
    "System note":     "Machine-written, excluded from human-work tallies",
    "Other":           "Written down but not yet classified",
}
```

---

## 5. Compliance checks — new, no LH2 analog

The SOP has two "mandatory rule" properties LH2's funnel doesn't have. These aren't KPIs (they
don't measure volume of work) — they're **data-hygiene gates**, and belong in their own report
section, computed as a simple property-presence check against the candidate-deal set already
pulled in §2.3 of the methodology doc:

```python
# Every deal currently at or past "Discovery call" should have GMeet Link set.
gmeet_missing = [d for d in deals_at_or_past("Discovery call")
                 if not d["properties"].get("gmeet_link")]

# Every deal currently at or past "One pager received" should have One Pager Results set.
onepager_missing = [d for d in deals_at_or_past("One pager received")
                    if not d["properties"].get("one_pager_results")]
```
Report these as a plain count (and ideally the deal names) per owner — "3 deals at Discovery
Call with no GMeet Link" is exactly the kind of thing a pod lead needs to chase, and it's a
direct, mechanical readout of the SOP's own "before you close your queue" checklist.

**Decision point:** confirm the actual internal property names for `GMeet Link`, `GMeet1 Link`,
and `One Pager Results` on this portal (`GET /crm/v3/properties/deals` and grep for the labels)
— the snake_case names above are guesses at HubSpot's usual internal-name convention, not
confirmed values.

---

## 6. Daily target (100/person) — reuse "leads engaged" as-is

The SOP's daily target — *"call attempted... and followed up by WhatsApp or email... every lead
you're assigned must be engaged today"* — maps directly onto the methodology doc's existing
**"leads engaged"** headline metric (§6 there): the deduplicated union of "deals I moved a stage
on" and "deals I wrote a note on." No new mechanism needed — just add a target column:

```python
target = 100
attainment_pct = round(100 * len(eng[oid]) / target, 1)
```
Render it next to the existing "Leads engaged" number in the report table (`87/100 — 87%`).

---

## 7. Net-new / reject-set — re-derive `WRONG_SPOC`-equivalent

The methodology doc's reject-set excludes deals ending in `WrongNumber` or matching a
`WRONG_SPOC` note regex, on the reasoning "a wrong number or wrong SPOC is not a lead we
engaged, it's a list defect." Directly analogous here:

```python
if str(lab).endswith("Wrong Number"): reject.add(did)
if raw == "Wrong number" or WRONG_SPOC.search(t): reject.add(did)
```
**Decision point:** confirm whether this SOP's callers ever encounter a "wrong SPOC, gave me
another number" situation distinct from a flat-out wrong number — if the SOP genuinely has no
such case (nothing in the PDF suggests one), the `WRONG_SPOC` regex may be droppable here, or
kept narrowly scoped just to `Wrong number`.

---

## 8. Everything else — reused unchanged

Per the methodology doc's own closing checklist, these transfer with zero changes once the auth
key and `PEOPLE` list point at the new portal:
- The two-tier candidate-then-history API call pattern (§2.2–2.4 there).
- IST day-bucketing (`ist_day()`), including the "window must end today" guard on
  `hs_v2_date_entered_current_stage` — **check first** whether this portal has real
  `hs_date_entered_<stage_id>` properties; if it does, use those and drop the guard entirely.
- Notes pull + note→deal association batch-read.
- The `eng[oid]` / `stage_deals[oid]` set-based dedup logic for "leads engaged."
- HTML/plaintext rendering and `gmail_sender.send()` (or this codebase's own mail transport, if
  different — confirm before assuming `gmail_sender.py` is even present here).

---

## 9. The prompt — hand this to an agent working *in that other codebase*

Copy everything in the fenced block below into a fresh session that has access to the Company
Ops Data HubSpot portal and its own repo. It is self-contained — it doesn't assume that session
has seen this conversation.

```
I need you to build an end-of-day HubSpot report + email system for the Company Ops Data
funnel, modeled exactly on a working system from a sibling project (LH2's Codebase-Supply-Funnel
daily report). I have two spec documents describing it — read both in full before writing any
code:

1. DAILY_FULLFUNNEL_METHODOLOGY.md — the generic, pipeline-agnostic mechanics: how candidate
   deals are found via a broad hs_lastmodifieddate search then narrowed by
   hs_v2_date_entered_current_stage, how full dealstage history is pulled per candidate and
   filtered to sourceType=="CRM_UI" only (never count API/integration-driven moves), how
   timestamps convert to IST calendar dates, how notes are pulled and associated back to deals,
   and — most importantly — the three-layer measurement model: Stage KPIs (METRICS dict, exact
   stage-label membership, never cascading), Note-only activity (ordered regex NOTE_RULES, first
   match wins, negations before positives), and "leads engaged" as the deduplicated union of
   both, with BUCKET_MAP preventing a note from double-counting a KPI its stage-move already
   captured.

2. COMPANY_OPS_DATA_DAILY_REPORT_IMPLEMENTATION.md — this funnel's specific instantiation:
   proposed METRICS, a starter (NOT verified) NOTE_RULES set, BUCKET_MAP, two new compliance
   checks this funnel has that the source system doesn't (GMeet Link must be set once a deal
   reaches Discovery Call; One Pager Results must be set once a deal reaches One Pager Received),
   and how the SOP's "100 leads engaged per person per day" target maps onto the existing
   "leads engaged" metric with no new mechanism needed.

Before writing code:
- Pull GET /crm/v3/pipelines/deals on this portal and reconcile the live stage list against the
  table in the implementation doc — fix any naming mismatch.
- Pull GET /crm/v3/properties/deals and confirm the real internal property names for GMeet Link,
  GMeet1 Link, and One Pager Results — the implementation doc's guesses are unverified.
- Check whether this portal has real hs_date_entered_<stage_id> properties per stage. If it
  does, use those instead of hs_v2_date_entered_current_stage and drop the
  "window-must-end-today" constraint entirely — note this in your build.
- Collect a real sample of this team's actual notes (at least a few days' worth) and rebuild
  NOTE_RULES against what people actually wrote, the same way the source system's rules were
  derived — don't ship the starter list unverified. Look specifically at what falls into
  "Other" and add rules for real patterns you find.
- Confirm the two flagged judgment calls in the implementation doc before trusting the numbers:
  (a) whether "Dead: Discovery Call / No Show" should count toward "discovery calls held" (the
  proposed answer is yes, on a consumed-caller-time test — verify this matches how the team
  actually thinks about it), and (b) whether a WRONG_SPOC-style reject-set regex is even needed
  for this funnel, or whether "Wrong Number" alone covers it.
- Confirm which owners (GET /crm/v3/owners on this portal) should appear in the report, and
  which private-app key/env var this portal uses for the Bearer token.

Build:
- A METRICS dict and KPI display list per the implementation doc, imported from one canonical
  location (not hand-copied elsewhere).
- NOTE_RULES + classify()/plain() following the source system's ordering discipline, plus its
  small self-test block of real note-text -> expected-bucket pairs.
- BUCKET_MAP wired so no note double-counts a stage-driven KPI.
- The two compliance checks (GMeet Link presence, One Pager Results presence) as their own
  report section — plain counts per owner, not folded into the KPI table.
- A "leads engaged" section with the 100/day target and attainment percentage per person.
- HTML + plaintext output, written to disk on every run regardless of send, with an optional
  --send/--to flag wired to whatever mail transport this codebase already uses (check for one
  before assuming Gmail OAuth).
- Support both a daily mode and a --week (Monday-to-today) mode, exactly mirroring the source
  system's day-list handling and its guard against non-today-ending windows.

Ask me before finalizing anything you couldn't verify against live data (the two flagged
judgment calls, the exact property names, the actual note vocabulary) — don't guess silently
on those.
```

---

## 10. What's still open

Everything under "Decision point" above (§2 pt. 2, §5, §7) and the note-rules verification in
§3/§9 needs either live API access to the Company Ops Data portal or a real notes sample from
that team — neither is available from this session. This document is complete as a **spec to
build from**, not as a verified, ready-to-run report.
