# Research brief: does buying Apollo solve our problem? (buy/no-buy decision)

**Prepared 18 Aug 2026 from live API testing on two separate free-tier keys.**
We need one narrow question answered well. Please do not broaden the scope.

---

## 1. What we are trying to do

Given **an Indian IT-services company name** (small/mid firm, 10–250 staff), we need to identify
its **founder / CEO / MD** well enough to then look up that person's **mobile number** with a
different vendor (SignalHire), where we already hold 4,737 prepaid reveal credits.

So we need Apollo for **people discovery only**:

- ✅ we need: the person's **full name** and/or their **LinkedIn profile URL**
- ❌ we do NOT need: their email, their phone number, or any contact data from Apollo

SignalHire's reveal step takes a **LinkedIn URL or a SignalHire uid** as input. That is the
hand-off. Anything Apollo returns that does not include a full name or a LinkedIn URL is unusable
to us, no matter how accurate it is.

**Why we are looking at Apollo at all:** SignalHire's *search* endpoint is capped at roughly
171–297 calls per rolling 24 hours and is opaque (no quota endpoint, no counters). Apollo's people
search is documented at **0 credits and 600 calls/hour**. If Apollo can do discovery, our
throughput problem disappears. Its *reveal* leg is fine and we are keeping it.

## 2. What we observed in live testing

Endpoint: `POST https://api.apollo.io/api/v1/mixed_people/api_search`
Payload: `q_organization_name`, `organization_locations:["India"]`, `person_titles:[CEO, Founder,
Co-Founder, CTO, Managing Director, ...]`, `person_seniorities:[owner, founder, c_suite]`, `per_page:5`

It **works and finds the right person** — HTTP 200, correct company, correct seniority. But the
record is obfuscated. Full response for one company:

```json
{ "id": "690595f2a76fb60001dba8e7",
  "first_name": "Nabyendu",
  "last_name_obfuscated": "Ma***l",
  "title": "CEO of a Private Company",
  "has_email": false,
  "has_direct_phone": "Yes",
  "organization": { "name": "Zealous System", "has_phone": true, "has_city": true, ... } }
```

Confirmed by testing:

- **No `last_name` field at all** — only `last_name_obfuscated`
- **No `linkedin_url` field anywhere in the payload** (grepped the whole response: 0 matches)
- `title` is generic ("CEO of a Private Company"), not the person's real title
- Organization object contains only `has_*` booleans, never values
- Reproduced identically on **two different API keys**

Adjacent endpoints, same keys:

| Endpoint | Result |
|---|---|
| `mixed_people/api_search` | **200** — obfuscated as above |
| `mixed_people/search` | **403** `API_INACCESSIBLE` — "not authorized ... include this endpoint in its configured scope" |
| `people/search` | **403** same |
| `people/match` (People Enrichment) | **403** same |
| `organizations/enrich` | **200** — fully un-obfuscated, 61 populated fields |
| `mixed_companies/search` | **200** — fully un-obfuscated |

**Note the asymmetry: Apollo's COMPANY data comes back complete and unmasked on the free tier;
only PEOPLE data is masked.** Company enrichment on a domain returns real name, primary_domain,
estimated_num_employees, industry, city, country, founded_year, company linkedin_url and phone.

## 3. The conflict we cannot resolve from outside

- Apollo's **own API reference for People API Search** documents `last_name_obfuscated` as a
  standard response field, and describes the masking format ("first 2 characters, asterisks, last
  character"), **with no mention of any plan or tier condition**. That reads as though obfuscation
  is a property of the *endpoint*.
- A third-party guide states obfuscation applies on **free / Basic** plans, implying paid plans
  return full names. That reads as though it is a property of the *plan*.

These cannot both be the whole truth, and the difference decides whether buying helps.

## 4. The questions that determine the buy decision

Please answer these specifically, with sources, and ideally with confirmation from Apollo sales,
support, or documentation rather than blog inference.

**Q1 (primary).** On a **paid** Apollo plan, does `POST /api/v1/mixed_people/api_search` return the
**full `last_name`** and a **`linkedin_url`** for each person? Or is the obfuscation inherent to
that endpoint at every tier? If it differs by tier, **which named plan** is the lowest that returns
full names?

**Q2.** Is `mixed_people/search` (note: *not* `api_search`) a currently supported endpoint that
returns un-obfuscated people including `linkedin_url`? It 403s on our keys with a message implying
it merely needs to be added to the key's scope. Is it available on paid plans, deprecated, or
internal-only?

**Q3 (the cost question).** `people/match` (People Enrichment) accepts the `person_id` we already
get free from `api_search`, and Apollo's docs say it returns full name and LinkedIn URL **even when
email/phone are not revealed**. Docs also say credits are consumed "only when relevant data is
found", quoting 1 credit for demographics/email and +8 if a mobile phone is returned.
**With `reveal_personal_emails=false` AND `reveal_phone_number=false`, and only a name +
LinkedIn URL returned — does that call cost 0 credits or 1 credit?** This single number changes
our cost for a 3,100-company backlog from nothing to 3,100 credits.

**Q4.** What are the credit allowances and rate limits per paid tier, for: people search, people
enrichment, organization search, organization enrichment? Are people-credits and
organization-credits separate pools?

**Q5.** Indian coverage. What is Apollo's realistic **founder/CEO identification rate for Indian
IT-services companies of 10–250 employees** — not enterprises, not US firms? We do not need their
phone numbers, only whether the right person is identifiable.

**Q6.** Is there any contractual or ToS restriction on taking a person's identity from Apollo and
looking up their contact details with a **different** vendor? We want to be sure the intended
architecture is permitted.

## 5. How the answers map to our decision

| Finding | Decision |
|---|---|
| Paid plan un-obfuscates `api_search` (full name + LinkedIn URL) | **BUY** — cheapest path, 0-credit search at 600/hr solves everything |
| `mixed_people/search` available on a paid plan, un-obfuscated | **BUY** — same outcome |
| Only route is `people/match`, and it costs **0 credits** identity-only | **BUY** |
| Only route is `people/match`, and it costs **1 credit** identity-only | **BUY IF** the plan bundles ≥5,000 credits/month at sensible cost |
| `people/match` forces a phone reveal, or costs ~8–9 credits per person | **DO NOT BUY** — we would be paying twice for phones we already get from SignalHire |
| Obfuscation applies at every tier and `people/match` is the only option at high cost | **DO NOT BUY** — Apollo is an enrichment vendor for us, not a search vendor, which is the opposite of what we need |

## 6. Explicitly out of scope

Do not research: email deliverability, sequences/outreach features, CRM integration, Apollo's
Chrome extension, or competitor comparisons. We are not evaluating Apollo as a sales platform. The
only question is whether it can hand us **a full name or a LinkedIn URL, at volume, cheaply**.

## 7. Useful context if it helps you weight answers

- We already know Apollo's **company** data is complete and free to us, and we will use it
  regardless of this decision (to backfill headcount / founding year / industry on ~6,700 domains
  we hold). That is not in question and should not influence the people-side recommendation.
- Our fallback if Apollo cannot do discovery is to keep SignalHire's capped search (~171/day,
  ~19 days to clear our backlog) and separately negotiate a higher limit with SignalHire.
