# Research brief: find more Indian IT-association member directories to scrape

## What we are doing and why

LH2 AI Labs acquires **dormant software codebases** from small and mid-sized Indian IT-services
companies — firms that built custom software for clients years ago, retained the IP, and no longer
maintain or monetise it. We buy that code.

To find these firms we need **large, public lists of Indian software/IT companies with their
websites**. Company websites matter more than anything else: our qualification pipeline crawls each
site for evidence the firm (a) owns IP rather than just staffing out developers, (b) has pre-2024
code, and (c) shows real engineering signals (GitHub/GitLab references, code-review or CI/CD
mentions in job ads).

We have already mined GoodFirms and NASSCOM. On 18 Aug 2026 we scraped four regional IT-industry
associations, which produced **672 genuinely new companies** after deduplication. We want more
sources of exactly that kind, covering the whole of India.

## What we just scraped (do NOT return these — already done)

| Association | Region | URL | Members scraped | New after dedup |
|---|---|---|---|---|
| GESIA | Gujarat | gesia.org/members-directory | 139 | 94 |
| HYSEA | Hyderabad / Telangana | hysea.in/existing-members/ | 822 | 254 |
| GTech | Kerala | gtechindia.org/members | 228 | 152 |
| iTAAP | Andhra Pradesh | theitaap.org/members/member-directory/ | 214 | 174 |
| **Total** | | | **1,403** | **672** |

Also already mined: **NASSCOM** member list, **GoodFirms** India listings. Roughly 26% of the
association members overlapped with what we already held, so these sources are genuinely additive.

## What we want from you

A list of **additional public member directories / company listings of Indian software and IT
companies**, with, for each one:

1. **Exact URL** of the directory page
2. **Region / state** it covers
3. **Approximate number of member companies**
4. **Whether member company websites are listed** (critical — see below)
5. **How the data loads**: plain HTML, paginated HTML, JavaScript-rendered, or backed by an API.
   If you can see an API endpoint or pagination pattern, include it.
6. **Any access barrier**: login, CAPTCHA, token/challenge handshake, aggressive rate limiting

Prioritise **state and city IT associations, software technology parks, and industry bodies** —
these are the closest analogues to what worked. Regions we have not covered at all include:
Karnataka/Bengaluru, Maharashtra/Pune/Mumbai, Tamil Nadu/Chennai/Coimbatore, Delhi NCR/Noida/Gurugram,
West Bengal/Kolkata, Rajasthan/Jaipur, Madhya Pradesh/Indore, Punjab/Mohali, Odisha/Bhubaneswar,
Uttar Pradesh/Lucknow, and the STPI (Software Technology Parks of India) regional units.

## What makes a source GOOD (the pattern that worked)

- Members are **independent small/mid Indian IT-services or software product companies**, roughly
  **10–250 employees**
- The directory **lists each member's own website URL** — this is the single most important field
- Public, no login
- Ideally a few hundred members or more

## What makes a source BAD (concrete counter-example)

We probed **DSCI** (dsci.in/corporate-member/member-directory) and rejected it. It is a useful
illustration of what not to send back:

- Its members are **large enterprises, banks and global capability centres** — Accenture, Adobe,
  HSBC, Airtel Payments Bank, Aditya Birla, Agratas Energy. Its own sector taxonomy includes
  BFSI, GCC-BFSI, GCC-Digital, GCC-Manufacturing, Pharmaceuticals, Aviation, Oil Energy & Power.
  Captives and enterprises are explicitly **not** our target — they do not sell dormant IP.
- It lists only **company name, sector and city — no website**, so every row would need domain
  resolution afterwards.
- It is **deliberately anti-automation**: the directory API returns 401 and requires a Bearer token
  obtained through a `challenge_id`/`solution` exchange.

So please exclude: enterprise/CIO bodies, GCC associations, BFSI or pharma industry groups,
chambers of commerce with mixed membership, and any directory without company websites.

## Also useful, lower priority

- Regional **software technology park** tenant/company lists (STPI units, Technopark, Infopark,
  Cyberpark, Hinjawadi/Rajiv Gandhi Infotech Park, HITEC City)
- **State IT department** registered-company lists or IT-policy beneficiary lists
- Startup ecosystem directories filtered to IT services (not funded product startups — we want
  services firms that built client software and kept the IP)

## Output format we would like

A simple table or CSV: `association_name, region, directory_url, approx_members, websites_listed
(yes/no), data_loading (html/paginated/js/api), access_barrier, notes`.

Volume matters — twenty usable directories at 200 members each is worth far more to us than a
perfect analysis of one.
