# -*- coding: utf-8 -*-
"""Pull a readable text snippet per company so an agent can judge what regexes cannot.

read_sites.py records only which patterns matched. That is enough to separate the obvious
cases but leaves ~45% "ambiguous", and a keyword list genuinely cannot tell a firm that
BUILDS software from one that merely SELLS or USES it. The agent needs prose.

Homepage plus a services/about page, stripped to text, trimmed to a budget that keeps a
batch of companies inside one agent's context.

Usage: python3 fetch_snippets.py [--src site_reads.json] [--limit 150] [--chars 2600]
"""
import os, re, sys, json, time, html, urllib.request
import concurrent.futures as cf

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "site_reads.json")
OUT = os.path.join(HERE, "snippets.json")
LIMIT, CHARS, WORKERS = 0, 2600, 12
ONLY = ("software_dev", "ambiguous")
for i, a in enumerate(sys.argv):
    if a == "--src": SRC = os.path.join(HERE, sys.argv[i+1])
    if a == "--out": OUT = os.path.join(HERE, sys.argv[i+1])
    if a == "--limit": LIMIT = int(sys.argv[i+1])
    if a == "--chars": CHARS = int(sys.argv[i+1])
    if a == "--only": ONLY = tuple(sys.argv[i+1].split(","))

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def text_of(h):
    h = re.sub(r"(?is)<(script|style|noscript|svg|header|footer|nav)[^>]*>.*?</\1>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def get(u, t=14):
    r = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    with urllib.request.urlopen(r, timeout=t) as x:
        return x.geturl(), x.read(700_000).decode(x.headers.get_content_charset() or "utf-8", "replace")


def second_page(base, h):
    """Prefer a services page — it states what they actually do far more plainly than /about."""
    best = ""
    for m in re.finditer(r'href=["\']([^"\']{1,180})["\']', h, re.I):
        u = m.group(1)
        if re.search(r"(service|what-we-do|expertise|capabilit|solutions|product)", u, re.I):
            best = u; break
        if not best and re.search(r"(about|company|who-we-are)", u, re.I):
            best = u
    if not best: return ""
    if best.startswith("http"): return best
    if best.startswith("/"): return re.match(r"(https?://[^/]+)", base).group(1) + best
    return ""


def one(r):
    site = r.get("final_url") or r["website"]
    try:
        final, h = get(site)
    except Exception:
        return None
    t = text_of(h)
    sp = second_page(final, h)
    if sp:
        try: t += " || " + text_of(get(sp)[1])
        except Exception: pass
    # Repeated nav/boilerplate is collapsed by dropping duplicate sentences. A backreference
    # pattern like (.{40,}?)\1{2,} expresses this in one line and backtracks catastrophically
    # on page-length text — it hung 150 fetches for ten minutes without emitting a single row.
    seen, keep = set(), []
    for part in re.split(r"(?<=[.!?])\s+|\s\|\s", t):
        k = part.strip().lower()
        if len(k) < 12 or k in seen: continue
        seen.add(k); keep.append(part.strip())
    t = " ".join(keep)
    return {"name": r["name"], "domain": r["domain"], "city": r.get("city", ""),
            "heuristic": r.get("verdict"), "prod_or_serv": r.get("prod_or_serv"),
            "founded_year": r.get("founded_year"), "text": t[:CHARS]}


def main():
    rows = [r for r in json.load(open(SRC, encoding="utf-8")) if r.get("verdict") in ONLY]
    if LIMIT: rows = rows[::max(1, len(rows)//LIMIT)][:LIMIT]
    print(f"fetching snippets for {len(rows)} companies...", flush=True)
    out, t0 = [], time.time()
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for i, r in enumerate(ex.map(one, rows), 1):
            if r and len(r["text"]) > 300: out.append(r)
            if i % 40 == 0: print(f"   {i}/{len(rows)}  {time.time()-t0:.0f}s", flush=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n{len(out)} usable snippets in {time.time()-t0:.0f}s -> {os.path.basename(OUT)}")
    print(f"median length: {sorted(len(r['text']) for r in out)[len(out)//2] if out else 0} chars")


main()
