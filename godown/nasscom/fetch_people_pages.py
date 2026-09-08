# -*- coding: utf-8 -*-
"""Grab the team/leadership/about prose so an agent can read out the founder, not regex it.

Two regex passes at this produced "Insights Blogs Case", "View Full Bio" and "Human Resources"
as founder names. Marketing pages interleave names, titles, nav and body copy with no reliable
structure, so pattern matching cannot separate a person from a heading. An agent reading the
prose can, which is the same reason the relevance classifier is an agent.

Kept per company: text from team/leadership/about pages, plus every linkedin.com/in/ URL seen
with a little surrounding context — the URL is the one checkable artefact on the page and lets
the agent tie a name to a profile rather than inventing the pairing.

Usage: python3 fetch_people_pages.py [--workers 8] [--chars 3000]
"""
import os, re, sys, json, time, html, urllib.request
import concurrent.futures as cf

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "scoring_evidence.json")
OUT = os.path.join(HERE, "people_pages.json")
WORKERS, CHARS = 8, 3000
for i, a in enumerate(sys.argv):
    if a == "--src": SRC = os.path.join(HERE, sys.argv[i+1])
    if a == "--out": OUT = os.path.join(HERE, sys.argv[i+1])
    if a == "--workers": WORKERS = int(sys.argv[i+1])
    if a == "--chars": CHARS = int(sys.argv[i+1])

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
LI = re.compile(r"https?://(?:[a-z]{2,3}\.)?linkedin\.com/in/([A-Za-z0-9._%-]{3,60})", re.I)
KEY = re.compile(r"(founder|chief executive|\bceo\b|managing director|chairman|\bcto\b|"
                 r"leadership|proprietor|our team|management)", re.I)
EXTRA = ["/team", "/our-team", "/leadership", "/management", "/about-us", "/about", "/who-we-are"]


def get(u, t=12):
    r = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    with urllib.request.urlopen(r, timeout=t) as x:
        ct = (x.headers.get("Content-Type") or "").lower()
        if "html" not in ct and "text" not in ct: raise ValueError("not html")
        return x.read(700_000).decode(x.headers.get_content_charset() or "utf-8", "replace")


def text_of(h):
    h = re.sub(r"(?is)<(script|style|noscript|svg|nav|footer)[^>]*>.*?</\1>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def one(r):
    rec = {"name": r["name"], "domain": r.get("domain"), "linkedin_profiles": [],
           "pages": [], "text": ""}
    if r.get("error"): return rec
    base = (r.get("final_url") or r.get("website") or "").rstrip("/")
    m = re.match(r"(https?://[^/]+)", base)
    root = m.group(1) if m else base
    urls = [u for u in ((r.get("page_urls") or {}).get("team"),
                        (r.get("page_urls") or {}).get("about")) if u]
    urls += [root + p for p in EXTRA]
    chunks, seen = [], set()
    for u in urls[:5]:
        if u in seen: continue
        seen.add(u)
        try:
            h = get(u)
        except Exception:
            continue
        rec["pages"].append(u)
        for mm in LI.finditer(h):
            ctx = text_of(h[max(0, mm.start()-260): mm.end()+260])
            rec["linkedin_profiles"].append(
                {"url": f"https://www.linkedin.com/in/{mm.group(1)}", "context": ctx[:220]})
        t = text_of(h)
        # keep the parts of the page that talk about people
        keep = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\s{2,}", t)
                if 12 <= len(s.strip()) <= 300]
        hits = [s for s in keep if KEY.search(s)]
        chunks.append(" | ".join(hits[:25] if hits else keep[:15]))
        if sum(len(c) for c in chunks) > CHARS: break
        time.sleep(0.15)
    # dedupe profiles
    ded, s2 = [], set()
    for p in rec["linkedin_profiles"]:
        if p["url"].lower() in s2: continue
        s2.add(p["url"].lower()); ded.append(p)
    rec["linkedin_profiles"] = ded[:8]
    rec["text"] = " || ".join(chunks)[:CHARS]
    return rec


def main():
    rows = json.load(open(SRC, encoding="utf-8"))
    print(f"fetching people pages for {len(rows)} companies...", flush=True)
    out, t0 = [], time.time()
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for i, r in enumerate(ex.map(one, rows), 1):
            out.append(r)
            if i % 40 == 0: print(f"   {i}/{len(rows)}  {time.time()-t0:.0f}s", flush=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    usable = [r for r in out if len(r["text"]) > 200 or r["linkedin_profiles"]]
    print(f"\ndone in {time.time()-t0:.0f}s -> {os.path.basename(OUT)}")
    print(f"usable for agent extraction : {len(usable)}/{len(out)}")
    print(f"with >=1 linkedin profile   : {sum(1 for r in out if r['linkedin_profiles'])}")
    print(f"total linkedin profiles     : {sum(len(r['linkedin_profiles']) for r in out)}")

    os.makedirs(os.path.join(HERE, "people_batches"), exist_ok=True)
    per, n = 24, 0
    for i in range(0, len(usable), per):
        n += 1
        json.dump(usable[i:i+per],
                  open(os.path.join(HERE, "people_batches", f"pp_{n}.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    print(f"wrote {n} batches of {per} -> people_batches/")


main()
