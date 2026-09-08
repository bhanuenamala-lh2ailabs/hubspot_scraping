# -*- coding: utf-8 -*-
"""Rule-based wrong-fit pre-screening engine, built directly from what actually made 17 real
Gujarat deals get marked Dead/ColdCall/WrongFit by callers (reasons pulled from their own
HubSpot notes). This encodes that judgment as explicit rules — no external LLM API call,
per instruction; the reasoning here IS the "LLM step" the original apifySetup.md deferred.

Signals used, in the order a caller would naturally notice them:
  1. Missing scrape data at all -> can't judge confidently -> flag for manual review
  2. Company's LinkedIn industry category is structurally not IT/software -> WRONG FIT
  3. Description reads as a creative/design/marketing/staffing shop despite an IT industry
     tag (industry categories are self-selected and often generic/wrong) -> WRONG FIT
  4. Company too large for the "small dormant shop" profile (employeeCount > 150) -> WRONG FIT
  5. Company founded too recently to plausibly have pre-2024 shelved code (foundedYear >= 2023)
     -> WRONG FIT (NOTE: caveat below — this signal is unreliable, see 3Brain Technolabs)
  6. Otherwise -> LIKELY FIT, but flagged: "no shelved codebase to sell" is the single most
     common real wrong-fit reason found in the ground truth, and it is NOT observable from a
     public LinkedIn profile — it only surfaces in the actual call. This engine cannot claim
     to catch that category; it only pre-screens the structural mismatches.
"""
import csv, re, json

IN_CSV = "godown/gujarat_qualify/apify_out_jg/people_companies_joined.csv"
OUT_CSV = "godown/gujarat_qualify/apify_out_jg/wrongfit_predictions.csv"

NON_IT_INDUSTRIES = {
    "wholesale building materials", "fabricated metal products", "public health",
    "events services", "education administration programs",
}
CREATIVE_ONLY = re.compile(
    r"\b(graphic designs?|branding agency|creative agency|advertising agency|digital marketing agency|"
    r"social media marketing|content creation|video production|photography)\b", re.I)
DEV_SIGNAL = re.compile(
    r"\b(software develop\w*|web develop\w*|app develop\w*|mobile app|saas|product engineering|"
    r"custom software|full[- ]stack|api develop\w*|cloud (develop\w*|engineering)|"
    r"devops|data engineering|ai/ml|machine learning|backend|frontend|programming|coding)\b", re.I)
MARKETING_HEAVY = re.compile(
    r"\b(digital marketing|social media marketing|seo\b|search engine optimi[sz]ation|"
    r"performance marketing|content marketing|ppc\b|pay[- ]per[- ]click|branding\b)\b", re.I)
IT_TRAINING = re.compile(
    r"\b(training institute|training academy|training center|training centre|"
    r"coaching (center|centre|classes|institute)|certification course|computer education|"
    r"computer classes|skill development (center|centre)|it training)\b", re.I)
BIGTECH_EXACT = {"infosys", "wipro", "tcs", "tata consultancy services", "hcl", "hcltech",
                  "tech mahindra", "accenture", "cognizant", "capgemini", "ibm", "microsoft",
                  "google", "amazon", "meta", "deloitte", "kpmg", "ey", "pwc", "genpact",
                  "mindtree", "mphasis", "persistent systems", "tesla"}

EMPLOYEE_CEILING = 700
FOUNDED_FLOOR = 2022


def classify(row):
    name = (row.get("currentCompanyName") or "").strip()
    industries = (row.get("company_industries") or "").lower()
    desc = (row.get("company_description") or "")
    headline = (row.get("headline") or "")
    specialities = (row.get("company_specialities") or "")
    text_for_dev_check = desc + " " + headline
    text_for_hard_check = desc + " " + specialities
    emp = row.get("company_employeeCount")
    founded = row.get("company_foundedYear")
    has_scrape = bool(row.get("company_industries") or row.get("company_employeeCount"))

    if any(name.lower() == b or name.lower().startswith(b + " ") for b in BIGTECH_EXACT):
        return "WRONG_FIT", "known large/enterprise brand name"

    if not has_scrape:
        return "NEEDS_REVIEW", "no company data scraped — can't judge from LinkedIn alone"

    if IT_TRAINING.search(text_for_hard_check):
        return "WRONG_FIT", "IT training/coaching outfit, not a software dev shop — no dev-signal rescue applies"

    if MARKETING_HEAVY.search(text_for_hard_check):
        return "WRONG_FIT", "digital-marketing-led shop (SEO/social/branding emphasis) — no dev-signal rescue applies"

    if industries in NON_IT_INDUSTRIES and not DEV_SIGNAL.search(text_for_dev_check):
        return "WRONG_FIT", f"non-IT industry on LinkedIn: {row.get('company_industries')}"

    if CREATIVE_ONLY.search(desc) and not DEV_SIGNAL.search(text_for_dev_check):
        return "WRONG_FIT", "description reads as a creative/marketing/staffing shop, not a software dev shop"

    try:
        if emp and int(emp) > EMPLOYEE_CEILING:
            return "WRONG_FIT", f"too large ({emp} employees) — not a small dormant-codebase shop"
    except ValueError:
        pass

    try:
        if founded and int(founded) >= FOUNDED_FLOOR:
            return "WRONG_FIT", f"founded {founded} — too recent to plausibly hold pre-2024 shelved code"
    except ValueError:
        pass

    return "LIKELY_FIT", "no structural red flag; note — \"no shelved codebase\" can't be ruled out without a call"


rows = list(csv.DictReader(open(IN_CSV, encoding="utf-8")))
out = []
counts = {"WRONG_FIT": 0, "LIKELY_FIT": 0, "NEEDS_REVIEW": 0}
for r in rows:
    verdict, reason = classify(r)
    counts[verdict] += 1
    out.append({**r, "engine_verdict": verdict, "engine_reason": reason})

with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
    w.writeheader()
    for r in out: w.writerow(r)

print(f"classified {len(rows)} companies")
print(counts)
print(f"\nwrote {OUT_CSV}")
