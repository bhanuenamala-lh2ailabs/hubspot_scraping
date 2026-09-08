# -*- coding: utf-8 -*-
"""Final re-pass: the actual goal isn't just "not an IT-services shop" — it's "does this company
plausibly have real product-development artifacts (PRD, Jira/sprints, a roadmap, an in-house
engineering team shipping their own software) worth acquiring." That's a higher bar than the
earlier STARTUP/IT_SERVICES split, and it also catches genuine non-tech businesses (HR
consultancies, logistics, hospitality, events) that slipped through as "STARTUP" only because
they never tripped the IT-services wording — they were never a software company to begin with.

KEEP requires an actual technology/software signal (product, platform, app, SaaS, engineering,
AI/ML, API, dashboard, algorithm, tech stack) AND no IT-services/agency framing.
REMOVE covers: confirmed IT-services/agency, confirmed non-tech industry, or no usable
data/signal at all (can't be confident it holds a real codebase without any evidence).
"""
import json, re, os, csv

def nurl(u): return (u or "").strip().lower().rstrip("/")
def fix(u):
    u = (u or "").strip()
    if u and not u.lower().startswith(("http://", "https://")): u = "https://" + u
    return u

IT_SERVICES = re.compile(
    r"\b(it services|it outsourcing|staffing (solutions|services|agency)|"
    r"software development (company|services|outsourcing|studio)|"
    r"(web|app|mobile app) development (services|agency|company)|"
    r"digital marketing (agency|services)|consulting services|offshore development|"
    r"custom (software|tech) development (services|solutions)|it consulting|"
    r"managed services provider|body shopping|resource augmentation|staff augmentation|"
    r"development (solutions|studio) (for|to cater)|"
    r"(designed|built|developed) .{0,40}(websites|web-based applications|apps) for "
    r"(companies|clients|businesses)|proficiently deal with|streaming revenue with|"
    r"product[- ]first.{0,60}(team|partner)|full product & saas builds|"
    r"we build .{0,40}for (every|founders?|startups?|enterprises?)|"
    r"your product\.? your code|deal with the web and mobile app development)\b", re.I)

NON_TECH_INDUSTRY = re.compile(
    r"\b(trucking|logistics services|freight|hospitality group|restaurant chain|"
    r"m\.?i\.?c\.?e\.? management|tourism|travel agency|event management|events management|"
    r"people manager development|management consulting|hr consultancy|talent platform|"
    r"staffing agency|recruitment (agency|firm)|coaching institute|wellness clinic|"
    r"real estate (developer|agency)|manufacturing company|educational institution|"
    r"insurance broker|import export|construction company)\b", re.I)

TECH_SIGNAL = re.compile(
    r"\b(software|platform|saas\b|\bapp\b|application|api\b|dashboard|algorithm|"
    r"artificial intelligence|machine learning|\bai\b|\bml\b|engineering team|tech stack|"
    r"product roadmap|codebase|automation|data pipeline|cloud[- ]native|backend|frontend|"
    r"full[- ]stack|devops|infrastructure|mobile app|web app|digital product|"
    r"technology platform)\b", re.I)

# real, if rare, explicit process signals — strongest possible positive evidence
PROCESS_SIGNAL = re.compile(r"\b(jira|scrum|sprint|prd\b|product requirements|agile|"
                             r"product manager|product roadmap|backlog|changelog|release notes)\b", re.I)

NAME_SERVICES_HINT = re.compile(
    r"\b(it solutions|infotech|info solutions|it brains|web solutions|digital solutions|"
    r"info systems|infosystems|it services)\b", re.I)
NAME_NONTECH_HINT = re.compile(
    r"\b(trucking|logistics|hospitality|entertainment|events?|tourism|travel|"
    r"foundation|institute|consultancy|staffing)\b", re.I)


