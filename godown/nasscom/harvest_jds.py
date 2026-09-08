# -*- coding: utf-8 -*-
"""Harvest actual job-description text — the primary evidence under the revised rubric.

WHY THIS EXISTS. Public repos are no longer scored: we are buying a codebase that has never been
public, so a public org proves the wrong thing, and only 4 firms in 200 had one anyway. The
signal that replaced it is what a firm tells its own engineers about working on its PRIVATE
repositories — and that lives in job descriptions.

The catch is that most firms do not put JD text on their own careers page; they link out to
Greenhouse, Lever, Workable, Zoho Recruit, Keka or Naukri. A careers blurb saying "join our
dynamic team" is marketing copy and scores nothing. So this follows the link.

What it looks for, in order of what it proves:
  PRIVATE-REPO HOST  bitbucket, azure devops, tfs, self-hosted gitlab, codecommit
                     -> nobody hosts open source on these; near-proof of private repos
  REVIEW GATE        raise a PR, review pull requests, merge request, peer review, code review,
                     branching strategy, gitflow, trunk-based
  QUALITY GATE       sonarqube, coverage threshold, definition of done
  CI/CD              jenkins, github actions, gitlab ci, azure pipelines, circleci, teamcity

Every match is stored with the sentence around it, so a score can be justified from the JD's own
words rather than a keyword count.

Usage: python3 harvest_jds.py [--src full_evidence.json] [--workers 10]
"""
import os, re, sys, json, time, html, collections, urllib.request
import concurrent.futures as cf

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "full_evidence.json")
OUT = os.path.join(HERE, "jd_evidence.json")
WORKERS, LIMIT = 10, 0
for i, a in enumerate(sys.argv):
    if a == "--src": SRC = os.path.join(HERE, sys.argv[i+1])
    if a == "--out": OUT = os.path.join(HERE, sys.argv[i+1])
    if a == "--workers": WORKERS = int(sys.argv[i+1])
    if a == "--limit": LIMIT = int(sys.argv[i+1])

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

BOARDS = re.compile(r"(boards\.greenhouse\.io|jobs\.lever\.co|\.workable\.com|\.recruitee\.com|"
                    r"zohorecruit\.|\.keka\.com|\.darwinbox\.|smartrecruiters\.com|"
                    r"jobs\.ashbyhq\.com|\.freshteam\.com|naukri\.com|\.peoplehum\.|"
                    r"\.hirist\.|instahyre\.com|\.zwayam\.|\.talentrecruit\.|"
                    # Romanian / CEE boards. Without these the Romania run found real careers text
                    # on only 36% of firms and just one Tier A — not because those firms hire
                    # loosely, but because this market advertises on local boards rather than on
                    # its own careers pages. A missing board pattern reads as a missing signal.
                    r"ejobs\.ro|bestjobs\.eu|hipo\.ro|undelucram\.ro|jobradar\.ro|"
                    r"peviitor\.ro|angajatorulmeu\.ro|catalog\.jobs|"
                    r"linkedin\.com/jobs|indeed\.com|glassdoor\.|europeanjobdays)", re.I)
# English plus Romanian: cariere/joburi/locuri-de-munca/alatura-te are what these sites actually use,
# and a careers page missed for language reasons looks identical to a firm that has none.
CAREER_PATH = re.compile(r"(career|cariere|job|joburi|vacan|opening|hiring|join|alatura|"
                         r"locuri-de-munca|work-with|life-at|we-are-hiring|echipa|recrut)", re.I)

SIGNALS = {
  "private_repo_host": r"\b(bitbucket|azure\s*devops|\bvsts\b|\btfs\b|team\s*foundation|"
                       r"self[- ]hosted\s*gitlab|gitlab\s*(ce|ee|server)|codecommit|"
                       r"on[- ]prem(ise)?\s*(git|repo))\b",
  "review_gate":       r"(raise\s+a?\s*pull\s*request|raising\s+prs?|review\s+pull\s*requests?|"
                       r"\bpull\s*requests?\b|\bmerge\s*requests?\b|peer\s*review|code\s*review|"
                       r"branching\s*strateg|git\s*flow|gitflow|trunk[- ]based|"
                       r"reviewing\s+code|code\s+reviews)",
  "quality_gate":      r"(sonarqube|sonar\s*cloud|code\s*quality\s*gate|coverage\s*(threshold|target|>|%)|"
                       r"definition\s*of\s*done|static\s*(code\s*)?analysis|lint(ing)?\s*rules)",
  "cicd":              r"(jenkins|github\s*actions|gitlab\s*ci|azure\s*pipelines|circleci|teamcity|"
                       r"bamboo|argo\s*cd|\bci/?cd\b|continuous\s+(integration|delivery|deployment))",
  "vcs_generic":       r"\b(git|github|version\s*control|source\s*control)\b",
  "testing":           r"(unit\s*test|integration\s*test|test\s*automation|tdd\b|junit|pytest|jest|"
                       r"selenium|cypress|playwright)",
}
COMPILED = {k: re.compile(v, re.I) for k, v in SIGNALS.items()}


