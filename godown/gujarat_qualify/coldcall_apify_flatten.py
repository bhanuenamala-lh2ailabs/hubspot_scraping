# -*- coding: utf-8 -*-
"""Flatten the NASSCOM/Founder Search validation-set Apify raw JSON into clean CSVs, joined by
company LinkedIn URL, plus a failed_urls.csv for anything that didn't come through.
"""
import json, csv, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "apify_out_coldcall")

people = json.load(open(os.path.join(OUT, "people_raw.json")))
companies = json.load(open(os.path.join(OUT, "companies_raw.json")))
input_company_urls = json.load(open("/tmp/coldcall_company_urls.json"))
input_people = json.load(open("/tmp/coldcall_deal_linkedins.json"))


def nurl(u):
    return (u or "").strip().lower().rstrip("/")


# ---------------------------------------------------------------- people CSV
people_rows = []
for p in people:
    cp = (p.get("currentPosition") or [{}])[0]
    exp0 = (p.get("experience") or [{}])[0]
    src = cp if cp.get("companyLinkedinUrl") else exp0
    people_rows.append({
        "firstName": p.get("firstName"), "lastName": p.get("lastName"),
        "linkedinUrl": p.get("linkedinUrl"), "headline": p.get("headline"),
        "location": (p.get("location") or {}).get("parsed", {}).get("text") if isinstance(p.get("location"), dict) else p.get("location"),
        "currentTitle": src.get("position"), "currentCompanyName": src.get("companyName"),
        "currentCompanyLinkedinUrl": src.get("companyLinkedinUrl"),
        "tenureAtCurrentRole": src.get("duration"),
        "topSkills": ", ".join(p.get("topSkills") or [])[:300],
        "experience_json": json.dumps(p.get("experience") or [], ensure_ascii=False),
    })

with open(os.path.join(OUT, "people_scraped.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(people_rows[0].keys()))
    w.writeheader()
    for r in people_rows: w.writerow(r)
print(f"wrote people_scraped.csv: {len(people_rows)} rows")

# ---------------------------------------------------------------- companies CSV
company_rows = []
for c in companies:
    hq = next((l for l in (c.get("locations") or []) if l.get("headquarter")), (c.get("locations") or [{}])[0] if c.get("locations") else {})
    company_rows.append({
        "name": c.get("name"), "linkedinUrl": c.get("linkedinUrl"), "website": c.get("website"),
        "tagline": c.get("tagline"), "description": (c.get("description") or "").replace("\n", " ")[:500],
        "foundedYear": (c.get("foundedOn") or {}).get("year"),
        "employeeCount": c.get("employeeCount"),
        "employeeCountRange": f"{(c.get('employeeCountRange') or {}).get('start','')}-{(c.get('employeeCountRange') or {}).get('end','')}",
        "followerCount": c.get("followerCount"),
        "companyType": c.get("companyType"),
        "industries": ", ".join(i.get("name","") for i in (c.get("industries") or [])),
        "specialities": ", ".join(c.get("specialities") or []),
        "hqCity": hq.get("city"), "hqCountry": (hq.get("parsed") or {}).get("country") or hq.get("country"),
    })

with open(os.path.join(OUT, "companies_scraped.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(company_rows[0].keys()))
    w.writeheader()
    for r in company_rows: w.writerow(r)
print(f"wrote companies_scraped.csv: {len(company_rows)} rows")

# ---------------------------------------------------------------- join
company_by_url = {nurl(c["linkedinUrl"]): c for c in company_rows}
joined_rows = []
for pr in people_rows:
    cu = nurl(pr.get("currentCompanyLinkedinUrl"))
    cdata = company_by_url.get(cu, {})
    joined = dict(pr)
    for k in ("employeeCount", "foundedYear", "industries", "companyType", "website",
              "hqCity", "hqCountry", "description", "specialities", "followerCount"):
        joined[f"company_{k}"] = cdata.get(k, "")
    joined_rows.append(joined)

with open(os.path.join(OUT, "people_companies_joined.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(joined_rows[0].keys()))
    w.writeheader()
    for r in joined_rows: w.writerow(r)
print(f"wrote people_companies_joined.csv: {len(joined_rows)} rows")

# ---------------------------------------------------------------- failed URLs
scraped_people_urls = set(nurl(p.get("linkedinUrl")) for p in people)
failed_people = [r for r in input_people if r.get("linkedin_url") and nurl(r.get("linkedin_url")) not in scraped_people_urls]
scraped_company_urls = set(nurl(c.get("linkedinUrl")) for c in companies)
failed_companies = [u for u in input_company_urls if nurl(u) not in scraped_company_urls]

with open(os.path.join(OUT, "failed_urls.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["type", "url", "name_or_company"])
    for r in failed_people:
        w.writerow(["person", r.get("linkedin_url"), r.get("dealname")])
    for u in failed_companies:
        w.writerow(["company", u, ""])
print(f"wrote failed_urls.csv: {len(failed_people)} people + {len(failed_companies)} companies failed")

no_founded = sum(1 for c in company_rows if not c["foundedYear"])
no_employees = sum(1 for c in company_rows if not c["employeeCount"])
print(f"\ndata quality: {no_founded}/{len(company_rows)} missing foundedYear, "
      f"{no_employees}/{len(company_rows)} missing employeeCount")
