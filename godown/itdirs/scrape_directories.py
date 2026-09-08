# -*- coding: utf-8 -*-
"""Harvest Indian IT-company directories -> one deduped company+domain universe.

Implements SCRAPE_IT_DIRECTORIES.md. Unit of output is a company WITH a resolved registrable
domain; rows without one are kept and flagged (backfill_needed) rather than binned.

Design notes worth knowing before editing:
  * Every fetched page is cached to raw/ and never re-fetched — these runs get interrupted.
  * Tracker->domain resolutions are cached in sqlite: aggregators use one tracker host for
    thousands of links, so resolving twice is pure waste and extra load on them.
  * robots.txt is honoured. Two sources in the brief are disallowed; we skip them by name AND
    re-check live, because a brief can go stale.
  * Nothing is scored or filtered by company quality here. That is the downstream prequal.

Usage:  python3 scrape_directories.py [--only key1,key2] [--max-pages N]
"""
import os, re, sys, csv, json, time, gzip, random, sqlite3, hashlib, collections
import urllib.request, urllib.error, urllib.parse
import urllib.robotparser as robotparser

HERE = os.path.dirname(os.path.abspath(__file__))
P = {"prior_universe": os.path.join(HERE, "data", "existing_universe.csv"),
     "crm_export": os.path.join(HERE, "data", "DEALS_MASTER.csv"),
     "out_companies": os.path.join(HERE, "out", "it_directory_universe.csv"),
     "out_rejects": os.path.join(HERE, "out", "rejects.csv"),
     "out_source_report": os.path.join(HERE, "out", "source_yield.csv"),
     "state_db": os.path.join(HERE, "state", "scrape_state.sqlite"),
     "raw": os.path.join(HERE, "raw")}
UA = "Mozilla/5.0 (compatible; LH2-research/1.0)"
DELAY = (2, 5); MAX_RETRIES = 3; BACKOFF = 30; TIMEOUT = 30
ONLY = None; MAXP = None
for i, a in enumerate(sys.argv):
    if a == "--only": ONLY = set(sys.argv[i + 1].split(","))
    if a == "--max-pages": MAXP = int(sys.argv[i + 1])
RUN = time.strftime("%Y-%m-%d")

# ---------------------------------------------------------------- domain utilities
TWO_LEVEL = {"co.in", "net.in", "org.in", "gen.in", "firm.in", "ind.in", "co.uk", "com.au",
             "co.nz", "com.sg", "com.my", "co.za", "com.br", "ac.in", "gov.in", "edu.in"}
SOCIAL = re.compile(r"(linkedin|facebook|twitter|x\.com|instagram|youtube|pinterest|justdial|"
                    r"indiamart|sulekha|google|blogspot|wordpress\.com|wixsite|bit\.ly|tinyurl|"
                    r"goo\.gl|t\.co|whatsapp|wa\.me|maps\.app|tripadvisor|glassdoor|crunchbase|"
                    r"ambitionbox|naukri|indeed|zaubacorp|tofler)", re.I)


def registrable(host):
    host = (host or "").lower().strip().strip(".")
    host = re.sub(r"^www\d?\.", "", host)
    parts = host.split(".")
    if len(parts) < 2: return ""
    last2 = ".".join(parts[-2:])
    if last2 in TWO_LEVEL and len(parts) >= 3: return ".".join(parts[-3:])
    return last2


def to_domain(url):
    """Any href/text -> clean registrable domain, or '' if it is not a company site."""
    u = (url or "").strip()
    if not u: return ""
    if not re.match(r"^https?://", u):
        if not re.match(r"^[a-z0-9.-]+\.[a-z]{2,}", u, re.I): return ""
        u = "http://" + u
    try: host = urllib.parse.urlparse(u).netloc
    except Exception: return ""
    d = registrable(host)
    if not d or SOCIAL.search(d): return ""
    return d


# ---------------------------------------------------------------- state / cache
def db():
    c = sqlite3.connect(P["state_db"])
    c.execute("CREATE TABLE IF NOT EXISTS pages(url TEXT PRIMARY KEY, ts INT)")
    c.execute("CREATE TABLE IF NOT EXISTS redirects(tracker TEXT PRIMARY KEY, domain TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS counters(source TEXT, k TEXT, v INT)")
    c.commit(); return c


