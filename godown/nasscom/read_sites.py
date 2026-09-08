# -*- coding: utf-8 -*-
"""Stage 1: read each candidate's website and extract what NASSCOM does not publish.

NASSCOM gives name, city, website. Both real filters — "shipping software well before 2024"
and "250-600 headcount" — have to come from somewhere else. This covers the first one and
kills the non-software firms; headcount is Stage 2 (LinkedIn) and is deliberately NOT
attempted here, because sites either omit it or inflate it.

Per company, from the homepage plus an about/company page when one is linked:
  founded_year   'since 1998', 'established in 2011', 'founded 2015', or a copyright floor
  dev_signals    evidence the firm actually builds software rather than reselling it
  prod_signals   product/platform/SaaS language vs pure services language
  self_headcount any team-size claim on the page, recorded but NOT trusted as the filter
  verdict        heuristic pre-sort so the agent step only judges genuinely ambiguous ones

Concurrent but polite: a small worker pool, short timeouts, one retry. A site that is slow,
parked or dead costs one row, never the run.

Usage: python3 read_sites.py [--src nasscom_candidates_ALL.csv] [--limit 60] [--workers 12]
"""
import os, re, sys, csv, json, time, html, collections, urllib.request, urllib.error
import concurrent.futures as cf

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "nasscom_candidates_ALL.csv")
OUT = os.path.join(HERE, "site_reads.json")
LIMIT, WORKERS = 0, 12
for i, a in enumerate(sys.argv):
    if a == "--src": SRC = os.path.join(HERE, sys.argv[i+1])
    if a == "--limit": LIMIT = int(sys.argv[i+1])
    if a == "--workers": WORKERS = int(sys.argv[i+1])
    if a == "--out": OUT = os.path.join(HERE, sys.argv[i+1])

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
THIS_YEAR = 2026

# Builds software itself.
DEV = [r"custom software (development|solution)", r"software development", r"product engineering",
       r"software engineering", r"application development", r"web development", r"mobile app development",
       r"\bsdlc\b", r"\bdevops\b", r"\bmicroservices\b", r"\bapi(s)? (development|integration)",
       r"\b(react|angular|node\.?js|django|laravel|spring boot|\.net|flutter|kotlin|golang)\b",
       r"\b(aws|azure|gcp) (cloud )?(development|migration|services)", r"full[- ]stack",
       r"\bqa\b|quality (assurance|engineering)", r"\bstaff augmentation\b", r"offshore development cent"]
# Sells someone else's software, or is not a software firm at all.
NOTDEV = [r"\b(reseller|authorized partner|distributor|dealer)\b", r"\b(msp|managed print|hardware supply)\b",
          r"\b(staffing|recruitment|manpower|payroll services)\b", r"\b(digital marketing|seo services|branding agency)\b",
          r"\b(bpo|call cent|transcription|data entry)\b",
          r"\b(manufactur|pharmaceutic|logistics|freight|insurance|hospital|automotive|seating|chemical)\b"]
PRODUCT = [r"\bour (product|platform)\b", r"\bsaas\b", r"\bplatform\b", r"\bpricing\b",
           r"\b(free trial|book a demo|request a demo|sign up free)\b", r"\bsubscription\b",
           r"\b(product suite|our solutions? include)\b"]
SERVICE = [r"\b(hire|dedicated) (developers?|teams?|engineers?)\b", r"\b(our services|service offerings)\b",
           r"\b(consulting|outsourcing) (services|partner)\b", r"\bengagement models?\b",
           r"\b(time and material|fixed price)\b", r"\bit services\b"]
HEAD = [r"([\d,]{2,6})\s*\+?\s*(?:employees|professionals|engineers|developers|experts|specialists|strong team|team members)",
        r"team of\s*([\d,]{2,6})", r"([\d,]{2,6})\s*\+?\s*(?:member|people) (?:team|strong)"]


def get(url, timeout=14):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read(900_000)
        enc = (r.headers.get_content_charset() or "utf-8")
        return r.geturl(), raw.decode(enc, "replace")


def text_of(h):
    h = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h)))


def about_link(base, h):
    for m in re.finditer(r'href=["\']([^"\']{1,180})["\']', h, re.I):
        u = m.group(1)
        if re.search(r"(about|company|who-we-are|our-story|overview)", u, re.I):
            if u.startswith("http"): return u
            if u.startswith("/"):
                return re.match(r"(https?://[^/]+)", base).group(1) + u
    return ""


