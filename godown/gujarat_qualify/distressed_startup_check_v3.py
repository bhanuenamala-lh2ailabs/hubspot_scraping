# -*- coding: utf-8 -*-
"""v3: incorporates real lessons from Lamiya's actual call notes (12 ground-truth cases, only
2 of which v1/v2 caught). Fixes applied:

  1. IT_SERVICES regex broadened to cover real phrasing v1/v2 missed: "development studio",
     "web/app development company" (not just "software development company"), "development
     solutions" + client-serving language ("cater to", "for businesses", "for clients").
  2. PRODUCT_RESCUE no longer fires on SaaS/platform/product words alone — a company saying
     "we build SaaS/products FOR clients/businesses/startups" is a services shop wearing
     product-company language (this is exactly what fooled v2 on Iqonic Design). Rescue now
     requires clear FIRST-PARTY ownership phrasing (our platform/product, we built/launched X,
     funding language) with no adjacent "for clients/businesses/startups/enterprises" framing.
  3. Company-identity cross-check: confirms the scraped company's own name actually matches the
     HubSpot deal's company name (core-normalized) before trusting the verdict — this is exactly
     what went wrong on Alpheric Inc, where the scraped record was actually NDIEM (an unrelated
     events-management institute), a LinkedIn currentPosition mismatch. Mismatches get their own
     verdict (COMPANY_MISMATCH) instead of a false STARTUP clearance.
  4. Name-based fallback for deals with zero scraped data (previously NEEDS_REVIEW with no
     verdict at all) — company/deal names containing strong services-y tokens (IT Solutions,
     InfoTech, Info Solutions, IT Brains, Web Solutions, Digital Solutions + Pvt Ltd/LLP) get a
     LOW_CONFIDENCE_IT_SERVICES flag instead of silently passing through unclassified.
"""
import json, re, os, csv

HUB = "/Users/bhanu/Desktop/hubspot"


def nurl(u): return (u or "").strip().lower().rstrip("/")
def fix(u):
    u = (u or "").strip()
    if u and not u.lower().startswith(("http://", "https://")): u = "https://" + u
    return u


CORP = re.compile(r"\b(pvt|private|limited|ltd|inc|llp|llc|co|company|technologies|technology|"
                   r"solutions|solution|softwares|software|systems|system|services|service|"
                   r"consulting|consultancy|infotech|labs|studio|studios|digital|group|india|the)\b", re.I)
def core(name):
    n = (name or "").lower(); n = re.sub(r"[^\w\s]", " ", n); n = CORP.sub(" ", n)
    return re.sub(r"\s+", " ", n).strip()


IT_SERVICES = re.compile(
    r"\b(it services|it outsourcing|staffing (solutions|services|agency)|"
    r"software development (company|services|outsourcing|studio)|"
    r"(web|app|mobile app) development (services|agency|company)|"
    r"digital marketing (agency|services)|consulting services|offshore development|"
    r"custom (software|tech) development (services|solutions)|it consulting|"
    r"managed services provider|body shopping|resource augmentation|staff augmentation|"
    r"development (solutions|studio) (for|to cater)|"
    r"(designed|built|developed) .{0,40}(websites|web-based applications|apps) for "
    r"(companies|clients|businesses)|proficiently deal with|streaming revenue with)\b", re.I)

# these phrases, if present near a product/SaaS word, mean the "product" is being built FOR
# someone else, not owned by the company — must NOT rescue in that case
CLIENT_SERVICE_FRAME = re.compile(
    r"\b(for (you|clients|businesses|startups|enterprises|organizations|users)|"
    r"we (build|deliver|create) .{0,30}for|partner with .{0,20}(startups|enterprises|businesses)|"
    r"cater to)\b", re.I)

PRODUCT_RESCUE = re.compile(
    r"\b(our platform|our app|our product|our own product|flagship product|proprietary|"
    r"patent(ed)?|we (built|build|created|launched) (our|the) |founded in \d{4} to build|"
    r"raised \$|seed round|series [a-c]\b|venture[- ]backed|self[- ]serve platform|"
    r"no[- ]code platform|^we are a startup|is a startup\b)\b", re.I | re.M)

NAME_SERVICES_HINT = re.compile(
    r"\b(it solutions|infotech|info solutions|it brains|web solutions|digital solutions|"
    r"info systems|infosystems|it services)\b", re.I)


