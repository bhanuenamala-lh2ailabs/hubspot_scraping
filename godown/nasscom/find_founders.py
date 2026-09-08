# -*- coding: utf-8 -*-
"""Founder / Co-founder / CEO per company, WITHOUT spending a SignalHire search.

The usual route (searchByQuery on currentCompany + founder titles) costs one search per firm and
the daily pool is exhausted. These firms publish the same fact themselves: 135 of the 200 have a
team or about page, and those pages routinely carry a name, a title and a personal LinkedIn link.

Sources, strongest first:
  1. a linkedin.com/in/ link sitting next to a founder-ish title  -> highest confidence, because
     the profile URL is checkable and cannot be a mis-parsed heading
  2. a person name adjacent to a founder-ish title in page text
  3. nothing found -> recorded as such, so it can go to SignalHire or MCA later

WHY NAME EXTRACTION IS CONSERVATIVE HERE. "Solutions Pvt Ltd" and "Our Leadership Team" both look
like capitalised name sequences. A wrong founder name is worse than a blank one — it reaches a
caller who greets a stranger by it — so a candidate must be 2-3 capitalised words, must not
contain a corporate or nav word, and must sit within a short window of the title. Anything else
is dropped rather than guessed.

Usage: python3 find_founders.py [--src scoring_evidence.json] [--workers 8]
"""
import os, re, sys, json, time, html, collections, urllib.request
import concurrent.futures as cf

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "scoring_evidence.json")
OUT = os.path.join(HERE, "founders.json")
WORKERS = 8
for i, a in enumerate(sys.argv):
    if a == "--src": SRC = os.path.join(HERE, sys.argv[i+1])
    if a == "--out": OUT = os.path.join(HERE, sys.argv[i+1])
    if a == "--workers": WORKERS = int(sys.argv[i+1])

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# "Partner" is deliberately absent: on a services site it almost always means "AWS Partner" or
# "our partners", and it produced 67 false hits — more than founder and co-founder combined.
TITLE = re.compile(r"\b(co[- ]?founder|founder|chief executive officer|\bceo\b|managing director|"
                   r"chairman|chairperson|chief technology officer|\bcto\b|proprietor)\b", re.I)
RANK = ["founder", "co-founder", "cofounder", "ceo", "chief executive", "managing director",
        "chairman", "cto", "proprietor"]
# Any of these inside a capitalised run proves it is not a person's name. The first run of this
# script returned "Insights Blogs Case", "Executive Vice Preside" and "American University" as
# founder names because the list only covered corporate words, not job-title and nav vocabulary.
NOTNAME = re.compile(r"\b(pvt|private|limited|ltd|llp|inc|solutions?|technolog\w*|systems?|services?|"
                     r"software|labs?|group|india|global|consulting|infotech|team|leadership|"
                     r"management|board|about|our|the|meet|company|contact|home|careers?|read|more|"
                     r"message|vision|mission|values|why|what|who|how|we|us|clients?|partners?|"
                     r"privacy|policy|terms|copyright|rights|reserved|"
                     r"founder|cofounder|ceo|cto|coo|cfo|chairman|chairperson|president|vice|"
                     r"executive|officer|chief|director|manager|head|lead|senior|principal|"
                     r"associate|advisory|insights?|blogs?|case|studies|study|university|college|"
                     r"certified|markets?|issuers?|wealth|consumer|banking|digital|business|data|"
                     r"cloud|\bai\b|analytics|engineering|products?|platform|news|events?|awards?|"
                     r"testimonial|overview|profile|story|journey|founded|experience|years?)\b", re.I)
NAME = re.compile(r"\b([A-Z][a-z]{1,15}(?:\s+[A-Z][a-z.]{1,15}){1,2})\b")
LI = re.compile(r"https?://(?:[a-z]{2,3}\.)?linkedin\.com/in/([A-Za-z0-9._%-]{3,60})", re.I)
EXTRA = ["/team", "/our-team", "/leadership", "/management", "/about-us", "/about",
         "/company/leadership", "/who-we-are"]


def get(u, t=12):
    r = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    with urllib.request.urlopen(r, timeout=t) as x:
        ct = (x.headers.get("Content-Type") or "").lower()
        if "html" not in ct and "text" not in ct: raise ValueError("not html")
        return x.read(700_000).decode(x.headers.get_content_charset() or "utf-8", "replace")


def text_of(h):
    h = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h)))