def years(t):
    """Explicit founding claims beat a copyright floor, which is only a weak upper bound."""
    yrs = []
    for rx in (r"(?:since|est(?:ablished)?\.?(?: in)?|founded(?: in)?|inception(?: in)?|incorporated(?: in)?)\s*[:\-]?\s*((?:19|20)\d{2})",
               r"((?:19|20)\d{2})\s*[-–]\s*(?:present|now)"):
        for m in re.finditer(rx, t, re.I):
            y = int(m.group(1))
            if 1970 <= y <= THIS_YEAR: yrs.append(y)
    return min(yrs) if yrs else None


def hits(t, pats):
    return sorted({re.sub(r"[\\\\^$.|?*+()\[\]{}]", "", p)[:26]
                   for p in pats if re.search(p, t, re.I)})


def read(row):
    site = row["website"].strip()
    if not site.startswith("http"): site = "http://" + site
    rec = {"name": row["name"], "city": row["city"], "domain": row["domain"], "website": site}
    page = ""
    for attempt, u in enumerate((site, site.replace("http://", "https://", 1))):
        try:
            final, h = get(u); page = h; rec["final_url"] = final; break
        except Exception as e:
            rec["error"] = f"{type(e).__name__}"
            if attempt: return rec | {"verdict": "unreachable"}
    if not page: return rec | {"verdict": "unreachable"}
    t = text_of(page)
    al = about_link(rec.get("final_url", site), page)
    if al:
        try: t += " " + text_of(get(al)[1])
        except Exception: pass
    rec["about_url"] = al
    low = t.lower()
    hc = None
    for rx in HEAD:
        m = re.search(rx, low)
        if m:
            v = int(m.group(1).replace(",", ""))
            if 5 <= v <= 200000: hc = v; break
    cw = re.findall(r"(?:©|copyright)\s*(?:\D{0,20})((?:19|20)\d{2})", t, re.I)
    rec |= {"founded_year": years(t),
            "copyright_year": min(int(c) for c in cw) if cw else None,
            "self_headcount": hc,
            "dev_signals": hits(low, DEV), "notdev_signals": hits(low, NOTDEV),
            "prod_signals": hits(low, PRODUCT), "serv_signals": hits(low, SERVICE),
            "text_len": len(t)}
    nd, d = len(rec["notdev_signals"]), len(rec["dev_signals"])
    if rec["text_len"] < 400: rec["verdict"] = "thin_site"
    elif nd >= 2 and d <= 1: rec["verdict"] = "not_software"
    elif d >= 2: rec["verdict"] = "software_dev"
    else: rec["verdict"] = "ambiguous"
    p, s = len(rec["prod_signals"]), len(rec["serv_signals"])
    rec["prod_or_serv"] = "product" if p > s + 1 else ("service" if s > p else "mixed")
    return rec


def main():
    rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
    if LIMIT: rows = rows[::max(1, len(rows)//LIMIT)][:LIMIT]   # spread, don't take the A's
    print(f"reading {len(rows)} sites with {WORKERS} workers...", flush=True)
    out, t0 = [], time.time()
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for i, r in enumerate(ex.map(read, rows), 1):
            out.append(r)
            if i % 20 == 0:
                print(f"   {i}/{len(rows)}  {time.time()-t0:.0f}s", flush=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    v = collections.Counter(r["verdict"] for r in out)
    print(f"\ndone in {time.time()-t0:.0f}s -> {os.path.basename(OUT)}")
    print("\nVERDICT:")
    for k, n in v.most_common(): print(f"   {n:>4}  {k}  ({n/len(out)*100:.0f}%)")
    reach = [r for r in out if r["verdict"] != "unreachable"]
    fy = [r for r in reach if r.get("founded_year")]
    print(f"\nreachable            : {len(reach)}/{len(out)}")
    print(f"founding year stated : {len(fy)}  ({len(fy)/max(len(reach),1)*100:.0f}% of reachable)")
    if fy:
        pre = [r for r in fy if r["founded_year"] <= 2020]
        print(f"   founded <=2020    : {len(pre)}  ({len(pre)/len(fy)*100:.0f}% of those stating one)")
    sh = [r for r in reach if r.get("self_headcount")]
    print(f"self-stated headcount: {len(sh)}  ({len(sh)/max(len(reach),1)*100:.0f}%)  <- NOT trusted, Stage 2 decides")
    if sh:
        band = [r for r in sh if 250 <= r["self_headcount"] <= 600]
        print(f"   claiming 250-600  : {len(band)}")
    print("\nproduct vs service:", dict(collections.Counter(r.get("prod_or_serv") for r in reach)))


main()