CONN = db()
_last_hit = {}


def cache_path(url):
    return os.path.join(P["raw"], hashlib.sha1(url.encode()).hexdigest() + ".html.gz")


def polite(host):
    t = _last_hit.get(host, 0); w = random.uniform(*DELAY) - (time.time() - t)
    if w > 0: time.sleep(w)
    _last_hit[host] = time.time()


ROBOTS = {}


def allowed(url):
    host = urllib.parse.urlparse(url).netloc
    if host not in ROBOTS:
        rp = robotparser.RobotFileParser()
        rp.set_url(f"https://{host}/robots.txt")
        try: rp.read()
        except Exception: rp = None
        ROBOTS[host] = rp
    rp = ROBOTS[host]
    if rp is None: return True
    try: return rp.can_fetch(UA, url)
    except Exception: return True


def fetch(url, force=False):
    """Cached, polite, retrying GET. Returns html or ''. Never re-fetches a cached page."""
    cp = cache_path(url)
    if os.path.exists(cp) and not force:
        try: return gzip.open(cp, "rt", encoding="utf-8", errors="replace").read()
        except Exception: pass
    if not allowed(url):
        print(f"    robots disallow -> skip {url[:80]}", flush=True); return "__ROBOTS__"
    host = urllib.parse.urlparse(url).netloc
    for a in range(MAX_RETRIES):
        polite(host)
        try:
            r = urllib.request.Request(url, headers={"User-Agent": UA,
                "Accept": "text/html,application/xhtml+xml,*/*", "Accept-Language": "en-US,en;q=0.9"})
            with urllib.request.urlopen(r, timeout=TIMEOUT) as x:
                raw = x.read()
                if x.headers.get("Content-Encoding") == "gzip": raw = gzip.decompress(raw)
                h = raw.decode("utf-8", "replace")
            with gzip.open(cp, "wt", encoding="utf-8") as f: f.write(h)
            CONN.execute("INSERT OR REPLACE INTO pages VALUES(?,?)", (url, int(time.time()))); CONN.commit()
            return h
        except urllib.error.HTTPError as e:
            if e.code in (403, 503): return f"__BLOCKED_{e.code}__"
            if e.code == 404: return ""
            if a == MAX_RETRIES - 1: return ""
            time.sleep(BACKOFF * (2 ** a))
        except Exception:
            if a == MAX_RETRIES - 1: return ""
            time.sleep(BACKOFF * (2 ** a))
    return ""


def resolve_tracker(url, aggregator_hosts):
    """4.C — follow a tracked 'Visit Website' link to the real company domain. Cached."""
    row = CONN.execute("SELECT domain FROM redirects WHERE tracker=?", (url,)).fetchone()
    if row: return row[0]
    dom = ""
    try:
        host = urllib.parse.urlparse(url).netloc; polite(host)
        class NoRedir(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, hdrs, newurl): return None
        op = urllib.request.build_opener(NoRedir)
        cur = url
        for _ in range(6):
            r = urllib.request.Request(cur, headers={"User-Agent": UA}, method="GET")
            try:
                with op.open(r, timeout=20) as x:
                    loc = x.headers.get("Location")
            except urllib.error.HTTPError as e:
                loc = e.headers.get("Location") if e.code in (301, 302, 303, 307, 308) else None
                if e.code not in (301, 302, 303, 307, 308) and not loc: break
            except Exception:
                break
            if not loc: break
            cur = urllib.parse.urljoin(cur, loc)
            h = urllib.parse.urlparse(cur).netloc.lower()
            if h and not any(a in h for a in aggregator_hosts):
                dom = to_domain(cur); break
    except Exception:
        dom = ""
    CONN.execute("INSERT OR REPLACE INTO redirects VALUES(?,?)", (url, dom)); CONN.commit()
    return dom


# ---------------------------------------------------------------- html helpers
def strip_tags(s): return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()


def unescape(s):
    for a, b in (("&amp;", "&"), ("&nbsp;", " "), ("&#039;", "'"), ("&quot;", '"'),
                 ("&#8217;", "'"), ("&rsquo;", "'"), ("&ndash;", "-"), ("&amp;amp;", "&")):
        s = (s or "").replace(a, b)
    return re.sub(r"&#\d+;", " ", s)


