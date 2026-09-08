# Problem: LinkedIn profile URL for a known person, free, at 349-scale

Hand this to a research agent. It is a NARROW successor to FOUNDER_LOOKUP_PROBLEM_V2.md — that
one asked "who is the founder"; we solved that. This asks only the one step left. Section 6 is
the question. Sections 4 and 5 are the walls already hit — do not re-propose anything there.

---

## 1. Exactly where we are

We ran a pipeline over 8,144 Indian IT-services companies and produced a ranked, evidence-
audited shortlist of 450 worth acquiring codebases from. For **349 of them we now have the
founder/director's real NAME**, each cited to a public MCA (Ministry of Corporate Affairs)
company-registry page — free, legally-published director data, obtained WITHOUT any search
engine (we construct quickcompany.in URL slugs directly). That half is solved and repeatable.

We hold **5,000 SignalHire reveal credits**. SignalHire's reveal endpoint turns an identifier
into a phone number + email. It accepts a **LinkedIn profile URL**, an email, or a phone as
the input item. It does **NOT** accept a name (their name→people *search* endpoint is
permanently disabled for our account). We tested email-as-input: it returns `failed`. So in
practice **the LinkedIn profile URL is the only key we can produce that reveal will accept.**

**The entire remaining problem, in one line:**

> Given a person's full NAME + their COMPANY name + the company's WEBSITE, find that specific
> person's LinkedIn profile URL (`linkedin.com/in/...`) — free, unattended, for 349 people
> now and ~3,000 more behind them.

## 2. Why we can't just fetch it

- **LinkedIn blocks all anonymous access** — any direct GET to linkedin.com returns HTTP 999.
  We never fetch LinkedIn. The URL must come from somewhere that already indexed it (a search
  engine's result list / snippet), and we accept a URL only when the snippet co-names the
  person AND the company, and the URL matches `^https?://([a-z]{2,3}\.)?linkedin\.com/in/[^/?#]+/?$`.
- So this reduces to: **run a web search like `site:linkedin.com/in "<name>" "<company>"` and
  read the result URL** — without a working search engine.

## 3. Why that is hard — the wall

Every free web-search surface we can reach **bot-walls our single residential IP**:

| Engine | Behaviour from our IP |
|---|---|
| DuckDuckGo HTML (`html.duckduckgo.com`) | Works for ~8 queries, then blocks; needs a multi-hour/overnight cooldown. ~8–50 usable queries/day. |
| Bing HTML | 200 OK but returns a bot-wall page, zero results |
| Ecosia | HTTP 403 |
| Mojeek | empty shell page |
| Yandex, Searx.be, Startpage | bot-wall / 429 |
| Google (scrape) | not attempted — assumed hardest wall |

At DuckDuckGo's ~8–50/day, 349 people (×1–2 queries each) is **1–3 weeks**; the 3,000-company
reserve behind them makes that unworkable. We have **one residential IP** and cannot rotate IPs.

## 4. ALREADY USED / RULED OUT — do not re-propose

- SignalHire name→company **search** endpoint — permanently banned for this account.
- Anthropic/Claude **web-search tool** — budget-dead (hard $20 cap consumed; was ~$0.02/company).
- **Company website /team /about /leadership scraping** (static + headless) — already done
  across all 450; only ~19% yielded a linkedin.com/in link. The residual sites publish none.
- **LinkedIn direct fetch** — HTTP 999, banned.
- **Common Crawl for linkedin.com/in** — near-zero coverage (LinkedIn blocks CCBot); ruled
  out by prior research.
- **Email-as-reveal-key** — SignalHire returns `failed` for email items; not a path.
- **Jina s.jina.ai / r.jina.ai** — keyless requests return HTTP 401/403 from here; a *free
  API key* is the open question in §6, not yet obtained.
- DuckDuckGo/Bing/Ecosia/Mojeek/Yandex/Searx/Startpage HTML scraping — all walled (see §3).

## 5. Constraints any answer must satisfy

1. **Free**, or a one-time free signup — no per-query paid API, no card. (We will do a 2-minute
   signup if that unlocks it.)
2. **Unattended batch** over 349 now, 3,000+ later, from **one residential IP** (no IP rotation).
3. **Verifiable**: the URL must appear in fetched content (a result snippet) that co-mentions
   person + company; no model-recalled or guessed URLs. A wrong LinkedIn URL wastes a reveal
   credit and, worse, calls the wrong person.
4. Tolerates multi-day runtime if it must, but must make steady unattended progress — not
   ~8 queries then a day of silence.
5. No credentialed/logged-in LinkedIn access.

## 6. The question

> What is a FREE (or free-signup) way to resolve `("<full name>", "<company>")` → that
> person's `linkedin.com/in/` URL, at 349→3,000 scale, from a single non-rotatable residential
> IP, given that DuckDuckGo/Bing/Ecosia/Mojeek/Yandex/Searx/Startpage all bot-wall this IP and
> we never fetch LinkedIn directly?

Specific sub-questions worth verdicts:
- **Jina AI free tier**: does a free `s.jina.ai` API key actually run server-side searches
  (from Jina's IPs, bypassing our wall) at a usable rate, in 2026? What's the real free quota,
  and does it return result URLs + snippets we can verify against? This is our current lead.
- **Google Programmable Search JSON API**: still offers a free 100 queries/day tier to *new*
  keys in 2026, or discontinued? If alive, that's 100/day at zero cost — enough.
- **Brave Search API / others**: any independent search index with a genuine free tier and an
  API (not HTML scraping, so the IP-wall wouldn't apply)?
- **A bulk inversion**: any free corpus/dump where one download maps many
  Indian-company-founders → LinkedIn URLs at once, instead of 349 individual lookups? (Common
  Crawl for linkedin.com/in is already ruled out — near-zero coverage.)
- **Anything that sidesteps needing the URL at all**: a free source that yields the person's
  direct mobile or a work email that SignalHire's *waterfall* mode (we currently use
  `withoutWaterfall:true`) would accept — turning name+company straight into a number.

## 7. What the solver may assume as available

Python on macOS; this repo's crawl/parse utilities; the 349 names each with company + verified
website + city + the MCA source URL; 5,000 SignalHire reveal credits; a HubSpot API key;
Google Sheets/Drive read-write + Gmail-send as the human account; GitHub CLI authenticated;
willingness to do ONE free third-party signup if that is the unlock. Zero paid-API budget. One
residential IP, currently engine-walled.