def get(u, t=14):
    r = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "text/html,*/*",
                                           "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(r, timeout=t) as x:
        ct = (x.headers.get("Content-Type") or "").lower()
        if "html" not in ct and "text" not in ct and "json" not in ct: raise ValueError("not text")
        return x.geturl(), x.read(900_000).decode(x.headers.get_content_charset() or "utf-8", "replace")


def text_of(h):
    h = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h)))


def sentences(t):
    return [s.strip() for s in re.split(r"(?<=[.!?;:])\s+|\s\|\s|•", t) if 20 <= len(s.strip()) <= 320]


def one(r):
    rec = {"name": r["name"], "domain": r.get("domain", ""), "pages_read": [],
           "job_boards": [], "signals": {}, "quotes": {}, "jd_chars": 0}
    if r.get("error"): return rec
    base = r.get("final_url") or r.get("website") or ""
    m = re.match(r"(https?://[^/]+)", base)
    root = m.group(1) if m else base
    if not root: return rec

    # 1. the careers page the crawler already found, else guess
    urls = []
    cu = (r.get("page_urls") or {}).get("careers")
    if cu: urls.append(cu)
    urls += [root + p for p in ("/careers", "/career", "/jobs", "/join-us", "/we-are-hiring", "/openings", "/cariere", "/joburi", "/alatura-te", "/locuri-de-munca", "/en/careers", "/company/careers")]

    seen, texts = set(), []
    for u in urls[:5]:
        if u in seen: continue
        seen.add(u)
        try:
            fu, h = get(u)
        except Exception:
            continue
        rec["pages_read"].append(fu)
        texts.append(text_of(h))
        # 2. follow links OFF the careers page: individual roles and external boards
        links = []
        for mm in re.finditer(r'href=["\']([^"\'#]{3,300})["\']', h, re.I):
            l = mm.group(1)
            full = l if l.startswith("http") else (root + l if l.startswith("/") else "")
            if not full: continue
            if BOARDS.search(full):
                links.append(full)
                if full not in rec["job_boards"]: rec["job_boards"].append(full)
            elif full.startswith(root) and CAREER_PATH.search(full) and full not in seen:
                links.append(full)
        for l in links[:6]:
            if l in seen: continue
            seen.add(l)
            try:
                fu2, h2 = get(l)
            except Exception:
                continue
            rec["pages_read"].append(fu2)
            texts.append(text_of(h2))
            if sum(len(t) for t in texts) > 120_000: break
        if sum(len(t) for t in texts) > 120_000: break
        time.sleep(0.1)

    joined = " ".join(texts)
    rec["jd_chars"] = len(joined)
    sents = sentences(joined)
    for k, rx in COMPILED.items():
        hits = [s for s in sents if rx.search(s)]
        if hits:
            rec["signals"][k] = len(hits)
            rec["quotes"][k] = hits[:3]
    return rec


def main():
    rows = json.load(open(SRC, encoding="utf-8"))
    done = {}
    if os.path.exists(OUT):
        done = {x["domain"]: x for x in json.load(open(OUT, encoding="utf-8"))}
    todo = [r for r in rows if r.get("domain") not in done]
    if LIMIT: todo = todo[:LIMIT]
    print(f"{len(rows)} firms | {len(done)} already harvested | {len(todo)} to do", flush=True)

    out, t0 = list(done.values()), time.time()
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for i, r in enumerate(ex.map(one, todo), 1):
            out.append(r)
            if i % 50 == 0:
                json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                got = sum(1 for x in out if x["signals"].get("private_repo_host"))
                print(f"   {i}/{len(todo)}  {time.time()-t0:.0f}s   private-repo-host hits so far: {got}", flush=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"\ndone in {time.time()-t0:.0f}s -> {os.path.basename(OUT)}")
    withjd = [x for x in out if x["jd_chars"] > 1500]
    print(f"firms with real careers/JD text : {len(withjd)}/{len(out)}")
    print(f"firms linking an external board : {sum(1 for x in out if x['job_boards'])}")
    print("\nsignal coverage:")
    for k in SIGNALS:
        n = sum(1 for x in out if x["signals"].get(k))
        print(f"   {n:>5}  {k}")
    both = [x for x in out if x["signals"].get("private_repo_host") and x["signals"].get("review_gate")]
    print(f"\nTIER A (+40) — private-repo host AND a review gate : {len(both)}")
    for x in both[:20]:
        q = (x["quotes"].get("private_repo_host") or [""])[0]
        print(f"   {x['name'][:38]:<40}{q[:76]}")


main()