def clean_name(s):
    s = unescape(strip_tags(s))
    s = re.sub(r"\s+", " ", s).strip(" -|,–·")
    return s[:120]


BARE_DOMAIN = re.compile(r"\b((?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:com|in|net|org|io|co|"
                         r"tech|dev|ai|biz|info|us|uk|app|solutions|digital|software))\b", re.I)


# ================================================================ PER-SOURCE PARSERS
# Each returns (rows, meta). rows = dicts; meta = {"attempted_pages","barrier"}.
# A parser never raises: a broken source logs a barrier and the run continues.

def _blocks(html, split_re):
    return re.split(split_re, html)[1:]


def src_infopark():
    """P1.1 — Infopark Kochi + satellites.

    Markup: one <div class="compy"> per company; <h5> carries the name and <div class="web">
    carries the site as PLAIN TEXT (no anchor), e.g. 'www.2basetechnologies.com'. An earlier
    anchor-based parser returned zero rows because there is no outbound <a> in the card at all.
    """
    rows, pages, barrier = [], 0, ""
    bases = ["https://infopark.in/companies",
             "https://infopark.in/companies/infopark-kochi-phase-1",
             "https://infopark.in/companies/infopark-thrissur",
             "https://infopark.in/companies/infopark-cherthala"]
    for base in bases:
        for pg in range(0, (MAXP or 16)):
            url = base if pg == 0 else f"{base}?page={pg}"
            h = fetch(url); pages += 1
            if h.startswith("__"): barrier = h.strip("_").lower(); break
            if not h: break
            got = 0
            for blk in re.split(r'<div class="compy">', h)[1:]:
                nm = re.search(r"<h5[^>]*>(.*?)</h5>", blk, re.S)
                if not nm: continue
                name = clean_name(nm.group(1))
                if not name: continue
                dom = ""
                w = re.search(r'<div class="web">(.*?)</div>', blk, re.S)
                if w:
                    b = BARE_DOMAIN.search(strip_tags(w.group(1)))
                    if b: dom = to_domain(b.group(1))
                if not dom:                       # fall back to any bare domain in the card
                    b = BARE_DOMAIN.search(strip_tags(blk))
                    if b: dom = to_domain(b.group(1))
                em = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", strip_tags(blk))
                ph = re.search(r"<div class=\"phone\">(.*?)</div>", blk, re.S)
                pr = re.search(r'href="(https?://infopark\.in/companies-profile/[^"]+)"', blk)
                rows.append({"company_name": name, "domain": dom,
                             "domain_source": "listed" if dom else "backfill_needed",
                             "city": "Kochi", "state_region": "Kerala",
                             "phone": strip_tags(ph.group(1))[:24] if ph else "",
                             "email": em.group(0) if em else "",
                             "source": "infopark", "profile_url": pr.group(1) if pr else url})
                got += 1
            print(f"    infopark {base.split('/')[-1][:26]} p{pg} — {got} rows, "
                  f"{sum(1 for r in rows if r['domain'])} domains cumulative", flush=True)
            if got == 0: break
    return rows, {"attempted_pages": pages, "barrier": barrier}


def src_technopark_mirror():
    """P1.2 — technoparktoday static mirror: plain table name/address/phone/email/website."""
    url = "https://technoparktoday.com/technopark-information/technopark-companies/"
    h = fetch(url)
    if h.startswith("__"): return [], {"attempted_pages": 1, "barrier": h.strip("_").lower()}
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", h, re.S | re.I):
        tds = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S | re.I)
        if len(tds) < 2: continue
        nm = clean_name(tds[0])
        if not nm or nm.lower() in ("company", "name", "sl no", "#"): continue
        cell = " ".join(tds)
        dom = ""
        a = re.search(r'href="(https?://[^"]+)"', cell)
        if a: dom = to_domain(a.group(1))
        if not dom:
            b = BARE_DOMAIN.search(strip_tags(cell))
            if b: dom = to_domain(b.group(1))
        em = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", strip_tags(cell))
        ph = re.search(r"(?:\+?91[\s-]?)?\d{3,5}[\s-]?\d{6,8}", strip_tags(cell))
        rows.append({"company_name": nm, "domain": dom,
                     "domain_source": "listed" if dom else "backfill_needed",
                     "city": "Trivandrum", "state_region": "Kerala",
                     "phone": ph.group(0) if ph else "", "email": em.group(0) if em else "",
                     "source": "technopark", "profile_url": url})
    print(f"    technopark mirror — {len(rows)} rows", flush=True)
    return rows, {"attempted_pages": 1, "barrier": ""}


