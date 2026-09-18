# Daily Full-Funnel Report — Methodology (for porting to another HubSpot account/funnel)

This documents exactly how `crm_mirror/enrich/daily_fullfunnel_mail.py` (plus the two modules
it imports from — `daily_activity_report.py` and `lh2-pipeline/dashboard/note_rules.py`) computes
its numbers, end to end, so the same approach can be rebuilt against a different HubSpot portal
with a different pipeline (e.g. the Company Ops Data funnel).

Nothing here is inferred — this is a straight read-through of the three source files.

---

## 1. The core idea: three independent measurement layers

HubSpot has **zero call objects** in this portal. There is no dial log. Every number in the
report is *inferred* from two things that do exist:

1. **Deal stage history** — when a deal's stage changed, to what, and who clicked the button.
2. **Notes** — free-text people type on a deal.

The report deliberately keeps these as **two separate counting passes** and only combines them
at the very end, for one specific number ("leads engaged"). This separation is the single most
important design decision in the whole system — get it wrong and you double-count.

- **Stage KPIs** — a KPI counted only when a deal's stage actually moved. Credited to whoever
  clicked (`sourceType == "CRM_UI"`, `updatedByUserId`).
- **Note-only activity** — work that left no stage change at all (a second no-answer call, a
  callback booked, a WhatsApp chase). Bucketed by classifying the note's text.
- **Leads engaged** — the union of "deals I moved a stage on" and "deals I wrote a note on",
  deduplicated by deal ID. This is the one number that answers "how many distinct leads did
  this person actually touch today," and it's why it's presented as the headline metric.

A rule enforced throughout: **if a note's content already IS a KPI** (e.g. a note that says
"gmeet fixed" on a deal that also moved to the GMeet Fixed stage), that note is **not** counted
a second time as note-only activity. It still counts toward "leads engaged" (the note proves a
human touched the deal), but it doesn't inflate the KPI/note-only tallies. See §5.

---

## 2. Data pulled, and the exact API calls

All three scripts hit the same HubSpot API with the same auth header
(`Authorization: Bearer <hubspot_key>`, from `.env`).

### 2.1 Pipeline stage labels
```
GET /crm/v3/pipelines/deals
```
Builds `{stage_id: stage_label}` across every pipeline in the portal — needed because deal
stage history returns raw stage IDs, and the KPI/note logic is written against human-readable
labels ("GMeet Fixed", not `3992480469`). **If your target portal has more than one pipeline
with the SAME stage names in the SAME order** (as this portal does — "Scraped" and "Campaign"),
this single label map works across both without extra code, because it's keyed by ID, not by
pipeline.

### 2.2 Owners
```
GET /crm/v3/owners?limit=200
```
Builds two maps:
- `OWN = {owner_id: "First Last"}` — for display names.
- `U2ID = {str(userId): owner_id}` — **this is the important one.** Deal stage history records
  *who* made the change as a `updatedByUserId` (a HubSpot **user** ID), which is a *different*
  ID space from the **owner** ID used everywhere else (`hubspot_owner_id` property). Every
  owner record returned by `/owners` carries both, so this map is how a stage-history entry
  gets attributed back to a person.

### 2.3 Candidate deals (broad net, then narrow)
```
POST /crm/v3/objects/deals/search
{
  "limit": 100,
  "properties": ["dealname", "hubspot_owner_id", "dealstage", "hs_v2_date_entered_current_stage"],
  "filterGroups": [{"filters": [
    {"propertyName": "hs_lastmodifieddate", "operator": "GTE", "value": "<window_start>T00:00:00Z"}
  ]}]
}
```
This is deliberately **too broad** — `hs_lastmodifieddate` changes on almost any edit, not just
a stage move (an enrichment backfill can touch 1,000+ deals without changing a single stage).
The code pulls everything modified since the window started, then narrows using
`hs_v2_date_entered_current_stage`: keep only deals where *that* timestamp falls inside the
window (converted to IST calendar dates — see §2.5).

