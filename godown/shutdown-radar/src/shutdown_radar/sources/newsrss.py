# -*- coding: utf-8 -*-
"""Discovery: seeds, Google News RSS, GDELT 2.0, media RSS, curated trackers."""
from __future__ import annotations
import os, re, csv, json, asyncio, datetime
from urllib.parse import quote
import feedparser

from ..models import SHUTDOWN_RE, extract_brand, norm_name, is_reputable
from ..db import upsert_candidate, add_evidence

QUERIES = [
    '"startup shuts down" India',
    '"startup ceases operations" India',
    'Indian startup "winds up" operations',
    'Indian startup "shuts shop"',
    'startup "files for insolvency" India NCLT',
    'startup "returns capital to investors" India',
    'Indian startup "pulls the plug"',
    'Indian startup "calls it quits"',
    '"deadpool" Indian startup',
    'startup shutdown Bengaluru OR Mumbai OR Delhi OR Gurugram OR Hyderabad OR Pune OR Chennai',
]
# MEDIA RSS IS A FORWARD MONITOR, NOT A BACKFILL. Measured 2026-08-05: every one of these
# feeds carries only the last 1-2 DAYS of articles (Inc42 24 entries, YourStory 20, Mint 35,
# ET 50 - all dated within 48 hours). On a normal day no Indian startup shutdown is
# announced, so ZERO hits is the correct result, not a failure. These feeds accumulate value
# only by being polled daily over months; they can never retrieve 2019-2024 history.
# For historical news, Google News date-bucketing and GDELT are the only routes.
#
# URLs verified 2026-08-05 (bot UA and browser UA behave identically - UA is NOT the issue):
MEDIA_RSS = [
    ("Inc42", "https://inc42.com/feed/"),                    # 200
    ("Entrackr", "https://entrackr.com/rss"),                # 200 - /feed/ 404s, was wrong
    ("YourStory", "https://yourstory.com/feed"),             # 200
    ("Moneycontrol", "https://www.moneycontrol.com/rss/latestnews.xml"),  # 200 - /technology 403s
    ("Mint", "https://www.livemint.com/rss/companies"),      # 200
    ("ET Tech", "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms"),  # 200
    # genuinely down as of 2026-08-05, kept so the run report names them:
    ("VCCircle", "https://www.vccircle.com/feed"),           # 500 server error
    ("Business Standard", "https://www.business-standard.com/rss/companies-101.rss"),  # 403
]
TRACKERS = [
    ("Entrackr shutdown tag", "https://entrackr.com/tags/shutdown"),
    ("Entrackr startups tag", "https://entrackr.com/tags/startups"),
    ("Inc42 shutdowns", "https://inc42.com/features/indian-startup-shutdowns-2024/"),
    ("Inc42 layoff tracker", "https://inc42.com/features/indian-startup-layoffs-tracker/"),
]


def months(since: str):
    y, m = int(since[:4]), int(since[5:7])
    today = datetime.date.today()
    while (y, m) <= (today.year, today.month):
        nm_y, nm_m = (y + 1, 1) if m == 12 else (y, m + 1)
        yield (f"{y}-{m:02d}-01", f"{nm_y}-{nm_m:02d}-01")
        y, m = nm_y, nm_m


def gnews_url(q: str, after: str, before: str) -> str:
    full = f"{q} after:{after} before:{before}"
    return ("https://news.google.com/rss/search?q=" + quote(full) +
            "&hl=en-IN&gl=IN&ceid=IN:en")


def gdelt_url(q: str, start: str, end: str) -> str:
    s = start.replace("-", "") + "000000"
    e = end.replace("-", "") + "000000"
    return ("https://api.gdeltproject.org/api/v2/doc/doc?query=" + quote(f"{q} sourcecountry:IN") +
            f"&mode=ArtList&maxrecords=250&format=json&startdatetime={s}&enddatetime={e}")


def _add(db, brand, source, *, kind="news", url=None, sname=None, pub=None, snippet=None, pat=None):
    n = norm_name(brand)
    if not n or len(n) < 3: return None
    cid = upsert_candidate(db, brand, n, source)
    add_evidence(db, cid, kind, source_url=url, source_name=sname, published_at=pub,
                 snippet=snippet, matched_pattern=pat)
    return cid


def load_seeds(db, path: str, log) -> int:
    if not os.path.exists(path):
        log("  seeds: seed_shutdowns.csv missing — skipped"); return 0
    n = 0
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            brand = (row.get("brand_name") or "").strip()
            if not brand: continue
            cid = upsert_candidate(db, brand, norm_name(brand), "manual_seed")
            add_evidence(db, cid, "manual", source_name=row.get("source_name") or "seed",
                         published_at=row.get("shutdown_date"),
                         snippet=f"{row.get('sector','')} · {row.get('city','')} · "
                                 f"{row.get('reason','')}"[:300],
                         raw=row)
            n += 1
    db.commit()
    log(f"  seeds: {n} known shutdowns loaded (zero network)")
    return n


