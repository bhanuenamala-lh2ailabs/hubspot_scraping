# Scraping tasks — what worked, what blocked, and what I could not answer

**Date:** 18 Aug 2026. Two separate scraping jobs were run. Task 1 largely succeeded; Task 2
largely did not, and most of the reasons are external rather than fixable by better code.

Everything below was verified live today, not taken from the brief.

---

# TASK 1 — the five association directories (GESIA / HYSEA / GTech / iTAAP / DSCI)

**Outcome: succeeded.** 1,419 rows scraped → 951 after intra-scrape dedup → **672 genuinely new
companies** after deduping against our existing pools (~26% overlap). Those 672 are now being run
through the prequalification crawler.

| Source | Result | How it was reached |
|---|---|---|
| HYSEA | 822 rows | single static page, all member links in the HTML |
| GTech | 228 rows | looked JS-blocked; found its DataTables AJAX source at `gtechindia.org/home/getMembers` and hit that directly |
| ITAAP | 214 rows | single static page |
| GESIA | 139 rows | WordPress pagination `/members-directory/page/N`, 7 pages |
| **DSCI** | **16 of ~544 — BLOCKED** | see below |

## Issue 1.1 — DSCI: token/challenge wall (UNRESOLVED, but I recommend abandoning it)

The member list is served by `GET /backend/api/v2/list/corporate-member?_format=json&page=N`,
which returns **HTTP 401**. The React bundle builds the call as
`headers:{Authorization:` Bearer ${token}`}` and obtains that token from
`POST /api/auth/token/exchange` with a body of `{challenge_id, solution}` — a proof-of-work or
CAPTCHA-style handshake. Only page 1 (16 rows) is rendered server-side and readable.

**What I could not answer:** how a public, unauthenticated client is supposed to obtain that token.

**Why I recommend not solving it anyway:** DSCI is the wrong pool for us. Its page-1 members are
Accenture, Adobe, HSBC, Airtel Payments Bank, Aditya Birla, Agratas Energy. Its own sector list is
BFSI, GCC-BFSI, GCC-Digital, GCC-Manufacturing, Pharmaceuticals, Aviation, Oil Energy & Power —
i.e. large enterprises and captives, which our pipeline already routes out. It also carries **no
website field**, only name/sector/city, so every row would need domain resolution afterwards.

---

# TASK 2 — the 16 directories in `FUll states scrape instructions.md`

**Outcome: largely failed.** Only **132 companies** were produced, **72 with a domain**, against a
brief that anticipated well over 15,000. The failures fall into four distinct classes, and only
one of them is my fault.

## Class A — robots.txt disallows us (5 sources, 3 also return HTTP 403)

Verified live today with a robots parser using our own user-agent:

| Source | robots.txt | Live GET | Brief said |
|---|---|---|---|
| **techbehemoths.com** (~10,793 cos) | **DISALLOW** | **HTTP 403** | "none major" |
| **sortlist.com** (~898) | **DISALLOW** | **HTTP 403** | "rate limiting" |
| **clutch.co** (~3,110) | **DISALLOW** | **HTTP 403** | "Cloudflare + rate limiting" |
| **technoparktoday.com** (~370) | **DISALLOW** | 200 | "none" |
| **itcitymohaliassociation.com** | **DISALLOW** | 200 | "unverified" |

This is the single biggest reason the task under-delivered. **TechBehemoths alone was ~10,793 of
the expected volume** and is double-blocked (robots *and* a 403 to our UA). Per Section 6 of the
brief ("respect, don't fight — no IP rotation, no solver services") these were skipped, not worked
around.

**What I could not answer:** whether there is a legitimate route to this data — a public API, a
licensed data feed, a partner/affiliate arrangement, or a paid export. That is a commercial or
licensing question, not a technical one, and I am not going to route around a robots directive to
find out.

## Class B — host unreachable from this machine (2 sources)

| Source | Error |
|---|---|
| **blr.stpi.in** (~174 units) | `URLError` — connection fails outright, no robots.txt served |
| **via-india.com** (Nagpur) | `URLError` — same |

