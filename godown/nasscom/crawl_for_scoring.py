# -*- coding: utf-8 -*-
"""Gather the evidence filterInstructions.md asks for, per company.

Step 1 of the rubric is explicit that most real signal lives OFF the homepage, so this fetches
/, careers|jobs, blog, about, team, tech-stack and scans the footer for VCS/social links. Pages
are discovered from the site's own nav first and only then guessed at common paths, because a
guessed /careers that 404s is not the same as a site with no careers page — and the rubric caps
score on "no careers AND no blog AND no team", so that distinction changes the number.

`pages_reached` is recorded verbatim, as the rubric requires.

Evidence is EXCERPTED, not dumped: sentences matching the rubric's own signal families, so the
scoring agent reads the relevant prose rather than 40k of nav boilerplate. Disqualifier families
(SEO/PPC bundling, helpdesk, MVP-in-N-days, template shops) are excerpted too — a cap can only
be applied fairly if the evidence for it survives the trim.

VCS links are collected here but NOT judged here: a github.com/<org> link in a footer is not
"visible merged PRs with multiple contributors". verify_vcs.py checks that against the API.

Usage: python3 crawl_for_scoring.py [--src nasscom_sample_200.csv] [--workers 10]
"""
import os, re, sys, csv, json, time, html, collections, urllib.request, urllib.error
import concurrent.futures as cf

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "nasscom_sample_200.csv")
OUT = os.path.join(HERE, "scoring_evidence.json")
WORKERS, LIMIT = 10, 0
for i, a in enumerate(sys.argv):
    if a == "--src": SRC = os.path.join(HERE, sys.argv[i+1])
    if a == "--out": OUT = os.path.join(HERE, sys.argv[i+1])
    if a == "--workers": WORKERS = int(sys.argv[i+1])
    if a == "--limit": LIMIT = int(sys.argv[i+1])

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# what to look for, and under which rubric line it counts
WANT = {
  "careers":    r"(career|jobs?|join-?us|work-with-us|we-?are-?hiring|openings|life-at)",
  "blog":       r"(blog|insights|articles|resources/blog|tech-?blog|engineering)",
  "about":      r"(about|who-we-are|our-story|company)",
  "team":       r"(team|leadership|our-people|management)",
  "tech-stack": r"(tech-?stack|technolog|expertise|capabilit|how-we-work|process|methodolog)",
}
FALLBACK = {"careers": ["/careers", "/career", "/jobs"], "blog": ["/blog", "/insights"],
            "about": ["/about", "/about-us"], "team": ["/team", "/leadership"],
            "tech-stack": ["/technologies", "/tech-stack", "/expertise"]}

SIGNALS = [
 ("pr_practice",  r"(code review|peer review|pull request|merge request|\bPR\b review|branching strateg|trunk[- ]based|git ?flow|version control|code quality gate)"),
 ("vcs",          r"\b(github|gitlab|bitbucket|\bgit\b)\b"),
 ("cicd",         r"(ci/?cd|continuous integration|continuous delivery|continuous deployment|jenkins|circleci|github actions|gitlab ci|azure devops|argo ?cd|terraform|infrastructure as code|\biac\b|kubernetes|docker|ansible|helm|pipeline)"),
 ("qa",           r"(test automation|automated test|unit test|shift[- ]left|selenium|cypress|playwright|jest|junit|pytest|\bqa\b|quality engineering|test[- ]driven)"),
 ("compliance",   r"(soc ?2|iso ?27001|iso ?9001|cmmi|hipaa|gdpr|pci ?dss)"),
 ("prod_eng",     r"(product engineering|platform engineering|engineering excellence)"),
 ("owns_product", r"(our product|our platform|accelerator|proprietary (platform|product|framework)|saas product|product suite)"),
 ("senior_roles", r"(staff engineer|principal engineer|vp of engineering|vp engineering|head of engineering|site reliability|\bsre\b|solution architect|technical architect|engineering manager|tech lead)"),
 ("enterprise",   r"(fortune 500|fortune500|enterprise client|regulated|bfsi|banking|insurance|healthcare|nasdaq|listed company)"),
 ("sdlc",         r"(sdlc|how we work|our process|engagement model|agile|scrum|sprint|kanban|devops practice)"),
 ("DQ_agency",    r"(\bseo\b|\bppc\b|\bsmm\b|social media marketing|content marketing|digital marketing|link building|google ads|branding)"),
 ("DQ_support",   r"(helpdesk|help desk|it support|\bamc\b|networking solutions|hardware|cctv|annual maintenance|managed print|desktop support)"),
 ("DQ_template",  r"(mvp in \d+ (days|weeks)|guaranteed delivery|website builder|template|wordpress theme|readymade|ready-made|clone script)"),
 ("DQ_bpo",       r"(\bbpo\b|\bkpo\b|data entry|transcription|call cent|back ?office|telecalling)"),
 ("DQ_training",  r"(training institute|certification course|placement|internship program|bootcamp|coaching)"),
]
VCS_RX = re.compile(r"https?://(?:www\.)?(github\.com|gitlab\.com|bitbucket\.org)/([A-Za-z0-9._-]{2,40})", re.I)
BLOG_RX = re.compile(r"https?://(?:www\.)?(medium\.com/@?[A-Za-z0-9._-]{2,40}|dev\.to/[A-Za-z0-9._-]{2,40})", re.I)
SKIP_ORG = {"features", "about", "pricing", "login", "signup", "explore", "topics", "collections",
            "marketplace", "sponsors", "readme", "site", "orgs", "apps", "settings", "search"}


