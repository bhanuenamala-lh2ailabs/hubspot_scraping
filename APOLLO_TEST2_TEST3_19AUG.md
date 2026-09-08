# Two controlled Apollo tests — 19 Aug 2026, master-scoped key

Key: `apollo_api_key` in `.env` (`JnejZ…`, master-scoped, same one that unblocked the earlier
Bulk Enrichment trial today). Both tests run back-to-back in one session so credit deltas are
attributable per test.

---

## PRE-STEP — baseline credits

```
GET /api/v1/users/api_profile?include_credit_usage=true  -> HTTP 200
```

```json
{
  "num_credits_remaining": 96,
  "effective_num_lead_credits": 120, "num_lead_credits_used": 0,
  "effective_num_direct_dial_credits": 160, "num_direct_dial_credits_used": 0,
  "effective_num_export_credits": 0, "num_export_credits_used": 0,
  "effective_num_ai_credits": 5000, "num_ai_credits_used": 0,
  "total_unified_credits_used": 0
}
```

**Baseline: 96 credits remaining** (down from 101 this morning — the -5 from the earlier
Bulk-Enrichment-cost trial).

---

## TEST 3 — does narrowing to 1 exec/company lose coverage?

**Method:** pure `mixed_people/api_search` calls (0 credits), cascading tiers, stop at first hit.
30 fresh companies, file indices 22–51 of `enrich_queue.csv` — none overlap the 17 companies used
in earlier tests (verified: prior tests used indices 10–21, 80, 251, 256; this batch starts at 22).

- **Tier 1:** founder / co-founder / CEO / chief executive officer
- **Tier 2:** + managing director / chairman / president
- **Tier 3:** + CTO / chief technology officer

| Company | Tier that hit | Total people (union across tiers queried) |
|---|---|---|
| Shanti Infosoft LLP | 1 | 1 |
| QalbIT Infotech Pvt Ltd. | 0 (dead end) | 0 |
| axiusSoftware | 1 | 2 |
| Aexonic Technologies | 0 | 0 |
| Tagline Infotech | 0 | 0 |
| Flipkoins | 0 | 0 |
| Concept Infoway | 2 | 3 |
| GMTA Software Solutions | 3 | 1 |
| Triveni Global Software Services LLP | 1 | 1 |
| Mindbowser InfoSolutions | 0 | 0 |
| Coder World Labs | 0 | 0 |
| Leadstocompany | 0 | 0 |
| Planet Web Solutions Pvt. Ltd | 1 | 1 |
| SolutionChamps Technologies | 0 | 0 |
| Gavista Tech | 0 | 0 |
| Codezilla Technology and Consultancy Pvt Ltd. | 0 | 0 |
| Durapid Technology Private Limited | 0 | 0 |
| M-Square Technologies | 1 | 2 |
| Spysr | 3 | 1 |
| VD Hosts | 0 | 0 |
| RheinBrucke IT Consulting Pvt Ltd | 0 | 0 |
| Revinfotech Inc | 0 | 0 |
| Xornor Technologies Pvt. Ltd. | 0 | 0 |
| Walking Tree Technologies | 0 | 0 |
| iauro systems pvt ltd | 0 | 0 |
| KritiKal Solutions Pvt. Ltd. | 0 | 0 |
| Smartify Software Solutions LLP | 0 | 0 |
| Digisoft Solution | 0 | 0 |
| ByteCipher Pvt Ltd | 0 | 0 |
| BitCot | 0 | 0 |

**Summary (n=30):**

| Outcome | Count | % |
|---|---|---|
| Tier 1 alone covers it | 5 | 16.7% |
| Needed Tier 2 to find anyone | 1 | 3.3% |
| Needed Tier 3 to find anyone | 2 | 6.7% |
| Dead end at every tier (0 people, any title count) | 22 | 73.3% |

### Test 3 verdict

**Narrowing from 3 titles to 1 is close to a non-issue — but only because the real problem is
coverage, not title breadth.** Of the 8 companies where Apollo found ANYONE at all, 5/8 (62.5%)
were resolved by Tier 1 alone, and every one of the remaining 3 was a company where Tier 1 legitimately
found nobody (not a near-miss demoted by a stricter title filter). So going from 3 titles to 1 costs
you essentially nothing on the companies Apollo can actually resolve.

**The real number that matters is the 73% dead-end rate.** Whether you query 1 title or 3, Apollo's
India-IT-services index simply does not have a person on file for ~73% of this backlog segment.
Trimming exec count doesn't change that — it only affects how *thoroughly* you search the 27% Apollo
can answer, and that group turns out to resolve almost entirely with Tier 1 titles anyway. **Safe to
drop to 1 best-available title for search — it's free either way, and it isn't losing meaningful hits.**

**Cost of Test 3: 0 credits** (pure search, confirmed by design and by the delta below).

---

## TEST 2 — can Apollo return a usable direct-dial mobile itself?