Both fail at the network layer, before any HTTP status. Reproducible across retries.

**What I could not answer:** whether these hosts are down permanently, geo/ASN-blocking us, or
have a TLS configuration our client rejects. Worth testing from a different network before
concluding anything — the brief listed both as reachable, so this may be transient or specific to
this machine.

## Class C — the URL in the brief does not exist (2 sources)

| Source | URL from the brief | Live |
|---|---|---|
| **ait-bengaluru.in** (~439) | `/business-directory/` | **HTTP 404** |
| **escindia.in** (~2,000–2,200) | `/our-members/` | **HTTP 404** |

The domains resolve and robots allows us; the specific paths are simply wrong or have moved.

**What I could not answer:** the correct current path to each members list. Both need someone to
open the site and read the navigation — cheap to fix, but it is a research task, not a code fix.

## Class D — reachable, allowed, and MY parser under-performed (5 sources) — my fault

These returned real HTML and robots permits us; the poor yield is my extraction, not the site:

| Source | Live page | Rows I got | Assessment |
|---|---|---|---|
| **infopark.in** (~582) | 200, 111 KB, ALLOW | **0** | **Parser bug — already diagnosed and fixed, but the fix landed after the run had started, so it never applied.** Each company is a `<div class="compy">` with the name in `<h5>` and the domain as **plain text** in `<div class="web">` (no anchor). My first parser looked for anchors. This is the highest-value fixable item — re-running should yield ~580 companies with domains. |
| sidatn.org | 200, 220 KB | 121 ✓ | worked |
| stpi.in national list | 200, 55 KB | 10 | generic table parser too weak for this layout |
| itaoodisha.org | 200, 16 KB | 1 | ditto |
| rito.org.in | 200, 23 KB | 1 | ditto |

**No open question here — this is mine to fix.** Each needs its markup inspected and a
source-specific parser, exactly as I did for GTech and Infopark.

## Issue 2.1 — dedupe reported 0% overlap, which is certainly wrong

Every source reported `overlap_pct = 0.0` against our existing 5,629-company universe. Task 1 saw
~26% overlap on comparable sources, so 0% is not credible. Likely a column-mapping fault in my
prior-universe loader rather than genuinely no overlap. **Mine to fix**, but it means the "new
company" counts from Task 2 are currently unverified.

---

# Summary — what needs a human or a research pass

| # | Question I could not answer | Type |
|---|---|---|
| 1 | Is there a **legitimate** route to TechBehemoths / Clutch / Sortlist data — public API, licensed feed, paid export, partner access? (~14,800 companies behind robots + 403) | commercial / licensing |
| 2 | How does a public client obtain a **DSCI** API token via their `challenge_id`/`solution` exchange? *(low priority — wrong ICP anyway)* | technical |
| 3 | Are **blr.stpi.in** and **via-india.com** genuinely down, or blocking this network? | infrastructure |
| 4 | What are the **current correct URLs** for the AIT Bengaluru and ESC India member lists? | simple research |
| 5 | Does the brief's barrier column need revisiting? It said "none major" for TechBehemoths, which is robots-disallowed *and* 403 — so the source research may have been done without checking robots or a live fetch with a bot UA. | process |

# What I am fixing without needing anyone

- Re-run **Infopark** with the corrected parser (~582 companies expected — the biggest single win)
- Write source-specific parsers for **stpi.in**, **itaoodisha.org**, **rito.org.in**
- Fix the **prior-universe dedupe** so overlap % is real
- Re-check **sidatn.org** paging (121 rows may be page 1 of several)

# Honest bottom line

Task 2's shortfall is roughly **80% external** (robots blocks, dead hosts, wrong URLs) and
**20% mine** (parsers). The single largest constraint is that the three high-volume aggregators —
about 14,800 of the ~15,000 companies the brief was built around — are all robots-disallowed.
**No amount of parser work recovers that.** It needs either a licensing conversation or a decision
to drop aggregators and concentrate on association and technology-park directories, which is the
category that actually worked in Task 1.