def src_stpi_blr():
    """P1.4 — STPI Bengaluru registered units."""
    url = "https://blr.stpi.in/registered-units.html"
    h = fetch(url)
    if h.startswith("__"): return [], {"attempted_pages": 1, "barrier": h.strip("_").lower()}
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", h, re.S | re.I):
        tds = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S | re.I)
        if len(tds) < 2: continue
        nm = clean_name(tds[1] if re.fullmatch(r"\d+", clean_name(tds[0]) or "x") else tds[0])
        if not nm or nm.lower().startswith(("sl", "s.no", "name of")): continue
        cell = " ".join(tds); dom = ""
        a = re.search(r'href="(https?://[^"]+)"', cell)
        if a: dom = to_domain(a.group(1))
        if not dom:
            b = BARE_DOMAIN.search(strip_tags(cell))
            if b: dom = to_domain(b.group(1))
        rows.append({"company_name": nm, "domain": dom,
                     "domain_source": "listed" if dom else "backfill_needed",
                     "city": "Bengaluru", "state_region": "Karnataka", "phone": "", "email": "",
                     "source": "stpi_blr", "profile_url": url})
    print(f"    stpi_blr — {len(rows)} rows", flush=True)
    return rows, {"attempted_pages": 1, "barrier": ""}


def _generic_member_page(key, urls, city, region):
    """P2 helper — associations whose member page is plain HTML of unknown shape."""
    rows, pages, barrier = [], 0, ""
    for url in urls:
        h = fetch(url); pages += 1
        if h.startswith("__"): barrier = h.strip("_").lower(); continue
        if not h: continue
        seen = set()
        # anchors first (a member row usually links to the member's own site)
        for m in re.finditer(r'<a\b[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>', h, re.S | re.I):
            href, txt = m.group(1), clean_name(m.group(2))
            d = to_domain(href)
            if not d or urllib.parse.urlparse(url).netloc.endswith(registrable(urllib.parse.urlparse(href).netloc)):
                continue
            if d in seen: continue
            seen.add(d)
            rows.append({"company_name": txt or d.split(".")[0], "domain": d, "domain_source": "listed",
                         "city": city, "state_region": region, "phone": "", "email": "",
                         "source": key, "profile_url": url})
        # then table rows with no anchor -> names-only backfill
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", h, re.S | re.I):
            tds = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S | re.I)
            if len(tds) < 2: continue
            cell = " ".join(tds)
            if re.search(r'href="https?://', cell): continue
            nm = clean_name(tds[1] if re.fullmatch(r"\d+", clean_name(tds[0]) or "x") else tds[0])
            if not nm or len(nm) < 3: continue
            rows.append({"company_name": nm, "domain": "", "domain_source": "backfill_needed",
                         "city": city, "state_region": region, "phone": "", "email": "",
                         "source": key, "profile_url": url})
        print(f"    {key} {url.split('/')[-1][:28]} — {len(rows)} cumulative", flush=True)
    return rows, {"attempted_pages": pages, "barrier": barrier}


def src_itao():
    """P2.5 — ITAO Odisha. Corporate Members render as plain div cards (no anchors at all,
    which is why the generic anchor-based parser found zero). life.php holds individual
    'life members', not companies, and is empty of this structure — corporate.php only."""
    url = "https://itaoodisha.org/corporate.php"
    h = fetch(url)
    if h.startswith("__"): return [], {"attempted_pages": 1, "barrier": h.strip("_").lower()}
    rows = []
    for blk in re.split(r'class="our-team-main"', h)[1:]:
        nm = re.search(r"<h3>([^<]+)</h3>", blk)
        name = clean_name(nm.group(1)) if nm else ""
        if not name: continue
        tail = strip_tags(blk[:900])
        em = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", tail)
        ph = re.search(r"\b\d{10}\b", tail)
        rows.append({"company_name": name, "domain": "", "domain_source": "backfill_needed",
                     "city": "Bhubaneswar", "state_region": "Odisha",
                     "phone": ph.group(0) if ph else "", "email": em.group(0) if em else "",
                     "source": "itao", "profile_url": url})
    print(f"    itao corporate.php — {len(rows)} rows", flush=True)
    return rows, {"attempted_pages": 1, "barrier": ""}
