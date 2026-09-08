# IT-Services Scrape → HubSpot — Exact Logic & Filters

_Verified against live code + config on **2026-07-31**. Every filter below lists **where its data comes from**._

Engine: `lh2-pipeline/` · CLI: `python -m lh2_pipeline.cli <phase>` · config: `lh2-pipeline/config.yaml`
Phases: `crawl → build → enrich → score → export` (`lh2 run` chains them, resumable)

---

## 1. CRAWL — where companies come from

### Source: **GoodFirms** (the only one live)

| Adapter | State | Note |
|---|---|---|
| `goodfirms` | ✅ **ON** | verified live 2026-06 — name+website+founded+size on the listing itself |
| `clutch` | ❌ off | crawler built; URL/selectors never live-verified |
| `techbehemoths` | ❌ off | selectors verified, but listing lacks website/founded/size → needs profile-page fetch |
| `manifest`, `designrush`, `nasscom` | ❌ off | built, not enabled |

### URL pattern
```
https://www.goodfirms.co/directory/city/top-software-development-companies/{city-slug}?page=N
```
- **20 cities** × **≤12 pages** each → up to 240 page fetches/run
- Cities: Bengaluru, Pune, Hyderabad, Ahmedabad, Indore, Jaipur, Noida, Gurugram, Delhi, Chennai, Coimbatore, Kochi, Mumbai, Kolkata, Mohali, Surat, Vadodara, Nagpur, Bhopal, Trivandrum
- **Slug overrides** (GoodFirms uses legacy names): `bengaluru→bangalore`, `gurugram→gurgaon`, `trivandrum→thiruvananthapuram`

### Fields scraped — CSS selectors on each listing card
| Field | Selector | Feeds which filter |
|---|---|---|
| card | `li.firm-wrapper` | — |
| **company name** | `h3.firm-name a` | outsourcer blocklist, known-name dedup |
| **website → domain** | `.firm-urls a.visit-website, a.visit-website` | known-domain dedup, primary key |
| **city** | `.firm-location span` | (informational; HQ is inferred — see §2.3) |
| **founded year** | `.firm-founded span` | **founded ≤2022 gate** |
| **team size** | `.firm-employees span` | **size gate** |
| segment | `.firm-short-description` | informational |

> ⚠️ **No people data exists on GoodFirms** — verified 2026-07-31 by fetching profile pages directly. "Founder/CEO" strings there are GoodFirms' own nav and **client reviewers'** names. Founders must come from enrichment (§3).

### Politeness settings
`workers_per_host: 1` · random delay **2–5s** · `request_timeout: 45s` · `retry_attempts: 3` ·
rotating identifiable `LH2Bot` user-agents · `honor_robots: false` (**explicit operator ToS decision, 2026-06-30** — crawl directory paths, keep rates polite)

---

## 2. BUILD — canonicalise → dedupe → **gate**

Gates run **in this order**. A firm failing any gate is **not deleted** — it's kept with `gate_pass=False` + a `gate_reason` (audit trail + denominator). **Fail-closed on unknowns**: a smaller correct dataset beats a larger guessed one.

### 2.1 Already-known — by **domain**
- **Rejects if:** the firm's domain is already ours
- **Source of truth:** `data/delivered_domains.txt` (**exported from HubSpot** — every company domain we hold, ~3.9k) + `gates.blocklist_known_domains` in config

### 2.2 Already-known — by **core name** (fuzzy)
- **Rejects if:** the name matches a firm we already have
- **Source of truth:** `dedup_names_sheet_hubspot.csv` (**Google Sheet tabs + HubSpot IT firms**) + `gates.blocklist_known_names`
- **How:** strip generic corporate tokens → compare the *distinctive core*
  - stripped: `technologies, technology, technolabs, tech, solutions, software, labs, systems, services, consulting, consultancy, infotech, infosystems, digital, studio, global, worldwide, group, ventures, pvt, private, ltd, limited, llp, inc, co, company, corp, india, indian`
  - match = **exact core equality** OR **fuzzy `token_set_ratio ≥ 92`**
  - fuzzy only applies if the core is **≥5 chars** — guards against a tiny core like `{"it"}` over-matching everything

