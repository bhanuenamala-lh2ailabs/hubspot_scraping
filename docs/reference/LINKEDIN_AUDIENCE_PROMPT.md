# Prompt — LinkedIn Campaign Manager audience setup (IT-services / codebase acquisition)

Copy everything in the block below and give it to the Claude Chrome extension with LinkedIn
Campaign Manager open on the **Audience** section of the campaign.

---

```
You are setting up the AUDIENCE section of a LinkedIn Campaign Manager campaign for me.
Apply the targeting below exactly. If an option doesn't exist under that name, pick the
closest LinkedIn equivalent and tell me what you chose and why.

## CONTEXT — what this campaign is for
We are LH2 AI Labs. We buy dormant, pre-2024 software CODEBASES from Indian IT-services
firms (dev shops / software agencies) — written-off client projects, abandoned MVPs and
retired internal tools. We pay founders a fast liquidity event for IP they've already
written off. So the person we need to reach is the OWNER of the business — someone who can
decide to sell company IP. Not engineers, not HR, not marketing.

## 1. LOCATION
- Include: India (whole country).
- Use "Locations: Recent or permanent" if offered.
- If city-level targeting is available and you can add them without shrinking the audience
  below LinkedIn's minimum, prioritise: Mohali, Surat, Chennai, Indore, Gurgaon, Bengaluru,
  Mumbai, Ahmedabad, Kolkata, Coimbatore. (These converted best for us historically.)
  If adding cities pushes the audience under ~50,000, drop back to all-India.

## 2. LANGUAGE
- Profile language: English.

## 3. COMPANY INDUSTRY  (this is the core filter)
Include these industries:
- "IT Services and IT Consulting"
- "Software Development"
- "Computer and Network Security"  (only if it doesn't over-broaden)
Do NOT include: Staffing & Recruiting, BPO, Telecommunications, Financial Services,
Education. We want firms that BUILD software for clients, not resellers or staffing shops.

## 4. COMPANY SIZE  — this one matters a lot
Include ONLY these two bands:
- 201-500 employees
- 501-1,000 employees
(That is our 200-700 target band; LinkedIn has no exact 200-700 option, so these two bands
are the correct approximation. Do NOT include 51-200, and do NOT include 1,001+.)

Reason: firms under ~200 usually have no dormant codebase worth buying, and firms over
~1,000 are large outsourcers with legal/IP processes that make a quick sale impossible.

## 5. JOB TITLES / SENIORITY  — who we actually want
Target the business owner / final decision maker. Use Job Title targeting with these
(add both spellings where LinkedIn splits them):
- Founder
- Co-Founder / Cofounder
- CEO / Chief Executive Officer
- Managing Director
- Owner
- Proprietor
- Chairman
- President
- Director  (only if it doesn't blow up the audience — in India "Director" often means
  a company director/owner, which is who we want)

Also set Job Seniority to: Owner/Partner, CXO, Vice President, Director.

If Job Function targeting is needed as well, use: Business Development, Entrepreneurship,
Operations, Engineering — but title + seniority should carry most of the targeting.

DO NOT target: Human Resources, Sales reps, Marketing, Support, Interns, Students,
individual contributors.

## 6. EXCLUSIONS  — important
Exclude these companies by name (large outsourcers — never our targets):
TCS, Tata Consultancy Services, Infosys, Wipro, HCL, HCLTech, Cognizant, Capgemini,
Accenture, Tech Mahindra, LTIMindtree, Mindtree, Mphasis, Coforge, Persistent Systems,
Hexaware, Zensar, Cyient, Birlasoft, Nagarro, Happiest Minds, IBM, L&T Technology Services.

Also exclude, if the option exists: current employees of my own company, and any matched
audience/contact list I have already uploaded (so we don't pay to re-touch people we've
already contacted).

## 7. SETTINGS THAT MUST BE TURNED OFF
- **Enable Audience Expansion — turn this OFF.** It shows ads to lookalikes outside my
  targeting and dilutes a precise audience. This is not optional.
- **LinkedIn Audience Network — turn OFF** (keep delivery on LinkedIn itself so the
  targeting holds).

## 8. AFTER YOU'RE DONE
Report back with:
1. Every filter you set, exactly as it appears in the UI.
2. The forecasted audience size LinkedIn shows.
3. Anything I asked for that LinkedIn does not support, and what you used instead.
4. Flag it clearly if the forecast is under 50,000 — at that size a Message/Conversation ad
   will barely deliver, and I should switch to a Single Image / Document ad format instead.
```

---

## Notes for you (not part of the prompt)

- **LinkedIn has no "founded year" filter.** Our scrape gate uses *founded ≤ 2022*; that
  cannot be reproduced in Campaign Manager. Company size is the closest proxy.
- **Company size on LinkedIn is self-reported** and is the same field that misled us in the
  scrape (GoodFirms had firms labelled 50-249 that were really 1-26 people). Expect some slop.
- **Audience Expansion off** is the single most important setting — it was the main thing
  diluting the earlier campaign.
- If the forecast comes back small, widen by dropping the city list before you touch the
  size bands or the titles — location is the cheapest constraint to relax.