def src_sida():
    """P2.6 — SIDA Madurai. Members render as WordPress popups already embedded in the page:
    name/city on the card, phone/email/website inside a hidden popup div per member (no AJAX
    needed — everything is server-rendered in one fetch of /members)."""
    url = "https://sidatn.org/members"
    h = fetch(url)
    if h.startswith("__"): return [], {"attempted_pages": 1, "barrier": h.strip("_").lower()}
    rows = []
    for blk in re.split(r'class="single-member-div', h)[1:]:
        nm = re.search(r'<h2 class="gs-member-name\s*">(.*?)</h2>', blk, re.S)
        if not nm:
            nm = re.search(r'itemprop="name"[^>]*>(.*?)</a>', blk, re.S)
        name = clean_name(nm.group(1)) if nm else ""
        if not name: continue
        city = re.search(r'itemprop="jobTitle">([^<]*)</div>', blk)
        web = re.search(r'href="(https?://[^"]+)"[^>]*>\s*(?:https?://)?[^<]*</a>\s*</div>\s*</td>\s*<td[^>]*>\s*<i class="fas fa-map', blk, re.S)
        if not web: web = re.search(r'fa-globe[^<]*</i>\s*(?:<br\s*/?>)?\s*<a[^>]+href="(https?://[^"]+)"', blk, re.S)
        dom = to_domain(web.group(1)) if web else ""
        em = re.search(r'mailto:([\w.+-]+@[\w-]+\.[\w.]+)', blk)
        ph = re.search(r'tel:(\+?\d[\d\s-]{7,})', blk)
        rows.append({"company_name": name, "domain": dom,
                     "domain_source": "listed" if dom else "backfill_needed",
                     "city": clean_name(city.group(1)) if city else "Madurai", "state_region": "Tamil Nadu",
                     "phone": ph.group(1).strip() if ph else "", "email": em.group(1) if em else "",
                     "source": "sida", "profile_url": url})
    print(f"    sida members — {len(rows)} rows, {sum(1 for r in rows if r['domain'])} with domain", flush=True)
    return rows, {"attempted_pages": 1, "barrier": ""}
def src_rito():
    """P2.7 — RITO Rajasthan. CONFIRMED 19 Aug: no public member directory exists anywhere on
    the site. /membership.html is a join-us signup form, not a listing. Logged as a barrier
    rather than silently returning zero -- there is genuinely nothing to scrape here."""
    return [], {"attempted_pages": 1, "barrier": "no_public_directory"}
def src_mohali(): return _generic_member_page("mohali_itca", ["https://itcitymohaliassociation.com/members",
                                                              "https://itcitymohaliassociation.com/"], "Mohali", "Punjab")
def src_esc():    return _generic_member_page("esc_india", ["https://escindia.in/our-members/"], "", "Pan-India")
def src_via():    return _generic_member_page("via_nagpur", ["https://via-india.com/member_directory/software-hardware/"],
                                              "Nagpur", "Maharashtra")
def src_ait():    return _generic_member_page("ait_blr", ["https://ait-bengaluru.in/business-directory/"], "Bengaluru", "Karnataka")
def src_stpi_nat():
    """P3.12 — STPI national statutory-services units. CONFIRMED 19 Aug: the real unit list is
    NOT in this HTML page -- only 3 company names leak into an auto-generated <meta
    description>, proving the actual list is a linked PDF (stpi.in/.../List-of-STP-unit-merged.pdf).
    Parsing a PDF is out of scope for this pass; logged as a barrier, not silently zeroed."""
    return [], {"attempted_pages": 1, "barrier": "data_in_pdf_not_html"}