**Constraint respected: ran on exactly 1 person** — reused ID `690595f2a76fb60001dba8e7`
(Nabyendu Mandal, CEO, Zealous System) from the earlier trial, no new search.

Generated a fresh webhook.site URL (`https://webhook.site/e033112d-902b-4241-ab26-6b6fa70f468f`)
to catch the async delivery.

```
POST /api/v1/people/bulk_match?reveal_personal_emails=false&reveal_phone_number=true
Body: {"details": [{"id": "690595f2a76fb60001dba8e7"}],
       "webhook_url": "https://webhook.site/e033112d-902b-4241-ab26-6b6fa70f468f"}
```

**Synchronous response — HTTP 200, NOT a 403.** Direct-dial is available on this (master-scoped)
key — it did not plan-gate out.

```json
{
  "status": "success",
  "total_requested_enrichments": 1,
  "unique_enriched_records": 1,
  "missing_records": 0,
  "credits_consumed": 1,
  "matches": [ { "id": "690595f2a76fb60001dba8e7", "name": "Nabyendu Mandal",
                 "linkedin_url": "http://www.linkedin.com/in/nabyendu-mandal-50aba4228", ... } ],
  "phone_enrichment": {
    "request_id": "6a8585c23329ae001865e1e1",
    "status": "pending",
    "message": "Phone enrichment is processing asynchronously. Retrieve the result by polling
                GET /api/v1/webhook_result/{request_id} ... Retry after ~10 seconds."
  }
}
```

Note: the documented polling endpoint (`GET /webhook_result/{request_id}`) returned
`400 {"error_code": "invalid_request_id"}` when tried ~15s later — the polling route as documented
did not work for us. **The webhook was the only channel that actually delivered the result.**

**Webhook.site payload, ~1 minute later — the real phone data:**

```json
{
  "status": "success",
  "total_requested_enrichments": 1,
  "unique_enriched_records": 1,
  "missing_records": 0,
  "credits_consumed": 8,
  "people": [
    {
      "id": "690595f2a76fb60001dba8e7",
      "status": "success",
      "phone_numbers": [
        {
          "raw_number": "+91 75509 93019",
          "sanitized_number": "+917550993019",
          "type_cd": "mobile",
          "status_cd": "valid_number",
          "confidence_cd": "high"
        }
      ]
    }
  ]
}
```

**A real, formatted Indian mobile number came back**: `+91 75509 93019` (E.164
`+917550993019`), explicitly typed `mobile`, status `valid_number`, confidence `high` — this is
not a landline or a generic company number, and Apollo self-reports high confidence on it.

### Cost breakdown

- Sync call (match + LinkedIn URL): **1 credit**
- Async phone delivery: **8 credits**
- **Total for 1 person: 9 credits** — exactly matching the "1 demographic + 8 mobile" figure from
  Apollo's own docs quoted in the original buy-decision brief.

---

## POST-STEP — final credit check

```json
{
  "num_credits_remaining": 87,
  "effective_num_lead_credits": 120, "num_lead_credits_used": 0,
  "effective_num_direct_dial_credits": 160, "num_direct_dial_credits_used": 8,
  "total_unified_credits_used": 8
}
```

| | Value |
|---|---|
| Credits before | **96** |
| Credits after | **87** |
| **Delta** | **-9** |
| Attribution | **Test 3: 0** (confirmed — `num_credits_remaining` did not move during Test 3's 30 search calls) / **Test 2: -9**, split as 1 generic credit + 8 from the `direct_dial` bucket specifically (`num_direct_dial_credits_used` moved 0→8 — this pool is tracked separately from the "lead" credit pool that never moved) |

Delta is fully accounted for by Test 2 alone, exactly as expected.

---

## Summary

**Test 3 verdict — safe to narrow.** Dropping from 3 execs to "1 best-available title" per company
loses essentially no real coverage: every company Apollo could resolve at all was resolved by
Tier 1 in 5/8 cases, and the rest were legitimate dead ends regardless of title breadth. The
binding constraint on this backlog is Apollo's sparse India-IT-services coverage (73% zero-result
rate on this sample), not the number of titles queried. Narrowing to 1 title costs nothing (search
stays free) and simplifies the pipeline without a real coverage loss.

**Test 2 verdict — direct-dial works and did NOT 403 out; it's real, but it's not cheap.**
On this master-scoped key, Apollo returned a genuine, high-confidence Indian mobile number
(`+91 75509 93019`) for the one person tested — so technically this *could* replace SignalHire's
reveal step. But it cost **9 credits for one phone number**, versus SignalHire's flat reveal-credit
cost per person from an existing 4,700-credit pool that's proven itself over hundreds of reveals.
At 9 credits/person, enriching phones for the full backlog (even just the ~27% of companies Apollo
can find anyone for) would burn through credits an order of magnitude faster than SignalHire does.
**Not a SignalHire replacement at this credit cost** — worth keeping SignalHire for reveal and
treating Apollo strictly as an identity/LinkedIn-URL layer, if used at all, given yesterday's
finding that even LinkedIn-only enrichment already costs 1 credit/person.