**Why not just fetch full history for everything `hs_lastmodifieddate`-filtered?** Cost: one
`propertiesWithHistory` call per deal is ~expensive at scale (documented as "one history call
each is ~16 minutes" for ~1,000 deals in the code comments). Filtering candidates down first via
a single cheap batched search, then only paying the expensive per-deal history call for the
much smaller set that *actually* changed stage, is the whole optimization.

**The load-bearing caveat, verbatim from the code:** this portal has no per-stage
`hs_date_entered_<stage_id>` properties, only `hs_v2_date_entered_current_stage`, which holds
**only the most recent stage entry**. That is a sound filter *only if the report window ends
today* — if you ask for a past window, a deal that moved again after that window would have
overwritten the field, silently hiding the earlier move. Both scripts guard this explicitly:
`daily_activity_report.py` hard-exits if `max(DAYS) < today`; `daily_fullfunnel_mail.py` exits
if `_end > _today`. **When porting: check whether the target portal exposes real per-stage
`hs_date_entered_*` properties — if it does, use those instead and this whole caveat disappears.**

### 2.4 Full stage history, per candidate deal
```
GET /crm/v3/objects/deals/{id}?propertiesWithHistory=dealstage
```
Returns every historical value of `dealstage` for that one deal, each entry carrying:
`value` (stage ID), `timestamp`, `sourceType`, `updatedByUserId` (present when `sourceType` is
`CRM_UI`).

**Only `sourceType == "CRM_UI"` entries are counted.** Comment in the code: *"42% is integration
noise; never count it."* Any programmatic/API-driven stage change (a script pushing/bulk-editing
deals, an integration sync) is excluded — only clicks made by a human in the HubSpot UI count as
work. This is the mechanism that makes every bulk operation we've run today (retagging,
reassigning owners, bulk stage moves) invisible to this report — which is correct, since none of
that is a caller's actual work.

### 2.5 Timestamp → IST calendar date
```python
def ist_day(ts):
    if isinstance(ts, (int, float)) or str(ts).isdigit():
        return datetime.datetime.fromtimestamp(int(ts)/1000, IST).date().isoformat()
    return datetime.datetime.fromisoformat(str(ts).replace("Z", "+00:00")).astimezone(IST).date().isoformat()
```
`IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))`. Every timestamp HubSpot
returns (either epoch-millis or ISO8601 UTC, both show up depending on the property) gets
converted to an IST calendar date before being compared against the report's day list. **This
matters because "today" in IST and "today" in UTC disagree for roughly 5.5 hours a day** — get
this wrong and stage moves near midnight IST land on the wrong day.

### 2.6 Notes
```
POST /crm/v3/objects/notes/search
{
  "limit": 100,
  "properties": ["hs_note_body", "hs_timestamp", "hubspot_owner_id"],
  "filterGroups": [{"filters": [{"propertyName": "hs_timestamp", "operator": "GTE", "value": "<window_start>T00:00:00Z"}]}]
}
```
Pulled once for the whole window, then filtered client-side to `ist_day(hs_timestamp) in DAYS`
and `hubspot_owner_id` being one of the tracked people. Attribution here uses the note's own
`hubspot_owner_id` directly — no user-ID translation needed, unlike stage history.

### 2.7 Note → deal association (so a note counts toward "leads engaged")
```
POST /crm/v4/associations/notes/deals/batch/read
{"inputs": [{"id": note_id}, ...]}   # batched in groups of 100
```
Builds `{note_id: [deal_id, ...]}`. Every deal a note is attached to gets added to that owner's
"engaged" set.

---

## 3. Stage KPIs — the `METRICS` mapping

This is the single most important thing to redo carefully for a new pipeline, because it *is*
the pipeline's vocabulary translated into countable events.