### 2.3 Large-outsourcer blocklist
- **Rejects if:** name matches a big outsourcer — never a target
- **Source of truth:** `gates.blocklist_outsourcers` in config.yaml (**20 names**: TCS, Tata Consultancy Services, Infosys, Wipro, HCL, HCLTech, Cognizant, Capgemini, Accenture, Tech Mahindra, …)
- **How:** word-boundary substring match OR fuzzy `token_set_ratio ≥ 90`

### 2.4 HQ country = India
- **Source:** **inferred, not scraped** — we only crawl India city pages, so `hq_country` defaults to `India`
- A firm explicitly marked foreign is **noted, not rejected** ("foreign-incorporated; India-delivery assumed")

### 2.5 Founded year ≤ **2022**
- **Source:** GoodFirms listing card (`.firm-founded span`)
- **Rejects if:** `founded_year > 2022` **or `founded_year` is unknown** (fail-closed)
- **Why:** we want real operating history — a codebase worth acquiring

### 2.6 Size: **50 – 1,000 employees**
- **Source:** GoodFirms listing card (`.firm-employees span`) — a coarse *range*
- **Normalisation:** representative headcount = **midpoint of the range**
  - `"50 - 249" → 149` · `"250 - 999" → 624` · `"10000+" → 10000` · `"300" → 300`
- **Buckets:** `1-100` (≤100), `100-500` (≤500), `500-1000` (≤1000); above 1000 → no bucket → reject
- **Rejects if:** headcount **< 50** (floor) · **> 1000** (ceiling) · bucket not in targets · **size unknown**
- Headcount **≥ 900** (90% of ceiling) is flagged as a note, not rejected

---

## 3. ENRICH — company → founder → contact

**This is the bottleneck.** Crawling yields ~1,121 gate-passed firms; only **~8%** end up with a resolved founder.

| Provider | Role | State |
|---|---|---|
| **SignalHire** | `searchByQuery` → find founder by company+title · `candidate/search` → reveal phone/email | ✅ **only live provider** |
| `company_site` | founder from their own /about, /team | ❌ off (~5% hit rate when tested) |
| `registry_founders` | MCA/ZaubaCorp directors — *legal ground truth* | ❌ off (**source went paywalled**, 2026-07-31) |
| `linkedin_optional` | Proxycurl / Coresignal | ❌ off, keys unset |

- **Cascade** (config): `phone / email / linkedin / name: [signalhire]` — single provider, **no fallback**
- **Phone filter:** normalise to E.164, **keep +91 only** (drops foreign/namesake numbers)
- **Budget guard:** hard **4,000 credits/month**, spread as a fair daily share (`governor.py` + `quota_ledger.py`)
- ⚠️ **Real limit is the SignalHire *daily search quota*, not credits** — returns **HTTP 402** and founder discovery stops dead

## 4. SCORE — namesake guard

- **Namesake guard** (`rapidfuzz ≥ 88`): a contact is only pinned to a company if the profile's **experience** actually matches that company — stops "right name, wrong company"
- Confidence score per person → **green / amber / red**
- Claude used for extraction/judgment
- Registry data (when available) **overrides** aggregator data

## 5. EXPORT / PUSH

- `targets_hyperlinked.csv` (14-column deliverable) + `linkedin_review.csv`
- Google Sheets sync (needs `GOOGLE_SHEETS_KEY` — currently unset)
- **HubSpot:** Company (by domain) + Contact (by email) + Deal — pipeline **Scraped**, stage **Cold Call**, `scraped_type = ITservices`, owner+PoC = assigned caller
- In practice pushes run via `crm_mirror/enrich/push_itservices.py` (gives explicit owner/stage control + local-mirror dedup)

---

## Measured funnel (run of 2026-07-30)

| Stage | Count |
|---|---|
| Pages crawled | 140 |
| Raw listings | 5,456 |
| Unique companies | 5,369 |
| **Gate-passed (net-new)** | **1,121** |
| Excluded as already-known | 468 |
| Enriched (capped run) | 100 → 161 founders, 73 phones, 11 emails |
| **With a resolved founder** | **~91 (≈8% of gate-passed)** |

## Known gaps
1. **1 of 6 crawlers live** — Clutch (largest agency directory) is off; free coverage left on the table.
2. **Single-provider enrichment** — cascade is built for fallbacks but has none to fall back to.
3. **Founder identity is the constraint**, not company discovery. See `LEAD_SOURCING_PROBLEM_BRIEF.md`.
4. Email coverage for this segment is only **~15–30%**; phone is the reliable field.
