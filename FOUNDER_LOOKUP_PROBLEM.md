# Problem statement: finding a company's founder, at volume, cheaply

Written to be handed to someone with no context. Everything below is measured from real runs,
not estimated. If you want to propose a solution, section 7 is the actual question.

---

## 1. What we are trying to do

We buy dormant software codebases from small IT-services firms. To do that we cold-call the
person who can actually sell one — the founder, co-founder, CEO or managing director. Nobody
below that level can authorise selling a codebase, so a generic `info@` address or a
switchboard number is worth roughly nothing to us.

Our input is a **list of companies**, not a list of people. We source these lists from industry
directories (NASSCOM, the Indian IT industry body — 2,775 members; similar directories for other
countries). A directory row gives us: company name, website, city, sometimes headcount. It does
**not** give us a person.

So for every company that survives our qualification filters, we must answer one question:

> **Who runs this company, and what is their mobile number?**

Scale: we graded **1,702** NASSCOM firms, of which **144** passed filters and are worth calling.
That 144 is one batch from one directory. We expect to repeat this for other directories and
other countries indefinitely. So a solution that costs a lot per company does not scale, and a
manual solution does not scale either.

---

## 2. The enrichment chain, and exactly where it breaks

```
   company name + website
            |
            v
     [ STEP 1 ]  find the founder's NAME                     <-- works, ~72-91%
            |
            v
     [ STEP 2 ]  find that person's LINKEDIN PROFILE URL     <-- THIS IS THE BOTTLENECK
            |
            v
     [ STEP 3 ]  SignalHire "reveal" the profile -> phone    <-- works, and we have credits
            |
            v
     [ STEP 4 ]  push to CRM, caller dials
```

**Step 3 is not the problem and this is the counter-intuitive part.** We have a SignalHire
account with **5,000 reveal credits sitting unused**. Reveal works well: given a LinkedIn
profile URL it returns the person's name, current title, phone numbers, emails and other socials.
Measured: 17/17 successful reveals, 13 of which carried a phone number.

The catch is that **reveal is a lookup, not a search**. Its input must be an identifier we
already possess — a LinkedIn profile URL, an email, or a phone. You cannot ask it "who is the
founder of Acme Systems Pvt Ltd". The endpoint that *did* answer that question
(`/candidate/searchByQuery`, company/title → list of people) runs on a **separate daily search
quota that is exhausted**, and we have been instructed not to use it again.

So we hold 5,000 credits we cannot spend, because we lack the keys to spend them on.

**Step 2 is therefore the whole problem.** A founder's name alone is useless to us — we cannot
dial a name. We need the name converted into a resolvable identifier.

---

## 3. The measured numbers

For the **144** qualified firms:

| | count | % |
|---|---|---|
| Firms needing a contact | 144 | 100% |
| Founder **name** found | 103 | 72% |
| Founder **LinkedIn URL** found | 47 | 33% |
| **Name found but no LinkedIn URL** → dead end | **56** | **39%** |

Across the wider pool of 311 firms we attempted:

| | count | % |
|---|---|---|
| Attempted | 311 | 100% |
| Name found | 283 | 91% |
| LinkedIn URL found | 130 | 42% |
| Name but no URL → dead end | 153 | 49% |

**Read that gap.** Roughly half of all successful founder identifications terminate in a name we
cannot act on. That is the single largest loss in the pipeline.

---

## 4. Everything already tried, and how each one failed

| Method | Result | Why it failed |
|---|---|---|
| **Scrape company website** (`/team`, `/about`, `/leadership`) | 83/200 firms yielded any person (41%) | Small firms genuinely do not publish a team page. Not a scraping defect — the data is absent |
| **Headless-browser render** (Playwright) of the same pages | 5/56 firms yielded a LinkedIn profile URL (9%) | Confirms the above: the residual firms publish nothing. JS rendering did not help because there was nothing to render |
| **GoodFirms** (B2B directory that lists founder names) | 403 on every company profile | Cloudflare bot challenge |
| **LinkedIn directly** (company page → "people" tab) | HTTP 999 | Hard-gated against non-authenticated access |
| **MCA / data.gov.in** (Indian corporate registry) | Datasets contain registration data but **not director names** | Director data exists in MCA's paid per-document portal, not the open bulk datasets |
| **SignalHire `searchByQuery`** (company → people) | Would solve this exactly | Daily search quota exhausted; permanently retired by instruction |
| **SignalHire `reveal`** (identifier → contact) | Works, 5,000 credits available | Cannot be used without an identifier from step 2 |
| **LLM with live web search** (Claude Haiku + `web_search`) | Best result so far: 91% name, 42% URL | Works, but **costs money per company** — see below |
| **RDAP / WHOIS** (domain registration) | Registration dates yes, names no | Registrant identity is redacted by privacy services on essentially every domain |