```python
METRICS = {
    "att":  {"No Pickup", "Dead/ColdCall/WrongNumber", "Dead/ColdCall/Not Interested",
             "Dead/ColdCall/NoPickup", "Interested"},
    "conn": {"Dead/ColdCall/Not Interested", "Interested"},
    "gm":   {"GMeet Fixed"},
    "vc":   {"Dead/GMeet/NoShow", "Dead/GMeet/wrong fit", "Dead/GMeet/Privacy Concerns",
             "Script Shared"},
    "ss":   {"Script Shared"},
    "rr":   {"Script Results Received"},
    "ev":   {"Dead/ResultsReceived/WrongFit-Rejected", "Commercial Negotiation"},
    "cn":   {"Commercial Negotiation"},
    "neg":  {"Dead/Negotiation/Pricing", "Dead/Negotiation/Contractual", "Deal Contract Signed"},
    "dcs":  {"Deal Contract Signed"},
    "won":  {"Closed/Won"},
}

def metrics_for(lab):
    return [k for k, s in METRICS.items() if lab in s]
```

**Design rules, stated explicitly in the code comments — copy these, don't reinvent them:**

1. **Explicit set membership, never cascading.** A KPI is a literal set of stage *labels* that
   count toward it. It is tempting to write "reaching any later stage implies the earlier ones
   happened too" — the code comment says this was tried once and it inflated one person's daily
   attempt count from 18 to 54, because a deal that jumped straight to a late stage doesn't mean
   11 KPI events happened on the way. **Every label that should count toward a KPI must be
   listed for that KPI, explicitly.**

2. **A stage can (and often should) count toward more than one KPI.** `Interested` is in both
   `att` (attempted) and `conn` (connected), because reaching Interested necessarily means the
   call connected. This is intentional — it's not the cascading anti-pattern above, it's just
   that one real-world event (a connected, interested call) is legitimately two KPI facts.

3. **Exclusions carry real meaning — read them as decisions, not omissions.** Two examples
   called out directly in the code:
   - `Dead/ColdCall/WrongFit` is **absent** from `att` (attempted) — a lead screened out before
     ever being dialled is not a dial attempt.
   - `Dead/GMeet/Cancelled` is **absent** from `vc` (VC/meeting done) — a meeting called off in
     advance never consumed anyone's time, so it shouldn't count as "done."

   **When porting to a new funnel: for every dead-end stage, ask "did this consume the effort
   the KPI is trying to measure, or did it get short-circuited before that effort happened?"**
   That question is what separates, e.g., `Dead/ColdCall/WrongFit` (never dialled → excluded
   from attempts) from `Dead/ColdCall/NoPickup` (was dialled → included in attempts).

4. **One canonical copy, imported everywhere, never hand-copied.** The code comment is blunt
   about why: *"an earlier hand-copy of the KPI definitions drifted and inflated dial counts
   2.7x."* `daily_activity_report.py`'s `METRICS` is a verbatim copy-paste of
   `lh2-pipeline/dashboard/build_dashboard.py`'s own `METRICS`, with a comment instructing "If a
   quota or stage changes, change it there first and re-copy" — i.e. even the *copy* has a
   documented source of truth. **For a new pipeline, define `METRICS` once, in whichever script
   is the "real" one (the one that runs in CI / drives the live dashboard, if there is one), and
   import it everywhere else rather than retyping it.**

The corresponding, human-facing KPI label list used for the report table:
```python
KPI = [("att", "Calls attempted"), ("conn", "Calls connected"), ("gm", "GMeets fixed"),
       ("vc", "VCs done"), ("ss", "Scripts shared"), ("rr", "Script results recvd"),
       ("ev", "Evaluations done"), ("cn", "Commercial negotiation"), ("neg", "Negotiation calls"),
       ("dcs", "Contracts signed"), ("won", "Closed/Won")]
```
This is just display order/labels for the same keys `METRICS` defines — trivial to redo for a
new stage vocabulary once `METRICS` itself is right.

---

