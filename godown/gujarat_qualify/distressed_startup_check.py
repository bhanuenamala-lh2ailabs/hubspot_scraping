# -*- coding: utf-8 -*-
"""Classifies today's distressed-startups Cold Call deals (Lamiya/Ishpreet) as STARTUP vs
IT_SERVICES using real scraped LinkedIn company data. Goal was genuine startups; an IT-services/
outsourcing/staffing shop that works FOR clients (no owned product) doesn't fit and gets flagged.

IT_SERVICES signal: "IT services", "outsourcing", "staffing", "software development company"/
"services", "consulting services", "web development services", "digital marketing agency" — with
NO product-ownership language rescuing it (own platform/app/SaaS/proprietary product wording).
STARTUP signal (rescue / default): proprietary/own product, platform, SaaS, app, funding/venture
language, "we built", "our platform".
"""
import json, re, csv, os

OUT_DIR = "godown/gujarat_qualify/apify_out_distressed_check"
people = json.load(open(os.path.join(OUT_DIR, "people_raw.json")))
companies = json.load(open(os.path.join(OUT_DIR, "companies_raw.json")))
deals = json.load(open("/tmp/distressed2_coldcall_deals.json"))


def nurl(u): return (u or "").strip().lower().rstrip("/")


# map deal -> person (by LinkedIn URL)
by_li = {nurl(p.get("linkedinUrl")): p for p in people}
company_by_url = {nurl(c.get("linkedinUrl")): c for c in companies}

IT_SERVICES = re.compile(
    r"\b(it services|it outsourcing|staffing (solutions|services|agency)|"
    r"software development (company|services|outsourcing)|web development (services|agency)|"
    r"digital marketing (agency|services)|consulting services|offshore development|"
    r"custom software development services|it consulting|managed services provider|"
    r"body shopping|resource augmentation|staff augmentation)\b", re.I)

PRODUCT_RESCUE = re.compile(
    r"\b(our platform|our app|our product|proprietary|patent(ed)?|saas\b|we (built|build|created|"
    r"launched)|founded in \d{4} to build|raised \$|seed round|series [a-c]\b|venture[- ]backed|"
    r"self[- ]serve platform|no[- ]code platform)\b", re.I)

rows = []
for d in deals:
    li = nurl(d.get("LinkedIn URL"))
    p = by_li.get(li)
    if not p:
        rows.append({**d, "verdict": "NEEDS_REVIEW", "reason": "profile not scraped", "company_name": ""})
        continue
    cp = (p.get("currentPosition") or [{}])[0]
    exp0 = (p.get("experience") or [{}])[0]
    src = cp if cp.get("companyLinkedinUrl") else exp0
    cu = nurl(src.get("companyLinkedinUrl"))
    c = company_by_url.get(cu)
    if not c:
        rows.append({**d, "verdict": "NEEDS_REVIEW", "reason": "company not scraped",
                     "company_name": src.get("companyName", "")})
        continue
    desc = c.get("description") or ""
    tagline = c.get("tagline") or ""
    specialities = " ".join(c.get("specialities") or []) if isinstance(c.get("specialities"), list) else (c.get("specialities") or "")
    # deliberately EXCLUDES the LinkedIn "industries" category tag: it's a generic self-selected
    # dropdown ("IT Services and IT Consulting" is the closest option many genuine AI/SaaS
    # startups pick since LinkedIn's taxonomy has no better fit) — using it as a hard signal
    # produced false positives on real product startups (Opsight AI, Quantian, Castler, etc.
    # all tagged "IT Services and IT Consulting" while literally describing themselves as a
    # "Startup" / "AI products company" / "Platform" in their own words).
    blob = f"{desc} {tagline} {specialities}"

    if IT_SERVICES.search(blob) and not PRODUCT_RESCUE.search(blob):
        verdict, reason = "IT_SERVICES", "reads as an outsourcing/dev-services/staffing shop, no owned-product rescue"
    elif IT_SERVICES.search(blob) and PRODUCT_RESCUE.search(blob):
        verdict, reason = "STARTUP", "IT-services language present but product-ownership signal rescues it"
    elif not blob.strip():
        verdict, reason = "NEEDS_REVIEW", "no description/tagline/specialities scraped"
    else:
        verdict, reason = "STARTUP", "no IT-services red flag"

    rows.append({**d, "verdict": verdict, "reason": reason, "company_name": c.get("name", ""),
                 "description": desc[:300]})

with open("/tmp/distressed2_classification.json", "w") as f:
    json.dump(rows, f, indent=1, ensure_ascii=False)

counts = {}
for r in rows:
    counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
print("classified:", len(rows))
print(counts)

it_rows = [r for r in rows if r["verdict"] == "IT_SERVICES"]
with open("godown/gujarat_qualify/distressed_it_services_flagged.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["deal_id", "dealname", "owner_id", "company_name", "reason", "description"])
    w.writeheader()
    for r in it_rows:
        w.writerow({k: r.get(k, "") for k in w.fieldnames})
print(f"\nwrote godown/gujarat_qualify/distressed_it_services_flagged.csv: {len(it_rows)} flagged")