def classify(dealname, li_desc, li_spec, website_text, has_any_scrape):
    blob = f"{li_desc} {' '.join(li_spec or [])} {website_text or ''}"

    if not has_any_scrape:
        if NAME_SERVICES_HINT.search(dealname or ""):
            return "LOW_CONFIDENCE_IT_SERVICES", "no company data scraped, but the deal/company name itself strongly suggests an IT-services shop"
        return "NEEDS_REVIEW", "no company data scraped and no name-based signal either"

    it_hit = IT_SERVICES.search(blob)
    if it_hit:
        # check if a rescue applies, but only count the rescue if it's NOT immediately framed
        # as client/for-hire work
        rescue_hit = PRODUCT_RESCUE.search(blob)
        if rescue_hit:
            window = blob[max(0, rescue_hit.start() - 60): rescue_hit.end() + 60]
            if CLIENT_SERVICE_FRAME.search(window):
                return "IT_SERVICES", f"services language ('{it_hit.group(0)}') present; nearby product-sounding phrase is framed as client work, no genuine rescue"
            return "STARTUP", f"services phrase present but genuine first-party product ownership language rescues it ('{rescue_hit.group(0)}')"
        return "IT_SERVICES", f"matched: '{it_hit.group(0)}'"

    return "STARTUP", "no IT-services red flag across LinkedIn+website text"


def main():
    scope = json.load(open("/tmp/distressed_final_scope.json"))
    people = json.load(open(os.path.join(HUB, "godown/gujarat_qualify/apify_out_distressed_check/people_raw.json")))
    companies = json.load(open(os.path.join(HUB, "godown/gujarat_qualify/apify_out_distressed_check/companies_raw.json")))
    crawl = json.load(open("/tmp/distressed2_website_crawl.json")) if os.path.exists("/tmp/distressed2_website_crawl.json") else []

    by_li = {nurl(p.get("linkedinUrl")): p for p in people}
    company_by_url = {nurl(c.get("linkedinUrl")): c for c in companies}
    site_by_url = {nurl(it.get("url")): it for it in crawl}

    rows = []
    for d in scope:
        li = nurl(d.get("LinkedIn URL"))
        p = by_li.get(li)
        li_desc = li_spec = website_text = ""
        scraped_company_name = ""
        has_scrape = False
        if p:
            cp = (p.get("currentPosition") or [{}])[0]
            exp0 = (p.get("experience") or [{}])[0]
            src = cp if cp.get("companyLinkedinUrl") else exp0
            cu = nurl(src.get("companyLinkedinUrl"))
            c = company_by_url.get(cu)
            if c:
                has_scrape = True
                scraped_company_name = c.get("name", "")
                li_desc = c.get("description") or ""
                li_spec = c.get("specialities") or []
                website_url = nurl(fix(c.get("website")))
                site = (site_by_url.get(website_url) or site_by_url.get(website_url.replace("https://", "http://")) or
                        site_by_url.get("https://www." + website_url.replace("https://", "").replace("http://", "")))
                if site:
                    website_text = (site.get("markdown") or "")[:3000]

        # identity check: does the scraped company actually match the HubSpot deal's company?
        mismatch = False
        if has_scrape:
            dn, sn = core(d.get("dealname")), core(scraped_company_name)
            dn_tokens, sn_tokens = set(dn.split()), set(sn.split())
            dn_sq, sn_sq = dn.replace(" ", ""), sn.replace(" ", "")  # whitespace-insensitive
            # e.g. "ExpertItBrains" vs "Expert IT Brains" — same name, different spacing/hyphens
            close_enough = (dn_sq == sn_sq or dn_sq in sn_sq or sn_sq in dn_sq)
            mismatch = bool(dn) and bool(sn) and not (dn in sn or sn in dn or (dn_tokens & sn_tokens) or close_enough)

        if mismatch:
            verdict, reason = "COMPANY_MISMATCH", (f"scraped company '{scraped_company_name}' doesn't match "
                                                     f"deal company '{d.get('dealname')}' — likely wrong "
                                                     f"currentPosition on the LinkedIn profile; needs a human look")
        else:
            verdict, reason = classify(d.get("dealname"), li_desc, li_spec, website_text, has_scrape)

        rows.append({**d, "verdict": verdict, "reason": reason, "scraped_company_name": scraped_company_name})

    counts = {}
    for r in rows: counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    print(f"classified {len(rows)} deals (Lamiya+Ishpreet, Cold Call, distressed_startups_salesnav2)")
    print(counts)

    json.dump(rows, open("/tmp/distressed_classification_v3.json", "w"), indent=1, ensure_ascii=False)

    flag_verdicts = {"IT_SERVICES", "LOW_CONFIDENCE_IT_SERVICES", "COMPANY_MISMATCH"}
    flagged = [r for r in rows if r["verdict"] in flag_verdicts]
    with open(os.path.join(HUB, "godown/gujarat_qualify/distressed_it_services_flagged_v3.csv"), "w",
              newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["deal_id", "dealname", "owner_id", "verdict", "scraped_company_name", "reason"])
        w.writeheader()
        for r in flagged: w.writerow({k: r.get(k, "") for k in w.fieldnames})
    print(f"\nwrote distressed_it_services_flagged_v3.csv: {len(flagged)} flagged")
    for r in flagged:
        print(f"  [{r['verdict']:<26}] {r['dealname']:<35} {r['reason'][:90]}")


main()