## 4. Note classification — `NOTE_RULES` (ordered regex, first match wins)

Lives in `lh2-pipeline/dashboard/note_rules.py` (moved there from `daily_activity_report.py` —
see §7 for why the location matters). Two functions:

```python
def plain(s):
    """HubSpot note bodies are HTML. Strip tags and collapse whitespace before matching."""
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s or "")).split())

def classify(t):
    s = t.lower()
    for name, rx in NOTE_RULES:
        if re.search(rx, s): return name
    return "Other"
```

`NOTE_RULES` is an **ordered list** of `(bucket_name, regex)` pairs. The order is not
cosmetic — it is the entire correctness mechanism, and the file's own docstring explains why:

> "Not interested" must be tested before "Interested", and bad-number before no-pickup, or the
> wrong bucket wins... Getting that order wrong silently turns every rejection into an approval
> — which is exactly how a regex misread "Not fully relevant" as an approval earlier this week.

Concretely, the order in this file is:
1. `System note` — machine-written notes (deadpool wave lead, relevance check banners, test
   deals, lead-gen form imports) are caught **first** so they can never be misattributed as
   somebody's actual work.
2. `Script received` — tested before `Script shared`, because it restates a KPI the caller maps
   to `None` (see §5) and must not fall through to a different bucket.
3. `Bad number` — tested before `No pickup`, because a lot of "wrong number" phrasing also
   contains words that would otherwise match no-pickup patterns.
4. `Vetted - out` (`^irrelevant|not relevant...`) **before** `Vetted - in` (`^relevant...`) — a
   naive "does it contain 'relevant'" match would flag "not relevant" as relevant.
5. `Not interested` before the bare `Interested` match at the very end of the list, for the same
   reason.
6. Everything else — `Disqualified`, `No pickup`, `Callback booked`, `Meeting fixed`,
   `Script shared`, `Chase sent` — ordered so none of their regexes accidentally shadow a
   higher-priority, more specific rule above them.
7. Anything matching nothing falls through to `"Other"`.

**The rules were derived empirically, not designed up front.** Docstring: *"Note buckets were
derived by reading the actual 106 notes written on 6-7 Aug, not invented,"* and later, *"Rules
were extended after the first run surfaced 12 unmatched notes — every gap below was a real note
somebody wrote, not a hypothetical."* **This is the actual porting procedure for a new funnel:
run the classifier against a real sample of that team's notes, look at what falls into `Other`,
and add a rule for each real pattern you find — don't try to anticipate every phrasing up
front.** The file even ships a small regression-test block (`if __name__ == "__main__":`) of
real note-text → expected-bucket pairs, specifically so a future rule change can't silently
break an earlier one; port that pattern too.

`BUCKETS = [b for b, _ in NOTE_RULES] + ["Other"]` — just the ordered bucket-name list, used to
build table columns.

---

## 5. Avoiding double-counting — `BUCKET_MAP`

This is the piece that stitches §3 and §4 together correctly. `daily_fullfunnel_mail.py`:

```python
BUCKET_MAP = {"Vetted - in": "Lead vetted", "Vetted - out": "Lead vetted",
              "Meeting fixed": None, "Script shared": None, "Interested": None,
              "Script received": None}
```

Two things happen here:
- **Collapsing:** `classify()`'s `"Vetted - in"` and `"Vetted - out"` both display as one
  bucket, `"Lead vetted"`, in the final report (a caller doesn't need two rows for "vetted in"
  vs "vetted out," just that vetting happened).
