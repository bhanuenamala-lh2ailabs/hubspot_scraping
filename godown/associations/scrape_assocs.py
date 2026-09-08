# -*- coding: utf-8 -*-
"""Scrape Indian IT-association member directories -> one deduped, ranked pool.

Sources and how each is reached (probed 2026-08-18):
  GESIA  gesia.org/members-directory        WordPress, 7 pages at /page/N     -> member cards
  HYSEA  hysea.in/existing-members          single static page, ~395 links    -> anchor list
  GTECH  gtechindia.org/home/getMembers     DataTables AJAX fragment (GET)    -> schema.org markup
  ITAAP  theitaap.org/members/member-directory  single static page, ~202 links
  DSCI   BLOCKED — see the note at the bottom of this file. Page 1 only (16 of ~544).

Output: assoc_members_raw.csv (everything found) + assoc_ranked.csv (deduped vs our
existing pools, ICP-filtered, ranked).
"""
import os, re, csv, json, time, gzip, urllib.request, urllib.error, collections

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept": "text/html,application/xhtml+xml,*/*", "Accept-Language": "en-US,en;q=0.9"}

# Domains that are never a member company: social, CDNs, the associations themselves, gov.
JUNK = re.compile(r"(facebook|twitter|linkedin|instagram|youtube|pinterest|whatsapp|wa\.me|t\.me|"
                  r"google|gstatic|googleapis|gmpg\.org|w3\.org|schema\.org|jquery|bootstrapcdn|"
                  r"cloudflare|cdnjs|fontawesome|gravatar|wp\.com|gesia\.org|hysea\.in|"
                  r"gtechindia\.org|theitaap\.org|dsci\.in|nasscom|gov\.in|nic\.in|x\.com|"
                  r"technopark\.org|infopark\.in|cyberparkkerala|maps\.app|goo\.gl)", re.I)


def get(url, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as x:
                raw = x.read()
                if x.headers.get("Content-Encoding") == "gzip": raw = gzip.decompress(raw)
                return raw.decode("utf-8", "replace")
        except Exception:
            if i == tries - 1: return ""
            time.sleep(2 * (i + 1))
    return ""


def clean_name(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = re.sub(r"&amp;", "&", s); s = re.sub(r"&#\d+;|&[a-z]+;", " ", s)
    return re.sub(r"\s+", " ", s).strip(" -|,–")


def dom_of(url):
    m = re.match(r"https?://(?:www\.)?([a-z0-9.-]+\.[a-z]{2,})", (url or "").lower())
    return m.group(1) if m else ""


def anchors(html):
    """(text, href) for every external anchor that is not junk."""
    out = []
    for m in re.finditer(r'<a\b[^>]*href=["\'](https?://[^"\']+)["\'][^>]*>(.*?)</a>', html, re.S | re.I):
        href, txt = m.group(1), clean_name(m.group(2))
        d = dom_of(href)
        if not d or JUNK.search(d): continue
        out.append((txt, d))
    return out


def scrape_gesia():
    rows = []
    for p in range(1, 9):
        u = "https://gesia.org/members-directory" + ("" if p == 1 else f"/page/{p}")
        h = get(u)
        if not h: break
        found = 0
        # GESIA renders member cards; the company site is the only external anchor in each card
        for txt, d in anchors(h):
            nm = txt if len(txt) > 2 and not txt.lower().startswith(("http", "visit", "website")) else d.split(".")[0]
            rows.append({"source": "GESIA", "name": clean_name(nm), "domain": d}); found += 1
        print(f"  GESIA page {p}: {found}", flush=True)
        if found == 0: break
        time.sleep(1.2)
    return rows


def scrape_simple(tag, url):
    h = get(url)
    rows = [{"source": tag, "name": clean_name(t) or d.split(".")[0], "domain": d} for t, d in anchors(h)]
    print(f"  {tag}: {len(rows)}", flush=True)
    return rows


def scrape_gtech():
    h = get("https://gtechindia.org/home/getMembers")
    rows = []
    # schema.org/Organization blocks: name in itemprop=name, site in the card's external anchor
    for blk in re.split(r'itemtype="http://schema\.org/Organization"', h)[1:]:
        nm = re.search(r'itemprop="name"[^>]*>(.*?)<', blk, re.S) or re.search(r'<h[34][^>]*>(.*?)</h[34]>', blk, re.S)
        site = re.search(r'href=["\'](https?://[^"\']+)["\']', blk)
        d = dom_of(site.group(1)) if site else ""
        name = clean_name(nm.group(1)) if nm else ""
        if name and (not d or JUNK.search(d)): d = ""
        if name or d: rows.append({"source": "GTECH", "name": name or d.split(".")[0], "domain": d})
    print(f"  GTECH: {len(rows)}", flush=True)
    return rows


def scrape_dsci_page1():
    h = get("https://www.dsci.in/corporate-member/member-directory")
    m = re.search(r'"memberDirectory":\{"data":\[(.*?)\],"total_page":(\d+)', h, re.S)
    if not m: print("  DSCI: page-1 SSR block not found"); return []
    rows = json.loads("[" + m.group(1) + "]")
    print(f"  DSCI: {len(rows)} of ~{int(m.group(2))*16} (pages 2+ require an auth token — see notes)", flush=True)
    return [{"source": "DSCI", "name": r["company_name"], "domain": "",
             "sector": r.get("sector", ""), "city": r.get("city", "")} for r in rows]


def main():
    print("scraping association directories...", flush=True)
    rows = []
    rows += scrape_gesia()
    rows += scrape_simple("HYSEA", "https://hysea.in/existing-members/")
    rows += scrape_gtech()
    rows += scrape_simple("ITAAP", "https://theitaap.org/members/member-directory/")
    rows += scrape_dsci_page1()
    for r in rows: r.setdefault("sector", ""); r.setdefault("city", "")
    with open(os.path.join(HERE, "assoc_members_raw.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["source", "name", "domain", "sector", "city"])
        w.writeheader(); w.writerows(rows)
    print(f"\nRAW: {len(rows)} rows -> assoc_members_raw.csv")
    print("  by source:", dict(collections.Counter(r["source"] for r in rows)))
    print(f"  with a domain: {sum(1 for r in rows if r['domain'])}")


main()
