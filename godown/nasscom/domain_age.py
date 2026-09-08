# -*- coding: utf-8 -*-
"""Domain registration date via RDAP — the fast route to the pre-2024 gate.

WHY THIS REPLACED WAYBACK MID-RUN. archive.org started at ~9s per firm and degraded to ~150s
under throttling; the remaining 1,200 firms would have taken 17 hours. RDAP answers a slightly
narrower question in ~1.2s with no rate limiting, so it can cover the whole pool in minutes.

WHAT EACH SIGNAL ACTUALLY PROVES — they are not interchangeable, and the grader is told so:
  Wayback snapshot   the firm's own site was ADVERTISING SOFTWARE WORK before 2024.
                     Strongest. Already collected for 546 firms; kept as the primary evidence.
  RDAP registration  the domain EXISTED before 2024. Does not prove what they were doing with it,
                     but a 2005 domain plus a site that sells software today is a reasonable
                     inference, and a 2024 registration is a genuine red flag.

So RDAP is a floor, not a substitute. Where Wayback evidence exists it wins.

Usage: python3 domain_age.py [--src all_evidence.json] [--workers 8]
"""
import os, re, sys, json, time, collections, urllib.request
import concurrent.futures as cf

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "all_evidence.json")
OUT = os.path.join(HERE, "domain_age.json")
WORKERS = 8
for i, a in enumerate(sys.argv):
    if a == "--src": SRC = os.path.join(HERE, sys.argv[i+1])
    if a == "--out": OUT = os.path.join(HERE, sys.argv[i+1])
    if a == "--workers": WORKERS = int(sys.argv[i+1])

UA = "lh2-lead-research/1.0"


def rdap(domain):
    """-> (registration_date 'YYYY-MM-DD' | '', note). rdap.org routes to the right registry."""
    for attempt in range(3):
        try:
            r = urllib.request.Request(f"https://rdap.org/domain/{domain}",
                                       headers={"User-Agent": UA, "Accept": "application/rdap+json"})
            with urllib.request.urlopen(r, timeout=20) as x:
                j = json.loads(x.read().decode())
            for e in (j.get("events") or []):
                if e.get("eventAction") == "registration":
                    return (e.get("eventDate") or "")[:10], ""
            return "", "no registration event"
        except urllib.error.HTTPError as e:
            if e.code == 404: return "", "domain not found in RDAP"
            if e.code in (429, 503) and attempt < 2: time.sleep(3 * (attempt + 1)); continue
            return "", f"http{e.code}"
        except Exception as e:
            if attempt == 2: return "", type(e).__name__
            time.sleep(2 * (attempt + 1))
    return "", "retries exhausted"


def one(r):
    d = r.get("domain") or ""
    rec = {"name": r["name"], "domain": d, "registered": "", "note": ""}
    if not d: return rec
    reg, note = rdap(d)
    rec["registered"], rec["note"] = reg, note
    if reg:
        rec["pre2024_domain"] = reg < "2024-01-01"
        rec["age_years"] = round((2026 - int(reg[:4])) + (1 - int(reg[5:7]) / 12), 1)
    return rec


def main():
    rows = [r for r in json.load(open(SRC, encoding="utf-8")) if not r.get("error")]
    done = {}
    if os.path.exists(OUT):
        done = {x["domain"]: x for x in json.load(open(OUT, encoding="utf-8"))}
    todo = [r for r in rows if r.get("domain") not in done]
    print(f"{len(rows)} firms | {len(done)} done | {len(todo)} to look up", flush=True)

    out, t0 = list(done.values()), time.time()
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for i, r in enumerate(ex.map(one, todo), 1):
            out.append(r)
            if i % 100 == 0:
                json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                got = sum(1 for x in out if x.get("registered"))
                print(f"   {i}/{len(todo)}  {time.time()-t0:.0f}s   resolved {got}", flush=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    ok = [x for x in out if x.get("registered")]
    pre = [x for x in ok if x.get("pre2024_domain")]
    print(f"\ndone in {time.time()-t0:.0f}s -> {os.path.basename(OUT)}")
    print(f"resolved a registration date : {len(ok)}/{len(out)}")
    print(f"   domain predates 2024      : {len(pre)}  ({len(pre)/max(len(ok),1)*100:.0f}%)")
    print(f"   registered 2024 or later  : {len(ok)-len(pre)}   <- RED FLAG")
    yrs = collections.Counter(x["registered"][:4] for x in ok)
    print("\nregistration year:")
    for y in sorted(yrs):
        if y >= "2015" or yrs[y] > 30:
            print(f"   {y}  {'#'*min(yrs[y]//3,40)} {yrs[y]}")
    old = sorted(ok, key=lambda x: x["registered"])[:12]
    print("\noldest domains in the pool:")
    for x in old: print(f"   {x['registered']}  {x['name'][:46]}")


main()