def plausible(n):
    """Strict on purpose. Recall lost here is recoverable later from SignalHire or MCA; a wrong
    name is not recoverable — it reaches a caller who greets a stranger by it."""
    if NOTNAME.search(n): return False
    if TITLE.search(n): return False
    parts = n.split()
    if not (2 <= len(parts) <= 3): return False
    for p in parts:
        p = p.strip(".")
        if len(p) < 2 and not p.isupper(): return False      # allow an initial like "R."
        if not re.fullmatch(r"[A-Za-z]{1,15}", p): return False
    return True


def rank_of(t):
    tl = t.lower()
    for i, k in enumerate(RANK):
        if k in tl: return i
    return len(RANK)


def from_html(h):
    """LinkedIn-anchored first: a /in/ link next to a founder title is the checkable case."""
    out = []
    for m in LI.finditer(h):
        s, e = max(0, m.start() - 700), min(len(h), m.end() + 700)
        win = text_of(h[s:e])
        tm = TITLE.search(win)
        if not tm: continue
        seg = win[max(0, tm.start() - 90): tm.start() + 90]
        cands = [c for c in NAME.findall(seg) if plausible(c)]
        out.append({"name": cands[0] if cands else "", "title": tm.group(0),
                    "linkedin": f"https://www.linkedin.com/in/{m.group(1)}",
                    "how": "linkedin link beside title", "rank": rank_of(tm.group(0))})
    return out


def from_text(t):
    out = []
    for tm in TITLE.finditer(t):
        seg = t[max(0, tm.start() - 110): tm.start() + 110]
        for c in NAME.findall(seg):
            if plausible(c):
                out.append({"name": c, "title": tm.group(0), "linkedin": "",
                            "how": "name beside title in page text", "rank": rank_of(tm.group(0))})
                break
    return out


def one(r):
    rec = {"name": r["name"], "domain": r.get("domain"), "people": [], "pages_used": []}
    if r.get("error"): rec["note"] = "site unreachable"; return rec
    base = (r.get("final_url") or r.get("website") or "").rstrip("/")
    root = re.match(r"(https?://[^/]+)", base)
    root = root.group(1) if root else base
    urls = []
    for k in ("team", "about"):
        u = (r.get("page_urls") or {}).get(k)
        if u: urls.append(u)
    urls += [root + p for p in EXTRA]
    seen_url, found = set(), []
    for u in urls[:6]:
        if u in seen_url: continue
        seen_url.add(u)
        try:
            h = get(u)
        except Exception:
            continue
        rec["pages_used"].append(u)
        found += from_html(h)
        if not found: found += from_text(text_of(h))
        if any(p["rank"] <= 2 for p in found): break   # a real founder/CEO hit; stop crawling
        time.sleep(0.2)
    best, seen = [], set()
    for p in sorted(found, key=lambda x: (x["rank"], not x["linkedin"])):
        k = (p["name"].lower(), p["linkedin"].lower())
        if k in seen: continue
        seen.add(k)
        if p["name"] or p["linkedin"]: best.append(p)
        if len(best) >= 4: break
    rec["people"] = best
    if not best: rec["note"] = "no founder/CEO found on site"
    return rec


def main():
    rows = json.load(open(SRC, encoding="utf-8"))
    done = {}
    if os.path.exists(OUT):
        done = {x["domain"]: x for x in json.load(open(OUT, encoding="utf-8"))}
    todo = [r for r in rows if r.get("domain") not in done]
    print(f"{len(rows)} companies | {len(done)} done | {len(todo)} to search", flush=True)
    out, t0 = list(done.values()), time.time()
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for i, r in enumerate(ex.map(one, todo), 1):
            out.append(r)
            if i % 25 == 0:
                print(f"   {i}/{len(todo)}  {time.time()-t0:.0f}s", flush=True)
                json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    got = [r for r in out if r["people"]]
    withli = [r for r in got if any(p["linkedin"] for p in r["people"])]
    named = [r for r in got if any(p["name"] for p in r["people"])]
    print(f"\ndone in {time.time()-t0:.0f}s -> {os.path.basename(OUT)}")
    print(f"companies with a person found : {len(got)}/{len(out)}")
    print(f"   ...with a LinkedIn profile : {len(withli)}")
    print(f"   ...with a name             : {len(named)}")
    tt = collections.Counter(p["title"].lower() for r in got for p in r["people"])
    print("\ntitles found:")
    for k, n in tt.most_common(10): print(f"   {n:>4}  {k}")
    print("\nsample:")
    for r in got[:15]:
        p = r["people"][0]
        print(f"   {r['name'][:34]:<36}{(p['name'] or '-')[:22]:<24}{p['title'][:18]:<20}{p['linkedin'][:44]}")


main()