- **Suppressing double-counts (the important part):** `Meeting fixed`, `Script shared`,
  `Interested`, and `Script received` all map to **`None`**. The code comment explains exactly
  why: *"already a KPI (GMeet fixed / Scripts shared / results received / Interested->
  connected), so it is NOT re-counted as note-only work. The deal still counts toward 'leads
  engaged' — the note proves the person touched it."*

  Concretely: if a caller writes "GMeet fixed for tomorrow" on a deal, and that deal's stage
  also moved to `GMeet Fixed` today, the stage move already incremented the `gm` KPI (§3). If
  the note-bucket pass *also* counted that note under a "Meeting fixed" note-only bucket, the
  same single action would show up twice in the report — once as a KPI, once as note-only
  activity. `None` here means "this note's content is real, but don't add it to the note-only
  tally" — while the note still gets added to that person's engaged-deals set two paragraphs
  down, so the "leads engaged" number doesn't lose it.

  **When porting:** any bucket whose regex is *describing the same event a stage-KPI already
  captures* needs to map to `None` here. The test is: "if I already counted this via a stage
  move, would counting the note too be counting the same real-world action twice?" If yes, map
  it to `None`.

The buckets that survive into the actual "note-only activity" report table:
```python
NOTE_ONLY = {
    "No pickup":       "Dialled, nobody answered (re-dials included)",
    "Callback booked": "Reached them, call arranged for later",
    "Bad number":      "Number wrong / dead — needs re-enrichment",
    "Lead vetted":     "Desk qualification, relevant or not, before any dial",
    "Not interested":  "Said no on the call",
    "Disqualified":    "Ruled out on the facts (still operating, sold, no codebase)",
    "Chase sent":      "Followed up by WhatsApp / mail / text",
    "Other":           "Written down but not yet classified",
}
```
Each has a plain-English "what it means" string that gets rendered next to the number in the
email — worth keeping, it's what makes the report legible to someone who didn't write the code.

---

## 6. "Leads engaged" — the headline number

```python
eng = collections.defaultdict(set)          # owner_id -> {deal_id, ...}
stage_deals = collections.defaultdict(set)  # owner_id -> {deal_id, ...}  (stage-move subset only)
```

- Every stage-move event that counts toward a KPI (§3) also adds that deal ID to both `eng[oid]`
  and `stage_deals[oid]`.
- Every note that (a) belongs to a tracked owner and (b) is associated with a deal adds that
  deal ID to `eng[oid]` **regardless of what bucket it classified into** — even notes whose
  bucket mapped to `None` in §5 still land here, because touching the deal is real regardless of
  whether it double-counts as a KPI.

Because both are Python `set`s keyed by deal ID, working the same deal twice (once via a stage
move, once via a note) contributes exactly one entry to `eng[oid]` — this is the deduplication,
and it's automatic from using a set rather than a counter.

Final numbers per person, per the report table:
- **Leads engaged** = `len(eng[oid])`
- **via stage move** = `len(stage_deals[oid])`
- **note only** = `len(eng[oid]) - len(stage_deals[oid])` (deals touched *only* via a note, never
  a stage move that day)
- **KPI events** = `sum(kpi[oid].values())` — note this can be *larger* than "via stage move,"
  because one deal can trigger multiple KPI keys at once (§3, rule 2).

---

## 7. NET NEW engaged, and the reject set

```python
human = sorted([e for e in hist if e.get("sourceType") == "CRM_UI"], key=lambda e: e.get("timestamp") or "")
first_h = human[0] if human else None
...
if first_h is not None and e is first_h:
    netnew[oid].add(did)
```

For every candidate deal, the code looks at its **entire** stage history (not just the window),
finds the earliest ever human (`CRM_UI`) touch, and — if that earliest touch happens to fall
inside today's window — marks the deal as "NET NEW": a deal that had literally never been worked
by a human before today. This distinguishes "I opened a brand-new conversation today" from "I
did more work today on a deal someone already started days ago."

