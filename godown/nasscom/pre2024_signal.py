# -*- coding: utf-8 -*-
"""Tier GOLD: did this firm actually ship software BEFORE 2024?

A GitHub org settles it outright, but only 8 of 200 firms have one. The Wayback Machine covers
everybody, costs nothing and needs no key — and it answers a sharper question than a founding
year does. "Established 2011" proves a company existed; a 2022 snapshot of their own site
advertising custom software development proves they were BUILDING software then, which is the
actual claim being tested.

Two facts per company:
  first_snapshot   earliest capture of the domain. Later than 2024 is a red flag, not a neutral.
  pre2024_software a capture from before 2024-01-01 whose text already sells software work.
                   Fetched from the middle of the pre-2024 window, not the very first capture,
                   because an early snapshot is often a parked domain or a holding page.

Both are recorded even when negative, so the scoring agent can tell "no evidence" apart from
"evidence of the opposite" — the rubric treats those differently.

Also mines dated artefacts already crawled: blog and case-study dates that predate 2024.

Usage: python3 pre2024_signal.py [--src scoring_evidence.json] [--workers 6]
"""
import os, re, sys, json, time, html, collections, urllib.request, urllib.error
import concurrent.futures as cf

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "scoring_evidence.json")
OUT = os.path.join(HERE, "pre2024.json")
WORKERS = 2          # archive.org rate-limits aggressively; 6 workers got throttled to nothing
for i, a in enumerate(sys.argv):
    if a == "--src": SRC = os.path.join(HERE, sys.argv[i+1])
    if a == "--out": OUT = os.path.join(HERE, sys.argv[i+1])
    if a == "--workers": WORKERS = int(sys.argv[i+1])

UA = "Mozilla/5.0 (compatible; lh2-lead-research/1.0)"
# "we build software", not "we are a company"
BUILDS = re.compile(
    r"(custom software|software development|product engineering|application development|"
    r"web development|mobile app development|software solutions|we build|our product|"
    r"case stud|portfolio|our work|clients we|projects delivered|technolog(y|ies) we use|"
    r"\b(java|python|php|\.net|react|angular|node|android|ios)\b)", re.I)


def get(u, t=25, tries=4):
    """archive.org throttles hard. Retry with backoff and let the LAST failure raise, so a
    throttled request is never mistaken for an absent record — an earlier version swallowed
    every exception and reported 193 of 200 domains as 'never archived', which was simply
    six workers being rate limited."""
    last = None
    for a in range(tries):
        try:
            r = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "*/*"})
            with urllib.request.urlopen(r, timeout=t) as x:
                return x.read(700_000).decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 503, 504, 520, 522): time.sleep(4 * (a + 1)); continue
            raise
        except Exception as e:
            last = e; time.sleep(3 * (a + 1))
    raise last


def text_of(h):
    h = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h)))


def cdx(domain, frm=None, to=None, limit=1, rev=False):
    u = (f"http://web.archive.org/cdx/search/cdx?url={domain}&output=json"
         f"&fl=timestamp,original,statuscode&filter=statuscode:200&collapse=timestamp:6&limit={limit}")
    if frm: u += f"&from={frm}"
    if to: u += f"&to={to}"
    if rev: u += "&sort=reverse"
    try:
        d = json.loads(get(u))
        return d[1:] if len(d) > 1 else []
    except Exception as e:
        # surfaced, not swallowed: caller records it so "lookup failed" stays distinguishable
        # from "genuinely never archived"
        raise RuntimeError(f"cdx {type(e).__name__}") from e


def one(r):
    """ADAPTIVE, because archive.org's CDX endpoint runs 3-30s per query and three of them per
    company put the run at ~90 minutes.

    Wayback redirects /web/<date>/<url> to the nearest capture on its own, so the common case —
    the firm's site existed and was captured in 2023 — costs ONE request and simultaneously
    proves the domain predates 2024. Only when that misses do we spend a CDX call, and then
    solely to tell "no captures at all" apart from "captured, but not in that window"."""
    dom = r.get("domain") or ""
    out = {"name": r["name"], "domain": dom, "first_snapshot": None,
           "pre2024_software": False, "snapshot_used": None, "evidence": "", "note": ""}
    if not dom or r.get("error"): out["note"] = "site unreachable, not archived-checked"; return out

    for stamp in ("20230601", "20220601", "20200601"):
        try:
            raw = get(f"https://web.archive.org/web/{stamp}id_/http://{dom}/", tries=2)
        except Exception:
            continue
        t = text_of(raw)
        if len(t) < 300: continue
        out["snapshot_used"] = stamp
        out["first_snapshot"] = "pre-" + stamp        # a capture here proves it predates 2024
        m = BUILDS.search(t)
        if m:
            i = m.start()
            out["pre2024_software"] = True
            out["evidence"] = re.sub(r"\s+", " ", t[max(0, i-60):i+90]).strip()[:150]
        else:
            out["note"] = "archived pre-2024 but page did not mention building software"
        return out

    # nothing fetchable in any pre-2024 window — now it is worth one CDX call to find out why
    try:
        first = cdx(dom, limit=1)
    except RuntimeError as e:
        out["note"] = f"LOOKUP FAILED ({e}) — NOT evidence of absence"; return out
    if not first:
        out["note"] = "no wayback capture at all"; return out
    out["first_snapshot"] = first[0][0][:8]
    if out["first_snapshot"] >= "20240101":
        out["note"] = "domain first archived 2024 or later — RED FLAG"
    else:
        out["note"] = "captured pre-2024 but no snapshot fetchable to read"
    return out


def main():
    rows = json.load(open(SRC, encoding="utf-8"))
    done = {}
    if os.path.exists(OUT):
        done = {x["domain"]: x for x in json.load(open(OUT, encoding="utf-8"))}
    todo = [r for r in rows if r.get("domain") not in done]
    print(f"{len(rows)} companies | {len(done)} already checked | {len(todo)} to check", flush=True)
    out, t0 = list(done.values()), time.time()
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for i, r in enumerate(ex.map(one, todo), 1):
            out.append(r)
            if i % 20 == 0:
                print(f"   {i}/{len(todo)}  {time.time()-t0:.0f}s", flush=True)
                json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"\ndone in {time.time()-t0:.0f}s -> {os.path.basename(OUT)}")
    gold = [r for r in out if r["pre2024_software"]]
    red = [r for r in out if r["first_snapshot"] and r["first_snapshot"] >= "20240101"]
    none_ = [r for r in out if not r["first_snapshot"]]
    print(f"\nTIER GOLD — pre-2024 software evidence : {len(gold)}/{len(out)}")
    print(f"RED FLAG  — domain first archived 2024+: {len(red)}")
    print(f"no wayback capture at all              : {len(none_)}")
    yrs = collections.Counter(r["first_snapshot"][:4] for r in out if r["first_snapshot"])
    print("\nfirst-archived year:")
    for y, n in sorted(yrs.items()): print(f"   {y}  {'#'*min(n,40)} {n}")
    if red:
        print("\nthe 2024+ ones (treat as red flags):")
        for r in red[:15]: print(f"   {r['name'][:44]:<46}{r['first_snapshot']}")


main()