def src_techbehemoths():
    """P4.14 — highest raw volume. PATH pagination /companies/india/{n}. Trackers must resolve."""
    rows, pages, barrier = [], 0, ""
    AGG = ("techbehemoths.com",)
    cap = MAXP or 40
    for pg in range(1, cap + 1):
        url = "https://techbehemoths.com/companies/india" + ("" if pg == 1 else f"/{pg}")
        h = fetch(url); pages += 1
        if h.startswith("__"): barrier = h.strip("_").lower(); break
        if not h: break
        got = 0
        for m in re.finditer(r'<a[^>]+href="(/company/[^"]+)"[^>]*>(.*?)</a>', h, re.S | re.I):
            prof, nm = m.group(1), clean_name(m.group(2))
            if not nm or len(nm) < 2: continue
            rows.append({"company_name": nm, "domain": "", "domain_source": "backfill_needed",
                         "city": "", "state_region": "India", "phone": "", "email": "",
                         "source": "techbehemoths", "profile_url": "https://techbehemoths.com" + prof})
            got += 1
        # direct outbound links on the listing (some cards expose them)
        for m in re.finditer(r'href="(https?://[^"]+)"[^>]*[^>]*>\s*(?:Visit\s*Website|Website)', h, re.I):
            d = resolve_tracker(m.group(1), AGG) if "techbehemoths.com" in m.group(1) else to_domain(m.group(1))
            if d and rows: rows[-1]["domain"] = d; rows[-1]["domain_source"] = "redirect"
        print(f"    techbehemoths p{pg} — {got} rows", flush=True)
        if got == 0: break
    return rows, {"attempted_pages": pages, "barrier": barrier}


def src_clutch():
    """P4.15 — Cloudflare-guarded. One attempt at normal pace; bank partial and move on."""
    url = "https://clutch.co/in/developers/information-technology-industry"
    h = fetch(url)
    if h.startswith("__"):
        print("    clutch — challenge/blocked, banking partial", flush=True)
        return [], {"attempted_pages": 1, "barrier": "cloudflare"}
    rows = []
    for m in re.finditer(r'<a[^>]+href="(/profile/[^"]+)"[^>]*>(.*?)</a>', h, re.S | re.I):
        nm = clean_name(m.group(2))
        if nm and len(nm) > 2:
            rows.append({"company_name": nm, "domain": "", "domain_source": "backfill_needed",
                         "city": "", "state_region": "India", "phone": "", "email": "",
                         "source": "clutch", "profile_url": "https://clutch.co" + m.group(1)})
    print(f"    clutch — {len(rows)} rows", flush=True)
    return rows, {"attempted_pages": 1, "barrier": "" if rows else "cloudflare"}


def src_sortlist():
    rows, pages, barrier = [], 0, ""
    for base in ("https://www.sortlist.com/web-development/india-in",
                 "https://www.sortlist.com/app-development/india-in",
                 "https://www.sortlist.com/s/software-development/india-in"):
        for pg in range(1, (MAXP or 6) + 1):
            url = base if pg == 1 else f"{base}?page={pg}"
            h = fetch(url); pages += 1
            if h.startswith("__"): barrier = h.strip("_").lower(); break
            if not h: break
            got = 0
            for m in re.finditer(r'href="(/agency/[^"]+)"[^>]*>(.*?)</a>', h, re.S | re.I):
                nm = clean_name(m.group(2))
                if not nm or len(nm) < 2: continue
                rows.append({"company_name": nm, "domain": "", "domain_source": "backfill_needed",
                             "city": "", "state_region": "India", "phone": "", "email": "",
                             "source": "sortlist", "profile_url": "https://www.sortlist.com" + m.group(1)})
                got += 1
            print(f"    sortlist {base.split('/')[-2]} p{pg} — {got} rows", flush=True)
            if got == 0: break
    return rows, {"attempted_pages": pages, "barrier": barrier}


SOURCES = [("infopark", "P1", src_infopark), ("technopark", "P1", src_technopark_mirror),
           ("stpi_blr", "P1", src_stpi_blr),
           ("itao", "P2", src_itao), ("sida", "P2", src_sida), ("rito", "P2", src_rito),
           ("mohali_itca", "P2", src_mohali), ("esc_india", "P2", src_esc),
           ("via_nagpur", "P3", src_via), ("ait_blr", "P3", src_ait), ("stpi_national", "P3", src_stpi_nat),
           ("techbehemoths", "P4", src_techbehemoths), ("clutch", "P4", src_clutch),
           ("sortlist", "P4", src_sortlist)]
