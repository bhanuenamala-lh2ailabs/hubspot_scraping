# Problem V2: company → founder identity, free, at 450-company scale

Successor to FOUNDER_LOOKUP_PROBLEM.md (which produced the prequalification pipeline that
created this exact situation). Everything below is measured from real runs on 2026-08-14/15.
Section 5 lists every method already used — **do not re-propose anything in it.** Section 6
lists what was considered but never actually attempted — those are fair game if you can crack
the access problem. Section 8 is the question.

---

## 1. Context in one paragraph

We buy dormant software codebases from small Indian IT-services firms (25–800 headcount). A
usable lead = the founder/CEO/CTO's personal mobile. We hold **5,000 SignalHire reveal
credits**: given a **LinkedIn profile URL** (or an email/phone), reveal returns the person's
name, title, phones, emails — that step is solved and paid for. The *search* endpoint
(company name → people) is permanently retired for us. So the entire problem is:

> company name + verified website → the leader's NAME and, ideally, their LINKEDIN URL.

## 2. Current stock (the immediate work-list)

A ranked, evidence-audited queue of **450 companies** (plus 3,092 in reserve behind it, so
the method must repeat):

| Identity state | n | Meaning |
|---|---|---|
| full (name + title + LinkedIn URL) | 30 | reveal-ready today |
| name only, no URL | 54 | cannot be revealed — URL/email/phone are the only accepted keys |
| nothing | 366 | the problem |

Every company has: verified live website, city, headcount band, founded year (most),
service-mix and owned-product evidence quotes, careers-page text (median firm publishes
20k+ chars of JD text), and domain registration date. These are *rich* inputs — richer than
a cold company name.

## 3. Why this is hard — the shape of the target

Median firm ≈ 40–150 employees, city-tier mixed, **no Crunchbase, no press, no Wikipedia**.
About 60% publish no team page at all (measured: 41% of 200 yielded any person; a JS-render
pass on the residual added ~5%). Their founders exist on LinkedIn almost universally — but
LinkedIn is gated (HTTP 999 anonymous), and every free search engine that can find LinkedIn
profiles has bot-walled this machine's IP (details below).

## 4. What SUCCESS must look like (constraints, unchanged from V1 plus new ones)

1. **Free or near-free at 450+ scale, repeatable weekly.** Anthropic web search worked (91%
   names / 42% URLs) but is budget-dead: hard $20 cap consumed; ~$0.02+/company at our volume
   was ruled unacceptable even before that.
2. **Verifiable, not recalled.** Every name needs a checkable source; a wrong name torches a
   cold call. Model memory alone is banned.
3. **Unattended batch operation.** No per-company manual work.
4. **Output priority:** LinkedIn URL > work email > name alone (name alone still helps — a
   caller can ask the switchboard for the person by name — but it cannot feed reveal).
5. **No credentialed/logged-in scraping of LinkedIn.**
6. The downstream +91-mobile gate and seniority gate stay; reveal handles those.

## 5. ALREADY USED — do not propose again

| Method | Result |
|---|---|
| SignalHire searchByQuery | retired permanently, instruction-level ban |
| Anthropic (Claude) web-search tool | best performer; budget-dead; also only 42% URL yield |
| Company site /team /about /leadership scrape (static) | 41% of firms yield any person |
| Same, with headless render (Playwright) | +5% on the residual — the data is absent, not hidden |
| GoodFirms company profiles | Cloudflare 403 wall |
| GoodFirms crawler's OWN people table (local sqlite) | exploited fully — source of today's 30 |
| Prior NASSCOM founder-search caches (local) | exploited fully |
| LinkedIn direct (company pages, people tab) | HTTP 999 |
| DuckDuckGo HTML endpoint | worked for ~15 queries, then permanent anomaly-wall on this IP |
| Bing HTML | botwall page (200 OK, zero results) |
| Ecosia | 403 |
| Mojeek | empty shell page |
| Google cache/search | not attempted directly (assumed hardest wall) — see §6 |
| MCA via data.gov.in open datasets | registration data only, **no director names** |
| RDAP/WHOIS registrant | privacy-redacted everywhere |
| Wayback | dates only, no people |
| CRM contact emails' domains | personal gmail/yahoo (reveals return personal emails) |
| Domain-slug guessing + homepage verification | solved DOMAINS (10/12), not people |

Engine-wall detail that matters: the walls are per-IP and sticky. 10-second pacing did not
lift them within a session. Untested: overnight cooldown, different network, per-engine
rotation at very low rate (e.g. 50/day/engine). A method that needs 1 query per company and
tolerates 3 days of runtime is acceptable.

## 6. Considered, NEVER attempted — fair game

- **MCA director-data aggregators**: Zaubacorp, Tofler, FalconEbiz, IndiaFilings company
  pages list directors (DIN + full names) for every Pvt Ltd — the legally-public answer to
  "who runs this company". Expected Cloudflare; never actually probed. Company-name →
  legal-entity-name matching is fuzzy but our V1 solved that class of problem before.
- **GST portal / IEC lookups** — proprietor names for smaller entities.
- **Justdial / IndiaMART / Sulekha listings** — SMB listings frequently carry the owner's
  name and a direct mobile (which would skip reveal entirely).
- **Google Programmable Search JSON API** — 100 queries/day FREE tier; 450 companies ≈ 5
  days at zero cost, or split across multiple free keys. This is an *API*, not scraping —
  the wall problem may not apply. Nobody has tried it here.
- **LinkedIn public profile URLs via sitemap/commoncrawl** — Common Crawl has LinkedIn
  profile pages in its index; a title-search for "<Company> founder" inside CC's index is
  free and bulk.
- **Company GitHub orgs** → org owners/members → profile pages often link LinkedIn.
- **Founder-authored content**: company blog author pages, YouTube channel "about", press
  releases on free PR wires, award lists (NASSCOM awards, Clutch leader lists).
- **The companies' own careers ATS instances** (Zoho Recruit, Keka, etc.) sometimes expose
  "reporting to" or leadership names.
- **Email-pattern inference + free SMTP verification** (MX + RCPT probe) — we already built
  a Selenium/SMTP validation engine for a different task; pattern-guess `founder-name@domain`
  requires the name first, so this only helps once names exist — but `info@domain` reveal
  attempts are NOT banned and cost only a failed-credit check (needs confirming whether
  SignalHire charges for misses).
- **Waterfall reveal mode** — our reveal calls use `withoutWaterfall: True`; SignalHire's
  waterfall/callback mode may accept weaker keys. Unverified; needs reading their docs.

## 7. Assets the solution may assume

Python on macOS; this repo's crawl utilities; HubSpot API; SignalHire reveal credits (5,000);
full Google Sheets/Drive read-write + Gmail-send as the human account; GitHub CLI authed; the
two corpora (GoodFirms sqlite with 5,455 raw listing HTMLs on disk, NASSCOM harvests);
**zero** paid-API budget; one residential-class IP currently engine-walled.

## 8. The question

> For 450 (then 3,000+) small Indian IT firms with verified websites and rich metadata but
> no published team pages: what is a FREE, repeatable, unattended route to the founder's
> NAME and preferably LINKEDIN URL that is not in Section 5 — with a concrete access plan
> for whatever wall it hits (Cloudflare, rate limits, engine bans)?

Secondary: is there any free bulk corpus (Common Crawl, MCA bulk XBRL, public LinkedIn
sitemap dumps) where ONE download answers hundreds of these at once, inverting the
per-company lookup entirely?
