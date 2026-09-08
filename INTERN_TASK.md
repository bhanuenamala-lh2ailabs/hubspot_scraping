# Automation Intern — Take-Home Task

## Contact-Enrichment Pipeline

This is a real slice of what the Founder's Office actually does. It is not a puzzle with a
clean answer — it is a messy, real-world automation problem, and how you handle the mess is
exactly what we're evaluating. Use any AI tools you like (Claude Code, Cursor, ChatGPT) — we
use them daily and expect you to. We care about working software and good judgement, not
whether you memorised an API.

**Time:** budget ~4–6 hours of real work. Submit within **4 days**. Don't spend money — free
tiers only.

---

## The problem

We buy things from small IT-services companies, so we constantly need to reach **the right
decision-maker** at a company — a founder, co-founder, CEO, CTO, Managing Director, or similar
— not a sales rep, not an intern, and not a random namesake.

**You get:** a CSV of **25 small/mid IT companies** (`companies.csv`, attached) — each row has
`company_name, website, city`.

**You build:** an unattended Python pipeline that, for each company, finds the **best person to
contact** and outputs:

```
company, website, city, person_name, person_title, linkedin_url, email_or_phone,
source_url, confidence, notes
```

…and writes the result to a **Google Sheet** (via the Sheets API, not copy-paste).

"Best person" = the most senior person who could actually authorise a business decision. You
decide the priority order and defend it. A founder beats a CTO beats a marketing manager. If
you can only find a name and no contact, that's still a partial result — record it, don't drop
it.

---

## Why this is hard — the real problems you'll hit (and we hit, every day)

These are not hypothetical. Every one of them is a wall we've run into on this exact pipeline.
How you deal with them *is* the test:

1. **LinkedIn blocks scraping.** Fetching a LinkedIn profile directly returns HTTP 999. You
   cannot scrape it. So a profile URL has to come from somewhere that already indexed it, and
   you have to be cleverer than "just scrape LinkedIn."

2. **Free search engines bot-wall a single IP fast.** Hit DuckDuckGo/Bing/Google HTML more than
   a handful of times from one machine and you get blocked for hours. Design around it —
   server-side search APIs, careful pacing, official data sources, whatever works. Tell us what
   you chose and why.

3. **Namesakes.** "Rajesh Kumar" returns fifty people. Picking the wrong one means we call a
   stranger. You must **verify** the person actually belongs to *that* company — and when you
   genuinely can't tell, it is better to leave it blank than to guess. **A wrong contact is
   worse than an empty one.**

4. **No hallucination.** Every non-empty answer must be backed by a `source_url` you actually
   fetched in the run. If an AI model "recalls" a plausible email that no page confirms, that's
   a bug, not a feature. Show how you keep the model honest.

5. **Names are messy.** Official registry names are ALL-CAPS with surname-first ordering and
   middle names ("KUMAR RAJESH S"); LinkedIn has "Rajesh Kumar Srinivasan". Matching them is
   fuzzy. Data cleaning is half the job.

6. **Runs break.** APIs rate-limit (429), pages time out, the process gets killed. Your pipeline
   must **checkpoint and resume** — if it dies at company 14 of 25, re-running continues from 14,
   doesn't redo 1–13, and doesn't double-spend any quota.

7. **Cost is real.** Everything is on free tiers. Track what each run costs (API calls, credits)
   and tell us where it breaks if we run it on **5,000** companies instead of 25.

---

## Must-have

- **Python**, structured as something we could actually run and read.
- **A working discovery approach** for company → person → LinkedIn URL, with your reasoning for
  the tools/sources chosen (free-tier search API, public registry data, etc.).
- **Verification logic** that defends each pick against the namesake problem.
- **Checkpoint / resume** so an interrupted run continues cleanly.
- **Rate-limit handling** — back off on 429s, don't hammer a blocked source.
- **Google Sheets output** via the Sheets API using OAuth (your own Google account, free).
- **No secrets in the repo** — keys via environment variables / a `.env` you don't commit.
- **A short README** (see "Writeup" below).

## Good to have (pick what you can — not all expected)

- An **LLM/agent step** — e.g. use an AI model to extract the decision-maker from messy page
  text, or to judge whether a candidate profile matches the company. If you use one, show how
  you stop it from making things up.
- A **contact-finding step** beyond the URL — a verified work email (free email-finder tier) or
  a phone, with the same no-hallucination rule.
- A **daily summary emailed via the Gmail API** at a fixed time (tests scheduling + Gmail
  OAuth) — "ran 25 companies, found 18, 3 failed, here they are."
- Graceful handling of companies with **no findable person** — route them to a "needs manual
  review" lane, don't crash.

---

## What we're evaluating

| We look at | What good looks like |
|---|---|
| **Does it work?** | We run it on the 25 and it produces the sheet, end-to-end, unattended. |
| **Correctness** | We spot-check 5 contacts. Are they the right person at the right company? |
| **Judgement on the hard cases** | How you handle namesakes, bot-walls, failures — the writeup and the code both show your thinking. |
| **Honesty** | Blanks where you couldn't verify, not confident-wrong guesses. Sources cited. |
| **Engineering** | Resumable, rate-limit-safe, no hardcoded secrets, readable. |
| **Scaling sense** | You understand what breaks at 5,000 and roughly what it'd cost. |
| **Bonus components** | Any of the "good to have" done well. |

We genuinely weight a **thoughtful writeup about what *didn't* work** as highly as a high hit
rate. This problem has no 100% solution — some of these people simply aren't findable — and
recognising that honestly is a strong signal.

---

## Writeup (put it in the README)

Keep it short — half a page to a page:

1. **Your approach** — the pipeline stages and which tools/sources you used for discovery, and
   why.
2. **The hardest sub-problem** you hit and how you handled it.
3. **What didn't work** — dead ends, sources that walled you, people you couldn't find, and why.
4. **Cost + scaling** — what one run costs, and what changes (cost, architecture, rate limits)
   if this ran on 5,000 companies daily.
5. **Your hit rate** — of 25, how many did you find a verified decision-maker for? Be honest.

---

## Submit

- A **GitHub repo** (public, or invite us) — code + README, runnable with clear setup steps.
- The **Google Sheet** link (view access) with your 25 rows filled in.
- Anything you're proud of.

We'll read the code, run it if we can, and the strongest submissions get a short call to walk
through your choices. Build something real. Have fun with it.
