# Apollo people-search test — 19 Aug 2026

Follow-up test to the buy/no-buy investigation in `APOLLO_BUY_DECISION_BRIEF.md`. Purpose: confirm
whether the obfuscation problem observed on 18 Aug is still present, using the current key in
`.env` (`apollo_api_key`), and add one more coverage data point.

## Key used

```
apollo_api_key present: True, length 22, starts "dwqD…"
```
Same key as yesterday's second test (the one that replaced the first, revoked key). Confirmed
alive before testing:

```
GET https://api.apollo.io/api/v1/auth/health
-> HTTP 200  {"healthy": true, "is_logged_in": true}
```

## Script used

```python
import json, requests

env = { ... read from .env ... }
H = {"Content-Type": "application/json", "Cache-Control": "no-cache",
     "X-Api-Key": env["apollo_api_key"]}
URL = "https://api.apollo.io/api/v1/mixed_people/api_search"

for company in ("Zealous System", "2Base Technologies", "Kireeti Soft Technologies"):
    body = {
        "q_organization_name": company,
        "organization_locations": ["India"],
        "person_titles": ["CEO", "Founder", "Co-Founder", "CTO",
                           "Managing Director", "MD"],
        "person_seniorities": ["owner", "founder", "c_suite"],
        "per_page": 5
    }
    r = requests.post(URL, headers=H, json=body, timeout=45)
    print(company, r.status_code, r.json())
```

Endpoint: `POST /api/v1/mixed_people/api_search` — the only people-search endpoint this key has
scope for (`mixed_people/search`, `people/search` and `people/match` all still return 403
`API_INACCESSIBLE` on this key, per yesterday's testing).

Three companies tested: **Zealous System** (repeat, to confirm nothing changed since yesterday),
**2Base Technologies** (new, drawn from our own scraped queue), **Kireeti Soft Technologies**
(new, one of the top-ranked companies from yesterday's association scrape).

## What was requested — the exact payload

```json
{
  "q_organization_name": "<company name>",
  "organization_locations": ["India"],
  "person_titles": ["CEO", "Founder", "Co-Founder", "CTO", "Managing Director", "MD"],
  "person_seniorities": ["owner", "founder", "c_suite"],
  "per_page": 5
}
```

## What came back — raw responses

### 1. Zealous System — HTTP 200

```json
{ "total_entries": 1,
  "people": [
    { "id": "690595f2a76fb60001dba8e7",
      "first_name": "Nabyendu",
      "last_name_obfuscated": "Ma***l",
      "title": "CEO of a Private Company",
      "last_refreshed_at": "2026-07-03T13:48:36.614+00:00",
      "has_email": false,
      "has_city": true, "has_state": true, "has_country": true,
      "has_direct_phone": "Yes",
      "organization": {
        "name": "Zealous System",
        "has_industry": true, "has_phone": true, "has_city": true,
        "has_state": true, "has_country": true, "has_zip_code": true,
        "has_revenue": true, "has_employee_count": true
      }
    }
  ]
}
```

Identical in shape to the response captured on 18 Aug — same person, same obfuscation, same
missing fields. Confirms nothing has changed on Apollo's side or in our access since yesterday.

### 2. 2Base Technologies — HTTP 200

```json
{ "total_entries": 0, "people": [] }
```

Zero matches. Not an access or key problem — the call succeeded (200) and the other two calls in
the same run found people normally. This is a genuine coverage miss: Apollo's index does not have
a founder/CEO/CTO/MD record for this company under the given filters.

### 3. Kireeti Soft Technologies — HTTP 200

```json
{ "total_entries": 1,
  "people": [
    { "id": "60a4f9d979c22a0001472c07",
      "first_name": "Sridhar",
      "last_name_obfuscated": "Na***a",
      "title": "CEO",
      "last_refreshed_at": "2026-08-14T22:10:18.502+00:00",
      "has_email": true,
      "has_city": true, "has_state": true, "has_country": true,
      "has_direct_phone": "Yes",
      "organization": {
        "name": "Kireeti Soft Technologies Ltd",
        "has_industry": true, "has_phone": true, "has_city": true,
        "has_state": true, "has_country": true, "has_zip_code": true,
        "has_revenue": false, "has_employee_count": true
      }
    }
  ]
}
```

## Summary table

| Company | HTTP | People found | Full name? | LinkedIn URL? | Notes |
|---|---|---|---|---|---|
| Zealous System | 200 | 1 | ❌ obfuscated (`Ma***l`) | ❌ none | repeat of 18 Aug result, unchanged |
| 2Base Technologies | 200 | 0 | — | — | genuine index miss, not an access fault |
| Kireeti Soft Technologies | 200 | 1 | ❌ obfuscated (`Na***a`) | ❌ none | new data point |

## What this confirms

1. **The obfuscation problem is unchanged.** Every person record still returns `last_name_obfuscated`
   instead of `last_name`, and **no response has ever contained a `linkedin_url` field** across
   any of the five companies tested over two days. The buy/no-buy analysis in
   `APOLLO_BUY_DECISION_BRIEF.md` stands as written — this key/endpoint combination cannot supply
   an identity that SignalHire's reveal step can act on.
2. **The key and endpoint are functioning correctly.** `auth/health` is green and 200s returned
   correctly with real data on 2 of 3 companies, so the 2Base zero-result is data coverage, not a
   fault.
3. **One new evidence point for the pending research brief (Q5 — Indian coverage rate):** Apollo's
   people-search index does not have universal coverage even for companies where the search itself
   works — 1 of 3 tested here returned nothing at all.
