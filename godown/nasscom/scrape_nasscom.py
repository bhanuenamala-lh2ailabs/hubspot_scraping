# -*- coding: utf-8 -*-
"""Scrape the full NASSCOM member directory -> name, city, website.

The listing is plain server-rendered Drupal HTML behind `?page=N`, 15 members a page, and
robots.txt permits /members-listing (it blocks /search/, /admin/, /core/, /profiles/). No
headless browser, no API key.

Politeness: one request at a time with a delay. This is a membership directory, not a public
API — hammering it would be both rude and the fastest way to get blocked mid-run.

Writes godown/nasscom/nasscom_members.csv and can resume: pages already captured are skipped,
so a network drop costs one page rather than the whole run.

Usage: python3 scrape_nasscom.py [--pages 233] [--delay 0.4]
"""
import os, re, sys, csv, html, time, json, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "nasscom_members.csv")
RAW = os.path.join(HERE, "_pages.json")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

PAGES = 233; DELAY = 0.4
for i, a in enumerate(sys.argv):
    if a == "--pages": PAGES = int(sys.argv[i+1])
    if a == "--delay": DELAY = float(sys.argv[i+1])


def fetch(n):
    for attempt in range(4):
        try:
            r = urllib.request.Request(f"https://nasscom.in/members-listing?page={n}",
                                       headers={"User-Agent": UA, "Accept": "text/html"})
            with urllib.request.urlopen(r, timeout=45) as x:
                return x.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(3 * (attempt + 1)); continue
            raise
        except Exception:
            if attempt == 3: raise
            time.sleep(3 * (attempt + 1))


def parse(s):
    """Each member is one .perspectives_card: h3.job_title = name, .category = city,
    .fee > a[href] = website. Split on the card class rather than regexing the whole page,
    so a missing website on one card cannot swallow the next card's."""
    out = []
    for blk in s.split('class="perspectives_card"')[1:]:
        nm = re.search(r'<h3 class="job_title">(.*?)</h3>', blk, re.S)
        if not nm: continue
        ct = re.search(r'<div class="category">(.*?)</div>', blk, re.S)
        wb = re.search(r'<div class="fee"><a href="(.*?)"', blk, re.S)
        out.append({"name": html.unescape(nm.group(1)).strip(),
                    "city": html.unescape(ct.group(1)).strip() if ct else "",
                    "website": html.unescape(wb.group(1)).strip() if wb else ""})
    return out


def main():
    seen = json.load(open(RAW, encoding="utf-8")) if os.path.exists(RAW) else {}
    print(f"resuming with {len(seen)} pages already captured" if seen else "starting fresh", flush=True)
    for n in range(PAGES + 1):
        if str(n) in seen: continue
        try:
            rows = parse(fetch(n))
        except Exception as e:
            print(f"   page {n}: FAILED {type(e).__name__} — leaving for a re-run", flush=True)
            continue
        seen[str(n)] = rows
        if (n + 1) % 25 == 0:
            json.dump(seen, open(RAW, "w", encoding="utf-8"), ensure_ascii=False)
            print(f"   {n+1}/{PAGES+1} pages | {sum(len(v) for v in seen.values())} members", flush=True)
        time.sleep(DELAY)
    json.dump(seen, open(RAW, "w", encoding="utf-8"), ensure_ascii=False)

    allrows = [r for n in sorted(seen, key=int) for r in seen[n]]
    # the same firm can appear on two pages if the listing re-orders mid-scrape
    uniq, key = [], set()
    for r in allrows:
        k = (r["name"].lower().strip(), r["website"].lower().strip())
        if k in key: continue
        key.add(k); uniq.append(r)
    with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["name", "city", "website"]); w.writeheader(); w.writerows(uniq)
    print(f"\npages captured : {len(seen)}/{PAGES+1}")
    print(f"members scraped: {len(allrows)} raw -> {len(uniq)} unique")
    print(f"with a website : {sum(1 for r in uniq if r['website'])}")
    print(f"wrote {OUT}")


main()
