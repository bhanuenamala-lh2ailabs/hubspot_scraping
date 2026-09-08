CONTEXT
-------
We run a lead-enrichment pipeline against the SignalHire API. Two calls per company:

  1. POST https://www.signalhire.com/api/v1/candidate/searchByQuery
     -> finds the founder/CEO at a company. Returns uid/name/title. NO contact data.
     Auth: `apikey` header.
     Current payload:
       { "currentCompany": "<company name>",
         "location": "India",
         "size": 3,
         "currentTitle": "founder OR co-founder OR cofounder OR owner OR CEO OR chief executive OR managing director OR CTO OR chief technology OR chairman OR president" }

  2. POST /api/v1/candidate/search  -> the reveal (uid -> phone/email). Spends reveal
     credits. NOT the problem. Do not change this leg.

THE PROBLEM
-----------
searchByQuery returns HTTP 402 with body:
  {"message":"You have reached your daily search attempts quota. ..."}

Established empirically:
  - Metered PER CALL, not per profile. Zero-result calls still burn quota.
    (86 calls returned only 160 profiles; 24/86 returned zero profiles.)
  - Therefore `size` is FREE against this meter.
  - Reset is ~24h03m after exhaustion, NOT a calendar-day boundary.
  - Volume before 402 is inconsistent: 297 calls one cycle, 171 the next.
  - Working hypothesis: a ROLLING 24-hour window. Calls age out individually
    24h after they were made, so a cycle that starts against a partly-full
    window recovers only a partial allowance.
  - The API exposes NO quota-remaining endpoint, no counter, no limit, no
    reset timestamp, no Retry-After header. We are blind.
  - /credits reports reveal credits only. Irrelevant to this.
  - We pace at ~0.35s and have NEVER seen 429. This is a quota wall, not rate limiting.

Existing raw log: godown/founder_id/searchq_raw_log.json

BUILD THIS
----------
A resumable search runner with client-side quota accounting.

1. CONFIG
   - SEARCH_SIZE: default 10 (raise from 3 — free against the call meter).
     Make it a config value, not a literal.
   - ASSUMED_WINDOW_HOURS: 24.0
   - ASSUMED_CALL_BUDGET: 171 (conservative; the lower observed figure)
   - SAFETY_MARGIN: 0.9 (stop at 90% of assumed budget)
   - MIN_INTERVAL_S: 0.35

2. LEDGER (SQLite at godown/founder_id/search_ledger.db)
   Table `calls`: id, ts_utc, company, http_status, profiles_returned,
                  size_used, total_reported, run_id
   Table `events`: ts_utc, kind ('402'|'recovery'|'run_start'|'run_end'), note

   Backfill from searchq_raw_log.json on first run if the ledger is empty.

3. PRE-FLIGHT GATE (before every call)
   - trailing_calls = COUNT(calls WHERE ts_utc > now - ASSUMED_WINDOW_HOURS)
   - If trailing_calls >= ASSUMED_CALL_BUDGET * SAFETY_MARGIN: do not call.
     Compute next_slot = ts of the (trailing_calls - budget + 1)-th oldest call
     inside the window, plus ASSUMED_WINDOW_HOURS. Sleep until then. Log it.
   - This is the whole point: never discover the wall by hitting it.

4. ADAPTIVE PACING
   If the rolling hypothesis holds, even spacing beats bursting.
   Spread calls at interval = ASSUMED_WINDOW_HOURS*3600 / ASSUMED_CALL_BUDGET,
   floored at MIN_INTERVAL_S. Make pacing mode switchable:
   --pace even | burst | asap

5. 402 HANDLING
   On 402: log an 'events' row kind='402'. Do NOT retry-storm. Compute the
   earliest time a slot ages out from the ledger and sleep to it. On the first
   subsequent 200, log kind='recovery' with the measured gap. Every 402/recovery
   pair auto-refines ASSUMED_CALL_BUDGET — write the observed value back to a
   calibration file.

6. BURST EXPERIMENT MODE  (--experiment)
   Purpose: distinguish rolling window from fixed daily cap.
   - Start from a fully rested state.
   - Fire N=50 calls as fast as MIN_INTERVAL_S allows, timestamping each. Stop.
   - Wait 6h. Fire another 50. Stop.
   - Continue until 402.
   - On recovery, report whether it arrived ~24h after the EARLIEST calls
     (=> rolling) or at a fixed wall-clock time (=> calendar).
   Emit a plain-English verdict, not just numbers.

7. QUEUE
   Resumable work queue over our ~3,100-company backlog. A company is 'done'
   when it has a 200 response logged, regardless of whether profiles were
   returned. Never re-search a done company. Support --limit and --resume.

8. REPORT  (--report)
   Print: calls in trailing 24h, remaining budget estimate, profiles/call,
   zero-result rate, dial-ready yield if reveal outcomes are joinable,
   companies remaining, and projected days-to-clear at observed throughput.

CONSTRAINTS
-----------
- Do not touch the reveal leg or its credit accounting.
- Log every response verbatim; we may need to re-derive facts later.
- Assume the API tells us nothing. All quota state is ours to infer.
- Python. Standard library + requests. No heavy framework.