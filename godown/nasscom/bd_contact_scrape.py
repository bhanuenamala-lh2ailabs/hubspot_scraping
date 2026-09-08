# -*- coding: utf-8 -*-
"""Scrape phone numbers and emails off the Bangladesh firms' own contact pages.

Why this is worth doing rather than waiting for SignalHire: the rule for this batch is that ANY
dialable number qualifies, and Bangladeshi software firms publish a company mainline on a
/contact page far more consistently than Indian firms do. A number we can read for free today
beats a search we cannot spend until the quota resets.

What it collects, in preference order:
  1. tel: hrefs          — unambiguous, the site itself marked it as a phone
  2. +880 / 01XXXXXXXXX patterns in the contact page text
  3. any other international-looking number (some firms list a US or UK sales line)
  4. mailto: and inline emails, with role addresses (info@, sales@) ranked below personal ones

Numbers are labelled, not filtered: bangladesh_number.py says whether something is a valid BD
mobile, but a landline or a foreign line is still recorded because the caller can use it. The
label is what lets a human decide, rather than the scraper deciding silently.

Usage: python3 bd_contact_scrape.py [--src bangladesh_top100.csv] [--workers 10]
"""
import os, re, sys, csv, json, time, html, collections, urllib.request
import concurrent.futures as cf

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HUB, "crm_mirror", "enrich"))
from bangladesh_number import to_e164 as bd_e164, classify as bd_class

SRC = os.path.join(HERE, "bangladesh_top100.csv")
OUT = os.path.join(HERE, "bd_contacts.json")
WORKERS = 10
for i, a in enumerate(sys.argv):
    if a == "--src": SRC = os.path.join(HERE, sys.argv[i+1])
    if a == "--out": OUT = os.path.join(HERE, sys.argv[i+1])
    if a == "--workers": WORKERS = int(sys.argv[i+1])

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
PAGES = ["/contact", "/contact-us", "/contacts", "/get-in-touch", "/reach-us", "/about-us", ""]
TEL = re.compile(r'href=["\']tel:([+0-9().\-\s]{7,25})["\']', re.I)
MAILTO = re.compile(r'href=["\']mailto:([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})', re.I)
BD = re.compile(r'(?:\+?880[\s\-]?|\b0)1[3-9]\d{2}[\s\-]?\d{6}\b')
INTL = re.compile(r'\+\d{1,3}[\s\-]?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,6}')
EMAIL = re.compile(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b')
ROLE = re.compile(r'^(info|sales|contact|hello|support|admin|career|hr|marketing|enquiry|inquiry)@', re.I)
JUNK = re.compile(r'(example|sentry|wixpress|godaddy|\.png|\.jpg|@2x|domain\.com)', re.I)


def get(u, t=12):
    r = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    with urllib.request.urlopen(r, timeout=t) as x:
        ct = (x.headers.get("Content-Type") or "").lower()
        if "html" not in ct and "text" not in ct: raise ValueError("not html")
        return x.read(600_000).decode(x.headers.get_content_charset() or "utf-8", "replace")


def text_of(h):
    h = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h)))


def one(row):
    site = (row.get("website") or "").strip()
    if not site.startswith("http"): site = "http://" + site
    m = re.match(r"(https?://[^/]+)", site)
    root = m.group(1) if m else site
    rec = {"name": row["name"], "domain": row.get("domain", ""), "pages": [],
           "phones": [], "emails": []}
    raw_ph, raw_em = [], []
    for p in PAGES:
        u = root + p if p else site
        try:
            h = get(u)
        except Exception:
            continue
        rec["pages"].append(u)
        t = text_of(h)
        raw_ph += [x.strip() for x in TEL.findall(h)]
        raw_ph += BD.findall(t)
        raw_ph += INTL.findall(t)
        raw_em += MAILTO.findall(h) + EMAIL.findall(t)
        if raw_ph and raw_em: break        # contact page had both; no need to keep fetching
        time.sleep(0.1)
    seen = set()
    for p in raw_ph:
        d = re.sub(r"[^\d+]", "", p)
        if len(re.sub(r"\D", "", d)) < 9: continue
        if d in seen: continue
        seen.add(d)
        bd = bd_e164(d)
        rec["phones"].append({"raw": p.strip()[:26], "e164": bd or d,
                              "kind": bd_class(bd) if bd else "other/landline",
                              "is_bd_mobile": bool(bd)})
        if len(rec["phones"]) >= 4: break
    se = set()
    for em in raw_em:
        em = em.lower().strip(".")
        if em in se or JUNK.search(em): continue
        se.add(em)
        rec["emails"].append({"email": em, "role_address": bool(ROLE.match(em))})
        if len(rec["emails"]) >= 4: break
    # personal addresses first — they reach a human, role inboxes reach a queue
    rec["emails"].sort(key=lambda e: e["role_address"])
    rec["phones"].sort(key=lambda p: not p["is_bd_mobile"])
    return rec


def main():
    rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
    print(f"scraping contact details for {len(rows)} Bangladesh firms...", flush=True)
    out, t0 = [], time.time()
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for i, r in enumerate(ex.map(one, rows), 1):
            out.append(r)
            if i % 25 == 0: print(f"   {i}/{len(rows)}  {time.time()-t0:.0f}s", flush=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    wph = [r for r in out if r["phones"]]
    bdm = [r for r in out if any(p["is_bd_mobile"] for p in r["phones"])]
    wem = [r for r in out if r["emails"]]
    per = [r for r in out if any(not e["role_address"] for e in r["emails"])]
    print(f"\ndone in {time.time()-t0:.0f}s -> {os.path.basename(OUT)}")
    print(f"firms with ANY phone      : {len(wph)}/{len(out)}  ({len(wph)/len(out)*100:.0f}%)")
    print(f"   ...a real BD MOBILE    : {len(bdm)}")
    print(f"   ...landline/other only : {len(wph)-len(bdm)}")
    print(f"firms with an email       : {len(wem)}")
    print(f"   ...non-role (a person) : {len(per)}")
    print("\nsample:")
    for r in wph[:12]:
        p = r["phones"][0]
        em = r["emails"][0]["email"] if r["emails"] else "-"
        print(f"   {r['name'][:30]:<32}{p['e164']:<18}{p['kind']:<22}{em[:30]}")


main()