# stpi_noida omitted by design: robots.txt disallow (brief section 6) — manual pull only.


# ================================================================ NORMALIZE + DEDUPE
LEGAL = re.compile(r"\b(pvt|private|ltd|limited|llp|llc|inc|incorporated|co|company|technologies|"
                   r"technology|solutions|software|systems|labs|services|india|infotech)\b", re.I)


def nkey(name):
    s = LEGAL.sub(" ", (name or "").lower())
    return re.sub(r"[^a-z0-9]", "", s)


def tokset(name):
    return set(t for t in re.split(r"[^a-z0-9]+", LEGAL.sub(" ", (name or "").lower())) if len(t) > 1)


def jacc(a, b):
    if not a or not b: return 0.0
    return len(a & b) / len(a | b)


def load_prior():
    dom, nm = set(), set()
    for path, dcols, ncols in ((P["prior_universe"], ("domain", "website"), ("name",)),
                               (P["crm_export"], ("lh2_domain",), ("dealname",))):
        if not os.path.exists(path): print(f"  (no {os.path.basename(path)} — skipping that dedupe)"); continue
        try:
            for r in csv.DictReader(open(path, encoding="utf-8-sig")):
                for c in dcols:
                    d = to_domain(r.get(c, ""))
                    if d: dom.add(d)
                for c in ncols:
                    k = nkey(r.get(c, ""))
                    if k: nm.add(k)
        except Exception as e: print(f"  prior load warn {path}: {e}")
    return dom, nm


