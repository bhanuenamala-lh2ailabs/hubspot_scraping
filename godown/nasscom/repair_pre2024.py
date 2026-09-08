# -*- coding: utf-8 -*-
"""Second pass at Tier GOLD for the firms whose first check found nothing readable.

WHY A REPAIR PASS EXISTS. pre2024_signal.py probes three fixed dates — 2023-06-01, 2022-06-01,
2020-06-01 — and asks Wayback for the nearest capture. That is fast and right for a site archived
continuously, but a site captured only in, say, March 2021 and January 2019 can miss all three
and come back "no snapshot fetchable". 56 firms landed there, and because the rubric caps a
company at 45 without pre-2024 evidence, every one was pushed to Skip on a LOOKUP failure rather
than on anything true about the business. MTAP Technologies scored 80 on process evidence and
still fell to 45 this way.

So here we spend the CDX call we skipped: ask for the timestamps that ACTUALLY exist before 2024
and fetch those exact captures. Slower per company, but it only runs on the firms where the cheap
path failed.

Usage: python3 repair_pre2024.py [--src pre2024.json]
"""
import os, re, sys, json, time, html, collections, urllib.request, urllib.error
import concurrent.futures as cf

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "pre2024.json")
OUT = os.path.join(HERE, "pre2024_repaired.json")
WORKERS = 3
for i, a in enumerate(sys.argv):
    if a == "--src": SRC = os.path.join(HERE, sys.argv[i+1])
    if a == "--out": OUT = os.path.join(HERE, sys.argv[i+1])
    if a == "--workers": WORKERS = int(sys.argv[i+1])

UA = "Mozilla/5.0 (compatible; lh2-lead-research/1.0)"
# Tightened from the first pass: "platform", "our work" and "portfolio" alone matched a coworking
# operator's workspace-booking page and marked it as pre-2024 software evidence. Require language
# that only a firm building software would use.
BUILDS = re.compile(
    r"(custom software (development|solution)|software development (services|company|firm)|"
    r"product engineering|application development|web (and|&) mobile development|"
    r"mobile app development|software engineering|we build (software|applications|products)|"
    r"offshore development|dedicated (developers|development team)|"
    r"\b(java|python|php|asp\.net|\.net|reactjs|angularjs|node\.?js|laravel|django)\b)", re.I)
NEEDS_REPAIR = ("no snapshot fetchable", "LOOKUP FAILED", "no wayback capture")


def get(u, t=30, tries=3):
    last = None
    for a in range(tries):
        try:
            r = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "*/*"})
            with urllib.request.urlopen(r, timeout=t) as x:
                return x.read(700_000).decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 503, 504): time.sleep(5 * (a + 1)); continue
            raise
        except Exception as e:
            last = e; time.sleep(3 * (a + 1))
    raise last


def text_of(h):
    h = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h)))


def one(r):
    d = r["domain"]
    out = dict(r); out["repaired"] = False
    u = (f"http://web.archive.org/cdx/search/cdx?url={d}&output=json&fl=timestamp"
         f"&filter=statuscode:200&collapse=timestamp:4&to=20231231&limit=40")
    try:
        rows = json.loads(get(u))[1:]
    except Exception as e:
        out["note"] = f"LOOKUP FAILED on repair ({type(e).__name__}) — still NOT absence"
        return out
    if not rows:
        out["note"] = "confirmed: no pre-2024 capture exists"
        out["first_snapshot"] = None
        return out
    stamps = [x[0] for x in rows]
    out["first_snapshot"] = stamps[0][:8]
    # newest-first inside the pre-2024 window: a mature page beats a launch placeholder
    for ts in sorted(stamps, reverse=True)[:6]:
        try:
            t = text_of(get(f"https://web.archive.org/web/{ts}id_/http://{d}/", tries=2))
        except Exception:
            continue
        if len(t) < 300: continue
        m = BUILDS.search(t)
        out["snapshot_used"] = ts[:8]
        out["repaired"] = True
        if m:
            i = m.start()
            out["pre2024_software"] = True
            out["evidence"] = re.sub(r"\s+", " ", t[max(0, i-60):i+90]).strip()[:150]
            out["note"] = f"REPAIRED: pre-2024 software evidence in {ts[:8]} capture"
        else:
            out["pre2024_software"] = False
            out["note"] = f"REPAIRED: {ts[:8]} capture readable, no software language"
        return out
    out["note"] = f"{len(stamps)} pre-2024 captures exist but none fetchable — MISSING, not absent"
    return out


def main():
    rows = json.load(open(SRC, encoding="utf-8"))
    todo = [r for r in rows if any(k in (r.get("note") or "") for k in NEEDS_REPAIR)]
    keep = [r for r in rows if r not in todo]
    print(f"{len(rows)} checked | {len(todo)} need repair", flush=True)
    fixed, t0 = [], time.time()
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for i, r in enumerate(ex.map(one, todo), 1):
            fixed.append(r)
            if i % 10 == 0: print(f"   {i}/{len(todo)}  {time.time()-t0:.0f}s", flush=True)
    allr = keep + fixed
    json.dump(allr, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    won = [r for r in fixed if r.get("pre2024_software")]
    print(f"\ndone in {time.time()-t0:.0f}s -> {os.path.basename(OUT)}")
    print(f"newly proven pre-2024 software : {len(won)}")
    print(f"readable but no software text  : {sum(1 for r in fixed if r.get('repaired') and not r.get('pre2024_software'))}")
    print(f"confirmed never captured       : {sum(1 for r in fixed if 'no pre-2024 capture exists' in (r.get('note') or ''))}")
    print(f"still unresolved (MISSING)     : {sum(1 for r in fixed if not r.get('repaired') and 'no pre-2024 capture' not in (r.get('note') or ''))}")
    print(f"\nTIER GOLD total now: {sum(1 for r in allr if r.get('pre2024_software'))} / {len(allr)}")
    for r in won[:20]: print(f"   {r['name'][:44]:<46}{r.get('snapshot_used')}")


main()