def get(u, t=12):
    r = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "text/html,*/*",
                                           "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(r, timeout=t) as x:
        ct = (x.headers.get("Content-Type") or "").lower()
        if "html" not in ct and "text" not in ct: raise ValueError("not html")
        return x.geturl(), x.read(800_000).decode(x.headers.get_content_charset() or "utf-8", "replace")


def text_of(h):
    h = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def root(u):
    m = re.match(r"(https?://[^/]+)", u); return m.group(1) if m else u


def discover(base, h):
    """Site's own nav first — a guessed path that 404s must not look like a missing page."""
    found = {}
    for m in re.finditer(r'href=["\']([^"\'#]{1,200})["\']', h, re.I):
        u = m.group(1)
        if u.startswith(("mailto:", "tel:", "javascript:")): continue
        full = u if u.startswith("http") else (root(base) + u if u.startswith("/") else "")
        if not full or root(full) != root(base): continue
        for k, rx in WANT.items():
            if k not in found and re.search(rx, u, re.I): found[k] = full
    return found


def excerpt(t):
    """Sentences carrying rubric signals. Keeps the disqualifier families too — a cap has to be
    justifiable from the same evidence bundle the score is."""
    out, hits = collections.defaultdict(list), collections.Counter()
    for s in re.split(r"(?<=[.!?])\s+|\s\|\s|\s•\s", t):
        s = s.strip()
        if not (25 <= len(s) <= 320): continue
        for k, rx in SIGNALS:
            if re.search(rx, s, re.I):
                hits[k] += 1
                if len(out[k]) < 4 and s not in out[k]: out[k].append(s)
    return dict(out), dict(hits)


def one(row):
    site = (row.get("website") or "").strip()
    if not site.startswith("http"): site = "http://" + site
    rec = {"name": row["name"], "city": row.get("city", ""), "domain": row.get("domain", ""),
           "website": site, "pages_reached": [], "pages_missing": [], "vcs": [], "blogs": [],
           "evidence": {}, "signal_counts": {}}
    try:
        final, h = get(site)
    except Exception as e:
        try:
            final, h = get(site.replace("http://", "https://", 1))
        except Exception as e2:
            rec["error"] = type(e2).__name__; return rec
    rec["final_url"] = final; rec["pages_reached"].append("/")
    pages = {"/": h}
    found = discover(final, h)
    for k in WANT:
        url = found.get(k)
        tried = [url] if url else [root(final) + p for p in FALLBACK[k]]
        got = False
        for u in tried[:3]:
            try:
                fu, hh = get(u)
                if len(text_of(hh)) < 200: continue
                pages[k] = hh; rec["pages_reached"].append(k)
                rec.setdefault("page_urls", {})[k] = fu
                got = True; break
            except Exception:
                continue
        if not got: rec["pages_missing"].append(k)
    alltext, allhtml = [], []
    for k, hh in pages.items():
        allhtml.append(hh); alltext.append(text_of(hh))
    joined = " ".join(alltext); rawhtml = " ".join(allhtml)
    for host, org in VCS_RX.findall(rawhtml):
        if org.lower() in SKIP_ORG: continue
        u = f"https://{host}/{org}"
        if u not in rec["vcs"]: rec["vcs"].append(u)
    rec["blogs"] = sorted(set(f"https://{m}" for m in BLOG_RX.findall(rawhtml)))[:3]
    rec["evidence"], rec["signal_counts"] = excerpt(joined)
    rec["text_len"] = len(joined)
    return rec


def main():
    rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
    if LIMIT: rows = rows[:LIMIT]
    print(f"crawling {len(rows)} companies x up to 6 pages, {WORKERS} workers...", flush=True)
    out, t0 = [], time.time()
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for i, r in enumerate(ex.map(one, rows), 1):
            out.append(r)
            if i % 20 == 0:
                print(f"   {i}/{len(rows)}  {time.time()-t0:.0f}s", flush=True)
                json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    ok = [r for r in out if not r.get("error")]
    print(f"\ndone in {time.time()-t0:.0f}s -> {os.path.basename(OUT)}")
    print(f"reachable: {len(ok)}/{len(out)}")
    pc = collections.Counter()
    for r in ok:
        for p in r["pages_reached"]: pc[p] += 1
    print("\npages actually reached:")
    for k, n in pc.most_common(): print(f"   {n:>4}  {k}")
    print(f"\ncompanies with a VCS org link : {sum(1 for r in ok if r['vcs'])}")
    print(f"companies with medium/dev.to  : {sum(1 for r in ok if r['blogs'])}")
    nb = sum(1 for r in ok if "careers" not in r["pages_reached"]
             and "blog" not in r["pages_reached"] and "team" not in r["pages_reached"])
    print(f"no careers AND no blog AND no team (rubric caps at 40): {nb}")
    sc = collections.Counter()
    for r in ok:
        for k in r["signal_counts"]: sc[k] += 1
    print("\ncompanies showing each signal family:")
    for k, n in sc.most_common(): print(f"   {n:>4}  {k}")


main()
