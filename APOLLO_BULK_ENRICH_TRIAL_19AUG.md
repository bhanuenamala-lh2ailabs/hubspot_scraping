# Controlled trial: does Apollo Bulk People Enrichment give LinkedIn URLs for free?

**Date:** 19 Aug 2026. Key tested: `apollo_api_key` in `.env` (`dwqD…`, same key used in all
prior Apollo testing this week). **Result: the trial could not run past Step 2 — the key has no
scope for either endpoint the test depends on.** Both blockers were logged with the raw API
response, not inferred.

---

## Step 1 — baseline credit balance: BLOCKED

Tried the documented endpoint (found via Apollo's docs, "View Credit Usage Stats" links to the
`include_credit_usage` param on Get Current User Profile):

```
GET https://api.apollo.io/api/v1/users/api_profile?include_credit_usage=true
```

Raw response — **HTTP 403**:

```json
{
  "error": "This API key is not authorized to access api/v1/users/api_profile. Request an API key from your administrator that includes this endpoint in its configured scope.",
  "error_code": "API_INACCESSIBLE"
}
```

No browser session is available in this environment to log into Apollo's Billing UI directly, so
there was no fallback path to get a baseline number. **No credit balance was ever recorded** —
this is a hard blocker on measuring any credit delta, not a soft one.

## Step 2 — search 5 people (ran fine, 0 credits, as expected)

Note: you said 5 is enough for this trial, so I stopped there rather than grinding through more
companies to force exactly 10 — Apollo's India-services index is sparse (most companies in our
backlog return 0 people; ~15 companies had to be queried to surface 5 hits, all logged).

Endpoint: `POST /api/v1/mixed_people/api_search`, same filters we've used all week
(`currentCompany`/`organization_locations:["India"]`, titles CEO/Founder/Co-Founder/CTO/MD,
seniorities owner/founder/c_suite).

| Company | HTTP | People found |
|---|---|---|
| Zealous System | 200 | 1 |
| 2Base Technologies | 200 | 0 |
| Kireeti Soft Technologies | 200 | 1 |
| TechAhead | 200 | 0 |
| Procedure Technologies | 200 | 0 |
| Digital Web Weaver | 200 | 0 |
| Rays Techserv Private Limited | 200 | 0 |
| Dev Technosys LLC | 200 | 0 |
| Qodequay Technologies | 200 | 2 |
| Exavibes Services Private Limited | 200 | 0 |
| Xicom | 200 | 0 |
| Verve Systems Pvt. Ltd. | 200 | 0 |
| Orion InfoSolutions | 200 | 0 |
| Start Designs | 200 | 0 |
| Finoit Technologies, Inc | 200 | 0 |
| UniConverge Technologies | 200 | 0 |
| Gary Global Solutions | 200 | 2 |

The 5 IDs collected (raw records, unmodified):

```json
[
  {"id": "690595f2a76fb60001dba8e7", "first_name": "Nabyendu", "last_name_obfuscated": "Ma***l",
   "title": "CEO of a Private Company", "organization": {"name": "Zealous System"}},
  {"id": "60a4f9d979c22a0001472c07", "first_name": "Sridhar", "last_name_obfuscated": "Na***a",
   "title": "CEO", "organization": {"name": "Kireeti Soft Technologies Ltd"}},
  {"id": "68793091556e730001e26068", "first_name": "Shridhar", "last_name_obfuscated": "Ma***i",
   "title": "Chief Technology Officer", "organization": {"name": "Qodequay Technologies"}},
  {"id": "6250045a2529c90001f59926", "first_name": "Sunil", "last_name_obfuscated": "Ma***e",
   "title": "Founder Director", "organization": {"name": "Qodequay Technologies"}},
  {"id": "5b31be50a6da9840a9e4ee2c", "first_name": "Prateek", "last_name_obfuscated": "Gu***a",
   "title": "CEO & Founder", "organization": {"name": "Gary Global Solutions"}}
]
```

Confirmed exactly as expected: **5/5 have `id`, 5/5 have `last_name_obfuscated`, 0/5 have
`linkedin_url`.** (Full raw JSON for all 17 company calls, including the zero-result ones, is in
`/tmp/apollo_trial_full_dump.json` if you want to inspect it.)

## Step 3 — Bulk People Enrichment on those 5 IDs: BLOCKED

```
POST https://api.apollo.io/api/v1/people/bulk_match?reveal_personal_emails=false&reveal_phone_number=false
Body: {"details": [{"id": "690595f2a76fb60001dba8e7"}, {"id": "60a4f9d979c22a0001472c07"},
                    {"id": "68793091556e730001e26068"}, {"id": "6250045a2529c90001f59926"},
                    {"id": "5b31be50a6da9840a9e4ee2c"}]}
```

Raw response — **HTTP 403**:

```json
{
  "error": "This API key is not authorized to access api/v1/people/bulk_match. Request an API key from your administrator that includes this endpoint in its configured scope.",
  "error_code": "API_INACCESSIBLE"
}
```

Same "not in configured scope" message as `mixed_people/search`, `people/search`, and
`people/match` earlier this week (see `APOLLO_BUY_DECISION_BRIEF.md`). **`bulk_match` is not on
this key's scope at all, so no `linkedin_url`, no credit metadata, no `unique_enriched_records` —
nothing came back to inspect.**

