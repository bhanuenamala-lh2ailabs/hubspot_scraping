# -*- coding: utf-8 -*-
"""Headcount per company from SignalHire's searchByQuery `total`.

WHY THIS AND NOT THE OBVIOUS SOURCES
  LinkedIn company pages  - now gated; 20 of 24 attempts returned HTTP 999 -> "Sign Up".
  GoodFirms (already on disk, 5,369 rows) - covers only 115 of our 2,499 candidates (5%),
                            and its top band is an unbounded "250+" which cannot express 250-600.
  NASSCOM itself          - publishes name, city, website only; no member detail pages exist.
SignalHire returns an exact integer, so 250-600 is directly filterable rather than approximated
by a band. Validated against the one ground truth in the repo: Velotio -> 246, where
verify_headcount.py records the analyst figure as 244.

COST: 1 SEARCH per company, 0 credits. Daily search limit is 4,000 (quota table), which the
whole candidate list fits inside. Reveals are NOT performed here - this is a size filter, and
paying credits for a founder before knowing the company is in band is the wrong order.

WHAT THE NUMBER ACTUALLY IS: how many people SignalHire has on file listing this employer.
It tracks real headcount closely for firms with normal web presence and UNDER-counts firms with
a thin one. So a company below the floor may be genuinely small or merely invisible - those are
recorded as `below_range`, not silently deleted, and the raw total is always kept.

Usage: python3 headcount_sh.py --src agent_verdicts_pilot.json [--lo 250] [--hi 600]
"""
import os, re, sys, json, time, collections, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
SH = env["signal_hire"]

SRC = os.path.join(HERE, "agent_verdicts_pilot.json")
OUT = os.path.join(HERE, "headcounts.json")
LO, HI, DELAY, LIMIT = 250, 600, 0.35, 0
RELEVANT_ONLY = True
for i, a in enumerate(sys.argv):
    if a == "--src": SRC = os.path.join(HERE, sys.argv[i+1])
    if a == "--out": OUT = os.path.join(HERE, sys.argv[i+1])
    if a == "--lo": LO = int(sys.argv[i+1])
    if a == "--hi": HI = int(sys.argv[i+1])
    if a == "--limit": LIMIT = int(sys.argv[i+1])
    if a == "--all": RELEVANT_ONLY = False

LEGAL = re.compile(r"\b(private|pvt\.?|limited|ltd\.?|llp|inc\.?|corporation|corp\.?|co\.?)\b", re.I)


def query_name(n):
    """SignalHire matches the employer string people actually put on their profile, which is the
    brand, not the registered name. Strip the legal wrapper and any parenthetical alias.
    Guard against over-stripping: a 1-2 character stub would match half the database."""
    s = re.sub(r"\(.*?\)", " ", n or "")
    s = LEGAL.sub(" ", s)
    s = re.sub(r"[^\w&.\- ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip(" -.&")
    # A trailing "India" is the registered entity's name, not what staff put on their profile:
    # "Goavega Software India" returns 0 where "Goavega Software" returns 56. Only strip it when
    # something substantial remains, so "Tech India" does not collapse to "Tech".
    st = re.sub(r"\s+India$", "", s)
    if st != s and len(st) >= 6: s = st
    return s if len(s) >= 3 else (n or "").strip()


def total_for(name):
    """-> (total|None, note). 1 search, 0 credits."""
    body = {"currentCompany": name, "size": 1}
    req = urllib.request.Request("https://www.signalhire.com/api/v1/candidate/searchByQuery",
                                 data=json.dumps(body).encode(), method="POST",
                                 headers={"apikey": SH, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.loads(r.read().decode())
        return d.get("total"), ""
    except urllib.error.HTTPError as e:
        return None, ("QUOTA" if e.code == 402 else f"http{e.code}")
    except Exception as e:
        return None, type(e).__name__


def main():
    rows = json.load(open(SRC, encoding="utf-8"))
    if RELEVANT_ONLY:
        rows = [r for r in rows if r.get("relevant")]
    if LIMIT: rows = rows[:LIMIT]
    state = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else []
    done = {r["domain"] for r in state}
    print(f"{len(rows)} companies to size | {len(done)} already done | range {LO}-{HI}", flush=True)

    t0 = time.time()
    for i, r in enumerate(rows, 1):
        if r["domain"] in done: continue
        q = query_name(r["name"])
        tot, note = total_for(q)
        if note == "QUOTA":
            print("!! SignalHire SEARCH quota exhausted — stopping cleanly", flush=True); break
        rec = {"name": r["name"], "domain": r["domain"], "query": q, "total": tot, "note": note,
               "prod_or_serv": r.get("prod_or_serv"), "confidence": r.get("confidence"),
               "founded_year": r.get("founded_year")}
        if tot is None: rec["band"] = "lookup_failed"
        elif tot < LO: rec["band"] = "below_range"
        elif tot > HI: rec["band"] = "above_range"
        else: rec["band"] = "IN RANGE"
        state.append(rec); done.add(r["domain"])
        json.dump(state, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        if rec["band"] == "IN RANGE" or i % 20 == 0:
            print(f'  [{i}/{len(rows)}] {time.time()-t0:>5.0f}s  {q[:36]:<38}{str(tot):>8}  {rec["band"]}', flush=True)
        time.sleep(DELAY)

    print(f"\nsized {len(state)} in {time.time()-t0:.0f}s -> {os.path.basename(OUT)}")
    b = collections.Counter(r["band"] for r in state)
    print("\nBAND:")
    for k, n in b.most_common(): print(f"   {n:>5}  {k}  ({n/len(state)*100:.0f}%)")
    ok = [r for r in state if r["total"] is not None]
    if ok:
        s = sorted(r["total"] for r in ok)
        print(f"\nmedian headcount: {s[len(s)//2]}")
        print(f"distribution: <50 {sum(1 for x in s if x<50)} | 50-249 {sum(1 for x in s if 50<=x<250)} | "
              f"{LO}-{HI} {sum(1 for x in s if LO<=x<=HI)} | >{HI} {sum(1 for x in s if x>HI)}")
    hits = [r for r in state if r["band"] == "IN RANGE"]
    if hits:
        print(f"\nIN RANGE ({len(hits)}):")
        for r in sorted(hits, key=lambda x: -x["total"]):
            print(f"   {r['name'][:46]:<48}{r['total']:>6}   {r['prod_or_serv']}")


main()