async def discover(db, http, since: str, log, which="all") -> dict:
    counts = {"google_news": 0, "gdelt": 0, "media_rss": 0, "tracker": 0}
    zero = []

    if which in ("all", "news"):
        urls = [(q, gnews_url(q, a, b)) for q in QUERIES for a, b in months(since)]
        log(f"  google news: {len(urls)} monthly buckets")
        # Google soft-bans a burst: 320 buckets fired concurrently earns an HTTP 503
        # "Sorry..." interstitial for the whole IP, and every later bucket returns nothing.
        # Fetch in small serial waves and bail out loudly the moment the ban page appears,
        # rather than quietly recording a near-empty discovery run.
        res, banned = [], False
        for i in range(0, len(urls), 8):
            wave = await asyncio.gather(*[http.get_text(u) for _, u in urls[i:i + 8]])
            res.extend(wave)
            if any(b and "Sorry..." in b[:400] for b in wave):
                banned = True
                log(f"  !! GOOGLE NEWS SOFT-BAN at bucket {i}: serving the 'Sorry...' "
                    f"interstitial. Remaining {len(urls) - i - 8} buckets abandoned — "
                    f"their results are NOT missing data, they were never fetched. "
                    f"Re-run later; the cache keeps what did land.")
                break
            await asyncio.sleep(1.5)
        res += [None] * (len(urls) - len(res))
        zero.append("google_news:SOFT_BANNED") if banned else None
        for (q, u), body in zip(urls, res):
            if not body or "Sorry..." in body[:400]: continue
            for e in feedparser.parse(body).entries:
                title = getattr(e, "title", "") or ""
                if not SHUTDOWN_RE.search(title): continue
                brand = extract_brand(title)
                if not brand: continue
                m = SHUTDOWN_RE.search(title)
                src = getattr(getattr(e, "source", None), "title", "") or ""
                if _add(db, brand, "google_news", url=getattr(e, "link", None),
                        sname=src or "Google News", pub=getattr(e, "published", None),
                        snippet=title, pat=m.group(0)):
                    counts["google_news"] += 1
        db.commit()
        if counts["google_news"] == 0: zero.append("google_news")

    if which in ("all", "gdelt"):
        urls = [(q, gdelt_url(q, a, b)) for q in QUERIES[:5] for a, b in months(since)]
        log(f"  gdelt: {len(urls)} buckets")
        res = await asyncio.gather(*[http.get_json(u) for _, u in urls])
        for (q, u), d in zip(urls, res):
            for art in (d or {}).get("articles", []) or []:
                title = art.get("title") or ""
                if not SHUTDOWN_RE.search(title): continue
                brand = extract_brand(title)
                if not brand: continue
                if _add(db, brand, "gdelt", url=art.get("url"), sname=art.get("domain"),
                        pub=art.get("seendate"), snippet=title,
                        pat=SHUTDOWN_RE.search(title).group(0)):
                    counts["gdelt"] += 1
        db.commit()
        if counts["gdelt"] == 0: zero.append("gdelt")

    if which in ("all", "rss"):
        res = await asyncio.gather(*[http.get_text(u) for _, u in MEDIA_RSS])
        for (name, u), body in zip(MEDIA_RSS, res):
            if not body: zero.append(f"media_rss:{name}"); continue
            hits = 0
            for e in feedparser.parse(body).entries:
                title = getattr(e, "title", "") or ""
                blob = title + " " + (getattr(e, "summary", "") or "")
                if not SHUTDOWN_RE.search(blob): continue
                brand = extract_brand(title)
                if not brand: continue
                if _add(db, brand, "media_rss", url=getattr(e, "link", None), sname=name,
                        pub=getattr(e, "published", None), snippet=title,
                        pat=SHUTDOWN_RE.search(blob).group(0)):
                    counts["media_rss"] += 1; hits += 1
            log(f"    {name}: {hits}")
        db.commit()

    if which in ("all", "trackers"):
        res = await asyncio.gather(*[http.get_text(u) for _, u in TRACKERS])
        for (name, u), body in zip(TRACKERS, res):
            if not body: zero.append(f"tracker:{name}"); continue
            text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", body)
            for m in re.finditer(r"<a[^>]+href=\"([^\"]+)\"[^>]*>([^<]{8,140})</a>", text):
                href, label = m.group(1), re.sub(r"\s+", " ", m.group(2)).strip()
                if not SHUTDOWN_RE.search(label): continue
                brand = extract_brand(label)
                if not brand: continue
                if _add(db, brand, "tracker", kind="news", url=href, sname=name,
                        snippet=label, pat=SHUTDOWN_RE.search(label).group(0)):
                    counts["tracker"] += 1
        db.commit()

    total = sum(counts.values())
    log(f"  discovery totals: {counts} = {total}")
    if total and total < 150:
        log(f"  !! SANITY GATE: only {total} news candidates (expected 300-1500). "
            f"Regex or bucketing may be broken.")
    return {"counts": counts, "zero_sources": zero, "total": total}