def classify(dealname, blob, has_any_scrape):
    if not has_any_scrape:
        if NAME_SERVICES_HINT.search(dealname or ""):
            return "REMOVE", "no data scraped; name strongly suggests an IT-services shop"
        if NAME_NONTECH_HINT.search(dealname or ""):
            return "REMOVE", "no data scraped; name suggests a non-tech business (trucking/hospitality/events/consultancy)"
        return "REMOVE", "no company data scraped anywhere and no name-based signal — can't confirm a real codebase exists"

    if IT_SERVICES.search(blob):
        return "REMOVE", f"IT-services/agency framing: '{IT_SERVICES.search(blob).group(0)}'"
    if NON_TECH_INDUSTRY.search(blob):
        return "REMOVE", f"non-tech industry: '{NON_TECH_INDUSTRY.search(blob).group(0)}'"
    if PROCESS_SIGNAL.search(blob):
        return "KEEP", f"explicit product-process signal: '{PROCESS_SIGNAL.search(blob).group(0)}'"
    if TECH_SIGNAL.search(blob):
        return "KEEP", f"genuine tech/product company signal: '{TECH_SIGNAL.search(blob).group(0)}'"
    return "REMOVE", "no tech/product signal anywhere in scraped text — can't confirm this is a software company at all"


def main():
    scope = json.load(open("/tmp/distressed_final_scope.json"))
    people = json.load(open("godown/gujarat_qualify/apify_out_distressed_check/people_raw.json"))
    companies = json.load(open("godown/gujarat_qualify/apify_out_distressed_check/companies_raw.json"))
    crawl1 = json.load(open("/tmp/distressed2_website_crawl.json"))
    crawl2 = json.load(open("/tmp/distressed_resolved_crawl.json"))
    resolved_good = json.load(open("/tmp/distressed_resolved_good.json"))
    v3 = json.load(open("/tmp/distressed_classification_v3.json"))

    by_li = {nurl(p.get("linkedinUrl")): p for p in people}
    company_by_url = {nurl(c.get("linkedinUrl")): c for c in companies}
    site_by_url = {}
    for it in crawl1 + crawl2:
        site_by_url[nurl(it.get("url"))] = it
    v3_by_deal = {r["deal_id"]: r for r in v3}
    resolved_by_dealname = {g["dealname"]: g for g in resolved_good}

    rows = []
    for d in scope:
        v3r = v3_by_deal.get(d["deal_id"], {})
        li_desc = li_spec = website_text = ""
        has_scrape = False

        if v3r.get("verdict") not in ("COMPANY_MISMATCH", "NEEDS_REVIEW"):
            li = nurl(d.get("LinkedIn URL"))
            p = by_li.get(li)
            if p:
                cp = (p.get("currentPosition") or [{}])[0]
                exp0 = (p.get("experience") or [{}])[0]
                src = cp if cp.get("companyLinkedinUrl") else exp0
                cu = nurl(src.get("companyLinkedinUrl"))
                c = company_by_url.get(cu)
                if c:
                    has_scrape = True
                    li_desc = c.get("description") or ""
                    li_spec = c.get("specialities") or []
                    wu = nurl(fix(c.get("website")))
                    site = site_by_url.get(wu) or site_by_url.get(wu.replace("https://", "http://"))
                    if site: website_text = (site.get("markdown") or "")[:3000]
        else:
            g = resolved_by_dealname.get(d["dealname"])
            if g:
                has_scrape = True
                li_desc = g.get("description") or ""
                li_spec = g.get("specialities") or []
                wu = nurl(fix(g.get("website")))
                site = site_by_url.get(wu) or site_by_url.get(wu.replace("https://", "http://"))
                if site: website_text = (site.get("markdown") or "")[:3000]

        blob = f"{li_desc} {' '.join(li_spec or [])} {website_text}"
        verdict, reason = classify(d.get("dealname"), blob, has_scrape)
        rows.append({**d, "verdict": verdict, "reason": reason})

    counts = {}
    for r in rows: counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    print(f"classified {len(rows)} deals")
    print(counts)
    json.dump(rows, open("/tmp/distressed_product_signal_final.json", "w"), indent=1, ensure_ascii=False)

    remove_rows = [r for r in rows if r["verdict"] == "REMOVE"]
    with open("godown/gujarat_qualify/distressed_to_remove_final.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["deal_id", "dealname", "owner_id", "reason"])
        w.writeheader()
        for r in remove_rows: w.writerow({k: r.get(k, "") for k in w.fieldnames})
    print(f"\nwrote distressed_to_remove_final.csv: {len(remove_rows)} to remove")


main()