### On the LLM-with-web-search route specifically

This is currently the best method and the reason the numbers in section 3 are as high as they
are. Measured cost: **~$0.022 per company** (one web search at $10/1,000 searches, plus ~11k
tokens of a cheap model). We deliberately used a search tool rather than model recall, because
recall produces confident, plausible, wrong people — every row we keep carries a source URL so
the name can be checked, and a name with no source is recorded as not-found rather than guessed.

**Why it is not the answer:** we are on a hard **$20 budget cap, of which $19.32 is already
spent**. At $0.022/company that budget buys roughly 900 lookups total, and it is now essentially
gone. It also only produced a usable LinkedIn URL 42% of the time even when it *was* running —
so it does not solve step 2 either, it just fails at it slightly less often.

---

## 5. Constraints any proposal has to respect

1. **Cost.** Effectively zero budget. Free, or a one-off cost that does not scale per company.
   A method costing $0.02/company is already too expensive at our volume and cadence.
2. **The identifier problem is the real one.** A method that returns founder *names* more
   accurately does not help — we are already at 72–91% on names. We need names converted into
   something dialable or resolvable.
3. **Phone must be a mobile.** For Indian leads there is a hard rule: no Indian mobile number,
   no push to the CRM. Switchboards and `info@` addresses are rejected. (For non-Indian
   batches the country rule is relaxed, but a personal line is still worth far more than a
   switchboard.)
4. **Accuracy over coverage.** A wrong name is worse than no name — a caller who opens with the
   wrong person's name loses the call immediately. Any proposal must be verifiable against a
   source, not a model's recollection.
5. **No credentialed LinkedIn scraping.** Not proposing to log in and scrape.
6. **Repeatable and unattended.** This runs as a batch job over hundreds of firms. Something
   requiring manual work per company does not qualify.
7. **The companies are small and low-profile.** Median NASSCOM member is ~43 employees. These
   are not firms with press coverage, Crunchbase pages, or Wikipedia entries. Any method that
   implicitly assumes the company is well-documented on the open web will score far worse than
   its benchmarks suggest. **This is the single most common reason a proposed solution fails
   here.**

---

## 6. What we already know about the shape of the answer

- The reveal step is solved and paid for. Anything that produces **a LinkedIn profile URL, a
  work email, or a phone number** for a named person instantly unlocks 5,000 waiting credits.
  A proposal only has to reach one of those three identifiers — not all the way to a phone.
- Roughly half of our dead ends have a **confirmed correct name** attached. So the input to any
  proposed step 2 is not "company name" alone — it can be `(company name, website, city, person
  name, person title)`. That is a much richer query than a cold company lookup, and we do not
  believe it has been fully exploited.
- Domain is known for every firm, which makes work-email pattern inference (`first.last@domain`)
  theoretically available — but we have not found a free way to *verify* a guessed address, and
  an unverified guess violates constraint 4.

---

## 7. The question

> Given `(company name, website, city, and for ~half of them a confirmed founder name and
> title)`, for small, low-profile Indian IT firms of ~40–600 employees — **what is a free or
> near-free, repeatable, unattended way to obtain a LinkedIn profile URL, verified work email,
> or direct phone number for that specific person?**

Secondary question, if the above has no good answer:

> Is there a fundamentally different acquisition channel that skips the company→person lookup
> entirely — i.e. a source that is *natively* a list of founders which can then be filtered down
> to firms matching our criteria, rather than a list of companies we must resolve to people?

Note on the secondary question: our own data supports it. Across all lead sources we have run,
hand-picked leads convert at **20.8%** while everything acquired by bulk scraping converts at
**0.21%** — a ~100× difference. So a lower-volume, higher-quality channel is not a consolation
prize; it may be the correct answer.