## Step 4 — post-check credit balance: also BLOCKED

Repeated the Step 1 call. Same 403 `API_INACCESSIBLE`, unsurprisingly — nothing changed because
Step 3 never touched a working endpoint.

## Step 5 — the delta

**Cannot be computed.** Baseline: unknown. Post: unknown. Delta: unknown. No per-person cost can
be projected, because the one endpoint the whole question hinges on — `people/bulk_match` — 403s
outright on this key, before any credit could possibly be spent.

## What this actually tells us

This is a **scope problem, not a "did it charge us" problem** — we never got far enough to see a
charge. It confirms the standing finding from `APOLLO_BUY_DECISION_BRIEF.md`: on the current
free-tier key, every people-enrichment/match endpoint except `mixed_people/api_search` itself is
locked out with `API_INACCESSIBLE`. `api_search` is free and works, but it's also the one endpoint
that structurally never returns a `linkedin_url` — so the "search is free, does enrichment cost
anything" question can't be answered empirically until we either:

1. Get a key with `people/bulk_match` (or `people/match`) in its configured scope — this needs
   Apollo support/sales to add the scope, possibly gated to a paid tier per Q1 in the buy-decision
   brief, or
2. Get a key with `users/api_profile` in scope so credit balance can even be read via API, or
3. Check the Billing → Credit usage page manually in a real browser session logged into the
   Apollo account (not available to me in this environment) as a one-off baseline/post check
   around a manual `bulk_match` test.

**Bottom line: this specific controlled trial is blocked at the access layer, not something a
different test design fixes.** The next move has to be either a scope upgrade from Apollo or a
manual UI check — not another API variant.

---

## RETRY — 19 Aug 2026, later same day, with a new master-scoped key

You swapped in a new key (`JnejZ…`) with master-key scope and asked to retry Steps 1, 3, 4 using
the **same 5 IDs already retrieved in Step 2** (no need to re-search).

### Step 1 (retry) — baseline: SUCCESS

```
GET /api/v1/users/api_profile?include_credit_usage=true  -> HTTP 200
```

```json
{
  "num_credits_remaining": 101,
  "effective_num_lead_credits": 120, "num_lead_credits_used": 0,
  "effective_num_direct_dial_credits": 160, "num_direct_dial_credits_used": 0,
  "effective_num_export_credits": 0, "num_export_credits_used": 0,
  "effective_num_ai_credits": 5000, "num_ai_credits_used": 0,
  "total_unified_credits_used": 0
}
```

**Baseline: 101 credits remaining.**

### Step 3 (retry) — Bulk People Enrichment on the 5 saved IDs: SUCCESS

```
POST /api/v1/people/bulk_match?reveal_personal_emails=false&reveal_phone_number=false  -> HTTP 200
```

`total_requested_enrichments: 5`, `unique_enriched_records: 5`, `missing_records: 0`.

**Every one of the 5 came back with a real, populated `linkedin_url`:**

| Person | linkedin_url | email (despite reveal flags = false) |
|---|---|---|
| Nabyendu Mandal | linkedin.com/in/nabyendu-mandal-50aba4228 | unavailable |
| Sridhar Narra | linkedin.com/in/sridhar-narra-86aa644b | sridhar@us2guntur.com (verified) |
| Shridhar Malagi | linkedin.com/in/shridhar-malagi-79abb7214 | unavailable |
| Sunil Mane | linkedin.com/in/sunil-mane-687a60223 | unavailable |
| Prateek Gupta | linkedin.com/in/growwithprateekgupta | prateek@garyglobalsolutions.com (verified) |

**The response body itself carries a credit field: `"credits_consumed": 5`.** Note also: 2 of 5
returned a *verified* work email even with both reveal flags set to `false` — the flags appear to
suppress "personal" email guesses only, not previously-verified professional emails already on
file. Not something we asked for, but observed.

### Step 4 (retry) — post-check: SUCCESS

```json
{ "num_credits_remaining": 96, ... everything else unchanged ... }
```

### Step 5 — the delta (now answerable)

| | Value |
|---|---|
| Baseline credits | **101** |
| Post-enrichment credits | **96** |
| **Delta** | **-5** |
| Per-person cost | **1 credit/person** (matches `credits_consumed: 5` from the API response directly) |

**This settles it: Bulk People Enrichment is NOT free, even for LinkedIn-URL-only retrieval with
both reveal flags off.** It costs exactly 1 credit per matched person, same as a full reveal would.

### What this means for the 3,100-company backlog

At 1 credit/person, enriching **9,300 people** (3,100 companies × 3 execs) costs **9,300 credits**.
The account currently shows `effective_num_lead_credits: 120` — read either as a ~120/period
allotment or the live `num_credits_remaining: 101/96` pool, **both are two orders of magnitude
short of 9,300.** Buying this at scale requires a materially larger Apollo plan; it does not fit
inside anything close to the current allowance.

**Revised recommendation per the buy-decision brief's own table:** this lands squarely on
*"`people/match`-equivalent forces 1 credit/person → BUY IF the plan bundles ≥5,000 credits/month
at sensible cost."* Whether to buy now depends entirely on price-per-credit at a tier that clears
~9,300/month (plus ongoing volume) — worth getting that number from Apollo sales before deciding,
rather than assuming the free/basic tier can absorb this.