**Reject set** — deals excluded from NET NEW because they're a data-quality defect, not a real
new lead:
```python
if str(lab).endswith("WrongNumber"): reject.add(did)
...
if raw == "Bad number" or WRONG_SPOC.search(t): reject.add(did)
```
Two trigger conditions: the deal's stage label ends in `WrongNumber`, or a note on it classifies
as `Bad number` or matches `WRONG_SPOC` (a separate regex catching phrases like "wrong SPOC,"
"not the right person," "gave me another number," etc. — see the source for the full pattern).
The code comment is explicit about the reasoning: *"a wrong number or a wrong SPOC is not a lead
we engaged, it is a list defect."* This same `WRONG_SPOC` regex is shared with
`monthly_wow_report.py` specifically so the daily and weekly NET NEW figures can never disagree
— **if you port this, keep one definition and import it everywhere the concept is used, exactly
like `METRICS`.**

`netnew[oid] - reject` is what actually gets displayed.

---

## 8. Weekly mode

Same script, `--week` flag: `DAYS` becomes every day from Monday of the current week through
today (`_start = _end - timedelta(days=_end.weekday())`), and everything above runs unchanged
against that wider day list. The one guard that matters: the whole `hs_v2_date_entered_current_stage`
filtering approach (§2.3) is **only valid when the window ends today** — both scripts check this
and hard-exit otherwise. A week-to-date report works because it still ends today; a report for
*last* week would silently under-count and is correctly refused.

---

## 9. Output — HTML + plaintext + email

- `build()` renders three HTML tables (KPIs / note-only / leads-engaged) with inline CSS (no
  external stylesheet — this is an email body, so styles must be inline to survive most mail
  clients).
- `main()` also builds a plaintext version of the same numbers, printed to stdout and used as
  the email's plaintext fallback.
- Sending goes through `crm_mirror/enrich/gmail_sender.py` (`gmail_sender.send(to, subject, text, html=html)`),
  which resolves whichever mail transport is configured (OAuth, service-account, SMTP, or a
  local outbox file if nothing is configured — see that file's own docstring). Not specific to
  this report; reused as-is.
- Every run also writes the HTML to disk (`daily_fullfunnel.html` or `weekly_fullfunnel.html`
  next to the script) regardless of whether `--send` was passed, so a dry run still produces a
  file you can open and eyeball before deciding to send it.

---

## 10. Checklist for porting this to a different HubSpot portal / funnel

1. **New `.env` entry** for the target portal's private-app token (this portal uses `hubspot_key`
   in `.env`; the Company Ops portal already has its own key, `hubspot_kartik`, per this repo's
   README — point the `H` auth header at that key instead).
2. **Re-derive `METRICS`** against the new pipeline's actual stage labels (§3) — for every dead
   stage, explicitly decide which KPI(s) it should or shouldn't count toward, using the "did the
   effort actually happen before this dead-end" test.
3. **Re-check whether the portal has real `hs_date_entered_<stage_id>` properties.** If yes, use
   those directly instead of the `hs_v2_date_entered_current_stage` "only holds the latest move"
   workaround — it removes the window-must-end-today constraint entirely.
4. **Update `PEOPLE`** to the new portal's owner IDs (`GET /crm/v3/owners` on that portal) and the
   people you actually want reported on.
5. **Sample real notes from that team and rebuild `NOTE_RULES` from what you actually see** —
   don't port the existing regexes as-is; the wording people use is funnel-specific ("script
   shared," "GMeet fixed" are Codebase-Supply-Funnel vocabulary; a different funnel's callers
   will write different words for the equivalent actions). Keep the *ordering discipline*
   (negations/disqualifiers before the positive words they contain) — that principle transfers
   even though the specific words won't.
6. **Re-derive `BUCKET_MAP`** — for every note bucket, ask "does this restate something a stage
   KPI in step 2 already counts?" and map those to `None`.
7. **Re-check `WRONG_SPOC` / reject-set logic** — decide what counts as a list defect vs a real
   engaged lead for the new funnel; it may not be "wrong number/wrong SPOC" verbatim.
8. **Everything else — the API call shapes, the IST day-bucketing, the leads-engaged
   union/dedup logic, the NET NEW earliest-touch logic, the HTML/plaintext rendering, the mail
   send — is pipeline-agnostic and can be reused unchanged.**