def main():
    for d in ("out", "raw", "state"): os.makedirs(os.path.join(HERE, d), exist_ok=True)
    prior_dom, prior_nm = load_prior()
    print(f"prior universe: {len(prior_dom)} domains, {len(prior_nm)} names\n")
    allrows, report, rejects = [], [], []
    for key, tier, fn in SOURCES:
        if ONLY and key not in ONLY: continue
        print(f"[{tier}] {key}", flush=True)
        t0 = time.time()
        try: rows, meta = fn()
        except Exception as e:
            print(f"    ERROR {type(e).__name__}: {str(e)[:90]}", flush=True)
            rows, meta = [], {"attempted_pages": 0, "barrier": f"error:{type(e).__name__}"}
        for r in rows: r["first_seen_run"] = RUN; r["notes"] = ""
        allrows += rows
        report.append({"source": key, "tier": tier, "attempted_pages": meta.get("attempted_pages", 0),
                       "rows_parsed": len(rows), "with_domain": sum(1 for r in rows if r["domain"]),
                       "barrier": meta.get("barrier", ""), "secs": round(time.time() - t0)})
        print(f"    -> {len(rows)} parsed, {sum(1 for r in rows if r['domain'])} with domain "
              f"({round(time.time()-t0)}s){' BARRIER=' + meta['barrier'] if meta.get('barrier') else ''}\n", flush=True)

    total_parsed = len(allrows)
    # ---- drop social/rejected domains
    keep = []
    for r in allrows:
        if r["domain"] and SOCIAL.search(r["domain"]):
            rejects.append({**r, "reason": "non_company_domain"}); continue
        keep.append(r)
    # ---- dedupe within scrape: domain first, then name+city
    by_dom, by_nm, out = {}, {}, []
    for r in keep:
        d = r["domain"]
        if d:
            if d in by_dom:
                o = by_dom[d]
                o["source"] = ";".join(sorted(set(o["source"].split(";") + [r["source"]])))
                for f in ("city", "phone", "email", "state_region"):
                    if not o.get(f) and r.get(f): o[f] = r[f]
                rejects.append({**r, "reason": "dup_domain_within_scrape"}); continue
            by_dom[d] = r; out.append(r); continue
        k = nkey(r["company_name"]) + "|" + (r.get("city") or "").lower()
        if k in by_nm:
            o = by_nm[k]; o["source"] = ";".join(sorted(set(o["source"].split(";") + [r["source"]])))
            rejects.append({**r, "reason": "dup_name_within_scrape"}); continue
        by_nm[k] = r; out.append(r)
    # ---- dedupe vs prior universe + CRM
    final, ov = [], collections.Counter()
    prior_tok = None
    for r in out:
        d, k = r["domain"], nkey(r["company_name"])
        if d and d in prior_dom:
            rejects.append({**r, "reason": "already_held"}); ov[r["source"]] += 1; continue
        if k and k in prior_nm:
            rejects.append({**r, "reason": "already_held"}); ov[r["source"]] += 1; continue
        final.append(r)
    # ---- write
    cols = ["company_name", "domain", "domain_source", "city", "state_region", "phone", "email",
            "source", "profile_url", "first_seen_run", "notes"]
    with open(P["out_companies"], "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(final)
    with open(P["out_rejects"], "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols + ["reason"], extrasaction="ignore"); w.writeheader(); w.writerows(rejects)
    for rep in report:
        n = sum(1 for r in final if rep["source"] in r["source"].split(";"))
        rep["new_after_dedupe"] = n
        rep["overlap_pct"] = round(100 * ov[rep["source"]] / max(1, rep["rows_parsed"]), 1)
    with open(P["out_source_report"], "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["source", "tier", "attempted_pages", "rows_parsed", "with_domain",
                                          "new_after_dedupe", "overlap_pct", "barrier", "secs"])
        w.writeheader(); w.writerows(report)

    # ================================================================ SELF-AUDIT
    print("\n" + "=" * 96); print("SELF-AUDIT"); print("=" * 96)
    ok = True
    print(f"1. source report rows: {len(report)} (one per directory attempted)  "
          f"{'PASS' if len(report) else 'FAIL'}")
    bad = [r for r in final if r["domain"] and SOCIAL.search(r["domain"])]
    print(f"2. social/blocked domains in output: {len(bad)}  {'PASS' if not bad else 'FAIL'}"); ok &= not bad
    cons = len(final) + len(rejects) == total_parsed
    print(f"3. conservation: final {len(final)} + rejects {len(rejects)} == parsed {total_parsed}  "
          f"{'PASS' if cons else 'FAIL (' + str(total_parsed - len(final) - len(rejects)) + ' unaccounted)'}")
    fill = 100 * sum(1 for r in final if r["domain"]) / max(1, len(final))
    print(f"4. domain fill-rate overall: {fill:.1f}%")
    for rep in report:
        f_ = 100 * rep["with_domain"] / max(1, rep["rows_parsed"])
        flag = "  <-- LOW for a P1/P2 source, re-inspect parser" if (rep["tier"] in ("P1", "P2") and f_ < 50 and rep["rows_parsed"]) else ""
        print(f"     {rep['source']:<18}{rep['rows_parsed']:>6} parsed{rep['with_domain']:>7} dom {f_:>6.1f}%{flag}")
    guessed = [r for r in final if r["domain"] and r["domain_source"] not in ("listed", "profile", "redirect")]
    print(f"5. non-evidenced domains: {len(guessed)}  {'PASS' if not guessed else 'FAIL'}"); ok &= not guessed
    samp = [r for r in final if r["domain_source"] == "listed"][:15]
    hit = 0
    for r in samp:
        cp = cache_path(r["profile_url"])
        try:
            if r["domain"].split(".")[0] in gzip.open(cp, "rt", encoding="utf-8", errors="replace").read().lower(): hit += 1
        except Exception: pass
    print(f"6. sampled {len(samp)} 'listed' rows, domain found in cached HTML: {hit}/{len(samp)}")
    dd = collections.Counter(r["domain"] for r in final if r["domain"])
    dups = [d for d, c in dd.items() if c > 1]
    print(f"7. duplicate domains in output: {len(dups)}  {'PASS' if not dups else 'FAIL'}"); ok &= not dups
    print("=" * 96)
    print(f"\nTOTALS: {len(final)} companies | with domain {sum(1 for r in final if r['domain'])} | "
          f"backfill_needed {sum(1 for r in final if not r['domain'])} | rejects {len(rejects)}")
    print(f"outputs -> {P['out_companies']}")


if __name__ == "__main__":
    main()
