# -*- coding: utf-8 -*-
"""Option B: combines the LinkedIn company data (already scraped) with each company's own
website homepage text (freshly crawled) for a richer IT-services-vs-startup classification.
Same rule logic as the corrected v1 (judge on prose, never on LinkedIn's noisy industry-tag
dropdown), but now also reads the company's own "About/Home" copy, which resolves a lot of the
v1 NEEDS_REVIEW cases and gives more confidence on borderline ones.
"""
import json, re, csv, os

IT_SERVICES = re.compile(
    r"\b(it services|it outsourcing|staffing (solutions|services|agency)|"
    r"software development (company|services|outsourcing)|web development (services|agency)|"
    r"digital marketing (agency|services)|consulting services|offshore development|"
    r"custom software development services|it consulting|managed services provider|"
    r"body shopping|resource augmentation|staff augmentation|we (build|develop) (websites|apps|"
    r"software) for (our )?clients|hire (developers|our team)|outsource your)\b", re.I)

PRODUCT_RESCUE = re.compile(
    r"\b(our platform|our app|our product|proprietary|patent(ed)?|saas\b|we (built|build|created|"
    r"launched)|founded in \d{4} to build|raised \$|seed round|series [a-c]\b|venture[- ]backed|"
    r"self[- ]serve platform|no[- ]code platform|startup\b|our own product|flagship product)\b", re.I)


def nurl(u): return (u or "").strip().lower().rstrip("/")
def fix(u):
    u = (u or "").strip()
    if u and not u.lower().startswith(("http://", "https://")): u = "https://" + u
    return u


crawl = json.load(open("/tmp/distressed2_website_crawl.json"))
by_url = {}
for it in crawl:
    for variant in (nurl(it.get("url")),):
        by_url[variant] = it

targets = json.load(open("/tmp/distressed2_website_targets.json"))

rows = []
for t in targets:
    website_url = nurl(fix(t.get("website")))
    site = (by_url.get(website_url) or by_url.get(website_url.replace("https://", "http://")) or
            by_url.get("https://www." + website_url.replace("https://", "").replace("http://", "")))
    site_text = (site.get("markdown") or "")[:3000] if site else ""

    li_text = t.get("li_description", "") + " " + " ".join(t.get("li_specialities") or [])
    blob = f"{li_text} {site_text}"

    if not blob.strip():
        verdict, reason = "NEEDS_REVIEW", "no LinkedIn text and no website content"
    elif IT_SERVICES.search(blob) and not PRODUCT_RESCUE.search(blob):
        verdict, reason = "IT_SERVICES", "reads as outsourcing/dev-services/staffing across LinkedIn+website, no product rescue"
    else:
        verdict, reason = "STARTUP", "no IT-services red flag across LinkedIn+website text"

    rows.append({**t, "verdict": verdict, "reason": reason, "had_website_text": bool(site_text)})

counts = {}
for r in rows:
    counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
print("classified:", len(rows))
print(counts)
print(f"had website text: {sum(1 for r in rows if r['had_website_text'])}/{len(rows)}")

json.dump(rows, open("/tmp/distressed2_classification_v2.json", "w"), indent=1, ensure_ascii=False)

it_rows = [r for r in rows if r["verdict"] == "IT_SERVICES"]
with open("godown/gujarat_qualify/distressed_it_services_flagged_v2.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["deal_id", "dealname", "owner_id", "company_name", "website", "reason"])
    w.writeheader()
    for r in it_rows:
        w.writerow({k: r.get(k, "") for k in w.fieldnames})
print(f"\nwrote distressed_it_services_flagged_v2.csv: {len(it_rows)} flagged")
