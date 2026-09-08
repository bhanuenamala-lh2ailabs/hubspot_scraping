# -*- coding: utf-8 -*-
"""Pass 2 for the wrong-SPOC blanks — DDG throttled pass 1 into 12 false 'not found's.

Evidence it was the engine, not reality: every local-source hit (cache, site scrape)
succeeded while 12 consecutive DDG-dependent rows returned nothing — including firms whose
leadership is trivially public. Zero without verification is not a finding.

This pass: 10s pacing on DDG, Bing HTML as an independent keyless engine, and for the
name-only rows a targeted '<name> <company> linkedin' search to convert names into reveal
keys. Only rows with action in (not found, name-only) are retouched.
"""
import os, re, sys, json, time, urllib.request, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "right_spoc_found.json")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
SENIOR = re.compile(r"founder|co[- ]?founder|ceo|cto|chief|managing director|\bmd\b|owner|director|president", re.I)


def fetch(url):
    try:
        r = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(r, timeout=15) as x:
            return x.read(500_000).decode("utf-8", "replace")
    except Exception:
        return ""


def bing(q):
    h = fetch("https://www.bing.com/search?q=" + urllib.parse.quote(q))
    out = re.findall(r'<h2><a href="(https?://[^"]+)"[^>]*>(.*?)</a>', h, re.S)
    time.sleep(4)
    return [(re.sub(r"<[^>]+>", "", t)[:90], u) for u, t in out]


def ddg(q):
    h = fetch("https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(q))
    out = []
    for m in re.finditer(r'class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', h, re.S):
        u = m.group(1); mm = re.search(r"uddg=([^&]+)", u)
        if mm: u = urllib.parse.unquote(mm.group(1))
        out.append((re.sub(r"<[^>]+>", "", m.group(2))[:90], u))
    time.sleep(10)
    return out


def li_from(results):
    for ttl, u in results:
        if "linkedin.com/in/" in u:
            return u.split("?")[0], ttl
    return "", ""


def main():
    rows = json.load(open(OUT))
    for r in rows:
        act = r.get("action", "")
        if not (act.startswith("not found") or act.startswith("name-only")): continue
        nm, comp = r.get("person", ""), r["name"]
        q = (f'{nm} {comp} linkedin' if nm else f'{comp} founder OR CEO linkedin')
        li, ttl = li_from(bing(q))
        eng = "bing"
        if not li:
            li, ttl = li_from(ddg(q + " site:linkedin.com/in")); eng = "ddg2"
        if li:
            if not nm:
                cand = re.split(r"[-–|]", ttl)[0].strip()
                if 4 < len(cand) < 40: r["person"] = cand
                tm = SENIOR.search(ttl)
                if tm and not r.get("title"): r["title"] = tm.group(0)
            r["linkedin"] = li; r["source"] = (r.get("source", "") + f" + {eng}").strip(" +")
            r["action"] = "reveal-candidate"
        print(f'{comp[:30]:<32}{(r.get("person") or "-")[:22]:<24}{"LI" if li else "--"}  [{eng}]', flush=True)
        json.dump(rows, open(OUT, "w"), indent=1, ensure_ascii=False)
    acts = {}
    for r in rows: acts[r["action"].split(" ")[0]] = acts.get(r["action"].split(" ")[0], 0) + 1
    print("\nafter pass 2:", acts)


main()
